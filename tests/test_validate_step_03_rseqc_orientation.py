import csv
import subprocess
import sys
from pathlib import Path

from validation_roster_expectations import assert_exact_check_roster

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_03_rseqc_orientation.py"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    source = root / "S.infer_experiment.txt"
    source.write_text(
        "Fraction of reads failed to determine: 0.01\n"
        'Fraction of reads explained by "1++,1--,2+-,2-+": 0.97\n'
        'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n'
    )
    out = root / "out"; out.mkdir()
    return source, out / "S.validation.tsv"


def run(values, *extra):
    source, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S",
         "--infer-report", str(source), "--output", str(output), *extra],
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
    assert_exact_check_roster(rows(values[-1]), "03")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_invalid_fraction_and_sum_are_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[0].write_text(
        "Fraction of reads failed to determine: 0.01\n"
        'Fraction of reads explained by "1++,1--,2+-,2-+": 1.20\n'
        'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n'
    )
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["paired_orientation_fraction_a"] == "fail"
    assert status["fraction_sum"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[0].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (values[0], values[1].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[-1].parent / f".{values[-1].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"
