import csv
import subprocess
import sys
from pathlib import Path

from validation_roster_expectations import assert_exact_check_roster

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_06_orientation_outputs.py"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    fwd_bam = root / "S.FWD_like.bam"; fwd_bam.write_bytes(b"BAM\x01synthetic")
    fwd_bai = root / "S.FWD_like.bam.bai"; fwd_bai.write_bytes(b"BAI\x01synthetic")
    rev_bam = root / "S.REV_like.bam"; rev_bam.write_bytes(b"BAM\x01synthetic")
    rev_bai = root / "S.REV_like.bam.bai"; rev_bai.write_bytes(b"BAI\x01synthetic")
    counts = root / "S.orientation_counts.tsv"
    counts.write_text(
        "sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        "flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        "assigned_records\tunassigned_records\tassigned_fraction\n"
        "S\t10\t3\t2\t2\t1\t5\t3\t8\t2\t0.800000\n"
    )
    out = root / "out"; out.mkdir()
    return fwd_bam, fwd_bai, rev_bam, rev_bai, counts, out / "S.validation.tsv"


def run(values, *extra):
    fwd_bam, fwd_bai, rev_bam, rev_bai, counts, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S",
         "--fwd-bam", str(fwd_bam), "--fwd-bai", str(fwd_bai),
         "--rev-bam", str(rev_bam), "--rev-bai", str(rev_bai),
         "--counts", str(counts), "--output", str(output), *extra],
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
    assert_exact_check_roster(rows(values[-1]), "06")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_count_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[4].write_text(
        "sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        "flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        "assigned_records\tunassigned_records\tassigned_fraction\n"
        "S\t10\t3\t2\t2\t1\t6\t3\t8\t2\t0.700000\n"
    )
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["fwd_count_arithmetic"] == "fail"
    assert status["assigned_count_arithmetic"] == "fail"


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
