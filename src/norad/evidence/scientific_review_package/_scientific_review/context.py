"""Explicit input resolution and review-package context construction."""

from __future__ import annotations

import argparse
from pathlib import Path

from ._evidence_manifest import validate_evidence_manifest
from ._review_plan import validate_review_plan
from .contracts import review_package, step08, step09
from .evidence import make_review_summary, validate_evidence_payloads
from .intake import (
    Artifact,
    ReviewContext,
    artifact_from_binary,
    artifact_from_table,
    register_artifact,
    require_directory,
    step09_paths,
)


def build_context(
    arguments: argparse.Namespace,
) -> tuple[
    ReviewContext,
    dict[str, tuple[tuple[str, ...], list[dict[str, str]]]],
]:
    step08.validate_safe_id("review_id", arguments.review_id)
    artifacts: dict[str, Artifact] = {}
    input_hashes: dict[Path, str] = {}

    def register_table(key: str, label: str, table: step08.Table) -> None:
        """Register one validated table in both artifact and hash indexes."""
        register_artifact(
            artifacts, input_hashes, key, artifact_from_table(label, table)
        )

    plan_table, plan, _allowed_analyses = validate_review_plan(
        arguments.review_plan, arguments.review_id
    )
    register_table("review_plan", "Scientific review plan", plan_table)
    sample_table, sample_ids, sample_rows = step08.validate_sample_manifest(
        arguments.sample_manifest
    )
    register_table("sample_manifest", "Sample manifest", sample_table)
    partition_table = step08.validate_partition_manifest(arguments.partition_manifest)
    register_table("partition_manifest", "Partition manifest", partition_table)
    sample_hash = artifacts["sample_manifest"].sha256
    partition_hash = artifacts["partition_manifest"].sha256

    step08_inputs = step08.validate_step08_inputs(
        arguments.step08_inputs,
        sample_ids,
        partition_table.rows,
        sample_hash,
        partition_hash,
    )
    register_table("step08_inputs", "Step 08 input receipt", step08_inputs)
    step08_sites = step08.validate_step08_sites(
        arguments.step08_sites,
        sample_ids,
        partition_table.rows,
        step08_inputs.rows,
    )
    register_table("step08_sites", "Step 08 sites table", step08_sites)
    step08_summary = step08.validate_step08_summary(
        arguments.step08_summary,
        sample_ids,
        partition_table.rows,
        step08_inputs.rows,
        step08_sites.rows,
        sample_hash,
        partition_hash,
    )
    register_table("step08_summary", "Step 08 summary", step08_summary)

    analysis_dir = require_directory(
        "Step 09 analysis directory", arguments.step09_analysis_dir
    )
    analysis_id = plan["primary_analysis_id"]
    if analysis_dir.name != analysis_id:
        step08.fail(
            "Step 09 analysis directory basename must equal primary_analysis_id."
        )
    paths = step09_paths(analysis_dir, analysis_id)
    all_sites = step09.validate_step09_results(
        "Step 09 all-sites",
        paths["step09_all_sites"],
        sample_ids,
        analysis_id,
        step08_sites.rows,
    )
    if [row["candidate_id"] for row in all_sites.rows] != [
        row["candidate_id"] for row in step08_sites.rows
    ]:
        step08.fail("Step 09 all-sites candidate order/universe differs from Step 08.")
    register_table("step09_all_sites", "Step 09 all-sites", all_sites)
    significant = step09.validate_step09_results(
        "Step 09 significant-sites",
        paths["step09_significant_sites"],
        sample_ids,
        analysis_id,
        step08_sites.rows,
    )
    step09.validate_significant_subset(all_sites.rows, significant.rows)
    register_table("step09_significant_sites", "Step 09 significant-sites", significant)
    step09_summary_table = step09.validate_step09_summary(
        paths["step09_summary"],
        analysis_id,
        step08_inputs.rows[0]["cohort_id"],
        sample_ids,
        sample_rows,
        all_sites.rows,
        sample_table.path,
        partition_table.path,
        step08_sites.path,
        step08_inputs.path,
        sample_hash,
        partition_hash,
        artifacts["step08_sites"].sha256,
        artifacts["step08_inputs"].sha256,
        step08_inputs.rows[0]["orientation_policy"],
    )
    step09.validate_step09_result_semantics(
        all_sites.rows, step09_summary_table.rows[0], sample_rows
    )
    register_table("step09_summary", "Step 09 summary", step09_summary_table)
    mutation = step09.validate_mutation_spectrum(
        paths["step09_mutation_spectrum"], analysis_id, all_sites.rows
    )
    register_table("step09_mutation_spectrum", "Step 09 mutation spectrum", mutation)
    for key, label in (
        ("step09_mutation_spectrum_pdf", "Step 09 mutation-spectrum PDF"),
        ("step09_depth_delta_pdf", "Step 09 depth-delta PDF"),
    ):
        pdf_path = step08.require_file(label, paths[key])
        step09.validate_pdf(label, pdf_path)
        register_artifact(
            artifacts,
            input_hashes,
            key,
            artifact_from_binary(label, pdf_path),
        )
    if plan["orientation_policy"] != step09_summary_table.rows[0]["orientation_policy"]:
        step08.fail("Scientific review plan orientation policy differs from Step 09.")

    evidence_manifest, evidence_rows, category_rows, evidence_index = (
        validate_evidence_manifest(
            arguments.evidence_manifest,
            arguments.review_id,
            plan,
            input_hashes,
        )
    )
    register_table(
        "evidence_manifest", "Scientific evidence manifest", evidence_manifest
    )

    output_dir = (
        Path(arguments.output_root).expanduser().resolve() / arguments.review_id
    )
    output_paths = {
        key: output_dir / f"{arguments.review_id}.{suffix}"
        for key, suffix in review_package.OUTPUT_SUFFIXES
    }
    context = ReviewContext(
        review_id=arguments.review_id,
        plan=plan,
        evidence_rows=evidence_rows,
        category_rows=category_rows,
        evidence_index_rows=evidence_index,
        artifacts=artifacts,
        input_hashes=input_hashes,
        sample_ids=sample_ids,
        sample_rows=sample_rows,
        partition_rows=partition_table.rows,
        step08_input_rows=step08_inputs.rows,
        step08_site_rows=step08_sites.rows,
        step09_all_rows=all_sites.rows,
        step09_significant_rows=significant.rows,
        step09_summary=step09_summary_table.rows[0],
        output_paths=output_paths,
    )
    decisions, selected, adjudicated = validate_evidence_payloads(
        arguments.review_id,
        plan,
        evidence_rows,
        category_rows,
        sample_ids,
        sample_rows,
        partition_table.rows,
        step08_inputs.rows,
        all_sites.rows,
        step09_summary_table.rows[0],
        step09_summary_table.path,
        input_hashes,
    )
    summary_row = make_review_summary(
        context, decisions, selected, adjudicated, analysis_dir
    )
    output_tables: dict[str, tuple[tuple[str, ...], list[dict[str, str]]]] = {
        "review_plan": (review_package.REVIEW_PLAN_HEADER, [dict(plan)]),
        "evidence_index": (review_package.EVIDENCE_INDEX_HEADER, evidence_index),
    }
    for category in review_package.CATEGORY_ORDER:
        output_tables[category] = (
            review_package.CATEGORY_HEADERS[category],
            category_rows[category],
        )
    output_tables["review_summary"] = (
        review_package.REVIEW_SUMMARY_HEADER,
        [summary_row],
    )
    if tuple(output_tables) != tuple(key for key, _ in review_package.OUTPUT_SUFFIXES):
        step08.fail("Internal Step 09c output ordering is inconsistent.")
    return context, output_tables
