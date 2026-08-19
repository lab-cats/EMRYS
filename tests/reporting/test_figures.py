"""Focused boundaries for the private scientific-figure renderer."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from norad.reporting._run_report import figures
from norad.reporting._run_report import scientific_context_figures as context_figures
from norad.reporting._run_report.inputs import _snapshot_regular
from norad.reporting._run_report.models import (
    SCIENTIFIC_FIGURE_IDS,
    ComputationalResults,
    ComputationalSampleManifest,
    ComputationalTable,
    ReportRenderError,
    SamplePair,
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
from norad.reporting._run_report.figures import _matplotlib_api, _render_svg

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
    assert "reporting performs no motif scan" in first[1].caption.lower()
    assert "BH as not applicable" in first[1].caption


def test_selected_context_tracks_use_only_upstream_ranks_and_paired_af(
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
    context_results = ScientificContextResults(
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
    significant_path = tmp_path / "significant.tsv"
    with significant_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(("candidate_id", "AF__control", "AF__treatment"))
        for index in range(8):
            writer.writerow(
                (f"significant_up_{index:02d}", f"0.{index + 1}", f"0.{index + 2}")
            )
    significant = computational_table(significant_path)
    manifest_path = tmp_path / "samples.tsv"
    manifest_path.write_text("synthetic manifest\n", encoding="utf-8")
    manifest_snapshot = _snapshot_regular(manifest_path, "sample manifest fixture")
    manifest = ComputationalSampleManifest(
        role="sample_manifest",
        path=manifest_path,
        sha256=manifest_snapshot.sha256,
        size_bytes=manifest_snapshot.size_bytes,
        sample_ids=("control", "treatment"),
        control_condition="control",
        treatment_condition="treatment",
        pairs=(SamplePair("R1", "control", "treatment"),),
        snapshot=manifest_snapshot,
    )
    computational = ComputationalResults(
        analysis_id="analysis",
        sample_ids=("control", "treatment"),
        validation=significant,
        all_sites=significant,
        significant_sites=significant,
        summary=significant,
        mutation_spectrum=significant,
        sample_manifest=manifest,
    )

    rendered = context_figures._selected_context_track_figure(
        context_results, computational
    )

    assert rendered.status == "available"
    assert rendered.population.startswith("Exactly 8 candidates with upstream")
    assert "no report-side selection or reranking" in rendered.population
    assert rendered.svg_size_bytes is not None and rendered.svg_size_bytes < 4_000_000


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


def test_selected_profiles_use_the_fixed_top_eight_display_rule(
    tmp_path: Path,
) -> None:
    path = tmp_path / "significant.tsv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(("candidate_id", "cmh_fdr_bh", "treatment_control_difference"))
        rows = (
            ("tie-z", "0.01", "0.2"),
            ("tie-a", "0.01", "-0.2"),
            ("larger-effect", "0.01", "0.4"),
            *(
                (f"candidate-{index}", str(0.02 + index / 100), "0.1")
                for index in range(8)
            ),
        )
        writer.writerows(rows)

    selected = figures._selected_profiles(computational_table(path))

    assert len(selected) == figures._PROFILE_DISPLAY_LIMIT
    assert [profile.row["candidate_id"] for profile in selected[:3]] == [
        "larger-effect",
        "tie-a",
        "tie-z",
    ]
    assert "candidate-7" not in {profile.row["candidate_id"] for profile in selected}


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
    assert counts == (1, 1, 0, 2, 1)
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
