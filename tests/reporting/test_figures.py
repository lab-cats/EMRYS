"""Focused boundaries for the private scientific-figure renderer."""

from __future__ import annotations

import base64
import csv
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from emrys.reporting.paired_cmh_candidate_ranking_report import figures
from emrys.reporting.paired_cmh_candidate_ranking_report import (
    scientific_context_figures as context_figures,
)
from emrys.reporting.paired_cmh_candidate_ranking_report.candidate_display import (
    CandidateLocation,
    CandidateMotifEvidence,
    CandidateMotifHit,
    CandidatePairEvidence,
    CandidateSampleEvidence,
    MotifState,
    SelectedCandidate,
    SelectedCandidateProjection,
)
from emrys.reporting._run_report.inputs import _snapshot_regular
from emrys.reporting._run_report.models import ReportRenderError
from emrys.reporting.paired_cmh_candidate_ranking_report.computational import (
    ComputationalTable,
)
from emrys.reporting.paired_cmh_candidate_ranking_report.figure_models import (
    SCIENTIFIC_FIGURE_IDS,
    ScientificFigurePanel,
)
from emrys.reporting.paired_cmh_candidate_ranking_report.scientific_context import (
    ScientificContextResults,
)
from tests import scientific_context_test_support as CONTEXT_FIXTURE


def computational_table(
    path: Path, *, role: str = "significant_sites"
) -> ComputationalTable:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        rows = list(reader)
    snapshot = _snapshot_regular(path, "scientific figure fixture")
    return ComputationalTable(
        role=role,
        table_id=f"computational_{role}",
        artifact_id=f"analysis.synthetic.{role}",
        title=role,
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=len(rows) - 1,
        display_row_limit=250,
        header=tuple(rows[0]),
        display_rows=(),
        snapshot=snapshot,
    )


def context_table(path: Path, role: str, *, materialize: bool) -> ComputationalTable:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        rows = list(reader)
    snapshot = _snapshot_regular(path, "scientific-context figure fixture")
    return ComputationalTable(
        role=role,
        table_id=f"scientific_context_{role}",
        artifact_id=f"analysis.synthetic.{role}",
        title=role,
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=len(rows) - 1,
        display_row_limit=len(rows) - 1 if materialize else 0,
        header=tuple(rows[0]),
        display_rows=tuple(tuple(row) for row in rows[1:]) if materialize else (),
        snapshot=snapshot,
    )


def selected_candidate(
    rank: int,
    candidate_id: str,
    *,
    motif_state: MotifState = "present",
    hit_offset: int = 5,
) -> SelectedCandidate:
    sequence = list("A" * 201)
    if motif_state == "present":
        sequence[100 + hit_offset : 106 + hit_offset] = "TGTACA"
    hits = (
        (
            CandidateMotifHit(
                motif_id="PUM_UGUANA",
                matched_sequence="TGTACA",
                start_offset=hit_offset,
                end_offset=hit_offset + 5,
                midpoint_offset=Decimal(str(hit_offset + 2.5)),
                bin_start=hit_offset,
                bin_end=hit_offset + 10,
            ),
        )
        if motif_state == "present"
        else ()
    )
    context_available = motif_state != "step10_unavailable"
    return SelectedCandidate(
        display_rank=rank,
        candidate_id=candidate_id,
        call_status="significant_up",
        mean_analysis_dp=Decimal("72.5"),
        mean_control_af=Decimal("0.125"),
        mean_treatment_af=Decimal("0.375"),
        treatment_control_difference=Decimal("0.25"),
        cmh_fdr_bh=Decimal("0.004"),
        common_odds_ratio=Decimal("2.4"),
        location=CandidateLocation(
            chromosome="1",
            position_1based=101,
            genomic_ref="A",
            genomic_alt="G",
            rna_ref="A",
            rna_alt="G",
            workflow_orientation="FWD_like",
            orientation_policy="legacy_reverse_stranded_v1",
            annotation_strand="+",
            gene_ids=("GENE1",),
            transcript_ids=("TX1", "TX2"),
            region_memberships=("3' UTR", "exon"),
        ),
        pairs=(
            CandidatePairEvidence(
                replicate="R1",
                control=CandidateSampleEvidence(
                    sample_id="control",
                    allele_fraction=Decimal("0.10"),
                    alternate_depth=10,
                    total_depth=100,
                ),
                treatment=CandidateSampleEvidence(
                    sample_id="treatment",
                    allele_fraction=Decimal("0.40"),
                    alternate_depth=40,
                    total_depth=100,
                ),
            ),
        ),
        motif=CandidateMotifEvidence(
            state=motif_state,
            motif_id="PUM_UGUANA",
            rna_consensus="UGUANA",
            dna_consensus="TGTANA",
            context_radius=100,
            match_policy="exact_iupac_presented_strand_v1",
            context_status="available" if context_available else None,
            orientation_action="identity" if context_available else None,
            window_start_1based=1 if context_available else None,
            window_end_1based=201 if context_available else None,
            edit_offset_0based=100 if context_available else None,
            oriented_sequence="".join(sequence) if context_available else None,
            hits=hits,
            unavailable_reason=(
                "The complete admitted Step 10 context is unavailable."
                if motif_state == "step10_unavailable"
                else None
            ),
        ),
    )


