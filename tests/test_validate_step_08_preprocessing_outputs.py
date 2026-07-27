import csv
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from step_09c_scientific_validation import (
    STEP08_INPUTS_HEADER,
    STEP08_METADATA_HEADER,
    STEP08_SUMMARY_HEADER,
)

SCRIPT = ROOT / "scripts/validate_step_08_preprocessing_outputs.py"


def write_tsv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    samples = root / "samples.tsv"
    write_tsv(
        samples,
        ("sample_id", "r1_fastq", "r2_fastq", "strandedness", "condition", "replicate"),
        (("S", "/r1", "/r2", "reverse", "control", "1"),),
    )
    partitions = root / "partitions.tsv"
    write_tsv(
        partitions,
        ("partition_id", "selector_type", "selector_value"),
        (("p1", "region", "1"),),
    )
    annotation = root / "annotation.gtf"
    annotation.write_text('1\ts\tgene\t1\t10\t.\t+\t.\tgene_id "g";\n')
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    sites = root / "cohort.step08_sites.tsv"
    write_tsv(
        sites,
        STEP08_METADATA_HEADER + ("DP__S", "AD__S", "AF__S"),
        (
            (
                "p1", "c1", "FWD_like", "1", "2", "1", "A", "G", "A", "G",
                "+", "g", "t", "TRUE", "FALSE", "FALSE", "TRUE", "FALSE", "60",
                "PASS", "4", "legacy_provisional_v1", "10", "2", "0.2",
            ),
            (
                "p1", "c2", "REV_like", "1", "3", "1", "C", "T", "G", "A",
                "-", "g", "t", "TRUE", "FALSE", "FALSE", "TRUE", "FALSE", "50",
                "PASS", "3", "legacy_provisional_v1", "8", "1", "0.125",
            ),
        ),
    )
    inputs = root / "cohort.step08_inputs.tsv"
    common = (
        "cohort", "p1", "region", "1", None, "/step07/receipt.tsv", "1" * 64,
        None, "2" * 64, digest(samples), digest(partitions), str(annotation.resolve()),
        digest(annotation), "1", "1", "1", "1", "1", "0", "0",
    )
    write_tsv(
        inputs,
        STEP08_INPUTS_HEADER,
        (
            (*common[:4], "FWD_like", *common[5:7], "/step07/fwd.vcf",
             *common[8:], "1", "legacy_provisional_v1"),
            (*common[:4], "REV_like", *common[5:7], "/step07/rev.vcf",
             *common[8:], "1", "legacy_provisional_v1"),
        ),
    )
    summary = root / "cohort.step08_summary.tsv"
    write_tsv(
        summary,
        STEP08_SUMMARY_HEADER,
        ((
            "cohort", "1", "1", "2", "1", "2", "2", "2", "0", "0", "2",
            digest(samples), digest(partitions), str(annotation.resolve()),
            digest(annotation), "legacy_provisional_v1",
        ),),
    )
    out = root / "out"; out.mkdir()
    return samples, partitions, annotation, sites, inputs, summary, out / "cohort.validation.tsv"


def run(values, *extra):
    samples, partitions, annotation, sites, inputs, summary, output = values
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--cohort-id", "cohort",
         "--sample-manifest", str(samples), "--partition-manifest", str(partitions),
         "--annotation-gtf", str(annotation), "--sites", str(sites),
         "--inputs", str(inputs), "--summary", str(summary),
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
    assert len(rows(values[-1])) == 5
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_summary_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    text = values[5].read_text()
    values[5].write_text(text.replace("\t2\t2\t2\t0\t0\t2\t", "\t9\t2\t2\t0\t0\t2\t"))
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["summary_count_reconciliation"] == "fail"


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
