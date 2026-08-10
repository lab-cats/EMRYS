"""Protect NORAD's deliberately narrow internal package distribution."""

from __future__ import annotations

import hashlib
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
EVIDENCE_PACKAGE_PATHS = frozenset(
    {
        "norad/evidence/__init__.py",
        "norad/evidence/assemble_scientific_review_evidence_package/__init__.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/__init__.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/_evidence_manifest.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/_intake_models.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/_intake_support.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/_review_candidates.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/_review_decisions.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/_review_plan.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/_review_sensitivity.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/audits.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/context.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/contracts.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/evidence.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "_scientific_review/intake.py",
        "norad/evidence/assemble_scientific_review_evidence_package/"
        "step_09c_scientific_validation.py",
        "norad/evidence/canonical_bam_qc/__init__.py",
        "norad/evidence/canonical_bam_qc/validator.py",
        "norad/evidence/rseqc_orientation/__init__.py",
        "norad/evidence/rseqc_orientation/validator.py",
        "norad/evidence/storage_inventory/__init__.py",
        "norad/evidence/storage_inventory/_storage_contract.py",
        "norad/evidence/storage_inventory/_storage_measurement.py",
        "norad/evidence/storage_inventory/_storage_publication.py",
        "norad/evidence/storage_inventory/storage_inventory.py",
    }
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
        assert {
            member for member in members if member.startswith("norad/evidence/")
        } == EVIDENCE_PACKAGE_PATHS
        assert {member for member in members if member.startswith("norad/stages/")} == {
            "norad/stages/canonical_bam/__init__.py",
            "norad/stages/canonical_bam/validator.py",
            "norad/stages/duplicate_marking/__init__.py",
            "norad/stages/duplicate_marking/validator.py",
            "norad/stages/fasta_sidecars/__init__.py",
            "norad/stages/fasta_sidecars/validator.py",
            "norad/stages/__init__.py",
            "norad/stages/gtf_to_bed12/__init__.py",
            "norad/stages/gtf_to_bed12/converter.py",
            "norad/stages/gtf_to_bed12/validator.py",
            "norad/stages/mechanical_orientation/__init__.py",
            "norad/stages/mechanical_orientation/validator.py",
            "norad/stages/partitioned_cohort_mpileup/__init__.py",
            "norad/stages/partitioned_cohort_mpileup/validator.py",
            "norad/stages/split_n_cigar/__init__.py",
            "norad/stages/split_n_cigar/validator.py",
            "norad/stages/star_index/__init__.py",
            "norad/stages/star_index/validator.py",
            "norad/stages/star_alignment/__init__.py",
            "norad/stages/star_alignment/validator.py",
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


def _assert_validation_dry_run(
    result: subprocess.CompletedProcess[str],
    output_path: Path,
    *,
    step_id: str,
    expected_check_ids: set[str],
) -> None:
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert result.stdout.endswith("Dry-run complete; no output was written.\n")
    report_rows = [
        line.split("\t")
        for line in result.stdout.splitlines()
        if line.startswith(f"{step_id}\t")
    ]
    assert len(report_rows) == len(expected_check_ids)
    assert {row[2] for row in report_rows} == expected_check_ids
    assert {row[3] for row in report_rows} == {"pass"}
    assert not output_path.exists()
    assert not list(output_path.parent.glob(".*validation*"))


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
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="00a",
        expected_check_ids={
            "index_members",
            "fasta_identity",
            "gtf_identity",
            "contig_names_lengths",
            "sjdb_overhang",
        },
    )
    assert unrelated_path.read_text(encoding="utf-8") == "preserve\n"


def _build_fasta_sidecars_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path]:
    reference_directory = working_directory / "fasta-sidecar-reference"
    reference_directory.mkdir()
    fasta_path = reference_directory / "genome.fa"
    fasta_path.write_text(">1\nACGT\n", encoding="utf-8")
    fai_path = reference_directory / "genome.fa.fai"
    fai_path.write_text("1\t4\t3\t4\t5\n", encoding="utf-8")
    dictionary_path = reference_directory / "genome.dict"
    dictionary_path.write_text(
        "@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n",
        encoding="utf-8",
    )
    output_directory = working_directory / "fasta-sidecar-validation"
    output_directory.mkdir()
    return (
        fasta_path,
        fai_path,
        dictionary_path,
        output_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_fasta_sidecars_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    fasta_path, fai_path, dictionary_path, output_path = _build_fasta_sidecars_fixture(
        working_directory
    )
    input_bytes = tuple(
        path.read_bytes() for path in (fasta_path, fai_path, dictionary_path)
    )
    unrelated_path = working_directory / "fasta-sidecar-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "fasta-sidecars",
        "--scope-id",
        "wheel_fixture",
        "--reference-fasta",
        str(fasta_path),
        "--reference-fai",
        str(fai_path),
        "--reference-dict",
        str(dictionary_path),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="00c",
        expected_check_ids={
            "fasta_structure",
            "fai_structure",
            "dict_structure",
            "fai_contig_agreement",
            "dict_contig_agreement",
        },
    )
    assert (
        tuple(path.read_bytes() for path in (fasta_path, fai_path, dictionary_path))
        == input_bytes
    )
    assert unrelated_path.read_text(encoding="utf-8") == "preserve\n"


