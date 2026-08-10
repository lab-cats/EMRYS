"""Convert GTF transcript exon models to BED12 for RSeQC."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

VALID_STRANDS = frozenset({"+", "-", "."})
DESCRIPTION = (
    "Convert a GTF annotation file to BED12 transcript models suitable "
    "for RSeQC infer_experiment.py."
)

WarningHandler = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class Exon:
    """One exon in BED coordinate space."""

    start: int
    end: int


@dataclass(slots=True)
class Transcript:
    """Collected exons and metadata for one transcript."""

    transcript_id: str
    chrom: str
    strand: str
    gene_id: str | None = None
    exons: list[Exon] = field(default_factory=list)
    invalid_reason: str | None = None


@dataclass(frozen=True, slots=True)
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
        fields = (
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
            "".join(f"{size}," for size in self.block_sizes),
            "".join(f"{start}," for start in self.block_starts),
        )
        return "\t".join(fields)


@dataclass(frozen=True, slots=True)
class _GtfSelection:
    feature: str
    name_attribute: str
    gene_attribute: str


@dataclass(frozen=True, slots=True)
class _ExonObservation:
    transcript_id: str
    gene_id: str | None
    chrom: str
    strand: str
    exon: Exon
    row_number: int


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add the converter owner's arguments to a command parser."""
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


def _report_warning(handler: WarningHandler | None, message: str) -> None:
    if handler is not None:
        handler(message)


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_gtf_attributes(attribute_text: str) -> dict[str, str]:
    attributes: dict[str, str] = {}

    # Accept both common GTF whitespace syntax and GFF-style key=value syntax.
    for segment in attribute_text.strip().rstrip(";").split(";"):
        segment = segment.strip()
        if not segment:
            continue
        if "=" in segment and (
            segment.find("=") < segment.find(" ") or " " not in segment
        ):
            key, value = segment.split("=", 1)
        else:
            parts = segment.split(None, 1)
            key, value = (parts[0], "") if len(parts) == 1 else parts

        key = key.strip()
        if key:
            attributes[key] = _strip_quotes(value)
    return attributes


def _clean_name_component(value: str) -> str:
    return re.sub(r"\s+", "_", value.strip())


def _build_bed_name(transcript_id: str, gene_id: str | None) -> str:
    clean_transcript_id = _clean_name_component(transcript_id)
    if gene_id and (clean_gene_id := _clean_name_component(gene_id)):
        return f"{clean_transcript_id}|{clean_gene_id}"
    return clean_transcript_id


def _parse_exon_row(
    raw_line: str,
    row_number: int,
    selection: _GtfSelection,
    on_warning: WarningHandler | None,
) -> _ExonObservation | None:
    line = raw_line.rstrip("\n")
    if not line or line.startswith("#"):
        return None

    columns = line.split("\t")
    if len(columns) != 9:
        _report_warning(
            on_warning,
            f"row {row_number}: expected 9 tab-separated columns; skipping row",
        )
        return None

    chrom, _, row_feature, start_text, end_text, _, strand, _, attribute_text = columns
    if row_feature != selection.feature:
        return None
    if strand not in VALID_STRANDS:
        _report_warning(
            on_warning,
            f"row {row_number}: invalid strand '{strand}'; skipping row",
        )
        return None

    try:
        gtf_start = int(start_text)
        gtf_end = int(end_text)
    except ValueError:
        _report_warning(
            on_warning,
            f"row {row_number}: start and end must be integers; skipping row",
        )
        return None
    if gtf_start < 1 or gtf_end < gtf_start:
        _report_warning(
            on_warning,
            f"row {row_number}: invalid coordinates start={gtf_start} end={gtf_end}; "
            "skipping row",
        )
        return None

    attributes = _parse_gtf_attributes(attribute_text)
    transcript_id = attributes.get(selection.name_attribute, "").strip()
    if not transcript_id:
        _report_warning(
            on_warning,
            f"row {row_number}: missing required attribute "
            f"'{selection.name_attribute}'; skipping row",
        )
        return None
    return _ExonObservation(
        transcript_id=transcript_id,
        gene_id=attributes.get(selection.gene_attribute, "").strip() or None,
        chrom=chrom,
        strand=strand,
        exon=Exon(start=gtf_start - 1, end=gtf_end),
        row_number=row_number,
    )


