"""Compute partitioned cohort VCFs and their scientific receipt in working paths."""

from __future__ import annotations

import argparse
import gzip
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.libraries.alignments.orientation import ORIENTATIONS
from emrys.libraries.validation import ValidationError, mpileup, sha256_file
from emrys.libraries.validation.tsv import read_strict_tsv

ANNOTATIONS = (
    "FORMAT/DP,FORMAT/AD,FORMAT/ADF,FORMAT/ADR,FORMAT/SP,INFO/AD,INFO/ADF,INFO/ADR"
)
DEFAULT_FILTER = "INFO/AD[1-]>2 & MAX(FORMAT/DP)>20"
DEFAULT_MAX_DEPTH = 10_000_000
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class ProducerError(RuntimeError):
    """Step 07 scientific preparation or computation failed."""


@dataclass(frozen=True, slots=True)
class Context:
    arguments: argparse.Namespace
    sample_ids: tuple[str, ...]
    selector_type: str
    selector_value: str
    selector_path: Path | None
    manifest_hashes: tuple[str, str]
    bams: tuple[tuple[Path, ...], tuple[Path, ...]]
    bcftools: str
    paths: dict[str, Path]
    final_vcfs: tuple[Path, Path]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    for name in (
        "cohort-id",
        "sample-manifest",
        "partition-manifest",
        "partition-id",
        "orientation-root",
        "reference-fasta",
    ):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--bcftools-bin")
    parser.add_argument("--max-depth", default=str(DEFAULT_MAX_DEPTH))
    parser.add_argument("--filter-expression", default=DEFAULT_FILTER)
    for name in (
        "fwd-vcf-output",
        "rev-vcf-output",
        "receipt-output",
        "fwd-vcf-final",
        "rev-vcf-final",
    ):
        parser.add_argument(f"--{name}", required=True, type=Path)


def fail(message: str) -> None:
    raise ProducerError(message)


def _safe_id(label: str, value: str) -> None:
    if not SAFE_ID.fullmatch(value):
        fail(f"{label} must match [A-Za-z0-9][A-Za-z0-9._-]*; got: {value}")


def _positive_integer(label: str, value: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]*", value):
        fail(f"{label} must be a positive integer; got: {value}")
    return int(value)


def _nonempty(label: str, path: Path) -> None:
    try:
        valid = path.is_file() and path.stat().st_size > 0
    except OSError:
        valid = False
    if not valid:
        fail(f"{label} does not exist or is empty: {path}")


def _digest(path: Path) -> str:
    try:
        return sha256_file(path)
    except OSError as exc:
        raise ProducerError(f"Could not hash {path}: {exc}") from exc


def _executable(requested: str | None) -> str:
    value = requested or os.environ.get("BCFTOOLS_BIN_OVERRIDE") or "bcftools"
    if "/" in value:
        if not Path(value).exists():
            fail(f"bcftools does not exist: {value}")
        if not os.access(value, os.X_OK):
            fail(f"bcftools exists but is not executable: {value}")
        return value
    resolved = shutil.which(value)
    if resolved is None:
        fail(f"bcftools executable was not found on PATH: {value}")
    return resolved


def _selector_lines(path: Path) -> Iterable[str]:
    try:
        if path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
                yield from stream
        else:
            with path.open(encoding="utf-8", newline="") as stream:
                yield from stream
    except (OSError, UnicodeError, EOFError) as exc:
        raise ProducerError(f"Could not read regions file {path}: {exc}") from exc