def _build_star_alignment_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    output_directory = working_directory / "star-alignment-output"
    output_directory.mkdir()
    bam_path = output_directory / "wheel_fixture.Aligned.sortedByCoord.out.bam"
    bam_path.write_bytes(b"BAM\x01synthetic")
    final_log_path = output_directory / "wheel_fixture.Log.final.out"
    final_log_path.write_text(
        "Number of input reads | 100\n"
        "Uniquely mapped reads % | 90.00%\n"
        "% of reads mapped to multiple loci | 8.00%\n"
        "% of reads mapped to too many loci | 1.00%\n",
        encoding="utf-8",
    )
    log_path = output_directory / "wheel_fixture.Log.out"
    log_path.write_text("ALL DONE!\n", encoding="utf-8")
    progress_path = output_directory / "wheel_fixture.Log.progress.out"
    progress_path.write_text("ALL DONE!\n", encoding="utf-8")
    splice_junction_path = output_directory / "wheel_fixture.SJ.out.tab"
    splice_junction_path.write_text(
        "1\t10\t20\t1\t1\t0\t1\t0\t1\n",
        encoding="utf-8",
    )
    validation_directory = working_directory / "star-alignment-validation"
    validation_directory.mkdir()
    return (
        bam_path,
        final_log_path,
        log_path,
        progress_path,
        splice_junction_path,
        validation_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_star_alignment_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    *input_paths, output_path = _build_star_alignment_fixture(working_directory)
    input_bytes = tuple(path.read_bytes() for path in input_paths)
    unrelated_path = working_directory / "star-alignment-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "star-alignment",
        "--scope-id",
        "wheel_fixture",
        "--bam",
        str(input_paths[0]),
        "--log-final",
        str(input_paths[1]),
        "--log-out",
        str(input_paths[2]),
        "--log-progress",
        str(input_paths[3]),
        "--sj-out",
        str(input_paths[4]),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="01",
        expected_check_ids={
            "output_files",
            "bam_structure",
            "final_log_structure",
            "mapping_summary",
            "splice_junction_structure",
        },
    )
    assert tuple(path.read_bytes() for path in input_paths) == input_bytes
    assert unrelated_path.read_text(encoding="utf-8") == "preserve\n"


