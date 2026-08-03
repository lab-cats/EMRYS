import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = ROOT / "tests" / "validation_roster_expectations.py"
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "align_rna_reads_with_star_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src/norad/stages/align_RNA_reads_with_STAR"
    / "validate_step_01_star_alignment.py"
)


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.Aligned.sortedByCoord.out.bam"
    bam.write_bytes(b"BAM\x01synthetic")
    final = root / "S.Log.final.out"
    final.write_text(
        "Number of input reads | 100\n"
        "Uniquely mapped reads % | 90.00%\n"
        "% of reads mapped to multiple loci | 8.00%\n"
        "% of reads mapped to too many loci | 1.00%\n"
    )
    log = root / "S.Log.out"; log.write_text("ALL DONE!\n")
    progress = root / "S.Log.progress.out"; progress.write_text("ALL DONE!\n")
    sj = root / "S.SJ.out.tab"; sj.write_text("1\t10\t20\t1\t1\t0\t1\t0\t1\n")
    out = root / "out"; out.mkdir()
    return bam, final, log, progress, sj, out / "S.validation.tsv"


def run(values, *extra, cwd=ROOT):
    bam, final, log, progress, sj, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S", "--bam", str(bam),
         "--log-final", str(final), "--log-out", str(log),
         "--log-progress", str(progress), "--sj-out", str(sj),
         "--output", str(output), *extra],
        cwd=cwd, text=True, capture_output=True,
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
    assert_exact_check_roster(rows(values[-1]), "01")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_bad_mapping_summary_and_sj_are_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[1].write_text("Uniquely mapped reads % | invalid\n")
    values[4].write_text("1\t2\n")
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["mapping_summary"] == "fail"
    assert status["splice_junction_structure"] == "fail"


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


def test_non_repo_cwd_dry_run_execute_repeat_is_deterministic(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation = tmp_path / "invocation"
    invocation.mkdir()

    dry = run(values, cwd=invocation)
    assert dry.returncode == 0
    assert dry.stderr == ""
    assert dry.stdout.endswith("Dry-run complete; no output was written.\n")
    assert not values[-1].exists()

    first = run(values, "--execute", cwd=invocation)
    assert first.returncode == 0
    assert first.stderr == ""
    first_bytes = values[-1].read_bytes()

    second = run(values, "--execute", cwd=invocation)
    assert second.returncode == 0
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert values[-1].read_bytes() == first_bytes
    assert_exact_check_roster(rows(values[-1]), "01")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}
    assert list(invocation.iterdir()) == []
    assert not [path for path in values[-1].parent.iterdir() if path.name.startswith(".")]
