"""Real-R scientific-context producer and canonical-admission integration."""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest
from norad.contracts.scientific_evidence import scientific_context
from norad.libraries.process_environment import (
    guarded_r_environment,
    guarded_rscript_argv,
)
from tests import scientific_evidence_test_support as STEP_FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCER = (
    REPO_ROOT
    / "src/norad/analyses/scientific_context_projection/scientific_context_projection.sh"
)


def _test_environment() -> dict[str, str]:
    selected_library = os.environ.get("NORAD_RENV_LIBRARY")
    environment = (
        guarded_r_environment(
            REPO_ROOT,
            Path(selected_library),
            base_environment=os.environ,
        )
        if selected_library
        else os.environ.copy()
    )
    environment["NORAD_SHA256_PYTHON"] = sys.executable
    environment.setdefault("NORAD_LOCAL_PILOT_R", "0")
    environment.pop("NORAD_RUN_TOKEN", None)
    return environment


def _rscript(environment: Mapping[str, str]) -> str:
    guarded = environment.get("NORAD_LOCAL_PILOT_R") == "1"
    requested = os.environ.get("RSCRIPT_BIN_OVERRIDE", "Rscript")
    resolved = (
        str(Path(requested).resolve()) if "/" in requested else shutil.which(requested)
    )
    if not resolved or not os.access(resolved, os.X_OK):
        message = f"real scientific-context test requires Rscript: {requested}"
        if guarded:
            pytest.fail(message)
        pytest.skip(message)
    probe_arguments = (
        "-e",
        'required <- c("Biostrings", "GenomicRanges", "IRanges", '
        '"Rsamtools"); quit(status = if '
        "(all(vapply(required, requireNamespace, logical(1), quietly = TRUE))) "
        "0L else 1L)",
    )
    probe_command = (
        guarded_rscript_argv(resolved, probe_arguments)
        if guarded
        else [resolved, *probe_arguments]
    )
    package_check = subprocess.run(
        probe_command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=dict(environment),
    )
    if package_check.returncode != 0:
        if guarded:
            detail = " ".join(
                (package_check.stdout + " " + package_check.stderr).split()
            )
            pytest.fail(
                "guarded real-R package probe failed with exit "
                f"{package_check.returncode}"
                + (f": {detail}" if detail else "")
            )
        pytest.skip(
            "real scientific-context test requires the locked Bioconductor packages"
        )
    return resolved