def _build_canonical_bam_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path]:
    input_directory = working_directory / "canonical-bam-inputs"
    input_directory.mkdir()
    bam_path = input_directory / "wheel_fixture.sorted.bam"
    bam_path.write_bytes(b"BAM\x01synthetic")
    bai_path = input_directory / "wheel_fixture.sorted.bam.bai"
    bai_path.write_bytes(b"BAI\x01synthetic")
    samtools_path = input_directory / "samtools"
    samtools_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'case "${1:-} ${2:-}" in\n'
        "  'quickcheck -v') exit 0 ;;\n"
        "  'view -H')\n"
        "    printf '@HD\\tVN:1.6\\tSO:coordinate\\n"
        "@RG\\tID:wheel_fixture\\tSM:wheel_fixture\\n' ;;\n"
        "  'view -c') printf '10\\n' ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    samtools_path.chmod(0o755)
    validation_directory = working_directory / "canonical-bam-validation"
    validation_directory.mkdir()
    return (
        bam_path,
        bai_path,
        samtools_path,
        validation_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_canonical_bam_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    bam_path, bai_path, samtools_path, output_path = _build_canonical_bam_fixture(
        working_directory
    )
    input_paths = (bam_path, bai_path, samtools_path)
    input_states = tuple(
        (path.read_bytes(), path.stat().st_mode) for path in input_paths
    )
    unrelated_path = working_directory / "canonical-bam-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "canonical-bam",
        "--scope-id",
        "wheel_fixture",
        "--bam",
        str(bam_path),
        "--bai",
        str(bai_path),
        "--samtools-bin",
        str(samtools_path),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="02",
        expected_check_ids={
            "bam_bai_structure",
            "samtools_quickcheck",
            "coordinate_sorting",
            "read_group_header",
            "alignment_rg_tags",
        },
    )
    assert (
        tuple((path.read_bytes(), path.stat().st_mode) for path in input_paths)
        == input_states
    )
    assert unrelated_path.read_text(encoding="utf-8") == "preserve\n"


def _build_canonical_bam_qc_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path]:
    input_directory = working_directory / "canonical-bam-qc-inputs"
    input_directory.mkdir()
    quickcheck_path = input_directory / "wheel_fixture.quickcheck.txt"
    quickcheck_path.write_text(
        "PASS: samtools quickcheck completed with no errors.\n",
        encoding="utf-8",
    )
    flagstat_path = input_directory / "wheel_fixture.flagstat.txt"
    flagstat_path.write_text(
        "10 + 0 in total (QC-passed reads + QC-failed reads)\n"
        "8 + 0 mapped (80.00% : N/A)\n",
        encoding="utf-8",
    )
    validation_directory = working_directory / "canonical-bam-qc-validation"
    validation_directory.mkdir()
    return (
        quickcheck_path,
        flagstat_path,
        validation_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_canonical_bam_qc_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    quickcheck_path, flagstat_path, output_path = _build_canonical_bam_qc_fixture(
        working_directory
    )
    input_paths = (quickcheck_path, flagstat_path)
    input_states = tuple(
        (path.read_bytes(), path.stat().st_mode) for path in input_paths
    )
    unrelated_path = working_directory / "canonical-bam-qc-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")
    unrelated_state = (unrelated_path.read_bytes(), unrelated_path.stat().st_mode)

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "canonical-bam-qc",
        "--scope-id",
        "wheel_fixture",
        "--quickcheck",
        str(quickcheck_path),
        "--flagstat",
        str(flagstat_path),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="02b",
        expected_check_ids={
            "quickcheck_structure",
            "flagstat_structure",
            "total_records",
            "mapped_records",
            "count_consistency",
        },
    )
    assert (
        tuple((path.read_bytes(), path.stat().st_mode) for path in input_paths)
        == input_states
    )
    assert (unrelated_path.read_bytes(), unrelated_path.stat().st_mode) == (
        unrelated_state
    )


def _build_rseqc_orientation_fixture(
    working_directory: Path,
) -> tuple[Path, Path]:
    input_directory = working_directory / "rseqc-orientation-inputs"
    input_directory.mkdir()
    report_path = input_directory / "wheel_fixture.infer_experiment.txt"
    report_path.write_text(
        "Fraction of reads failed to determine: 0.01\n"
        'Fraction of reads explained by "1++,1--,2+-,2-+": 0.97\n'
        'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n',
        encoding="utf-8",
    )
    validation_directory = working_directory / "rseqc-orientation-validation"
    validation_directory.mkdir()
    return report_path, validation_directory / "wheel_fixture.validation.tsv"