def candidate_projection(
    candidates: tuple[SelectedCandidate, ...],
    *,
    significant_count: int | None = None,
) -> SelectedCandidateProjection:
    return SelectedCandidateProjection(
        analysis_id="analysis",
        control_condition="control",
        treatment_condition="treatment",
        selection_source="step10_display_rank",
        significant_candidate_count=(
            len(candidates) if significant_count is None else significant_count
        ),
        candidates=candidates,
    )


def test_unavailable_roster_needs_no_matplotlib_import() -> None:
    imported_before = {name for name in sys.modules if name.startswith("matplotlib")}
    rendered = figures.build_scientific_figures(None, "missing Step 09 bundle")

    assert tuple(figure.figure_id for figure in rendered) == SCIENTIFIC_FIGURE_IDS
    assert all(figure.status == "unavailable" for figure in rendered)
    assert all(figure.data_uri is None for figure in rendered)
    assert {
        name for name in sys.modules if name.startswith("matplotlib")
    } == imported_before


def test_matplotlib_bootstrap_is_clean_and_deterministic_across_processes(
    tmp_path: Path,
) -> None:
    script = """
import json
import os
from emrys.reporting.paired_cmh_candidate_ranking_report.figures import (
    _matplotlib_api,
    _render_svg,
)

keys = ("MPLBACKEND", "MPLCONFIGDIR", "MPL_IGNORE_SYSTEM_FONTS")
before = {key: os.environ.get(key) for key in keys}
matplotlib, _figure, _canvas = _matplotlib_api()
_svg, digest, size = _render_svg(
    "cache-probe",
    lambda figure: figure.add_subplot(1, 1, 1).plot([0, 1], [0, 1]),
)
after = {key: os.environ.get(key) for key in keys}
print(json.dumps({
    "after": after,
    "before": before,
    "digest": digest,
    "size": size,
    "version": matplotlib.__version__,
    "logomaker_loaded": "logomaker" in __import__("sys").modules,
}, sort_keys=True))
"""
    probes: list[dict[str, object]] = []
    for index in range(2):
        root = tmp_path / f"process-{index}"
        home = root / "home"
        cache = root / "cache"
        temporary = root / "temporary"
        for directory in (home, cache, temporary):
            directory.mkdir(parents=True, exist_ok=True)
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home),
                "TMPDIR": str(temporary),
                "XDG_CACHE_HOME": str(cache),
            }
        )
        result = subprocess.run(
            [
                sys.executable,
                "-X",
                "pycache_prefix=/dev/null",
                "-I",
                "-c",
                script,
            ],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        probe = json.loads(result.stdout)
        assert probe["version"] == "3.11.1"
        assert probe["logomaker_loaded"] is True
        assert (
            probe["before"]
            == probe["after"]
            == {
                "MPLBACKEND": None,
                "MPLCONFIGDIR": None,
                "MPL_IGNORE_SYSTEM_FONTS": None,
            }
        )
        assert not tuple(home.rglob("*"))
        assert not tuple(cache.rglob("*"))
        assert not tuple(temporary.rglob("*"))
        probes.append(probe)

    assert probes[0]["digest"] == probes[1]["digest"]
    assert probes[0]["size"] == probes[1]["size"]


def test_available_step10_logos_and_enrichment_are_deterministic(
    tmp_path: Path,
) -> None:
    paths = CONTEXT_FIXTURE.build_outputs(tmp_path / "context")
    candidate = context_table(
        paths["candidate_context"], "candidate_context", materialize=False
    )
    hits = context_table(paths["motif_hits"], "motif_hits", materialize=False)
    logo = context_table(paths["sequence_logo"], "sequence_logo", materialize=True)
    statistics = context_table(
        paths["motif_statistics"], "motif_statistics", materialize=True
    )
    results = ScientificContextResults(
        analysis_id="analysis",
        validation=candidate,
        candidate_context=candidate,
        motif_hits=hits,
        sequence_logo=logo,
        motif_statistics=statistics,
        receipt=candidate,
        bound_inputs=(),
        receipt_metadata={},
    )

    first = context_figures.build_scientific_context_figures(
        results, None, None, "Step 09 sample values unavailable"
    )
    second = context_figures.build_scientific_context_figures(
        results, None, None, "Step 09 sample values unavailable"
    )

    assert tuple(figure.status for figure in first) == (
        "available",
        "available",
        "unavailable",
    )
    assert first[0].svg_sha256 == second[0].svg_sha256
    assert first[1].svg_sha256 == second[1].svg_sha256
    assert "not de novo motif discovery" in first[0].text_summary.lower()
    assert "reporting performs no motif scan" in first[1].caption.lower()
    assert "BH as not applicable" in first[1].caption
    assert "100*admitted nearest-hit" in first[1].mapping


def test_scientific_figure_assets_bind_shape_hash_size_and_unique_panel_ids(
    tmp_path: Path,
) -> None:
    paths = CONTEXT_FIXTURE.build_outputs(tmp_path / "context")
    logo = context_table(paths["sequence_logo"], "sequence_logo", materialize=True)
    rendered = context_figures._sequence_context_logo_figure(
        ScientificContextResults(
            analysis_id="analysis",
            validation=logo,
            candidate_context=logo,
            motif_hits=logo,
            sequence_logo=logo,
            motif_statistics=logo,
            receipt=logo,
            bound_inputs=(),
            receipt_metadata={},
        )
    )
    rendered.validate()
    assert rendered.svg_size_bytes is not None
    with pytest.raises(ReportRenderError, match="byte size"):
        replace(rendered, svg_size_bytes=rendered.svg_size_bytes + 1).validate()

    asset = rendered.assets[0]
    mixed = replace(
        rendered,
        panels=(
            ScientificFigurePanel(
                panel_id="mixed-panel",
                data_uri=asset.data_uri,
                alt_text=asset.alt_text,
                svg_sha256=asset.svg_sha256,
                svg_size_bytes=asset.svg_size_bytes,
            ),
        ),
    )
    with pytest.raises(ReportRenderError, match="mixes legacy and panel"):
        mixed.validate()

    duplicated = replace(
        rendered,
        data_uri=None,
        svg_sha256=None,
        svg_size_bytes=None,
        panels=(asset, asset),
    )
    with pytest.raises(ReportRenderError, match="repeats a panel ID"):
        duplicated.validate()


def test_position_profiles_use_each_populations_analyzable_denominator() -> None:
    rows = (
        {
            "bin_start": "-10",
            "bin_end": "0",
            "analyzable_candidate_count": "20",
            "candidate_with_motif_count": "2",
        },
        {
            "bin_start": "0",
            "bin_end": "10",
            "analyzable_candidate_count": "20",
            "candidate_with_motif_count": "3",
        },
    )

    midpoints, percentages, analyzable, with_hit = (
        context_figures._position_profile_percentages(rows)
    )

    assert midpoints == (-5.0, 5.0)
    assert percentages == (10.0, 15.0)
    assert analyzable == 20
    assert with_hit == 5


def test_selected_context_panels_use_shared_order_and_list_out_of_slice_hits() -> None:
    candidates = tuple(
        selected_candidate(
            index,
            f"significant_up_{index:02d}",
            hit_offset=45 if index == 1 else 5,
        )
        for index in range(1, 9)
    )
    projection = candidate_projection(candidates, significant_count=12)

    first = context_figures._selected_context_track_figure(projection)
    second = context_figures._selected_context_track_figure(projection)

    assert first.status == "available"
    assert first.data_uri is first.svg_sha256 is first.svg_size_bytes is None
    assert len(first.panels) == 8
    assert tuple(panel.panel_id for panel in first.panels) == tuple(
        f"selected-context-track-figure-candidate-{index:02d}-panel"
        for index in range(1, 9)
    )
    assert tuple(panel.svg_sha256 for panel in first.panels) == tuple(
        panel.svg_sha256 for panel in second.panels
    )
    assert "+45..+50" in first.panels[0].alt_text
    assert "orientation policy legacy_reverse_stranded_v1" in first.panels[0].alt_text
    assert "12 significant candidates" in first.population
    assert "no figure-side selection or reranking" in first.population
    assert "Figure 2 performs no selection or reranking" in first.caption
    assert all(panel.svg_size_bytes < 4_000_000 for panel in first.panels)


def test_many_manifest_pairs_use_bounded_visual_notes() -> None:
    pairs = tuple(
        CandidatePairEvidence(
            replicate=f"R{index}",
            control=CandidateSampleEvidence(
                sample_id=f"control_{index}",
                allele_fraction=Decimal("0.10"),
                alternate_depth=10,
                total_depth=100,
            ),
            treatment=CandidateSampleEvidence(
                sample_id=f"treatment_{index}",
                allele_fraction=Decimal("0.40"),
                alternate_depth=40,
                total_depth=100,
            ),
        )
        for index in range(1, 9)
    )
    candidate = replace(selected_candidate(1, "many-pairs"), pairs=pairs)
    projection = replace(
        candidate_projection((candidate,)),
        control_condition="control-" + "c" * 80,
        treatment_condition="treatment-" + "t" * 80,
    )

    context_figure = context_figures._selected_context_track_figure(projection)
    profile_figure = figures._paired_sample_profile_figure(projection)
    context_svg = base64.b64decode(context_figure.panels[0].data_uri.partition(",")[2])
    assert profile_figure.data_uri is not None
    profile_svg = base64.b64decode(profile_figure.data_uri.partition(",")[2])

    assert b"8 manifest pairs; exact values below" in context_svg
    assert b"8 manifest pairs; exact values in candidate records" in profile_svg
    assert projection.control_condition.encode() not in context_svg
    assert projection.control_condition.encode() not in profile_svg


def test_selected_context_panel_keeps_step10_unavailable_distinct() -> None:
    projection = candidate_projection(
        (selected_candidate(1, "fallback", motif_state="step10_unavailable"),)
    )

    rendered = context_figures._selected_context_track_figure(projection)

    assert rendered.status == "available"
    assert "fallback=step10_unavailable" in rendered.alt_text
    assert "Registered motif evidence was not admitted" in rendered.panels[0].alt_text
    assert "state step10_unavailable" in rendered.panels[0].alt_text
    assert "Registered motif UGUANA" not in rendered.panels[0].alt_text


def test_selected_context_panel_bounds_long_labels_and_boundary_text() -> None:
    candidate = selected_candidate(
        1,
        "candidate-" + "x" * 180,
        motif_state="boundary_unavailable",
    )
    candidate = replace(
        candidate,
        location=replace(
            candidate.location,
            chromosome="contig-" + "y" * 120,
            gene_ids=("gene-" + "z" * 120,),
        ),
        motif=replace(
            candidate.motif,
            motif_id="motif-" + "m" * 120,
            context_status="boundary-" + "s" * 120,
            orientation_action="orientation-" + "a" * 120,
        ),
    )
    projection = replace(
        candidate_projection((candidate,)),
        control_condition="control-" + "c" * 120,
        treatment_condition="treatment-" + "t" * 120,
    )

    lines = context_figures._motif_panel_lines(candidate)
    rendered = context_figures._selected_context_track_figure(projection)

    assert lines
    assert max(map(len, lines)) <= context_figures._MOTIF_PANEL_LINE_WIDTH
    assert (
        len(context_figures._panel_condition_label(projection.control_condition))
        <= context_figures._PANEL_CONDITION_LABEL_LIMIT
    )
    assert len(rendered.panels) == 1
    assert rendered.panels[0].svg_size_bytes < 4_000_000
    assert candidate.candidate_id in rendered.panels[0].alt_text


def test_candidate_grid_is_population_complete_and_size_bounded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "all_sites.tsv"
    header = (
        "test_status",
        "call_status",
        "mean_analysis_dp",
        "treatment_control_difference",
    )
    row_count = 20_000
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        statuses = ("effect_not_met", "significant_down", "significant_up")
        for index in range(row_count):
            writer.writerow(
                (
                    "tested",
                    statuses[index % len(statuses)],
                    str(1 + index % 2_000),
                    str(((index % 201) - 100) / 100),
                )
            )
    snapshot = _snapshot_regular(path, "large candidate fixture")
    table = ComputationalTable(
        role="all_sites",
        table_id="computational_all_sites",
        artifact_id="analysis.synthetic.cmh_all_sites",
        title="All candidates",
        path=path,
        sha256=snapshot.sha256,
        size_bytes=snapshot.size_bytes,
        row_count=row_count,
        display_row_limit=250,
        header=header,
        display_rows=(),
        snapshot=snapshot,
    )

    grid, observed, _limits = figures._candidate_grid(table)

    assert observed == row_count
    assert sum(sum(cells.values()) for cells in grid.values()) == row_count
    assert sum(len(cells) for cells in grid.values()) <= (
        3 * figures._LANDSCAPE_X_BINS * figures._LANDSCAPE_Y_BINS
    )


def test_exact_significant_overlays_preserve_admitted_coordinates(
    tmp_path: Path,
) -> None:
    path = tmp_path / "significant-overlays.tsv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(
            (
                "test_status",
                "call_status",
                "mean_analysis_dp",
                "treatment_control_difference",
            )
        )
        writer.writerows(
            (
                ("tested", "effect_not_met", "10", "0.01"),
                ("tested", "significant_up", "75.5", "0.125"),
                ("tested", "significant_down", "44", "-0.25"),
                ("low_coverage", "not_tested", "NA", "NA"),
            )
        )

    points = figures._exact_significant_points(
        computational_table(path, role="all_sites"),
        x_field="mean_analysis_dp",
        y_field="treatment_control_difference",
        x_positive=True,
    )

    assert points == {
        "significant_down": ((44.0, -0.25),),
        "significant_up": ((75.5, 0.125),),
    }


