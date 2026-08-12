"""Orientation, annotation, QC-funnel, and replicate evidence checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from norad.contracts.scientific_evidence import review_package, step08, step09
from norad.contracts.scientific_evidence.step08 import NA_VALUE, values_close
from norad.libraries.alignments import orientation as alignment_orientation

from .intake import complement_base, validate_candidate_reference, validate_iso_date


def validate_orientation_evidence(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    sample_rows: Sequence[Mapping[str, str]],
    partition_ids: set[str],
    plan: Mapping[str, str],
    complete: bool,
) -> None:
    step08.ensure_unique(rows, "locus_id", "Orientation locus audit")
    samples = {row["sample_id"]: row for row in sample_rows}
    observed_orientations: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        step08.validate_safe_id("Orientation audit locus_id", row["locus_id"])
        result = validate_candidate_reference(
            f"Orientation audit row {row_number}",
            row["candidate_id"],
            candidates,
        )
        if row["partition_id"] not in partition_ids:
            step08.fail("Orientation audit references an unknown partition.")
        step08.validate_enum(
            "Orientation audit orientation",
            row["orientation"],
            alignment_orientation.ORIENTATIONS,
        )
        observed_orientations.add(row["orientation"])
        if any(
            row[column] != result[column]
            for column in (
                "partition_id",
                "orientation",
                "chromosome",
                "position",
                "genomic_ref",
                "genomic_alt",
                "rna_ref",
                "rna_alt",
            )
        ):
            step08.fail("Orientation audit candidate identity differs from Step 09.")
        sample = samples.get(row["sample_id"])
        if sample is None:
            step08.fail("Orientation audit references an unknown sample.")
        if (
            row["condition"] != sample["condition"]
            or row["replicate"] != sample["replicate"]
        ):
            step08.fail("Orientation audit sample metadata differs from the manifest.")
        expected_transcripts = result["transcript_ids"].split(";")
        if result["transcript_ids"] == NA_VALUE:
            valid_transcript = row["transcript_id"] == NA_VALUE
        else:
            valid_transcript = row["transcript_id"] in expected_transcripts
        if not valid_transcript:
            step08.fail(
                "Orientation audit transcript_id is not part of the "
                "Step 09 candidate annotation."
            )
        if row["transcript_strand"] != result["annotation_strand"]:
            step08.fail(
                "Orientation audit transcript_strand differs from the "
                "candidate annotation strand."
            )
        expected_flags = alignment_orientation.MECHANICAL_ORIENTATION_FLAG_GROUPS[
            row["orientation"]
        ]
        if row["flag_group"] not in expected_flags:
            step08.fail(
                "Orientation audit flag_group is incompatible with its "
                "mechanical orientation."
            )
        raw_dp = step08.parse_nonnegative_int("Orientation audit raw_dp", row["raw_dp"])
        raw_ad = step08.parse_nonnegative_int("Orientation audit raw_ad", row["raw_ad"])
        raw_ref = step08.parse_nonnegative_int(
            "Orientation audit raw_ref_count", row["raw_ref_count"]
        )
        if raw_ad > raw_dp or raw_ref + raw_ad != raw_dp:
            step08.fail("Orientation audit raw count arithmetic is invalid.")
        sample_id = row["sample_id"]
        if (
            row["raw_dp"] != result[f"DP__{sample_id}"]
            or row["raw_ad"] != result[f"AD__{sample_id}"]
        ):
            step08.fail(
                "Orientation audit raw counts differ from the Step 09 "
                "candidate/sample counts."
            )
        for allele_column in (
            "current_expected_rna_ref",
            "current_expected_rna_alt",
            "inverted_expected_rna_ref",
            "inverted_expected_rna_alt",
        ):
            if row[allele_column] not in ("A", "C", "G", "T"):
                step08.fail(f"Orientation audit {allele_column} must be a DNA base.")
        if (
            row["current_expected_rna_ref"] != result["rna_ref"]
            or row["current_expected_rna_alt"] != result["rna_alt"]
            or row["inverted_expected_rna_ref"] != complement_base(result["rna_ref"])
            or row["inverted_expected_rna_alt"] != complement_base(result["rna_alt"])
        ):
            step08.fail(
                "Orientation audit expected alleles do not match the current "
                "and inverted candidate interpretations."
            )
        step08.validate_enum(
            "Orientation audit concordance_status",
            row["concordance_status"],
            review_package.CONCORDANCE_STATUSES,
        )
        validate_iso_date("Orientation audit review_date", row["review_date"])
        step08.require_text("Orientation audit reviewer", row["reviewer"])
        step08.require_text("Orientation audit detail", row["detail"])
    if complete and len(rows) != step08.parse_nonnegative_int(
        "Scientific review plan locus_target_count", plan["locus_target_count"]
    ):
        step08.fail(
            "Complete orientation audit row count differs from locus_target_count."
        )
    if (
        complete
        and rows
        and observed_orientations != alignment_orientation.REQUIRED_ORIENTATIONS
    ):
        step08.fail("Complete orientation audit must cover both required orientations.")


def validate_annotation_evidence(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    plan: Mapping[str, str],
    complete: bool,
) -> None:
    step08.ensure_unique(rows, "audit_id", "Annotation audit")
    observed_cases: set[str] = set()
    observed_strands: set[str] = set()
    observed_orientations: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        result = validate_candidate_reference(
            f"Annotation audit row {row_number}",
            row["candidate_id"],
            candidates,
        )
        step08.validate_enum(
            "Annotation audit orientation",
            row["orientation"],
            alignment_orientation.ORIENTATIONS,
        )
        if row["annotation_strand"] not in ("+", "-"):
            step08.fail("Annotation audit annotation_strand must be + or -.")
        if any(
            row[column] != result[column]
            for column in (
                "chromosome",
                "position",
                "orientation",
                "annotation_strand",
            )
        ):
            step08.fail("Annotation audit candidate identity differs from Step 09.")
        observed_mapping = {
            "observed_gene_ids": result["gene_ids"],
            "observed_transcript_ids": result["transcript_ids"],
            "observed_is_cds": result["is_cds"],
            "observed_is_five_prime_utr": result["is_five_prime_utr"],
            "observed_is_three_prime_utr": result["is_three_prime_utr"],
            "observed_is_exon": result["is_exon"],
            "observed_is_intron": result["is_intron"],
        }
        for column, expected in observed_mapping.items():
            if row[column] != expected:
                step08.fail(
                    f"Annotation audit {column} differs from the Step 09 "
                    "candidate annotation."
                )
        for column in (
            "expected_is_cds",
            "expected_is_five_prime_utr",
            "expected_is_three_prime_utr",
            "expected_is_exon",
            "expected_is_intron",
        ):
            if row[column] not in ("TRUE", "FALSE"):
                step08.fail(f"Annotation audit {column} must be TRUE or FALSE.")
        for column in ("expected_gene_ids", "expected_transcript_ids"):
            step08.require_text(
                f"Annotation audit {column}", row[column], allow_na=True
            )
        step08.validate_enum(
            "Annotation audit assignment_status",
            row["assignment_status"],
            review_package.ANNOTATION_ASSIGNMENT_STATUSES,
        )
        step08.validate_enum(
            "Annotation audit ambiguity_status",
            row["ambiguity_status"],
            review_package.ANNOTATION_AMBIGUITY_STATUSES,
        )
        expected_mapping = {
            "expected_gene_ids": row["observed_gene_ids"],
            "expected_transcript_ids": row["observed_transcript_ids"],
            "expected_is_cds": row["observed_is_cds"],
            "expected_is_five_prime_utr": row["observed_is_five_prime_utr"],
            "expected_is_three_prime_utr": row["observed_is_three_prime_utr"],
            "expected_is_exon": row["observed_is_exon"],
            "expected_is_intron": row["observed_is_intron"],
        }
        expected_matches = all(
            row[column] == expected for column, expected in expected_mapping.items()
        )
        if row["assignment_status"] == "match" and not expected_matches:
            step08.fail(
                "Annotation audit assignment_status=match conflicts with "
                "observed/expected fields."
            )
        if row["assignment_status"] == "mismatch" and expected_matches:
            step08.fail(
                "Annotation audit assignment_status=mismatch has no observed "
                "difference."
            )
        observed_cases.add(row["case_type"])
        observed_strands.add(row["annotation_strand"])
        observed_orientations.add(row["orientation"])
        validate_iso_date("Annotation audit review_date", row["review_date"])
        step08.require_text("Annotation audit reviewer", row["reviewer"])
        step08.require_text("Annotation audit detail", row["detail"])
    if complete:
        required_cases = set(plan["required_annotation_cases"].split(","))
        if not required_cases.issubset(observed_cases):
            step08.fail("Complete annotation audit is missing required case types.")
        if observed_strands != {"+", "-"}:
            step08.fail("Complete annotation audit must cover both annotation strands.")
        if observed_orientations != alignment_orientation.REQUIRED_ORIENTATIONS:
            step08.fail("Complete annotation audit must cover both orientations.")


def _expected_qc_rows(
    step08_inputs: Sequence[Mapping[str, str]],
    all_rows: Sequence[Mapping[str, str]],
    target_rna_change: str,
) -> list[dict[str, str]]:
    target_ref, target_alt = target_rna_change.split(">")
    result: list[dict[str, str]] = []
    for input_row in step08_inputs:
        selected = [
            row
            for row in all_rows
            if row["partition_id"] == input_row["partition_id"]
            and row["orientation"] == input_row["orientation"]
        ]
        target = [
            row
            for row in selected
            if row["rna_ref"] == target_ref and row["rna_alt"] == target_alt
        ]
        result.append(
            {
                "scope_type": "partition_orientation",
                "partition_id": input_row["partition_id"],
                "orientation": input_row["orientation"],
                "step07_declared_vcf_records": input_row["declared_vcf_record_count"],
                "step08_observed_vcf_records": input_row["observed_vcf_record_count"],
                "step08_observed_alt_alleles": input_row["observed_alt_allele_count"],
                "step08_supported_snvs": input_row["supported_snv_count"],
                "step08_skipped_symbolic": input_row["skipped_symbolic_count"],
                "step08_skipped_non_snv": input_row["skipped_non_snv_count"],
                "step08_published_candidates": input_row["published_candidate_count"],
                "step09_candidates": str(len(selected)),
                "step09_target_candidates": str(len(target)),
                "step09_tested": str(
                    step09.count_status(selected, "test_status", "tested")
                ),
                "step09_not_target": str(
                    step09.count_status(selected, "test_status", "not_target_change")
                ),
                "step09_missing_counts": str(
                    step09.count_status(selected, "test_status", "missing_counts")
                ),
                "step09_low_coverage": str(
                    step09.count_status(selected, "test_status", "low_coverage")
                ),
                "step09_degenerate": str(
                    step09.count_status(selected, "test_status", "degenerate_table")
                ),
                "step09_below_mean_dp": str(
                    step09.count_status(selected, "call_status", "below_mean_dp")
                ),
                "step09_background_not_passed": str(
                    step09.count_status(
                        selected, "call_status", "background_not_passed"
                    )
                ),
                "step09_fdr_not_met": str(
                    step09.count_status(selected, "call_status", "fdr_not_met")
                ),
                "step09_effect_not_met": str(
                    step09.count_status(selected, "call_status", "effect_not_met")
                ),
                "step09_significant_up": str(
                    step09.count_status(selected, "call_status", "significant_up")
                ),
                "step09_significant_down": str(
                    step09.count_status(selected, "call_status", "significant_down")
                ),
                "reconciliation_status": "reconciled",
            }
        )
    return result


def validate_qc_funnel(
    rows: Sequence[Mapping[str, str]],
    step08_inputs: Sequence[Mapping[str, str]],
    all_rows: Sequence[Mapping[str, str]],
    target_rna_change: str,
    complete: bool,
) -> None:
    seen: set[tuple[str, str]] = set()
    expected_by_scope = {
        (row["partition_id"], row["orientation"]): row
        for row in _expected_qc_rows(
            step08_inputs,
            all_rows,
            target_rna_change,
        )
    }
    compared_columns = tuple(
        column
        for column in review_package.QC_FUNNEL_HEADER
        if column
        not in (
            "review_id",
            "evidence_id",
            "analysis_id",
            "detail",
        )
    )
    for row in rows:
        scope = (row["partition_id"], row["orientation"])
        if scope in seen:
            step08.fail("QC funnel contains a duplicate partition/orientation scope.")
        seen.add(scope)
        expected = expected_by_scope.get(scope)
        if expected is None:
            step08.fail("QC funnel references an undeclared partition/orientation.")
        for column in compared_columns:
            if row[column] != expected[column]:
                step08.fail(
                    f"QC funnel {scope[0]}/{scope[1]} {column} does not reconcile."
                )
    if complete and seen != set(expected_by_scope):
        step08.fail("Complete QC funnel does not cover every partition/orientation.")


def validate_replicate_effects(
    rows: Sequence[Mapping[str, str]],
    candidates: Mapping[str, Mapping[str, str]],
    sample_rows: Sequence[Mapping[str, str]],
    summary: Mapping[str, str],
    complete: bool,
) -> None:
    replicates, pairs = step09.paired_samples(
        sample_rows,
        summary["control_condition"],
        summary["treatment_condition"],
    )
    seen: set[tuple[str, str]] = set()
    for row_number, row in enumerate(rows, start=2):
        result = validate_candidate_reference(
            f"Replicate-effects row {row_number}",
            row["candidate_id"],
            candidates,
        )
        if result["test_status"] != "tested":
            step08.fail(
                "Replicate-effects evidence may only summarize successfully "
                "tested candidates."
            )
        replicate = row["replicate"]
        if replicate not in replicates:
            step08.fail("Replicate-effects evidence references an unknown replicate.")
        key = (row["candidate_id"], replicate)
        if key in seen:
            step08.fail("Replicate-effects evidence contains a duplicate stratum row.")
        seen.add(key)
        control_sample, treatment_sample = pairs[replicate]
        if (
            row["control_sample"] != control_sample
            or row["treatment_sample"] != treatment_sample
        ):
            step08.fail("Replicate-effects sample pairing differs from the manifest.")
        if any(
            row[column] != result[column] for column in ("partition_id", "orientation")
        ):
            step08.fail("Replicate-effects candidate scope differs from Step 09.")
        for prefix, sample in (
            ("control", control_sample),
            ("treatment", treatment_sample),
        ):
            for metric in ("dp", "ad", "af"):
                if row[f"{prefix}_{metric}"] != result[f"{metric.upper()}__{sample}"]:
                    step08.fail(
                        "Replicate-effects counts differ from Step 09 "
                        f"for candidate {row['candidate_id']}."
                    )
        control_af = step08.parse_number(
            "Replicate-effects control_af", row["control_af"]
        )
        treatment_af = step08.parse_number(
            "Replicate-effects treatment_af", row["treatment_af"]
        )
        delta = step08.parse_number(
            "Replicate-effects treatment_control_difference",
            row["treatment_control_difference"],
        )
        if (
            control_af is None
            or treatment_af is None
            or delta is None
            or not values_close(delta, treatment_af - control_af)
        ):
            step08.fail("Replicate-effects treatment-control difference is invalid.")
        expected_direction = (
            "concordant_up"
            if delta > 0
            else ("concordant_down" if delta < 0 else "no_change")
        )
        if row["direction_status"] != expected_direction:
            step08.fail(
                "Replicate-effects direction_status conflicts with the "
                "treatment-control difference."
            )
        validate_iso_date("Replicate-effects review_date", row["review_date"])
    if complete:
        if not rows:
            step08.fail(
                "Complete replicate-effects evidence must contain at least "
                "one tested candidate."
            )
        candidate_replicates: dict[str, set[str]] = {}
        for candidate_id, replicate in seen:
            candidate_replicates.setdefault(candidate_id, set()).add(replicate)
        for candidate_id, observed in candidate_replicates.items():
            if observed != set(replicates):
                step08.fail(
                    "Complete replicate-effects evidence must cover every "
                    f"replicate for candidate {candidate_id}."
                )
