"""Protect NORAD's deliberately narrow internal package distribution."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_PATHS = (
    "norad/contracts/schemas/artifacts/v1/artifact_record.schema.json",
    "norad/contracts/schemas/artifacts/v1/common.schema.json",
    "norad/contracts/schemas/artifacts/v1/report_receipt.schema.json",
    "norad/contracts/schemas/artifacts/v1/run_summary.schema.json",
    "norad/contracts/schemas/artifacts/v1/scientific_review_record.schema.json",
    "norad/reporting/styles/run_report.css",
    "norad/reporting/templates/run_report.qmd",
    "norad/reporting/templates/run_report_pdf.qmd",
)


def run_command(arguments: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return subprocess.run(
        arguments,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def test_package_metadata_is_an_unreleased_import_substrate() -> None:
    configuration = tomllib.loads(
        (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert configuration["build-system"] == {
        "requires": ["setuptools==80.9.0"],
        "build-backend": "setuptools.build_meta",
    }
    assert configuration["project"]["name"] == "norad-rna-workflow"
    assert configuration["project"]["requires-python"] == ">=3.11"
    assert configuration["project"]["dependencies"] == []
    assert (
        configuration["tool"]["setuptools"]["packages"]["find"]["namespaces"] is False
    )

    development_requirements = (
        (REPO_ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()
    )
    assert "setuptools==80.9.0" in development_requirements
    assert "ruff==0.16.2" in development_requirements
    assert "vulture==2.16" in development_requirements
    assert not any(line.startswith("pylint") for line in development_requirements)


def test_wheel_contains_only_explicit_packages_and_exact_resources(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    shutil.copy2(REPO_ROOT / "pyproject.toml", project / "pyproject.toml")
    shutil.copy2(REPO_ROOT / "README.md", project / "README.md")
    shutil.copytree(REPO_ROOT / "src", project / "src")

    wheel_directory = tmp_path / "wheel"
    wheel_directory.mkdir()
    build = run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(wheel_directory),
            str(project),
        ],
        cwd=tmp_path,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    wheels = list(wheel_directory.glob("*.whl"))
    assert len(wheels) == 1
    wheel = wheels[0]

    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        assert set(RESOURCE_PATHS) <= members
        assert {
            member
            for member in members
            if member.startswith("norad/") and not member.endswith(".py")
        } == set(RESOURCE_PATHS)
        assert not any(
            member.startswith(("norad/analyses/", "norad/ingestion/", "norad/stages/"))
            for member in members
        )
        assert not any(member.endswith((".R", ".sh", ".slurm")) for member in members)
        for resource in RESOURCE_PATHS:
            source = REPO_ROOT / "src" / resource
            assert archive.read(resource) == source.read_bytes()

    target = tmp_path / "installed"
    install = run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-compile",
            "--no-deps",
            "--no-index",
            "--target",
            str(target),
            str(wheel),
        ],
        cwd=tmp_path,
    )
    assert install.returncode == 0, install.stdout + install.stderr

    arbitrary_working_directory = tmp_path / "arbitrary-cwd"
    arbitrary_working_directory.mkdir()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(target)
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.metadata, json, norad; "
                "from norad.contracts.artifacts._artifact_contracts.schema "
                "import load_schema_registry; "
                "from norad.reporting._run_report.bundle_models "
                "import PDF_TEMPLATE; "
                "from norad.reporting._run_report.models "
                "import CSS_TEMPLATE, QMD_TEMPLATE; "
                "schemas, _ = load_schema_registry(); "
                "print(json.dumps({"
                "'module': norad.__file__, "
                "'version': importlib.metadata.version('norad-rna-workflow'), "
                "'schemas': sorted(schemas), "
                "'resources': [str(QMD_TEMPLATE), str(CSS_TEMPLATE), "
                "str(PDF_TEMPLATE)]}))"
            ),
        ],
        cwd=arbitrary_working_directory,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr
    observed = json.loads(probe.stdout)
    assert Path(observed["module"]).resolve().is_relative_to(target.resolve())
    assert observed["version"] == "0.0.0"
    assert observed["schemas"] == [
        "artifact-record",
        "common",
        "report-receipt",
        "run-summary",
        "scientific-review-record",
    ]
    assert all(Path(path).is_file() for path in observed["resources"])
