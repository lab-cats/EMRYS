import csv
import subprocess
import sys
from pathlib import Path

from validation_roster_expectations import assert_exact_check_roster

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_04_mark_duplicates.py"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.markdup.bam"; bam.write_bytes(b"BAM\x01synthetic")
    bai = root / "S.markdup.bam.bai"; bai.write_bytes(b"BAI\x01synthetic")
    metrics = root / "S.markdup.metrics.txt"
    metrics.write_text(
        "## METRICS CLASS picard.sam.DuplicationMetrics\n"
        "LIBRARY\tREAD_PAIRS_EXAMINED\tREAD_PAIR_DUPLICATES\tPERCENT_DUPLICATION\n"
        "S\t10\t2\t0.2\n"
    )
    tool = root / "samtools"
    tool.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        "case \"$1 $2\" in\n"
        " 'quickcheck -v') exit \"${QUICKCHECK_EXIT:-0}\" ;;\n"
        " 'view -H') printf '@HD\\tVN:1.6\\tSO:%s\\n@RG\\tID:%s\\tSM:%s\\n' "
        "\"${SORT_ORDER:-coordinate}\" \"${RG_ID:-S}\" \"${RG_SM:-S}\" ;;\n"
        " *) exit 9 ;;\nesac\n"
    )
    tool.chmod(0o755)
    out = root / "out"; out.mkdir()
    return bam, bai, metrics, tool, out / "S.validation.tsv"


def run(values, *extra, env=None):
    bam, bai, metrics, tool, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S", "--bam", str(bam),
         "--bai", str(bai), "--metrics", str(metrics),
         "--samtools-bin", str(tool), "--output", str(output), *extra],
        cwd=ROOT, text=True, capture_output=True, env=env,
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
    assert_exact_check_roster(rows(values[-1]), "04")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_bad_header_and_metrics_are_failed_evidence(tmp_path):
    import os
    values = fixture(tmp_path)
    values[2].write_text("LIBRARY\tPERCENT_DUPLICATION\nS\t2\n")
    env = dict(os.environ, SORT_ORDER="queryname", RG_ID="wrong")
    assert run(values, "--execute", env=env).returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["coordinate_sorting"] == "fail"
    assert status["read_group_preservation"] == "fail"
    assert status["duplication_metrics"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[2].unlink()
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
