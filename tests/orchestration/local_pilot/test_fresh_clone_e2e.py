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

import pytest

from norad import __file__ as norad_package_file
from norad.contracts.orchestration import api as orchestration_contracts
from norad.orchestration.local_pilot import doctor, inspection, reporting_boundary
from norad.orchestration.local_pilot.normalization import normalize_request
from tests.orchestration.local_pilot.fixture import build as build_intake_fixture

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "tests/orchestration/local_pilot/fixtures/b6_cli_harness.py"
OPT_IN = "NORAD_FRESH_CLONE_E2E"
SOURCE_ROOT = "NORAD_FRESH_CLONE_E2E_SOURCE_ROOT"
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
    assert Path(norad_package_file).resolve().is_relative_to(REPO_ROOT / "src/norad")

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


def _write_runtime_profile(root: Path) -> Path:
    root.mkdir()

    def executable(name: str, output: str) -> Path:
        path = root / name
        path.write_text(
            "#!/bin/sh\n" + f"printf '%s\\n' '{output}'\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        return path

    tools = {
        "star": executable("STAR", "2.7.11b"),
        "samtools": executable("samtools", "samtools 1.19.2"),
        "bcftools": executable("bcftools", "bcftools 1.21"),
        "infer_experiment": executable("infer_experiment.py", "RSeQC v5.0.4"),
        "gunzip": executable("gunzip", "gzip 1.13"),
    }
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
    starter = REPO_ROOT / "configs/local_pilot_runtime.example.tsv"
    with starter.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        assert reader.fieldnames is not None
        header = tuple(reader.fieldnames)
        rows = list(reader)
    by_name = {row["check_id"]: row for row in rows}
    package_versions: dict[str, str] = {}
    for check_id, package in doctor.LOCAL_PILOT_R_PACKAGES:
        exact = by_name[check_id]["expected"]
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
        r_lines.append(f"  *' {package} '*) printf '{version}\\n' ;;")
    r_lines.extend(("  *) exit 42 ;;", "esac"))
    rscript.write_text("\n".join(r_lines) + "\n", encoding="utf-8")
    rscript.chmod(0o755)

    for row in rows:
        check_id = row["check_id"]
        check_type = row["check_type"]
        target = str(tools.get(check_id, root / check_id))
        probe_args = json.loads(row["probe_args"])
        if check_id == "bash":
            target = "/bin/bash"
        elif check_id == "python":
            target = sys.executable
        elif check_id in {"snakemake", "sha256_python"}:
            target = sys.executable
            if check_id == "snakemake":
                probe_args = [
                    "-X",
                    "pycache_prefix=/dev/null",
                    "-I",
                    "-m",
                    "snakemake",
                    "--version",
                ]
            else:
                probe_args = ["python_hashlib"]
        elif check_id == "java":
            target = str(java)
        elif check_id == "gatk":
            target = str(gatk)
        elif check_id == "picard":
            target = str(java)
            probe_args = [
                "-jar",
                str(picard_jar),
                "MarkDuplicates",
                "--version",
            ]
        elif check_id == "picard_jar":
            target = str(picard_jar)
        elif check_id == "rscript":
            target = str(rscript)
        elif check_id == "renv_project":
            target = str(REPO_ROOT)
        elif check_id == "renv_library":
            target = str(renv_library)
        elif check_type == "r_namespace":
            target = row["target"]
            probe_args = [str(rscript)]
        row["target"] = target
        row["probe_args"] = json.dumps(probe_args, separators=(",", ":"))

    profile = root / "runtime.tsv"
    with profile.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=header, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return profile


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
            "norad",
            *arguments,
        ],
        cwd=REPO_ROOT,
        environment=environment,
    )


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


def _verify_bound_input_snapshots(execution: dict[str, Any]) -> int:
    verified_paths: set[Path] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if set(value) == {"path", "size_bytes", "sha256"}:
                path = Path(str(value["path"]))
                assert path.is_file() and not path.is_symlink()
                data = path.read_bytes()
                assert len(data) == value["size_bytes"]
                assert hashlib.sha256(data).hexdigest() == value["sha256"]
                verified_paths.add(path)
                return
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(execution)
    return len(verified_paths)


