"""Versioned scientific-context tables and receipt admission.

The context transaction is a deterministic projection of validated Step 09
candidates onto one hash-bound reference and one fixed known-motif catalog.
It supplies figure-ready scientific values; it does not render figures,
discover motifs, infer transcript direction, or adjudicate candidates.
"""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from norad.contracts.scientific_evidence.step08 import (
    ContractError,
    NA_VALUE,
    Table,
    fail,
    parse_nonnegative_int,
    parse_number,
    read_tsv,
    require_file,
    require_text,
    sha256_file,
    validate_enum,
    validate_hash,
    validate_safe_id,
    values_close,
)
from norad.contracts.scientific_evidence.step09 import (
    STEP09_RESULT_HEADER,
    validate_step09_projection,
)

__all__ = (
    "ContractError",
    "NA_VALUE",
    "ContextTable",
    "ScientificContextOutputs",
    "ScientificContextTransaction",
    "SCIENTIFIC_CONTEXT_SCHEMA_VERSION",
    "SCIENTIFIC_CONTEXT_RECEIPT_SCHEMA_VERSION",
    "CANDIDATE_CONTEXT_HEADER",
    "MOTIF_HITS_HEADER",
    "SEQUENCE_LOGO_HEADER",
    "MOTIF_STATISTICS_HEADER",
    "MOTIF_CATALOG_HEADER",
    "SCIENTIFIC_CONTEXT_RECEIPT_HEADER",
    "CONTEXT_POPULATIONS",
    "CONTEXT_STATUS_BY_CALL_STATUS",
    "CONTEXT_ORIENTATION_POLICY",
    "CONTEXT_RADIUS",
    "LOGO_RADIUS",
    "DISPLAY_LIMIT",
    "MOTIF_ID",
    "MOTIF_RNA_CONSENSUS",
    "MOTIF_DNA_CONSENSUS",
    "MOTIF_MATCH_POLICY",
    "MOTIF_DISTANCE_POLICY",
    "MOTIF_DISTANCE_BIN_WIDTH",
    "FOREGROUND_POPULATION",
    "BACKGROUND_POPULATION",
    "SEPARATE_POPULATION",
    "POPULATION_MINIMUM_COUNTS",
    "validate_motif_catalog",
    "validate_scientific_context_outputs",
    "validate_scientific_context_transaction",
)


SCIENTIFIC_CONTEXT_SCHEMA_VERSION = "1.0.0"
SCIENTIFIC_CONTEXT_RECEIPT_SCHEMA_VERSION = "1.0.0"

CONTEXT_RADIUS = 100
LOGO_RADIUS = 10
DISPLAY_LIMIT = 8
MOTIF_DISTANCE_BIN_WIDTH = 10
CONTEXT_ORIENTATION_POLICY = "legacy_rna_change_oriented_genomic_v1"
MOTIF_MATCH_POLICY = "exact_iupac_presented_strand_v1"
MOTIF_DISTANCE_POLICY = "nearest_midpoint_from_edit_v1"
MOTIF_ID = "PUM_UGUANA"
MOTIF_RNA_CONSENSUS = "UGUANA"
MOTIF_DNA_CONSENSUS = "TGTANA"
FOREGROUND_POPULATION = "significant_up"
BACKGROUND_POPULATION = "background"
SEPARATE_POPULATION = "significant_down"
CONTEXT_POPULATIONS = (
    FOREGROUND_POPULATION,
    BACKGROUND_POPULATION,
    SEPARATE_POPULATION,
)
CONTEXT_STATUS_BY_CALL_STATUS = {
    "significant_up": FOREGROUND_POPULATION,
    "fdr_not_met": BACKGROUND_POPULATION,
    "effect_not_met": BACKGROUND_POPULATION,
    "significant_down": SEPARATE_POPULATION,
}
POPULATION_MINIMUM_COUNTS = {
    FOREGROUND_POPULATION: 10,
    BACKGROUND_POPULATION: 20,
    SEPARATE_POPULATION: 10,
}

_BASES = ("A", "C", "G", "T")
_CONTEXT_STATUSES = ("available", "boundary_truncated")
_ORIENTATION_ACTIONS = ("identity", "reverse_complement")
_AVAILABILITY_STATUSES = (
    "available",
    "population_below_minimum",
    "background_below_minimum",
    "uninformative_table",
)
_STATISTIC_TYPES = ("enrichment", "position_bin")
_COMPLEMENT = str.maketrans("ACGTN", "TGCAN")
_DNA_RE = re.compile(r"^[ACGTN]+$")
_GIT_COMMIT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
_MOTIF_RE = re.compile(r"TGTA[ACGT]A")
_BIN_STARTS = tuple(range(-CONTEXT_RADIUS, CONTEXT_RADIUS, MOTIF_DISTANCE_BIN_WIDTH))
_R_UNIROOT_TOLERANCE = math.ulp(1.0) ** 0.25
_NCP_LOG_BOUND = -math.log(math.ulp(1.0))

CANDIDATE_CONTEXT_HEADER = (
    "analysis_id",
    "candidate_id",
    "population",
    "display_rank",
    "chromosome",
    "position",
    "contig_length",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
    "orientation_action",
    "window_start_1based",
    "window_end_1based",
    "edit_offset_0based",
    "context_status",
    "oriented_sequence",
)

MOTIF_HITS_HEADER = (
    "analysis_id",
    "candidate_id",
    "population",
    "motif_id",
    "matched_sequence",
    "start_offset",
    "end_offset",
    "midpoint_offset",
    "bin_start",
    "bin_end",
)

SEQUENCE_LOGO_HEADER = (
    "analysis_id",
    "population",
    "availability_status",
    "relative_position",
    "base",
    "candidate_count",
    "observed_base_count",
    "base_count",
    "base_fraction",
)

