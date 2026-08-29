"""Independent local characterization of every tracked SLURM entry point."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from dataclasses import dataclass, fields
from pathlib import Path

import pytest
from slurm_wrapper_cases import (
    CONTRACTS,
    DELEGATED_FIXTURES,
    DELEGATED_JOBS,
    EMPTY_ARRAY_DRY_RUN_DEFECTS,
    ENV_BASH_JOBS,
    EXECUTABLE_JOBS,
    JOB_PATHS,
    NO_EXPLICIT_MODE_JOBS,
    SBATCH_DIRECTIVES,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
JOBS_ROOT = REPO_ROOT / "jobs"
REPOSITORY_OWNING_JOBS = frozenset(
    {
        "step_00a_build_novogene_star_index.slurm",
        "step_00b_gtf_to_bed12.slurm",
        "step_00c_prepare_gatk_reference.slurm",
        "step_01_star_align.slurm",
        "step_02_sort_index_bam.slurm",
        "step_02b_bam_qc.slurm",
        "step_03_infer_strandedness_and_orientation.slurm",
        "step_04_mark_duplicates.slurm",
        "step_05_split_n_cigar_reads.slurm",
        "step_06_split_bam_by_read_orientation.slurm",
        "step_07_bcftools_mpileup_by_chrom_and_strand.slurm",
        "step_08_vcf_preprocessing.slurm",
        "step_09_cmh_editing_site_calling.slurm",
        "scientific_context_projection.slurm",
    }
)
CHECKOUT_HELPERS = (
    Path("src/emrys/libraries/argument_parsing.sh"),
    Path("src/emrys/libraries/gatk_invocation.sh"),
    Path("src/emrys/libraries/orientation.sh"),
    Path("src/emrys/libraries/process_environment.py"),
)


def job_path(name: str) -> Path:
    return REPO_ROOT / JOB_PATHS[name]


@dataclass
class PreparedWrapper:
    name: str
    submit: Path
    launch: Path
    environment: dict[str, str]
    expected_args: tuple[str, ...]
    outputs: tuple[Path, ...]
    output_directories: tuple[Path, ...]
    delegate_log: Path
    delegate_cwd_log: Path
    module_log: Path


def write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def touch(path: Path, content: str = "fixture\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def install_module_fake(fake_bin: Path) -> None:
    write_executable(
        fake_bin / "module",
        """#!/bin/bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_MODULE_LOG:?}"
exit_code="${FAKE_MODULE_EXIT:-0}"
case "${1:-}" in
    list) exit_code="${FAKE_MODULE_LIST_EXIT:-$exit_code}" ;;
    load) exit_code="${FAKE_MODULE_LOAD_EXIT:-$exit_code}" ;;
esac
exit "$exit_code"
""",
    )


def install_tool_fakes(fake_bin: Path) -> None:
    body = """#!/bin/bash
set -euo pipefail
tool="${0##*/}"
{
    printf '%s' "$tool"
    printf '\t%s' "$@"
    printf '\n'
} >> "${FAKE_TOOL_LOG:?}"
if [[ "${FAKE_FAIL_TOOL:-}" == "$tool" ]]; then
    exit "${FAKE_TOOL_EXIT:-37}"
fi
if [[ "$tool" == "java" && "${1:-}" == "-jar" && "${FAKE_FAIL_JAVA_JAR:-0}" == "1" ]]; then
    exit "${FAKE_TOOL_EXIT:-37}"
fi
case "$tool" in
    java)
        if [[ -n "${FAKE_JAVA_VERSION_OUTPUT:-}" ]]; then
            printf '%s\n' "$FAKE_JAVA_VERSION_OUTPUT" >&2
        else
            printf 'openjdk version "17.0.14"\n' >&2
        fi
        ;;
    STAR)
        printf 'STAR_2.7.11b\n'
        args=("$@")
        for ((i = 0; i < ${#args[@]}; i++)); do
            if [[ "${args[$i]}" == "--genomeDir" ]]; then
                mkdir -p "${args[$((i + 1))]}"
                printf 'mock STAR index\n' > "${args[$((i + 1))]}/Genome"
            fi
        done
        ;;
    samtools)
        printf 'samtools 1.19.2\n'
        ;;
    gatk)
        printf 'GATK 4.6.1.0\n'
        ;;
    bcftools)
        printf 'bcftools 1.21\n'
        ;;
    Rscript)
        printf 'Rscript 4.6.1\n'
        ;;
    python)
        printf 'Python 3.11.0\n'
        ;;
esac
"""
    for name in (
        "STAR",
        "samtools",
        "gatk",
        "bcftools",
        "Rscript",
        "infer_experiment.py",
        "python",
        "java",
    ):
        write_executable(fake_bin / name, body)


def install_delegate_stub(path: Path, *, python_prefix: bool = False) -> None:
    prefix = (
        """if [[ "${4:-}" == "-c" ]]; then
    printf '%s\n' "${FAKE_PYTHON_MODULE_PATH:?}"
    exit 0
fi
shift 5
"""
        if python_prefix
        else ""
    )
    write_executable(
        path,
        """#!/bin/bash
set -euo pipefail
"""
        + prefix
        + """\
printf '%s\n' "$@" > "${FAKE_DELEGATE_LOG:?}"
printf '%s\n' "$PWD" > "${FAKE_DELEGATE_CWD_LOG:?}"
if [[ "${FAKE_CHILD_EXIT:-0}" != "0" ]]; then
    exit "$FAKE_CHILD_EXIT"
fi
execute=0
for argument in "$@"; do
    [[ "$argument" == "--execute" ]] && execute=1