def test_condition_grid_is_population_complete_and_bounded(tmp_path: Path) -> None:
    path = tmp_path / "all-sites.tsv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(
            (
                "test_status",
                "call_status",
                "mean_control_af",
                "mean_treatment_af",
            )
        )
        for index in range(10_000):
            writer.writerow(
                (
                    "tested",
                    "significant_up" if index % 2 else "effect_not_met",
                    str((index % 101) / 100),
                    str(((index * 7) % 101) / 100),
                )
            )

    grid, observed = figures._condition_grid(
        computational_table(path, role="all_sites")
    )

    assert observed == 10_000
    assert sum(sum(cells.values()) for cells in grid.values()) == observed
    assert sum(len(cells) for cells in grid.values()) <= (
        3 * figures._CONCORDANCE_BINS * figures._CONCORDANCE_BINS
    )


def test_paired_profiles_preserve_the_shared_candidate_roster() -> None:
    projection = candidate_projection(
        (
            selected_candidate(1, "candidate-z"),
            selected_candidate(2, "candidate-a"),
        ),
        significant_count=9,
    )

    rendered = figures._paired_sample_profile_figure(projection)

    assert rendered.status == "available"
    assert "candidate-z, candidate-a" in rendered.caption
    assert "Shared ordered roster of 2 of 9" in rendered.population
    assert "100*AF__sample" in rendered.mapping


