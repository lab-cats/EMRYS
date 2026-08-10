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

import pytest

from norad import __main__ as norad_cli

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
STAR_INDEX_MEMBERS = (
    "genomeParameters.txt",
    "Genome",
    "SA",
    "SAindex",
    "chrLength.txt",
    "chrName.txt",
    "chrNameLength.txt",
    "chrStart.txt",
    "exonGeTrInfo.tab",
    "exonInfo.tab",
    "geneInfo.tab",
    "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab",
    "sjdbList.out.tab",
    "transcriptInfo.tab",
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


def test_package_metadata_is_an_unreleased_distribution() -> None:
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
    assert "scripts" not in configuration["project"]
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


@pytest.mark.parametrize(
    "configuration",
    ("[project\n", '[project]\nname = "another-project"\n'),
)
def test_checkout_detection_ignores_invalid_candidates(
    tmp_path: Path,
    configuration: str,
) -> None:
    checkout = tmp_path / "checkout"
    nested_directory = checkout / "nested"
    package = checkout / "src" / "norad"
    nested_directory.mkdir(parents=True)
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (checkout / "pyproject.toml").write_text(configuration, encoding="utf-8")

    assert norad_cli._find_checkout_root(nested_directory.resolve()) is None


def test_cli_rejects_another_checkout_but_accepts_its_editable_owner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checkout = tmp_path / "checkout"
    nested_directory = checkout / "nested"
    package = checkout / "src" / "norad"
    nested_directory.mkdir(parents=True)
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (checkout / "pyproject.toml").write_text(
        '[project]\nname = "norad-rna-workflow"\n',
        encoding="utf-8",
    )

    monkeypatch.chdir(nested_directory)
    assert norad_cli.main(["--help"]) == 2
    assert "not the current checkout" in capsys.readouterr().err

    monkeypatch.chdir(REPO_ROOT)
    assert norad_cli._checkout_mismatch() is None


def _build_wheel(tmp_path: Path) -> tuple[Path, Path]:
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
    return project, wheels[0]


def _assert_wheel_contents(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        assert set(RESOURCE_PATHS) <= members
        assert {
            member
            for member in members
            if member.startswith("norad/") and not member.endswith(".py")
        } == set(RESOURCE_PATHS)
        assert "norad/ingestion/__init__.py" in members
        assert "norad/ingestion/sample_manifest_admission/__init__.py" in members
        assert "norad/ingestion/sample_manifest_admission/validator.py" in members
        assert (
            "norad/ingestion/sample_manifest_admission/validate_manifest.py"
            not in members
        )
        assert {member for member in members if member.startswith("norad/stages/")} == {
            "norad/stages/__init__.py",
            "norad/stages/gtf_to_bed12/__init__.py",
            "norad/stages/gtf_to_bed12/converter.py",
            "norad/stages/gtf_to_bed12/validator.py",
            "norad/stages/star_index/__init__.py",
            "norad/stages/star_index/validator.py",
        }
        assert not any(member.startswith("norad/analyses/") for member in members)
        assert not any(member.endswith((".R", ".sh", ".slurm")) for member in members)
        for resource in RESOURCE_PATHS:
            source = REPO_ROOT / "src" / resource
            assert archive.read(resource) == source.read_bytes()


def _assert_target_install(wheel: Path, tmp_path: Path) -> Path:
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

    working_directory = tmp_path / "arbitrary-cwd"
    working_directory.mkdir()
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
        cwd=working_directory,
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
    return working_directory


def _install_wheel_in_environment(wheel: Path, tmp_path: Path) -> Path:
    environment_directory = tmp_path / "environment"
    create_environment = run_command(
        [sys.executable, "-m", "venv", str(environment_directory)],
        cwd=tmp_path,
    )
    assert create_environment.returncode == 0, (
        create_environment.stdout + create_environment.stderr
    )
    environment_python = environment_directory / "bin" / "python"
    install_wheel = run_command(
        [
            str(environment_python),
            "-m",
            "pip",
            "install",
            "--no-compile",
            "--no-deps",
            "--no-index",
            str(wheel),
        ],
        cwd=tmp_path,
    )
    assert install_wheel.returncode == 0, install_wheel.stdout + install_wheel.stderr
    return environment_python


def _hostile_python_environment(tmp_path: Path) -> dict[str, str]:
    foreign_package = tmp_path / "foreign" / "norad"
    foreign_package.mkdir(parents=True)
    (foreign_package / "__init__.py").write_text(
        "raise RuntimeError('foreign norad package imported')\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(foreign_package.parent)
    return environment


def _run_installed_norad(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(environment_python), "-I", "-m", "norad", *arguments],
        cwd=working_directory,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def _build_star_index_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path]:
    reference_directory = working_directory / "star-reference"
    reference_directory.mkdir()
    fasta_path = reference_directory / "genome.fa"
    fasta_path.write_text(">1\nACGT\n", encoding="utf-8")
    gtf_path = reference_directory / "genome.gtf"
    gtf_path.write_text(
        '1\tfixture\tgene\t1\t4\t.\t+\t.\tgene_id "G1";\n',
        encoding="utf-8",
    )

    index_directory = working_directory / "star-index"
    index_directory.mkdir()
    for member_name in STAR_INDEX_MEMBERS:
        (index_directory / member_name).write_text("fixture\n", encoding="utf-8")
    (index_directory / "chrName.txt").write_text("1\n", encoding="utf-8")
    (index_directory / "chrLength.txt").write_text("4\n", encoding="utf-8")
    (index_directory / "genomeParameters.txt").write_text(
        f"genomeFastaFiles {fasta_path}\nsjdbGTFfile {gtf_path}\nsjdbOverhang 149\n",
        encoding="utf-8",
    )

    output_directory = working_directory / "star-validation"
    output_directory.mkdir()
    return (
        index_directory,
        fasta_path,
        gtf_path,
        output_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_star_index_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    index_directory, fasta_path, gtf_path, output_path = _build_star_index_fixture(
        working_directory
    )
    unrelated_path = working_directory / "star-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "star-index",
        "--scope-id",
        "wheel_fixture",
        "--index-dir",
        str(index_directory),
        "--reference-fasta",
        str(fasta_path),
        "--reference-gtf",
        str(gtf_path),
        "--parameter-path-base",
        str(working_directory),
        "--expected-sjdb-overhang",
        "149",
        "--output",
        str(output_path),
    )
    assert validation.returncode == 0, validation.stdout + validation.stderr
    assert validation.stderr == ""
    assert validation.stdout.endswith("Dry-run complete; no output was written.\n")
    report_rows = [
        line.split("\t")
        for line in validation.stdout.splitlines()
        if line.startswith("00a\t")
    ]
    assert len(report_rows) == 5
    assert {row[2] for row in report_rows} == {
        "index_members",
        "fasta_identity",
        "gtf_identity",
        "contig_names_lengths",
        "sjdb_overhang",
    }
    assert {row[3] for row in report_rows} == {"pass"}
    assert not output_path.exists()
    assert not list(output_path.parent.glob(".*validation*"))
    assert unrelated_path.read_text(encoding="utf-8") == "preserve\n"


def _assert_installed_commands(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    manifest_help = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "manifest",
        "--help",
    )
    assert manifest_help.returncode == 0, manifest_help.stdout + manifest_help.stderr
    assert "usage: norad validate manifest" in manifest_help.stdout

    bed12_help = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "bed12",
        "--help",
    )
    assert bed12_help.returncode == 0, bed12_help.stdout + bed12_help.stderr
    assert "usage: norad validate bed12" in bed12_help.stdout

    gtf_path = working_directory / "input.gtf"
    bed_path = working_directory / "output" / "models.bed"
    unrelated_path = working_directory / "unrelated.txt"
    gtf_path.write_text(
        'chr1\tfixture\texon\t1\t4\t.\t+\t.\tgene_id "g1"; transcript_id "tx1";\n',
        encoding="utf-8",
    )
    unrelated_path.write_text("preserve\n", encoding="utf-8")
    conversion = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "convert",
        "gtf-to-bed12",
        "--gtf",
        str(gtf_path),
        "--bed",
        str(bed_path),
    )
    assert conversion.returncode == 0, conversion.stdout + conversion.stderr
    assert conversion.stderr == ""
    assert conversion.stdout == f"Wrote 1 transcript BED12 record(s) to {bed_path}\n"
    assert bed_path.read_bytes() == (b"chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n")
    assert unrelated_path.read_text(encoding="utf-8") == "preserve\n"

    _assert_installed_star_index_validation(
        environment_python,
        working_directory,
        environment,
    )


