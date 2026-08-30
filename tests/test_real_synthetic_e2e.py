"""Fast parser and direct-oracle contracts for the retained real E2E driver."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from tests.tools import real_synthetic_e2e as DRIVER


def _plan_text(workspace: Path) -> str:
    return "\n".join(
        (
            "Run ID: run-" + "a" * 64,
            f"Run root: {workspace}/runs/run-{'a' * 64}",
            "Work: 35 pending, 0 reusable",
            "Resources: 1 cores, 6144 MiB",
            "Reporting: automatic after scientific work",
            "Dry-run complete; no workspace state was written.",
        )
    )


def test_parser_exposes_only_explicit_profiles_and_external_runtime_inputs() -> None:
    parser = DRIVER.build_parser()
    arguments = parser.parse_args(
        [
            "--profile",
            "100000",
            "--repo-root",
            "/repo",
            "--operator-root",
            "/operator",
            "--runtime-prefix",
            "/runtime",
            "--rscript",
            "/runtime/Rscript",
            "--renv-library",
            "/runtime/renv",
            "--storage-compute-launcher-json",
            '["/usr/bin/srun","--partition=emrys-ci"]',
            "--slurm-partition",
            "emrys-ci",
        ]
    )

    assert arguments.profile == "100000"
    assert DRIVER.PROFILE_DATASETS[arguments.profile] == "production-like-v1"
    assert arguments.slurm_account is None
    assert arguments.slurm_qos is None
    assert arguments.slurm_cpus == 4
    assert arguments.slurm_memory == 8192
    assert arguments.execute is False

    selected = parser.parse_args(
        [
            "--profile",
            "130",
            "--repo-root",
            "/repo",
            "--operator-root",
            "/operator",
            "--runtime-prefix",
            "/runtime",
            "--rscript",
            "/runtime/Rscript",
            "--renv-library",
            "/runtime/renv",
            "--storage-compute-launcher-json",
            '["/usr/bin/srun"]',
            "--slurm-partition",
            "emrys-ci",
            "--slurm-memory",
            "6G",
        ]
    )
    assert selected.slurm_memory == 6144

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--profile",
                "unexpected",
                "--repo-root",
                "/repo",
                "--operator-root",
                "/operator",
            ]
        )


def test_storage_launcher_is_one_explicit_no_shell_argv(tmp_path: Path) -> None:
    launcher = tmp_path / "srun"
    launcher.write_text("#!/bin/sh\n", encoding="utf-8")
    launcher.chmod(0o755)

    assert DRIVER.parse_launcher_prefix(
        json.dumps([str(launcher), "--nodes=1", "--ntasks=1"])
    ) == (str(launcher), "--nodes=1", "--ntasks=1")

    with pytest.raises(DRIVER.DriverError, match="string array"):
        DRIVER.parse_launcher_prefix(json.dumps(str(launcher)))
    with pytest.raises(DRIVER.DriverError, match="control character"):
        DRIVER.parse_launcher_prefix(json.dumps([str(launcher), "bad\nargument"]))


def test_slurm_profile_reuses_admitted_synthetic_resources(tmp_path: Path) -> None:
    from emrys.orchestration.local_pilot import synthetic_fixture
    from emrys.orchestration.local_pilot.execution_profile import (
        SlurmPlacement,
        load_execution_profile,
    )

    request = tmp_path / "project.yaml"
    request.write_text("fixture request\n", encoding="utf-8")
    direct_path = tmp_path / "emrys.execution.yaml"
    direct_path.write_bytes(synthetic_fixture._execution_profile())
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    rendered = DRIVER.slurm_execution_profile_bytes(
        request,
        direct_path,
        account=None,
        partition="emrys-ci",
        qos=None,
        cpus_per_task=2,
        memory_mb=6144,
        time_limit="02:00:00",
        nodelist=None,
        scratch_parent=scratch,
    )
    slurm_path = tmp_path / "emrys.execution.slurm.json"
    slurm_path.write_bytes(rendered)
    direct = load_execution_profile(request, config_path=direct_path)
    slurm = load_execution_profile(request, config_path=slurm_path)

    assert slurm.resource_policy.document() == direct.resource_policy.document()
    assert isinstance(slurm.placement, SlurmPlacement)
    assert slurm.placement.partition == "emrys-ci"
    assert slurm.placement.cpus_per_task == 2
    assert slurm.placement.memory_mb == 6144
    assert slurm.placement.scratch_parent == scratch


def test_workflow_python_preserves_lexical_virtualenv_launcher(tmp_path: Path) -> None:
    target = tmp_path / "runtime" / "python3"
    target.parent.mkdir()
    target.write_text("#!/bin/sh\n", encoding="utf-8")
    target.chmod(0o755)
    launcher = tmp_path / "repo" / ".venv" / "bin" / "python"
    launcher.parent.mkdir(parents=True)
    launcher.symlink_to(target)

    assert DRIVER._lexical_executable(launcher, "workflow Python") == launcher
    assert launcher.resolve(strict=True) == target


def test_runtime_paths_admit_the_locked_picard_slim_layout(tmp_path: Path) -> None:
    prefix = tmp_path / "runtime"
    bin_dir = prefix / "bin"
    bin_dir.mkdir(parents=True)
    for tool in (
        "STAR",
        "samtools",
        "gatk",
        "bcftools",
        "python",
        "infer_experiment.py",
        "gunzip",
        "java",
    ):
        executable = bin_dir / tool
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        executable.chmod(0o755)
    picard_jar = prefix / "share" / "picard-slim-3.1.1-0" / "picard.jar"
    picard_jar.parent.mkdir(parents=True)
    picard_jar.write_bytes(b"locked picard jar fixture\n")
    rscript = tmp_path / "Rscript"
    rscript.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    rscript.chmod(0o755)
    renv_library = tmp_path / "renv-library"
    renv_library.mkdir()

    observed = DRIVER.resolve_runtime_paths(prefix, rscript, renv_library)

    assert observed.picard_jar == picard_jar


def test_gatk_adapter_binds_exact_python_java_and_forwarded_args(
    tmp_path: Path,
) -> None:
    runtime_python = tmp_path / "runtime" / "bin" / "python"
    runtime_python.parent.mkdir(parents=True)
    python_marker = tmp_path / "python-argv.txt"
    runtime_python.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$@\" > {shlex.quote(str(python_marker))}\n"
        f'exec {shlex.quote(sys.executable)} "$@"\n',
        encoding="utf-8",
    )
    runtime_python.chmod(0o755)

    selected_home = tmp_path / "runtime" / "java-home"
    selected_java = selected_home / "bin" / "java"
    selected_java.parent.mkdir(parents=True)
    selected_java.write_text(
        "#!/bin/sh\n"
        "printf 'selected-java\\n%s\\n' \"$#\"\n"
        'for argument in "$@"; do\n'
        "    printf '<%s>\\n' \"$argument\"\n"
        "done\n",
        encoding="utf-8",
    )
    selected_java.chmod(0o755)
    poison_home = tmp_path / "poison-java-home"
    poison_java = poison_home / "bin" / "java"
    poison_java.parent.mkdir(parents=True)
    poison_java.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
    poison_java.chmod(0o755)

    delegate = tmp_path / "runtime" / "share" / "gatk" / "gatk"
    delegate.parent.mkdir(parents=True)
    delegate.write_text(
        "import json, os, shutil, subprocess, sys\n"
        "probe = subprocess.run(\n"
        "    ['java', 'identity', 'two words'],\n"
        "    check=False, capture_output=True, text=True,\n"
        ")\n"
        "selectors = (\n"
        "    'CLASSPATH', 'GATK_GCS_STAGING', 'GATK_JAR', 'GATK_LOCAL_JAR',\n"
        "    'GATK_SPARK_JAR', 'GCLOUD_HOME', 'JAVA_OPTS', 'JAVA_TOOL_OPTIONS',\n"
        "    'JDK_JAVA_OPTIONS', 'SPARK_HOME', '_JAVA_OPTIONS',\n"
        ")\n"
        "print(json.dumps({\n"
        "    'args': sys.argv[1:],\n"
        "    'dont_write_bytecode': sys.flags.dont_write_bytecode,\n"
        "    'isolated': sys.flags.isolated,\n"
        "    'java_home': os.environ.get('JAVA_HOME'),\n"
        "    'java_path': shutil.which('java'),\n"
        "    'path': os.environ.get('PATH'),\n"
        "    'probe': [probe.returncode, probe.stdout, probe.stderr],\n"
        "    'selectors': {name: os.environ.get(name, 'unset') for name in selectors},\n"
        "}))\n",
        encoding="utf-8",
    )
    delegate.chmod(0o755)

    first = DRIVER.gatk_adapter_bytes(runtime_python, delegate, selected_java)
    second = DRIVER.gatk_adapter_bytes(runtime_python, delegate, selected_java)
    adapter = tmp_path / "operator" / "runtime-adapters" / "gatk"
    adapter.parent.mkdir(parents=True)
    adapter.write_bytes(first)
    adapter.chmod(0o700)
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": f"{poison_java.parent}:/usr/bin:/bin",
            "JAVA_HOME": str(poison_home),
            "CLASSPATH": "/ambient/classes",
            "GATK_GCS_STAGING": "/ambient/gcs-staging",
            "GATK_JAR": "/ambient/gatk.jar",
            "GATK_LOCAL_JAR": "/ambient/local.jar",
            "GATK_SPARK_JAR": "/ambient/spark.jar",
            "GCLOUD_HOME": "/ambient/gcloud",
            "JAVA_OPTS": "-Dambient.opts=true",
            "JAVA_TOOL_OPTIONS": "-Dambient.tool.options=true",
            "JDK_JAVA_OPTIONS": "-Dambient.jdk.options=true",
            "SPARK_HOME": "/ambient/spark",
            "_JAVA_OPTIONS": "-Dambient.underscore.options=true",
        }
    )

    result = subprocess.run(
        (str(adapter), "one", "two words"),
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert first == second
    assert result.returncode == 0
    assert result.stderr == ""
    assert python_marker.read_text(encoding="utf-8").splitlines() == [
        "-I",
        "-B",
        str(delegate),
        "one",
        "two words",
    ]
    assert json.loads(result.stdout) == {
        "args": ["one", "two words"],
        "dont_write_bytecode": 1,
        "isolated": 1,
        "java_home": str(selected_home),
        "java_path": str(selected_java),
        "path": f"{selected_java.parent}:/usr/bin:/bin",
        "probe": [
            0,
            "selected-java\n2\n<identity>\n<two words>\n",
            "",
        ],
        "selectors": {
            "CLASSPATH": "unset",
            "GATK_GCS_STAGING": "unset",
            "GATK_JAR": "unset",
            "GATK_LOCAL_JAR": "unset",
            "GATK_SPARK_JAR": "unset",
            "GCLOUD_HOME": "unset",
            "JAVA_OPTS": "unset",
            "JAVA_TOOL_OPTIONS": "unset",
            "JDK_JAVA_OPTIONS": "unset",
            "SPARK_HOME": "unset",
            "_JAVA_OPTIONS": "unset",
        },
    }


def test_gunzip_adapter_restores_decompression_after_symlink_resolution(
    tmp_path: Path,
) -> None:
    target = tmp_path / "bin" / "gzip"
    target.parent.mkdir()
    target.write_text(
        "#!/bin/sh\n"
        'if [ "$#" -eq 1 ] && [ "$1" = "--version" ]; then\n'
        "    printf '%s\\n' 'gzip test-version'\n"
        "    exit 0\n"
        "fi\n"
        'printf \'%s\\n\' "${0##*/}" "$#"\n'
        'for argument in "$@"; do\n'
        "    printf '<%s>\\n' \"$argument\"\n"
        "done\n",
        encoding="utf-8",
    )
    target.chmod(0o755)
    launcher = target.parent / "gunzip"
    launcher.symlink_to(target.name)

    delegate = DRIVER._canonical_file(launcher, "gunzip delegate", executable=True)
    first = DRIVER.gunzip_adapter_bytes(delegate)
    second = DRIVER.gunzip_adapter_bytes(delegate)
    adapter = tmp_path / "runtime-adapters" / "gunzip"
    adapter.parent.mkdir()
    adapter.write_bytes(first)
    adapter.chmod(0o700)

    version = subprocess.run(
        (str(adapter), "--version"), text=True, capture_output=True, check=False
    )
    delegated = subprocess.run(
        (str(adapter), "-c", "reads with space.fastq.gz"),
        text=True,
        capture_output=True,
        check=False,
    )

    assert delegate == target
    assert first == second
    assert (version.returncode, version.stdout, version.stderr) == (
        0,
        "gzip test-version\n",
        "",
    )
    assert (delegated.returncode, delegated.stdout, delegated.stderr) == (
        0,
        "gzip\n3\n<-d>\n<-c>\n<reads with space.fastq.gz>\n",
        "",
    )


def test_rseqc_adapter_has_exact_version_surface_and_delegates_other_args(
    tmp_path: Path,
) -> None:
    delegate = tmp_path / "delegate.py"
    delegate.write_text(
        "import json, sys\n"
        "print(json.dumps({"
        "'args': sys.argv[1:], "
        "'isolated': sys.flags.isolated, "
        "'dont_write_bytecode': sys.flags.dont_write_bytecode"
        "}))\n",
        encoding="utf-8",
    )
    adapter = tmp_path / "infer_experiment.py"
    first = DRIVER.rseqc_adapter_bytes(Path(sys.executable), delegate)
    second = DRIVER.rseqc_adapter_bytes(Path(sys.executable), delegate)
    assert first == second
    assert b"RSeQC 5.0.4" not in first
    assert b" -I -B " in first
    adapter.write_bytes(first)
    adapter.chmod(0o700)

    version = subprocess.run(
        (str(adapter), "--version"), text=True, capture_output=True, check=False
    )
    delegated = subprocess.run(
        (str(adapter), "one", "two words"),
        text=True,
        capture_output=True,
        check=False,
    )

    assert (version.returncode, version.stdout, version.stderr) == (
        0,
        "infer_experiment.py 5.0.4\n",
        "",
    )
    assert delegated.returncode == 0
    assert json.loads(delegated.stdout) == {
        "args": ["one", "two words"],
        "isolated": 1,
        "dont_write_bytecode": 1,
    }


def test_plan_parser_requires_current_work_and_reporting_contract(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    expected = workspace / "runs" / f"run-{'a' * 64}"

    assert (
        DRIVER.parse_run_plan(_plan_text(workspace), workspace, no_write=True)
        == expected
    )

    with pytest.raises(DRIVER.DriverError, match="expected 35 pending work items"):
        DRIVER.parse_run_plan(
            _plan_text(workspace).replace(
                "Work: 35 pending, 0 reusable", "Work: 34 pending, 1 reusable"
            ),
            workspace,
            no_write=True,
        )
    with pytest.raises(DRIVER.DriverError, match="no-write boundary"):
        DRIVER.parse_run_plan(
            _plan_text(workspace).replace(
                "Dry-run complete; no workspace state was written.", ""
            ),
            workspace,
            no_write=True,
        )

    executed = _plan_text(workspace).replace(
        "Dry-run complete; no workspace state was written.",
        f"Evidence: {expected}/attempts/workflow-attempt-1/attempt-receipt.json",
    )
    assert DRIVER.parse_run_plan(executed, workspace, no_write=False) == expected
    assert DRIVER.parse_execution_evidence(executed, expected) == (
        expected / "attempts/workflow-attempt-1/attempt-receipt.json"
    )


def test_scheduler_plan_parser_requires_no_write_workspace_log_patterns(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    profile = tmp_path / "emrys.execution.slurm.json"
    text = "\n".join(
        (
            "Execution placement: Slurm",
            f"Execution profile: {profile}",
            f"Scheduler stdout: {workspace}/logs/emrys-local-pilot-%j.out",
            f"Scheduler stderr: {workspace}/logs/emrys-local-pilot-%j.err",
            "Dry-run complete; no scheduler or workspace state was written.",
        )
    )

    assert DRIVER.parse_scheduler_plan(text, profile, workspace) == (
        workspace / "logs/emrys-local-pilot-%j.out",
        workspace / "logs/emrys-local-pilot-%j.err",
    )
    with pytest.raises(DRIVER.DriverError, match="no-write boundary"):
        DRIVER.parse_scheduler_plan(
            text.replace(
                "Dry-run complete; no scheduler or workspace state was written.",
                "",
            ),
            profile,
            workspace,
        )


def test_submission_and_scontrol_parsers_fail_closed(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    text = "\n".join(
        (
            "JOB_ID=1234",
            f"OUT={logs}/emrys-local-pilot-1234.out",
            f"ERR={logs}/emrys-local-pilot-1234.err",
        )
    )

    submitted = DRIVER.parse_submission(text, logs)
    assert submitted.job_id == "1234"
    assert DRIVER.parse_scontrol_job(
        "JobId=1234 JobState=COMPLETED ExitCode=0:0 Partition=emrys-ci"
    ) == ("COMPLETED", "0:0")

    with pytest.raises(DRIVER.DriverError, match="unexpected stdout"):
        DRIVER.parse_submission(text.replace("1234.out", "other.out"), logs)
    with pytest.raises(DRIVER.DriverError, match="omits JobState"):
        DRIVER.parse_scontrol_job("JobId=1234 Partition=emrys-ci")


def test_cancel_job_sends_term_once_and_confirms_terminal_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def run(
        command: tuple[str, ...], **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[0] == "/usr/bin/scancel":
            return subprocess.CompletedProcess(command, 0, "", "")
        return subprocess.CompletedProcess(
            command,
            0,
            "JobId=1234 JobState=CANCELLED ExitCode=0:15\n",
            "",
        )

    monkeypatch.setattr(DRIVER.subprocess, "run", run)

    state = DRIVER.cancel_job(
        "1234",
        scancel=Path("/usr/bin/scancel"),
        scontrol=Path("/usr/bin/scontrol"),
        cwd=tmp_path,
        poll_seconds=0.01,
    )

    assert state == "CANCELLED"
    assert calls == [
        ("/usr/bin/scancel", "--signal=TERM", "1234"),
        ("/usr/bin/scontrol", "show", "job", "-o", "1234"),
    ]


def _write_table(path: Path, candidate_ids: tuple[str, ...]) -> None:
    path.write_text(
        "candidate_id\tcall_status\n"
        + "".join(
            f"{candidate_id}\tsignificant_up\n" for candidate_id in candidate_ids
        ),
        encoding="utf-8",
    )


def test_step09_oracle_reads_direct_tables_not_a_summary_claim(tmp_path: Path) -> None:
    significant_id = "REV_like|chrSynthetic|50000|A>G"
    all_sites = tmp_path / "all.tsv"
    significant = tmp_path / "significant.tsv"
    _write_table(all_sites, ("candidate-a", significant_id, "candidate-c"))
    _write_table(significant, (significant_id,))
    fixture = {
        "expected_terminal_computational_result": {
            "all_sites_rows": 3,
            "significant_sites_rows": 1,
            "significant_candidate_id": significant_id,
        }
    }

    observed = DRIVER.validate_step09_oracle(all_sites, significant, fixture)

    assert observed["all_sites_rows"] == 3
    assert observed["significant_sites_rows"] == 1
    assert observed["significant_candidate_id"] == significant_id

    _write_table(significant, ("candidate-a",))
    with pytest.raises(DRIVER.DriverError, match="candidate identity"):
        DRIVER.validate_step09_oracle(all_sites, significant, fixture)


def test_operator_root_is_empty_external_and_preserved(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    operator = tmp_path / "operator"
    operator.mkdir()

    paths = DRIVER.require_operator_root(operator, repo)
    assert paths.workspace == operator / "synthetic-inputs"
    assert paths.runtime_profile == paths.workspace / "runtime/runtime.tsv"
    assert not paths.workspace.exists()

    retained = operator / "retained.partial"
    retained.write_text("preserve me\n", encoding="utf-8")
    with pytest.raises(DRIVER.DriverError, match="preserve existing"):
        DRIVER.require_operator_root(operator, repo)
    assert retained.read_text(encoding="utf-8") == "preserve me\n"

    nested = repo / "operator"
    nested.mkdir()
    with pytest.raises(DRIVER.DriverError, match="outside the source checkout"):
        DRIVER.require_operator_root(nested, repo)


def test_failure_summary_disclaims_completion_and_cleanup(tmp_path: Path) -> None:
    parser = DRIVER.build_parser()
    arguments = parser.parse_args(
        [
            "--profile",
            "130",
            "--repo-root",
            "/repo",
            "--operator-root",
            str(tmp_path),
            "--runtime-prefix",
            "/runtime",
            "--rscript",
            "/runtime/Rscript",
            "--renv-library",
            "/runtime/renv",
            "--storage-compute-launcher-json",
            '["/usr/bin/srun"]',
            "--slurm-partition",
            "emrys-ci",
        ]
    )
    summary = DRIVER._failure_summary(
        arguments,
        DRIVER.Transcripts(tmp_path / "transcripts"),
        DRIVER.DriverError("doctor", "injected blocker"),
    )

    assert summary["schema_version"] == "emrys.ci-real-synthetic-e2e-summary.v2"
    assert summary["status"] == "failed"
    assert summary["failed_stage"] == "doctor"
    assert summary["biological_interpretation_claimed"] is False
    assert "no cleanup" in summary["retention"]


def test_unadmitted_nonempty_root_is_not_mutated_by_main(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    operator = tmp_path / "operator"
    operator.mkdir()
    retained = operator / "retained.partial"
    retained.write_text("preserve me\n", encoding="utf-8")

    status = DRIVER.main(
        [
            "--profile",
            "130",
            "--repo-root",
            str(repo),
            "--operator-root",
            str(operator),
            "--runtime-prefix",
            str(tmp_path),
            "--rscript",
            str(retained),
            "--renv-library",
            str(tmp_path),
            "--storage-compute-launcher-json",
            json.dumps([str(retained)]),
            "--slurm-partition",
            "emrys-ci",
            "--execute",
        ]
    )

    assert status == 2
    assert retained.read_text(encoding="utf-8") == "preserve me\n"
    assert not (operator / "e2e-summary.json").exists()


def test_driver_is_no_write_without_explicit_execute(tmp_path: Path) -> None:
    operator = tmp_path / "absent-operator-root"

    status = DRIVER.main(
        [
            "--profile",
            "130",
            "--repo-root",
            str(tmp_path / "absent-repo"),
            "--operator-root",
            str(operator),
            "--runtime-prefix",
            str(tmp_path / "absent-runtime"),
            "--rscript",
            str(tmp_path / "absent-Rscript"),
            "--renv-library",
            str(tmp_path / "absent-renv"),
            "--storage-compute-launcher-json",
            '["/absent/srun"]',
            "--slurm-partition",
            "emrys-ci",
        ]
    )

    assert status == 0
    assert not operator.exists()