def test_maximum_paired_profile_roster_fits_the_print_height_bound() -> None:
    projection = candidate_projection(
        tuple(selected_candidate(index, f"candidate-{index}") for index in range(1, 9))
    )

    rendered = figures._paired_sample_profile_figure(projection)

    assert rendered.data_uri is not None
    svg = base64.b64decode(rendered.data_uri.partition(",")[2])
    root = ET.fromstring(svg)
    height_points = float(root.attrib["height"].removesuffix("pt"))
    assert height_points <= figures._PROFILE_MAX_HEIGHT_INCHES * 72


def test_location_memberships_remain_independent_and_nonexclusive(
    tmp_path: Path,
) -> None:
    path = tmp_path / "significant.tsv"
    header = tuple(field for field, _label in figures._LOCATION_FIELDS)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(
            (
                ("TRUE", "TRUE", "FALSE", "TRUE", "FALSE"),
                ("FALSE", "FALSE", "FALSE", "TRUE", "TRUE"),
                ("FALSE", "FALSE", "FALSE", "FALSE", "FALSE"),
            )
        )

    counts, population = figures._location_memberships(computational_table(path))

    assert population == 3
    assert counts == (1, 1, 0, 2, 1, 1)
    assert sum(counts) > population


@pytest.mark.parametrize(
    "payload",
    (
        b'<svg xmlns="http://www.w3.org/2000/svg"><script/></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg"><use href="https://example.org/x"/></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg"><style>@import url(https://example.org/x.css);</style></svg>',
        b'<svg xmlns="http://www.w3.org/2000/svg" xml:base="https://example.org/"/>',
    ),
)
def test_svg_validation_rejects_active_or_external_content(payload: bytes) -> None:
    with pytest.raises(ReportRenderError):
        figures._validated_svg(payload, "invalid-probe")