def _assert_installed_rseqc_orientation_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    report_path, output_path = _build_rseqc_orientation_fixture(working_directory)
    input_state = (report_path.read_bytes(), report_path.stat().st_mode)
    unrelated_path = working_directory / "rseqc-orientation-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")
    unrelated_state = (unrelated_path.read_bytes(), unrelated_path.stat().st_mode)

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "rseqc-orientation",
        "--scope-id",
        "wheel_fixture",
        "--infer-report",
        str(report_path),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="03",
        expected_check_ids={
            "report_structure",
            "failed_fraction",
            "paired_orientation_fraction_a",
            "paired_orientation_fraction_b",
            "fraction_sum",
        },
    )
    assert (report_path.read_bytes(), report_path.stat().st_mode) == input_state
    assert (unrelated_path.read_bytes(), unrelated_path.stat().st_mode) == (
        unrelated_state
    )


def _build_duplicate_marking_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path, Path]:
    input_directory = working_directory / "duplicate-marking-inputs"
    input_directory.mkdir()
    bam_path = input_directory / "wheel_fixture.markdup.bam"
    bam_path.write_bytes(b"BAM\x01synthetic")
    bai_path = input_directory / "wheel_fixture.markdup.bam.bai"
    bai_path.write_bytes(b"BAI\x01synthetic")
    metrics_path = input_directory / "wheel_fixture.markdup.metrics.txt"
    metrics_path.write_text(
        "## METRICS CLASS picard.sam.DuplicationMetrics\n"
        "LIBRARY\tREAD_PAIRS_EXAMINED\tREAD_PAIR_DUPLICATES\t"
        "PERCENT_DUPLICATION\n"
        "wheel_fixture\t10\t2\t0.2\n",
        encoding="utf-8",
    )
    samtools_path = input_directory / "samtools"
    samtools_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'case "${1:-} ${2:-}" in\n'
        "  'quickcheck -v') exit 0 ;;\n"
        "  'view -H')\n"
        "    printf '@HD\\tVN:1.6\\tSO:coordinate\\n"
        "@RG\\tID:wheel_fixture\\tSM:wheel_fixture\\n' ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    samtools_path.chmod(0o755)
    validation_directory = working_directory / "duplicate-marking-validation"
    validation_directory.mkdir()
    return (
        bam_path,
        bai_path,
        metrics_path,
        samtools_path,
        validation_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_duplicate_marking_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    *input_paths, output_path = _build_duplicate_marking_fixture(working_directory)
    input_states = tuple(
        (path.read_bytes(), path.stat().st_mode) for path in input_paths
    )
    unrelated_path = working_directory / "duplicate-marking-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")
    unrelated_state = (unrelated_path.read_bytes(), unrelated_path.stat().st_mode)

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "duplicate-marking",
        "--scope-id",
        "wheel_fixture",
        "--bam",
        str(input_paths[0]),
        "--bai",
        str(input_paths[1]),
        "--metrics",
        str(input_paths[2]),
        "--samtools-bin",
        str(input_paths[3]),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="04",
        expected_check_ids={
            "bam_bai_structure",
            "samtools_quickcheck",
            "coordinate_sorting",
            "read_group_preservation",
            "duplication_metrics",
        },
    )
    assert (
        tuple((path.read_bytes(), path.stat().st_mode) for path in input_paths)
        == input_states
    )
    assert (unrelated_path.read_bytes(), unrelated_path.stat().st_mode) == (
        unrelated_state
    )


