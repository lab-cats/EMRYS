import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_00c_reference_sidecars.py"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    fasta = root / "genome.fa"; fasta.write_text(">1\nACGT\n>MT\nAA\n")
    fai = root / "genome.fa.fai"; fai.write_text("1\t4\t3\t4\t5\nMT\t2\t12\t2\t3\n")
    dictionary = root / "genome.dict"
    dictionary.write_text("@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n@SQ\tSN:MT\tLN:2\n")
    outdir = root / "out"; outdir.mkdir()
    return fasta, fai, dictionary, outdir / "novogene_ref.validation.tsv"


def run(values, *extra):
    fasta, fai, dictionary, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--scope-id", "novogene_ref",
         "--reference-fasta", str(fasta), "--reference-fai", str(fai),
         "--reference-dict", str(dictionary), "--output", str(output), *extra],
        cwd=ROOT, text=True, capture_output=True,
    )


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[3].exists()


def test_execute_publishes_five_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert len(rows(values[3])) == 5
    assert {item["status"] for item in rows(values[3])} == {"pass"}


def test_sidecar_mismatch_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[1].write_text("1\t4\t3\t4\t5\nMT\t3\t12\t3\t4\n")
    assert run(values, "--execute").returncode == 0
    status = {item["check_id"]: item["status"] for item in rows(values[3])}
    assert status["fai_contig_agreement"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[1].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (*values[:3], values[3].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[3].parent / f".{values[3].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"
