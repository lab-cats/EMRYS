from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster


@dataclass(frozen=True, slots=True)
class AlignmentFixture:
    bam: Path
    final_log: Path
    general_log: Path
    progress_log: Path
    splice_junctions: Path
    output: Path


def build_validation_fixture(root: Path) -> AlignmentFixture:
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.Aligned.sortedByCoord.out.bam"
    bam.write_bytes(b"BAM\x01synthetic")
    final_log = root / "S.Log.final.out"
    final_log.write_text(
        "Number of input reads | 100\n"
        "Uniquely mapped reads % | 90.00%\n"
        "% of reads mapped to multiple loci | 8.00%\n"
        "% of reads mapped to too many loci | 1.00%\n",
        encoding="utf-8",
    )
    general_log = root / "S.Log.out"
    general_log.write_text("ALL DONE!\n", encoding="utf-8")
    progress_log = root / "S.Log.progress.out"
    progress_log.write_text("ALL DONE!\n", encoding="utf-8")
    splice_junctions = root / "S.SJ.out.tab"
    splice_junctions.write_text(
        "1\t10\t20\t1\t1\t0\t1\t0\t1\n",
        encoding="utf-8",
    )
    output_directory = root / "out"
    output_directory.mkdir()
    return AlignmentFixture(
        bam=bam,
        final_log=final_log,
        general_log=general_log,
        progress_log=progress_log,
        splice_junctions=splice_junctions,
        output=output_directory / "S.validation.tsv",
    )


def run_validator(
    alignment: AlignmentFixture,
    *extra: str,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad",
            "validate",
            "star-alignment",
            "--scope-id",
            "S",
            "--bam",
            str(alignment.bam),
            "--log-final",
            str(alignment.final_log),
            "--log-out",
            str(alignment.general_log),
            "--log-progress",
            str(alignment.progress_log),
            "--sj-out",
            str(alignment.splice_junctions),
            "--output",
            str(alignment.output),
            *extra,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    alignment = build_validation_fixture(tmp_path)
    assert run_validator(alignment).returncode == 0
    assert not alignment.output.exists()


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    alignment = build_validation_fixture(tmp_path)
    result = run_validator(alignment, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(alignment.output)
    assert_exact_check_roster(rows, "01")
    assert {row["status"] for row in rows} == {"pass"}


def test_bad_mapping_summary_and_sj_are_failed_evidence(tmp_path: Path) -> None:
    alignment = build_validation_fixture(tmp_path)
    alignment.final_log.write_text(
        "Uniquely mapped reads % | invalid\n",
        encoding="utf-8",
    )
    alignment.splice_junctions.write_text("1\t2\n", encoding="utf-8")
    assert run_validator(alignment, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in report_rows(alignment.output)}
    assert status["mapping_summary"] == "fail"
    assert status["splice_junction_structure"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    alignment = build_validation_fixture(tmp_path)
    alignment.general_log.unlink()
    assert run_validator(alignment, "--execute").returncode == 2
    valid_alignment = build_validation_fixture(tmp_path / "second")
    invalid_alignment = AlignmentFixture(
        bam=valid_alignment.bam,
        final_log=valid_alignment.final_log,
        general_log=valid_alignment.general_log,
        progress_log=valid_alignment.progress_log,
        splice_junctions=valid_alignment.splice_junctions,
        output=valid_alignment.output.parent / "wrong.tsv",
    )
    assert run_validator(invalid_alignment, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    alignment = build_validation_fixture(tmp_path)
    lock = alignment.output.parent / f".{alignment.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(alignment, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_non_repo_cwd_dry_run_execute_repeat_is_deterministic(
    tmp_path: Path,
) -> None:
    alignment = build_validation_fixture(tmp_path / "fixture")
    invocation = tmp_path / "invocation"
    invocation.mkdir()

    dry = run_validator(alignment, cwd=invocation)
    assert dry.returncode == 0
    assert dry.stderr == ""
    assert dry.stdout.endswith("Dry-run complete; no output was written.\n")
    assert not alignment.output.exists()

    first = run_validator(alignment, "--execute", cwd=invocation)
    assert first.returncode == 0
    assert first.stderr == ""
    first_bytes = alignment.output.read_bytes()

    second = run_validator(alignment, "--execute", cwd=invocation)
    assert second.returncode == 0
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert alignment.output.read_bytes() == first_bytes
    rows = report_rows(alignment.output)
    assert_exact_check_roster(rows, "01")
    assert {row["status"] for row in rows} == {"pass"}
    assert list(invocation.iterdir()) == []
    assert not [
        path for path in alignment.output.parent.iterdir() if path.name.startswith(".")
    ]
