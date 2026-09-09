"""Compute cohort candidate tables and scientific receipts in runner-owned paths."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.contracts.scientific_evidence import step08
from emrys.libraries import validation as report
from emrys.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY as POLICY,
    ORIENTATIONS,
)
from emrys.libraries.validation.mpileup import RECEIPT_HEADER, VCF_FIXED_COLUMNS
from emrys.libraries.validation.tsv import read_strict_tsv


class ProducerError(RuntimeError):
    """Step 08 admission, execution, or publication failed."""


@dataclass(frozen=True)
class Step07Input:
    partition: dict[str, str]
    receipt: str
    receipt_hash: str
    vcfs: tuple[str, str]
    vcf_hashes: tuple[str, str]
    counts: tuple[int, int]


@dataclass(frozen=True)
class Context:
    arguments: argparse.Namespace
    samples: tuple[str, ...]
    partitions: tuple[dict[str, str], ...]
    hashes: tuple[str, str, str]
    step07: tuple[Step07Input, ...]
    threads: int
    rscript: str
    paths: dict[str, Path]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    for name in (
        "cohort-id",
        "sample-manifest",
        "partition-manifest",
        "step07-root",
        "annotation-gtf",
    ):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--threads", default="1")
    parser.add_argument("--rscript-bin")
    parser.add_argument(
        "--r-script",
        default=os.environ.get(
            "STEP08_R_SCRIPT",
            str(Path(__file__).with_name("step_08_vcf_preprocessing.R")),
        ),
    )
    for name in ("sites-output", "inputs-output", "summary-output"):
        parser.add_argument(f"--{name}", required=True, type=Path)


def fail(message: str) -> None:
    raise ProducerError(message)


def digest(path: Path) -> str:
    try:
        return report.sha256_file(path)
    except OSError as exc:
        raise ProducerError(f"Could not hash {path}: {exc}") from exc


def nonempty(label: str, path: Path) -> None:
    try:
        valid = path.is_file() and path.stat().st_size > 0
    except OSError:
        valid = False
    if not valid:
        fail(f"{label} does not exist or is empty: {path}")


def integer(label: str, value: str, *, positive: bool = False) -> int:
    pattern = r"[1-9][0-9]*" if positive else r"0|[1-9][0-9]*"
    if not re.fullmatch(pattern, value):
        qualifier = "positive" if positive else "non-negative"
        fail(f"{label} must be a {qualifier} integer; got: {value}")
    return int(value)


def executable(requested: str | None) -> str:
    value = requested or os.environ.get("RSCRIPT_BIN_OVERRIDE") or "Rscript"
    if "/" in value:
        if not Path(value).exists():
            fail(f"Rscript does not exist: {value}")
        if not os.access(value, os.X_OK):
            fail(f"Rscript exists but is not executable: {value}")
        return value
    resolved = shutil.which(value)
    if resolved is None:
        fail(f"Rscript executable was not found on PATH: {value}")
    return resolved


def inspect_vcf(
    label: str,
    path: Path,
    samples: Sequence[str],
    declared: int,
) -> None:
    definitions = {
        prefix: False
        for prefix in ("##INFO=<ID=AD,", "##FORMAT=<ID=DP,", "##FORMAT=<ID=AD,")
    }
    header_count = observed = 0
    invalid_header = blank_data = False
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            for raw_line in stream:
                line = raw_line.removesuffix("\n")
                for prefix in definitions:
                    definitions[prefix] |= line.startswith(prefix)
                if line.startswith("#CHROM"):
                    header_count += 1
                    fields = line.split("\t")
                    invalid_header |= tuple(fields[:9]) != VCF_FIXED_COLUMNS or fields[
                        9:
                    ] != list(samples)
                elif line.startswith("#"):
                    continue
                elif not line.strip():
                    blank_data = True
                else:
                    observed += 1
    except (OSError, UnicodeError) as exc:
        raise ProducerError(f"Could not read {label} VCF {path}: {exc}") from exc
    if header_count != 1 or invalid_header or not all(definitions.values()):
        fail(f"{label} VCF header or required definitions are invalid: {path}")
    if blank_data or observed != declared:
        fail(f"{label} VCF record count does not match its Step 07 receipt: {path}")


def admit_step07(
    arguments: argparse.Namespace,
    partition: dict[str, str],
    samples: Sequence[str],
    sample_hash: str,
    partition_hash: str,
) -> Step07Input:
    partition_id = partition["partition_id"]
    root = f"{arguments.step07_root}/{arguments.cohort_id}/{partition_id}"
    prefix = f"{arguments.cohort_id}.{partition_id}"
    receipt = f"{root}/{prefix}.step07_outputs.tsv"
    vcfs = tuple(
        f"{root}/{prefix}.{orientation}.mpileup.vcf" for orientation in ORIENTATIONS
    )
    nonempty(f"Step 07 receipt for partition {partition_id}", Path(receipt))
    for orientation, path in zip(ORIENTATIONS, vcfs, strict=True):
        nonempty(f"Step 07 {orientation} VCF for partition {partition_id}", Path(path))
    before = (digest(Path(receipt)), *(digest(Path(path)) for path in vcfs))
    _, rows = read_strict_tsv(
        f"Step 07 receipt for partition {partition_id}",
        Path(receipt),
        RECEIPT_HEADER,
        fail,
    )
    if len(rows) != 2:
        fail(
            f"Step 07 receipt must contain the exact header and two 10-field rows: {receipt}"
        )
    counts: list[int] = []
    for row, orientation, vcf in zip(rows, ORIENTATIONS, vcfs, strict=True):
        identity = (
            row["cohort_id"] == arguments.cohort_id
            and row["partition_id"] == partition_id
            and row["selector_type"] == partition["selector_type"]
            and row["selector_value"] == partition["selector_value"]
            and row["orientation"] == orientation
            and row["sample_manifest_sha256"] == sample_hash
            and row["partition_manifest_sha256"] == partition_hash
        )
        try:
            same_vcf = Path(row["vcf_path"]).samefile(Path(vcf))
        except OSError:
            same_vcf = False
        if (
            not identity
            or not same_vcf
            or integer("Step 07 sample count", row["sample_count"]) != len(samples)
        ):
            fail(f"Step 07 receipt provenance mismatch: {receipt}")
        declared = integer(
            f"Step 07 {orientation} record count", row["vcf_record_count"]
        )
        inspect_vcf(f"Step 07 {orientation}", Path(vcf), samples, declared)
        counts.append(declared)
    return Step07Input(
        dict(partition),
        receipt,
        before[0],
        (vcfs[0], vcfs[1]),
        (before[1], before[2]),
        (counts[0], counts[1]),
    )


def build_context(arguments: argparse.Namespace) -> Context:
    threads = integer("--threads", arguments.threads, positive=True)
    try:
        step08.validate_safe_id("--cohort-id", arguments.cohort_id)
        _, samples, _ = step08.validate_sample_manifest(Path(arguments.sample_manifest))
        partition_table = step08.validate_partition_manifest(
            Path(arguments.partition_manifest)
        )
    except step08.ContractError as exc:
        raise ProducerError(str(exc)) from exc
    nonempty("Annotation GTF", Path(arguments.annotation_gtf))
    nonempty("Step 08 R script", Path(arguments.r_script))
    hashes = tuple(
        digest(Path(path))
        for path in (
            arguments.sample_manifest,
            arguments.partition_manifest,
            arguments.annotation_gtf,
        )
    )
    step07 = tuple(
        admit_step07(arguments, row, samples, hashes[0], hashes[1])
        for row in partition_table.rows
    )
    context = Context(
        arguments,
        tuple(samples),
        tuple(map(dict, partition_table.rows)),
        (hashes[0], hashes[1], hashes[2]),
        step07,
        threads,
        executable(arguments.rscript_bin),
        {
            "sites": arguments.sites_output,
            "summary": arguments.summary_output,
            "inputs": arguments.inputs_output,
        },
    )
    return context


def validate_outputs(context: Context) -> None:
    paths = context.paths
    try:
        inputs = step08.validate_step08_inputs(
            paths["inputs"], context.samples, context.partitions, *context.hashes[:2]
        )
        sites = step08.validate_step08_sites(
            paths["sites"], context.samples, context.partitions, inputs.rows
        )
        summary = step08.validate_step08_summary(
            paths["summary"],
            context.samples,
            context.partitions,
            inputs.rows,
            sites.rows,
            *context.hashes[:2],
        )
    except step08.ContractError as exc:
        raise ProducerError(str(exc)) from exc
    expected = [(item, index) for item in context.step07 for index in range(2)]
    for row, (item, index) in zip(inputs.rows, expected, strict=True):
        values = (
            row["cohort_id"] == context.arguments.cohort_id,
            row["step07_receipt_path"] == str(item.receipt),
            row["step07_receipt_sha256"] == item.receipt_hash,
            row["vcf_path"] == str(item.vcfs[index]),
            row["vcf_sha256"] == item.vcf_hashes[index],
            row["annotation_gtf"] == context.arguments.annotation_gtf,
            row["annotation_gtf_sha256"] == context.hashes[2],
            row["orientation_policy"] == POLICY,
            int(row["declared_vcf_record_count"]) == item.counts[index],
        )
        if not all(values):
            fail("Step 08 input receipt contains invalid admitted provenance.")
    if any(int(row["position"]) < 1 for row in sites.rows):
        fail("Step 08 sites positions must be positive.")
    row = summary.rows[0]
    summary_identity = (
        row["cohort_id"],
        row["annotation_gtf"],
        row["annotation_gtf_sha256"],
        row["orientation_policy"],
    )
    if summary_identity != (
        context.arguments.cohort_id,
        context.arguments.annotation_gtf,
        context.hashes[2],
        POLICY,
    ):
        fail("Step 08 summary contains invalid admitted provenance.")


def r_command(context: Context) -> list[str]:
    arguments, p = context.arguments, context.paths
    command = [context.rscript]
    if os.environ.get("EMRYS_LOCAL_PILOT_R", "0") == "1":
        command += ["--no-environ", "--no-site-file", "--no-restore", "--no-save"]
    command += [
        arguments.r_script,
        "--cohort-id",
        arguments.cohort_id,
        "--sample-manifest",
        arguments.sample_manifest,
        "--partition-manifest",
        arguments.partition_manifest,
        "--step07-root",
        arguments.step07_root,
        "--annotation-gtf",
        arguments.annotation_gtf,
        "--sample-manifest-sha256",
        context.hashes[0],
        "--partition-manifest-sha256",
        context.hashes[1],
        "--annotation-gtf-sha256",
        context.hashes[2],
        "--threads",
        str(context.threads),
        "--sites-output",
        str(p["sites"]),
        "--inputs-output",
        str(p["inputs"]),
        "--summary-output",
        str(p["summary"]),
    ]
    return command


def execute(context: Context) -> None:
    if subprocess.run(r_command(context)).returncode:
        fail("Step 08 R VCF preprocessing failed.")
    validate_outputs(context)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    try:
        execute(build_context(parser.parse_args(argv)))
        return 0
    except (ProducerError, OSError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