def _assert_complete_products(run_root: Path, run_id: str) -> None:
    execution = orchestration_contracts.load_json_object(
        run_root / "contract/normalized.json"
    )
    profile = orchestration_contracts.load_json_object(
        run_root / "contract/profile.json"
    )
    observed = inspection.inspect_run(run_root)
    assert observed.local_pipeline_complete
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
    report_root = run_root / "products/report" / run_id
    assert (summary_root / f"{run_id}.artifacts.tsv").is_file()
    assert (summary_root / f"{run_id}.artifact_receipt.tsv").is_file()
    summary_path = summary_root / f"{run_id}.run_summary.json"
    assert summary_path.is_file()
    assert (summary_root / f"{run_id}.run_summary_receipt.tsv").is_file()
    assert (report_root / f"{run_id}.scientific_report.html").is_file()
    assert (report_root / f"{run_id}.evidence_report.html").is_file()
    assert (report_root / f"{run_id}.run_summary.tsv").is_file()
    assert (report_root / f"{run_id}.report_outputs.tsv").is_file()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["interpretation_boundary"] == (
        "computational_candidates_only_biological_validation_outside_norad"
    )
    assert "science_status" not in summary
    assert "scientific_review" not in summary


def test_public_cli_accepts_explicit_control_ops_and_harness_starts(
    tmp_path: Path,
) -> None:
    program = """
import json
from types import SimpleNamespace
from norad import __main__ as cli
from norad.orchestration.local_pilot import control

def unreachable(*_args, **_kwargs):
    raise AssertionError("unreachable control dependency")

observed = SimpleNamespace(
    run_id="run-explicit-ops",
    run_root=__import__("pathlib").Path("/explicit/run-root"),
    state="resume_available",
    latest_workflow_attempt_id="workflow-explicit-ops",
    tasks=(),
    reporting_completion_records={},
    blockers=(),
    resume_available=True,
    local_pipeline_complete=False,
)
ops = control.ControlOps(
    inspect_readiness=unreachable,
    normalize=unreachable,
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
    assert "State: resume_available" in seam.stdout
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
    assert "norad: error:" in harness.stderr


@FRESH_CLONE_ONLY
def test_fresh_clone_public_failure_resume_and_outputs(tmp_path: Path) -> None:
    raw_source_root = os.environ.get(SOURCE_ROOT)
    assert raw_source_root, f"{SOURCE_ROOT} must name the cloned source checkout"
    source_root = Path(os.path.abspath(raw_source_root))
    _assert_prepared_fresh_clone(source_root)

    intake_root = tmp_path / "intake"
    request = build_intake_fixture(intake_root)
    workspace = tmp_path / "workspace"
    runtime_profile = _write_runtime_profile(tmp_path / "runtime")
    environment = _command_environment(source_root, tmp_path)
    normalized = normalize_request(
        request,
        REPO_ROOT / "workflow/contracts/local_cmh_v2.json",
    )
    run_root = workspace / "runs" / normalized.run_id
    common = [
        "--request",
        str(request),
        "--workspace",
        str(workspace),
        "--runtime-profile",
        str(runtime_profile),
    ]

    help_result = _public_command(["--help"], environment=environment)
    assert help_result.returncode == 0, help_result.stdout + help_result.stderr
    assert "usage: norad" in help_result.stdout

    qualification_common = [
        "inspect",
        "storage-qualification",
        "--workspace",
        str(workspace),
        "--reference-fasta",
        str(normalized.execution_contract["reference"]["fasta"]["path"]),
    ]
    compute_environment = dict(environment)
    compute_environment["SLURM_JOB_ID"] = "fresh-clone-fixture"
    compute_qualification = _public_command(
        [*qualification_common, "--phase", "compute", "--execute"],
        environment=compute_environment,
    )
    assert compute_qualification.returncode == 0, (
        compute_qualification.stdout + compute_qualification.stderr
    )
    final_environment = dict(environment)
    final_environment.pop("SLURM_JOB_ID", None)
    final_qualification = _public_command(
        [*qualification_common, "--phase", "finalize", "--execute"],
        environment=final_environment,
    )
    assert final_qualification.returncode == 0, (
        final_qualification.stdout + final_qualification.stderr
    )

    readiness = _public_command(
        ["doctor", "local-pilot", *common],
        environment=environment,
    )
    assert readiness.returncode == 0, readiness.stdout + readiness.stderr
    assert "READY: local-pilot prerequisites passed." in readiness.stdout

    dry_run = _public_command(["run", *common], environment=environment)
    assert dry_run.returncode == 0, dry_run.stdout + dry_run.stderr
    assert f"Owner jobs: {EXPECTED_OWNER_JOB_COUNT}" in dry_run.stdout
    assert "Reporting transactions: 3" in dry_run.stdout
    assert "Dry-run complete; no workspace state was written." in dry_run.stdout
    assert not workspace.exists()

    failed_run = _harness_command(
        "failure",
        ["run", *common, "--execute"],
        environment=environment,
    )
    assert failed_run.returncode == 1, failed_run.stdout + failed_run.stderr
    assert "Attempt status: failed" in failed_run.stdout
    assert run_root.is_dir()

    failed_receipts = sorted(run_root.glob("attempts/*/attempt-receipt.json"))
    assert len(failed_receipts) == 1
    first_receipt = orchestration_contracts.load_record(
        failed_receipts[0], "attempt-receipt"
    )
    assert first_receipt["status"] == "failed"
    assert first_receipt["snakemake_exit_code"] == 23

    failed_inspect = _public_command(
        ["inspect", "local-pilot-run", "--run-root", str(run_root)],
        environment=environment,
    )
    assert failed_inspect.returncode == 0, failed_inspect.stderr
    assert "State: resume_available" in failed_inspect.stdout
    assert "Resume available: yes" in failed_inspect.stdout
    second_initial = _harness_command(
        "success",
        ["run", *common, "--execute"],
        environment=environment,
    )
    assert second_initial.returncode == 2
    assert "Run root already exists; inspect or resume it instead" in (
        second_initial.stderr
    )

    execution = orchestration_contracts.load_json_object(
        run_root / "contract/normalized.json"
    )
    assert _verify_bound_input_snapshots(execution) == 12
    first_attempt = orchestration_contracts.load_record(
        failed_receipts[0].with_name("attempt.json"), "workflow-attempt"
    )
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
        "--runtime-profile",
        str(runtime_profile),
    ]
    resume_dry_run = _harness_command(
        "success",
        resume_common,
        environment=environment,
    )
    assert resume_dry_run.returncode == 0, resume_dry_run.stdout + resume_dry_run.stderr
    assert f"Reusable completed owner jobs: {len(verified_before)}" in (
        resume_dry_run.stdout
    )
    assert "Dry-run complete; no resume state was written." in resume_dry_run.stdout
    assert _tree_snapshot(run_root) == before_resume_dry_run

    resumed = _harness_command(
        "success",
        [*resume_common, "--execute"],
        environment=environment,
    )
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert "Attempt status: succeeded" in resumed.stdout
    reused_after = _reusable_snapshot(run_root)
    assert reused_before.keys() <= reused_after.keys()
    assert all(reused_after[path] == value for path, value in reused_before.items())

    completed_inspect = _public_command(
        ["inspect", "local-pilot-run", "--run-root", str(run_root)],
        environment=environment,
    )
    assert completed_inspect.returncode == 0, completed_inspect.stderr
    assert "State: local_pipeline_complete" in completed_inspect.stdout
    assert "Local pipeline complete: yes" in completed_inspect.stdout

    _assert_complete_products(run_root, normalized.run_id)

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
    assert second_receipt["status"] == "succeeded"
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
    assert "Completed local-pilot run refuses resume" in completed_resume.stderr

    forbidden = str(source_root).encode()
    for path in run_root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            assert forbidden not in path.read_bytes(), path

    clean_intake_root = tmp_path / "clean-intake"
    clean_request = build_intake_fixture(clean_intake_root)
    clean_normalized = normalize_request(
        clean_request,
        REPO_ROOT / "workflow/contracts/local_cmh_v2.json",
    )
    clean_workspace = tmp_path / "clean-workspace"
    clean_common = [
        "--request",
        str(clean_request),
        "--workspace",
        str(clean_workspace),
        "--runtime-profile",
        str(runtime_profile),
    ]
    clean_run = _harness_command(
        "success",
        ["run", *clean_common, "--execute"],
        environment=environment,
    )
    assert clean_run.returncode == 0, clean_run.stdout + clean_run.stderr
    assert "Attempt status: succeeded" in clean_run.stdout
    clean_root = clean_workspace / "runs" / clean_normalized.run_id
    clean_inspect = _public_command(
        ["inspect", "local-pilot-run", "--run-root", str(clean_root)],
        environment=environment,
    )
    assert clean_inspect.returncode == 0, clean_inspect.stderr
    assert "State: local_pipeline_complete" in clean_inspect.stdout
    assert "Local pipeline complete: yes" in clean_inspect.stdout
    _assert_complete_products(clean_root, clean_normalized.run_id)
    for path in clean_root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            assert forbidden not in path.read_bytes(), path
    assert _git("status", "--porcelain=v1", "--untracked-files=all") == ""