def _assert_private_source_layout() -> None:
    manifest_owner = REPO_ROOT / "src/norad/ingestion/sample_manifest_admission"
    assert not (manifest_owner / "validate_manifest.py").exists()
    assert (manifest_owner / "validator.py").stat().st_mode & 0o111 == 0

    stage_owner = REPO_ROOT / "src/norad/stages/gtf_to_bed12"
    assert not (REPO_ROOT / "src/norad/stages/convert_GTF_to_BED12").exists()
    for retired_name in ("gtf_to_bed12.py", "validate_step_00b_bed12.py"):
        assert not (stage_owner / retired_name).exists()
    for private_name in ("converter.py", "validator.py"):
        assert (stage_owner / private_name).stat().st_mode & 0o111 == 0

    star_index_owner = REPO_ROOT / "src/norad/stages/star_index"
    assert not (REPO_ROOT / "src/norad/stages/construct_STAR_index").exists()
    assert not (star_index_owner / "validate_step_00a_star_index.py").exists()
    assert (star_index_owner / "validator.py").stat().st_mode & 0o111 == 0

    assert not (REPO_ROOT / "tests/stages/construct_STAR_index").exists()
    assert (REPO_ROOT / "tests/stages/star_index").is_dir()


def _assert_wrong_checkout_rejected(
    environment_python: Path,
    project: Path,
    environment: dict[str, str],
) -> None:
    nested_checkout_directory = project / "nested" / "work"
    nested_checkout_directory.mkdir(parents=True)
    for working_directory in (project, nested_checkout_directory):
        probe = _run_installed_norad(
            environment_python,
            working_directory,
            environment,
            "--help",
        )
        assert probe.returncode == 2
        assert "not the current checkout" in probe.stderr


def test_wheel_contains_only_explicit_packages_and_exact_resources(
    tmp_path: Path,
) -> None:
    project, wheel = _build_wheel(tmp_path)

    _assert_wheel_contents(wheel)
    arbitrary_working_directory = _assert_target_install(wheel, tmp_path)
    environment_python = _install_wheel_in_environment(wheel, tmp_path)
    isolated_environment = _hostile_python_environment(tmp_path)
    _assert_installed_commands(
        environment_python,
        arbitrary_working_directory,
        isolated_environment,
    )
    _assert_private_source_layout()
    _assert_wrong_checkout_rejected(
        environment_python,
        project,
        isolated_environment,
    )