def _accumulate_exon(
    transcripts: dict[str, Transcript],
    observation: _ExonObservation,
    warned_gene_conflicts: set[str],
    on_warning: WarningHandler | None,
) -> None:
    transcript = transcripts.get(observation.transcript_id)
    if transcript is None:
        transcripts[observation.transcript_id] = Transcript(
            transcript_id=observation.transcript_id,
            chrom=observation.chrom,
            strand=observation.strand,
            gene_id=observation.gene_id,
            exons=[observation.exon],
        )
        return

    if transcript.chrom != observation.chrom or transcript.strand != observation.strand:
        transcript.invalid_reason = (
            "conflicting chromosome or strand for transcript "
            f"'{observation.transcript_id}' at row {observation.row_number}"
        )
    if observation.gene_id:
        if transcript.gene_id is None:
            transcript.gene_id = observation.gene_id
        elif (
            transcript.gene_id != observation.gene_id
            and observation.transcript_id not in warned_gene_conflicts
        ):
            _report_warning(
                on_warning,
                f"transcript '{observation.transcript_id}' has multiple non-empty "
                f"gene IDs; keeping first gene ID '{transcript.gene_id}' and ignoring "
                f"'{observation.gene_id}'",
            )
            warned_gene_conflicts.add(observation.transcript_id)
    transcript.exons.append(observation.exon)


def _collect_transcripts(
    gtf_path: Path,
    selection: _GtfSelection,
    on_warning: WarningHandler | None,
) -> dict[str, Transcript]:
    if not gtf_path.exists():
        raise FileNotFoundError(f"Input GTF does not exist: {gtf_path}")
    if not gtf_path.is_file():
        raise FileNotFoundError(f"Input GTF is not a file: {gtf_path}")

    transcripts: dict[str, Transcript] = {}
    warned_gene_conflicts: set[str] = set()
    with gtf_path.open(encoding="utf-8") as handle:
        for row_number, raw_line in enumerate(handle, start=1):
            observation = _parse_exon_row(
                raw_line,
                row_number,
                selection,
                on_warning,
            )
            if observation is not None:
                _accumulate_exon(
                    transcripts,
                    observation,
                    warned_gene_conflicts,
                    on_warning,
                )
    return transcripts


def _project_bed_records(
    transcripts: dict[str, Transcript],
    on_warning: WarningHandler | None,
) -> list[BedRecord]:
    records: list[BedRecord] = []
    for transcript in transcripts.values():
        if transcript.invalid_reason:
            _report_warning(
                on_warning,
                f"{transcript.invalid_reason}; skipping entire transcript",
            )
            continue
        if not transcript.exons:
            continue

        exons = sorted(transcript.exons, key=lambda exon: exon.start)
        chrom_start = min(exon.start for exon in exons)
        chrom_end = max(exon.end for exon in exons)
        records.append(
            BedRecord(
                chrom=transcript.chrom,
                chrom_start=chrom_start,
                chrom_end=chrom_end,
                name=_build_bed_name(transcript.transcript_id, transcript.gene_id),
                strand=transcript.strand,
                block_sizes=tuple(exon.end - exon.start for exon in exons),
                block_starts=tuple(exon.start - chrom_start for exon in exons),
            )
        )
    return sorted(records, key=BedRecord.sort_key)


def normalize_gtf(
    gtf_path: Path,
    feature: str,
    name_attribute: str,
    gene_attribute: str,
    on_warning: WarningHandler | None = None,
) -> list[BedRecord]:
    """Normalize one selected GTF feature set into deterministic BED12 records."""
    selection = _GtfSelection(feature, name_attribute, gene_attribute)
    transcripts = _collect_transcripts(gtf_path, selection, on_warning)
    return _project_bed_records(transcripts, on_warning)


def write_bed(records: Sequence[BedRecord], bed_path: Path) -> None:
    bed_path.parent.mkdir(parents=True, exist_ok=True)
    with bed_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(f"{record.to_line()}\n")


def _stderr_warning(message: str) -> None:
    print(f"WARNING: {message}", file=sys.stderr)


def convert_from_args(arguments: argparse.Namespace) -> int:
    """Convert and report one parsed GTF-to-BED12 request."""
    try:
        records = normalize_gtf(
            arguments.gtf,
            arguments.feature,
            arguments.name_attribute,
            arguments.gene_attribute,
            _stderr_warning,
        )
        if not records:
            print("ERROR: no transcripts were written.", file=sys.stderr)
            return 1
        write_bed(records, arguments.bed)
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(records)} transcript BED12 record(s) to {arguments.bed}")
    return 0
