import csv
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = ROOT / "tests" / "validation_roster_expectations.py"
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "construct_canonical_bam_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src/norad/stages/construct_canonical_BAM/validate_step_02_canonical_bam.py"
)


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.sorted.bam"; bam.write_bytes(b"BAM\x01synthetic")
    bai = root / "S.sorted.bam.bai"; bai.write_bytes(b"BAI\x01synthetic")
    tool = root / "samtools"
    tool.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "case \"$1 $2\" in\n"
        "  'quickcheck -v') exit \"${QUICKCHECK_EXIT:-0}\" ;;\n"
        "  'view -H') printf '@HD\\tVN:1.6\\tSO:%s\\n@RG\\tID:%s\\tSM:%s\\n' "
        "\"${SORT_ORDER:-coordinate}\" \"${RG_ID:-S}\" \"${RG_SM:-S}\" ;;\n"
        "  'view -c')\n"
        "    if [[ \"${3:-}\" == -d ]]; then printf '%s\\n' \"${TAGGED:-10}\"; "
        "else printf '%s\\n' \"${TOTAL:-10}\"; fi ;;\n"
        "  *) exit 9 ;;\n"
        "esac\n"
    )
    tool.chmod(0o755)
    out = root / "out"; out.mkdir()
    return bam, bai, tool, out / "S.validation.tsv"


def run(values, *extra, env=None, cwd: Path | None = None):
    bam, bai, tool, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S", "--bam", str(bam),
         "--bai", str(bai), "--samtools-bin", str(tool),
         "--output", str(output), *extra],
        cwd=ROOT if cwd is None else cwd,
        text=True,
        capture_output=True,
        env=env,
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
    assert_exact_check_roster(rows(values[-1]), "02")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_sort_rg_and_tag_failures_are_evidence(tmp_path, monkeypatch):
    values = fixture(tmp_path)
    env = dict(**__import__("os").environ, SORT_ORDER="queryname", RG_ID="wrong",
               TAGGED="9", QUICKCHECK_EXIT="1")
    assert run(values, "--execute", env=env).returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["samtools_quickcheck"] == "fail"
    assert status["coordinate_sorting"] == "fail"
    assert status["read_group_header"] == "fail"
    assert status["alignment_rg_tags"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[1].unlink()
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


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_exact(tmp_path):
    values = fixture(tmp_path / "data")
    invocation = tmp_path / "invoke"
    invocation.mkdir()
    inputs = values[:3]
    before = {
        path: (path.read_bytes(), path.stat().st_mode) for path in inputs
    }

    dry = run(values, cwd=invocation)
    assert dry.returncode == 0
    assert dry.stderr == ""
    assert not values[-1].exists()
    assert hashlib.sha256(dry.stdout.encode()).hexdigest() == (
        "e0edf8f70d40ffc6ca9ae6ef732c797ac00abd056ee16496ad22038e277c5c1f"
    )

    first = run(values, "--execute", cwd=invocation)
    assert first.returncode == 0
    assert first.stderr == ""
    first_bytes = values[-1].read_bytes()
    assert len(first_bytes) == 542
    assert hashlib.sha256(first_bytes).hexdigest() == (
        "0007c190b23071286fea72670f72d9cf98666c5c11fd76f1657715aa2d76a7c8"
    )
    assert_exact_check_roster(rows(values[-1]), "02")

    second = run(values, "--execute", cwd=invocation)
    assert second.returncode == 0
    assert second.stderr == ""
    assert values[-1].read_bytes() == first_bytes
    assert {
        path: (path.read_bytes(), path.stat().st_mode) for path in inputs
    } == before
    assert list(invocation.iterdir()) == []