MOTIF_STATISTICS_HEADER = (
    "analysis_id",
    "motif_id",
    "population",
    "statistic_type",
    "availability_status",
    "bin_start",
    "bin_end",
    "eligible_candidate_count",
    "analyzable_candidate_count",
    "candidate_with_motif_count",
    "hit_count",
    "background_candidate_count",
    "background_with_motif_count",
    "odds_ratio",
    "odds_ratio_ci95_lower",
    "odds_ratio_ci95_upper",
    "fisher_p_value_two_sided",
    "fisher_p_value_bh",
)

MOTIF_CATALOG_HEADER = (
    "motif_id",
    "rna_consensus",
    "dna_consensus",
)

SCIENTIFIC_CONTEXT_RECEIPT_HEADER = (
    "schema_name",
    "schema_version",
    "analysis_id",
    "step09_all_sites_path",
    "step09_all_sites_sha256",
    "step09_significant_sites_path",
    "step09_significant_sites_sha256",
    "step09_summary_path",
    "step09_summary_sha256",
    "reference_fasta_path",
    "reference_fasta_sha256",
    "reference_fai_path",
    "reference_fai_sha256",
    "motif_catalog_path",
    "motif_catalog_sha256",
    "scientific_context_schema_version",
    "context_orientation_policy",
    "context_radius",
    "logo_radius",
    "display_limit",
    "motif_match_policy",
    "motif_distance_policy",
    "motif_distance_bin_width",
    "foreground_population",
    "background_population",
    "separate_population",
    "foreground_minimum_count",
    "background_minimum_count",
    "separate_minimum_count",
    "enrichment_test",
    "enrichment_alternative",
    "multiple_testing_method",
    "candidate_context_path",
    "candidate_context_sha256",
    "candidate_context_row_count",
    "motif_hits_path",
    "motif_hits_sha256",
    "motif_hits_row_count",
    "sequence_logo_path",
    "sequence_logo_sha256",
    "sequence_logo_row_count",
    "motif_statistics_path",
    "motif_statistics_sha256",
    "motif_statistics_row_count",
    "published_output_count",
    "producer",
    "producer_version",
    "r_version",
    "biostrings_version",
    "rsamtools_version",
    "git_commit",
    "transaction_state",
)


@dataclass(frozen=True, slots=True)
class ContextTable:
    """Identity of one semantically admitted context TSV."""

    path: Path
    header: tuple[str, ...]
    row_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ScientificContextOutputs:
    """The four figure-ready files in one context transaction."""

    candidate_context: ContextTable
    motif_hits: ContextTable
    sequence_logo: ContextTable
    motif_statistics: ContextTable


@dataclass(frozen=True, slots=True)
class ScientificContextTransaction:
    """A receipt-backed and semantically re-admitted context transaction."""

    receipt: Table
    receipt_sha256: str
    outputs: ScientificContextOutputs


@dataclass(frozen=True, slots=True)
class _FaiEntry:
    length: int
    offset: int
    line_bases: int
    line_width: int


@contextmanager
def _stream_tsv(
    label: str,
    value: str | Path,
    expected_header: Sequence[str],
) -> Iterator[tuple[Path, Iterator[tuple[int, dict[str, str]]]]]:
    path = require_file(label, value)
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            try:
                header = tuple(next(reader))
            except StopIteration:
                fail(f"{label} is empty: {path}")
            if header != tuple(expected_header):
                fail(
                    f"{label} header is invalid: {path}\n"
                    f"Expected: {' | '.join(expected_header)}\n"
                    f"Observed: {' | '.join(header)}"
                )

            def rows() -> Iterator[tuple[int, dict[str, str]]]:
                for row_number, values in enumerate(reader, start=2):
                    if len(values) != len(header):
                        fail(
                            f"{label} row {row_number} has {len(values)} fields; "
                            f"expected {len(header)}: {path}"
                        )
                    yield row_number, dict(zip(header, values, strict=True))

            yield path, rows()
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not read {label} as UTF-8 TSV ({path}): {exc}")


def _context_table(path: Path, header: Sequence[str], row_count: int) -> ContextTable:
    return ContextTable(path, tuple(header), row_count, sha256_file(path))


def _canonical_float(label: str, value: str, *, allow_infinite: bool = False) -> float:
    if allow_infinite and value == "Inf":
        return math.inf
    parsed = parse_number(label, value, nonnegative=True)
    assert parsed is not None
    return parsed


def _expect_na(label: str, row: Mapping[str, str], fields: Sequence[str]) -> None:
    if any(row[field] != NA_VALUE for field in fields):
        fail(f"{label} must use NA for {', '.join(fields)}.")


def _availability(population: str, count: int) -> str:
    return (
        "available"
        if count >= POPULATION_MINIMUM_COUNTS[population]
        else "population_below_minimum"
    )


def _bin_for_midpoint(midpoint: float) -> int:
    index = math.floor((midpoint + CONTEXT_RADIUS) / MOTIF_DISTANCE_BIN_WIDTH)
    return -CONTEXT_RADIUS + index * MOTIF_DISTANCE_BIN_WIDTH


def _format_half(value: float) -> str:
    return f"{value:.1f}"


def _expected_hits(row: Mapping[str, str]) -> list[dict[str, str]]:
    if row["context_status"] != "available":
        return []
    sequence = row["oriented_sequence"]
    edit_offset = int(row["edit_offset_0based"])
    hits: list[dict[str, str]] = []
    for index in range(len(sequence) - len(MOTIF_DNA_CONSENSUS) + 1):
        matched = sequence[index : index + len(MOTIF_DNA_CONSENSUS)]
        if _MOTIF_RE.fullmatch(matched) is None:
            continue
        start = index - edit_offset
        end = start + len(MOTIF_DNA_CONSENSUS) - 1
        midpoint = (start + end) / 2
        bin_start = _bin_for_midpoint(midpoint)
        hits.append(
            {
                "analysis_id": row["analysis_id"],
                "candidate_id": row["candidate_id"],
                "population": row["population"],
                "motif_id": MOTIF_ID,
                "matched_sequence": matched,
                "start_offset": str(start),
                "end_offset": str(end),
                "midpoint_offset": _format_half(midpoint),
                "bin_start": str(bin_start),
                "bin_end": str(bin_start + MOTIF_DISTANCE_BIN_WIDTH),
            }
        )
    return hits


