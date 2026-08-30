"""Opt-in fresh-clone proof for the public B6 local-pilot journey."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import pytest

from emrys import __file__ as emrys_package_file
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.evidence.runtime_availability._probes import (
    R_NAMESPACE_ROOT_OUTPUT_MARKER,
)
from emrys.orchestration.local_pilot import inspection, reporting_boundary
from emrys.orchestration.local_pilot.normalization import admit_project
from tests.orchestration.local_pilot.fixture import build as build_intake_fixture

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "tests/orchestration/local_pilot/fixtures/b6_cli_harness.py"
OPT_IN = "EMRYS_FRESH_CLONE_E2E"
SOURCE_ROOT = "EMRYS_FRESH_CLONE_E2E_SOURCE_ROOT"
REPORTING_KINDS = ("artifact_index", "run_summary", "html_report")
EXPECTED_OWNER_JOB_COUNT = 35

FRESH_CLONE_ONLY = pytest.mark.skipif(
    os.environ.get(OPT_IN) != "1",
    reason=(
        "fresh-clone proof is operator-prepared; clone and run locked uv setup "
        f"before setting {OPT_IN}=1"
    ),
)


def _run(
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def _git(*arguments: str) -> str:
    result = _run(["git", *arguments], cwd=REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout.strip()


def _assert_prepared_fresh_clone(source_root: Path) -> None:
    assert source_root.is_absolute()
    assert source_root != REPO_ROOT
    assert REPO_ROOT not in source_root.parents
    assert source_root not in REPO_ROOT.parents
    assert (REPO_ROOT / ".git").is_dir(), "proof requires an ordinary fresh clone"
    assert _git("rev-parse", "--show-toplevel") == str(REPO_ROOT)
    assert _git("status", "--porcelain=v1", "--untracked-files=all") == ""
    origin = _git("config", "--get", "remote.origin.url")
    local_origin = origin.removeprefix("file://")
    assert Path(local_origin).is_absolute(), "proof requires an explicit local origin"
    assert Path(os.path.abspath(local_origin)) == source_root
    assert Path(os.path.abspath(sys.executable)) == REPO_ROOT / ".venv/bin/python"
    assert Path(emrys_package_file).resolve().is_relative_to(REPO_ROOT / "src/emrys")

    uv = shutil.which("uv")
    assert uv is not None, "uv must be provisioned before fresh-clone setup"
    check = _run(
        [
            uv,
            "sync",
            "--locked",
            "--group",
            "workflow",
            "--check",
            "--offline",
            "--no-python-downloads",
        ],
        cwd=REPO_ROOT,
        environment=os.environ.copy(),
    )
    assert check.returncode == 0, check.stdout + check.stderr


def _project_fixture(root: Path) -> Path:
    request = build_intake_fixture(root)
    project = root / "project.yaml"
    request.rename(project)
    for name in ("logs", "runs", "runtime"):
        (root / name).mkdir(mode=0o700)
    return project


def _runtime_discovery_environment(
    root: Path,
    base_environment: dict[str, str],
) -> dict[str, str]:
    root.mkdir()

    def executable(name: str, output: str) -> Path:
        path = root / name
        path.write_text(
            "#!/bin/sh\n" + f"printf '%s\\n' '{output}'\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    executable("STAR", "2.7.11b")
    executable("samtools", "samtools 1.19.2")
    executable("bcftools", "bcftools 1.21")
    executable("infer_experiment.py", "infer_experiment.py 5.0.4")
    executable("gunzip", "gzip 1.13")
    java_home = root / "fixture-jdk"
    java = java_home / "bin" / "java"
    picard_jar = root / "fixture-picard.jar"
    picard_jar.write_bytes(b"bounded no-science Picard fixture\n")
    java.parent.mkdir(parents=True)
    java.write_text(
        "#!/bin/sh\n"
        f'[ "$#" -eq 4 ] && [ "$1" = -jar ] && '
        f"[ \"$2\" = '{picard_jar}' ] && "
        '[ "$3" = MarkDuplicates ] && [ "$4" = --version ] && {\n'
        "    printf 'Version:3.1.1\\n' >&2\n"
        "    exit 1\n"
        "}\n"
        '[ "$#" -eq 1 ] && [ "$1" = -version ] && {\n'
        "    printf 'openjdk version \"17.0.1\"\\n' >&2\n"
        "    exit 0\n"
        "}\n"
        "exit 2\n",
        encoding="utf-8",
    )
    java.chmod(0o755)
    gatk = root / "gatk"
    gatk.write_text(
        "#!/bin/sh\n"
        f"[ \"${{JAVA_HOME:-}}\" = '{java_home}' ] || exit 91\n"
        f"[ \"$(command -v java)\" = '{java}' ] || exit 92\n"
        "printf 'Using GATK jar fixture.jar\\nRunning:\\njava -jar fixture.jar --version\\n' >&2\n"
        "printf 'The Genome Analysis Toolkit (GATK) v4.6.1.0\\n'\n",
        encoding="utf-8",
    )
    gatk.chmod(0o755)
    rscript = root / "fixture-Rscript"
    renv_library = root / "fixture-renv-library"
    renv_library.mkdir()
    installed_renv = renv_library / "renv"
    installed_renv.mkdir()
    (installed_renv / "DESCRIPTION").write_text(
        "Package: renv\nVersion: 1.2.3\n", encoding="utf-8"
    )
    starter = REPO_ROOT / "src/emrys/resources/runtime/runtime_policy.tsv"
    with starter.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        assert reader.fieldnames is not None
        rows = list(reader)
    package_versions: dict[str, str] = {}
    for row in rows:
        if row["check_type"] != "r_namespace":
            continue
        package = row["target"]
        exact = row["expected"]
        version = exact.removeprefix("^").removesuffix("$").replace("[.]", ".")
        assert re.fullmatch(r"[0-9]+(?:[.][0-9]+)+", version)
        package_versions[package] = version
        package_root = renv_library / package
        package_root.mkdir()
        (package_root / "DESCRIPTION").write_text(
            f"Package: {package}\nVersion: {version}\n", encoding="utf-8"
        )
    r_lines = [
        "#!/bin/sh",
        'case " $* " in',
        "  *' --version '*) printf 'Rscript (R) version 4.6.1\\n' ;;",
    ]
    for package, version in package_versions.items():
        package_root = (renv_library / package).resolve(strict=True)
        encoded_root = str(package_root).encode("utf-8").hex()
        output = f"{version}{R_NAMESPACE_ROOT_OUTPUT_MARKER}{encoded_root}"
        r_lines.append(f"  *' {package} '*) printf '{output}\\n' ;;")
    r_lines.extend(("  *) exit 42 ;;", "esac"))
    rscript.write_text("\n".join(r_lines) + "\n", encoding="utf-8")
    rscript.chmod(0o755)

    (root / "bash").symlink_to("/bin/bash")
    (root / "java").symlink_to(java)
    return {
        **base_environment,
        "PATH": str(root),
        "JAVA_HOME": str(java_home),
        "EMRYS_PICARD_JAR": str(picard_jar),
        "EMRYS_RSCRIPT": str(rscript),
        "EMRYS_RENV_LIBRARY": str(renv_library),
    }


def _command_environment(source_root: Path, tmp_path: Path) -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": str(source_root / "src"),
        "XDG_CACHE_HOME": str(tmp_path / "xdg-cache"),
    }


def _public_command(
    arguments: list[str],
    *,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "emrys",
            *arguments,
        ],
        cwd=REPO_ROOT,
        environment=environment,
    )


def _qualify_storage(
    workspace: Path,
    reference_fasta: Path,
    *,
    environment: dict[str, str],
) -> None:
    common = [
        "inspect",
        "storage-qualification",
        "--workspace",
        str(workspace),
        "--reference-fasta",
        str(reference_fasta),
    ]
    compute_environment = dict(environment)
    compute_environment["SLURM_JOB_ID"] = "700123"
    compute = _public_command(
        [*common, "--phase", "compute", "--execute"],
        environment=compute_environment,
    )
    assert compute.returncode == 0, compute.stdout + compute.stderr

    final_environment = dict(environment)
    final_environment.pop("SLURM_JOB_ID", None)
    final = _public_command(
        [*common, "--phase", "finalize", "--execute"],
        environment=final_environment,
    )
    assert final.returncode == 0, final.stdout + final.stderr


def _harness_command(
    mode: str,
    arguments: list[str],
    *,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return _run(
        [
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            str(HARNESS),
            mode,
            *arguments,
        ],
        cwd=REPO_ROOT,
        environment=environment,
    )


def _planned_run(stdout: str, workspace: Path) -> tuple[str, Path]:
    """Read the immutable Run selected by the public control-plane plan."""

    run_ids = re.findall(r"^Run ID: (run-[0-9a-f]{64})$", stdout, re.MULTILINE)
    assert len(run_ids) == 1, stdout
    run_id = run_ids[0]
    run_root = workspace.resolve() / "runs" / run_id
    return run_id, run_root


def _tree_snapshot(root: Path) -> dict[Path, tuple[bytes, int]]:
    return {
        path.relative_to(root): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def _reusable_snapshot(run_root: Path) -> dict[Path, tuple[bytes, int]]:
    paths: set[Path] = set()
    for record_path in (run_root / "state/verified").glob("*/*.json"):
        record = orchestration_contracts.load_record(record_path, "verified-task")
        paths.add(record_path)
        paths.update(Path(str(item["path"])) for item in record["outputs"])
        paths.add(run_root / str(record["validation_report"]["path"]))
    return {
        path: (path.read_bytes(), path.stat().st_mtime_ns) for path in sorted(paths)
    }


def _assert_complete_products(run_root: Path, run_id: str) -> None:
    execution = orchestration_contracts.load_json_object(run_root / "contract/run.json")
    assert execution["schema_version"] == "emrys.run-binding.v1"
    assert execution["run_id"] == run_id
    assert not (run_root / "contract/normalized.json").exists()
    profile = orchestration_contracts.load_json_object(
        run_root / "contract/profile.json"
    )
    observed = inspection.inspect_run(run_root)
    assert observed.authority is not None
    assert observed.authority.run_binding.run_id == run_id
    assert observed.authority.analysis_revision.analysis_revision_id.startswith(
        "analysis-"
    )
    assert observed.authority.execution_plan.execution_plan_id.startswith("plan-")
    assert observed.integrity == "valid"
    assert observed.attempt_outcome == "succeeded"
    assert observed.results_status == "complete"
    assert observed.reporting_status == "complete"
    assert observed.latest_attempt is not None
    assert observed.latest_attempt["snakemake_argv"][-2:] == ["--", "cohort_slice"]
    assert observed.latest_receipt is not None
    assert observed.latest_receipt["schema_version"] == "emrys.attempt-receipt.v2"
    assert "reporting_completion_records" not in observed.latest_receipt
    assert "local_pipeline_complete" not in observed.latest_receipt
    assert (
        len(list((run_root / "state/verified").glob("*/*.json")))
        == EXPECTED_OWNER_JOB_COUNT
    )
    for kind in REPORTING_KINDS:
        assert (run_root / "state/reporting" / kind / "start.json").is_file()
        assert (run_root / "state/reporting" / kind / "verified.json").is_file()
        reporting_boundary.validate_verified(
            kind,
            run_root,
            execution,
            profile,
        )

    summary_root = run_root / "products/artifact-summary" / run_id
    report_root = run_root / "results/reports" / run_id
    assert (summary_root / f"{run_id}.artifacts.tsv").is_file()
    assert (summary_root / f"{run_id}.artifact_receipt.tsv").is_file()
    summary_path = summary_root / f"{run_id}.run_summary.json"
    assert summary_path.is_file()
    assert (summary_root / f"{run_id}.run_summary_receipt.tsv").is_file()
    assert (report_root / f"{run_id}.scientific_report.html").is_file()
    assert (report_root / f"{run_id}.evidence_report.html").is_file()
    assert (report_root / f"{run_id}.run_summary.tsv").is_file()
    assert (report_root / f"{run_id}.report_outputs.tsv").is_file()
    results_root = run_root / "results"
    assert results_root.is_dir() and not results_root.is_symlink()
    assert {path.name for path in results_root.iterdir()} == {
        "editing",
        "reports",
        "scientific_context",
    }
    for directory in (
        results_root / "editing",
        results_root / "reports",
        results_root / "scientific_context",
        run_root / "products" / "native",
    ):
        assert directory.is_dir() and not directory.is_symlink()
    assert not os.path.lexists(run_root / "products" / "report")
    scientific_html = (report_root / f"{run_id}.scientific_report.html").read_text(
        encoding="utf-8"
    )
    evidence_html = (report_root / f"{run_id}.evidence_report.html").read_text(
        encoding="utf-8"
    )
    for content in (scientific_html, evidence_html):
        assert 'aria-label="Result files"' in content
        assert "Threshold-passing candidates" in content
        assert "Complete candidate table" in content
        assert "Candidate context" in content
    with (summary_root / f"{run_id}.artifacts.tsv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        artifacts = {
            row["adapter"]: run_root / row["source_path"]
            for row in csv.DictReader(stream, delimiter="\t")
        }
    for label, adapter in (
        ("Threshold-passing candidates", "step09_cmh_significant_sites_v1"),
        ("Complete candidate table", "step09_cmh_all_sites_v1"),
        ("Candidate context", "step10_candidate_context_v1"),
    ):
        match = re.search(
            rf'href="([^"]+)"><strong>{re.escape(label)}</strong>',
            scientific_html,
        )
        assert match is not None
        assert (report_root / unquote(match.group(1))).resolve(
            strict=True
        ) == artifacts[adapter].resolve(strict=True)
    assert "emrys inspect local-pilot-run --run-root" not in scientific_html
    assert f"emrys inspect local-pilot-run --run-root {run_root}" in evidence_html
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["interpretation_boundary"] == (
        "computational_candidates_only_biological_validation_outside_emrys"
    )
    assert "science_status" not in summary
    assert "scientific_review" not in summary


def test_public_cli_accepts_explicit_control_ops_and_harness_starts(
    tmp_path: Path,
) -> None:
    program = """
