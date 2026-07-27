import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_05_split_ncigar.py"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.split_ncigar.bam"; bam.write_bytes(b"BAM\x01synthetic")
    bai = root / "S.split_ncigar.bam.bai"; bai.write_bytes(b"BAI\x01synthetic")
    fasta = root / "genome.fa"; fasta.write_text(">1\nACGT\n")
    fai = root / "genome.fa.fai"; fai.write_text("1\t4\t3\t4\t5\n")
    dictionary = root / "genome.dict"
    dictionary.write_text("@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n")
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
    return bam, bai, fasta, fai, dictionary, tool, out / "S.validation.tsv"


def run(values, *extra):
    bam, bai, fasta, fai, dictionary, tool, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "S", "--bam", str(bam),
         "--bai", str(bai), "--reference-fasta", str(fasta),
         "--reference-fai", str(fai), "--reference-dict", str(dictionary),
         "--samtools-bin", str(tool), "--output", str(output), *extra],
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
    assert len(rows(values[-1])) == 5
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_sidecar_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[3].write_text("1\t5\t3\t5\t6\n")
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["reference_sidecars"] == "fail"


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