def _read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def _write_tsv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=header,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _expanded_step09(
    root: Path,
) -> tuple[str, Path, Path, Path, Path, Path]:
    """Expand canonical Step 09 rows to exercise all available populations."""
    built = STEP_FIXTURE.build_fixture(root / "source")
    analysis_id = STEP_FIXTURE.PRIMARY_ANALYSIS_ID
    source_dir = built.step09_analysis_dir
    source_all = source_dir / f"{analysis_id}.cmh_all_sites.tsv"
    source_summary = source_dir / f"{analysis_id}.cmh_summary.tsv"
    header, source_rows = _read_tsv(source_all)
    _, summary_rows = _read_tsv(source_summary)
    by_status = {row["call_status"]: row for row in source_rows}

    rows: list[dict[str, str]] = []
    positions: dict[str, int] = {}
    population_specs = (
        ("significant_up", 10, "up"),
        ("effect_not_met", 20, "background"),
        ("significant_down", 10, "down"),
    )
    row_index = 0
    for call_status, count, label in population_specs:
        for index in range(count):
            row = dict(by_status[call_status])
            position = 201 + row_index * 220
            candidate_id = f"context_{label}_{index:02d}"
            row.update(
                partition_id="context",
                candidate_id=candidate_id,
                chromosome="context_contig",
                position=str(position),
            )
            rows.append(row)
            positions[candidate_id] = position
            row_index += 1

    summary = dict(summary_rows[0])
    summary.update(
        candidate_count="40",
        target_candidate_count="40",
        successfully_tested_count="40",
        not_target_change_count="0",
        missing_counts_count="0",
        low_coverage_count="0",
        degenerate_table_count="0",
        below_mean_dp_count="0",
        background_not_passed_count="0",
        fdr_not_met_count="0",
        effect_not_met_count="20",
        significant_up_count="10",
        significant_down_count="10",
    )
    step09_dir = root / "expanded"
    step09_dir.mkdir(parents=True)
    all_sites = step09_dir / f"{analysis_id}.cmh_all_sites.tsv"
    significant = step09_dir / f"{analysis_id}.cmh_significant_sites.tsv"
    summary_path = step09_dir / f"{analysis_id}.cmh_summary.tsv"
    _write_tsv(all_sites, header, rows)
    _write_tsv(
        significant,
        header,
        [
            row
            for row in rows
            if row["call_status"] in ("significant_up", "significant_down")
        ],
    )
    _write_tsv(summary_path, list(summary), [summary])

    contig_length = max(positions.values()) + 200
    sequence = ["A"] * contig_length
    for row in rows:
        position = positions[row["candidate_id"]]
        sequence[position - 1] = row["genomic_ref"]
        population_index = int(row["candidate_id"].rsplit("_", 1)[1])
        has_hit = (
            (row["call_status"] == "significant_up" and population_index < 5)
            or (row["call_status"] == "effect_not_met" and population_index < 2)
            or (row["call_status"] == "significant_down" and population_index < 1)
        )
        if has_hit:
            motif_start = (
                position - 10 if row["genomic_ref"] != row["rna_ref"] else position + 5
            )
            genomic_motif = (
                "TTTACA" if row["genomic_ref"] != row["rna_ref"] else "TGTACA"
            )
            sequence[motif_start - 1 : motif_start + 5] = genomic_motif
    reference_fasta = (root / "reference.fa").resolve()
    reference_fai = (root / "reference.fa.fai").resolve()
    header_text = ">context_contig\n"
    sequence_text = "".join(sequence) + "\n"
    reference_fasta.write_text(header_text + sequence_text, encoding="ascii")
    reference_fai.write_text(
        f"context_contig\t{contig_length}\t{len(header_text)}\t"
        f"{contig_length}\t{contig_length + 1}\n",
        encoding="ascii",
    )
    return (
        analysis_id,
        all_sites,
        significant,
        summary_path,
        reference_fasta,
        reference_fai,
    )


