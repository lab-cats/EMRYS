import csv
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_07_mpileup_outputs.py"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    samples = root / "samples.tsv"
    samples.write_text("sample_id\tcondition\nA\tx\nB\ty\n")
    partitions = root / "partitions.tsv"
    partitions.write_text("partition_id\tselector_type\tselector_value\np1\tregion\t1:1-10\n")
    fai = root / "ref.fa.fai"; fai.write_text("1\t100\t0\t80\t81\n")
    header = (
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tA\tB\n"
    )
    fwd = root / "cohort.p1.FWD_like.mpileup.vcf"
    rev = root / "cohort.p1.REV_like.mpileup.vcf"
    fwd.write_text(header + "1\t2\t.\tA\tG\t.\tPASS\t.\tGT\t0/1\t0/0\n")
    rev.write_text(header)
    receipt = root / "cohort.p1.step07_outputs.tsv"
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    receipt.write_text(
        "cohort_id\tpartition_id\tselector_type\tselector_value\torientation\t"
        "vcf_path\tsample_manifest_sha256\tpartition_manifest_sha256\t"
        "sample_count\tvcf_record_count\n"
        f"cohort\tp1\tregion\t1:1-10\tFWD_like\t{fwd.resolve()}\t"
        f"{sha(samples)}\t{sha(partitions)}\t2\t1\n"
        f"cohort\tp1\tregion\t1:1-10\tREV_like\t{rev.resolve()}\t"
        f"{sha(samples)}\t{sha(partitions)}\t2\t0\n"
    )
    out = root / "out"; out.mkdir()
    return samples, partitions, fai, fwd, rev, receipt, out / "cohort__p1.validation.tsv"


def run(values, *extra):
    samples, partitions, fai, fwd, rev, receipt, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--cohort-id", "cohort",
         "--partition-id", "p1", "--sample-manifest", str(samples),
         "--partition-manifest", str(partitions), "--reference-fai", str(fai),
         "--fwd-vcf", str(fwd), "--rev-vcf", str(rev),
         "--receipt", str(receipt), "--output", str(output), *extra],
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


def test_receipt_count_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[5].write_text(values[5].read_text().replace("\t2\t1\n", "\t2\t9\n"))
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["vcf_record_counts"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[3].unlink()
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
