"""Protect NORAD's installed-wheel contract without replaying repository tests."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path

from tests.reporting.fixtures.artifact_run_summary_v1 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DEPENDENCIES = {"jinja2", "jsonschema", "pyyaml", "referencing"}
RUNTIME_REQUIREMENT_SPECIFIERS = {
    "jinja2": "==3.1.6",
    "jsonschema": ">=4.18.0",
    "pyyaml": "==6.0.3",
    "referencing": ">=0.28.4",
}
RESOURCE_PATHS = (
    "norad/contracts/schemas/artifacts/v1/artifact_record.schema.json",
    "norad/contracts/schemas/artifacts/v1/common.schema.json",
    "norad/contracts/schemas/artifacts/v2/report_receipt.schema.json",
    "norad/contracts/schemas/artifacts/v1/run_summary.schema.json",
    "norad/contracts/schemas/artifacts/v1/scientific_review_record.schema.json",
    "norad/contracts/schemas/orchestration/v1/request.schema.json",
    "norad/contracts/schemas/orchestration/v1/profile.schema.json",
    "norad/contracts/schemas/orchestration/v1/execution.schema.json",
    "norad/contracts/schemas/orchestration/v1/reference.schema.json",
    "norad/contracts/schemas/orchestration/v1/policy.schema.json",
    "norad/contracts/schemas/orchestration/v1/workflow_attempt.schema.json",
    "norad/contracts/schemas/orchestration/v1/attempt_receipt.schema.json",
    "norad/contracts/schemas/orchestration/v1/run_lock.schema.json",
    "norad/contracts/schemas/orchestration/v1/task_start.schema.json",
    "norad/contracts/schemas/orchestration/v1/task_attempt.schema.json",
    "norad/contracts/schemas/orchestration/v1/verified_task.schema.json",
    "norad/contracts/schemas/orchestration/v1/reporting_start.schema.json",
    "norad/contracts/schemas/orchestration/v1/verified_reporting.schema.json",
    "norad/contracts/schemas/orchestration/v1/common.schema.json",
    "norad/reporting/styles/run_report.css",
    "norad/reporting/templates/run_report.html.j2",
)


def command_environment(*, hostile_pythonpath: bool = False) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    if hostile_pythonpath:
        environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    return environment


def run_command(
    arguments: list[str], *, cwd: Path, hostile_pythonpath: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        cwd=cwd,
        env=command_environment(hostile_pythonpath=hostile_pythonpath),
        text=True,
        capture_output=True,
        check=False,
    )


def require_success(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stdout + result.stderr


def uv_executable() -> str:
    executable = shutil.which("uv")
    assert executable is not None, "uv is required; run the documented setup"
    return executable


def build_wheel(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(REPO_ROOT / name, project / name)
    shutil.copytree(
        REPO_ROOT / "src",
        project / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"),
    )
    wheel_directory = tmp_path / "wheel"
    wheel_directory.mkdir()
    result = run_command(
        [
            uv_executable(),
            "build",
            "--wheel",
            "--force-pep517",
            "--offline",
            "--no-python-downloads",
            "--out-dir",
            str(wheel_directory),
            str(project),
        ],
        cwd=tmp_path,
    )
    require_success(result)
    wheels = list(wheel_directory.glob("*.whl"))
    assert len(wheels) == 1
    return wheels[0]


def normalized_requirement(requirement: str) -> str:
    return re.split(r"[ ;(<=>!~\[]", requirement, maxsplit=1)[0].lower()


def declared_requirements(requirements: list[str]) -> dict[str, str]:
    return {
        normalized_requirement(requirement): requirement.split(";", 1)[0]
        .strip()
        .lower()
        for requirement in requirements
    }


def inspect_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        (metadata_member,) = (
            member for member in members if member.endswith(".dist-info/METADATA")
        )
        (entry_points_member,) = (
            member
            for member in members
            if member.endswith(".dist-info/entry_points.txt")
        )
        metadata = Parser().parsestr(archive.read(metadata_member).decode())
        declared = declared_requirements(metadata.get_all("Requires-Dist", []))

        assert metadata["Name"] == "norad-rna-workflow"
        assert metadata["Version"] == "0.0.0"
        assert set(declared) == RUNTIME_DEPENDENCIES
        assert declared == {
            name: f"{name}{specifier}"
            for name, specifier in RUNTIME_REQUIREMENT_SPECIFIERS.items()
        }
        entry_points = archive.read(entry_points_member).decode().splitlines()
        assert "norad = norad.__main__:main" in entry_points
        assert set(RESOURCE_PATHS) <= members
        for resource in RESOURCE_PATHS:
            assert archive.read(resource) == (REPO_ROOT / "src" / resource).read_bytes()


def install_locked_wheel(wheel: Path, tmp_path: Path) -> tuple[Path, Path]:
    locked = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    constraints = sorted(
        f"{item['name']}=={item['version']}"
        for item in locked["package"]
        if "version" in item
    )
    installer = tmp_path / "installer"
    installer.mkdir()
    (installer / "pyproject.toml").write_text(
        "[project]\n"
        'name = "norad-wheel-smoke"\n'
        'version = "0"\n'
        'requires-python = ">=3.11"\n'
        f"dependencies = [{json.dumps(f'norad-rna-workflow @ {wheel.as_uri()}')}]\n"
        "[tool.uv]\n"
        "constraint-dependencies = [\n"
        + "".join(f"    {json.dumps(requirement)},\n" for requirement in constraints)
        + "]\n",
        encoding="utf-8",
    )
    lock = run_command(
        [
            uv_executable(),
            "lock",
            "--offline",
            "--no-python-downloads",
            "--project",
            str(installer),
        ],
        cwd=tmp_path,
    )
    require_success(lock)
    sync = run_command(
        [
            uv_executable(),
            "sync",
            "--locked",
            "--no-dev",
            "--no-install-project",
            "--offline",
            "--no-python-downloads",
            "--python",
            sys.executable,
            "--project",
            str(installer),
        ],
        cwd=tmp_path,
    )
    require_success(sync)
    environment_root = installer / ".venv"
    environment_python = environment_root / "bin" / "python"
    console = environment_root / "bin" / "norad"
    assert console.is_file()
    return environment_python, console


def installed_probe(environment_python: Path, cwd: Path) -> dict[str, object]:
    probe = run_command(
        [
            str(environment_python),
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-c",
            (
                "import importlib.metadata, json, norad, sys; "
                "from importlib.resources import files; "
                f"resources={RESOURCE_PATHS!r}; root=files('norad'); "
                f"dependencies={sorted(RUNTIME_DEPENDENCIES)!r}; "
                "print(json.dumps({"
                "'module': norad.__file__, "
                "'requirements': importlib.metadata.requires('norad-rna-workflow'), "
                "'installed': {name: importlib.metadata.version(name) "
                "for name in dependencies}, "
                "'resources': [root.joinpath(path.removeprefix('norad/')).is_file() "
                "for path in resources], "
                "'sys_path': sys.path}))"
            ),
        ],
        cwd=cwd,
        hostile_pythonpath=True,
    )
    require_success(probe)
    return json.loads(probe.stdout)


def test_isolated_wheel_installs_resources_and_public_commands(tmp_path: Path) -> None:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "report-fixture",
        science_status="science_review_complete_exploratory",
        roles=("candidate_selection",),
        display_limits={"candidate_selection": 1},
    )
    summary_result = run_command(
        [
            sys.executable,
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "norad",
            "build",
            "run-summary",
            *fixture.command_args(execute=True),
        ],
        cwd=REPO_ROOT,
    )
    require_success(summary_result)
    artifact_source_root = tmp_path / "wheel-artifact-source"
    relative_table_path = "wheel-only/report_table_approvals.tsv"
    approved_table = artifact_source_root / relative_table_path
    approved_table.parent.mkdir(parents=True)
    shutil.copy2(
        REPO_ROOT / "configs/report_table_approvals.example.tsv",
        approved_table,
    )
    relative_summary = FIXTURE.copy_summary_with_repo_relative_approved_table(
        fixture.summary_json_path,
        artifact_source_root,
        relative_table_path=relative_table_path,
        table_source_root=artifact_source_root,
        summary_git_commit="upstream-summary-commit",
    )
    wheel = build_wheel(tmp_path)
    inspect_wheel(wheel)
    environment_python, console = install_locked_wheel(wheel, tmp_path)
    arbitrary_cwd = tmp_path / "outside-checkout"
    arbitrary_cwd.mkdir()
    observed = installed_probe(environment_python, arbitrary_cwd)
    module = Path(str(observed["module"])).resolve()
    assert module.is_relative_to(environment_python.parents[1].resolve())
    assert not module.is_relative_to(REPO_ROOT.resolve())
    assert all(observed["resources"])
    assert declared_requirements(observed["requirements"]) == {
        name: f"{name}{specifier}"
        for name, specifier in RUNTIME_REQUIREMENT_SPECIFIERS.items()
    }
    assert set(observed["installed"]) == RUNTIME_DEPENDENCIES
    assert all(observed["installed"].values())
    assert str((REPO_ROOT / "src").resolve()) not in {
        str(Path(entry).resolve()) for entry in observed["sys_path"] if entry
    }
    module_help = run_command(
        [str(environment_python), "-I", "-m", "norad", "--help"],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(module_help)
    assert "usage: norad" in module_help.stdout
    console_help = run_command([str(console), "--help"], cwd=arbitrary_cwd)
    require_success(console_help)
    assert "usage: norad" in console_help.stdout
    manifest = arbitrary_cwd / "samples.tsv"
    manifest.write_text(
        "sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\n"
        "sample_001\treads/R1.fastq.gz\treads/R2.fastq.gz\treverse\tcontrol\n",
        encoding="utf-8",
    )
    validation = run_command(
        [
            str(environment_python),
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "norad",
            "validate",
            "manifest",
            "--manifest",
            str(manifest),
        ],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(validation)
    assert "Manifest validation passed." in validation.stdout
    assert "Samples: 1" in validation.stdout
    report_output_root = arbitrary_cwd / "reports"
    report_help = run_command(
        [str(environment_python), "-I", "-m", "norad", "build", "report", "--help"],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(report_help)
    assert "--source-checkout" in report_help.stdout
    assert "--artifact-source-root" in report_help.stdout
    assert "--quarto-bin" not in report_help.stdout
    rendered = run_command(
        [
            str(environment_python),
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "norad",
            "build",
            "report",
            "--source-checkout",
            str(REPO_ROOT),
            "--artifact-source-root",
            str(artifact_source_root),
            "--run-summary",
            str(relative_summary),
            "--output-root",
            str(report_output_root),
            "--execute",
        ],
        cwd=arbitrary_cwd,
        hostile_pythonpath=True,
    )
    require_success(rendered)
    assert f"Source checkout: {REPO_ROOT}" in rendered.stdout
    assert f"Artifact source root: {artifact_source_root}" in rendered.stdout
    run_id = fixture.run_id
    report_directory = report_output_root / run_id
    assert {path.name for path in report_directory.iterdir()} == {
        f"{run_id}.run_report.html",
        f"{run_id}.run_summary.tsv",
        f"{run_id}.report_outputs.tsv",
    }
    assert "Jinja2" in (report_directory / f"{run_id}.report_outputs.tsv").read_text(
        encoding="utf-8"
    )
    assert "example_run" in (report_directory / f"{run_id}.run_report.html").read_text(
        encoding="utf-8"
    )
    with (report_directory / f"{run_id}.report_outputs.tsv").open(
        encoding="utf-8",
        newline="",
    ) as stream:
        receipt_rows = list(csv.DictReader(stream, delimiter="\t"))
    receipt_values = {row["report_receipt_json"] for row in receipt_rows}
    assert len(receipt_values) == 1
    receipt = json.loads(receipt_values.pop())
    checkout_commit = run_command(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=REPO_ROOT,
    )
    require_success(checkout_commit)
    assert Path(receipt["input_run_summary"]["path"]).is_relative_to(
        artifact_source_root
    )
    assert not Path(receipt["input_run_summary"]["path"]).is_relative_to(REPO_ROOT)
    assert receipt["provenance"]["git_commit"] in {
        "local_build",
        checkout_commit.stdout.strip(),
    }
    assert receipt["provenance"]["git_commit"] != "upstream-summary-commit"
    wrong_checkout = run_command(
        [str(environment_python), "-I", "-m", "norad", "--help"],
        cwd=REPO_ROOT,
        hostile_pythonpath=True,
    )
    assert wrong_checkout.returncode == 2
    assert "not the current checkout" in wrong_checkout.stderr
