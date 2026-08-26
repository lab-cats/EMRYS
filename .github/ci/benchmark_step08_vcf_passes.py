#!/usr/bin/env python3
"""Disposable baseline/candidate benchmark adapter for Step 08 VCF passes."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from pathlib import Path

COHORT_ID = "cohort_benchmark"
ORIENTATIONS = ("FWD_like", "REV_like")
POLICY = "legacy_provisional_v1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_vcf(path: Path, chromosome: str, record_count: int) -> None:
    with path.open("x", encoding="ascii", newline="") as handle:
        handle.write(
            "##fileformat=VCFv4.2\n"
            '##INFO=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">\n'
            '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"
            "\tsample_A\tsample_B\n"
        )
        for start in range(1, record_count + 1, 10000):
            stop = min(start + 10000, record_count + 1)
            handle.writelines(
                f"{chromosome}\t{position}\t.\tA\tG\t60\tPASS\tAD=20,4"
                "\tDP:AD\t10:8,2\t10:8,2\n"
                for position in range(start, stop)
            )


def generate_case(root: Path, partition_count: int, records_per_vcf: int) -> None:
    root.mkdir(mode=0o700, parents=True)
    (root / "samples.tsv").write_text(
        "sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\treplicate\n"
        "sample_A\t/reads/A_R1.fastq.gz\t/reads/A_R2.fastq.gz\tunknown\tEV\t1\n"
        "sample_B\t/reads/B_R1.fastq.gz\t/reads/B_R2.fastq.gz\tunknown\tPUM1\t2\n",
        encoding="utf-8",
    )
    partition_rows = [
        (f"p{ordinal:03d}", "region", f"chr{ordinal:03d}")
        for ordinal in range(1, partition_count + 1)
    ]
    with (root / "partitions.tsv").open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("partition_id", "selector_type", "selector_value"))
        writer.writerows(partition_rows)
    (root / "annotation.gtf").write_text(
        'chr001\tsource\ttranscript\t1\t100\t.\t+\t.\tgene_id "g"; '
        'transcript_id "t";\n',
        encoding="utf-8",
    )
    (root / "step08_impl.R").write_text("# benchmark fake R program\n")

    sample_hash = sha256(root / "samples.tsv")
    partition_hash = sha256(root / "partitions.tsv")
    for partition_id, selector_type, selector_value in partition_rows:
        partition_root = root / "step07" / COHORT_ID / partition_id
        partition_root.mkdir(mode=0o700, parents=True)
        vcf_paths = {}
        for orientation in ORIENTATIONS:
            vcf = partition_root / (
                f"{COHORT_ID}.{partition_id}.{orientation}.mpileup.vcf"
            )
            write_vcf(vcf, selector_value, records_per_vcf)
            vcf_paths[orientation] = vcf
        receipt = partition_root / f"{COHORT_ID}.{partition_id}.step07_outputs.tsv"
        with receipt.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerow(
                (
                    "cohort_id",
                    "partition_id",
                    "selector_type",
                    "selector_value",
                    "orientation",
                    "vcf_path",
                    "sample_manifest_sha256",
                    "partition_manifest_sha256",
                    "sample_count",
                    "vcf_record_count",
                )
            )
            for orientation in ORIENTATIONS:
                writer.writerow(
                    (
                        COHORT_ID,
                        partition_id,
                        selector_type,
                        selector_value,
                        orientation,
                        str(vcf_paths[orientation]),
                        sample_hash,
                        partition_hash,
                        2,
                        records_per_vcf,
                    )
                )


def generate(root: Path) -> None:
    root.mkdir(mode=0o700)
    generate_case(root / "one-large", 1, 500000)
    generate_case(root / "many-small", 25, 20000)


def parse_options(arguments: list[str]) -> dict[str, str]:
    if len(arguments) % 2:
        raise RuntimeError("fake R invocation must contain option/value pairs")
    return dict(zip(arguments[0::2], arguments[1::2], strict=True))


def fake_rscript(arguments: list[str]) -> None:
    if arguments == ["--version"]:
        print("R scripting front-end version 4.benchmark")
        return
    if not arguments:
        raise RuntimeError("fake R invocation is missing its program")
    options = parse_options(arguments[1:])
    sample_manifest = Path(options["--sample-manifest"])
    partition_manifest = Path(options["--partition-manifest"])
    step07_root = Path(options["--step07-root"])
    cohort_id = options["--cohort-id"]
    sample_ids = []
    with sample_manifest.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            sample_ids.append(row["sample_id"])
    with partition_manifest.open(encoding="utf-8", newline="") as handle:
        partitions = list(csv.DictReader(handle, delimiter="\t"))

    sites_header = [
        "partition_id",
        "candidate_id",
        "orientation",
        "chromosome",
        "position",
        "alt_index",
        "genomic_ref",
        "genomic_alt",
        "rna_ref",
        "rna_alt",
        "annotation_strand",
        "gene_ids",
        "transcript_ids",
        "is_cds",
        "is_five_prime_utr",
        "is_three_prime_utr",
        "is_exon",
        "is_intron",
        "qual",
        "filter",
        "info_alt_depth",
        "orientation_policy",
    ]
    sites_header.extend(f"DP__{sample_id}" for sample_id in sample_ids)
    sites_header.extend(f"AD__{sample_id}" for sample_id in sample_ids)
    sites_header.extend(f"AF__{sample_id}" for sample_id in sample_ids)
    with Path(options["--sites-output"]).open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        csv.writer(handle, delimiter="\t", lineterminator="\n").writerow(
            sites_header
        )

    inputs_header = (
        "cohort_id",
        "partition_id",
        "selector_type",
        "selector_value",
        "orientation",
        "step07_receipt_path",
        "step07_receipt_sha256",
        "vcf_path",
        "vcf_sha256",
        "sample_manifest_sha256",
        "partition_manifest_sha256",
        "annotation_gtf",
        "annotation_gtf_sha256",
        "sample_count",
        "declared_vcf_record_count",
        "observed_vcf_record_count",
        "observed_alt_allele_count",
        "supported_snv_count",
        "skipped_symbolic_count",
        "skipped_non_snv_count",
        "published_candidate_count",
        "orientation_policy",
    )
    input_rows = []
    observed_total = 0
    for partition in partitions:
        partition_id = partition["partition_id"]
        receipt = (
            step07_root
            / cohort_id
            / partition_id
            / f"{cohort_id}.{partition_id}.step07_outputs.tsv"
        )
        receipt_hash = sha256(receipt)
        with receipt.open(encoding="utf-8", newline="") as handle:
            receipt_rows = list(csv.DictReader(handle, delimiter="\t"))
        for receipt_row in receipt_rows:
            vcf = Path(receipt_row["vcf_path"])
            declared = int(receipt_row["vcf_record_count"])
            observed_total += declared
            input_rows.append(
                (
                    cohort_id,
                    partition_id,
                    partition["selector_type"],
                    partition["selector_value"],
                    receipt_row["orientation"],
                    str(receipt),
                    receipt_hash,
                    str(vcf),
                    sha256(vcf),
                    options["--sample-manifest-sha256"],
                    options["--partition-manifest-sha256"],
                    options["--annotation-gtf"],
                    options["--annotation-gtf-sha256"],
                    len(sample_ids),
                    declared,
                    declared,
                    0,
                    0,
                    0,
                    0,
                    0,
                    POLICY,
                )
            )
    with Path(options["--inputs-output"]).open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(inputs_header)
        writer.writerows(input_rows)

    summary_header = (
        "cohort_id",
        "partition_count",
        "step07_receipt_count",
        "input_vcf_count",
        "sample_count",
        "observed_vcf_record_count",
        "observed_alt_allele_count",
        "supported_snv_count",
        "skipped_symbolic_count",
        "skipped_non_snv_count",
        "published_candidate_count",
        "sample_manifest_sha256",
        "partition_manifest_sha256",
        "annotation_gtf",
        "annotation_gtf_sha256",
        "orientation_policy",
    )
    summary_row = (
        cohort_id,
        len(partitions),
        len(partitions),
        len(input_rows),
        len(sample_ids),
        observed_total,
        0,
        0,
        0,
        0,
        0,
        options["--sample-manifest-sha256"],
        options["--partition-manifest-sha256"],
        options["--annotation-gtf"],
        options["--annotation-gtf-sha256"],
        POLICY,
    )
    with Path(options["--summary-output"]).open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(summary_header)
        writer.writerow(summary_row)


def run(variant: int, case_name: str, trial: Path) -> int:
    root_variable = (
        "EMRYS_BASELINE_ROOT" if variant == 1 else "EMRYS_CANDIDATE_ROOT"
    )
    source_root = Path(os.environ[root_variable])
    fixture = Path(os.environ["EMRYS_STEP08_FIXTURE_ROOT"]) / case_name
    script = source_root / (
        "src/emrys/stages/cohort_candidate_preprocessing/"
        "step_08_vcf_preprocessing.sh"
    )
    command = [
        str(script),
        "--cohort-id",
        COHORT_ID,
        "--sample-manifest",
        str(fixture / "samples.tsv"),
        "--partition-manifest",
        str(fixture / "partitions.tsv"),
        "--step07-root",
        str(fixture / "step07"),
        "--annotation-gtf",
        str(fixture / "annotation.gtf"),
        "--output-root",
        str(trial / "output"),
        "--qc-root",
        str(trial / "qc"),
        "--rscript-bin",
        str(Path(__file__).resolve()),
        "--r-script",
        str(fixture / "step08_impl.R"),
        "--execute",
    ]
    environment = os.environ.copy()
    environment["EMRYS_RUN_TOKEN"] = "benchmark"
    environment["EMRYS_REQUIRE_BOUND_SHA256"] = "1"
    environment["EMRYS_SHA256_PYTHON"] = str(Path(sys.executable).resolve())
    completed = subprocess.run(
        command, env=environment, capture_output=True, check=False
    )
    sys.stdout.buffer.write(completed.stdout)
    sys.stderr.buffer.write(completed.stderr)
    return completed.returncode


def validate(trial: Path) -> None:
    expected = (
        trial / "output" / COHORT_ID / f"{COHORT_ID}.step08_sites.tsv",
        trial / "output" / COHORT_ID / f"{COHORT_ID}.step08_inputs.tsv",
        trial / "qc" / f"{COHORT_ID}.step08_summary.tsv",
    )
    if any(not path.is_file() or path.stat().st_size == 0 for path in expected):
        raise RuntimeError("Step 08 benchmark outputs are incomplete")
    stdout = (trial / "producer.stdout.log").read_text(encoding="utf-8")
    stderr = (trial / "producer.stderr.log").read_text(encoding="utf-8")
    if "Step 08 execute complete." not in stdout or stderr:
        raise RuntimeError("Step 08 benchmark did not complete cleanly")
    residue = [
        path
        for root in (trial / "output", trial / "qc")
        for path in root.rglob(".*.step08.*")
    ]
    if residue:
        raise RuntimeError(f"Step 08 benchmark left scratch residue: {residue[0]}")


def main() -> int:
    arguments = sys.argv[1:]
    if arguments == ["--version"]:
        print("R scripting front-end version 4.benchmark")
    elif arguments[0] == "generate":
        generate(Path(arguments[1]))
    elif arguments[0] == "run":
        return run(int(arguments[1]), arguments[2], Path(arguments[3]))
    elif arguments[0] == "validate":
        validate(Path(arguments[3]))
    else:
        fake_rscript(arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