def _build_split_n_cigar_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    input_directory = working_directory / "split-n-cigar-inputs"
    input_directory.mkdir()
    bam_path = input_directory / "wheel_fixture.split_ncigar.bam"
    bam_path.write_bytes(b"BAM\x01synthetic")
    bai_path = input_directory / "wheel_fixture.split_ncigar.bam.bai"
    bai_path.write_bytes(b"BAI\x01synthetic")
    fasta_path = input_directory / "genome.fa"
    fasta_path.write_text(">1\nACGT\n", encoding="utf-8")
    fai_path = input_directory / "genome.fa.fai"
    fai_path.write_text("1\t4\t3\t4\t5\n", encoding="utf-8")
    dictionary_path = input_directory / "genome.dict"
    dictionary_path.write_text(
        "@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n",
        encoding="utf-8",
    )
    samtools_path = input_directory / "samtools"
    samtools_path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'case "${1:-} ${2:-}" in\n'
        "  'quickcheck -v') exit 0 ;;\n"
        "  'view -H')\n"
        "    printf '@HD\\tVN:1.6\\tSO:coordinate\\n"
        "@RG\\tID:wheel_fixture\\tSM:wheel_fixture\\n' ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    samtools_path.chmod(0o755)
    validation_directory = working_directory / "split-n-cigar-validation"
    validation_directory.mkdir()
    return (
        bam_path,
        bai_path,
        fasta_path,
        fai_path,
        dictionary_path,
        samtools_path,
        validation_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_split_n_cigar_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    *input_paths, output_path = _build_split_n_cigar_fixture(working_directory)
    input_states = tuple(
        (path.read_bytes(), path.stat().st_mode) for path in input_paths
    )
    unrelated_path = working_directory / "split-n-cigar-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")
    unrelated_state = (unrelated_path.read_bytes(), unrelated_path.stat().st_mode)

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "split-n-cigar",
        "--scope-id",
        "wheel_fixture",
        "--bam",
        str(input_paths[0]),
        "--bai",
        str(input_paths[1]),
        "--reference-fasta",
        str(input_paths[2]),
        "--reference-fai",
        str(input_paths[3]),
        "--reference-dict",
        str(input_paths[4]),
        "--samtools-bin",
        str(input_paths[5]),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="05",
        expected_check_ids={
            "bam_bai_structure",
            "samtools_quickcheck",
            "coordinate_sorting",
            "read_group_preservation",
            "reference_sidecars",
        },
    )
    assert (
        tuple((path.read_bytes(), path.stat().st_mode) for path in input_paths)
        == input_states
    )
    assert (unrelated_path.read_bytes(), unrelated_path.stat().st_mode) == (
        unrelated_state
    )


def _build_mechanical_orientation_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    input_directory = working_directory / "mechanical-orientation-inputs"
    input_directory.mkdir()
    fwd_bam_path = input_directory / "wheel_fixture.FWD_like.bam"
    fwd_bam_path.write_bytes(b"BAM\x01synthetic")
    fwd_bai_path = input_directory / "wheel_fixture.FWD_like.bam.bai"
    fwd_bai_path.write_bytes(b"BAI\x01synthetic")
    rev_bam_path = input_directory / "wheel_fixture.REV_like.bam"
    rev_bam_path.write_bytes(b"BAM\x01synthetic")
    rev_bai_path = input_directory / "wheel_fixture.REV_like.bam.bai"
    rev_bai_path.write_bytes(b"BAI\x01synthetic")
    counts_path = input_directory / "wheel_fixture.orientation_counts.tsv"
    counts_path.write_text(
        "sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        "flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        "assigned_records\tunassigned_records\tassigned_fraction\n"
        "wheel_fixture\t10\t3\t2\t2\t1\t5\t3\t8\t2\t0.800000\n",
        encoding="utf-8",
    )
    validation_directory = working_directory / "mechanical-orientation-validation"
    validation_directory.mkdir()
    return (
        fwd_bam_path,
        fwd_bai_path,
        rev_bam_path,
        rev_bai_path,
        counts_path,
        validation_directory / "wheel_fixture.validation.tsv",
    )


