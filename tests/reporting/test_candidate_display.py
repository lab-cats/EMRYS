"""Focused tests for the immutable selected-candidate projection."""

from __future__ import annotations

import csv
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path

import pytest

from norad.contracts.scientific_evidence import scientific_context, step09
from norad.reporting._run_report.candidate_display import build_candidate_display
from norad.reporting._run_report.inputs import _snapshot_regular
from norad.reporting._run_report.models import (
    ComputationalResults,
    ComputationalSampleManifest,
    ComputationalTable,
    ReportRenderError,
    SamplePair,
    ScientificContextResults,
)


SAMPLES = ("EV_1", "PUM1_1", "EV_2", "PUM1_2")
RESULT_HEADER = (
    *step09.STEP09_RESULT_HEADER,
    *(f"DP__{sample}" for sample in SAMPLES),
    *(f"AD__{sample}" for sample in SAMPLES),
    *(f"AF__{sample}" for sample in SAMPLES),
)


def _write_table(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
    *,
    role: str,
) -> ComputationalTable:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            delimiter="\t",
            lineterminator="\n",
            fieldnames=header,
        )
        writer.writeheader()
        writer.writerows(rows)
    snapshot = _snapshot_regular(path, f"{role} candidate-display fixture")
    return ComputationalTable(
        role=role,
        table_id=f"candidate_display_{role}",
        artifact_id=f"analysis.synthetic.{role}",
        title=role,
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=len(rows),
        display_row_limit=0,
        header=header,
        display_rows=(),
        snapshot=snapshot,
    )


def _result_row(
    candidate_id: str,
    *,
    chromosome: str,
    position: int,
    fdr: str,
    difference: str,
    call_status: str = "significant_up",
    genes: str = "GENE1;GENE2",
    transcripts: str = "TX1;TX2",
    regions: tuple[str, ...] = ("is_cds", "is_exon"),
) -> dict[str, str]:
    row = {column: "NA" for column in RESULT_HEADER}
    row.update(
        {
            "analysis_id": "analysis",
            "partition_id": "p1",
            "candidate_id": candidate_id,
            "orientation": "FWD_like",
            "chromosome": chromosome,
            "position": str(position),
            "alt_index": "1",
            "genomic_ref": "T",
            "genomic_alt": "C",
            "rna_ref": "A",
            "rna_alt": "G",
            "annotation_strand": "+",
            "gene_ids": genes,
            "transcript_ids": transcripts,
            "qual": "60",
            "filter": "PASS",
            "info_alt_depth": "90",
            "orientation_policy": "legacy_provisional_v1",
            "control_condition": "EV",
            "treatment_condition": "PUM1",
            "target_rna_change": "A>G",
            "replicate_count": "2",
            "test_status": "tested",
            "call_status": call_status,
            "background_condition": "NA",
            "background_status": "disabled",
            "min_analysis_dp": "80",
            "mean_analysis_dp": "95.5",
            "mean_control_af": "0.115",
            "mean_treatment_af": "0.315",
            "treatment_control_difference": difference,
            "max_background_af": "NA",
            "cmh_statistic": "12",
            "cmh_degrees_freedom": "1",
            "cmh_p_value": "0.0005",
            "cmh_fdr_bh": fdr,
            "common_odds_ratio": "3.5",
            "DP__EV_1": "100",
            "AD__EV_1": "10",
            "AF__EV_1": "0.1",
            "DP__PUM1_1": "100",
            "AD__PUM1_1": "30",
            "AF__PUM1_1": "0.3",
            "DP__EV_2": "80",
            "AD__EV_2": "10",
            "AF__EV_2": "0.125",
            "DP__PUM1_2": "100",
            "AD__PUM1_2": "33",
            "AF__PUM1_2": "0.33",
        }
    )
    for field in (
        "is_cds",
        "is_five_prime_utr",
        "is_three_prime_utr",
        "is_exon",
        "is_intron",
    ):
        row[field] = str(field in regions).upper()
    return row


def _context_row(
    step09_row: dict[str, str],
    *,
    rank: int,
    context_status: str,
) -> dict[str, str]:
    if context_status == "available":
        start, end, offset, sequence = 1, 201, 100, "A" * 201
    else:
        start, end, offset, sequence = 1, 151, 49, "A" * 151
    return {
        "analysis_id": step09_row["analysis_id"],
        "candidate_id": step09_row["candidate_id"],
        "population": step09_row["call_status"],
        "display_rank": str(rank),
        "chromosome": step09_row["chromosome"],
        "position": step09_row["position"],
        "contig_length": "1000",
        "genomic_ref": step09_row["genomic_ref"],
        "genomic_alt": step09_row["genomic_alt"],
        "rna_ref": step09_row["rna_ref"],
        "rna_alt": step09_row["rna_alt"],
        "orientation_action": "reverse_complement",
        "window_start_1based": str(start),
        "window_end_1based": str(end),
        "edit_offset_0based": str(offset),
        "context_status": context_status,
        "oriented_sequence": sequence,
    }