import json
from types import SimpleNamespace
from emrys import __main__ as cli
from emrys.orchestration.local_pilot import control

def unreachable(*_args, **_kwargs):
    raise AssertionError("unreachable control dependency")

observed = SimpleNamespace(
    run_id="run-explicit-ops",
    run_root=__import__("pathlib").Path("/explicit/run-root"),
    integrity="valid",
    attempt_outcome="failed",
    results_status="incomplete",
    reporting_status="incomplete",
    latest_attempt={
        "workflow_attempt_id": "workflow-explicit-ops",
        "created_at": "2026-08-12T20:00:00Z",
    },
    latest_receipt={
        "finished_at": "2026-08-12T20:01:00Z",
    },
    tasks=(),
    reporting_completion_records={},
    blockers=(),
    integrity_blockers=(),
    results_blockers=(),
    reporting_blockers=(),
    receipt_blockers=(),
    recovery_available=True,
    verified_report_locations=(),
)
ops = control.ControlOps(
    inspect_readiness=unreachable,
    admit_project=unreachable,
    inspect_run=lambda _root: observed,
    execute_plan=unreachable,
    transform_plan=unreachable,
    now=unreachable,
    token=unreachable,
)
status = cli.main(
    ["inspect", "local-pilot-run", "--run-root", "/ignored"],
    local_pilot_control_ops=ops,
)
print(json.dumps({"status": status}))
"""
    seam = _run(
        [
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-c",
            program,
        ],
        cwd=REPO_ROOT,
        environment=os.environ.copy(),
    )
    assert seam.returncode == 0, seam.stdout + seam.stderr
    assert "Run ID: run-explicit-ops" in seam.stdout
    assert "Attempt outcome: failed" in seam.stdout
    assert "Scientific Results: incomplete" in seam.stdout
    assert "Recovery available: yes" in seam.stdout
    assert "Results:" not in seam.stdout.splitlines()
    assert json.loads(seam.stdout.splitlines()[-1]) == {"status": 0}

    harness = _run(
        [
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            str(HARNESS),
            "success",
            "inspect",
            "local-pilot-run",
            "--run-root",
            str(tmp_path / "absent-run"),
        ],
        cwd=REPO_ROOT,
        environment=os.environ.copy(),
    )
    assert harness.returncode == 2
    assert "emrys: error:" in harness.stderr


@FRESH_CLONE_ONLY
def test_fresh_clone_public_failure_resume_and_outputs(tmp_path: Path) -> None:
    raw_source_root = os.environ.get(SOURCE_ROOT)
    assert raw_source_root, f"{SOURCE_ROOT} must name the cloned source checkout"
    source_root = Path(os.path.abspath(raw_source_root))
    _assert_prepared_fresh_clone(source_root)

    intake_root = tmp_path / "intake"
    request = _project_fixture(intake_root)
    workspace = request.parent
    environment = _command_environment(source_root, tmp_path)
    runtime_environment = _runtime_discovery_environment(
        tmp_path / "runtime-tools", environment
    )
    runtime_profile = workspace / "runtime/runtime.tsv"
    normalized = admit_project(
        request,
        REPO_ROOT / "workflow/contracts/local_cmh_v2.json",
    )
    discovery = ["runtime", "discover", "--project", str(request)]
    discovery_plan = _public_command(discovery, environment=runtime_environment)
    assert discovery_plan.returncode == 0, discovery_plan.stdout + discovery_plan.stderr
    assert not runtime_profile.exists()
    discovery_execute = _public_command(
        [*discovery, "--execute"], environment=runtime_environment
    )
    assert discovery_execute.returncode == 0, (
        discovery_execute.stdout + discovery_execute.stderr
    )
    assert runtime_profile.is_file()
    common = ["--project", str(request)]
    run_common = [
        *common,
        "--execution-profile",
        str(request.parent / "emrys.execution.yaml"),
    ]

    help_result = _public_command(["--help"], environment=environment)
    assert help_result.returncode == 0, help_result.stdout + help_result.stderr
    assert "usage: emrys" in help_result.stdout

    _qualify_storage(
        workspace,
        Path(str(normalized.construction["reference"]["fasta"]["path"])),
        environment=environment,
    )

    readiness = _public_command(
        ["doctor", "local-pilot", *common],
        environment=environment,
    )
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    assert "READY: local-pilot prerequisites passed." in readiness.stdout

    dry_run = _public_command(["run", *run_common], environment=environment)
    assert dry_run.returncode == 0, dry_run.stdout + dry_run.stderr
    assert f"Work: {EXPECTED_OWNER_JOB_COUNT} pending, 0 reusable" in dry_run.stderr
    assert "Reporting: automatic after scientific work" in dry_run.stderr
    assert "Dry-run complete; no workspace state was written." in dry_run.stderr
    assert not any((workspace / name).iterdir() for name in ("runs", "logs"))
    run_id, run_root = _planned_run(dry_run.stderr, workspace)

    failed_run = _harness_command(
        "failure",
        ["run", *run_common, "--execute"],
        environment=environment,
    )
    assert failed_run.returncode == 1, failed_run.stdout + failed_run.stderr
    assert "emrys-run failed: phase=terminal status=failed" in failed_run.stderr
    assert "Results:" not in failed_run.stderr.splitlines()
    assert _planned_run(failed_run.stderr, workspace) == (run_id, run_root)
    assert run_root.is_dir()

    failed_receipts = sorted(run_root.glob("attempts/*/attempt-receipt.json"))
    assert len(failed_receipts) == 1
    first_receipt = orchestration_contracts.load_record(
        failed_receipts[0], "attempt-receipt"
    )
    assert first_receipt["schema_version"] == "emrys.attempt-receipt.v2"
    assert first_receipt["status"] == "failed"
    assert first_receipt["snakemake_exit_code"] == 23
    assert "reporting_completion_records" not in first_receipt
    assert "local_pipeline_complete" not in first_receipt

    failed_inspect = _public_command(
        ["inspect", "local-pilot-run", "--run-root", str(run_root)],
        environment=environment,
    )
    assert failed_inspect.returncode == 0, failed_inspect.stderr
    assert "Attempt outcome: failed" in failed_inspect.stdout
    assert "Scientific Results: incomplete" in failed_inspect.stdout
    assert "Recovery available: yes" in failed_inspect.stdout
    assert "Results:" not in failed_inspect.stdout.splitlines()
    second_initial = _harness_command(
        "success",
        ["run", *run_common, "--execute"],
        environment=environment,
    )
    assert second_initial.returncode == 2
    assert "Run root already exists; inspect or resume it instead" in (
        second_initial.stderr
    )

    execution = orchestration_contracts.load_json_object(run_root / "contract/run.json")
    assert execution["run_id"] == run_id
    first_attempt = orchestration_contracts.load_record(
        failed_receipts[0].with_name("attempt.json"), "workflow-attempt"
    )
    assert first_attempt["snakemake_argv"][-2:] == ["--", "cohort_slice"]
    assert first_attempt["source_checkout"] == {
        "path": str(REPO_ROOT),
        "commit": _git("rev-parse", "HEAD"),
        "clean": True,
    }
    authored_request = request.read_bytes()
    assert first_attempt["request"]["size_bytes"] == len(authored_request)
    assert (
        first_attempt["request"]["sha256"]
        == hashlib.sha256(authored_request).hexdigest()
    )

    reused_before = _reusable_snapshot(run_root)
    verified_before = list((run_root / "state/verified").glob("*/*.json"))
    assert 0 < len(verified_before) < EXPECTED_OWNER_JOB_COUNT
    before_resume_dry_run = _tree_snapshot(run_root)
    resume_common = [
        "resume",
        "--run-root",
        str(run_root),
    ]
    resume_dry_run = _harness_command(
        "success",
        resume_common,
        environment=environment,
    )
    assert resume_dry_run.returncode == 0, resume_dry_run.stdout + resume_dry_run.stderr
    assert (
        f"Work: {EXPECTED_OWNER_JOB_COUNT - len(verified_before)} pending, "
        f"{len(verified_before)} reusable"
    ) in resume_dry_run.stderr
    assert "Dry-run complete; no resume state was written." in resume_dry_run.stderr
    assert "Results:" not in resume_dry_run.stderr.splitlines()
    assert _tree_snapshot(run_root) == before_resume_dry_run

    resumed = _harness_command(
        "success",
        [*resume_common, "--execute"],
        environment=environment,
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "Evidence:" in resumed.stderr
    report_root = run_root / "results" / "reports" / run_id
    expected_results = (
        "Results:\n"
        f"  Scientific report: {report_root}/{run_id}.scientific_report.html\n"
        f"  Evidence report: {report_root}/{run_id}.evidence_report.html\n"
    )
    assert expected_results in resumed.stderr
    reused_after = _reusable_snapshot(run_root)
    assert reused_before.keys() <= reused_after.keys()
    assert all(reused_after[path] == value for path, value in reused_before.items())

    completed_inspect = _public_command(
        ["inspect", "local-pilot-run", "--run-root", str(run_root)],
        environment=environment,
    )
    assert completed_inspect.returncode == 0, completed_inspect.stderr
    assert "Attempt outcome: succeeded" in completed_inspect.stdout
    assert "Scientific Results: complete" in completed_inspect.stdout
    assert "Reporting: complete" in completed_inspect.stdout
    assert expected_results in completed_inspect.stdout

    _assert_complete_products(run_root, run_id)

    receipts = sorted(run_root.glob("attempts/*/attempt-receipt.json"))
    assert len(receipts) == 2
    receipt_records = [
        orchestration_contracts.load_record(path, "attempt-receipt")
        for path in receipts
    ]
    second_index = next(
        index
        for index, record in enumerate(receipt_records)
        if record["workflow_attempt_id"] != first_receipt["workflow_attempt_id"]
    )
    second_receipt = receipt_records[second_index]
    assert second_receipt["schema_version"] == "emrys.attempt-receipt.v2"
    assert second_receipt["status"] == "succeeded"
    assert "reporting_completion_records" not in second_receipt
    assert "local_pipeline_complete" not in second_receipt
    second_attempt_path = receipts[second_index].with_name("attempt.json")
    second_attempt = orchestration_contracts.load_record(
        second_attempt_path, "workflow-attempt"
    )
    assert (
        second_attempt["supersedes_workflow_attempt_id"]
        == first_receipt["workflow_attempt_id"]
    )
    assert second_attempt["source_checkout"] == first_attempt["source_checkout"]

    completed_resume = _harness_command(
        "success",
        resume_common,
        environment=environment,
    )
    assert completed_resume.returncode == 2
    assert "Results are complete" in completed_resume.stderr

    forbidden = str(source_root).encode()
    for path in run_root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            assert forbidden not in path.read_bytes(), path

    clean_intake_root = tmp_path / "clean-intake"
    clean_request = _project_fixture(clean_intake_root)
    clean_normalized = admit_project(
        clean_request,
        REPO_ROOT / "workflow/contracts/local_cmh_v2.json",
    )
    clean_workspace = clean_request.parent
    clean_discovery = _public_command(
        [
            "runtime",
            "discover",
            "--project",
            str(clean_request),
            "--execute",
        ],
        environment=runtime_environment,
    )
    assert clean_discovery.returncode == 0, (
        clean_discovery.stdout + clean_discovery.stderr
    )
    assert (clean_workspace / "runtime/runtime.tsv").is_file()
    clean_common = [
        "--project",
        str(clean_request),
        "--execution-profile",
        str(clean_request.parent / "emrys.execution.yaml"),
    ]
    _qualify_storage(
        clean_workspace,
        Path(str(clean_normalized.construction["reference"]["fasta"]["path"])),
        environment=environment,
    )
    clean_run = _harness_command(
        "success",
        ["run", *clean_common, "--execute"],
        environment=environment,
    )
    assert clean_run.returncode == 0, clean_run.stdout + clean_run.stderr
    assert "Evidence:" in clean_run.stderr
    clean_run_id, clean_root = _planned_run(clean_run.stderr, clean_workspace)
    clean_report_root = clean_root / "results" / "reports" / clean_run_id
    clean_expected_results = (
        "Results:\n"
        f"  Scientific report: {clean_report_root}/{clean_run_id}.scientific_report.html\n"
        f"  Evidence report: {clean_report_root}/{clean_run_id}.evidence_report.html\n"
    )
    assert clean_expected_results in clean_run.stderr
    clean_inspect = _public_command(
        ["inspect", "local-pilot-run", "--run-root", str(clean_root)],
        environment=environment,
    )
    assert clean_inspect.returncode == 0, clean_inspect.stderr
    assert "Attempt outcome: succeeded" in clean_inspect.stdout
    assert "Scientific Results: complete" in clean_inspect.stdout
    assert "Reporting: complete" in clean_inspect.stdout
    assert clean_expected_results in clean_inspect.stdout
    _assert_complete_products(clean_root, clean_run_id)
    for path in clean_root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            assert forbidden not in path.read_bytes(), path
    assert _git("status", "--porcelain=v1", "--untracked-files=all") == ""