def _validate_candidate_row(
    row: Mapping[str, str],
    row_number: int,
    analysis_id: str,
) -> None:
    label = f"Candidate context row {row_number}"
    if row["analysis_id"] != analysis_id:
        fail(f"{label} has the wrong analysis_id.")
    require_text(f"{label} candidate_id", row["candidate_id"])
    require_text(f"{label} chromosome", row["chromosome"])
    validate_enum(f"{label} population", row["population"], CONTEXT_POPULATIONS)
    validate_enum(
        f"{label} orientation_action",
        row["orientation_action"],
        _ORIENTATION_ACTIONS,
    )
    validate_enum(f"{label} context_status", row["context_status"], _CONTEXT_STATUSES)
    position = parse_nonnegative_int(f"{label} position", row["position"])
    contig_length = parse_nonnegative_int(
        f"{label} contig_length", row["contig_length"]
    )
    start = parse_nonnegative_int(
        f"{label} window_start_1based", row["window_start_1based"]
    )
    end = parse_nonnegative_int(f"{label} window_end_1based", row["window_end_1based"])
    edit_offset = parse_nonnegative_int(
        f"{label} edit_offset_0based", row["edit_offset_0based"]
    )
    if not 1 <= position <= contig_length:
        fail(f"{label} position is outside the declared contig.")
    expected_start = max(1, position - CONTEXT_RADIUS)
    expected_end = min(contig_length, position + CONTEXT_RADIUS)
    if (start, end) != (expected_start, expected_end):
        fail(f"{label} window does not equal the declared genomic +/-100 context.")
    sequence = row["oriented_sequence"]
    if _DNA_RE.fullmatch(sequence) is None or len(sequence) != end - start + 1:
        fail(f"{label} oriented_sequence is not the declared genomic window.")
    expected_offset = position - start
    if row["orientation_action"] == "reverse_complement":
        expected_offset = end - position
    if (
        edit_offset != expected_offset
        or edit_offset >= len(sequence)
        or sequence[edit_offset] != row["rna_ref"]
    ):
        fail(f"{label} center does not equal the declared RNA reference base.")
    for field in ("genomic_ref", "genomic_alt", "rna_ref", "rna_alt"):
        if row[field] not in _BASES:
            fail(f"{label} {field} must be one canonical DNA base.")
    if row["genomic_ref"] == row["genomic_alt"] or row["rna_ref"] == row["rna_alt"]:
        fail(f"{label} must describe a nucleotide substitution.")
    if row["orientation_action"] == "identity":
        expected_change = (row["genomic_ref"], row["genomic_alt"])
    else:
        expected_change = tuple(
            base.translate(_COMPLEMENT)
            for base in (row["genomic_ref"], row["genomic_alt"])
        )
    if (row["rna_ref"], row["rna_alt"]) != expected_change:
        fail(f"{label} orientation_action does not reconcile genomic and RNA bases.")
    expected_status = (
        "available"
        if start == position - CONTEXT_RADIUS and end == position + CONTEXT_RADIUS
        else "boundary_truncated"
    )
    if row["context_status"] != expected_status:
        fail(f"{label} context_status does not match its window bounds.")
    rank = row["display_rank"]
    if row["population"] == BACKGROUND_POPULATION:
        if rank != NA_VALUE:
            fail(f"{label} background candidate must not have a display rank.")
    elif rank != NA_VALUE:
        parsed_rank = parse_nonnegative_int(f"{label} display_rank", rank)
        if not 1 <= parsed_rank <= DISPLAY_LIMIT:
            fail(f"{label} display_rank must be between 1 and {DISPLAY_LIMIT}.")


def _validate_hit_row(
    observed: Mapping[str, str],
    expected: Mapping[str, str],
    row_number: int,
) -> None:
    if observed != expected:
        fail(
            "Motif hits must contain every exact overlapping PUM hit in "
            f"candidate order; first disagreement is row {row_number}."
        )


def _conditional_fisher_values(
    a: int,
    b: int,
    c: int,
    d: int,
) -> tuple[float, float, float, float]:
    """Return R-compatible conditional odds, 95% CI, and two-sided p-value."""

    first_column = a + c
    second_column = b + d
    first_row = a + b
    lower_support = max(0, first_row - second_column)
    upper_support = min(first_row, first_column)
    support = tuple(range(lower_support, upper_support + 1))
    log_coefficients = tuple(
        math.lgamma(first_column + 1)
        - math.lgamma(value + 1)
        - math.lgamma(first_column - value + 1)
        + math.lgamma(second_column + 1)
        - math.lgamma(first_row - value + 1)
        - math.lgamma(second_column - first_row + value + 1)
        for value in support
    )

    def probabilities(log_ncp: float) -> tuple[float, ...]:
        log_weights = tuple(
            coefficient + log_ncp * value
            for coefficient, value in zip(log_coefficients, support, strict=True)
        )
        maximum = max(log_weights)
        weights = tuple(math.exp(value - maximum) for value in log_weights)
        total = math.fsum(weights)
        return tuple(value / total for value in weights)

    observed_index = a - lower_support
    null_probabilities = probabilities(0.0)
    observed_probability = null_probabilities[observed_index]
    p_value = min(
        1.0,
        math.fsum(
            probability
            for probability in null_probabilities
            if probability <= observed_probability * (1.0 + 1e-7)
        ),
    )

    def mean(log_ncp: float) -> float:
        return math.fsum(
            value * probability
            for value, probability in zip(support, probabilities(log_ncp), strict=True)
        )

    def lower_tail(log_ncp: float) -> float:
        return math.fsum(probabilities(log_ncp)[: observed_index + 1])

    def upper_tail(log_ncp: float) -> float:
        return math.fsum(probabilities(log_ncp)[observed_index:])

    def solve(
        statistic: Callable[[float], float],
        target: float,
        *,
        increasing: bool,
    ) -> float:
        lower = -_NCP_LOG_BOUND
        upper = _NCP_LOG_BOUND
        lower_delta = statistic(lower) - target
        upper_delta = statistic(upper) - target
        if (increasing and not lower_delta <= 0 <= upper_delta) or (
            not increasing and not upper_delta <= 0 <= lower_delta
        ):
            return math.exp(lower if abs(lower_delta) <= abs(upper_delta) else upper)
        for _ in range(80):
            midpoint = (lower + upper) / 2.0
            delta = statistic(midpoint) - target
            if (delta < 0) == increasing:
                lower = midpoint
            else:
                upper = midpoint
        return math.exp((lower + upper) / 2.0)

    odds_ratio = (
        0.0
        if a == lower_support
        else math.inf
        if a == upper_support
        else solve(mean, float(a), increasing=True)
    )
    alpha = 0.025
    ci_lower = 0.0 if a == lower_support else solve(upper_tail, alpha, increasing=True)
    ci_upper = (
        math.inf if a == upper_support else solve(lower_tail, alpha, increasing=False)
    )
    return odds_ratio, ci_lower, ci_upper, p_value


