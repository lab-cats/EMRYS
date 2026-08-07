#!/usr/bin/env python3
"""Convert GTF transcript exon models to BED12 for RSeQC infer_experiment.py.

This prepares a transcript-model reference for downstream strandness checks.
Input is a GTF annotation; output is a BED12 file with one row per transcript.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO


VALID_STRANDS = {"+", "-", "."}


# Small records keep parsing, validation, and BED serialization easy to inspect.
@dataclass(frozen=True)
class Exon:
    """One exon in BED coordinate space."""

    start: int
    end: int


@dataclass
class Transcript:
    """Collected exons and metadata for one transcript."""

    transcript_id: str
    chrom: str
    strand: str
    gene_id: str | None = None
    exons: list[Exon] = field(default_factory=list)
    invalid_reason: str | None = None
    warned_gene_conflict: bool = False


@dataclass(frozen=True)
class BedRecord:
    """One BED12 record ready to serialize."""

    chrom: str
    chrom_start: int
    chrom_end: int
    name: str
    strand: str
    block_sizes: tuple[int, ...]
    block_starts: tuple[int, ...]

    def sort_key(self) -> tuple[str, int, int, str]:
        return (self.chrom, self.chrom_start, self.chrom_end, self.name)

    def to_line(self) -> str:
        block_sizes = "".join(f"{size}," for size in self.block_sizes)
        block_starts = "".join(f"{start}," for start in self.block_starts)
        fields = [
            self.chrom,
            str(self.chrom_start),
            str(self.chrom_end),
            self.name,
            "0",
            self.strand,
            str(self.chrom_start),
            str(self.chrom_end),
            "0",
            str(len(self.block_sizes)),
            block_sizes,
            block_starts,
        ]
        return "\t".join(fields)


def parse_args() -> argparse.Namespace:
    # Expose all input/output choices through the CLI so paths stay portable.
    parser = argparse.ArgumentParser(
        description=(
            "Convert a GTF annotation file to BED12 transcript models suitable "
            "for RSeQC infer_experiment.py."
        )
    )
    parser.add_argument(
        "--gtf",
        required=True,
        type=Path,
        help="Input GTF annotation file.",
    )
    parser.add_argument(
        "--bed",
        required=True,
        type=Path,
        help="Output BED12 file to write.",
    )
    parser.add_argument(
        "--feature",
        default="exon",
        help="GTF feature type to convert. Defaults to exon.",
    )
    parser.add_argument(
        "--name-attribute",
        default="transcript_id",
        help="GTF attribute used as the transcript name. Defaults to transcript_id.",
    )
    parser.add_argument(
        "--gene-attribute",
        default="gene_id",
        help="GTF attribute used as the gene name. Defaults to gene_id.",
    )
    return parser.parse_args()


def warn(message: str, stderr: TextIO) -> None:
    print(f"WARNING: {message}", file=stderr)


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_gtf_attributes(attribute_text: str) -> dict[str, str]:
    attributes: dict[str, str] = {}

    # Accept common GTF/GFF-style attribute separators without guessing elsewhere.
    for segment in attribute_text.strip().rstrip(";").split(";"):
        segment = segment.strip()
        if not segment:
            continue

        if "=" in segment and (segment.find("=") < segment.find(" ") or " " not in segment):
            key, value = segment.split("=", 1)
        else:
            parts = segment.split(None, 1)
            if len(parts) == 1:
                key, value = parts[0], ""
            else:
                key, value = parts

        key = key.strip()
        if key:
            attributes[key] = strip_quotes(value)

    return attributes


def clean_name_component(value: str) -> str:
    return re.sub(r"\s+", "_", value.strip())


def build_bed_name(transcript_id: str, gene_id: str | None) -> str:
    clean_transcript_id = clean_name_component(transcript_id)
    if gene_id:
        clean_gene_id = clean_name_component(gene_id)
        if clean_gene_id:
            return f"{clean_transcript_id}|{clean_gene_id}"
    return clean_transcript_id


def add_exon(
    transcripts: dict[str, Transcript],
    transcript_id: str,
    gene_id: str | None,
    chrom: str,
    strand: str,
    exon: Exon,
    row_number: int,
    stderr: TextIO,
) -> None:
    # Collect rows by transcript, marking transcripts invalid if core metadata conflicts.
    transcript = transcripts.get(transcript_id)
    if transcript is None:
        transcripts[transcript_id] = Transcript(
            transcript_id=transcript_id,
            chrom=chrom,
            strand=strand,
            gene_id=gene_id,
            exons=[exon],
        )
        return

    if transcript.chrom != chrom or transcript.strand != strand:
        transcript.invalid_reason = (
            f"conflicting chromosome or strand for transcript '{transcript_id}' "
            f"at row {row_number}"
        )

    if gene_id:
        if transcript.gene_id is None:
            transcript.gene_id = gene_id
        elif transcript.gene_id != gene_id and not transcript.warned_gene_conflict:
            warn(
                f"transcript '{transcript_id}' has multiple non-empty gene IDs; "
                f"keeping first gene ID '{transcript.gene_id}' and ignoring '{gene_id}'",
                stderr,
            )
            transcript.warned_gene_conflict = True

    transcript.exons.append(exon)


def parse_gtf(
    gtf_path: Path,
    feature: str,
    name_attribute: str,
    gene_attribute: str,
    stderr: TextIO,
) -> dict[str, Transcript]:
    # Validate the input file before scanning rows so failures are immediate.
    if not gtf_path.exists():
        raise FileNotFoundError(f"Input GTF does not exist: {gtf_path}")
    if not gtf_path.is_file():
        raise FileNotFoundError(f"Input GTF is not a file: {gtf_path}")

    transcripts: dict[str, Transcript] = {}

    # Skip malformed rows with warnings so one bad annotation row does not stop conversion.
    with gtf_path.open() as handle:
        for row_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line or line.startswith("#"):
                continue

            columns = line.split("\t")
            if len(columns) != 9:
                warn(f"row {row_number}: expected 9 tab-separated columns; skipping row", stderr)
                continue

            chrom, _source, row_feature, start_text, end_text, _score, strand, _frame, attrs = columns
            if row_feature != feature:
                continue

            if strand not in VALID_STRANDS:
                warn(f"row {row_number}: invalid strand '{strand}'; skipping row", stderr)
                continue

            try:
                gtf_start = int(start_text)
                gtf_end = int(end_text)
            except ValueError:
                warn(f"row {row_number}: start and end must be integers; skipping row", stderr)
                continue

            if gtf_start < 1 or gtf_end < gtf_start:
                warn(
                    f"row {row_number}: invalid coordinates start={gtf_start} end={gtf_end}; "
                    "skipping row",
                    stderr,
                )
                continue

            attributes = parse_gtf_attributes(attrs)
            transcript_id = attributes.get(name_attribute, "").strip()
            if not transcript_id:
                warn(
                    f"row {row_number}: missing required attribute '{name_attribute}'; "
                    "skipping row",
                    stderr,
                )
                continue

            gene_id = attributes.get(gene_attribute, "").strip() or None
            exon = Exon(start=gtf_start - 1, end=gtf_end)
            add_exon(transcripts, transcript_id, gene_id, chrom, strand, exon, row_number, stderr)

    return transcripts


def build_bed_records(transcripts: dict[str, Transcript], stderr: TextIO) -> list[BedRecord]:
    records: list[BedRecord] = []

    # Convert each valid transcript into BED12 block sizes and starts.
    for transcript in transcripts.values():
        if transcript.invalid_reason:
            warn(f"{transcript.invalid_reason}; skipping entire transcript", stderr)
            continue

        if not transcript.exons:
            continue

        exons = sorted(transcript.exons, key=lambda exon: exon.start)
        chrom_start = min(exon.start for exon in exons)
        chrom_end = max(exon.end for exon in exons)
        block_sizes = tuple(exon.end - exon.start for exon in exons)
        block_starts = tuple(exon.start - chrom_start for exon in exons)
        records.append(
            BedRecord(
                chrom=transcript.chrom,
                chrom_start=chrom_start,
                chrom_end=chrom_end,
                name=build_bed_name(transcript.transcript_id, transcript.gene_id),
                strand=transcript.strand,
                block_sizes=block_sizes,
                block_starts=block_starts,
            )
        )

    return sorted(records, key=BedRecord.sort_key)


def write_bed(records: list[BedRecord], bed_path: Path) -> None:
    # Create the destination directory intentionally for local and cluster runs.
    bed_path.parent.mkdir(parents=True, exist_ok=True)
    with bed_path.open("w") as handle:
        for record in records:
            handle.write(record.to_line())
            handle.write("\n")


def main() -> int:
    args = parse_args()

    # Keep orchestration here: parse GTF, build records, write BED, and report failures.
    try:
        transcripts = parse_gtf(
            args.gtf,
            args.feature,
            args.name_attribute,
            args.gene_attribute,
            sys.stderr,
        )
        records = build_bed_records(transcripts, sys.stderr)
        if not records:
            print("ERROR: no transcripts were written.", file=sys.stderr)
            return 1
        write_bed(records, args.bed)
    except OSError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {len(records)} transcript BED12 record(s) to {args.bed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
