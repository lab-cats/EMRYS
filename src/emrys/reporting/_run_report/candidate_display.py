"""Immutable selected-candidate facts for scientific report presentation."""

from __future__ import annotations

import csv
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

from emrys.contracts.scientific_evidence import scientific_context as owner_context

from .inputs import _assert_snapshot, _fail
from .models import (
    ComputationalResults,
    ComputationalTable,
    ReportRenderError,
    ScientificContextResults,
)


SelectionSource = Literal["step10_display_rank", "step09_display_rule"]
MotifState = Literal[
    "present",
    "no_registered_hit",
    "boundary_unavailable",
    "step10_unavailable",
]

_NA = "NA"
_REGION_MEMBERSHIPS = (
    ("is_cds", "CDS"),
    ("is_five_prime_utr", "5′ UTR"),
    ("is_three_prime_utr", "3′ UTR"),
    ("is_exon", "exon"),
    ("is_intron", "intron"),
)
_CONTEXT_IDENTITY_FIELDS = (
    "analysis_id",
    "candidate_id",
    "chromosome",
    "position",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
)


@dataclass(frozen=True, slots=True)
class CandidateSampleEvidence:
    """One admitted sample's editing rate and exact read support."""

    sample_id: str
    allele_fraction: Decimal | None
    alternate_depth: int | None
    total_depth: int | None


@dataclass(frozen=True, slots=True)
class CandidatePairEvidence:
    """One manifest-defined control/treatment replicate pair."""

    replicate: str
    control: CandidateSampleEvidence
    treatment: CandidateSampleEvidence


@dataclass(frozen=True, slots=True)
class CandidateLocation:
    """Carried Step 08/09 location facts without an inferred exclusive region."""

    chromosome: str
    position_1based: int
    genomic_ref: str
    genomic_alt: str
    rna_ref: str
    rna_alt: str
    workflow_orientation: str
    orientation_policy: str
    annotation_strand: str
    gene_ids: tuple[str, ...]
    transcript_ids: tuple[str, ...]
    region_memberships: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CandidateMotifHit:
    """One exact registered-motif hit admitted by Step 10."""

    motif_id: str
    matched_sequence: str
    start_offset: int
    end_offset: int
    midpoint_offset: Decimal
    bin_start: int
    bin_end: int


@dataclass(frozen=True, slots=True)
class CandidateMotifEvidence:
    """Registered-motif evidence with explicit availability semantics."""

    state: MotifState
    motif_id: str | None
    rna_consensus: str | None
    dna_consensus: str | None
    context_radius: int | None
    match_policy: str | None
    context_status: str | None
    orientation_action: str | None
    window_start_1based: int | None
    window_end_1based: int | None
    edit_offset_0based: int | None
    oriented_sequence: str | None
    hits: tuple[CandidateMotifHit, ...]
    unavailable_reason: str | None


@dataclass(frozen=True, slots=True)
class SelectedCandidate:
    """One selected candidate's complete reader-facing scientific facts."""

    display_rank: int
    candidate_id: str
    call_status: str
    mean_analysis_dp: Decimal | None
    mean_control_af: Decimal | None
    mean_treatment_af: Decimal | None
    treatment_control_difference: Decimal | None
    cmh_fdr_bh: Decimal | None
    common_odds_ratio: Decimal | None
    location: CandidateLocation
    pairs: tuple[CandidatePairEvidence, ...]
    motif: CandidateMotifEvidence


@dataclass(frozen=True, slots=True)
class SelectedCandidateProjection:
    """The one deterministic roster shared by scientific views and figures."""

    analysis_id: str
    control_condition: str
    treatment_condition: str
    selection_source: SelectionSource
    significant_candidate_count: int
    candidates: tuple[SelectedCandidate, ...]


def _decimal(label: str, value: str, *, allow_na: bool = True) -> Decimal | None:
    if value == _NA and allow_na:
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        _fail(f"{label} is not numeric: {value!r}")
    if not parsed.is_finite():
        _fail(f"{label} must be finite: {value!r}")
    return parsed