def _assert_installed_mechanical_orientation_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    (
        fwd_bam_path,
        fwd_bai_path,
        rev_bam_path,
        rev_bai_path,
        counts_path,
        output_path,
    ) = _build_mechanical_orientation_fixture(working_directory)
    input_paths = (
        fwd_bam_path,
        fwd_bai_path,
        rev_bam_path,
        rev_bai_path,
        counts_path,
    )
    input_states = tuple(
        (path.read_bytes(), path.stat().st_mode) for path in input_paths
    )
    unrelated_path = working_directory / "mechanical-orientation-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")
    unrelated_state = (unrelated_path.read_bytes(), unrelated_path.stat().st_mode)

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "mechanical-orientation",
        "--scope-id",
        "wheel_fixture",
        "--fwd-bam",
        str(fwd_bam_path),
        "--fwd-bai",
        str(fwd_bai_path),
        "--rev-bam",
        str(rev_bam_path),
        "--rev-bai",
        str(rev_bai_path),
        "--counts",
        str(counts_path),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="06",
        expected_check_ids={
            "output_containers",
            "counts_structure",
            "fwd_count_arithmetic",
            "rev_count_arithmetic",
            "assigned_count_arithmetic",
        },
    )
    assert (
        tuple((path.read_bytes(), path.stat().st_mode) for path in input_paths)
        == input_states
    )
    assert (unrelated_path.read_bytes(), unrelated_path.stat().st_mode) == (
        unrelated_state
    )


def _build_partitioned_cohort_mpileup_fixture(
    working_directory: Path,
) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    input_directory = working_directory / "partitioned-cohort-mpileup-inputs"
    input_directory.mkdir()
    sample_manifest_path = input_directory / "samples.tsv"
    sample_manifest_path.write_text(
        "sample_id\tcondition\nS1\tx\nS2\ty\n",
        encoding="utf-8",
    )
    partition_manifest_path = input_directory / "partitions.tsv"
    partition_manifest_path.write_text(
        "partition_id\tselector_type\tselector_value\np1\tregion\t1:1-10\n",
        encoding="utf-8",
    )
    reference_fai_path = input_directory / "genome.fa.fai"
    reference_fai_path.write_text("1\t100\t0\t80\t81\n", encoding="utf-8")
    vcf_header = (
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\tS2\n"
    )
    fwd_vcf_path = input_directory / "wheel_cohort.p1.FWD_like.mpileup.vcf"
    fwd_vcf_path.write_text(
        vcf_header + "1\t2\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/0\n",
        encoding="utf-8",
    )
    rev_vcf_path = input_directory / "wheel_cohort.p1.REV_like.mpileup.vcf"
    rev_vcf_path.write_text(vcf_header, encoding="utf-8")
    sample_manifest_sha256 = hashlib.sha256(
        sample_manifest_path.read_bytes()
    ).hexdigest()
    partition_manifest_sha256 = hashlib.sha256(
        partition_manifest_path.read_bytes()
    ).hexdigest()
    receipt_path = input_directory / "wheel_cohort.p1.step07_outputs.tsv"
    receipt_path.write_text(
        "cohort_id\tpartition_id\tselector_type\tselector_value\torientation\t"
        "vcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\t"
        "sample_count\tvcf_record_count\n"
        f"wheel_cohort\tp1\tregion\t1:1-10\tFWD_like\t{fwd_vcf_path}\t"
        f"{sample_manifest_sha256}\t{partition_manifest_sha256}\t2\t1\n"
        f"wheel_cohort\tp1\tregion\t1:1-10\tREV_like\t{rev_vcf_path}\t"
        f"{sample_manifest_sha256}\t{partition_manifest_sha256}\t2\t0\n",
        encoding="utf-8",
    )
    validation_directory = working_directory / "partitioned-cohort-mpileup-validation"
    validation_directory.mkdir()
    return (
        sample_manifest_path,
        partition_manifest_path,
        reference_fai_path,
        fwd_vcf_path,
        rev_vcf_path,
        receipt_path,
        validation_directory / "wheel_cohort__p1.validation.tsv",
    )