def _hit_row(context_row: dict[str, str]) -> dict[str, str]:
    return {
        "analysis_id": context_row["analysis_id"],
        "candidate_id": context_row["candidate_id"],
        "population": context_row["population"],
        "motif_id": scientific_context.MOTIF_ID,
        "matched_sequence": "TGTAAA",
        "start_offset": "-5",
        "end_offset": "0",
        "midpoint_offset": "-2.5",
        "bin_start": "-10",
        "bin_end": "0",
    }


def _computational_results(
    tmp_path: Path,
    rows: list[dict[str, str]],
) -> ComputationalResults:
    significant = _write_table(
        tmp_path / "significant.tsv",
        RESULT_HEADER,
        rows,
        role="significant_sites",
    )
    manifest_path = tmp_path / "samples.tsv"
    manifest_path.write_text("fixture\n", encoding="utf-8")
    manifest_snapshot = _snapshot_regular(
        manifest_path, "candidate-display sample manifest"
    )
    manifest = ComputationalSampleManifest(
        role="sample_manifest",
        path=manifest_path,
        sha256=manifest_snapshot.sha256,
        size_bytes=manifest_snapshot.size_bytes,
        sample_ids=SAMPLES,
        control_condition="EV",
        treatment_condition="PUM1",
        pairs=(
            SamplePair("1", "EV_1", "PUM1_1"),
            SamplePair("2", "EV_2", "PUM1_2"),
        ),
        snapshot=manifest_snapshot,
    )
    return ComputationalResults(
        analysis_id="analysis",
        sample_ids=SAMPLES,
        validation=significant,
        all_sites=significant,
        significant_sites=significant,
        summary=significant,
        mutation_spectrum=significant,
        sample_manifest=manifest,
    )


def _context_results(
    tmp_path: Path,
    context_rows: list[dict[str, str]],
    hit_rows: list[dict[str, str]],
) -> ScientificContextResults:
    context = _write_table(
        tmp_path / "candidate_context.tsv",
        scientific_context.CANDIDATE_CONTEXT_HEADER,
        context_rows,
        role="candidate_context",
    )
    hits = _write_table(
        tmp_path / "motif_hits.tsv",
        scientific_context.MOTIF_HITS_HEADER,
        hit_rows,
        role="motif_hits",
    )
    return ScientificContextResults(
        analysis_id="analysis",
        validation=context,
        candidate_context=context,
        motif_hits=hits,
        sequence_logo=context,
        motif_statistics=context,
        receipt=context,
        bound_inputs=(),
        receipt_metadata={},
    )


def _three_rows() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    present = _result_row(
        "FWD_like|1|100|T>C",
        chromosome="1",
        position=100,
        fdr="0.002",
        difference="0.20",
    )
    no_hit = _result_row(
        "FWD_like|2|200|T>C",
        chromosome="2",
        position=200,
        fdr="0.001",
        difference="0.10",
        genes="NA",
        transcripts="NA",
        regions=(),
    )
    boundary = _result_row(
        "FWD_like|3|50|T>C",
        chromosome="3",
        position=50,
        fdr="0.002",
        difference="-0.30",
        call_status="significant_down",
        regions=("is_three_prime_utr", "is_exon"),
    )
    return present, no_hit, boundary


def test_step10_rank_drives_one_joined_immutable_roster(tmp_path: Path) -> None:
    present, no_hit, boundary = _three_rows()
    computational = _computational_results(tmp_path, [no_hit, present, boundary])
    contexts = [
        _context_row(boundary, rank=1, context_status="boundary_truncated"),
        _context_row(present, rank=2, context_status="available"),
        _context_row(no_hit, rank=3, context_status="available"),
    ]
    context = _context_results(tmp_path, contexts, [_hit_row(contexts[1])])

    projection = build_candidate_display(computational, context)

    assert projection.selection_source == "step10_display_rank"
    assert projection.significant_candidate_count == 3
    assert tuple(candidate.candidate_id for candidate in projection.candidates) == (
        boundary["candidate_id"],
        present["candidate_id"],
        no_hit["candidate_id"],
    )
    candidate = projection.candidates[1]
    assert candidate.display_rank == 2
    assert candidate.mean_control_af == Decimal("0.115")
    assert candidate.mean_treatment_af == Decimal("0.315")
    assert candidate.treatment_control_difference == Decimal("0.20")
    assert candidate.mean_analysis_dp == Decimal("95.5")
    assert candidate.cmh_fdr_bh == Decimal("0.002")
    assert candidate.common_odds_ratio == Decimal("3.5")
    assert candidate.pairs[0].replicate == "1"
    assert candidate.pairs[0].control.allele_fraction == Decimal("0.1")
    assert candidate.pairs[0].control.alternate_depth == 10
    assert candidate.pairs[0].control.total_depth == 100
    assert candidate.pairs[1].treatment.allele_fraction == Decimal("0.33")
    assert candidate.location.position_1based == 100
    assert candidate.location.gene_ids == ("GENE1", "GENE2")
    assert candidate.location.transcript_ids == ("TX1", "TX2")
    assert candidate.location.region_memberships == ("CDS", "exon")
    with pytest.raises(FrozenInstanceError):
        candidate.display_rank = 99  # type: ignore[misc]