def _validate_regions_file(path: Path, contigs: dict[str, int]) -> None:
    file_type, _compression = mpileup.selector_file_semantics(path)
    row_mode: int | None = None
    data_rows = 0
    for row_number, raw in enumerate(_selector_lines(path), start=1):
        if not raw.strip() or raw.startswith("#"):
            continue
        fields = raw.rstrip("\r\n").split("\t")
        contig = fields[0]
        if contig not in contigs:
            fail(f"regions file contig is absent from FASTA index: {contig}")
        data_rows += 1
        valid = False
        if file_type == "bed" and len(fields) >= 3:
            if re.fullmatch(r"[0-9]+", fields[1]) and re.fullmatch(
                r"[0-9]+", fields[2]
            ):
                start, end = int(fields[1]), int(fields[2])
                valid = 0 <= start < end <= contigs[contig]
        elif file_type == "vcf" and len(fields) >= 2:
            valid = (
                bool(re.fullmatch(r"[1-9][0-9]*", fields[1]))
                and int(fields[1]) <= contigs[contig]
            )
        elif file_type == "tab" and len(fields) >= 2:
            mode = 2 if len(fields) == 2 else 3
            if row_mode is None:
                row_mode = mode
            elif row_mode != mode:
                fail(
                    f"regions file mixes position and interval rows at row {row_number}"
                )
            if re.fullmatch(r"[1-9][0-9]*", fields[1]):
                start = int(fields[1])
                valid = start <= contigs[contig]
                if mode == 3:
                    valid = (
                        valid
                        and bool(re.fullmatch(r"[1-9][0-9]*", fields[2]))
                        and start <= int(fields[2]) <= contigs[contig]
                    )
        if not valid:
            descriptor = (
                "BED interval"
                if file_type == "bed"
                else "VCF position"
                if file_type == "vcf"
                else "regions file row"
            )
            fail(f"invalid {descriptor} on regions file row {row_number}")
    if not data_rows:
        fail(f"regions file contains no selector rows: {path}")


def _selector(
    partition_manifest: Path,
    partition_id: str,
    reference_fai: Path,
) -> tuple[str, str, Path | None]:
    try:
        selector_type, selector_value = mpileup.read_partition(
            partition_manifest, partition_id
        )
        contigs = mpileup.read_fai(reference_fai)
    except (OSError, UnicodeError, ValidationError) as exc:
        fail(str(exc))
    if any(not contig or length < 1 for contig, length in contigs.items()):
        fail(f"Reference FASTA index validation failed: {reference_fai}")
    if selector_type == "region":
        if not mpileup.selector_ok(
            selector_type, selector_value, partition_manifest, contigs
        ):
            fail(
                f"Region selector is invalid or outside FASTA bounds: {selector_value}"
            )
        return selector_type, selector_value, None
    path = Path(selector_value)
    if not path.is_absolute():
        path = (partition_manifest.parent.resolve() / path).resolve()
    _nonempty(f"Regions file for partition {partition_id}", path)
    _validate_regions_file(path, contigs)
    return selector_type, selector_value, path


def build_context(arguments: argparse.Namespace) -> Context:
    _safe_id("--cohort-id", arguments.cohort_id)
    _safe_id("--partition-id", arguments.partition_id)
    arguments.max_depth = _positive_integer("--max-depth", arguments.max_depth)
    if not arguments.filter_expression:
        fail("--filter-expression must be non-empty.")
    sample_manifest = Path(arguments.sample_manifest)
    partition_manifest = Path(arguments.partition_manifest)
    reference = Path(arguments.reference_fasta)
    reference_fai = Path(f"{arguments.reference_fasta}.fai")
    for label, path in (
        ("Sample manifest", sample_manifest),
        ("Partition manifest", partition_manifest),
        ("Reference FASTA", reference),
        ("Reference FASTA index", reference_fai),
    ):
        _nonempty(label, path)
    manifest_hashes = (_digest(sample_manifest), _digest(partition_manifest))
    try:
        sample_ids = tuple(mpileup.read_sample_ids(sample_manifest))
    except (OSError, UnicodeError, ValidationError) as exc:
        fail(str(exc))
    for sample_id in sample_ids:
        _safe_id("sample_id", sample_id)
    selector_type, selector_value, selector_path = _selector(
        partition_manifest, arguments.partition_id, reference_fai
    )
    bams = tuple(
        tuple(
            Path(arguments.orientation_root)
            / sample_id
            / f"{sample_id}.{orientation}.bam"
            for sample_id in sample_ids
        )
        for orientation in ORIENTATIONS
    )
    for orientation, members in zip(ORIENTATIONS, bams, strict=True):
        for sample_id, bam in zip(sample_ids, members, strict=True):
            _nonempty(f"{orientation} BAM for {sample_id}", bam)
            _nonempty(f"{orientation} BAI for {sample_id}", Path(f"{bam}.bai"))
    context = Context(
        arguments=arguments,
        sample_ids=sample_ids,
        selector_type=selector_type,
        selector_value=selector_value,
        selector_path=selector_path,
        manifest_hashes=manifest_hashes,
        bams=bams,
        bcftools=_executable(arguments.bcftools_bin),
        paths={
            "fwd": arguments.fwd_vcf_output,
            "rev": arguments.rev_vcf_output,
            "receipt": arguments.receipt_output,
        },
        final_vcfs=(arguments.fwd_vcf_final, arguments.rev_vcf_final),
    )
    return context