def _r_uniroot_value_close(observed: float, expected: float) -> bool:
    """Compare on the root scale used by R's default ``uniroot`` call."""

    if math.isinf(expected) or math.isinf(observed):
        return observed == expected
    observed_root = observed if observed <= 1.0 else 1.0 / observed
    expected_root = expected if expected <= 1.0 else 1.0 / expected
    return math.isclose(
        observed_root,
        expected_root,
        rel_tol=1.5e-8,
        abs_tol=_R_UNIROOT_TOLERANCE,
    )


def _validate_logo_rows(
    value: str | Path,
    analysis_id: str,
    analyzable: Mapping[str, int],
    logo_counts: Mapping[str, Mapping[int, Mapping[str, int]]],
) -> ContextTable:
    row_count = 0
    with _stream_tsv("Sequence logo", value, SEQUENCE_LOGO_HEADER) as (path, rows):
        for population in CONTEXT_POPULATIONS:
            candidate_count = analyzable[population]
            status = _availability(population, candidate_count)
            for position in range(-LOGO_RADIUS, LOGO_RADIUS + 1):
                counts = logo_counts[population][position]
                observed_count = sum(counts.values())
                for base in _BASES:
                    try:
                        row_number, row = next(rows)
                    except StopIteration:
                        fail("Sequence logo lacks its complete fixed matrix.")
                    expected_identity = {
                        "analysis_id": analysis_id,
                        "population": population,
                        "availability_status": status,
                        "relative_position": str(position),
                        "base": base,
                        "candidate_count": str(candidate_count),
                        "observed_base_count": str(observed_count),
                        "base_count": str(counts[base]),
                    }
                    if any(
                        row[field] != expected
                        for field, expected in expected_identity.items()
                    ):
                        fail(f"Sequence logo row {row_number} does not reconcile.")
                    fraction = parse_number(
                        f"Sequence logo row {row_number} base_fraction",
                        row["base_fraction"],
                        allow_na=True,
                        nonnegative=True,
                    )
                    expected_fraction = (
                        None if observed_count == 0 else counts[base] / observed_count
                    )
                    if not values_close(fraction, expected_fraction):
                        fail(
                            f"Sequence logo row {row_number} fraction does not reconcile."
                        )
                    row_count += 1
        try:
            next(rows)
        except StopIteration:
            pass
        else:
            fail("Sequence logo contains rows beyond its fixed matrix.")
    return _context_table(path, SEQUENCE_LOGO_HEADER, row_count)


def _validate_enrichment_values(
    row: Mapping[str, str],
    row_number: int,
    status: str,
    foreground_count: int,
    foreground_with_motif: int,
    background_count: int,
    background_with_motif: int,
) -> None:
    statistical_fields = (
        "odds_ratio",
        "odds_ratio_ci95_lower",
        "odds_ratio_ci95_upper",
        "fisher_p_value_two_sided",
        "fisher_p_value_bh",
    )
    if status != "available":
        _expect_na(f"Motif statistics row {row_number}", row, statistical_fields)
        return
    odds = _canonical_float(
        f"Motif statistics row {row_number} odds_ratio",
        row["odds_ratio"],
        allow_infinite=True,
    )
    lower = _canonical_float(
        f"Motif statistics row {row_number} odds-ratio lower bound",
        row["odds_ratio_ci95_lower"],
        allow_infinite=True,
    )
    upper = _canonical_float(
        f"Motif statistics row {row_number} odds-ratio upper bound",
        row["odds_ratio_ci95_upper"],
        allow_infinite=True,
    )
    if lower > odds or odds > upper:
        fail(f"Motif statistics row {row_number} odds ratio lies outside its CI.")
    expected_odds, expected_lower, expected_upper, expected_p = (
        _conditional_fisher_values(
            foreground_with_motif,
            foreground_count - foreground_with_motif,
            background_with_motif,
            background_count - background_with_motif,
        )
    )
    if not _r_uniroot_value_close(odds, expected_odds):
        fail(
            f"Motif statistics row {row_number} conditional odds ratio "
            "does not reconcile."
        )
    if not _r_uniroot_value_close(lower, expected_lower):
        fail(
            f"Motif statistics row {row_number} odds-ratio lower bound "
            "does not reconcile."
        )
    if not _r_uniroot_value_close(upper, expected_upper):
        fail(
            f"Motif statistics row {row_number} odds-ratio upper bound "
            "does not reconcile."
        )
    p_value = parse_number(
        f"Motif statistics row {row_number} Fisher p-value",
        row["fisher_p_value_two_sided"],
        nonnegative=True,
    )
    if row["fisher_p_value_bh"] != NA_VALUE:
        fail(
            f"Motif statistics row {row_number} must not report BH for the "
            "single registered motif."
        )
    if p_value is None or p_value > 1 or not values_close(p_value, expected_p):
        fail(f"Motif statistics row {row_number} Fisher p-value does not reconcile.")