def _integer(label: str, value: str, *, allow_na: bool = True) -> int | None:
    if value == _NA and allow_na:
        return None
    try:
        parsed = int(value)
    except ValueError:
        _fail(f"{label} is not an integer: {value!r}")
    if parsed < 0:
        _fail(f"{label} must be nonnegative: {value!r}")
    return parsed


def _required_integer(label: str, value: str) -> int:
    parsed = _integer(label, value, allow_na=False)
    assert parsed is not None
    return parsed


def _identifiers(value: str) -> tuple[str, ...]:
    return () if value == _NA else tuple(value.split(";"))


def _visit_rows(
    table: ComputationalTable,
    visitor: Callable[[Mapping[str, str], int], None],
) -> None:
    """Stream one admitted TSV under before/after snapshot and roster checks."""

    label = f"candidate-display input {table.artifact_id!r}"
    _assert_snapshot(table.snapshot, label)
    observed_count = 0
    try:
        with table.path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t", strict=True)
            if tuple(reader.fieldnames or ()) != table.header:
                _fail(f"{label} header changed after canonical admission")
            for row_number, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    _fail(f"{label} row {row_number} has the wrong field count")
                observed_count += 1
                visitor(row, row_number)
    except ReportRenderError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        _fail(f"Could not read {label}: {exc}")
    if observed_count != table.row_count:
        _fail(
            f"{label} row count changed after canonical admission: observed "
            f"{observed_count}; expected {table.row_count}"
        )
    _assert_snapshot(table.snapshot, label)


def _step09_rank_key(row: Mapping[str, str]) -> tuple[Decimal, Decimal, str]:
    fdr = _decimal(
        f"candidate {row['candidate_id']!r} CMH BH FDR",
        row["cmh_fdr_bh"],
        allow_na=False,
    )
    difference = _decimal(
        f"candidate {row['candidate_id']!r} treatment-control difference",
        row["treatment_control_difference"],
        allow_na=False,
    )
    assert fdr is not None and difference is not None
    return fdr, -abs(difference), row["candidate_id"]


def _fallback_rows(
    table: ComputationalTable,
) -> tuple[tuple[dict[str, str], ...], int]:
    selected: list[tuple[tuple[Decimal, Decimal, str], dict[str, str]]] = []
    seen: set[str] = set()

    def retain(row: Mapping[str, str], row_number: int) -> None:
        candidate_id = row["candidate_id"]
        if candidate_id in seen:
            _fail(
                "Admitted Step 09 significant table repeats candidate "
                f"{candidate_id!r} at row {row_number}"
            )
        seen.add(candidate_id)
        selected.append((_step09_rank_key(row), dict(row)))
        selected.sort(key=lambda item: item[0])
        del selected[owner_context.DISPLAY_LIMIT :]

    _visit_rows(table, retain)
    return tuple(row for _key, row in selected), len(seen)


def _selected_context_rows(
    table: ComputationalTable,
) -> dict[str, tuple[int, dict[str, str]]]:
    selected: dict[str, tuple[int, dict[str, str]]] = {}
    ranks: set[int] = set()

    def retain(row: Mapping[str, str], row_number: int) -> None:
        if row["display_rank"] == _NA:
            return
        rank = _required_integer(
            f"Step 10 candidate context row {row_number} display_rank",
            row["display_rank"],
        )
        if not 1 <= rank <= owner_context.DISPLAY_LIMIT:
            _fail(f"Step 10 display_rank is outside the supported roster: {rank}")
        candidate_id = row["candidate_id"]
        if candidate_id in selected:
            _fail(f"Step 10 repeats selected candidate {candidate_id!r}")
        if rank in ranks:
            _fail(f"Step 10 repeats selected display_rank {rank}")
        ranks.add(rank)
        selected[candidate_id] = (rank, dict(row))

    _visit_rows(table, retain)
    if ranks != set(range(1, len(ranks) + 1)):
        _fail("Step 10 selected display ranks are not contiguous from one")
    return selected


