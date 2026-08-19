"""Independent API and behavior tests for the neutral Step 09 contract."""

from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import json
import math
from collections.abc import Callable
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from norad.contracts.scientific_evidence import step08 as STEP08
from norad.contracts.scientific_evidence import step09 as STEP09
from tests import scientific_evidence_test_support as FIXTURES

ROOT = Path(__file__).resolve().parents[3]


def read_tsv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        assert reader.fieldnames is not None
        return tuple(reader.fieldnames), list(reader)


def write_tsv(
    path: Path,
    header: tuple[str, ...],
    rows: list[dict[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(header),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def replace_cell(path: Path, row_index: int, column: str, value: str) -> None:
    header, rows = read_tsv(path)
    rows[row_index][column] = value
    write_tsv(path, header, rows)


def public_fingerprint(module: ModuleType) -> bytes:
    constants = [
        "NA_VALUE",
        "STEP09_RESULT_HEADER",
        "STEP09_SUMMARY_HEADER",
        "STEP09_MUTATION_HEADER",
        "CANONICAL_MUTATIONS",
        "STEP09_TEST_STATUSES",
        "STEP09_CALL_STATUSES",
        "STEP09_BACKGROUND_STATUSES",
        "STEP09_STATUS_COUNT_FIELDS",
    ]
    functions = [
        "validate_step09_results",
        "validate_step09_summary",
        "validate_step09_result_semantics",
        "validate_significant_subset",
        "validate_mutation_spectrum",
        "validate_pdf",
    ]
    document = {
        "constants": {name: getattr(module, name) for name in constants},
        "functions": {
            name: str(inspect.signature(getattr(module, name))) for name in functions
        },
        "table_fields": list(module.Table.__dataclass_fields__),
        "error_base": [value.__name__ for value in module.ContractError.__mro__],
    }
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()


def build_valid(root: Path) -> SimpleNamespace:
    built = FIXTURES.build_fixture(root)
    sample_hash = STEP08.sha256_file(built.sample_manifest)
    partition_hash = STEP08.sha256_file(built.partition_manifest)
    sites_hash = STEP08.sha256_file(built.step08_sites)
    inputs_hash = STEP08.sha256_file(built.step08_inputs)
    sample_table, sample_ids, sample_rows = STEP08.validate_sample_manifest(
        built.sample_manifest
    )
    partitions = STEP08.validate_partition_manifest(built.partition_manifest)
    inputs = STEP08.validate_step08_inputs(
        built.step08_inputs,
        sample_ids,
        partitions.rows,
        sample_hash,
        partition_hash,
    )
    sites = STEP08.validate_step08_sites(
        built.step08_sites,
        sample_ids,
        partitions.rows,
        inputs.rows,
    )
    analysis_id = FIXTURES.PRIMARY_ANALYSIS_ID
    all_sites_path = built.step09_analysis_dir / f"{analysis_id}.cmh_all_sites.tsv"
    significant_path = (
        built.step09_analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
    )
    summary_path = built.step09_analysis_dir / f"{analysis_id}.cmh_summary.tsv"
    mutation_path = built.step09_analysis_dir / f"{analysis_id}.mutation_spectrum.tsv"
    mutation_pdf = built.step09_analysis_dir / f"{analysis_id}.mutation_spectrum.pdf"
    depth_pdf = built.step09_analysis_dir / f"{analysis_id}.depth_delta.pdf"
    return SimpleNamespace(
        built=built,
        analysis_id=analysis_id,
        sample_hash=sample_hash,
        partition_hash=partition_hash,
        sites_hash=sites_hash,
        inputs_hash=inputs_hash,
        sample_table=sample_table,
        sample_ids=sample_ids,
        sample_rows=sample_rows,
        partitions=partitions,
        inputs=inputs,
        sites=sites,
        all_sites_path=all_sites_path,
        significant_path=significant_path,
        summary_path=summary_path,
        mutation_path=mutation_path,
        mutation_pdf=mutation_pdf,
        depth_pdf=depth_pdf,
    )


@pytest.fixture
def valid(tmp_path: Path) -> SimpleNamespace:
    return build_valid(tmp_path / "fixture")


def validate_results(valid: SimpleNamespace, path: Path | None = None):
    return STEP09.validate_step09_results(
        "Step 09 all-sites",
        valid.all_sites_path if path is None else path,
        valid.sample_ids,
        valid.analysis_id,
        valid.sites.rows,
    )


def validate_summary(
    valid: SimpleNamespace,
    all_rows: list[dict[str, str]],
    path: Path | None = None,
):
    return STEP09.validate_step09_summary(
        valid.summary_path if path is None else path,
        valid.analysis_id,
        FIXTURES.COHORT_ID,
        valid.sample_ids,
        valid.sample_rows,
        all_rows,
        valid.built.sample_manifest,
        valid.built.partition_manifest,
        valid.built.step08_sites,
        valid.built.step08_inputs,
        valid.sample_hash,
        valid.partition_hash,
        valid.sites_hash,
        valid.inputs_hash,
        valid.inputs.rows[0]["orientation_policy"],
    )


def validate_projection(
    valid: SimpleNamespace,
    *,
    mutation_spectrum: bool = False,
):
    return STEP09.validate_step09_projection(
        valid.all_sites_path,
        valid.significant_path,
        valid.summary_path,
        valid.analysis_id,
        mutation_spectrum=valid.mutation_path if mutation_spectrum else None,
    )


def test_public_api_fingerprint_matches_pre_extraction_oracle() -> None:
    payload = public_fingerprint(STEP09)

    assert len(payload) == 5607
    assert hashlib.sha256(payload).hexdigest() == (
        "a40e7b2cab9227cd80bf4750bd5495442caf43d960c10b0003901f992a2ba3a3"
    )


def test_declared_public_api_matches_supported_owner_surface() -> None:
    expected = {
        "ContractError",
        "Table",
        "NA_VALUE",
        "STEP09_RESULT_HEADER",
        "STEP09_SUMMARY_HEADER",
        "STEP09_MUTATION_HEADER",
        "CANONICAL_MUTATIONS",
        "STEP09_TEST_STATUSES",
        "STEP09_CALL_STATUSES",
        "STEP09_BACKGROUND_STATUSES",
        "STEP09_STATUS_COUNT_FIELDS",
        "count_status",
        "paired_samples",
        "resolve_recorded_path",
        "validate_step09_projection",
        "validate_step09_results",
        "validate_step09_summary",
        "validate_step09_result_semantics",
        "validate_significant_subset",
        "validate_mutation_spectrum",
        "validate_pdf",
    }

    assert set(STEP09.__all__) == expected
    assert all(hasattr(STEP09, name) for name in STEP09.__all__)


@pytest.mark.parametrize(
    ("guard_materialization", "mutation_spectrum"),
    ((False, False), (True, False), (False, True)),
)
def test_projection_streams_and_admits_the_intrinsic_result_set(
    valid: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    guard_materialization: bool,
    mutation_spectrum: bool,
) -> None:
    original_read_tsv = STEP09.read_tsv
    candidate_paths = {
        valid.all_sites_path.resolve(),
        valid.significant_path.resolve(),
    }

    def bounded_read_tsv(
        label: str,
        value: str | Path,
        expected_header: tuple[str, ...] | None = None,
    ):
        if Path(value).expanduser().resolve() in candidate_paths:
            pytest.fail(f"candidate table was materialized by read_tsv: {label}")
        return original_read_tsv(label, value, expected_header)

    if guard_materialization:
        monkeypatch.setattr(STEP09, "read_tsv", bounded_read_tsv)
    all_table, significant_table, summary_table, sample_ids = validate_projection(
        valid, mutation_spectrum=mutation_spectrum
    )

    assert all_table.path == valid.all_sites_path.resolve()
    assert significant_table.path == valid.significant_path.resolve()
    assert summary_table.path == valid.summary_path.resolve()
    assert sample_ids == tuple(valid.sample_ids)
    assert all_table.row_count == 6
    assert significant_table.row_count == 2
    assert all_table.header == significant_table.header
    assert not hasattr(all_table, "rows")
    assert not hasattr(significant_table, "rows")
    assert len(summary_table.rows) == 1


def test_projection_rejects_pairwise_mutation_spectrum_corruption(
    valid: SimpleNamespace,
) -> None:
    header, rows = read_tsv(valid.mutation_path)
    rows[0]["candidate_count"] = str(int(rows[0]["candidate_count"]) + 1)
    write_tsv(valid.mutation_path, header, rows)

    with pytest.raises(
        STEP09.ContractError, match="candidate_count does not reconcile"
    ):
        validate_projection(valid, mutation_spectrum=True)


def test_projection_rejects_aggregate_mutation_spectrum_corruption(
    valid: SimpleNamespace,
) -> None:
    all_header, all_rows = read_tsv(valid.all_sites_path)
    all_rows[2]["rna_alt"] = all_rows[2]["rna_ref"]
    write_tsv(valid.all_sites_path, all_header, all_rows)

    mutation_header, mutation_rows = read_tsv(valid.mutation_path)
    mutation_row = next(row for row in mutation_rows if row["mutation_type"] == "C>T")
    mutation_row.update(candidate_count="0", candidate_fraction="0")
    write_tsv(valid.mutation_path, mutation_header, mutation_rows)

    with pytest.raises(
        STEP09.ContractError,
        match="aggregate candidate_count does not reconcile",
    ):
        validate_projection(valid, mutation_spectrum=True)


@pytest.mark.parametrize(
    ("source", "column", "value", "expected"),
    (
        ("all", "analysis_id", "other", "wrong analysis_id"),
        ("all", "test_status", "unknown", "must be one of"),
        ("all", "replicate_count", "01", "non-negative integer"),
        ("all", "annotation_strand", ".", "annotation_strand must be one of"),
        ("all", "is_intron", "true", "is_intron must be one of TRUE, FALSE"),
        ("all", "transcript_ids", "tx1; tx2", "semicolon-delimited list"),
        ("all", "DP__FIRST", "NA", "one-sided DP/AD missingness"),
        ("all", "AD__FIRST", "101", "AD greater than DP"),
        ("all", "cmh_degrees_freedom", "2", "one CMH degree of freedom"),
        ("all", "cmh_p_value", "NA", "lacks complete CMH statistics"),
        ("summary", "multiple_testing_method", "BY", "approved CMH contract"),
        ("summary", "fdr_threshold", "not-a-number", "must be numeric"),
        ("summary", "candidate_count", "999", "candidate_count disagrees"),
        (
            "summary",
            "target_candidate_count",
            "999",
            "target_candidate_count disagrees",
        ),
        ("summary", "control_condition", "OTHER", "control_condition disagrees"),
    ),
)
def test_projection_rejects_intrinsic_mutations(
    valid: SimpleNamespace,
    source: str,
    column: str,
    value: str,
    expected: str,
) -> None:
    if column.endswith("__FIRST"):
        column = f"{column.removesuffix('__FIRST')}__{valid.sample_ids[0]}"
    path = valid.summary_path if source == "summary" else valid.all_sites_path
    replace_cell(path, 0, column, value)

    with pytest.raises(STEP09.ContractError, match=expected):
        validate_projection(valid)


def test_projection_rejects_header_duplicates_and_subset_drift(
    valid: SimpleNamespace,
) -> None:
    header, rows = read_tsv(valid.all_sites_path)
    write_tsv(valid.all_sites_path, header, [rows[0], rows[0], *rows[2:]])
    with pytest.raises(STEP09.ContractError, match="duplicate candidate_id"):
        validate_projection(valid)

    write_tsv(valid.all_sites_path, header, rows)
    significant_header, significant_rows = read_tsv(valid.significant_path)
    significant_rows[0]["qual"] = "61"
    write_tsv(valid.significant_path, significant_header, significant_rows)
    with pytest.raises(STEP09.ContractError, match="exact ordered"):
        validate_projection(valid)

    significant_rows[0]["qual"] = rows[0]["qual"]
    write_tsv(valid.significant_path, significant_header, significant_rows)
    bad_header = (*header[:-1], "AF__BROKEN")
    bad_rows = [
        {new: row.get(old, "NA") for new, old in zip(bad_header, header, strict=True)}
        for row in rows
    ]
    write_tsv(valid.all_sites_path, bad_header, bad_rows)
    with pytest.raises(STEP09.ContractError, match="invalid AF__ sample block"):
        validate_projection(valid)


def test_valid_fixture_passes_every_public_validator_with_exact_results(
    valid: SimpleNamespace,
) -> None:
    all_sites = validate_results(valid)
    significant = STEP09.validate_step09_results(
        "Step 09 significant-sites",
        valid.significant_path,
        valid.sample_ids,
        valid.analysis_id,
        valid.sites.rows,
    )
    summary = validate_summary(valid, all_sites.rows)
    mutation = STEP09.validate_mutation_spectrum(
        valid.mutation_path,
        valid.analysis_id,
        all_sites.rows,
    )

    assert all_sites.path == valid.all_sites_path.resolve()
    assert len(all_sites.rows) == 6
    assert [row["candidate_id"] for row in all_sites.rows] == [
        row["candidate_id"] for row in valid.sites.rows
    ]
    assert summary.rows[0]["successfully_tested_count"] == "3"
    assert [row["call_status"] for row in significant.rows] == [
        "significant_up",
        "significant_down",
    ]
    assert [row["mutation_type"] for row in mutation.rows] == list(
        STEP09.CANONICAL_MUTATIONS
    )
    assert (
        STEP09.validate_step09_result_semantics(
            all_sites.rows,
            summary.rows[0],
            valid.sample_rows,
        )
        is None
    )
    assert (
        STEP09.validate_significant_subset(
            all_sites.rows,
            significant.rows,
        )
        is None
    )
    assert STEP09.validate_pdf("Mutation PDF", valid.mutation_pdf) is None
    assert STEP09.validate_pdf("Depth PDF", valid.depth_pdf) is None


@pytest.mark.parametrize(
    ("column", "value", "expected"),
    (
        ("analysis_id", "other", "wrong analysis_id"),
        ("candidate_id", "unknown", "unknown Step 08 candidate"),
        ("chromosome", "other", "differs from the Step 08 candidate"),
        ("test_status", "unknown", "must be one of"),
        ("call_status", "unknown", "must be one of"),
        ("replicate_count", "01", "non-negative integer"),
    ),
)
def test_result_contract_rejects_core_row_mutations(
    valid: SimpleNamespace,
    column: str,
    value: str,
    expected: str,
) -> None:
    replace_cell(valid.all_sites_path, 0, column, value)

    with pytest.raises(STEP09.ContractError, match=expected):
        validate_results(valid)


def test_result_contract_rejects_header_and_duplicate_candidate_mutations(
    valid: SimpleNamespace,
) -> None:
    header, rows = read_tsv(valid.all_sites_path)
    duplicate_path = valid.all_sites_path.with_name("duplicate.tsv")
    write_tsv(duplicate_path, header, [rows[0], rows[0]])
    with pytest.raises(STEP09.ContractError, match="duplicate candidate_id"):
        validate_results(valid, duplicate_path)

    bad_header_path = valid.all_sites_path.with_name("bad-header.tsv")
    bad_header = (*header[:-1], "unexpected")
    bad_rows = [
        {new: row.get(old, "NA") for new, old in zip(bad_header, header, strict=True)}
        for row in rows
    ]
    write_tsv(bad_header_path, bad_header, bad_rows)
    with pytest.raises(STEP09.ContractError, match="header is invalid"):
        validate_results(valid, bad_header_path)


@pytest.mark.parametrize(
    ("column", "value", "expected"),
    (
        ("analysis_id", "other", "analysis_id differs"),
        ("cohort_id", "other", "cohort_id differs"),
        ("multiple_testing_method", "BY", "approved CMH contract"),
        ("sample_manifest_path", "/wrong", "differs from the explicit input"),
        ("sample_manifest_sha256", "b" * 64, "is stale"),
        ("sample_count", "7", "sample_count differs"),
        ("candidate_count", "7", "candidate_count differs"),
        ("target_rna_change", "A>N", "canonical SNV"),
        ("target_candidate_count", "4", "target candidate count"),
        ("successfully_tested_count", "2", "does not reconcile"),
        ("replicate_count", "2", "replicate_count differs"),
        ("orientation_policy", "other", "legacy_provisional_v1"),
        ("background_condition", "EV", "must be independent"),
        ("background_condition", "MISSING", "absent from the manifest"),
    ),
)
def test_summary_contract_rejects_core_mutations(
    valid: SimpleNamespace,
    column: str,
    value: str,
    expected: str,
) -> None:
    all_rows = validate_results(valid).rows
    replace_cell(valid.summary_path, 0, column, value)

    with pytest.raises(STEP09.ContractError, match=expected):
        validate_summary(valid, all_rows)


def test_summary_contract_rejects_row_count_and_result_context(
    valid: SimpleNamespace,
) -> None:
    all_rows = validate_results(valid).rows
    header, rows = read_tsv(valid.summary_path)
    write_tsv(valid.summary_path, header, [rows[0], rows[0]])
    with pytest.raises(STEP09.ContractError, match="exactly one data row"):
        validate_summary(valid, all_rows)

    write_tsv(valid.summary_path, header, rows)
    changed = copy.deepcopy(all_rows)
    changed[0]["control_condition"] = "OTHER"
    with pytest.raises(STEP09.ContractError, match="control_condition differs"):
        validate_summary(valid, changed)

    changed = copy.deepcopy(all_rows)
    changed[0]["orientation_policy"] = "other"
    with pytest.raises(STEP09.ContractError, match="inconsistent orientation policy"):
        validate_summary(valid, changed)


def test_semantic_contract_rejects_core_state_mutations(valid: SimpleNamespace) -> None:
    all_rows = validate_results(valid).rows
    summary = validate_summary(valid, all_rows).rows[0]

    def rejected(
        mutate: Callable[[list[dict[str, str]], dict[str, str]], None],
        expected: str,
    ) -> None:
        rows = copy.deepcopy(all_rows)
        summary_row = dict(summary)
        mutate(rows, summary_row)
        with pytest.raises(STEP09.ContractError, match=expected):
            STEP09.validate_step09_result_semantics(
                rows,
                summary_row,
                valid.sample_rows,
            )

    rejected(
        lambda rows, _summary: rows[2].update(
            test_status="tested", call_status="effect_not_met"
        ),
        "declared target change",
    )
    rejected(
        lambda rows, _summary: rows[0].update(max_background_af="0"),
        "background-disabled",
    )
    rejected(
        lambda rows, _summary: rows[0].update(mean_analysis_dp="999"),
        "depth metrics",
    )
    rejected(
        lambda rows, _summary: rows[0].update(mean_control_af="0.9"),
        "AF/delta metrics",
    )
    rejected(
        lambda rows, _summary: rows[3].update(
            {
                f"DP__{valid.sample_ids[0]}": "NA",
                f"AD__{valid.sample_ids[0]}": "NA",
                "min_analysis_dp": "1",
            }
        ),
        "must be NA when analysis counts are missing",
    )
    rejected(
        lambda rows, _summary: rows[3].update(
            {
                **{
                    f"{prefix}__{sample_id}": "0"
                    for prefix in ("DP", "AD")
                    for sample_id in valid.sample_ids
                },
                "min_analysis_dp": "0",
                "mean_analysis_dp": "0",
                "mean_control_af": "0",
            }
        ),
        "must be NA with zero analysis depth",
    )
    rejected(
        lambda rows, _summary: rows[0].update(
            {
                "test_status": "low_coverage",
                "call_status": "not_tested",
                **{
                    column: "NA"
                    for column in (
                        "cmh_statistic",
                        "cmh_degrees_freedom",
                        "cmh_p_value",
                        "cmh_fdr_bh",
                        "common_odds_ratio",
                    )
                },
            }
        ),
        "test_status conflicts",
    )
    rejected(
        lambda rows, _summary: rows[2].update(call_status="effect_not_met"),
        "untested Step 09 candidate",
    )
    rejected(
        lambda rows, _summary: rows[2].update(cmh_p_value="0.5"),
        "must use cmh_p_value=NA",
    )
    rejected(
        lambda rows, _summary: rows[0].update(call_status="not_tested"),
        "tested Step 09 candidate",
    )
    rejected(
        lambda rows, _summary: rows[0].update(cmh_degrees_freedom="2"),
        "statistics are malformed",
    )
    rejected(
        lambda rows, _summary: rows[0].update(call_status="effect_not_met"),
        "declared strict thresholds",
    )
    rejected(
        lambda rows, _summary: rows[0].update(cmh_fdr_bh="0.0014"),
        "global BH adjustment",
    )
    rejected(
        lambda _rows, summary_row: summary_row.update(fdr_threshold="0"),
        "thresholds are outside",
    )


def test_semantic_contract_rejects_enabled_background_without_samples(
    valid: SimpleNamespace,
) -> None:
    rows = validate_results(valid).rows
    summary = dict(validate_summary(valid, rows).rows[0])
    summary["background_condition"] = "BACKGROUND"

    with pytest.raises(STEP09.ContractError, match="enabled background has zero depth"):
        STEP09.validate_step09_result_semantics(
            rows,
            summary,
            valid.sample_rows,
        )


def test_semantic_contract_accepts_missing_counts_and_strict_threshold_edges(
    valid: SimpleNamespace,
) -> None:
    all_rows = validate_results(valid).rows
    summary = validate_summary(valid, all_rows).rows[0]

    missing_rows = copy.deepcopy(all_rows)
    missing_rows[3].update(
        {f"{prefix}__{valid.sample_ids[0]}": "NA" for prefix in ("DP", "AD", "AF")}
    )
    missing_rows[3].update(
        {
            column: "NA"
            for column in (
                "min_analysis_dp",
                "mean_analysis_dp",
                "mean_control_af",
                "mean_treatment_af",
                "treatment_control_difference",
                "cmh_statistic",
                "cmh_degrees_freedom",
                "cmh_p_value",
                "cmh_fdr_bh",
                "common_odds_ratio",
            )
        }
    )
    missing_rows[3]["test_status"] = "missing_counts"
    assert (
        STEP09.validate_step09_result_semantics(
            missing_rows,
            summary,
            valid.sample_rows,
        )
        is None
    )

    for column, value, expected_call in (
        ("mean_dp_threshold", "100", "below_mean_dp"),
        ("fdr_threshold", "0.0015", "fdr_not_met"),
        ("common_or_threshold", "3.5", "effect_not_met"),
        ("absolute_difference_threshold", "0.20", "effect_not_met"),
    ):
        rows = copy.deepcopy(all_rows)
        summary_row = dict(summary)
        summary_row[column] = value
        for row in rows:
            if row["test_status"] == "tested":
                row["call_status"] = expected_call
        STEP09.validate_step09_result_semantics(
            rows,
            summary_row,
            valid.sample_rows,
        )


@pytest.mark.parametrize(
    ("background_status", "dp", "ad", "maximum"),
    (
        ("pass", "100", "0", "0"),
        ("fail_fraction", "100", "5", "0.05"),
        ("missing_counts", "NA", "NA", "NA"),
        ("low_coverage", "0", "0", "NA"),
    ),
)
def test_enabled_background_reconciles_from_immutable_counts(
    valid: SimpleNamespace,
    background_status: str,
    dp: str,
    ad: str,
    maximum: str,
) -> None:
    all_rows = validate_results(valid).rows
    summary = dict(validate_summary(valid, all_rows).rows[0])
    summary["background_condition"] = "BACKGROUND"
    background_sample = dict(valid.sample_rows[0])
    background_sample.update(
        sample_id="BACKGROUND_1",
        condition="BACKGROUND",
        replicate="1",
    )
    sample_rows = [*valid.sample_rows, background_sample]
    rows = copy.deepcopy(all_rows)
    for row in rows:
        row.update(
            {
                "background_condition": "BACKGROUND",
                "background_status": background_status,
                "max_background_af": maximum,
                "DP__BACKGROUND_1": dp,
                "AD__BACKGROUND_1": ad,
            }
        )
        if row["test_status"] == "tested" and background_status != "pass":
            row["call_status"] = "background_not_passed"

    assert (
        STEP09.validate_step09_result_semantics(
            rows,
            summary,
            sample_rows,
        )
        is None
    )

    rows[0]["max_background_af"] = "0.5" if maximum != "NA" else "0"
    with pytest.raises(STEP09.ContractError, match="enabled-background"):
        STEP09.validate_step09_result_semantics(rows, summary, sample_rows)


def test_significant_subset_requires_exact_order_and_rows(
    valid: SimpleNamespace,
) -> None:
    all_rows = validate_results(valid).rows
    significant = STEP09.validate_step09_results(
        "Step 09 significant-sites",
        valid.significant_path,
        valid.sample_ids,
        valid.analysis_id,
        valid.sites.rows,
    ).rows
    assert STEP09.validate_significant_subset(all_rows, significant) is None

    for changed in (
        list(reversed(significant)),
        significant[:-1],
        [*significant, all_rows[-1]],
    ):
        with pytest.raises(STEP09.ContractError, match="exact ordered"):
            STEP09.validate_significant_subset(all_rows, changed)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("order", "canonical 12 SNVs"),
        ("identity", "identity columns"),
        ("count", "candidate_count does not reconcile"),
        ("fraction", "candidate_fraction is invalid"),
    ),
)
def test_mutation_spectrum_rejects_core_mutations(
    valid: SimpleNamespace,
    mutation: str,
    expected: str,
) -> None:
    all_rows = validate_results(valid).rows
    header, rows = read_tsv(valid.mutation_path)
    if mutation == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "identity":
        rows[0]["rna_ref"] = "T"
    elif mutation == "count":
        rows[0]["candidate_count"] = "1"
    else:
        rows[0]["candidate_fraction"] = "0.5"
    write_tsv(valid.mutation_path, header, rows)

    with pytest.raises(STEP09.ContractError, match=expected):
        STEP09.validate_mutation_spectrum(
            valid.mutation_path,
            valid.analysis_id,
            all_rows,
        )


def test_mutation_spectrum_accepts_empty_candidate_universe(tmp_path: Path) -> None:
    path = tmp_path / "empty-universe.tsv"
    rows = []
    for mutation_type in STEP09.CANONICAL_MUTATIONS:
        ref, alt = mutation_type.split(">")
        rows.append(
            {
                "analysis_id": "analysis",
                "rna_ref": ref,
                "rna_alt": alt,
                "mutation_type": mutation_type,
                "candidate_count": "0",
                "candidate_fraction": "0",
                "successfully_tested_count": "0",
                "significant_up_count": "0",
                "significant_down_count": "0",
            }
        )
    write_tsv(path, STEP09.STEP09_MUTATION_HEADER, rows)

    table = STEP09.validate_mutation_spectrum(path, "analysis", [])

    assert len(table.rows) == 12


def test_pdf_validation_rejects_signature_eof_and_read_failures(
    valid: SimpleNamespace,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad_signature = tmp_path / "bad-signature.pdf"
    bad_signature.write_bytes(b"not-a-pdf\n%%EOF\n")
    with pytest.raises(STEP09.ContractError, match="lacks a %PDF- signature"):
        STEP09.validate_pdf("Bad PDF", bad_signature)

    missing_eof = tmp_path / "missing-eof.pdf"
    missing_eof.write_bytes(b"%PDF-1.4\n")
    with pytest.raises(STEP09.ContractError, match="trailing %%EOF marker"):
        STEP09.validate_pdf("Bad PDF", missing_eof)

    with pytest.raises(STEP09.ContractError, match="does not exist"):
        STEP09.validate_pdf("Missing PDF", tmp_path / "missing.pdf")

    original_read_bytes = Path.read_bytes

    def fail_read(path: Path) -> bytes:
        if path == valid.mutation_pdf.resolve():
            raise OSError("injected read failure")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_read)
    with pytest.raises(STEP09.ContractError, match="Could not read Mutation PDF"):
        STEP09.validate_pdf("Mutation PDF", valid.mutation_pdf)


def test_private_parsing_path_count_and_pairing_edges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert STEP09.parse_nonnegative_or_infinite("value", "0") == 0
    assert math.isinf(STEP09.parse_nonnegative_or_infinite("value", "inf"))
    for value, expected in (
        ("not-a-number", "must be numeric"),
        ("nan", "non-negative and not NaN"),
        ("-1", "non-negative and not NaN"),
    ):
        with pytest.raises(STEP09.ContractError, match=expected):
            STEP09.parse_nonnegative_or_infinite("value", value)

    monkeypatch.chdir(tmp_path)
    assert (
        STEP09.resolve_recorded_path("nested/../record.tsv")
        == (tmp_path / "record.tsv").resolve()
    )
    absolute = (tmp_path / "absolute.tsv").resolve()
    assert STEP09.resolve_recorded_path(str(absolute)) == absolute
    assert (
        STEP09.count_status(
            ({"status": "pass"}, {"status": "fail"}, {"status": "pass"}),
            "status",
            "pass",
        )
        == 2
    )

    sample_rows = FIXTURES.sample_rows()
    replicates, pairs = STEP09.paired_samples(sample_rows, "EV", "PUM1")
    assert replicates == ["2", "3", "4"]
    assert pairs == {
        replicate: (control, treatment)
        for replicate, control, treatment in FIXTURES.PAIRINGS
    }
    with pytest.raises(STEP09.ContractError, match="conditions must differ"):
        STEP09.paired_samples(sample_rows, "EV", "EV")
    with pytest.raises(STEP09.ContractError, match="at least two strata"):
        STEP09.paired_samples(sample_rows[:1] + sample_rows[3:4], "EV", "PUM1")
    duplicate = [dict(row) for row in sample_rows]
    duplicate.append({**sample_rows[0], "sample_id": "DUPLICATE"})
    with pytest.raises(STEP09.ContractError, match="exactly one control"):
        STEP09.paired_samples(duplicate, "EV", "PUM1")