def test_all_four_motif_states_are_explicit_and_nonoverlapping(tmp_path: Path) -> None:
    present, no_hit, boundary = _three_rows()
    computational = _computational_results(tmp_path, [present, no_hit, boundary])
    contexts = [
        _context_row(present, rank=1, context_status="available"),
        _context_row(no_hit, rank=2, context_status="available"),
        _context_row(boundary, rank=3, context_status="boundary_truncated"),
    ]
    context = _context_results(tmp_path, contexts, [_hit_row(contexts[0])])

    projection = build_candidate_display(computational, context)
    motifs = tuple(candidate.motif for candidate in projection.candidates)

    assert tuple(motif.state for motif in motifs) == (
        "present",
        "no_registered_hit",
        "boundary_unavailable",
    )
    assert motifs[0].motif_id == "PUM_UGUANA"
    assert motifs[0].rna_consensus == "UGUANA"
    assert motifs[0].dna_consensus == "TGTANA"
    assert motifs[0].context_radius == 100
    assert motifs[0].hits[0].matched_sequence == "TGTAAA"
    assert motifs[0].hits[0].start_offset == -5
    assert motifs[0].hits[0].end_offset == 0
    assert motifs[0].hits[0].midpoint_offset == Decimal("-2.5")
    assert motifs[1].hits == () and motifs[1].unavailable_reason is None
    assert motifs[2].hits == ()
    assert motifs[2].unavailable_reason is not None

    historical = build_candidate_display(
        computational,
        scientific_context_unavailable_reason="Step 10 was not declared.",
    )
    assert all(
        candidate.motif.state == "step10_unavailable"
        for candidate in historical.candidates
    )
    assert all(
        candidate.motif.unavailable_reason == "Step 10 was not declared."
        for candidate in historical.candidates
    )
    assert all(
        (
            candidate.motif.motif_id,
            candidate.motif.rna_consensus,
            candidate.motif.dna_consensus,
            candidate.motif.context_radius,
            candidate.motif.match_policy,
        )
        == (None, None, None, None, None)
        for candidate in historical.candidates
    )


def test_historical_fallback_uses_bounded_fdr_effect_id_display_rule(
    tmp_path: Path,
) -> None:
    rows: list[dict[str, str]] = []
    for index in range(10):
        rows.append(
            _result_row(
                f"FWD_like|1|{100 + index}|T>C",
                chromosome="1",
                position=100 + index,
                fdr="0.001" if index in {8, 9} else f"0.00{index + 2}",
                difference="0.40" if index == 9 else "0.10",
            )
        )
    computational = _computational_results(tmp_path, list(reversed(rows)))

    projection = build_candidate_display(computational)

    assert projection.selection_source == "step09_display_rule"
    assert projection.significant_candidate_count == 10
    assert len(projection.candidates) == scientific_context.DISPLAY_LIMIT
    assert projection.candidates[0].candidate_id == rows[9]["candidate_id"]
    assert projection.candidates[1].candidate_id == rows[8]["candidate_id"]
    assert tuple(
        candidate.display_rank for candidate in projection.candidates
    ) == tuple(range(1, scientific_context.DISPLAY_LIMIT + 1))


def test_missing_sample_values_remain_explicitly_unavailable(tmp_path: Path) -> None:
    present, _no_hit, _boundary = _three_rows()
    present["DP__EV_1"] = "NA"
    present["AD__EV_1"] = "NA"
    present["AF__EV_1"] = "NA"
    computational = _computational_results(tmp_path, [present])

    projection = build_candidate_display(computational)

    control = projection.candidates[0].pairs[0].control
    assert control.allele_fraction is None
    assert control.alternate_depth is None
    assert control.total_depth is None


def test_step10_selected_identity_must_match_step09(tmp_path: Path) -> None:
    present, _no_hit, _boundary = _three_rows()
    computational = _computational_results(tmp_path, [present])
    context_row = _context_row(present, rank=1, context_status="available")
    context_row["chromosome"] = "other"
    context = _context_results(tmp_path, [context_row], [])

    with pytest.raises(ReportRenderError, match="differs from Step 09 field"):
        build_candidate_display(computational, context)


def test_candidate_projection_rechecks_admitted_snapshots(tmp_path: Path) -> None:
    present, _no_hit, _boundary = _three_rows()
    computational = _computational_results(tmp_path, [present])
    with computational.significant_sites.path.open("a", encoding="utf-8") as stream:
        stream.write("changed\n")

    with pytest.raises(ReportRenderError, match="changed during report rendering"):
        build_candidate_display(computational)


def test_present_context_and_unavailable_reason_cannot_coexist(tmp_path: Path) -> None:
    present, _no_hit, _boundary = _three_rows()
    computational = _computational_results(tmp_path, [present])
    context_row = _context_row(present, rank=1, context_status="available")
    context = _context_results(tmp_path, [context_row], [])

    with pytest.raises(ReportRenderError, match="cannot coexist"):
        build_candidate_display(computational, context, "not available")