def _step09_rows_for_context(
    table: ComputationalTable,
    selected_context: Mapping[str, tuple[int, Mapping[str, str]]],
) -> tuple[dict[str, dict[str, str]], int]:
    selected: dict[str, dict[str, str]] = {}
    seen: set[str] = set()

    def retain(row: Mapping[str, str], row_number: int) -> None:
        candidate_id = row["candidate_id"]
        if candidate_id in seen:
            _fail(
                "Admitted Step 09 significant table repeats candidate "
                f"{candidate_id!r} at row {row_number}"
            )
        seen.add(candidate_id)
        if candidate_id in selected_context:
            selected[candidate_id] = dict(row)

    _visit_rows(table, retain)
    if set(selected) != set(selected_context):
        missing = sorted(set(selected_context) - set(selected))
        _fail(
            "Step 10 selected roster differs from Step 09 significant candidates: "
            + ", ".join(missing)
        )
    expected_count = min(owner_context.DISPLAY_LIMIT, len(seen))
    if len(selected_context) != expected_count:
        _fail(
            "Step 10 selected roster has the wrong size for the admitted Step 09 "
            f"significant population: observed {len(selected_context)}; expected "
            f"{expected_count}"
        )
    return selected, len(seen)


def _validate_context_identity(
    step09_row: Mapping[str, str],
    context_row: Mapping[str, str],
) -> None:
    candidate_id = step09_row["candidate_id"]
    for field in _CONTEXT_IDENTITY_FIELDS:
        if context_row[field] != step09_row[field]:
            _fail(
                f"Step 10 selected candidate {candidate_id!r} differs from Step 09 "
                f"field {field!r}"
            )
    if context_row["population"] != step09_row["call_status"]:
        _fail(
            f"Step 10 selected candidate {candidate_id!r} differs from Step 09 "
            "call population"
        )


def _selected_hits(
    table: ComputationalTable,
    selected_context: Mapping[str, tuple[int, Mapping[str, str]]],
) -> dict[str, tuple[CandidateMotifHit, ...]]:
    hits: dict[str, list[CandidateMotifHit]] = {
        candidate_id: [] for candidate_id in selected_context
    }

    def retain(row: Mapping[str, str], row_number: int) -> None:
        candidate_id = row["candidate_id"]
        if candidate_id not in hits:
            return
        context = selected_context[candidate_id][1]
        if (
            row["analysis_id"] != context["analysis_id"]
            or row["population"] != context["population"]
        ):
            _fail(
                f"Step 10 motif-hit row {row_number} differs from selected candidate "
                f"{candidate_id!r}"
            )
        midpoint = _decimal(
            f"Step 10 motif-hit row {row_number} midpoint_offset",
            row["midpoint_offset"],
            allow_na=False,
        )
        assert midpoint is not None
        hits[candidate_id].append(
            CandidateMotifHit(
                motif_id=row["motif_id"],
                matched_sequence=row["matched_sequence"],
                start_offset=_required_integer_signed(
                    f"Step 10 motif-hit row {row_number} start_offset",
                    row["start_offset"],
                ),
                end_offset=_required_integer_signed(
                    f"Step 10 motif-hit row {row_number} end_offset",
                    row["end_offset"],
                ),
                midpoint_offset=midpoint,
                bin_start=_required_integer_signed(
                    f"Step 10 motif-hit row {row_number} bin_start",
                    row["bin_start"],
                ),
                bin_end=_required_integer_signed(
                    f"Step 10 motif-hit row {row_number} bin_end",
                    row["bin_end"],
                ),
            )
        )

    _visit_rows(table, retain)
    return {candidate_id: tuple(values) for candidate_id, values in hits.items()}


def _required_integer_signed(label: str, value: str) -> int:
    try:
        return int(value)
    except ValueError:
        _fail(f"{label} is not an integer: {value!r}")


def _sample_evidence(
    row: Mapping[str, str],
    sample_id: str,
) -> CandidateSampleEvidence:
    return CandidateSampleEvidence(
        sample_id=sample_id,
        allele_fraction=_decimal(
            f"candidate {row['candidate_id']!r} AF__{sample_id}",
            row[f"AF__{sample_id}"],
        ),
        alternate_depth=_integer(
            f"candidate {row['candidate_id']!r} AD__{sample_id}",
            row[f"AD__{sample_id}"],
        ),
        total_depth=_integer(
            f"candidate {row['candidate_id']!r} DP__{sample_id}",
            row[f"DP__{sample_id}"],
        ),
    )