def pipeline_commands(
    context: Context, orientation_index: int
) -> tuple[list[str], list[str]]:
    output = context.paths["fwd" if orientation_index == 0 else "rev"]
    selector = (
        ("-r", context.selector_value)
        if context.selector_type == "region"
        else ("-R", str(context.selector_path))
    )
    mpileup_command = [
        context.bcftools,
        "mpileup",
        "-Ou",
        "-f",
        context.arguments.reference_fasta,
        *selector,
        "-d",
        str(context.arguments.max_depth),
        "-I",
        "-a",
        ANNOTATIONS,
        *(str(path) for path in context.bams[orientation_index]),
    ]
    filter_command = [
        context.bcftools,
        "filter",
        "-i",
        context.arguments.filter_expression,
        "-Ov",
        "-o",
        str(output),
        "-",
    ]
    return mpileup_command, filter_command


def _run_pipeline(context: Context, orientation_index: int) -> None:
    mpileup_command, filter_command = pipeline_commands(context, orientation_index)
    source = subprocess.Popen(mpileup_command, stdout=subprocess.PIPE)
    try:
        consumer = subprocess.Popen(filter_command, stdin=source.stdout)
    finally:
        source.stdout.close()
    if consumer.wait() or source.wait():
        fail(
            f"{ORIENTATIONS[orientation_index]} bcftools mpileup/filter pipeline failed."
        )


def _bcftools(
    context: Context,
    *arguments: str,
    count_lines: bool = False,
) -> str | int:
    with subprocess.Popen(
        [context.bcftools, *arguments],
        stdout=subprocess.PIPE,
        text=True,
    ) as process:
        output = (
            sum(1 for _ in process.stdout) if count_lines else process.stdout.read()
        )
        process.stdout.close()
        status = process.wait()
    if status:
        fail(f"bcftools {' '.join(arguments[:2])} failed.")
    return output


def _validate_vcf(context: Context, label: str, path: Path) -> int:
    _nonempty(f"{label} VCF", path)
    _bcftools(context, "view", "-h", str(path))
    sample_output = _bcftools(context, "query", "-l", str(path))
    samples = tuple(sample_output.splitlines())
    if samples != context.sample_ids:
        expected_text = "\n".join(context.sample_ids)
        observed_text = "\n".join(samples)
        fail(
            f"{label} VCF sample order does not match the sample manifest: {path}\n"
            f"Expected samples:\n{expected_text}\n"
            f"Observed samples:\n{observed_text}"
        )
    count = _bcftools(context, "view", "-H", str(path), count_lines=True)
    return count


def _receipt_bytes(context: Context, counts: tuple[int, int]) -> bytes:
    rows = (
        "\t".join(
            (
                context.arguments.cohort_id,
                context.arguments.partition_id,
                context.selector_type,
                context.selector_value,
                orientation,
                str(context.final_vcfs[index]),
                *context.manifest_hashes,
                str(len(context.sample_ids)),
                str(counts[index]),
            )
        )
        for index, orientation in enumerate(ORIENTATIONS)
    )
    return ("\t".join(mpileup.RECEIPT_HEADER) + "\n" + "\n".join(rows) + "\n").encode()


def _validate_receipt(path: Path) -> None:
    _, rows = read_strict_tsv("Step 07 receipt", path, mpileup.RECEIPT_HEADER, fail)
    if len(rows) != 2:
        fail(f"Step 07 receipt must contain exactly two data rows: {path}")


def execute(context: Context) -> tuple[int, int]:
    _run_pipeline(context, 0)
    _run_pipeline(context, 1)
    counts = tuple(
        _validate_vcf(context, orientation, context.paths[name])
        for orientation, name in zip(ORIENTATIONS, ("fwd", "rev"), strict=True)
    )
    context.paths["receipt"].write_bytes(_receipt_bytes(context, counts))
    _validate_receipt(context.paths["receipt"])
    return counts


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    try:
        execute(build_context(parser.parse_args(argv)))
        return 0
    except (ProducerError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
