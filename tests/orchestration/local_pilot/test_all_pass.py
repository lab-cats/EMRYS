from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from emrys.libraries import validation
from emrys.orchestration.local_pilot.all_pass import require_all_pass

REPO_ROOT = Path(__file__).resolve().parents[3]


def report_bytes(
    *rows: tuple[str, ...], header: tuple[str, ...] = validation.HEADER
) -> bytes:
    return (
        "\t".join(header) + "\n" + "".join("\t".join(row) + "\n" for row in rows)
    ).encode("utf-8")


def passing_row(check_id: str = "declared_output") -> tuple[str, ...]:
    return (
        "01",
        "sample_001",
        check_id,
        "pass",
        "present",
        "present",
        "validated",
    )


def run_cli(*arguments: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-m", "emrys", "validate", "all-pass", *arguments],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_require_all_pass_returns_content_bound_ordered_evidence(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sample_001.validation.tsv"
    data = report_bytes(passing_row("first"), passing_row("second"))
    path.write_bytes(data)
    before = path.read_bytes()

    evidence = require_all_pass(path, step_id="01", scope_id="sample_001")

    assert evidence.report_path == path.absolute()
    assert evidence.report_sha256 == hashlib.sha256(data).hexdigest()
    assert evidence.row_count == 2
    assert evidence.check_ids == ("first", "second")
    assert evidence.step_id == "01"
    assert evidence.scope_id == "sample_001"
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "must be nonempty"),
        (report_bytes(header=("wrong",)), "header is invalid"),
        (report_bytes(), "contains no check rows"),
        (
            report_bytes(("01", "sample_001", "short", "pass", "x", "y")),
            "has 6 fields; expected 7",
        ),
        (
            report_bytes(("02", "sample_001", "check", "pass", "x", "y", "z")),
            "wrong step/scope",
        ),
        (
            report_bytes(("01", "other", "check", "pass", "x", "y", "z")),
            "wrong step/scope",
        ),
        (
            report_bytes(("01", "sample_001", "", "pass", "x", "y", "z")),
            "empty check_id",
        ),
        (
            report_bytes(passing_row("same"), passing_row("same")),
            "repeats check_id",
        ),
        (
            report_bytes(("01", "sample_001", "failed", "fail", "x", "y", "z")),
            "not all-pass: failed=fail",
        ),
        (
            report_bytes(("01", "sample_001", "unknown", "skip", "x", "y", "z")),
            "not all-pass: unknown=skip",
        ),
    ],
)
def test_require_all_pass_rejects_nonpassing_or_malformed_reports(
    tmp_path: Path,
    data: bytes,
    message: str,
) -> None:
    path = tmp_path / "sample_001.validation.tsv"
    path.write_bytes(data)
    before = path.read_bytes()

    with pytest.raises(validation.ValidationError, match=message):
        require_all_pass(path, step_id="01", scope_id="sample_001")

    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_grouped_cli_reports_hash_count_and_check_ids_without_writes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sample_001.validation.tsv"
    data = report_bytes(passing_row("first"), passing_row("second"))
    path.write_bytes(data)
    before = path.read_bytes()
    invocation_cwd = tmp_path / "elsewhere"
    invocation_cwd.mkdir()

    result = run_cli(
        "--report",
        str(path),
        "--step-id",
        "01",
        "--scope-id",
        "sample_001",
        cwd=invocation_cwd,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "Validation report semantic all-pass: PASS" in result.stdout
    assert f"SHA-256: {hashlib.sha256(data).hexdigest()}" in result.stdout
    assert "Check rows: 2" in result.stdout
    assert "Check IDs: first,second" in result.stdout
    assert path.read_bytes() == before
    assert list(invocation_cwd.iterdir()) == []


def test_grouped_cli_returns_nonzero_for_zero_exit_validator_fail_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sample_001.validation.tsv"
    path.write_bytes(
        report_bytes(
            ("01", "sample_001", "scientific_check", "fail", "0", "1", "failed")
        )
    )
    before = path.read_bytes()

    result = run_cli(
        "--report",
        str(path),
        "--step-id",
        "01",
        "--scope-id",
        "sample_001",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "not all-pass: scientific_check=fail" in result.stderr
    assert path.read_bytes() == before


def test_grouped_cli_help_is_available() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "--report" in result.stdout
    assert "--step-id" in result.stdout
    assert "--scope-id" in result.stdout