def _validate_statistics_rows(
    value: str | Path,
    analysis_id: str,
    eligible: Mapping[str, int],
    analyzable: Mapping[str, int],
    candidates_with_motif: Mapping[str, int],
    hit_counts: Mapping[str, Mapping[int, int]],
    nearest_counts: Mapping[str, Mapping[int, int]],
) -> ContextTable:
    row_count = 0
    with _stream_tsv("Motif statistics", value, MOTIF_STATISTICS_HEADER) as (
        path,
        rows,
    ):
        try:
            row_number, enrichment = next(rows)
        except StopIteration:
            fail("Motif statistics lacks the significant-up enrichment row.")
        foreground_count = analyzable[FOREGROUND_POPULATION]
        background_count = analyzable[BACKGROUND_POPULATION]
        foreground_with = candidates_with_motif[FOREGROUND_POPULATION]
        background_with = candidates_with_motif[BACKGROUND_POPULATION]
        if foreground_count < POPULATION_MINIMUM_COUNTS[FOREGROUND_POPULATION]:
            enrichment_status = "population_below_minimum"
        elif background_count < POPULATION_MINIMUM_COUNTS[BACKGROUND_POPULATION]:
            enrichment_status = "background_below_minimum"
        elif foreground_with + background_with in (
            0,
            foreground_count + background_count,
        ):
            enrichment_status = "uninformative_table"
        else:
            enrichment_status = "available"
        expected_enrichment = {
            "analysis_id": analysis_id,
            "motif_id": MOTIF_ID,
            "population": FOREGROUND_POPULATION,
            "statistic_type": "enrichment",
            "availability_status": enrichment_status,
            "bin_start": NA_VALUE,
            "bin_end": NA_VALUE,
            "eligible_candidate_count": str(eligible[FOREGROUND_POPULATION]),
            "analyzable_candidate_count": str(foreground_count),
            "candidate_with_motif_count": str(foreground_with),
            "hit_count": str(sum(hit_counts[FOREGROUND_POPULATION].values())),
            "background_candidate_count": str(background_count),
            "background_with_motif_count": str(background_with),
        }
        if any(
            enrichment[field] != expected
            for field, expected in expected_enrichment.items()
        ):
            fail(
                f"Motif statistics row {row_number} enrichment counts do not reconcile."
            )
        _validate_enrichment_values(
            enrichment,
            row_number,
            enrichment_status,
            foreground_count,
            foreground_with,
            background_count,
            background_with,
        )
        row_count += 1

        for population in CONTEXT_POPULATIONS:
            status = _availability(population, analyzable[population])
            for bin_start in _BIN_STARTS:
                try:
                    row_number, row = next(rows)
                except StopIteration:
                    fail("Motif statistics lacks its complete fixed position bins.")
                expected = {
                    "analysis_id": analysis_id,
                    "motif_id": MOTIF_ID,
                    "population": population,
                    "statistic_type": "position_bin",
                    "availability_status": status,
                    "bin_start": str(bin_start),
                    "bin_end": str(bin_start + MOTIF_DISTANCE_BIN_WIDTH),
                    "eligible_candidate_count": str(eligible[population]),
                    "analyzable_candidate_count": str(analyzable[population]),
                    "candidate_with_motif_count": str(
                        nearest_counts[population][bin_start]
                    ),
                    "hit_count": str(hit_counts[population][bin_start]),
                }
                if any(row[field] != wanted for field, wanted in expected.items()):
                    fail(
                        f"Motif statistics row {row_number} position bin does not reconcile."
                    )
                _expect_na(
                    f"Motif statistics row {row_number}",
                    row,
                    (
                        "background_candidate_count",
                        "background_with_motif_count",
                        "odds_ratio",
                        "odds_ratio_ci95_lower",
                        "odds_ratio_ci95_upper",
                        "fisher_p_value_two_sided",
                        "fisher_p_value_bh",
                    ),
                )
                row_count += 1
        try:
            next(rows)
        except StopIteration:
            pass
        else:
            fail("Motif statistics contains rows beyond its fixed roster.")
    return _context_table(path, MOTIF_STATISTICS_HEADER, row_count)


def validate_motif_catalog(value: str | Path) -> Table:
    """Validate the sole approved v1 known-motif model."""

    table = read_tsv("Scientific-context motif catalog", value, MOTIF_CATALOG_HEADER)
    expected = {
        "motif_id": MOTIF_ID,
        "rna_consensus": MOTIF_RNA_CONSENSUS,
        "dna_consensus": MOTIF_DNA_CONSENSUS,
    }
    if table.rows != [expected]:
        fail("Scientific-context motif catalog must contain exactly PUM UGUANA/TGTANA.")
    return table