def _pairs(
    row: Mapping[str, str],
    results: ComputationalResults,
) -> tuple[CandidatePairEvidence, ...]:
    return tuple(
        CandidatePairEvidence(
            replicate=pair.replicate,
            control=_sample_evidence(row, pair.control_sample_id),
            treatment=_sample_evidence(row, pair.treatment_sample_id),
        )
        for pair in results.sample_manifest.pairs
    )


def _location(row: Mapping[str, str]) -> CandidateLocation:
    memberships: list[str] = []
    for field, label in _REGION_MEMBERSHIPS:
        value = row[field]
        if value == "TRUE":
            memberships.append(label)
        elif value != "FALSE":
            _fail(f"candidate {row['candidate_id']!r} has invalid {field}: {value!r}")
    return CandidateLocation(
        chromosome=row["chromosome"],
        position_1based=_required_integer(
            f"candidate {row['candidate_id']!r} position", row["position"]
        ),
        genomic_ref=row["genomic_ref"],
        genomic_alt=row["genomic_alt"],
        rna_ref=row["rna_ref"],
        rna_alt=row["rna_alt"],
        workflow_orientation=row["orientation"],
        orientation_policy=row["orientation_policy"],
        annotation_strand=row["annotation_strand"],
        gene_ids=_identifiers(row["gene_ids"]),
        transcript_ids=_identifiers(row["transcript_ids"]),
        region_memberships=tuple(memberships),
    )


def _motif_evidence(
    context_row: Mapping[str, str] | None,
    hits: tuple[CandidateMotifHit, ...],
    unavailable_reason: str | None,
) -> CandidateMotifEvidence:
    common = {
        "motif_id": owner_context.MOTIF_ID,
        "rna_consensus": owner_context.MOTIF_RNA_CONSENSUS,
        "dna_consensus": owner_context.MOTIF_DNA_CONSENSUS,
        "context_radius": owner_context.CONTEXT_RADIUS,
        "match_policy": owner_context.MOTIF_MATCH_POLICY,
    }
    if context_row is None:
        return CandidateMotifEvidence(
            state="step10_unavailable",
            motif_id=None,
            rna_consensus=None,
            dna_consensus=None,
            context_radius=None,
            match_policy=None,
            context_status=None,
            orientation_action=None,
            window_start_1based=None,
            window_end_1based=None,
            edit_offset_0based=None,
            oriented_sequence=None,
            hits=(),
            unavailable_reason=(
                unavailable_reason
                or "The complete admitted Step 10 scientific-context bundle is unavailable."
            ),
        )
    context_status = context_row["context_status"]
    if context_status == "boundary_truncated":
        if hits:
            _fail(
                "Boundary-truncated Step 10 candidate unexpectedly has admitted "
                "motif hits"
            )
        state: MotifState = "boundary_unavailable"
        reason = (
            "The admitted +/-100-nt context crosses a contig boundary and is not "
            "analyzable under the Step 10 motif policy."
        )
    elif context_status == "available":
        state = "present" if hits else "no_registered_hit"
        reason = None
    else:
        _fail(f"Unsupported Step 10 context_status: {context_status!r}")
    return CandidateMotifEvidence(
        state=state,
        context_status=context_status,
        orientation_action=context_row["orientation_action"],
        window_start_1based=_required_integer(
            "Step 10 window_start_1based", context_row["window_start_1based"]
        ),
        window_end_1based=_required_integer(
            "Step 10 window_end_1based", context_row["window_end_1based"]
        ),
        edit_offset_0based=_required_integer(
            "Step 10 edit_offset_0based", context_row["edit_offset_0based"]
        ),
        oriented_sequence=context_row["oriented_sequence"],
        hits=hits,
        unavailable_reason=reason,
        **common,
    )