def _assert_installed_partitioned_cohort_mpileup_validation(
    environment_python: Path,
    working_directory: Path,
    environment: dict[str, str],
) -> None:
    (
        sample_manifest_path,
        partition_manifest_path,
        reference_fai_path,
        fwd_vcf_path,
        rev_vcf_path,
        receipt_path,
        output_path,
    ) = _build_partitioned_cohort_mpileup_fixture(working_directory)
    input_paths = (
        sample_manifest_path,
        partition_manifest_path,
        reference_fai_path,
        fwd_vcf_path,
        rev_vcf_path,
        receipt_path,
    )
    input_states = tuple(
        (path.read_bytes(), path.stat().st_mode) for path in input_paths
    )
    unrelated_path = working_directory / "partitioned-cohort-mpileup-unrelated.txt"
    unrelated_path.write_text("preserve\n", encoding="utf-8")
    unrelated_state = (unrelated_path.read_bytes(), unrelated_path.stat().st_mode)

    validation = _run_installed_norad(
        environment_python,
        working_directory,
        environment,
        "validate",
        "partitioned-cohort-mpileup",
        "--cohort-id",
        "wheel_cohort",
        "--partition-id",
        "p1",
        "--sample-manifest",
        str(sample_manifest_path),
        "--partition-manifest",
        str(partition_manifest_path),
        "--reference-fai",
        str(reference_fai_path),
        "--fwd-vcf",
        str(fwd_vcf_path),
        "--rev-vcf",
        str(rev_vcf_path),
        "--receipt",
        str(receipt_path),
        "--output",
        str(output_path),
    )
    _assert_validation_dry_run(
        validation,
        output_path,
        step_id="07",
        expected_check_ids={
            "receipt_structure",
            "vcf_structure",
            "selector_reconciliation",
            "manifest_identity_and_sample_order",
            "vcf_record_counts",
        },
    )
    assert (
        tuple((path.read_bytes(), path.stat().st_mode) for path in input_paths)
        == input_states
    )
    assert (unrelated_path.read_bytes(), unrelated_path.stat().st_mode) == (
        unrelated_state
    )


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
    _assert_installed_fasta_sidecars_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_star_alignment_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_canonical_bam_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_canonical_bam_qc_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_rseqc_orientation_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_duplicate_marking_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_split_n_cigar_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_mechanical_orientation_validation(
        environment_python,
        working_directory,
        environment,
    )
    _assert_installed_partitioned_cohort_mpileup_validation(
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

    normalized_owners = (
        (
            "stages/star_index",
            "stages/construct_STAR_index",
            "validate_step_00a_star_index.py",
        ),
        (
            "stages/fasta_sidecars",
            "stages/construct_FASTA_sidecars",
            "validate_step_00c_reference_sidecars.py",
        ),
        (
            "stages/star_alignment",
            "stages/align_RNA_reads_with_STAR",
            "validate_step_01_star_alignment.py",
        ),
        (
            "stages/canonical_bam",
            "stages/construct_canonical_BAM",
            "validate_step_02_canonical_bam.py",
        ),
        (
            "evidence/canonical_bam_qc",
            "evidence/collect_canonical_BAM_QC_evidence",
            "validate_step_02b_bam_qc.py",
        ),
        (
            "evidence/rseqc_orientation",
            "evidence/collect_RSeQC_paired_orientation_evidence",
            "validate_step_03_rseqc_orientation.py",
        ),
        (
            "stages/duplicate_marking",
            "stages/mark_BAM_duplicates_with_Picard",
            "validate_step_04_mark_duplicates.py",
        ),
        (
            "stages/split_n_cigar",
            "stages/split_N_cigar_reads_with_GATK",
            "validate_step_05_split_ncigar.py",
        ),
        (
            "stages/mechanical_orientation",
            "stages/partition_BAM_by_mechanical_read_orientation",
            "validate_step_06_orientation_outputs.py",
        ),
        (
            "stages/partitioned_cohort_mpileup",
            "stages/generate_partitioned_cohort_mpileup_VCFs",
            "validate_step_07_mpileup_outputs.py",
        ),
    )
    for current_relative, retired_relative, retired_validator in normalized_owners:
        current_source = REPO_ROOT / "src/norad" / current_relative
        assert not (REPO_ROOT / "src/norad" / retired_relative).exists()
        assert not (current_source / retired_validator).exists()
        assert (current_source / "validator.py").stat().st_mode & 0o111 == 0
        assert not (REPO_ROOT / "tests" / retired_relative).exists()
        assert (REPO_ROOT / "tests" / current_relative).is_dir()


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