def validate_scientific_context_outputs(
    candidate_context: str | Path,
    motif_hits: str | Path,
    sequence_logo: str | Path,
    motif_statistics: str | Path,
    analysis_id: str,
) -> ScientificContextOutputs:
    """Stream and reconcile the four figure-ready scientific-context TSVs."""

    validate_safe_id("analysis_id", analysis_id)
    eligible = {population: 0 for population in CONTEXT_POPULATIONS}
    analyzable = {population: 0 for population in CONTEXT_POPULATIONS}
    candidates_with_motif = {population: 0 for population in CONTEXT_POPULATIONS}
    hit_counts = {
        population: {bin_start: 0 for bin_start in _BIN_STARTS}
        for population in CONTEXT_POPULATIONS
    }
    nearest_counts = {
        population: {bin_start: 0 for bin_start in _BIN_STARTS}
        for population in CONTEXT_POPULATIONS
    }
    logo_counts = {
        population: {
            position: {base: 0 for base in _BASES}
            for position in range(-LOGO_RADIUS, LOGO_RADIUS + 1)
        }
        for population in CONTEXT_POPULATIONS
    }
    candidate_ids: set[str] = set()
    display_ranks: set[int] = set()
    significant_count = 0
    candidate_row_count = 0
    hit_row_count = 0

    with (
        _stream_tsv(
            "Candidate context", candidate_context, CANDIDATE_CONTEXT_HEADER
        ) as (candidate_path, candidate_rows),
        _stream_tsv("Motif hits", motif_hits, MOTIF_HITS_HEADER) as (
            hits_path,
            observed_hits,
        ),
    ):
        next_hit_number = 2
        for row_number, row in candidate_rows:
            _validate_candidate_row(row, row_number, analysis_id)
            candidate_id = row["candidate_id"]
            if candidate_id in candidate_ids:
                fail(
                    f"Candidate context contains duplicate candidate_id: {candidate_id}"
                )
            candidate_ids.add(candidate_id)
            candidate_row_count += 1
            population = row["population"]
            eligible[population] += 1
            if population != BACKGROUND_POPULATION:
                significant_count += 1
            if row["display_rank"] != NA_VALUE:
                rank = int(row["display_rank"])
                if rank in display_ranks:
                    fail(f"Candidate context contains duplicate display_rank: {rank}")
                display_ranks.add(rank)
            expected_hits = _expected_hits(row)
            for expected in expected_hits:
                try:
                    observed_number, observed = next(observed_hits)
                except StopIteration:
                    fail("Motif hits omits an exact hit from candidate context.")
                _validate_hit_row(observed, expected, observed_number)
                next_hit_number = observed_number + 1
                bin_start = int(expected["bin_start"])
                hit_counts[population][bin_start] += 1
                hit_row_count += 1
            if expected_hits:
                candidates_with_motif[population] += 1
                nearest = min(
                    expected_hits,
                    key=lambda hit: (
                        abs(float(hit["midpoint_offset"])),
                        int(hit["start_offset"]),
                    ),
                )
                nearest_counts[population][int(nearest["bin_start"])] += 1
            if row["context_status"] == "available":
                analyzable[population] += 1
                sequence = row["oriented_sequence"]
                center = int(row["edit_offset_0based"])
                for position in range(-LOGO_RADIUS, LOGO_RADIUS + 1):
                    base = sequence[center + position]
                    if base in _BASES:
                        logo_counts[population][position][base] += 1
        try:
            extra_number, _ = next(observed_hits)
        except StopIteration:
            pass
        else:
            fail(
                f"Motif hits contains an extra row at {extra_number or next_hit_number}."
            )

    selected_count = min(DISPLAY_LIMIT, significant_count)
    if display_ranks != set(range(1, selected_count + 1)):
        fail(
            "Candidate context display ranks must select exactly the top-eight roster."
        )

    candidate_table = _context_table(
        candidate_path, CANDIDATE_CONTEXT_HEADER, candidate_row_count
    )
    hit_table = _context_table(hits_path, MOTIF_HITS_HEADER, hit_row_count)
    logo_table = _validate_logo_rows(
        sequence_logo, analysis_id, analyzable, logo_counts
    )
    statistics_table = _validate_statistics_rows(
        motif_statistics,
        analysis_id,
        eligible,
        analyzable,
        candidates_with_motif,
        hit_counts,
        nearest_counts,
    )
    return ScientificContextOutputs(
        candidate_table,
        hit_table,
        logo_table,
        statistics_table,
    )


def _bound_path(row: Mapping[str, str], prefix: str) -> Path:
    path_text = row[f"{prefix}_path"]
    require_text(f"Scientific-context receipt {prefix}_path", path_text)
    path = Path(path_text)
    if not path.is_absolute() or path.resolve() != path:
        fail(
            f"Scientific-context receipt {prefix}_path must be absolute and canonical."
        )
    resolved = require_file(f"Scientific-context receipt {prefix}", path)
    validate_hash(
        f"Scientific-context receipt {prefix}_sha256", row[f"{prefix}_sha256"]
    )
    if sha256_file(resolved) != row[f"{prefix}_sha256"]:
        fail(f"Scientific-context receipt {prefix}_sha256 is stale.")
    return resolved


def _read_fai(path: Path) -> dict[str, _FaiEntry]:
    entries: dict[str, _FaiEntry] = {}
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream, delimiter="\t", strict=True)
            for row_number, fields in enumerate(reader, start=1):
                if len(fields) != 5:
                    fail(
                        f"Reference FAI row {row_number} must contain exactly five fields."
                    )
                name = fields[0]
                require_text(f"Reference FAI row {row_number} contig", name)
                if name in entries:
                    fail(f"Reference FAI contains duplicate contig: {name}")
                length = parse_nonnegative_int(
                    f"Reference FAI row {row_number} length", fields[1]
                )
                offset = parse_nonnegative_int(
                    f"Reference FAI row {row_number} offset", fields[2]
                )
                line_bases = parse_nonnegative_int(
                    f"Reference FAI row {row_number} line_bases", fields[3]
                )
                line_width = parse_nonnegative_int(
                    f"Reference FAI row {row_number} line_width", fields[4]
                )
                if length < 1 or line_bases < 1 or line_width < line_bases:
                    fail(f"Reference FAI row {row_number} has invalid dimensions.")
                entries[name] = _FaiEntry(length, offset, line_bases, line_width)
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not read reference FAI ({path}): {exc}")
    if not entries:
        fail("Reference FAI contains no contigs.")
    return entries


def _read_fasta_window(
    stream,
    fasta_path: Path,
    contig: str,
    entry: _FaiEntry,
    start: int,
    end: int,
) -> str:
    if not 1 <= start <= end <= entry.length:
        fail(f"Candidate context window is outside reference contig {contig}.")
    zero_based = start - 1
    remaining = end - start + 1
    chunks: list[bytes] = []
    while remaining:
        line_index, column = divmod(zero_based, entry.line_bases)
        take = min(remaining, entry.line_bases - column)
        stream.seek(entry.offset + line_index * entry.line_width + column)
        chunk = stream.read(take)
        if len(chunk) != take:
            fail(
                f"Reference FASTA ended inside the FAI-declared {contig} sequence: "
                f"{fasta_path}"
            )
        chunks.append(chunk)
        zero_based += take
        remaining -= take
    try:
        sequence = b"".join(chunks).decode("ascii").upper()
    except UnicodeError:
        fail(f"Reference FASTA {contig} window is not ASCII nucleotide text.")
    if _DNA_RE.fullmatch(sequence) is None:
        fail(f"Reference FASTA {contig} window contains unsupported bases.")
    return sequence