def _candidate(
    rank: int,
    row: Mapping[str, str],
    results: ComputationalResults,
    *,
    context_row: Mapping[str, str] | None,
    hits: tuple[CandidateMotifHit, ...],
    context_unavailable_reason: str | None,
) -> SelectedCandidate:
    candidate_id = row["candidate_id"]
    return SelectedCandidate(
        display_rank=rank,
        candidate_id=candidate_id,
        call_status=row["call_status"],
        mean_analysis_dp=_decimal(
            f"candidate {candidate_id!r} mean_analysis_dp", row["mean_analysis_dp"]
        ),
        mean_control_af=_decimal(
            f"candidate {candidate_id!r} mean_control_af", row["mean_control_af"]
        ),
        mean_treatment_af=_decimal(
            f"candidate {candidate_id!r} mean_treatment_af",
            row["mean_treatment_af"],
        ),
        treatment_control_difference=_decimal(
            f"candidate {candidate_id!r} treatment_control_difference",
            row["treatment_control_difference"],
        ),
        cmh_fdr_bh=_decimal(
            f"candidate {candidate_id!r} cmh_fdr_bh", row["cmh_fdr_bh"]
        ),
        common_odds_ratio=_decimal(
            f"candidate {candidate_id!r} common_odds_ratio",
            row["common_odds_ratio"],
        ),
        location=_location(row),
        pairs=_pairs(row, results),
        motif=_motif_evidence(context_row, hits, context_unavailable_reason),
    )


def build_candidate_display(
    computational_results: ComputationalResults,
    scientific_context_results: ScientificContextResults | None = None,
    scientific_context_unavailable_reason: str | None = None,
) -> SelectedCandidateProjection:
    """Build the sole selected-candidate presentation projection.

    The function reads only already admitted Step 09/10 TSVs under stable
    snapshot checks. It never opens a reference, scans a motif, selects an
    isoform, reruns a test, or changes an admitted Step 10 display rank.
    """

    if scientific_context_results is not None:
        if scientific_context_unavailable_reason is not None:
            _fail("Scientific-context results and an unavailable reason cannot coexist")
        if scientific_context_results.analysis_id != computational_results.analysis_id:
            _fail("Step 10 and Step 09 candidate-display analysis IDs differ")
        contexts = _selected_context_rows(scientific_context_results.candidate_context)
        step09_rows, significant_count = _step09_rows_for_context(
            computational_results.significant_sites, contexts
        )
        for candidate_id, (_rank, context_row) in contexts.items():
            _validate_context_identity(step09_rows[candidate_id], context_row)
        hits = _selected_hits(scientific_context_results.motif_hits, contexts)
        candidates = tuple(
            _candidate(
                rank,
                step09_rows[candidate_id],
                computational_results,
                context_row=context_row,
                hits=hits[candidate_id],
                context_unavailable_reason=None,
            )
            for candidate_id, (rank, context_row) in sorted(
                contexts.items(), key=lambda item: item[1][0]
            )
        )
        selection_source: SelectionSource = "step10_display_rank"
    else:
        selected_rows, significant_count = _fallback_rows(
            computational_results.significant_sites
        )
        candidates = tuple(
            _candidate(
                rank,
                row,
                computational_results,
                context_row=None,
                hits=(),
                context_unavailable_reason=scientific_context_unavailable_reason,
            )
            for rank, row in enumerate(selected_rows, start=1)
        )
        selection_source = "step09_display_rule"

    return SelectedCandidateProjection(
        analysis_id=computational_results.analysis_id,
        control_condition=computational_results.sample_manifest.control_condition,
        treatment_condition=(computational_results.sample_manifest.treatment_condition),
        selection_source=selection_source,
        significant_candidate_count=significant_count,
        candidates=candidates,
    )


__all__ = (
    "CandidateLocation",
    "CandidateMotifEvidence",
    "CandidateMotifHit",
    "CandidatePairEvidence",
    "CandidateSampleEvidence",
    "MotifState",
    "SelectedCandidate",
    "SelectedCandidateProjection",
    "SelectionSource",
    "build_candidate_display",
)
