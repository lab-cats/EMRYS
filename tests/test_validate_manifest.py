import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate_manifest.py"


def write_manifest(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    lines = ["\t".join(header)]
    lines.extend("\t".join(row) for row in rows)
    path.write_text("\n".join(lines) + "\n")
    return path


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def valid_header() -> list[str]:
    return ["sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition"]


def valid_rows() -> list[list[str]]:
    return [
        ["sample_001", "reads/sample_001_R1.fastq.gz", "reads/sample_001_R2.fastq.gz", "reverse", "control"],
        ["sample_002", "reads/sample_002_R1.fastq.gz", "reads/sample_002_R2.fastq.gz", "forward", "treatment"],
    ]


def test_help_interface() -> None:
    result = run_validator("--help")

    assert result.returncode == 0
    assert "--manifest" in result.stdout
    assert "--base-dir" in result.stdout
    assert "--check-files" in result.stdout


def test_valid_manifest_without_file_checks(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path / "samples.tsv", valid_header(), valid_rows())

    result = run_validator("--manifest", str(manifest))

    assert result.returncode == 0
    assert "Manifest validation passed." in result.stdout
    assert "Samples: 2" in result.stdout
    assert "Conditions: control, treatment" in result.stdout
    assert "Strandedness values: forward, reverse" in result.stdout


def test_valid_manifest_with_file_checks(tmp_path: Path) -> None:
    reads_dir = tmp_path / "reads"
    reads_dir.mkdir()
    for filename in (
        "sample_001_R1.fastq.gz",
        "sample_001_R2.fastq.gz",
        "sample_002_R1.fastq.gz",
        "sample_002_R2.fastq.gz",
    ):
        (reads_dir / filename).write_text("")
    manifest = write_manifest(tmp_path / "samples.tsv", valid_header(), valid_rows())

    result = run_validator(
        "--manifest",
        str(manifest),
        "--base-dir",
        str(tmp_path),
        "--check-files",
    )

    assert result.returncode == 0
    assert "Samples: 2" in result.stdout


def test_optional_notes_column_is_allowed(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header() + ["notes"],
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "unknown", "control", "pilot sample"]],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode == 0
    assert "Strandedness values: unknown" in result.stdout


def test_missing_required_column_fails(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        ["sample_id", "r1_fastq", "strandedness", "condition"],
        [["sample_001", "R1.fastq.gz", "reverse", "control"]],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode != 0
    assert "Missing required column(s): r2_fastq" in result.stderr


def test_unexpected_column_fails(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header() + ["batch"],
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "reverse", "control", "A"]],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode != 0
    assert "Unexpected column(s): batch" in result.stderr


def test_duplicate_sample_id_fails(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header(),
        [
            ["sample_001", "R1.fastq.gz", "R2.fastq.gz", "reverse", "control"],
            ["sample_001", "R1b.fastq.gz", "R2b.fastq.gz", "reverse", "control"],
        ],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode != 0
    assert "Row 3: duplicate sample_id 'sample_001' (first seen on row 2)" in result.stderr


def test_empty_required_fields_fail(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header(),
        [["", "", "", "reverse", "control"]],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode != 0
    assert "Row 2: sample_id must be non-empty" in result.stderr
    assert "Row 2: r1_fastq must be non-empty" in result.stderr
    assert "Row 2: r2_fastq must be non-empty" in result.stderr


def test_invalid_strandedness_fails(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header(),
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "antisense", "control"]],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode != 0
    assert "Row 2: strandedness must be one of" in result.stderr
    assert "got 'antisense'" in result.stderr


def test_header_only_manifest_fails(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path / "samples.tsv", valid_header(), [])

    result = run_validator("--manifest", str(manifest))

    assert result.returncode != 0
    assert "Manifest must contain at least one sample row" in result.stderr


def test_missing_fastq_files_fail_when_check_files_is_set(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path / "samples.tsv", valid_header(), valid_rows())

    result = run_validator(
        "--manifest",
        str(manifest),
        "--base-dir",
        str(tmp_path),
        "--check-files",
    )

    assert result.returncode != 0
    assert "Row 2: r1_fastq file does not exist:" in result.stderr
    assert "reads/sample_001_R1.fastq.gz" in result.stderr


def test_absolute_fastq_path_is_checked_directly(tmp_path: Path) -> None:
    r1 = tmp_path / "absolute_R1.fastq.gz"
    r2 = tmp_path / "absolute_R2.fastq.gz"
    r1.write_text("")
    r2.write_text("")
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header(),
        [["sample_001", str(r1), str(r2), "unstranded", "control"]],
    )

    result = run_validator(
        "--manifest",
        str(manifest),
        "--base-dir",
        str(tmp_path / "unused"),
        "--check-files",
    )

    assert result.returncode == 0
    assert "Strandedness values: unstranded" in result.stdout
