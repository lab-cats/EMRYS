#!/usr/bin/env python3
"""Disposable real-R benchmark adapter for Step 08 site fragments."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

COHORT_ID = "cohort_benchmark"
ORIENTATIONS = ("FWD_like", "REV_like")
PARTITION_COUNT = 8
BENCHMARK_CASES = {
    "100k_4": (100_000, 4),
    "100k_16": (100_000, 16),
    "1m_4": (1_000_000, 4),
    "1m_16": (1_000_000, 16),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_vcf(
    path: Path, chromosome: str, sample_ids: list[str], records_per_vcf: int
) -> None:
    genotype_columns = "\t".join("20:16,4:8,2:8,2:0" for _ in sample_ids)
    with path.open("x", encoding="ascii", newline="") as handle:
        handle.write(
            "##fileformat=VCFv4.2\n"
            '##FILTER=<ID=PASS,Description="All filters passed">\n'
            f"##contig=<ID={chromosome},length={records_per_vcf}>\n"
            '##INFO=<ID=AD,Number=R,Type=Integer,Description="Allelic depths">\n'
            '##INFO=<ID=ADF,Number=R,Type=Integer,Description="Forward depths">\n'
            '##INFO=<ID=ADR,Number=R,Type=Integer,Description="Reverse depths">\n'
            '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read depth">\n'
            '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allelic depths">\n'
            '##FORMAT=<ID=ADF,Number=R,Type=Integer,Description="Forward depths">\n'
            '##FORMAT=<ID=ADR,Number=R,Type=Integer,Description="Reverse depths">\n'
            '##FORMAT=<ID=SP,Number=1,Type=Integer,Description="Strand bias">\n'
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t"
            + "\t".join(sample_ids)
            + "\n"
        )
        for start in range(1, records_per_vcf + 1, 2_500):
            stop = min(start + 2_500, records_per_vcf + 1)
            handle.writelines(
                f"{chromosome}\t{position}\t.\tA\tG\t60\tPASS"
                f"\tAD=256,64;ADF=128,32;ADR=128,32"
                f"\tDP:AD:ADF:ADR:SP\t{genotype_columns}\n"
                for position in range(start, stop)
            )


def generate_case(root: Path, candidate_count: int, sample_count: int) -> None:
    records_per_vcf = candidate_count // (PARTITION_COUNT * len(ORIENTATIONS))
    if records_per_vcf * PARTITION_COUNT * len(ORIENTATIONS) != candidate_count:
        raise RuntimeError("candidate count must divide evenly across input VCFs")
    root.mkdir(mode=0o700)
    sample_ids = [f"sample_{index:02d}" for index in range(1, sample_count + 1)]
    with (root / "samples.tsv").open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(
            (
                "sample_id",
                "r1_fastq",
                "r2_fastq",
                "strandedness",
                "condition",
                "replicate",
            )
        )
        for index, sample_id in enumerate(sample_ids, start=1):
            writer.writerow(
                (
                    sample_id,
                    f"/reads/{sample_id}_R1.fastq.gz",
                    f"/reads/{sample_id}_R2.fastq.gz",
                    "unknown",
                    "condition_A" if index <= sample_count // 2 else "condition_B",
                    str(index),
                )
            )

    partitions = [
        (f"p{index:03d}", "region", f"chr{index:03d}:1-{records_per_vcf}")
        for index in range(1, PARTITION_COUNT + 1)
    ]
    with (root / "partitions.tsv").open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("partition_id", "selector_type", "selector_value"))
        writer.writerows(partitions)

    with (root / "annotation.gtf").open("x", encoding="utf-8", newline="") as handle:
        for index in range(1, PARTITION_COUNT + 1):
            chromosome = f"chr{index:03d}"
            for strand, suffix in (("+", "plus"), ("-", "minus")):
                handle.write(
                    f"{chromosome}\tbenchmark\texon\t1\t{records_per_vcf}\t.\t{strand}\t.\t"
                    f'gene_id "gene_{index:03d}_{suffix}"; '
                    f'transcript_id "tx_{index:03d}_{suffix}";\n'
                )

    sample_hash = sha256(root / "samples.tsv")
    partition_hash = sha256(root / "partitions.tsv")
    for partition_id, selector_type, selector_value in partitions:
        chromosome = selector_value.split(":", maxsplit=1)[0]
        partition_root = root / "step07" / COHORT_ID / partition_id
        partition_root.mkdir(mode=0o700, parents=True)
        vcf_paths: dict[str, Path] = {}
        for orientation in ORIENTATIONS:
            vcf_path = partition_root / (
                f"{COHORT_ID}.{partition_id}.{orientation}.mpileup.vcf"
            )
            write_vcf(vcf_path, chromosome, sample_ids, records_per_vcf)
            vcf_paths[orientation] = vcf_path
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
                        sample_count,
                        records_per_vcf,
                    )
                )

    metadata = {
        "annotation_sha256": sha256(root / "annotation.gtf"),
        "candidate_count": candidate_count,
        "input_count": PARTITION_COUNT * len(ORIENTATIONS),
        "partition_sha256": partition_hash,
        "sample_count": sample_count,
        "sample_sha256": sample_hash,
    }
    (root / "metadata.json").write_text(
        json.dumps(metadata, sort_keys=True) + "\n", encoding="utf-8"
    )


def generate(root: Path) -> None:
    root.mkdir(mode=0o700)
    for name, (candidate_count, sample_count) in BENCHMARK_CASES.items():
        generate_case(root / name, candidate_count, sample_count)


def fixture_path(case_name: str) -> Path:
    if case_name not in BENCHMARK_CASES:
        raise RuntimeError(f"unknown benchmark case: {case_name}")
    fixture_root = Path(os.environ["EMRYS_STEP08_FRAGMENT_FIXTURE"])
    return (fixture_root / case_name).resolve(strict=True)


def run(variant: int, case_name: str, trial: Path) -> None:
    root_name = "EMRYS_BASELINE_ROOT" if variant == 1 else "EMRYS_CANDIDATE_ROOT"
    source_root = Path(os.environ[root_name]).resolve(strict=True)
    fixture = fixture_path(case_name)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    engine = source_root / (
        "src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R"
    )
    command = [
        os.environ["EMRYS_RSCRIPT_BIN"],
        str(engine),
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
        "--sample-manifest-sha256",
        metadata["sample_sha256"],
        "--partition-manifest-sha256",
        metadata["partition_sha256"],
        "--annotation-gtf-sha256",
        metadata["annotation_sha256"],
        "--threads",
        "1",
        "--sites-output",
        str(trial / "sites.tsv"),
        "--inputs-output",
        str(trial / "inputs.tsv"),
        "--summary-output",
        str(trial / "summary.tsv"),
    ]
    os.execvpe(command[0], command, os.environ.copy())


def count_lines(path: Path) -> int:
    count = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            count += block.count(b"\n")
    return count


def validate(case_name: str, trial: Path) -> None:
    fixture = fixture_path(case_name)
    metadata = json.loads((fixture / "metadata.json").read_text(encoding="utf-8"))
    expected_lines = {
        "sites.tsv": metadata["candidate_count"] + 1,
        "inputs.tsv": metadata["input_count"] + 1,
        "summary.tsv": 2,
    }
    for name, expected in expected_lines.items():
        path = trial / name
        if not path.is_file() or path.is_symlink() or count_lines(path) != expected:
            raise RuntimeError(f"invalid {name} output")
    if list(trial.glob("sites.tsv.fragment-*.tsv")):
        raise RuntimeError("Step 08 left site-fragment residue")
    with (trial / "summary.tsv").open(encoding="utf-8", newline="") as handle:
        summary = next(csv.DictReader(handle, delimiter="\t"))
    if (
        int(summary["published_candidate_count"]) != metadata["candidate_count"]
        or int(summary["input_vcf_count"]) != metadata["input_count"]
        or int(summary["sample_count"]) != metadata["sample_count"]
    ):
        raise RuntimeError("Step 08 summary does not reconcile")
    stderr = (trial / "producer.stderr.log").read_text(encoding="utf-8")
    if "Step 08 preprocessing complete:" not in stderr or "ERROR:" in stderr:
        raise RuntimeError("Step 08 did not complete cleanly")

    report = trial / f"{COHORT_ID}.validation.tsv"
    validator = [
        sys.executable,
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "emrys",
        "validate",
        "cohort-candidate-preprocessing",
        "--cohort-id",
        COHORT_ID,
        "--sample-manifest",
        str(fixture / "samples.tsv"),
        "--partition-manifest",
        str(fixture / "partitions.tsv"),
        "--annotation-gtf",
        str(fixture / "annotation.gtf"),
        "--sites",
        str(trial / "sites.tsv"),
        "--inputs",
        str(trial / "inputs.tsv"),
        "--summary",
        str(trial / "summary.tsv"),
        "--output",
        str(report),
        "--execute",
    ]
    all_pass = [
        sys.executable,
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "emrys",
        "validate",
        "all-pass",
        "--report",
        str(report),
        "--step-id",
        "08",
        "--scope-id",
        COHORT_ID,
    ]
    for command in (validator, all_pass):
        completed = subprocess.run(command, capture_output=True, check=False)
        sys.stdout.buffer.write(completed.stdout)
        sys.stderr.buffer.write(completed.stderr)
        if completed.returncode != 0:
            raise RuntimeError("public Step 08 validation failed")


def main() -> int:
    arguments = sys.argv[1:]
    if len(arguments) == 2 and arguments[0] == "generate":
        generate(Path(arguments[1]))
    elif len(arguments) == 4 and arguments[0] == "run":
        run(int(arguments[1]), arguments[2], Path(arguments[3]))
    elif len(arguments) == 4 and arguments[0] == "validate":
        validate(arguments[2], Path(arguments[3]))
    else:
        raise RuntimeError(
            "expected generate ROOT, run VARIANT CASE TRIAL, or "
            "validate VARIANT CASE TRIAL"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
