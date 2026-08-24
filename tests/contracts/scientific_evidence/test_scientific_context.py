"""Independent contract examples for the scientific-context transaction."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from emrys.contracts.scientific_evidence import scientific_context as CONTEXT
from emrys.contracts.scientific_evidence.step08 import sha256_file
from tests import scientific_context_test_support as FIXTURE
from tests import scientific_evidence_test_support as STEP_FIXTURE


def test_v1_headers_and_policy_literals_are_frozen() -> None:
    assert CONTEXT.CANDIDATE_CONTEXT_HEADER == tuple(
        "analysis_id candidate_id population display_rank chromosome position "
        "contig_length genomic_ref genomic_alt rna_ref rna_alt "
        "orientation_action window_start_1based window_end_1based "
        "edit_offset_0based context_status oriented_sequence".split()
    )
    assert CONTEXT.MOTIF_HITS_HEADER == tuple(
        "analysis_id candidate_id population motif_id matched_sequence "
        "start_offset end_offset midpoint_offset bin_start bin_end".split()
    )
    assert CONTEXT.SEQUENCE_LOGO_HEADER == tuple(
        "analysis_id population availability_status relative_position base "
        "candidate_count observed_base_count base_count base_fraction".split()
    )
    assert CONTEXT.MOTIF_STATISTICS_HEADER == tuple(
        "analysis_id motif_id population statistic_type availability_status "
        "bin_start bin_end eligible_candidate_count analyzable_candidate_count "
        "candidate_with_motif_count hit_count background_candidate_count "
        "background_with_motif_count odds_ratio odds_ratio_ci95_lower "
        "odds_ratio_ci95_upper fisher_p_value_two_sided fisher_p_value_bh".split()
    )
    assert CONTEXT.SCIENTIFIC_CONTEXT_RECEIPT_HEADER == tuple(
        "schema_name schema_version analysis_id step09_all_sites_path "
        "step09_all_sites_sha256 step09_significant_sites_path "
        "step09_significant_sites_sha256 step09_summary_path "
        "step09_summary_sha256 reference_fasta_path reference_fasta_sha256 "
        "reference_fai_path reference_fai_sha256 motif_catalog_path "
        "motif_catalog_sha256 scientific_context_schema_version "
        "context_orientation_policy context_radius logo_radius display_limit "
        "motif_match_policy motif_distance_policy motif_distance_bin_width "
        "foreground_population background_population separate_population "
        "foreground_minimum_count background_minimum_count "
        "separate_minimum_count enrichment_test enrichment_alternative "
        "multiple_testing_method candidate_context_path candidate_context_sha256 "
        "candidate_context_row_count motif_hits_path motif_hits_sha256 "
        "motif_hits_row_count sequence_logo_path sequence_logo_sha256 "
        "sequence_logo_row_count motif_statistics_path "
        "motif_statistics_sha256 motif_statistics_row_count "
        "published_output_count producer producer_version r_version "
        "biostrings_version rsamtools_version git_commit transaction_state".split()
    )
    assert CONTEXT.CONTEXT_ORIENTATION_POLICY == (
        "legacy_rna_change_oriented_genomic_v1"
    )
    assert CONTEXT.MOTIF_DNA_CONSENSUS == "TGTANA"
    assert CONTEXT.CONTEXT_RADIUS == 100
    assert CONTEXT.LOGO_RADIUS == 10


def test_v1_outputs_admit_exact_hits_logos_and_statistics(tmp_path: Path) -> None:
    paths = FIXTURE.build_outputs(tmp_path)

    outputs = CONTEXT.validate_scientific_context_outputs(
        paths["candidate_context"],
        paths["motif_hits"],
        paths["sequence_logo"],
        paths["motif_statistics"],
        "analysis",
    )

    assert outputs.candidate_context.row_count == 40
    assert outputs.motif_hits.row_count == 8
    assert outputs.sequence_logo.row_count == 252
    assert outputs.motif_statistics.row_count == 61


def test_v1_outputs_reject_motif_and_statistic_mutations(tmp_path: Path) -> None:
    paths = FIXTURE.build_outputs(tmp_path)
    FIXTURE.replace_cell(paths["motif_hits"], 0, "midpoint_offset", "9.5")
    with pytest.raises(CONTEXT.ContractError, match="every exact overlapping"):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )

    paths = FIXTURE.build_outputs(tmp_path / "statistics")
    FIXTURE.replace_cell(
        paths["motif_statistics"], 0, "fisher_p_value_two_sided", "0.5"
    )
    with pytest.raises(CONTEXT.ContractError, match="Fisher p-value"):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("odds_ratio", "1", "conditional odds ratio"),
        ("odds_ratio_ci95_lower", "0", "lower bound"),
        ("odds_ratio_ci95_upper", "10", "upper bound"),
    ),
)
def test_v1_outputs_reject_forged_fisher_effects(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    paths = FIXTURE.build_outputs(tmp_path)
    FIXTURE.replace_cell(paths["motif_statistics"], 0, field, value)

    with pytest.raises(CONTEXT.ContractError, match=message):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )


def test_v1_catalog_and_policy_are_literal(tmp_path: Path) -> None:
    catalog = tmp_path / "motifs.tsv"
    FIXTURE.write_tsv(
        catalog,
        CONTEXT.MOTIF_CATALOG_HEADER,
        [
            {
                "motif_id": "PUM_UGUANA",
                "rna_consensus": "UGUANA",
                "dna_consensus": "TGTANA",
            }
        ],
    )
    assert CONTEXT.validate_motif_catalog(catalog).rows[0]["dna_consensus"] == "TGTANA"

    FIXTURE.replace_cell(catalog, 0, "dna_consensus", "TGTAAA")
    with pytest.raises(CONTEXT.ContractError, match="exactly PUM"):
        CONTEXT.validate_motif_catalog(catalog)


def test_v1_receipt_rejects_a_stale_bound_output(tmp_path: Path) -> None:
    built = STEP_FIXTURE.build_fixture(tmp_path / "step09")
    analysis_id = STEP_FIXTURE.PRIMARY_ANALYSIS_ID
    transaction = FIXTURE.build_transaction(
        tmp_path / "context",
        analysis_id=analysis_id,
        step09_all_sites=(
            built.step09_analysis_dir / f"{analysis_id}.cmh_all_sites.tsv"
        ),
        step09_significant_sites=(
            built.step09_analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        step09_summary=built.step09_analysis_dir / f"{analysis_id}.cmh_summary.tsv",
    )

    admitted = CONTEXT.validate_scientific_context_transaction(transaction.receipt)
    assert admitted.outputs.candidate_context.row_count == 3

    FIXTURE.replace_cell(transaction.candidate_context, 0, "chromosome", "2")
    with pytest.raises(CONTEXT.ContractError, match="sha256 is stale"):
        CONTEXT.validate_scientific_context_transaction(transaction.receipt)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("contig", "absent from the bound FAI"),
        ("contig_length", "contig_length differs"),
        ("window", "window does not equal"),
        ("sequence", "oriented_sequence differs"),
        ("reference_center", "genomic_ref differs"),
    ),
)
def test_v1_receipt_rederives_context_from_bound_reference(
    tmp_path: Path,
    mutation: str,
    expected: str,
) -> None:
    built = STEP_FIXTURE.build_fixture(tmp_path / "step09")
    analysis_id = STEP_FIXTURE.PRIMARY_ANALYSIS_ID
    transaction = FIXTURE.build_transaction(
        tmp_path / "context",
        analysis_id=analysis_id,
        step09_all_sites=(
            built.step09_analysis_dir / f"{analysis_id}.cmh_all_sites.tsv"
        ),
        step09_significant_sites=(
            built.step09_analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        step09_summary=built.step09_analysis_dir / f"{analysis_id}.cmh_summary.tsv",
    )
    with transaction.candidate_context.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        header = tuple(reader.fieldnames or ())
        rows = list(reader)

    if mutation == "contig":
        rows[0]["chromosome"] = "missing"
    elif mutation == "contig_length":
        rows[0]["contig_length"] = "21"
        rows[0]["window_end_1based"] = "21"
        rows[0]["edit_offset_0based"] = "11"
        rows[0]["oriented_sequence"] = "T" + rows[0]["oriented_sequence"]
    elif mutation == "window":
        rows[0]["window_start_1based"] = "2"
    elif mutation == "sequence":
        sequence = rows[0]["oriented_sequence"]
        rows[0]["oriented_sequence"] = ("C" if sequence[0] != "C" else "G") + sequence[
            1:
        ]
    else:
        fasta_lines = transaction.reference_fasta.read_text().splitlines()
        sequence = list(fasta_lines[1])
        sequence[9] = "C"
        fasta_lines[1] = "".join(sequence)
        transaction.reference_fasta.write_text("\n".join(fasta_lines) + "\n")
        FIXTURE.replace_cell(
            transaction.receipt,
            0,
            "reference_fasta_sha256",
            sha256_file(transaction.reference_fasta),
        )
    if mutation != "reference_center":
        FIXTURE.write_tsv(transaction.candidate_context, header, rows)
        FIXTURE.replace_cell(
            transaction.receipt,
            0,
            "candidate_context_sha256",
            sha256_file(transaction.candidate_context),
        )

    with pytest.raises(CONTEXT.ContractError, match=expected):
        CONTEXT.validate_scientific_context_transaction(transaction.receipt)


@pytest.mark.parametrize(
    ("row_index", "field", "value", "message"),
    (
        (0, "analysis_id", "other-analysis", "wrong analysis_id"),
        (0, "position", "0", "outside the declared contig"),
        (0, "window_start_1based", "2", "window does not equal"),
        (0, "oriented_sequence", "X" * 201, "not the declared genomic window"),
        (0, "edit_offset_0based", "0", "center does not equal"),
        (0, "genomic_alt", "X", "canonical DNA base"),
        (0, "genomic_alt", "A", "nucleotide substitution"),
        (0, "rna_alt", "T", "does not reconcile genomic and RNA bases"),
        (0, "context_status", "boundary_truncated", "does not match its window"),
        (0, "display_rank", "9", "between 1 and 8"),
        (10, "display_rank", "1", "background candidate"),
    ),
)
def test_v1_candidate_rows_reject_each_declared_invariant(
    tmp_path: Path,
    row_index: int,
    field: str,
    value: str,
    message: str,
) -> None:
    paths = FIXTURE.build_outputs(tmp_path)
    FIXTURE.replace_cell(paths["candidate_context"], row_index, field, value)

    with pytest.raises(CONTEXT.ContractError, match=message):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )


@pytest.mark.parametrize(
    ("row_index", "field", "source_index", "message"),
    (
        (1, "candidate_id", 0, "duplicate candidate_id"),
        (1, "display_rank", 0, "duplicate display_rank"),
    ),
)
def test_v1_candidate_roster_rejects_duplicate_identities(
    tmp_path: Path,
    row_index: int,
    field: str,
    source_index: int,
    message: str,
) -> None:
    paths = FIXTURE.build_outputs(tmp_path)
    with paths["candidate_context"].open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    FIXTURE.replace_cell(
        paths["candidate_context"], row_index, field, rows[source_index][field]
    )

    with pytest.raises(CONTEXT.ContractError, match=message):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )


def test_v1_outputs_reject_missing_extra_and_malformed_rows(tmp_path: Path) -> None:
    paths = FIXTURE.build_outputs(tmp_path / "missing-hit")
    with paths["motif_hits"].open(encoding="utf-8", newline="") as stream:
        hit_rows = list(csv.DictReader(stream, delimiter="\t"))
    FIXTURE.write_tsv(paths["motif_hits"], CONTEXT.MOTIF_HITS_HEADER, hit_rows[1:])
    with pytest.raises(CONTEXT.ContractError, match="every exact overlapping"):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )

    paths = FIXTURE.build_outputs(tmp_path / "extra-hit")
    with paths["motif_hits"].open(encoding="utf-8", newline="") as stream:
        hit_rows = list(csv.DictReader(stream, delimiter="\t"))
    FIXTURE.write_tsv(
        paths["motif_hits"], CONTEXT.MOTIF_HITS_HEADER, [*hit_rows, hit_rows[-1]]
    )
    with pytest.raises(CONTEXT.ContractError, match="extra row"):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )

    paths = FIXTURE.build_outputs(tmp_path / "malformed")
    paths["candidate_context"].write_text("wrong\theader\n", encoding="utf-8")
    with pytest.raises(CONTEXT.ContractError, match="header is invalid"):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )


@pytest.mark.parametrize(
    ("table", "mode", "message"),
    (
        ("sequence_logo", "missing", "lacks its complete fixed matrix"),
        ("sequence_logo", "extra", "beyond its fixed matrix"),
        ("motif_statistics", "missing", "lacks its complete fixed position bins"),
        ("motif_statistics", "extra", "beyond its fixed roster"),
    ),
)
def test_v1_fixed_output_matrices_reject_missing_and_extra_rows(
    tmp_path: Path,
    table: str,
    mode: str,
    message: str,
) -> None:
    paths = FIXTURE.build_outputs(tmp_path)
    headers = {
        "sequence_logo": CONTEXT.SEQUENCE_LOGO_HEADER,
        "motif_statistics": CONTEXT.MOTIF_STATISTICS_HEADER,
    }
    with paths[table].open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    changed = rows[:-1] if mode == "missing" else [*rows, rows[-1]]
    FIXTURE.write_tsv(paths[table], headers[table], changed)

    with pytest.raises(CONTEXT.ContractError, match=message):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )


@pytest.mark.parametrize(
    ("table", "row_index", "field", "value", "message"),
    (
        ("sequence_logo", 0, "base_fraction", "0.5", "fraction does not reconcile"),
        ("sequence_logo", 0, "base_count", "99", "does not reconcile"),
        (
            "motif_statistics",
            1,
            "candidate_with_motif_count",
            "99",
            "position bin does not reconcile",
        ),
        (
            "motif_statistics",
            1,
            "odds_ratio",
            "1",
            "must use NA",
        ),
    ),
)
def test_v1_derived_matrices_reject_value_mutations(
    tmp_path: Path,
    table: str,
    row_index: int,
    field: str,
    value: str,
    message: str,
) -> None:
    paths = FIXTURE.build_outputs(tmp_path)
    FIXTURE.replace_cell(paths[table], row_index, field, value)

    with pytest.raises(CONTEXT.ContractError, match=message):
        CONTEXT.validate_scientific_context_outputs(
            paths["candidate_context"],
            paths["motif_hits"],
            paths["sequence_logo"],
            paths["motif_statistics"],
            "analysis",
        )


def _build_transaction(tmp_path: Path) -> FIXTURE.ContextFixture:
    built = STEP_FIXTURE.build_fixture(tmp_path / "step09")
    analysis_id = STEP_FIXTURE.PRIMARY_ANALYSIS_ID
    return FIXTURE.build_transaction(
        tmp_path / "context",
        analysis_id=analysis_id,
        step09_all_sites=built.step09_analysis_dir / f"{analysis_id}.cmh_all_sites.tsv",
        step09_significant_sites=(
            built.step09_analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        step09_summary=built.step09_analysis_dir / f"{analysis_id}.cmh_summary.tsv",
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("schema_version", "2.0.0", "schema_version must be"),
        ("published_output_count", "4", "published_output_count must be"),
        ("transaction_state", "partial", "transaction_state must be"),
        ("git_commit", "short", "full hexadecimal commit"),
        ("r_version", "", "r_version"),
    ),
)
def test_v1_receipt_rejects_constant_and_identity_mutations(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    transaction = _build_transaction(tmp_path)
    FIXTURE.replace_cell(transaction.receipt, 0, field, value)

    with pytest.raises(CONTEXT.ContractError, match=message):
        CONTEXT.validate_scientific_context_transaction(transaction.receipt)


def test_v1_receipt_rejects_relative_paths_and_stale_row_counts(tmp_path: Path) -> None:
    transaction = _build_transaction(tmp_path / "relative")
    FIXTURE.replace_cell(
        transaction.receipt,
        0,
        "candidate_context_path",
        transaction.candidate_context.name,
    )
    with pytest.raises(CONTEXT.ContractError, match="absolute and canonical"):
        CONTEXT.validate_scientific_context_transaction(transaction.receipt)

    transaction = _build_transaction(tmp_path / "count")
    FIXTURE.replace_cell(transaction.receipt, 0, "candidate_context_row_count", "0")
    with pytest.raises(CONTEXT.ContractError, match="row_count is stale"):
        CONTEXT.validate_scientific_context_transaction(transaction.receipt)


def test_v1_receipt_rejects_malformed_fai_and_fasta_identity(tmp_path: Path) -> None:
    transaction = _build_transaction(tmp_path / "duplicate-fai")
    fai_text = transaction.reference_fai.read_text(encoding="utf-8")
    transaction.reference_fai.write_text(fai_text + fai_text, encoding="utf-8")
    FIXTURE.replace_cell(
        transaction.receipt,
        0,
        "reference_fai_sha256",
        sha256_file(transaction.reference_fai),
    )
    with pytest.raises(CONTEXT.ContractError, match="duplicate contig"):
        CONTEXT.validate_scientific_context_transaction(transaction.receipt)

    transaction = _build_transaction(tmp_path / "fasta-header")
    fasta_text = transaction.reference_fasta.read_text(encoding="utf-8")
    transaction.reference_fasta.write_text(
        fasta_text.replace(">1\n", ">2\n", 1), encoding="utf-8"
    )
    FIXTURE.replace_cell(
        transaction.receipt,
        0,
        "reference_fasta_sha256",
        sha256_file(transaction.reference_fasta),
    )
    with pytest.raises(CONTEXT.ContractError, match="does not match its FASTA header"):
        CONTEXT.validate_scientific_context_transaction(transaction.receipt)