def _run_projection(
    output_root: Path,
    inputs: tuple[str, Path, Path, Path, Path, Path],
    rscript: str,
    environment: Mapping[str, str],
) -> Path:
    analysis_id, all_sites, significant, summary, reference, fai = inputs
    subprocess.run(
        [
            str(PRODUCER),
            "--analysis-id",
            analysis_id,
            "--step09-all-sites",
            str(all_sites),
            "--step09-significant-sites",
            str(significant),
            "--step09-summary",
            str(summary),
            "--reference-fasta",
            str(reference),
            "--reference-fai",
            str(fai),
            "--output-root",
            str(output_root),
            "--rscript-bin",
            rscript,
            "--no-clobber",
            "--execute",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=dict(environment),
    )
    return output_root / analysis_id


def test_real_r_projection_is_canonically_admitted_and_deterministic(
    tmp_path: Path,
) -> None:
    environment = _test_environment()
    if os.environ.get("NORAD_RENV_LIBRARY"):
        assert environment["NORAD_LOCAL_PILOT_R"] == "1"
        assert environment["R_DEFAULT_PACKAGES"] == "NULL"
    rscript = _rscript(environment)
    inputs = _expanded_step09(tmp_path / "inputs")
    first_dir = _run_projection(tmp_path / "first", inputs, rscript, environment)
    second_dir = _run_projection(tmp_path / "second", inputs, rscript, environment)
    analysis_id = inputs[0]

    first = scientific_context.validate_scientific_context_transaction(
        first_dir / f"{analysis_id}.context_receipt.tsv"
    )
    second = scientific_context.validate_scientific_context_transaction(
        second_dir / f"{analysis_id}.context_receipt.tsv"
    )
    assert (
        first.outputs.candidate_context.row_count,
        first.outputs.motif_hits.row_count,
        first.outputs.sequence_logo.row_count,
        first.outputs.motif_statistics.row_count,
    ) == (40, 8, 252, 61)
    assert (
        second.outputs.candidate_context.row_count,
        second.outputs.motif_hits.row_count,
        second.outputs.sequence_logo.row_count,
        second.outputs.motif_statistics.row_count,
    ) == (40, 8, 252, 61)
    _, motif_hits = _read_tsv(first.outputs.motif_hits.path)
    reverse_hit = next(
        row for row in motif_hits if row["candidate_id"] == "context_up_00"
    )
    assert (
        reverse_hit["matched_sequence"],
        reverse_hit["start_offset"],
        reverse_hit["end_offset"],
        reverse_hit["midpoint_offset"],
    ) == ("TGTAAA", "5", "10", "7.5")
    for suffix in (
        "candidate_context.tsv",
        "motif_hits.tsv",
        "sequence_logo.tsv",
        "motif_statistics.tsv",
    ):
        assert (first_dir / f"{analysis_id}.{suffix}").read_bytes() == (
            second_dir / f"{analysis_id}.{suffix}"
        ).read_bytes()
    assert not [path for path in first_dir.iterdir() if path.name.startswith(".")]
    assert not [path for path in second_dir.iterdir() if path.name.startswith(".")]


def test_real_r_projection_enforces_canonical_fai_lexemes_and_dimensions(
    tmp_path: Path,
) -> None:
    environment = _test_environment()
    rscript = _rscript(environment)
    inputs = _expanded_step09(tmp_path / "inputs")
    fields = inputs[-1].read_text(encoding="ascii").rstrip("\n").split("\t")
    assert len(fields) == 5
    malformed = {
        "field_count": (fields + ["extra"], "exactly five fields"),
        "whitespace": ([f" {fields[0]}", *fields[1:]], "surrounding whitespace"),
        "leading_zero": (
            [fields[0], f"0{fields[1]}", *fields[2:]],
            "canonical non-negative decimal text",
        ),
        "negative_offset": (
            [fields[0], fields[1], "-1", *fields[3:]],
            "canonical non-negative decimal text",
        ),
        "nonfinite_offset": (
            [fields[0], fields[1], "9" * 400, *fields[3:]],
            "numeric fields must be finite",
        ),
        "zero_dimensions": (
            [fields[0], "0", fields[2], "0", fields[4]],
            "invalid dimensions",
        ),
        "narrow_line": (
            [*fields[:4], str(int(fields[3]) - 1)],
            "invalid dimensions",
        ),
    }
    analysis_id = inputs[0]
    for case, (bad_fields, expected) in malformed.items():
        bad_fai = tmp_path / f"{case}.fa.fai"
        bad_fai.write_text("\t".join(bad_fields) + "\n", encoding="ascii")
        output_root = tmp_path / f"output-{case}"
        with pytest.raises(subprocess.CalledProcessError) as failure:
            _run_projection(
                output_root,
                (*inputs[:-1], bad_fai),
                rscript,
                environment,
            )
        assert expected in failure.value.stderr
        assert not (
            output_root / analysis_id / f"{analysis_id}.context_receipt.tsv"
        ).exists()

    large_offset_fai = tmp_path / "large-offset.fa.fai"
    large_offset_fai.write_text(
        "\t".join(["other_contig", fields[1], "5000000000", *fields[3:]]) + "\n",
        encoding="ascii",
    )
    with pytest.raises(subprocess.CalledProcessError) as accepted_large_offset:
        _run_projection(
            tmp_path / "output-large-offset",
            (*inputs[:-1], large_offset_fai),
            rscript,
            environment,
        )
    assert "Candidate chromosome is absent from the exact reference FAI" in (
        accepted_large_offset.value.stderr
    )
