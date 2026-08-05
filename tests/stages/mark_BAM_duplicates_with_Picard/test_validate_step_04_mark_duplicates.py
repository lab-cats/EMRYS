import csv
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = ROOT / "tests" / "contract_integration" / "validation_rosters" / "validation_roster_expectations.py"
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "mark_duplicates_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src/norad/stages/mark_BAM_duplicates_with_Picard/"
    "validate_step_04_mark_duplicates.py"
)


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
        " 'view -H')\n"
        "   if [[ \"${VIEW_EXIT:-0}\" != 0 ]]; then\n"
        "     printf 'fake samtools header failure\\n' >&2\n"
        "     exit \"$VIEW_EXIT\"\n"
        "   fi\n"
        "   printf '@HD\\tVN:1.6\\tSO:%s\\n@RG\\tID:%s\\tSM:%s\\n' "
        "\"${SORT_ORDER:-coordinate}\" \"${RG_ID:-S}\" \"${RG_SM:-S}\"\n"
        "   if [[ -n \"${MUTATE_PATH:-}\" ]]; then\n"
        "     printf 'mutated-after-build\\n' >> \"$MUTATE_PATH\"\n"
        "   fi ;;\n"
        " *) exit 9 ;;\nesac\n"
    )
    tool.chmod(0o755)
    out = root / "out"; out.mkdir()
    return bam, bai, metrics, tool, out / "S.validation.tsv"


def run(values, *extra, env=None, cwd=ROOT):
    bam, bai, metrics, tool, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S", "--bam", str(bam),
         "--bai", str(bai), "--metrics", str(metrics),
         "--samtools-bin", str(tool), "--output", str(output), *extra],
        cwd=cwd, text=True, capture_output=True, env=env,
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


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_exact(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation = tmp_path / "invocation"
    invocation.mkdir()
    input_bytes = tuple(path.read_bytes() for path in values[:-1])

    dry_run = run(values, cwd=invocation)
    assert dry_run.returncode == 0, dry_run.stderr
    assert not values[-1].exists()
    assert list(invocation.iterdir()) == []

    first = run(values, "--execute", cwd=invocation)
    assert first.returncode == 0, first.stderr
    report_bytes = values[-1].read_bytes()
    assert dry_run.stdout.encode().startswith(report_bytes)
    assert_exact_check_roster(rows(values[-1]), "04")

    second = run(values, "--execute", cwd=invocation)
    assert second.returncode == 0, second.stderr
    assert values[-1].read_bytes() == report_bytes
    assert tuple(path.read_bytes() for path in values[:-1]) == input_bytes
    assert list(invocation.iterdir()) == []


def test_quickcheck_nonzero_publishes_failed_evidence_with_exit_zero(tmp_path):
    values = fixture(tmp_path)
    result = run(
        values,
        "--execute",
        env=dict(os.environ, QUICKCHECK_EXIT="17"),
    )

    assert result.returncode == 0, result.stderr
    report_rows = {row["check_id"]: row for row in rows(values[-1])}
    assert report_rows["samtools_quickcheck"]["status"] == "fail"
    assert report_rows["samtools_quickcheck"]["observed"] == "exit=17"
    assert {
        row["status"]
        for check_id, row in report_rows.items()
        if check_id != "samtools_quickcheck"
    } == {"pass"}


def test_header_tool_failure_preserves_valid_predecessor_report(tmp_path):
    values = fixture(tmp_path)
    first = run(values, "--execute")
    assert first.returncode == 0, first.stderr
    predecessor = values[-1].read_bytes()

    failed = run(
        values,
        "--execute",
        env=dict(os.environ, VIEW_EXIT="29"),
    )

    assert failed.returncode == 2
    assert failed.stdout == ""
    assert "samtools view -H failed: fake samtools header failure" in failed.stderr
    assert values[-1].read_bytes() == predecessor


def test_post_build_input_mutation_preserves_valid_predecessor_report(tmp_path):
    values = fixture(tmp_path)
    first = run(values, "--execute")
    assert first.returncode == 0, first.stderr
    predecessor = values[-1].read_bytes()
    original_bam = values[0].read_bytes()

    failed = run(
        values,
        "--execute",
        env=dict(os.environ, MUTATE_PATH=str(values[0])),
    )

    assert failed.returncode == 2
    assert "Input changed after validation" in failed.stderr
    assert values[0].read_bytes() == original_bam + b"mutated-after-build\n"
    assert values[-1].read_bytes() == predecessor