def _fasta_header_before_offset(stream, fasta_path: Path, offset: int) -> str:
    cursor = offset
    suffix = b""
    marker = -1
    while cursor > 0 and marker < 0:
        start = max(0, cursor - 4096)
        stream.seek(start)
        suffix = stream.read(cursor - start) + suffix
        marker = suffix.rfind(b"\n>")
        if marker >= 0:
            marker += 1
            break
        if start == 0 and suffix.startswith(b">"):
            marker = 0
            break
        cursor = start
    if marker < 0:
        fail(f"Reference FAI offset does not follow a FASTA header: {fasta_path}")
    header_record = suffix[marker:]
    newline = header_record.find(b"\n")
    if newline < 0 or marker + newline + 1 != len(suffix):
        fail(
            f"Reference FAI offset does not identify the first FASTA base: {fasta_path}"
        )
    try:
        header = header_record[1:newline].rstrip(b"\r").decode("utf-8")
    except UnicodeError:
        fail(f"Reference FASTA header before offset {offset} is not UTF-8.")
    name = header.split(maxsplit=1)[0] if header else ""
    if not name:
        fail(f"Reference FASTA contains an empty contig header before offset {offset}.")
    return name


def _validate_fai_entry(
    stream,
    fasta_path: Path,
    contig: str,
    entry: _FaiEntry,
) -> None:
    if _fasta_header_before_offset(stream, fasta_path, entry.offset) != contig:
        fail(f"Reference FAI contig name does not match its FASTA header: {contig}")
    _read_fasta_window(stream, fasta_path, contig, entry, 1, 1)
    _read_fasta_window(stream, fasta_path, contig, entry, entry.length, entry.length)
    last = entry.length - 1
    line_index, column = divmod(last, entry.line_bases)
    last_byte = entry.offset + line_index * entry.line_width + column
    newline_width = entry.line_width - entry.line_bases
    stream.seek(last_byte + 1)
    trailer = stream.read(newline_width + 1)
    if not trailer:
        return
    if trailer.startswith(b"\r\n"):
        following = trailer[2:]
    elif trailer.startswith(b"\n"):
        following = trailer[1:]
    else:
        fail(f"Reference FAI length ends before FASTA contig {contig} ends.")
    if following and following != b">":
        fail(f"Reference FAI length ends before FASTA contig {contig} ends.")


def _reconcile_reference_context(
    candidate_context: Path,
    reference_fasta: Path,
    reference_fai: Path,
) -> None:
    entries = _read_fai(reference_fai)
    validated_contigs: set[str] = set()
    try:
        with (
            reference_fasta.open("rb") as fasta_stream,
            _stream_tsv(
                "Candidate context", candidate_context, CANDIDATE_CONTEXT_HEADER
            ) as (_path, rows),
        ):
            for row_number, row in rows:
                chromosome = row["chromosome"]
                entry = entries.get(chromosome)
                if entry is None:
                    fail(
                        f"Candidate context row {row_number} chromosome is absent "
                        f"from the bound FAI: {chromosome}"
                    )
                if chromosome not in validated_contigs:
                    _validate_fai_entry(
                        fasta_stream,
                        reference_fasta,
                        chromosome,
                        entry,
                    )
                    validated_contigs.add(chromosome)
                if int(row["contig_length"]) != entry.length:
                    fail(
                        f"Candidate context row {row_number} contig_length differs "
                        "from the bound FAI."
                    )
                start = int(row["window_start_1based"])
                end = int(row["window_end_1based"])
                position = int(row["position"])
                genomic = _read_fasta_window(
                    fasta_stream,
                    reference_fasta,
                    chromosome,
                    entry,
                    start,
                    end,
                )
                genomic_center = genomic[position - start]
                if genomic_center != row["genomic_ref"]:
                    fail(
                        f"Candidate context row {row_number} genomic_ref differs "
                        "from the bound reference center."
                    )
                oriented = (
                    genomic
                    if row["orientation_action"] == "identity"
                    else genomic.translate(_COMPLEMENT)[::-1]
                )
                if oriented != row["oriented_sequence"]:
                    fail(
                        f"Candidate context row {row_number} oriented_sequence differs "
                        "from the bound reference window."
                    )
                if oriented[int(row["edit_offset_0based"])] != row["rna_ref"]:
                    fail(
                        f"Candidate context row {row_number} RNA center differs "
                        "from the oriented bound reference."
                    )
    except OSError as exc:
        fail(f"Could not reconcile candidate context with reference FASTA: {exc}")


def _validate_receipt_constants(row: Mapping[str, str], analysis_id: str) -> None:
    fixed = {
        "schema_name": "norad.scientific_context_receipt",
        "schema_version": SCIENTIFIC_CONTEXT_RECEIPT_SCHEMA_VERSION,
        "analysis_id": analysis_id,
        "scientific_context_schema_version": SCIENTIFIC_CONTEXT_SCHEMA_VERSION,
        "context_orientation_policy": CONTEXT_ORIENTATION_POLICY,
        "context_radius": str(CONTEXT_RADIUS),
        "logo_radius": str(LOGO_RADIUS),
        "display_limit": str(DISPLAY_LIMIT),
        "motif_match_policy": MOTIF_MATCH_POLICY,
        "motif_distance_policy": MOTIF_DISTANCE_POLICY,
        "motif_distance_bin_width": str(MOTIF_DISTANCE_BIN_WIDTH),
        "foreground_population": FOREGROUND_POPULATION,
        "background_population": "fdr_not_met,effect_not_met",
        "separate_population": SEPARATE_POPULATION,
        "foreground_minimum_count": str(
            POPULATION_MINIMUM_COUNTS[FOREGROUND_POPULATION]
        ),
        "background_minimum_count": str(
            POPULATION_MINIMUM_COUNTS[BACKGROUND_POPULATION]
        ),
        "separate_minimum_count": str(POPULATION_MINIMUM_COUNTS[SEPARATE_POPULATION]),
        "enrichment_test": "Fisher_exact",
        "enrichment_alternative": "two.sided",
        "multiple_testing_method": "none_single_registered_motif",
        "published_output_count": "5",
        "producer": "build_scientific_context",
        "producer_version": "1.0.0",
        "transaction_state": "complete",
    }
    for field, expected in fixed.items():
        if row[field] != expected:
            fail(
                f"Scientific-context receipt {field} must be {expected}; "
                f"got: {row[field]}"
            )
    for field in ("r_version", "biostrings_version", "rsamtools_version"):
        require_text(f"Scientific-context receipt {field}", row[field])
    if _GIT_COMMIT_RE.fullmatch(row["git_commit"]) is None:
        fail("Scientific-context receipt git_commit must be a full hexadecimal commit.")


