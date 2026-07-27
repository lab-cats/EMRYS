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
    normalized_help = " ".join(result.stdout.split())

    assert result.returncode == 0
    assert "--manifest" in result.stdout
    assert "--base-dir" in result.stdout
    assert "--check-files" in result.stdout
    assert "regular files" in normalized_help


def test_legacy_manifest_without_replicate_is_allowed(tmp_path: Path) -> None:
    manifest = write_manifest(tmp_path / "samples.tsv", valid_header(), valid_rows())

    result = run_validator("--manifest", str(manifest))

    assert result.returncode == 0
    assert "Manifest validation passed." in result.stdout
    assert "Samples: 2" in result.stdout
    assert "Conditions: control, treatment" in result.stdout
    assert "Strandedness values: forward, reverse" in result.stdout


def test_optional_replicate_column_is_allowed(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header() + ["replicate"],
        [
            [
                "sample_001",
                "reads/sample_001_R1.fastq.gz",
                "reads/sample_001_R2.fastq.gz",
                "reverse",
                "control",
                "1",
            ],
            [
                "sample_002",
                "reads/sample_002_R1.fastq.gz",
                "reads/sample_002_R2.fastq.gz",
                "reverse",
                "treatment",
                "1",
            ],
        ],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode == 0
    assert "Manifest validation passed." in result.stdout
    assert "Samples: 2" in result.stdout


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


def test_duplicate_and_empty_header_names_fail(tmp_path: Path) -> None:
    duplicate = write_manifest(
        tmp_path / "duplicate.tsv",
        valid_header() + [" sample_id "],
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "reverse", "control", "duplicate"]],
    )
    empty = write_manifest(
        tmp_path / "empty.tsv",
        valid_header() + ["   "],
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "reverse", "control", "value"]],
    )

    duplicate_result = run_validator("--manifest", str(duplicate))
    empty_result = run_validator("--manifest", str(empty))

    assert duplicate_result.returncode != 0
    assert "Duplicate column name(s): sample_id" in duplicate_result.stderr
    assert empty_result.returncode != 0
    assert "Header contains an empty column name" in empty_result.stderr


def test_extra_fields_fail_even_when_the_extra_field_is_empty(tmp_path: Path) -> None:
    with_value = write_manifest(
        tmp_path / "extra-value.tsv",
        valid_header(),
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "reverse", "control", "unexpected"]],
    )
    empty_value = write_manifest(
        tmp_path / "extra-empty.tsv",
        valid_header(),
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "reverse", "control", ""]],
    )

    with_value_result = run_validator("--manifest", str(with_value))
    empty_value_result = run_validator("--manifest", str(empty_value))

    assert with_value_result.returncode != 0
    assert (
        "Row 2: too many tab-separated fields: unexpected"
        in with_value_result.stderr
    )
    assert empty_value_result.returncode != 0
    assert "Row 2: too many tab-separated fields" in empty_value_result.stderr


def test_blank_lines_and_blank_rows_are_ignored(tmp_path: Path) -> None:
    manifest = tmp_path / "samples.tsv"
    manifest.write_text(
        "\t".join(valid_header())
        + "\n\n"
        + "\t".join(valid_rows()[0])
        + "\n\t\t\t\t\n"
        + "\t".join(valid_rows()[1])
        + "\n"
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode == 0, result.stderr
    assert "Samples: 2" in result.stdout


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


def test_empty_condition_fails(tmp_path: Path) -> None:
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header(),
        [["sample_001", "R1.fastq.gz", "R2.fastq.gz", "reverse", ""]],
    )

    result = run_validator("--manifest", str(manifest))

    assert result.returncode != 0
    assert "Row 2: condition must be non-empty" in result.stderr


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


def test_fastq_directories_fail_when_check_files_is_set(tmp_path: Path) -> None:
    reads_dir = tmp_path / "reads"
    r1_dir = reads_dir / "sample_001_R1.fastq.gz"
    r2 = reads_dir / "sample_001_R2.fastq.gz"
    r1_dir.mkdir(parents=True)
    r2.write_text("")
    manifest = write_manifest(
        tmp_path / "samples.tsv",
        valid_header(),
        [
            [
                "sample_001",
                "reads/sample_001_R1.fastq.gz",
                "reads/sample_001_R2.fastq.gz",
                "reverse",
                "control",
            ]
        ],
    )

    result = run_validator(
        "--manifest",
        str(manifest),
        "--base-dir",
        str(tmp_path),
        "--check-files",
    )

    assert result.returncode != 0
    assert "Row 2: r1_fastq is not a regular file:" in result.stderr


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