done
if [[ "$execute" == "1" && "${FAKE_SKIP_OUTPUTS:-0}" != "1" ]]; then
    while IFS= read -r output; do
        [[ -n "$output" ]] || continue
        mkdir -p "$(dirname "$output")"
        printf 'mock wrapper output\n' > "$output"
    done < "${FAKE_OUTPUT_LIST:?}"
fi
""",
    )


def install_checkout_helpers(submit: Path) -> None:
    for relative in CHECKOUT_HELPERS:
        destination = submit / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)


def base_environment(root: Path, fake_bin: Path) -> dict[str, str]:
    runtime_tmp = root / "runtime-tmp"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    module_log = root / "module.log"
    tool_log = root / "tool.log"
    picard = touch(root / "picard.jar", "mock jar\n")
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": os.pathsep.join((str(fake_bin), "/usr/bin", "/bin")),
            "TMPDIR": str(runtime_tmp),
            "USER": "emrys-test",
            "SLURM_JOB_ID": "local-wrapper-test",
            "SLURM_JOB_NAME": "local-wrapper-test",
            "SLURMD_NODENAME": "local-mock-node",
            "SLURM_CPUS_PER_TASK": "3",
            "JAVA_HOME": "",
            "PICARD": str(picard),
            "FAKE_MODULE_LOG": str(module_log),
            "FAKE_MODULE_EXIT": "0",
            "FAKE_TOOL_LOG": str(tool_log),
            "FAKE_TOOL_EXIT": "37",
            "FAKE_FAIL_TOOL": "",
            "FAKE_FAIL_JAVA_JAR": "0",
        }
    )
    environment.pop("EXECUTE", None)
    return environment


def prepare_delegated(name: str, tmp_path: Path) -> PreparedWrapper:
    contract = CONTRACTS[name]
    case = DELEGATED_FIXTURES[name]
    submit = tmp_path / "submit"
    launch = tmp_path / "alternate-launch"
    fake_bin = tmp_path / "fake-bin"
    submit.mkdir()
    launch.mkdir()
    fake_bin.mkdir()
    install_module_fake(fake_bin)
    install_tool_fakes(fake_bin)
    install_checkout_helpers(submit)
    if name == "step_08_vcf_preprocessing.slurm":
        producer = (
            submit / "src/emrys/stages/cohort_candidate_preprocessing/producer.py"
        )
        producer.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / producer.relative_to(submit), producer)
        install_delegate_stub(fake_bin / "emrys-python", python_prefix=True)
    else:
        install_delegate_stub(submit / contract.delegation)

    environment = base_environment(tmp_path, fake_bin)
    environment.update(
        {
            "SLURM_SUBMIT_DIR": str(submit),
            "FAKE_DELEGATE_LOG": str(tmp_path / "delegate.args"),
            "FAKE_DELEGATE_CWD_LOG": str(tmp_path / "delegate.cwd"),
            "FAKE_CHILD_EXIT": "0",
            "FAKE_SKIP_OUTPUTS": "0",
        }
    )
    if name == "step_08_vcf_preprocessing.slurm":
        environment["FAKE_PYTHON_MODULE_PATH"] = str(
            submit / "src/emrys/stages/cohort_candidate_preprocessing/producer.py"
        )
    context = {
        "submit": str(submit),
        "fake_bin": str(fake_bin),
        "python": str(REPO_ROOT / ".venv" / "bin" / "python"),
    }
    for fixture_path in case.paths:
        resolved = Path(fixture_path.template.format_map(context))
        if fixture_path.kind == "file":
            touch(resolved, fixture_path.content)
        elif fixture_path.kind == "directory":
            resolved.mkdir(parents=True)
        elif fixture_path.kind != "path":
            raise AssertionError(f"unknown fixture path kind: {fixture_path.kind}")
        context[fixture_path.name] = str(resolved)

    environment.update(
        {key: value.format_map(context) for key, value in case.environment}
    )
    expected_args = (
        tuple(
            item
            for flag, value in case.arguments
            for item in (flag, value.format_map(context))
        )
        + case.flags
    )
    outputs = tuple(Path(value.format_map(context)) for value in case.outputs)
    output_directories = tuple(
        Path(value.format_map(context)) for value in case.output_directories
    )
    output_list = tmp_path / "outputs.list"
    output_list.write_text(
        "".join(f"{output}\n" for output in outputs),
        encoding="utf-8",
    )
    environment["FAKE_OUTPUT_LIST"] = str(output_list)
    return PreparedWrapper(
        name=name,
        submit=submit,
        launch=launch,
        environment=environment,
        expected_args=expected_args,
        outputs=outputs,
        output_directories=output_directories,
        delegate_log=Path(environment["FAKE_DELEGATE_LOG"]),
        delegate_cwd_log=Path(environment["FAKE_DELEGATE_CWD_LOG"]),
        module_log=Path(environment["FAKE_MODULE_LOG"]),
    )


def run_prepared(
    prepared: PreparedWrapper,
    *,
    execute: str | None = None,
    environment_updates: dict[str, str] | None = None,
    environment_removals: tuple[str, ...] = (),
    cwd: Path | None = None,
    job: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = prepared.environment.copy()
    if execute is None:
        environment.pop("EXECUTE", None)
    else:
        environment["EXECUTE"] = execute
    if environment_updates:
        environment.update(environment_updates)
    for key in environment_removals:
        environment.pop(key, None)
    contract = CONTRACTS[prepared.name]
    if cwd is None:
        cwd = prepared.submit if contract.submit_cwd == "caller" else prepared.launch
    if job is None:
        job = job_path(prepared.name)
    return subprocess.run(
        ["/bin/bash", str(job)],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def read_nul_args(path: Path) -> tuple[str, ...]:
    return tuple(path.read_text(encoding="utf-8").splitlines())


def local_bash_major() -> int:
    result = subprocess.run(
        ["/bin/bash", "-c", "printf '%s' \"${BASH_VERSINFO[0]}\""],
        text=True,
        capture_output=True,
        check=True,
    )
    return int(result.stdout)


def read_lines(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(path.read_text(encoding="utf-8").splitlines())


def test_inventory_and_contract_decisions_cover_every_live_wrapper() -> None:
    live_flat_jobs = {Path("jobs") / path.name for path in JOBS_ROOT.glob("*.slurm")}
    expected_flat_jobs = {
        path for path in JOB_PATHS.values() if path.parent == Path("jobs")
    }

    assert live_flat_jobs == expected_flat_jobs
    assert set(JOB_PATHS) == set(CONTRACTS) == set(SBATCH_DIRECTIVES)
    assert all(job_path(name).is_file() for name in CONTRACTS)
    assert len(set(JOB_PATHS.values())) == len(CONTRACTS) == 16
    assert {
        name
        for name, contract in CONTRACTS.items()
        if contract.submit_cwd == "required"
    } == REPOSITORY_OWNING_JOBS
    for contract in CONTRACTS.values():
        assert all(
            getattr(contract, field.name)
            for field in fields(contract)
            if field.name != "module_calls"
        )
        if contract.module_policy == "preinstalled_python":
            assert contract.module_calls == ()
        else:
            assert contract.module_calls


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_sbatch_shebang_strict_mode_and_file_mode_are_exact(name: str) -> None:
    job = job_path(name)
    lines = job.read_text(encoding="utf-8").splitlines()
    directives = tuple(line for line in lines if line.startswith("#SBATCH "))

    assert directives == SBATCH_DIRECTIVES[name]
    assert lines[0] == (
        "#!/usr/bin/env bash" if name in ENV_BASH_JOBS else "#!/bin/bash"
    )
    assert "set -euo pipefail" in lines
    mode = job.stat().st_mode
    is_executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    assert is_executable is (name in EXECUTABLE_JOBS)


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_submit_directory_decision_is_literal(name: str) -> None:
    source = job_path(name).read_text(encoding="utf-8")
    decision = CONTRACTS[name].submit_cwd

    if decision == "required":
        guard = ': "${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR is required}"'
        change_directory = 'cd "$SLURM_SUBMIT_DIR"'
        assert guard in source
        assert 'cd "$SLURM_SUBMIT_DIR"' in source
        assert 'cd "${SLURM_SUBMIT_DIR:-$PWD}"' not in source
        assert "BASH_SOURCE" not in source
        assert source.index(guard) < source.index(change_directory)
        assert source.index(change_directory) < source.index("src/emrys/")
    elif decision == "fallback":
        assert 'cd "${SLURM_SUBMIT_DIR:-$PWD}"' in source
    else:
        assert "SLURM_SUBMIT_DIR" not in source


@pytest.mark.parametrize("name", sorted(NO_EXPLICIT_MODE_JOBS))
def test_legacy_and_utility_jobs_have_no_execute_mode(name: str) -> None:
    source = job_path(name).read_text(encoding="utf-8")

    assert "EXECUTE" not in source
    assert CONTRACTS[name].invalid_mode == "not_applicable"


@pytest.mark.parametrize(
    ("name", "missing_variable"),
    (
        ("step_07_bcftools_mpileup_by_chrom_and_strand.slurm", "SAMPLE_MANIFEST"),
        ("step_08_vcf_preprocessing.slurm", "STEP07_ROOT"),
    ),
)
def test_late_stage_requires_explicit_dataset_bindings_before_outputs(
    name: str,
    missing_variable: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        environment_removals=(missing_variable,),
    )

    assert result.returncode != 0
    assert f"{missing_variable} is required" in result.stderr
    assert not prepared.delegate_log.exists()
    assert not prepared.module_log.exists()
    assert all(not output.exists() for output in prepared.outputs)
    assert all(not directory.exists() for directory in prepared.output_directories)


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_default_is_mocked_dry_run_with_exact_contract(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(prepared)

    assert read_lines(prepared.module_log) == CONTRACTS[name].module_calls
    assert all(not output.exists() for output in prepared.outputs)
    for output_directory in prepared.output_directories:
        if name in {
            "step_02_sort_index_bam.slurm",
            "step_02b_bam_qc.slurm",
        }:
            assert output_directory.is_dir()
        else:
            assert not output_directory.exists()
    if name in EMPTY_ARRAY_DRY_RUN_DEFECTS and local_bash_major() < 4:
        assert result.returncode != 0
        assert "execute_args[@]: unbound variable" in result.stderr
        assert not prepared.delegate_log.exists()
        return

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args
    assert prepared.delegate_cwd_log.read_text(encoding="utf-8").strip() == str(
        prepared.submit
    )


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_execute_forwards_exact_args_and_checks_applicable_outputs(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert all(
        output.is_file() and output.stat().st_size > 0 for output in prepared.outputs
    )


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_invalid_mode_fails_before_modules_or_child(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(prepared, execute="unsafe")

    assert result.returncode != 0
    assert "EXECUTE must be 0 or 1" in result.stderr
    assert not prepared.delegate_log.exists()
    assert not prepared.module_log.exists()


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_child_exit_is_propagated(name: str, tmp_path: Path) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_CHILD_EXIT": "37"},
    )

    assert result.returncode == 37, result.stdout + result.stderr


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_output_validation_decision_is_observable(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    if CONTRACTS[name].output_validation == "wrapper_files":
        assert result.returncode != 0
        assert "Expected" in result.stderr
    else:
        assert CONTRACTS[name].output_validation == "delegate_only"
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_runs_from_external_slurm_spool_copy(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)
    spool = tmp_path / "slurm-spool"
    spool.mkdir()
    spool_job = spool / "slurm_script"
    shutil.copy2(job_path(name), spool_job)

    result = run_prepared(
        prepared,
        execute="1",
        cwd=prepared.launch,
        job=spool_job,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert prepared.delegate_cwd_log.read_text(encoding="utf-8").strip() == str(
        prepared.submit
    )
    assert not (spool / "logs").exists()
    assert not (prepared.launch / "logs").exists()


def test_step_02b_bam_qc_stale_named_outputs_mask_missing_child_outputs(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_02b_bam_qc.slurm", tmp_path)
    stale_bytes = (
        b"stale quickcheck evidence\n",
        b"stale flagstat evidence\n",
    )
    for output, content in zip(prepared.outputs, stale_bytes, strict=True):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert tuple(output.read_bytes() for output in prepared.outputs) == stale_bytes
    assert "Validated Step 02b QC outputs:" in result.stdout


def test_step_03_prefers_repository_venv_and_sources_activation(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )
    prepared.environment.pop("INFER_EXPERIMENT_BIN")
    venv_bin = prepared.submit / ".venv" / "bin"
    write_executable(venv_bin / "infer_experiment.py", "#!/bin/bash\nexit 0\n")
    activation_log = tmp_path / "activation.log"
    (venv_bin / "activate").write_text(
        "printf 'activated\\n' > \"${FAKE_ACTIVATION_LOG:?}\"\n",
        encoding="utf-8",
    )
    prepared.environment["FAKE_ACTIVATION_LOG"] = str(activation_log)

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert activation_log.read_text(encoding="utf-8") == "activated\n"
    assert read_nul_args(prepared.delegate_log) == (
        prepared.expected_args[:-1] + (".venv/bin/infer_experiment.py", "--execute")
    )
    assert all(
        output.is_file() and output.stat().st_size > 0 for output in prepared.outputs
    )


def test_step_03_without_repository_venv_delegates_path_command(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )
    prepared.environment.pop("INFER_EXPERIMENT_BIN")

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == (
        prepared.expected_args[:-1] + ("infer_experiment.py", "--execute")
    )


def test_step_03_dry_run_creates_logs_but_no_scientific_output(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )

    result = run_prepared(prepared)

    assert (prepared.submit / "logs").is_dir()
    assert all(not output.exists() for output in prepared.outputs)
    assert all(not directory.exists() for directory in prepared.output_directories)
    if local_bash_major() < 4:
        assert result.returncode != 0
        assert "execute_args[@]: unbound variable" in result.stderr
        assert not prepared.delegate_log.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert read_nul_args(prepared.delegate_log) == prepared.expected_args


def test_step_03_stale_named_report_masks_missing_child_output(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )
    stale_bytes = b"stale paired-orientation evidence\n"
    prepared.outputs[0].parent.mkdir(parents=True, exist_ok=True)
    prepared.outputs[0].write_bytes(stale_bytes)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert prepared.outputs[0].read_bytes() == stale_bytes
    assert "Validated Step 03 strandedness output:" in result.stdout


def test_step_04_mark_duplicates_selects_java_home_executable(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)
    java_home = tmp_path / "java-home"
    home_java = java_home / "bin" / "java"
    write_executable(
        home_java,
        "#!/bin/bash\nprintf 'openjdk version \\\"17.0.99\\\"\\n' >&2\n",
    )
    prepared.environment.pop("JAVA_BIN_OVERRIDE")
    prepared.environment["JAVA_HOME"] = str(java_home)

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == (
        prepared.expected_args[:-1] + (str(home_java), "--execute")
    )
    assert f"Java: {home_java}" in result.stdout


def test_step_04_mark_duplicates_falls_back_to_path_after_unusable_java_home(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)
    prepared.environment.pop("JAVA_BIN_OVERRIDE")
    prepared.environment["JAVA_HOME"] = str(tmp_path / "missing-java-home")

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert f"Java: {prepared.expected_args[-1]}" in result.stdout


def test_step_04_mark_duplicates_propagates_java_version_command_failure(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_FAIL_TOOL": "java", "FAKE_TOOL_EXIT": "37"},
    )

    assert result.returncode == 37, result.stdout + result.stderr
    assert not prepared.delegate_log.exists()


@pytest.mark.parametrize(
    ("version_output", "diagnostic"),
    (
        ('openjdk version "11.0.24"', "Picard requires Java 17 or newer"),
        ("unparseable java output", "Could not determine Java version"),
    ),
)
def test_step_04_mark_duplicates_rejects_unsupported_java_version_output(
    tmp_path: Path,
    version_output: str,
    diagnostic: str,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_JAVA_VERSION_OUTPUT": version_output},
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert diagnostic in result.stderr
    assert not prepared.delegate_log.exists()


def test_step_04_mark_duplicates_rejects_missing_picard_after_module_load(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"PICARD": ""},
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert "PICARD is not set after loading picard/3.1.1" in result.stderr
    assert read_lines(prepared.module_log) == ("list", "load picard/3.1.1")
    assert not prepared.delegate_log.exists()


def test_step_04_mark_duplicates_tolerates_list_only_module_failures(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={
            "FAKE_MODULE_LIST_EXIT": "23",
            "FAKE_MODULE_LOAD_EXIT": "0",
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_lines(prepared.module_log) == CONTRACTS[prepared.name].module_calls
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )


def test_step_04_mark_duplicates_dry_run_creates_logs_only(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)

    result = run_prepared(prepared)

    assert (prepared.submit / "logs").is_dir()
    assert all(not output.exists() for output in prepared.outputs)
    assert all(not directory.exists() for directory in prepared.output_directories)
    if local_bash_major() < 4:
        assert result.returncode != 0
        assert "execute_args[@]: unbound variable" in result.stderr
        assert not prepared.delegate_log.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert read_nul_args(prepared.delegate_log) == prepared.expected_args


def test_step_04_mark_duplicates_stale_triplet_masks_missing_child_outputs(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)
    stale_bytes = (
        b"stale duplicate-marked BAM\n",
        b"stale duplicate-marked BAI\n",
        b"stale Picard metrics\n",
    )
    for output, content in zip(prepared.outputs, stale_bytes, strict=True):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert tuple(output.read_bytes() for output in prepared.outputs) == stale_bytes
    assert "Validated Step 04 MarkDuplicates outputs:" in result.stdout


def test_step_04_mark_duplicates_unset_java_home_aborts_before_delegation(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_04_mark_duplicates.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_removals=("JAVA_HOME",),
    )

    assert result.returncode == 1, result.stdout + result.stderr
    assert "JAVA_HOME: unbound variable" in result.stderr
    assert not prepared.delegate_log.exists()


def test_step_05_split_n_cigar_reads_selects_java_home_executable(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)
    java_home = tmp_path / "java-home"
    home_java = java_home / "bin" / "java"
    write_executable(
        home_java,
        "#!/bin/bash\nprintf 'openjdk version \\\"17.0.99\\\"\\n' >&2\n",
    )
    prepared.environment.pop("JAVA_BIN_OVERRIDE")
    prepared.environment["JAVA_HOME"] = str(java_home)

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == (
        prepared.expected_args[:-1] + (str(home_java), "--execute")
    )
    assert f"Java: {home_java}" in result.stdout


def test_step_05_split_n_cigar_reads_falls_back_to_path_after_unusable_java_home(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)
    prepared.environment.pop("JAVA_BIN_OVERRIDE")
    prepared.environment["JAVA_HOME"] = str(tmp_path / "missing-java-home")

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert f"Java: {prepared.expected_args[-1]}" in result.stdout


@pytest.mark.parametrize("override_state", ("missing", "nonexecutable"))
def test_step_05_split_n_cigar_reads_rejects_unusable_java_override(
    tmp_path: Path,
    override_state: str,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)
    java_override = tmp_path / f"{override_state}-java"
    if override_state == "nonexecutable":
        touch(java_override, "not executable\n")

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"JAVA_BIN_OVERRIDE": str(java_override)},
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert "No usable Java executable was found" in result.stderr
    assert not prepared.delegate_log.exists()


def test_step_05_split_n_cigar_reads_propagates_java_version_command_failure(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_FAIL_TOOL": "java", "FAKE_TOOL_EXIT": "37"},
    )

    assert result.returncode == 37, result.stdout + result.stderr
    assert not prepared.delegate_log.exists()


@pytest.mark.parametrize(
    ("version_output", "diagnostic"),
    (
        ('openjdk version "11.0.24"', "GATK SplitNCigarReads requires Java 17"),
        ("unparseable java output", "Could not determine Java version"),
    ),
)
def test_step_05_split_n_cigar_reads_rejects_unsupported_java_version_output(
    tmp_path: Path,
    version_output: str,
    diagnostic: str,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_JAVA_VERSION_OUTPUT": version_output},
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert diagnostic in result.stderr
    assert not prepared.delegate_log.exists()


@pytest.mark.parametrize("tool", ("samtools",))
def test_step_05_split_n_cigar_reads_propagates_tool_version_command_failure(
    tmp_path: Path,
    tool: str,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_FAIL_TOOL": tool, "FAKE_TOOL_EXIT": "37"},
    )

    assert result.returncode == 37, result.stdout + result.stderr
    assert not prepared.delegate_log.exists()


@pytest.mark.parametrize(
    "name",
    (
        "step_00c_prepare_gatk_reference.slurm",
        "step_05_split_n_cigar_reads.slurm",
    ),
)
def test_gatk_wrappers_leave_version_probe_to_delegated_owner(
    tmp_path: Path,
    name: str,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_FAIL_TOOL": "gatk", "FAKE_TOOL_EXIT": "37"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert all(
        not line.startswith("gatk\t") for line in read_lines(tmp_path / "tool.log")
    )


@pytest.mark.parametrize(
    "name",
    (
        "step_00c_prepare_gatk_reference.slurm",
        "step_05_split_n_cigar_reads.slurm",
    ),
)
@pytest.mark.parametrize("python_state", ("missing", "nonexecutable", "unsupported"))
def test_gatk_wrappers_reject_unusable_controlled_python_before_delegation(
    tmp_path: Path,
    name: str,
    python_state: str,
) -> None:
    prepared = prepare_delegated(name, tmp_path)
    python = tmp_path / f"{python_state}-python"
    if python_state == "nonexecutable":
        touch(python, "not executable\n")
    elif python_state == "unsupported":
        write_executable(
            python,
            "#!/bin/bash\nprintf 'Python 3.10.0\\n' >&2\nexit 2\n",
        )

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"EMRYS_SHA256_PYTHON": str(python)},
    )

    assert result.returncode == 2, result.stdout + result.stderr
    assert "EMRYS_SHA256_PYTHON" in result.stderr
    assert not prepared.delegate_log.exists()


@pytest.mark.parametrize("tool", ("gatk", "samtools"))
@pytest.mark.parametrize("tool_state", ("missing", "nonexecutable"))
def test_step_05_split_n_cigar_reads_warns_and_delegates_unusable_tool(
    tmp_path: Path,
    tool: str,
    tool_state: str,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)
    tool_path = tmp_path / f"{tool_state}-{tool}"
    if tool_state == "nonexecutable":
        touch(tool_path, "not executable\n")
    environment_key = f"{tool.upper()}_BIN_OVERRIDE"
    option = f"--{tool}-bin"
    expected_args = list(prepared.expected_args)
    expected_args[expected_args.index(option) + 1] = str(tool_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={environment_key: str(tool_path)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    label = "GATK" if tool == "gatk" else "samtools"
    assert (
        f"WARNING: {label} path is not executable before script validation: {tool_path}"
    ) in result.stdout
    assert read_nul_args(prepared.delegate_log) == tuple(expected_args) + ("--execute",)
    assert all(
        output.read_bytes() == b"mock wrapper output\n" for output in prepared.outputs
    )


def test_step_05_split_n_cigar_reads_dry_run_creates_logs_only(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)

    result = run_prepared(prepared)

    assert (prepared.submit / "logs").is_dir()
    assert all(not output.exists() for output in prepared.outputs)
    assert all(not directory.exists() for directory in prepared.output_directories)
    if local_bash_major() < 4:
        assert result.returncode != 0
        assert "execute_args[@]: unbound variable" in result.stderr
        assert not prepared.delegate_log.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert read_nul_args(prepared.delegate_log) == prepared.expected_args


def test_step_05_split_n_cigar_reads_stale_pair_masks_missing_child_outputs(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_05_split_n_cigar_reads.slurm", tmp_path)
    stale_bytes = (b"stale split-N-cigar BAM\n", b"stale split-N-cigar BAI\n")
    for output, content in zip(prepared.outputs, stale_bytes, strict=True):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert tuple(output.read_bytes() for output in prepared.outputs) == stale_bytes
    assert "Validated Step 05 SplitNCigarReads outputs:" in result.stdout


def test_step_06_split_bam_by_read_orientation_propagates_samtools_version_failure(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_06_split_bam_by_read_orientation.slurm", tmp_path
    )

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_FAIL_TOOL": "samtools", "FAKE_TOOL_EXIT": "37"},
    )

    assert result.returncode == 37, result.stdout + result.stderr
    assert not prepared.delegate_log.exists()
    assert read_lines(tmp_path / "tool.log") == ("samtools\t--version",)


@pytest.mark.parametrize("tool_state", ("missing", "nonexecutable"))
@pytest.mark.parametrize(
    ("name", "tool", "override", "argument", "warns", "checks_empty_log"),
    (
        (
            "step_06_split_bam_by_read_orientation.slurm",
            "samtools",
            "SAMTOOLS_BIN_OVERRIDE",
            "--samtools-bin",
            True,
            False,
        ),
        (
            "step_07_bcftools_mpileup_by_chrom_and_strand.slurm",
            "bcftools",
            "BCFTOOLS_BIN_OVERRIDE",
            "--bcftools-bin",
            True,
            False,
        ),
        (
            "step_08_vcf_preprocessing.slurm",
            "Rscript",
            "RSCRIPT_BIN_OVERRIDE",
            "--rscript-bin",
            True,
            True,
        ),
        (
            "step_09_cmh_editing_site_calling.slurm",
            "Rscript",
            "RSCRIPT_BIN_OVERRIDE",
            "--rscript-bin",
            False,
            True,
        ),
    ),
)
def test_late_stage_delegates_unusable_tool_override(
    name: str,
    tool: str,
    override: str,
    argument: str,
    warns: bool,
    checks_empty_log: bool,
    tool_state: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)
    tool_path = tmp_path / f"{tool_state}-{tool}"
    if tool_state == "nonexecutable":
        touch(tool_path, "not executable\n")
    expected_args = list(prepared.expected_args)
    expected_args[expected_args.index(argument) + 1] = str(tool_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={override: str(tool_path)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    warning = f"WARNING: {tool} path is not executable before script validation"
    assert (warning in result.stdout) is warns
    assert read_nul_args(prepared.delegate_log) == tuple(expected_args) + ("--execute",)
    if checks_empty_log:
        assert read_lines(tmp_path / "tool.log") == ()
    assert all(
        output.read_bytes() == b"mock wrapper output\n" for output in prepared.outputs
    )


@pytest.mark.parametrize(
    ("name", "tool", "override", "argument", "probe_policy"),
    (
        (
            "step_06_split_bam_by_read_orientation.slurm",
            "samtools",
            "SAMTOOLS_BIN_OVERRIDE",
            "--samtools-bin",
            "warn",
        ),
        (
            "step_07_bcftools_mpileup_by_chrom_and_strand.slurm",
            "bcftools",
            "BCFTOOLS_BIN_OVERRIDE",
            "--bcftools-bin",
            "warn",
        ),
        (
            "step_08_vcf_preprocessing.slurm",
            "Rscript",
            "RSCRIPT_BIN_OVERRIDE",
            "--rscript-bin",
            "version",
        ),
        (
            "step_09_cmh_editing_site_calling.slurm",
            "Rscript",
            "RSCRIPT_BIN_OVERRIDE",
            "--rscript-bin",
            "none",
        ),
    ),
)
def test_late_stage_forwards_path_tool_basename(
    name: str,
    tool: str,
    override: str,
    argument: str,
    probe_policy: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)
    expected_args = list(prepared.expected_args)
    expected_args[expected_args.index(argument) + 1] = tool

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={override: tool},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == tuple(expected_args) + ("--execute",)
    tool_log = read_lines(tmp_path / "tool.log")
    assert (f"{tool}\t--version" in tool_log) is (probe_policy == "version")
    if probe_policy == "warn":
        assert (
            f"WARNING: {tool} path is not executable before script validation: {tool}"
            in result.stdout
        )
    elif probe_policy == "version":
        assert f"{tool} version:" in result.stdout
        assert "Rscript 4.6.1" in result.stdout
    else:
        assert "WARNING:" not in result.stdout
    assert all(
        output.read_bytes() == b"mock wrapper output\n" for output in prepared.outputs
    )


def test_step_06_split_bam_by_read_orientation_dry_run_creates_logs_only(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_06_split_bam_by_read_orientation.slurm", tmp_path
    )

    result = run_prepared(prepared)

    assert (prepared.submit / "logs").is_dir()
    assert all(not output.exists() for output in prepared.outputs)
    assert all(not directory.exists() for directory in prepared.output_directories)
    if local_bash_major() < 4:
        assert result.returncode != 0
        assert "execute_args[@]: unbound variable" in result.stderr
        assert not prepared.delegate_log.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert read_nul_args(prepared.delegate_log) == prepared.expected_args


def test_step_06_split_bam_by_read_orientation_threads_are_independent_of_one_cpu(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_06_split_bam_by_read_orientation.slurm", tmp_path
    )
    expected_args = list(prepared.expected_args)
    expected_args[expected_args.index("--threads") + 1] = "9"

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"SLURM_CPUS_PER_TASK": "1", "THREADS": "9"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "#SBATCH --cpus-per-task=1" in job_path(prepared.name).read_text(
        encoding="utf-8"
    )
    assert "Threads: 9" in result.stdout
    assert read_nul_args(prepared.delegate_log) == tuple(expected_args) + ("--execute",)


@pytest.mark.parametrize(
    ("name", "validation_message"),
    (
        (
            "step_06_split_bam_by_read_orientation.slurm",
            "Validated Step 06 read-orientation outputs:",
        ),
        (
            "step_07_bcftools_mpileup_by_chrom_and_strand.slurm",
            "Validated Step 07 cohort mpileup outputs:",
        ),
        (
            "step_08_vcf_preprocessing.slurm",
            "Validated Step 08 VCF preprocessing outputs:",
        ),
        (
            "step_09_cmh_editing_site_calling.slurm",
            "Validated Step 09 output paths:",
        ),
    ),
)
def test_late_stage_stale_outputs_mask_missing_child_outputs(
    name: str,
    validation_message: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)
    stale_bytes = tuple(
        f"stale preserved output {index}\n".encode()
        for index in range(len(prepared.outputs))
    )
    for output, content in zip(prepared.outputs, stale_bytes, strict=True):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert tuple(output.read_bytes() for output in prepared.outputs) == stale_bytes
    assert validation_message in result.stdout


def test_step_07_bcftools_mpileup_propagates_bcftools_version_failure(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_07_bcftools_mpileup_by_chrom_and_strand.slurm", tmp_path
    )

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_FAIL_TOOL": "bcftools", "FAKE_TOOL_EXIT": "37"},
    )

    assert result.returncode == 37, result.stdout + result.stderr
    assert not prepared.delegate_log.exists()
    assert read_lines(tmp_path / "tool.log") == ("bcftools\t--version",)


@pytest.mark.parametrize(
    "name",
    (
        "step_07_bcftools_mpileup_by_chrom_and_strand.slurm",
        "step_08_vcf_preprocessing.slurm",
        "step_09_cmh_editing_site_calling.slurm",
    ),
)
def test_late_stage_dry_run_creates_logs_only(name: str, tmp_path: Path) -> None:
    prepared = prepare_delegated(name, tmp_path)
    before = {path.relative_to(prepared.submit) for path in prepared.submit.rglob("*")}

    result = run_prepared(prepared)

    assert result.returncode == 0, result.stdout + result.stderr
    after = {path.relative_to(prepared.submit) for path in prepared.submit.rglob("*")}
    if name.startswith(("step_08", "step_09")):
        assert after - before == {Path("logs")}
    else:
        assert (prepared.submit / "logs").is_dir()
    assert all(not output.exists() for output in prepared.outputs)
    assert all(not directory.exists() for directory in prepared.output_directories)
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args


def test_step_08_vcf_preprocessing_tolerates_rscript_version_failure(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_08_vcf_preprocessing.slurm", tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_FAIL_TOOL": "Rscript", "FAKE_TOOL_EXIT": "37"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_lines(tmp_path / "tool.log") == ("Rscript\t--version",)
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + (
        "--execute",
    )
    assert all(
        output.read_bytes() == b"mock wrapper output\n" for output in prepared.outputs
    )


def test_step_08_vcf_preprocessing_forwards_r_program_for_child_validation(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_08_vcf_preprocessing.slurm", tmp_path)
    missing_r_program = prepared.submit / "implementation" / "missing-step08.R"
    expected_args = list(prepared.expected_args)
    expected_args[expected_args.index("--r-script") + 1] = str(missing_r_program)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"STEP08_R_SCRIPT": str(missing_r_program)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not missing_r_program.exists()
    assert read_nul_args(prepared.delegate_log) == tuple(expected_args) + ("--execute",)
    assert all(
        output.read_bytes() == b"mock wrapper output\n" for output in prepared.outputs
    )


def test_step_08_vcf_preprocessing_rejects_foreign_python_source(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_08_vcf_preprocessing.slurm", tmp_path)
    foreign = tmp_path / "foreign-source/producer.py"
    foreign.parent.mkdir()
    foreign.write_text("# foreign producer\n")

    result = run_prepared(
        prepared,
        environment_updates={"FAKE_PYTHON_MODULE_PATH": str(foreign)},
    )

    assert result.returncode == 1
    assert "does not resolve Step 08 from the submitted checkout" in result.stderr
    assert not prepared.delegate_log.exists()


def test_step_09_cmh_editing_site_calling_forwards_missing_r_program_to_child(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_09_cmh_editing_site_calling.slurm", tmp_path)
    missing_r_program = prepared.submit / "implementation" / "missing-step09.R"
    expected_args = list(prepared.expected_args)
    expected_args[expected_args.index("--r-script") + 1] = str(missing_r_program)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"STEP09_R_SCRIPT": str(missing_r_program)},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not missing_r_program.exists()
    assert read_lines(tmp_path / "tool.log") == ()
    assert read_nul_args(prepared.delegate_log) == tuple(expected_args) + ("--execute",)
    assert all(
        output.read_bytes() == b"mock wrapper output\n" for output in prepared.outputs
    )


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_module_failure_policy_is_observable(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_MODULE_EXIT": "23"},
    )

    if CONTRACTS[name].module_policy == "tolerated":
        assert result.returncode == 0, result.stdout + result.stderr
        assert prepared.delegate_log.exists()
    else:
        assert CONTRACTS[name].module_policy == "strict_loads_tolerated_lists"
        assert result.returncode == 23
        assert not prepared.delegate_log.exists()


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_requires_submit_directory_before_modules_or_child(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_removals=("SLURM_SUBMIT_DIR",),
        cwd=prepared.launch,
    )

    assert result.returncode != 0
    assert "SLURM_SUBMIT_DIR is required" in result.stderr
    assert not prepared.module_log.exists()
    assert not prepared.delegate_log.exists()


def test_step01_default_fixture_mode_creates_its_current_dry_run_placeholders(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_01_star_align.slurm", tmp_path)
    for key in ("SAMPLE_ID", "R1_FASTQ", "R2_FASTQ", "STAR_INDEX", "OUTPUT_DIR"):
        prepared.environment.pop(key)

    result = run_prepared(prepared)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (prepared.submit / "data/test/sample_001_R1.fastq.gz").is_file()
    assert (prepared.submit / "data/test/sample_001_R2.fastq.gz").is_file()
    assert (prepared.submit / "refs/test_star_index").is_dir()
    assert read_nul_args(prepared.delegate_log) == (
        "--sample-id",
        "sample_001",
        "--r1-fastq",
        "data/test/sample_001_R1.fastq.gz",
        "--r2-fastq",
        "data/test/sample_001_R2.fastq.gz",
        "--star-index",
        "refs/test_star_index",
        "--output-dir",
        "results/test/sample_001/star",
        "--threads",
        "3",
        "--no-clobber",
    )
    assert (
        prepared.submit / "refs/test_star_index/Genome"
    ).read_bytes() == b"dry-run STAR index fixture\n"


def prepare_legacy_environment(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    submit = tmp_path / "submit"
    launch = tmp_path / "alternate-launch"
    fake_bin = tmp_path / "fake-bin"
    submit.mkdir()
    launch.mkdir()
    fake_bin.mkdir()
    install_module_fake(fake_bin)
    install_tool_fakes(fake_bin)
    environment = base_environment(tmp_path, fake_bin)
    environment.update(
        {
            "EMRYS_PYTHON_BIN": str(fake_bin / "python"),
            "SLURM_SUBMIT_DIR": str(submit),
        }
    )
    return submit, launch, environment


UTILITY_JOBS = (
    "tool_check.slurm",
    "validate_manifest.slurm",
)
UTILITY_TOOL_CALLS = {
    "tool_check.slurm": (
        "python\t--version",
        "STAR\t--version",
        "samtools\t--version",
        "java\t-version",
        "java\t-jar\t{picard}\tMarkDuplicates\t--version",
    ),
    "validate_manifest.slurm": (
        "python\t--version",
        "python\t-I\t-m\temrys\tvalidate\tmanifest\t--manifest\tconfigs/samples.example.tsv\t--base-dir\t.",
    ),
}


@pytest.mark.parametrize("name", UTILITY_JOBS)
def test_utility_job_mocked_probe_arguments_modules_and_exit(
    name: str,
    tmp_path: Path,
) -> None:
    submit, _, environment = prepare_legacy_environment(tmp_path)
    touch(submit / "configs/samples.example.tsv")
    picard = Path(environment["PICARD"])

    result = subprocess.run(
        ["/bin/bash", str(job_path(name))],
        cwd=submit,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (
        read_lines(Path(environment["FAKE_MODULE_LOG"])) == CONTRACTS[name].module_calls
    )
    expected_calls = tuple(
        call.format(picard=picard) for call in UTILITY_TOOL_CALLS[name]
    )
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == expected_calls

    child_environment = environment.copy()
    child_environment["FAKE_FAIL_TOOL"] = "python"
    child_failed = subprocess.run(
        ["/bin/bash", str(job_path(name))],
        cwd=submit,
        env=child_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert child_failed.returncode == 37

    module_environment = environment.copy()
    module_environment["FAKE_MODULE_EXIT"] = "23"
    module_failed = subprocess.run(
        ["/bin/bash", str(job_path(name))],
        cwd=submit,
        env=module_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if CONTRACTS[name].module_calls:
        assert module_failed.returncode == 23
    else:
        assert CONTRACTS[name].module_policy == "preinstalled_python"
        assert module_failed.returncode == 0, (
            module_failed.stdout + module_failed.stderr
        )


def test_tool_check_tolerates_only_its_optional_picard_version_probe(
    tmp_path: Path,
) -> None:
    submit, _, environment = prepare_legacy_environment(tmp_path)
    environment["FAKE_FAIL_JAVA_JAR"] = "1"

    result = subprocess.run(
        ["/bin/bash", str(job_path("tool_check.slurm"))],
        cwd=submit,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