def _reconcile_step09_candidates(
    all_sites: Path,
    candidate_context: Path,
    analysis_id: str,
) -> None:
    significant: list[tuple[float, float, str]] = []
    # Reopen only to project the fields already validated by Step 09 admission.
    try:
        with all_sites.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t", strict=True)
            for row in reader:
                if row["call_status"] in (FOREGROUND_POPULATION, SEPARATE_POPULATION):
                    significant.append(
                        (
                            float(row["cmh_fdr_bh"]),
                            -abs(float(row["treatment_control_difference"])),
                            row["candidate_id"],
                        )
                    )
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not reread admitted Step 09 all-sites: {exc}")
    ranked = {
        candidate_id: str(rank)
        for rank, (_fdr, _effect, candidate_id) in enumerate(
            sorted(significant)[:DISPLAY_LIMIT], start=1
        )
    }
    with _stream_tsv(
        "Candidate context", candidate_context, CANDIDATE_CONTEXT_HEADER
    ) as (_candidate_path, context_rows):
        context_iterator = iter(context_rows)
        try:
            with all_sites.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream, delimiter="\t", strict=True)
                if (
                    reader.fieldnames is None
                    or tuple(reader.fieldnames[: len(STEP09_RESULT_HEADER)])
                    != STEP09_RESULT_HEADER
                ):
                    fail(
                        "Step 09 all-sites fixed header changed during reconciliation."
                    )
                for step09 in reader:
                    population = CONTEXT_STATUS_BY_CALL_STATUS.get(
                        step09["call_status"]
                    )
                    if population is None:
                        continue
                    try:
                        row_number, context = next(context_iterator)
                    except StopIteration:
                        fail("Candidate context omits an eligible Step 09 candidate.")
                    expected = {
                        "analysis_id": analysis_id,
                        "candidate_id": step09["candidate_id"],
                        "population": population,
                        "display_rank": ranked.get(step09["candidate_id"], NA_VALUE),
                        "chromosome": step09["chromosome"],
                        "position": step09["position"],
                        "genomic_ref": step09["genomic_ref"],
                        "genomic_alt": step09["genomic_alt"],
                        "rna_ref": step09["rna_ref"],
                        "rna_alt": step09["rna_alt"],
                    }
                    if any(
                        context[field] != value for field, value in expected.items()
                    ):
                        fail(
                            f"Candidate context row {row_number} does not reconcile "
                            "with its Step 09 candidate."
                        )
        except (OSError, UnicodeError, csv.Error) as exc:
            fail(f"Could not reconcile admitted Step 09 all-sites: {exc}")
        try:
            next(context_iterator)
        except StopIteration:
            pass
        else:
            fail("Candidate context contains a candidate absent from Step 09.")


def validate_scientific_context_transaction(
    receipt: str | Path,
) -> ScientificContextTransaction:
    """Admit a complete receipt-last scientific-context transaction."""

    receipt_table = read_tsv(
        "Scientific-context receipt", receipt, SCIENTIFIC_CONTEXT_RECEIPT_HEADER
    )
    if len(receipt_table.rows) != 1:
        fail("Scientific-context receipt must contain exactly one data row.")
    row = receipt_table.rows[0]
    analysis_id = row["analysis_id"]
    validate_safe_id("Scientific-context receipt analysis_id", analysis_id)
    _validate_receipt_constants(row, analysis_id)

    inputs = {
        prefix: _bound_path(row, prefix)
        for prefix in (
            "step09_all_sites",
            "step09_significant_sites",
            "step09_summary",
            "reference_fasta",
            "reference_fai",
            "motif_catalog",
        )
    }
    output_paths = {
        prefix: _bound_path(row, prefix)
        for prefix in (
            "candidate_context",
            "motif_hits",
            "sequence_logo",
            "motif_statistics",
        )
    }
    validate_motif_catalog(inputs["motif_catalog"])
    validate_step09_projection(
        inputs["step09_all_sites"],
        inputs["step09_significant_sites"],
        inputs["step09_summary"],
        analysis_id,
    )
    outputs = validate_scientific_context_outputs(
        output_paths["candidate_context"],
        output_paths["motif_hits"],
        output_paths["sequence_logo"],
        output_paths["motif_statistics"],
        analysis_id,
    )
    _reconcile_reference_context(
        output_paths["candidate_context"],
        inputs["reference_fasta"],
        inputs["reference_fai"],
    )
    for prefix, output in (
        ("candidate_context", outputs.candidate_context),
        ("motif_hits", outputs.motif_hits),
        ("sequence_logo", outputs.sequence_logo),
        ("motif_statistics", outputs.motif_statistics),
    ):
        if (
            parse_nonnegative_int(
                f"Scientific-context receipt {prefix}_row_count",
                row[f"{prefix}_row_count"],
            )
            != output.row_count
        ):
            fail(f"Scientific-context receipt {prefix}_row_count is stale.")
    _reconcile_step09_candidates(
        inputs["step09_all_sites"],
        output_paths["candidate_context"],
        analysis_id,
    )
    return ScientificContextTransaction(
        receipt_table,
        sha256_file(receipt_table.path),
        outputs,
    )
