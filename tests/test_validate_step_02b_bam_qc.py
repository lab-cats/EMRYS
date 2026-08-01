import csv
import subprocess
import sys
from pathlib import Path

from validation_roster_expectations import assert_exact_check_roster

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_02b_bam_qc.py"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    quick = root / "S.quickcheck.txt"
    quick.write_text("PASS: samtools quickcheck completed with no errors.\n")
    flag = root / "S.flagstat.txt"
    flag.write_text(
        "10 + 0 in total (QC-passed reads + QC-failed reads)\n"
        "8 + 0 mapped (80.00% : N/A)\n"
    )
    out = root / "out"; out.mkdir()
    return quick, flag, out / "S.validation.tsv"


def run(values, *extra):
    quick, flag, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S",
         "--quickcheck", str(quick), "--flagstat", str(flag),
         "--output", str(output), *extra],
        cwd=ROOT, text=True, capture_output=True,
    )


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[-1].exists()


def test_execute_publishes_five_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "02b")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_bad_quickcheck_and_counts_are_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[0].write_text("FAIL\n")
    values[1].write_text(
        "10 + 0 in total (QC-passed reads + QC-failed reads)\n"
        "11 + 0 mapped (110.00% : N/A)\n"
    )
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["quickcheck_structure"] == "fail"
    assert status["count_consistency"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[0].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (*values[:-1], values[-1].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[-1].parent / f".{values[-1].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"
