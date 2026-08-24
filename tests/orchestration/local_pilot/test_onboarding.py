from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pwd
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from emrys import __main__ as cli
from emrys.evidence.runtime_availability.inspector import load_runtime_profile_contract
from emrys.orchestration.local_pilot import doctor, onboarding, synthetic_fixture
from emrys.orchestration.local_pilot.launcher_config import BATCH_MARKER

REPO_ROOT = Path(__file__).resolve().parents[3]


def _namespace(output: Path, *, execute: bool) -> argparse.Namespace:
    return argparse.Namespace(output_dir=output, execute=execute)


def _publish_synthetic(output: Path) -> None:
    assert synthetic_fixture.init_from_args(_namespace(output, execute=True)) == 0


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _executable(path: Path, content: str = "#!/bin/sh\nexit 0\n") -> Path:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_init_local_pilot_is_dry_run_first_and_receipt_last(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "starter"
    assert onboarding.init_from_args(_namespace(output, execute=False)) == 0
    assert not output.exists()
    assert "Dry-run complete" in capsys.readouterr().out

    assert onboarding.init_from_args(_namespace(output, execute=True)) == 0
    expected = {
        "request.yaml",
        "emrys.launcher.yaml",
        "emrys.resources.yaml",
        "samples.tsv",
        "partitions.tsv",
        "runtime.tsv",
        "run-in-slurm.sh",
        "starter-set.manifest.tsv",
    }
    assert set(_tree_bytes(output)) == expected
    assert stat.S_IMODE((output / "run-in-slurm.sh").stat().st_mode) == 0o755
    rows = list(
        csv.DictReader(
            (output / "starter-set.manifest.tsv").open(encoding="utf-8"),
            delimiter="\t",
        )
    )
    assert [row["path"] for row in rows] == sorted(
        expected - {"starter-set.manifest.tsv"}
    )
    for row in rows:
        data = (output / row["path"]).read_bytes()
        assert int(row["size_bytes"]) == len(data)
        assert row["sha256"] == hashlib.sha256(data).hexdigest()
    request = (output / "request.yaml").read_text(encoding="utf-8")
    assert "sample_manifest: samples.tsv" in request
    assert "partition_manifest: partitions.tsv" in request
    launcher = yaml.safe_load(
        (output / "emrys.launcher.yaml").read_text(encoding="utf-8")
    )
    assert launcher["schema_version"] == "emrys.local-pilot-launcher.v1"
    assert "execute" not in launcher
    assert launcher["slurm"]["exclusive"] is False
    assert launcher["paths"]["request"] == "request.yaml"
    assert launcher["paths"]["runtime_profile"] == "runtime.selected.tsv"
    assert launcher["modules"] == {"mode": "none", "init": "", "load": []}
    assert not (output / ".env").exists()
    assert not (output / ".env.example").exists()


def test_init_refuses_predecessor_without_changing_it(tmp_path: Path) -> None:
    output = tmp_path / "starter"
    output.mkdir()
    predecessor = output / "owned.txt"
    predecessor.write_bytes(b"preserve me\n")

    assert onboarding.init_from_args(_namespace(output, execute=True)) == 2
    assert _tree_bytes(output) == {"owned.txt": b"preserve me\n"}


def test_synthetic_init_is_dry_run_first_and_refuses_predecessor(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "fixture"

    assert synthetic_fixture.init_from_args(_namespace(output, execute=False)) == 0
    assert not output.exists()
    assert "Dry-run complete" in capsys.readouterr().out

    output.mkdir()
    predecessor = output / "owned.txt"
    predecessor.write_bytes(b"preserve me\n")

    assert synthetic_fixture.init_from_args(_namespace(output, execute=True)) == 2
    captured = capsys.readouterr()
    assert "output directory must be absent" in captured.err
    assert _tree_bytes(output) == {"owned.txt": b"preserve me\n"}


def test_publication_re_admits_every_member_after_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "publication"
    real_write = onboarding._write_member

    def write_then_tamper(path: Path, data: bytes, mode: int) -> None:
        real_write(path, data, mode)
        if path.name == "complete.tsv":
            (path.parent / "request.yaml").write_bytes(b"changed after preparation\n")

    monkeypatch.setattr(onboarding, "_write_member", write_then_tamper)
    members = {"request.yaml": (b"original\n", 0o644)}

    with pytest.raises(
        onboarding.OnboardingError, match="member bytes changed"
    ) as failure:
        onboarding.publish_create_absent_tree(
            output,
            members,
            completion_name="complete.tsv",
            completion_bytes=b"complete\n",
        )

    assert "present-but-invalid" in str(failure.value)
    assert "presence alone is not completion proof" in str(failure.value)
    assert (output / "complete.tsv").is_file()
    assert (output / "request.yaml").read_bytes() == b"changed after preparation\n"


@pytest.mark.parametrize(
    "unsafe_name", ("../escape", "/absolute", "bad\\name", "bad\nname")
)
def test_publication_rejects_unsafe_member_paths(
    tmp_path: Path,
    unsafe_name: str,
) -> None:
    output = tmp_path / "publication"
    with pytest.raises(onboarding.OnboardingError, match="unsafe publication member"):
        onboarding.publish_create_absent_tree(
            output,
            {unsafe_name: (b"unsafe\n", 0o644)},
            completion_name="complete.tsv",
            completion_bytes=b"complete\n",
        )
    assert not output.exists()


def test_init_requires_an_absolute_external_output(tmp_path: Path) -> None:
    assert onboarding.init_from_args(_namespace(Path("relative"), execute=True)) == 2
    assert (
        onboarding.init_from_args(
            _namespace(REPO_ROOT / "forbidden-output", execute=True)
        )
        == 2
    )


def test_synthetic_fixture_is_deterministic_complete_and_normalizable(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _publish_synthetic(first)
    _publish_synthetic(second)

    assert _tree_bytes(first) == _tree_bytes(second)
    result = onboarding.validate_local_pilot_request(first / "request.yaml")
    assert result.sample_count == 4
    assert result.pair_count == 2
    assert result.partition_count == 1
    assert result.fasta_contigs == (("chrSynthetic", 100_000),)
    assert result.transcript_count == 2
    metadata = json.loads((first / "fixture.json").read_text(encoding="utf-8"))
    assert metadata["read_pairs_per_library"] == 130
    assert metadata["expected_terminal_computational_result"] == {
        "absolute_af_difference": 0.4375,
        "all_sites_rows": 3,
        "common_odds_ratio": 15.0,
        "control_af": 0.0625,
        "interpretation": "computational smoke expectation; not scientific adjudication",
        "significant_candidate_id": "REV_like|chrSynthetic|50000|A>G",
        "significant_sites_rows": 1,
        "treatment_af": 0.5,
    }
    manifest = json.loads((first / synthetic_fixture.COMPLETION_MANIFEST).read_text())
    assert set(manifest) == set(_tree_bytes(first)) - {
        synthetic_fixture.COMPLETION_MANIFEST
    }
    for relative, record in manifest.items():
        data = (first / relative).read_bytes()
        assert record["size_bytes"] == len(data)
        assert record["sha256"] == hashlib.sha256(data).hexdigest()


def test_synthetic_fastqs_have_complete_matching_mates(tmp_path: Path) -> None:
    import gzip

    output = tmp_path / "fixture"
    _publish_synthetic(output)
    for sample in synthetic_fixture.SAMPLES:
        sample_id = str(sample["sample_id"])
        with gzip.open(output / f"inputs/reads/{sample_id}_R1.fastq.gz", "rt") as r1:
            r1_lines = r1.read().splitlines()
        with gzip.open(output / f"inputs/reads/{sample_id}_R2.fastq.gz", "rt") as r2:
            r2_lines = r2.read().splitlines()
        assert (
            len(r1_lines)
            == len(r2_lines)
            == 4 * synthetic_fixture.PAIR_COUNT_PER_LIBRARY
        )
        assert [line.removesuffix("/1") for line in r1_lines[::4]] == [
            line.removesuffix("/2") for line in r2_lines[::4]
        ]
        assert all(len(sequence) == 75 for sequence in r1_lines[1::4])
        assert all(len(sequence) == 75 for sequence in r2_lines[1::4])


def test_request_validation_is_read_only(tmp_path: Path) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    before = _tree_bytes(output)

    assert (
        onboarding.validate_from_args(
            argparse.Namespace(request=output / "request.yaml")
        )
        == 0
    )

    assert _tree_bytes(output) == before


def test_request_validation_reports_invalid_request(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_request = tmp_path / "missing-request.yaml"

    assert (
        onboarding.validate_from_args(argparse.Namespace(request=missing_request)) == 1
    )
    assert "ERROR:" in capsys.readouterr().err


def test_public_cli_routes_synthetic_init_and_request_validation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "public-fixture"
    assert (
        cli.main(
            [
                "init",
                "synthetic-local-pilot",
                "--output-dir",
                str(output),
                "--execute",
            ]
        )
        == 0
    )
    assert (
        cli.main(
            [
                "validate",
                "local-pilot-request",
                "--request",
                str(output / "request.yaml"),
            ]
        )
        == 0
    )
    stdout = capsys.readouterr().out
    assert "Published deterministic local-pilot fixture" in stdout
    assert "Local-pilot request validation: PASS" in stdout


@pytest.mark.parametrize(
    ("target", "old", "new", "message"),
    (
        (
            "inputs/reference/genes.gtf",
            "chrSynthetic",
            "chrAbsent",
            "contig is absent from FASTA",
        ),
        (
            "partitions.tsv",
            "primary\tregion\tchrSynthetic",
            "primary\tregion\tchrSynthetic:99999-100001",
            "outside FASTA bounds",
        ),
    ),
)
def test_request_validation_rejects_reference_incompatibility(
    tmp_path: Path,
    target: str,
    old: str,
    new: str,
    message: str,
) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    path = output / target
    path.write_text(
        path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8"
    )

    with pytest.raises(onboarding.OnboardingError, match=message):
        onboarding.validate_local_pilot_request(output / "request.yaml")


def test_request_validation_checks_regions_file_against_fasta(tmp_path: Path) -> None:
    output = tmp_path / "fixture"
    _publish_synthetic(output)
    regions = output / "regions.tsv"
    regions.write_text("chrSynthetic\t1\t100000\n", encoding="utf-8")
    (output / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n"
        "primary\tregions_file\tregions.tsv\n",
        encoding="utf-8",
    )
    result = onboarding.validate_local_pilot_request(output / "request.yaml")
    assert result.partition_count == 1

    regions.write_text("chrAbsent\t1\t2\n", encoding="utf-8")
    with pytest.raises(onboarding.OnboardingError, match="absent from FASTA"):
        onboarding.validate_local_pilot_request(output / "request.yaml")


def test_request_validation_streams_gzip_regions_file(tmp_path: Path) -> None:
    import gzip

    output = tmp_path / "fixture"
    _publish_synthetic(output)
    regions = output / "regions.tsv.gz"
    with gzip.open(regions, "wt", encoding="utf-8", newline="") as handle:
        for start in range(1, 10_001):
            handle.write(f"chrSynthetic\t{start}\t{start}\n")
    (output / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\n"
        "primary\tregions_file\tregions.tsv.gz\n",
        encoding="utf-8",
    )

    result = onboarding.validate_local_pilot_request(output / "request.yaml")

    assert result.partition_count == 1


def _runtime_files(
    tmp_path: Path,
) -> tuple[dict[str, Path], Path, Path, Path, Path, Path]:
    tool_dir = tmp_path / "tools"
    tool_dir.mkdir()
    tools = {
        check_id: _executable(tool_dir / command)
        for check_id, command in onboarding.PATH_TOOL_COMMANDS.items()
    }
    java = _executable(tmp_path / "java")
    rscript = _executable(tmp_path / "Rscript")
    picard = tmp_path / "picard.jar"
    picard.write_bytes(b"synthetic jar\n")
    renv = tmp_path / "renv-library"
    renv.mkdir()
    return tools, tool_dir, java, rscript, picard, renv


def test_runtime_preparation_renders_fixed_policy_without_probes(
    tmp_path: Path,
) -> None:
    tools, tool_dir, java, rscript, picard, renv = _runtime_files(tmp_path)
    payload = onboarding.render_runtime_profile(
        java=java,
        picard_jar=picard,
        rscript=rscript,
        renv_library=renv,
        explicit_tools={check_id: None for check_id in tools},
        environment={"PATH": str(tool_dir)},
        root=REPO_ROOT,
        python_executable=Path(sys.executable),
    )
    rows = list(
        csv.DictReader(payload.decode().splitlines(), delimiter="\t", strict=True)
    )
    by_id = {row["check_id"]: row for row in rows}
    assert by_id["java"]["target"] == str(java)
    assert by_id["picard_jar"]["target"] == str(picard)
    assert by_id["renv_library"]["target"] == str(renv)
    assert json.loads(by_id["picard"]["probe_args"])[1] == str(picard)
    assert json.loads(by_id["r_variant_annotation"]["probe_args"]) == [str(rscript)]
    assert by_id["star"]["target"] == str(tools["star"])
    rendered = tmp_path / "runtime.tsv"
    rendered.write_bytes(payload)
    _profile_bytes, checks = load_runtime_profile_contract(rendered)
    doctor.validate_runtime_profile_contract(checks, REPO_ROOT)


def test_runtime_preparation_rejects_ambiguous_path_tool(tmp_path: Path) -> None:
    tools, first_dir, java, rscript, picard, renv = _runtime_files(tmp_path)
    second_dir = tmp_path / "second"
    second_dir.mkdir()
    _executable(second_dir / "STAR", "#!/bin/sh\nexit 99\n")
    explicit = {check_id: path for check_id, path in tools.items()}
    explicit["star"] = None

    with pytest.raises(onboarding.OnboardingError, match="multiple executables"):
        onboarding.render_runtime_profile(
            java=java,
            picard_jar=picard,
            rscript=rscript,
            renv_library=renv,
            explicit_tools=explicit,
            environment={"PATH": f"{first_dir}{os.pathsep}{second_dir}"},
            root=REPO_ROOT,
        )


def _wrapper_environment(
    tmp_path: Path,
    python: Path,
    module_init: Path,
) -> dict[str, str]:
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    scratch_parent = tmp_path / "scratch"
    scratch_parent.mkdir(exist_ok=True)
    live_uid = str(os.getuid())
    live_user = pwd.getpwuid(os.getuid()).pw_name
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "EMRYS_SUBMIT_UID": live_uid,
        "EMRYS_SUBMIT_USER": live_user,
        "USER": live_user,
        "LOGNAME": live_user,
        "EMRYS_SLURM_ACCOUNT": "test-account",
        "EMRYS_SLURM_PARTITION": "test-partition",
        "EMRYS_SLURM_QOS": "test-qos",
        "EMRYS_SLURM_CPUS": "4",
        "EMRYS_SLURM_MEMORY": "8G",
        "EMRYS_SLURM_TIME": "00:30:00",
        "EMRYS_SLURM_EXCLUSIVE": "0",
        "EMRYS_SLURM_NODELIST": "",
        "EMRYS_LOG_DIR": str(log_dir),
        "EMRYS_SOURCE_CHECKOUT": str(tmp_path / "checkout"),
        "EMRYS_PYTHON": str(python),
        "EMRYS_REQUEST": str(tmp_path / "request.yaml"),
        "EMRYS_WORKSPACE": str(tmp_path / "workspace"),
        "EMRYS_RUNTIME_PROFILE": str(tmp_path / "runtime.tsv"),
        "EMRYS_MODULE_MODE": "exact",
        "EMRYS_MODULE_INIT": str(module_init),
        "EMRYS_MODULES": "java/17.0.10:star/2.7.11b:samtools/1.19.2",
        "EMRYS_SCRATCH_PARENT": str(scratch_parent),
        "EMRYS_EXECUTE": "1",
    }


def _write_slurm_wrapper(tmp_path: Path) -> Path:
    source_checkout = tmp_path / "launcher-source"
    config_directory = source_checkout / "configs"
    config_directory.mkdir(parents=True)
    for name in (
        "local_pilot_launcher.example.yaml",
        "local_pilot_partitions.example.tsv",
        "local_pilot_request.example.yaml",
        "local_pilot_resources.example.yaml",
        "local_pilot_runtime.example.tsv",
        "local_pilot_samples.example.tsv",
    ):
        template = REPO_ROOT / "configs" / name
        (config_directory / name).write_bytes(template.read_bytes())
    members = onboarding.starter_members(
        root=source_checkout,
        python_executable=Path(sys.executable),
    )
    wrapper = tmp_path / "run-in-slurm.sh"
    wrapper.write_bytes(members["run-in-slurm.sh"][0])
    wrapper.chmod(0o755)
    launcher_member = members.get("emrys.launcher.yaml")
    if launcher_member is not None:
        (tmp_path / "emrys.launcher.yaml").write_bytes(launcher_member[0])
    return wrapper


def test_starter_rejects_python_parent_unsafe_for_sealed_path(
    tmp_path: Path,
) -> None:
    unsafe_parent = tmp_path / "unsafe:python-parent"
    unsafe_parent.mkdir()
    unsafe_python = _executable(unsafe_parent / "python")

    with pytest.raises(onboarding.OnboardingError, match="sealed PATH"):
        onboarding.starter_members(
            root=REPO_ROOT,
            python_executable=unsafe_python,
        )


def test_starter_preserves_a_lexical_virtualenv_python_launcher(
    tmp_path: Path,
) -> None:
    target = _executable(tmp_path / "python-target")
    launcher_parent = tmp_path / "venv" / "bin"
    launcher_parent.mkdir(parents=True)
    launcher = launcher_parent / "python"
    launcher.symlink_to(target)

    members = onboarding.starter_members(
        root=REPO_ROOT,
        python_executable=launcher,
    )

    wrapper = members["run-in-slurm.sh"][0].decode("utf-8")
    assert str(launcher) in wrapper
    assert str(target) not in wrapper


def _write_launcher_config(
    path: Path,
    tmp_path: Path,
    *,
    memory: str = "8G",
    exclusive: bool = False,
    nodelist: str | None = None,
) -> None:
    request = tmp_path / "request.yaml"
    runtime_profile = tmp_path / "runtime.tsv"
    request.touch()
    runtime_profile.touch()
    launcher = {
        "log_dir": tmp_path / "logs",
        "request": request,
        "workspace": tmp_path / "workspace",
        "runtime_profile": runtime_profile,
        "scratch_parent": tmp_path / "scratch",
    }
    path.write_text(
        "schema_version: emrys.local-pilot-launcher.v1\n"
        "slurm:\n"
        "  account: test-account\n"
        "  partition: test-partition\n"
        "  qos: test-qos\n"
        "  cpus_per_task: 4\n"
        f"  memory: {memory}\n"
        "  time: '00:30:00'\n"
        f"  exclusive: {'true' if exclusive else 'false'}\n"
        f"  nodelist: {json.dumps(nodelist)}\n"
        "paths:\n"
        f"  log_dir: {json.dumps(str(launcher['log_dir']))}\n"
        f"  request: {json.dumps(str(launcher['request']))}\n"
        f"  workspace: {json.dumps(str(launcher['workspace']))}\n"
        f"  runtime_profile: {json.dumps(str(launcher['runtime_profile']))}\n"
        f"  scratch_parent: {json.dumps(str(launcher['scratch_parent']))}\n"
        "modules:\n"
        "  mode: none\n"
        "  init: ''\n"
        "  load: []\n",
        encoding="utf-8",
    )


def _submit_with_launcher_config(
    tmp_path: Path,
    *,
    execute: bool,
    memory: str = "8G",
    exclusive: bool = False,
    nodelist: str | None = None,
    ambient_execute: str = "1",
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    wrapper = _write_slurm_wrapper(tmp_path)
    launcher_config = tmp_path / "selected-launcher.yaml"
    _write_launcher_config(
        launcher_config,
        tmp_path,
        memory=memory,
        exclusive=exclusive,
        nodelist=nodelist,
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    capture = tmp_path / "sbatch.args"
    _executable(
        bin_dir / "sbatch",
        "#!/bin/bash\n"
        "if [[ -n \"${SBATCH_EXCLUSIVE+x}${SBATCH_NODELIST+x}${SBATCH_MEM+x}\" || "
        "-n \"${SBATCH_WAIT+x}${EMRYS_EXECUTE+x}\" ]]; then exit 9; fi\n"
        "printf '%s\\n' \"$@\" > \"$LAUNCHER_CAPTURE\"\n"
        "printf '700123\\n'\n",
    )
    module_init = tmp_path / "modules.sh"
    module_init.write_text("module() { :; }\n", encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, Path(sys.executable), module_init)
    environment.update(
        {
            "PATH": f"{bin_dir}:{environment['PATH']}",
            "LAUNCHER_CAPTURE": str(capture),
            "EMRYS_EXECUTE": ambient_execute,
            "SBATCH_EXCLUSIVE": "1",
            "SBATCH_NODELIST": "ambient-node",
            "SBATCH_MEM": "1T",
            "SBATCH_WAIT": "1",
        }
    )
    command = [str(wrapper), "--launcher-config", str(launcher_config)]
    if execute:
        command.append("--execute")

    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    arguments = (
        capture.read_text(encoding="utf-8").splitlines()
        if capture.exists()
        else []
    )
    return result, arguments


@pytest.mark.parametrize(
    ("execute", "expected_execute"),
    ((False, "0"), (True, "1")),
)
def test_slurm_wrapper_execute_is_an_explicit_cli_gate(
    tmp_path: Path,
    execute: bool,
    expected_execute: str,
) -> None:
    result, arguments = _submit_with_launcher_config(
        tmp_path,
        execute=execute,
        ambient_execute="1",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    export_arguments = [
        argument for argument in arguments if argument.startswith("--export=")
    ]
    assert len(export_arguments) == 1
    export_fields = export_arguments[0].removeprefix("--export=").split(",")
    assert f"EMRYS_EXECUTE={expected_execute}" in export_fields
    unexpected_execute = "1" if expected_execute == "0" else "0"
    assert f"EMRYS_EXECUTE={unexpected_execute}" not in export_fields


def test_submission_strips_ambient_sbatch_policy_variables(
    tmp_path: Path,
) -> None:
    result, arguments = _submit_with_launcher_config(
        tmp_path,
        execute=False,
        memory="site-default",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "--exclusive" not in arguments
    assert not any(argument.startswith("--nodelist=") for argument in arguments)
    assert not any(argument.startswith("--mem=") for argument in arguments)


@pytest.mark.parametrize(
    ("exclusive", "nodelist", "expected_placement"),
    (
        (False, None, []),
        (
            True,
            "compute-test[01-02]",
            ["--exclusive", "--nodelist=compute-test[01-02]"],
        ),
    ),
)
def test_slurm_wrapper_uses_resolved_placement_settings(
    tmp_path: Path,
    exclusive: bool,
    nodelist: str | None,
    expected_placement: list[str],
) -> None:
    result, arguments = _submit_with_launcher_config(
        tmp_path,
        execute=False,
        exclusive=exclusive,
        nodelist=nodelist,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "--account=test-account" in arguments
    assert "--partition=test-partition" in arguments
    assert "--qos=test-qos" in arguments
    placement = [
        argument
        for argument in arguments
        if argument == "--exclusive" or argument.startswith("--nodelist=")
    ]
    assert placement == expected_placement


@pytest.mark.parametrize(
    ("memory", "expected_memory_argument"),
    (("8G", "--mem=8G"), ("site-default", None)),
)
def test_slurm_wrapper_head_mode_only_submits_and_prints_tail(
    tmp_path: Path,
    memory: str,
    expected_memory_argument: str | None,
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    capture = tmp_path / "sbatch.args"
    sbatch = _executable(
        bin_dir / "sbatch",
        "#!/bin/bash\nprintf '%s\\n' \"$@\" > \"$LAUNCHER_CAPTURE\"\nprintf '700123\\n'\n",
    )
    assert sbatch.is_file()
    fake_python = _executable(tmp_path / "python", '#!/bin/sh\ntouch "$PYTHON_RAN"\n')
    module_init = tmp_path / "modules.sh"
    module_init.write_text('touch "$MODULE_INIT_RAN"\n', encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment["EMRYS_SLURM_MEMORY"] = memory
    environment["PATH"] = f"{bin_dir}:/hostile/ambient:{environment['PATH']}"
    environment["LAUNCHER_CAPTURE"] = str(capture)
    environment["PYTHON_RAN"] = str(tmp_path / "python-ran")
    environment["MODULE_INIT_RAN"] = str(tmp_path / "module-init-ran")

    result = subprocess.run(
        [str(wrapper), "--memory", memory],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "JOB_ID=700123" in result.stdout
    assert "while [[ ! -e" in result.stdout
    assert "squeue -j 700123" in result.stdout
    assert "tail -n +1 -F" in result.stdout
    assert "emrys-local-pilot-700123.out" in result.stdout
    assert not (tmp_path / "python-ran").exists()
    assert not (tmp_path / "module-init-ran").exists()
    arguments = capture.read_text(encoding="utf-8").splitlines()
    assert "" not in arguments
    assert "--account=test-account" in arguments
    assert "--partition=test-partition" in arguments
    assert "--qos=test-qos" in arguments
    assert "--nodes=1" in arguments
    assert "--ntasks=1" in arguments
    memory_arguments = [
        argument for argument in arguments if argument.startswith("--mem=")
    ]
    assert memory_arguments == (
        [] if expected_memory_argument is None else [expected_memory_argument]
    )
    export_arguments = [
        argument for argument in arguments if argument.startswith("--export=")
    ]
    assert len(export_arguments) == 1
    export_fields = export_arguments[0].removeprefix("--export=").split(",")
    bound_python = Path(os.path.abspath(sys.executable))
    assert export_fields[0] == f"PATH={bound_python.parent}:/usr/bin:/bin"
    assert str(bin_dir) not in export_fields[0]
    assert "/hostile/ambient" not in export_fields[0]
    assert "EMRYS_SLURM_CPUS=4" in export_fields
    assert f"EMRYS_SUBMIT_UID={os.getuid()}" in export_fields
    assert f"EMRYS_SUBMIT_USER={pwd.getpwuid(os.getuid()).pw_name}" in export_fields
    assert f"USER={pwd.getpwuid(os.getuid()).pw_name}" in export_fields
    assert f"LOGNAME={pwd.getpwuid(os.getuid()).pw_name}" in export_fields
    assert "EMRYS_MODULE_MODE=none" in export_fields
    assert f"EMRYS_SCRATCH_PARENT={tmp_path / 'scratch'}" in export_fields
    assert f"EMRYS_PYTHON={bound_python}" in export_fields
    assert not any(field.startswith("EMRYS_TOOL_THREADS=") for field in export_fields)
    assert not any(
        field.startswith("EMRYS_SAMPLE_CONCURRENCY=") for field in export_fields
    )
    assert arguments[-2:] == [str(wrapper), BATCH_MARKER]


@pytest.mark.parametrize("python_path_kind", ("relative", "root", "colon"))
def test_slurm_wrapper_ignores_ambient_python_selection_before_submission(
    tmp_path: Path,
    python_path_kind: str,
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    submitted = tmp_path / "submitted"
    capture = tmp_path / "sbatch.args"
    _executable(
        bin_dir / "sbatch",
        "#!/bin/sh\ntouch \"$SUBMITTED\"\n"
        "printf '%s\\n' \"$@\" > \"$LAUNCHER_CAPTURE\"\n"
        "printf '700123\\n'\n",
    )
    fake_python = _executable(tmp_path / "python")
    module_init = tmp_path / "modules.sh"
    module_init.write_text("module() { :; }\n", encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment["PATH"] = f"{bin_dir}:{environment['PATH']}"
    environment["SUBMITTED"] = str(submitted)
    environment["LAUNCHER_CAPTURE"] = str(capture)
    environment["EMRYS_LAUNCHER_SOURCE_CHECKOUT"] = "/caller/source"
    environment["EMRYS_LAUNCHER_PYTHON"] = "/caller/python"
    environment["EMRYS_PYTHON"] = {
        "relative": "relative/python",
        "root": "/python",
        "colon": f"{tmp_path}/unsafe:directory/python",
    }[python_path_kind]

    result = subprocess.run(
        [str(wrapper)],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert submitted.exists()
    arguments = capture.read_text(encoding="utf-8").splitlines()
    export_argument = next(
        argument for argument in arguments if argument.startswith("--export=")
    )
    export_fields = export_argument.removeprefix("--export=").split(",")
    assert f"EMRYS_PYTHON={Path(os.path.abspath(sys.executable))}" in export_fields
    assert f"EMRYS_SOURCE_CHECKOUT={tmp_path / 'launcher-source'}" in export_fields


@pytest.mark.parametrize("unsafe", ("bad,value", "bad\nvalue"))
def test_slurm_wrapper_rejects_unsafe_export_values(
    tmp_path: Path,
    unsafe: str,
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    fake_python = _executable(tmp_path / "python")
    module_init = tmp_path / "modules.sh"
    module_init.write_text("module() { :; }\n", encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)

    result = subprocess.run(
        [str(wrapper), "--request", unsafe],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert result.returncode == 2
    assert "unsafe" in result.stderr


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("USER", None),
        ("LOGNAME", None),
        ("USER", "different-user"),
        ("LOGNAME", "different-user"),
        ("USER", "bad,user"),
        ("LOGNAME", "bad\nuser"),
    ),
)
def test_slurm_wrapper_rejects_unbound_submit_identity_before_submission(
    tmp_path: Path,
    name: str,
    value: str | None,
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    submitted = tmp_path / "submitted"
    _executable(bin_dir / "sbatch", '#!/bin/sh\ntouch "$SUBMITTED"\n')
    fake_python = _executable(tmp_path / "python")
    module_init = tmp_path / "modules.sh"
    module_init.write_text("module() { :; }\n", encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment["PATH"] = f"{bin_dir}:{environment['PATH']}"
    environment["SUBMITTED"] = str(submitted)
    if value is None:
        environment.pop(name)
    else:
        environment[name] = value

    result = subprocess.run(
        [str(wrapper)],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 2
    assert not submitted.exists()


@pytest.mark.parametrize(
    ("option", "value"),
    (
        ("--module-mode", "excat"),
        ("--memory", "site-defualt"),
    ),
)
def test_slurm_wrapper_rejects_invalid_portability_overrides(
    tmp_path: Path,
    option: str,
    value: str,
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    submitted = tmp_path / "submitted"
    _executable(bin_dir / "sbatch", '#!/bin/sh\ntouch "$SUBMITTED"\n')
    fake_python = _executable(tmp_path / "python")
    module_init = tmp_path / "modules.sh"
    module_init.write_text("module() { :; }\n", encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment["PATH"] = f"{bin_dir}:{environment['PATH']}"
    environment["SUBMITTED"] = str(submitted)

    result = subprocess.run(
        [str(wrapper), option, value],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 2
    assert not submitted.exists()


@pytest.mark.parametrize("module_mode", ("exact", "none"))
def test_slurm_wrapper_batch_mode_handles_modules_then_doctors_and_runs(
    tmp_path: Path,
    module_mode: str,
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    module_capture = tmp_path / "modules.log"
    python_capture = tmp_path / "python.log"
    allocation_capture = tmp_path / "allocation.log"
    module_init = tmp_path / "modules.sh"
    module_init.write_text(
        'printf \'source\\n\' >> "$MODULE_CAPTURE"\n'
        'module() { printf \'%s\\n\' "$*" >> "$MODULE_CAPTURE"; }\n',
        encoding="utf-8",
    )
    fake_python = _executable(
        tmp_path / "python",
        '#!/bin/bash\n'
        'printf \'%s\\n\' "$*" >> "$PYTHON_CAPTURE"\n'
        "printf '%s|%s|%s|%s\\n' "
        '"$SLURM_JOB_ID" "$SLURM_CPUS_PER_TASK" '
        '"$SLURM_MEM_PER_NODE" "${SLURM_MEM_PER_CPU-}" '
        '>> "$ALLOCATION_CAPTURE"\n',
    )
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    scratch_sentinel = tmp_path / "scratch" / "sibling-sentinel"
    scratch_sentinel.write_text("preserve\n", encoding="utf-8")
    environment.update(
        {
            "SLURM_JOB_ID": "700123",
            "SLURM_CPUS_PER_TASK": "4",
            "SLURM_MEM_PER_NODE": "8192",
            "MODULE_CAPTURE": str(module_capture),
            "PYTHON_CAPTURE": str(python_capture),
            "ALLOCATION_CAPTURE": str(allocation_capture),
        }
    )
    if module_mode == "none":
        environment.update(
            {
                "EMRYS_MODULE_MODE": "none",
                "EMRYS_MODULE_INIT": "",
                "EMRYS_MODULES": "",
            }
        )

    result = subprocess.run(
        [str(wrapper), BATCH_MARKER],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    observed_modules = (
        module_capture.read_text(encoding="utf-8").splitlines()
        if module_capture.exists()
        else []
    )
    expected_modules = (
        [
            "source",
            "load java/17.0.10",
            "load star/2.7.11b",
            "load samtools/1.19.2",
        ]
        if module_mode == "exact"
        else []
    )
    assert observed_modules == expected_modules
    assert f"EMRYS_SCRATCH_PARENT={tmp_path / 'scratch'}" in result.stdout
    assert f"TMPDIR={tmp_path / 'scratch'}/emrys-700123." in result.stdout
    assert "TMPDIR filesystem and capacity:" in result.stdout
    assert list((tmp_path / "scratch").iterdir()) == [scratch_sentinel]
    assert scratch_sentinel.read_text(encoding="utf-8") == "preserve\n"
    invocations = python_capture.read_text(encoding="utf-8").splitlines()
    assert len(invocations) == 3
    assert allocation_capture.read_text(encoding="utf-8").splitlines() == [
        "700123|4|8192|",
        "700123|4|8192|",
        "700123|4|8192|",
    ]
    assert "-m emrys validate local-pilot-request" in invocations[0]
    assert "-m emrys doctor local-pilot" in invocations[1]
    assert "-m emrys run" in invocations[2]
    assert "--allocated-cores" not in invocations[2]
    assert "--threads" not in invocations[2]
    assert "--workflow-cores" not in invocations[2]
    assert "--sample-concurrency" not in invocations[2]
    assert invocations[2].endswith("--execute")


@pytest.mark.parametrize("arguments", ((), (BATCH_MARKER, "unexpected")))
def test_slurm_wrapper_rejects_ambient_batch_mode_without_exact_marker(
    tmp_path: Path,
    arguments: tuple[str, ...],
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    python_capture = tmp_path / "python.log"
    fake_python = _executable(
        tmp_path / "python",
        '#!/bin/sh\ntouch "$PYTHON_CAPTURE"\n',
    )
    module_init = tmp_path / "modules.sh"
    module_init.write_text("module() { :; }\n", encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment.update(
        {
            "SLURM_JOB_ID": "700123",
            "PYTHON_CAPTURE": str(python_capture),
            "EMRYS_EXECUTE": "1",
        }
    )

    result = subprocess.run(
        [str(wrapper), *arguments],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 2
    assert "batch marker" in result.stderr
    assert not python_capture.exists()


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("EMRYS_SUBMIT_UID", "999999"),
        ("EMRYS_SUBMIT_USER", "different-user"),
        ("USER", "different-user"),
        ("LOGNAME", "different-user"),
    ),
)
def test_slurm_wrapper_batch_mode_rejects_scheduler_identity_drift(
    tmp_path: Path,
    name: str,
    value: str,
) -> None:
    wrapper = _write_slurm_wrapper(tmp_path)
    python_capture = tmp_path / "python.log"
    fake_python = _executable(
        tmp_path / "python",
        '#!/bin/sh\ntouch "$PYTHON_CAPTURE"\n',
    )
    module_capture = tmp_path / "module.log"
    module_init = tmp_path / "modules.sh"
    module_init.write_text('touch "$MODULE_CAPTURE"\n', encoding="utf-8")
    (tmp_path / "checkout").mkdir()
    environment = _wrapper_environment(tmp_path, fake_python, module_init)
    environment.update(
        {
            "SLURM_JOB_ID": "700123",
            "PYTHON_CAPTURE": str(python_capture),
            "MODULE_CAPTURE": str(module_capture),
            name: value,
        }
    )

    result = subprocess.run(
        [str(wrapper), BATCH_MARKER],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert result.returncode == 2
    assert "identity" in result.stderr
    assert not module_capture.exists()
    assert not python_capture.exists()
    assert not any(
        path.name.startswith("emrys-700123.")
        for path in (tmp_path / "scratch").iterdir()
    )
