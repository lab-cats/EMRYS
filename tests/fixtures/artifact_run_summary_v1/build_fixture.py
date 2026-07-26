#!/usr/bin/env python3
"""Build temporary artifact-run-summary fixtures from production contracts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "artifact_adapters_v1"
    / "build_fixture.py"
)
STEP09C_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "step09c" / "build_fixture.py"
)
FIXED_EPOCH = "1700000000"
REPORT_TABLE_APPROVALS_HEADER = (
    "run_id",
    "run_contract_sha256",
    "table_id",
    "artifact_id",
    "role",
    "title",
    "path",
    "sha256",
    "row_count",
    "display_row_limit",
    "approval_status",
    "approval_policy_version",
    "approved_by",
    "approved_at",
)


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load fixture module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER_FIXTURE = load_module(
    "norad_run_summary_adapter_fixture",
    ADAPTER_FIXTURE_PATH,
)
STEP09C_FIXTURE = load_module(
    "norad_run_summary_step09c_fixture",
    STEP09C_FIXTURE_PATH,
)
ADAPTER = ADAPTER_FIXTURE.ADAPTER
STEP09C = STEP09C_FIXTURE.CONTRACT


@dataclass(frozen=True)
class RunSummaryFixture:
    """Paths for one committed artifact transaction and its summary outputs."""

    root: Path
    run_id: str
    artifact_receipt: Path
    output_root: Path
    adapter_fixture: Any
    science_review_summary: Path | None = None
    step09c_fixture: Any | None = None
    report_table_approvals: Path | None = None

    @property
    def output_dir(self) -> Path:
        return self.output_root / self.run_id

    @property
    def summary_json_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.run_summary.json"

    @property
    def summary_tsv_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.run_summary.tsv"

    @property
    def qc_summary_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.qc_summary.tsv"

    @property
    def summary_receipt_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.run_summary_receipt.tsv"

    @property
    def lock_path(self) -> Path:
        return self.output_dir / f".{self.run_id}.run-summary.lock"

    @property
    def summary_paths(self) -> tuple[Path, ...]:
        return (
            self.summary_json_path,
            self.summary_tsv_path,
            self.qc_summary_path,
            self.summary_receipt_path,
        )

    def command_args(
        self,
        *,
        execute: bool = False,
        include_science: bool | None = None,
        include_approvals: bool | None = None,
    ) -> list[str]:
        arguments = [
            "--run-id",
            self.run_id,
            "--artifact-receipt",
            str(self.artifact_receipt),
            "--output-root",
            str(self.output_root),
        ]
        use_science = (
            self.science_review_summary is not None
            if include_science is None
            else include_science
        )
        if use_science:
            if self.science_review_summary is None:
                raise ValueError("Fixture has no science-review summary")
            arguments.extend(
                [
                    "--science-review-summary",
                    str(self.science_review_summary),
                ]
            )
        use_approvals = (
            self.report_table_approvals is not None
            if include_approvals is None
            else include_approvals
        )
        if use_approvals:
            if self.report_table_approvals is None:
                raise ValueError("Fixture has no report-table approvals")
            arguments.extend(
                [
                    "--report-table-approvals",
                    str(self.report_table_approvals),
                ]
            )
        if execute:
            arguments.append("--execute")
        return arguments


def fixed_epoch() -> tuple[str | None, str]:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    return previous, FIXED_EPOCH


def restore_epoch(previous: str | None) -> None:
    if previous is None:
        os.environ.pop("SOURCE_DATE_EPOCH", None)
    else:
        os.environ["SOURCE_DATE_EPOCH"] = previous


def publish_adapter_fixture(fixture: Any) -> None:
    previous, _ = fixed_epoch()
    try:
        context = ADAPTER.prepare_context(
            argparse.Namespace(
                run_id=fixture.run_id,
                run_contract=fixture.run_contract,
                inventory=fixture.inventory,
                output_root=fixture.output_root,
                execute=True,
            )
        )
        ADAPTER.publish_context(context)
    finally:
        restore_epoch(previous)


def build_fixture(
    root: Path,
    *,
    run_id: str = "synthetic_run",
) -> RunSummaryFixture:
    """Build the full default 67-record adapter transaction."""

    root = root.resolve()
    adapter_fixture = ADAPTER_FIXTURE.build_fixture(
        root / "adapter_fixture",
        run_id=run_id,
    )
    publish_adapter_fixture(adapter_fixture)
    return RunSummaryFixture(
        root=root,
        run_id=run_id,
        artifact_receipt=adapter_fixture.receipt_path,
        output_root=adapter_fixture.output_root,
        adapter_fixture=adapter_fixture,
    )


def build_missing_fixture(
    root: Path,
    *,
    run_id: str = "missing_artifact_run",
    artifact_id: str = "sample.SYNTH_A.canonical_bai",
) -> RunSummaryFixture:
    """Build a complete adapter transaction with one required source missing."""

    root = root.resolve()
    adapter_fixture = ADAPTER_FIXTURE.build_fixture(
        root / "adapter_fixture",
        run_id=run_id,
    )
    adapter_fixture.source_for(artifact_id).unlink()
    publish_adapter_fixture(adapter_fixture)
    return RunSummaryFixture(
        root=root,
        run_id=run_id,
        artifact_receipt=adapter_fixture.receipt_path,
        output_root=adapter_fixture.output_root,
        adapter_fixture=adapter_fixture,
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Mapping[str, str]) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_tsv(
    path: Path,
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def write_run_contract(
    path: Path,
    *,
    sample_manifest_sha256: str,
    partition_manifest_sha256: str,
    primary_analysis_id: str,
) -> dict[str, str]:
    policy = {
        "analysis_id": primary_analysis_id,
        "orientation_policy": "legacy_provisional_v1",
        "target_rna_change": "A>G",
    }
    components = {
        "sample_manifest_sha256": sample_manifest_sha256,
        "reference_contract_sha256": canonical_sha256(
            {"reference": "synthetic_step09c_reference"}
        ),
        "partition_manifest_sha256": partition_manifest_sha256,
        "primary_analysis_id": primary_analysis_id,
        "primary_analysis_policy_sha256": canonical_sha256(policy),
    }
    document = {
        "run_contract_sha256": ADAPTER_FIXTURE.canonical_run_contract_sha256(
            components
        ),
        **components,
    }
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return document


def explicit_science_inventory_rows(
    fixture: Any,
) -> list[dict[str, str]]:
    cohort_id = STEP09C_FIXTURE.COHORT_ID
    analysis_id = STEP09C_FIXTURE.PRIMARY_ANALYSIS_ID
    review_id = fixture.review_id
    step09_dir = fixture.step09_analysis_dir
    review_dir = fixture.output_root / review_id
    rows: list[dict[str, str]] = [
        {
            "artifact_id": f"cohort.{cohort_id}.step08_sites",
            "step_id": "08",
            "scope_type": "cohort",
            "scope_id": cohort_id,
            "adapter": "step08_sites_v1",
            "source_path": str(fixture.step08_sites),
            "required": "true",
        },
        {
            "artifact_id": f"cohort.{cohort_id}.step08_inputs",
            "step_id": "08",
            "scope_type": "cohort",
            "scope_id": cohort_id,
            "adapter": "step08_inputs_v1",
            "source_path": str(fixture.step08_inputs),
            "required": "true",
        },
        {
            "artifact_id": f"cohort.{cohort_id}.step08_summary",
            "step_id": "08",
            "scope_type": "cohort",
            "scope_id": cohort_id,
            "adapter": "step08_summary_v1",
            "source_path": str(fixture.step08_summary),
            "required": "true",
        },
    ]
    step09_sources = (
        (
            "cmh_all_sites",
            "step09_cmh_all_sites_v1",
            step09_dir / f"{analysis_id}.cmh_all_sites.tsv",
        ),
        (
            "cmh_significant_sites",
            "step09_cmh_significant_sites_v1",
            step09_dir / f"{analysis_id}.cmh_significant_sites.tsv",
        ),
        (
            "cmh_summary",
            "step09_cmh_summary_v1",
            step09_dir / f"{analysis_id}.cmh_summary.tsv",
        ),
        (
            "mutation_spectrum_tsv",
            "step09_mutation_spectrum_tsv_v1",
            step09_dir / f"{analysis_id}.mutation_spectrum.tsv",
        ),
        (
            "mutation_spectrum_pdf",
            "step09_mutation_spectrum_pdf_v1",
            step09_dir / f"{analysis_id}.mutation_spectrum.pdf",
        ),
        (
            "depth_delta_pdf",
            "step09_depth_delta_pdf_v1",
            step09_dir / f"{analysis_id}.depth_delta.pdf",
        ),
    )
    rows.extend(
        {
            "artifact_id": f"analysis.{analysis_id}.{suffix}",
            "step_id": "09",
            "scope_type": "analysis",
            "scope_id": analysis_id,
            "adapter": adapter,
            "source_path": str(source),
            "required": "true",
        }
        for suffix, adapter, source in step09_sources
    )
    for key, suffix in STEP09C.OUTPUT_SUFFIXES:
        rows.append(
            {
                "artifact_id": f"review.{review_id}.{key}",
                "step_id": "09c",
                "scope_type": "scientific_review",
                "scope_id": review_id,
                "adapter": f"step09c_{key}_v1",
                "source_path": str(review_dir / f"{review_id}.{suffix}"),
                "required": "true",
            }
        )
    return rows


def normalize_explicit_science_transaction(
    fixture: RunSummaryFixture,
) -> None:
    """Promote the synthetic 08/09/09c records for summary-only testing.

    The Step 09c fixture deliberately uses minimal Step 07 and PDF sources.
    Native adapter group reconciliation therefore records downstream scopes
    as failed/incomplete even though Step 09c itself validates and publishes
    all 13 tables. This synthetic-only normalization isolates run-summary
    science normalization from those upstream adapter-fixture limitations. It
    does not weaken or alter production adapter validation.
    """

    summary_path = fixture.science_review_summary
    if summary_path is None:
        raise RuntimeError("Explicit-science fixture lacks a review summary")
    summary_rows = read_tsv(summary_path)
    if len(summary_rows) != 1:
        raise RuntimeError("Expected one Step 09c review-summary row")
    summary = summary_rows[0]
    science_state = {
        "overall_status": summary["overall_science_status"],
        "orientation_status": summary["orientation_status"],
        "orientation_policy": summary["orientation_policy"],
        "review_id": summary["review_id"],
    }

    records: list[dict[str, Any]] = []
    record_bytes: list[bytes] = []
    for inventory_row in fixture.adapter_fixture.inventory_rows:
        record_path = (
            fixture.adapter_fixture.records_dir
            / f"{inventory_row['artifact_id']}.json"
        )
        record = ADAPTER.contracts.load_json_object(
            record_path,
            f"fixture artifact {inventory_row['artifact_id']}",
        )
        record["completion_status"] = "complete"
        record["state_reason"] = None
        record["warnings"] = []
        record["errors"] = []
        if record["scope"]["step_id"] == "09c":
            record["scientific_state"] = dict(science_state)
        payload = ADAPTER.canonical_json_bytes(record)
        record_path.write_bytes(payload)
        records.append(record)
        record_bytes.append(payload)

    index_rows = ADAPTER.build_index_rows(
        records=records,
        record_bytes=record_bytes,
        records_dir=fixture.adapter_fixture.records_dir,
    )
    index_bytes = ADAPTER.tsv_bytes(ADAPTER.ARTIFACT_INDEX_HEADER, index_rows)
    fixture.adapter_fixture.artifacts_path.write_bytes(index_bytes)

    old_receipt_rows = read_tsv(fixture.adapter_fixture.receipt_path)
    if len(old_receipt_rows) != 1:
        raise RuntimeError("Expected one adapter receipt row")
    old_receipt = old_receipt_rows[0]
    attempt_history = old_receipt["adapter_attempt_history"].split(",")
    attempt_id = attempt_history[-1]
    previous_attempt_id = (
        attempt_history[-2] if len(attempt_history) > 1 else None
    )
    run_contract = ADAPTER.contracts.load_json_object(
        fixture.adapter_fixture.run_contract,
        "explicit-science run contract",
    )
    receipt_row = ADAPTER.build_receipt_row(
        run_id=fixture.run_id,
        run_contract=run_contract,
        run_contract_path=fixture.adapter_fixture.run_contract,
        run_contract_file_sha256=sha256_file(
            fixture.adapter_fixture.run_contract
        ),
        inventory_path=fixture.adapter_fixture.inventory,
        inventory_sha256=sha256_file(fixture.adapter_fixture.inventory),
        inventory_row_count=len(fixture.adapter_fixture.inventory_rows),
        artifacts_path=fixture.adapter_fixture.artifacts_path,
        index_bytes=index_bytes,
        index_rows=index_rows,
        attempt_id=attempt_id,
        previous_attempt_id=previous_attempt_id,
        attempt_history=attempt_history[:-1],
        git_commit=old_receipt["git_commit"],
        started_at=old_receipt["started_at"],
        finished_at=old_receipt["finished_at"],
    )
    fixture.adapter_fixture.receipt_path.write_bytes(
        ADAPTER.tsv_bytes(ADAPTER.ARTIFACT_RECEIPT_HEADER, [receipt_row])
    )
    ADAPTER.validate_published_transaction(
        run_id=fixture.run_id,
        run_contract=run_contract,
        run_contract_path=fixture.adapter_fixture.run_contract,
        run_contract_file_sha256=sha256_file(
            fixture.adapter_fixture.run_contract
        ),
        inventory_path=fixture.adapter_fixture.inventory,
        inventory_sha256=sha256_file(fixture.adapter_fixture.inventory),
        inventory_rows=fixture.adapter_fixture.inventory_rows,
        records_dir=fixture.adapter_fixture.records_dir,
        artifacts_path=fixture.adapter_fixture.artifacts_path,
        receipt_path=fixture.adapter_fixture.receipt_path,
        require_current_source_locations=True,
    )


def build_explicit_science_fixture(
    root: Path,
    *,
    science_status: str = "evidence_incomplete",
    run_id: str | None = None,
    missing_categories: bool = False,
    mixed_categories: bool = False,
    mixed_computational: bool = False,
    computational_scope_bundle: bool = False,
    human_names: bool = False,
    empty_candidate_selection: bool = False,
) -> RunSummaryFixture:
    """Build a Step 08/09/09c adapter transaction with explicit science."""

    root = root.resolve()
    step09c_fixture = STEP09C_FIXTURE.build_fixture(
        root / "step09c_fixture",
        science_status,
    )
    if missing_categories and mixed_categories:
        raise ValueError(
            "missing_categories and mixed_categories are mutually exclusive"
        )
    if computational_scope_bundle and mixed_computational:
        raise ValueError(
            "computational_scope_bundle and mixed_computational are "
            "mutually exclusive"
        )
    if (
        missing_categories
        or mixed_categories
        or mixed_computational
        or computational_scope_bundle
        or human_names
        or empty_candidate_selection
    ):
        if science_status != "evidence_incomplete":
            raise ValueError(
                "incomplete evidence variants require evidence_incomplete"
            )
        with step09c_fixture.evidence_manifest.open(
            encoding="utf-8", newline=""
        ) as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            evidence_rows = list(reader)
    if computational_scope_bundle or human_names or empty_candidate_selection:
        plan_rows = read_tsv(step09c_fixture.review_plan)
        if len(plan_rows) != 1:
            raise RuntimeError("Expected one Step 09c review-plan row")
        if computational_scope_bundle:
            plan_rows[0].update(
                {
                    "runtime_validation_status": "passed",
                    "cluster_dry_run_status": "passed",
                    "cluster_proof_status": "proven",
                }
            )
        if human_names:
            plan_rows[0].update(
                {
                    "reviewer": "Jane Doe",
                    "decision_owner": "Scientific Review Team",
                    "git_commit": "local_build",
                }
            )
        if empty_candidate_selection:
            plan_rows[0].update(
                {
                    "top_up_count": "0",
                    "top_down_count": "0",
                    "discordant_count": "0",
                    "near_threshold_count": "0",
                }
            )
        write_tsv(
            step09c_fixture.review_plan,
            STEP09C.REVIEW_PLAN_HEADER,
            plan_rows,
        )
    if empty_candidate_selection:
        empty_categories = (
            (
                "candidate_selection",
                "e_selection",
                STEP09C.CANDIDATE_SELECTION_HEADER,
            ),
            (
                "candidate_adjudication",
                "e_adjudication",
                STEP09C.CANDIDATE_ADJUDICATION_HEADER,
            ),
        )
        for category, evidence_id, header in empty_categories:
            source_path = (
                step09c_fixture.root / "evidence" / f"{category}.tsv"
            )
            write_tsv(source_path, header, [])
            manifest_row = next(
                row
                for row in evidence_rows
                if row["evidence_id"] == evidence_id
            )
            manifest_row["source_sha256"] = sha256_file(source_path)
            manifest_row["source_row_count"] = "0"
    if missing_categories:
        for row in evidence_rows:
            if row["evidence_category"] == "computational_validation":
                continue
            row.update(
                {
                    "source_path": "NA",
                    "source_sha256": "NA",
                    "source_row_count": "NA",
                    "evidence_status": "missing",
                    "not_applicable_reason": "NA",
                    "evidence_date": "NA",
                }
            )
    elif mixed_categories:
        complete = next(
            row
            for row in evidence_rows
            if row["evidence_category"] == "qc_funnel"
        )
        missing = {
            **complete,
            "evidence_id": "e_qc_funnel_missing",
            "source_path": "NA",
            "source_sha256": "NA",
            "source_row_count": "NA",
            "evidence_status": "missing",
            "not_applicable_reason": "NA",
            "evidence_date": "NA",
        }
        not_applicable = {
            **complete,
            "evidence_id": "e_qc_funnel_not_applicable",
            "source_path": "NA",
            "source_sha256": "NA",
            "source_row_count": "NA",
            "evidence_status": "not_applicable",
            "not_applicable_reason": (
                "Synthetic evidence dimension is not applicable."
            ),
            "evidence_date": "NA",
        }
        evidence_rows.extend((missing, not_applicable))
    if mixed_computational:
        complete_computational = next(
            row
            for row in evidence_rows
            if row["evidence_category"] == "computational_validation"
        )
        evidence_rows.extend(
            (
                {
                    **complete_computational,
                    "evidence_id": "e_computational_missing",
                    "source_path": "NA",
                    "source_sha256": "NA",
                    "source_row_count": "NA",
                    "evidence_status": "missing",
                    "not_applicable_reason": "NA",
                    "evidence_date": "NA",
                },
                {
                    **complete_computational,
                    "evidence_id": "e_computational_not_applicable",
                    "source_path": "NA",
                    "source_sha256": "NA",
                    "source_row_count": "NA",
                    "evidence_status": "not_applicable",
                    "not_applicable_reason": (
                        "Synthetic runtime dimension is not applicable."
                    ),
                    "evidence_date": "NA",
                },
            )
        )
    if human_names:
        for row in evidence_rows:
            row["reviewer"] = "Jane Doe"
            row["owner"] = "Scientific Review Team"
        decisions_path = (
            step09c_fixture.root / "evidence" / "decisions.tsv"
        )
        decision_rows = read_tsv(decisions_path)
        for row in decision_rows:
            row["decision_owner"] = "Jane Doe"
        write_tsv(
            decisions_path,
            STEP09C.DECISIONS_HEADER,
            decision_rows,
        )
        decisions_manifest = next(
            row for row in evidence_rows if row["evidence_id"] == "e_decisions"
        )
        decisions_manifest["source_sha256"] = sha256_file(decisions_path)
        decisions_manifest["source_row_count"] = str(len(decision_rows))
    if computational_scope_bundle:
        computational_path = (
            step09c_fixture.root
            / "evidence"
            / "computational_validation.tsv"
        )
        computational_rows = read_tsv(computational_path)
        if len(computational_rows) != 1:
            raise RuntimeError(
                "Expected one initial computational-validation row"
            )
        evidence_dir = step09c_fixture.root / "computational_evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        scope_specs = (
            (
                "local_fixture_tests",
                "passed",
                "local-tests.log",
            ),
            (
                "runtime_log",
                "passed",
                "runtime.log",
            ),
            (
                "runtime_output",
                "passed",
                "runtime-output.tsv",
            ),
            (
                "cluster_dry_run",
                "passed",
                "cluster-dry-run.log",
            ),
            (
                "cluster_scheduler",
                "proven",
                "cluster-scheduler.tsv",
            ),
            (
                "cluster_log",
                "proven",
                "cluster.log",
            ),
            (
                "cluster_output",
                "proven",
                "cluster-output.tsv",
            ),
        )
        bundled_rows = []
        for scope, status, filename in scope_specs:
            evidence_path = evidence_dir / filename
            evidence_path.write_text(
                f"Synthetic {scope} evidence only.\n",
                encoding="utf-8",
            )
            bundled_rows.append(
                {
                    **computational_rows[0],
                    "validation_scope": scope,
                    "validation_status": status,
                    "evidence_path": str(evidence_path),
                    "evidence_sha256": sha256_file(evidence_path),
                    "scheduler_state": "COMPLETED",
                    "exit_code": "0",
                    "notes": (
                        f"Synthetic {scope} contract evidence; not "
                        "production validation."
                    ),
                }
            )
        write_tsv(
            computational_path,
            STEP09C.COMPUTATIONAL_VALIDATION_HEADER,
            bundled_rows,
        )
        computational_manifest = next(
            row
            for row in evidence_rows
            if row["evidence_id"] == "e_computational"
        )
        computational_manifest["source_sha256"] = sha256_file(
            computational_path
        )
        computational_manifest["source_row_count"] = str(len(bundled_rows))
    if (
        missing_categories
        or mixed_categories
        or mixed_computational
        or computational_scope_bundle
        or human_names
        or empty_candidate_selection
    ):
        write_tsv(
            step09c_fixture.evidence_manifest,
            STEP09C.EVIDENCE_MANIFEST_HEADER,
            evidence_rows,
        )
    arguments = STEP09C.parse_arguments(
        [*step09c_fixture.command_args(), "--execute"]
    )
    context, output_tables = STEP09C.build_context(arguments)
    STEP09C.publish_outputs(context, output_tables)

    resolved_run_id = run_id or (
        "science_exploratory_run"
        if science_status == "science_review_complete_exploratory"
        else "science_incomplete_run"
    )
    adapter_root = root / "adapter_fixture"
    adapter_root.mkdir(parents=True, exist_ok=True)
    inventory = adapter_root / "artifact_inventory.tsv"
    run_contract = adapter_root / "run_contract.json"
    rows = explicit_science_inventory_rows(step09c_fixture)
    write_tsv(inventory, ADAPTER.contracts.INVENTORY_HEADER, rows)
    write_run_contract(
        run_contract,
        sample_manifest_sha256=sha256_file(step09c_fixture.sample_manifest),
        partition_manifest_sha256=sha256_file(
            step09c_fixture.partition_manifest
        ),
        primary_analysis_id=STEP09C_FIXTURE.PRIMARY_ANALYSIS_ID,
    )
    output_root = root / "artifacts"
    adapter_fixture = ADAPTER_FIXTURE.FixturePaths(
        root=adapter_root,
        run_id=resolved_run_id,
        run_contract=run_contract,
        inventory=inventory,
        source_root=step09c_fixture.root,
        output_root=output_root,
        inventory_rows=tuple(rows),
        source_paths={
            row["artifact_id"]: Path(row["source_path"]) for row in rows
        },
    )
    publish_adapter_fixture(adapter_fixture)
    science_review_summary = (
        step09c_fixture.output_root
        / step09c_fixture.review_id
        / (
            f"{step09c_fixture.review_id}."
            "step09c_review_summary.tsv"
        )
    )
    fixture = RunSummaryFixture(
        root=root,
        run_id=resolved_run_id,
        artifact_receipt=adapter_fixture.receipt_path,
        output_root=output_root,
        adapter_fixture=adapter_fixture,
        science_review_summary=science_review_summary,
        step09c_fixture=step09c_fixture,
    )
    normalize_explicit_science_transaction(fixture)
    review_records = [
        ADAPTER.contracts.load_json_object(
            adapter_fixture.records_dir / f"{row['artifact_id']}.json",
            f"normalized fixture artifact {row['artifact_id']}",
        )
        for row in rows
        if row["step_id"] == "09c"
    ]
    if len(review_records) != 13 or any(
        record["completion_status"] != "complete"
        or record["scientific_state"] is None
        for record in review_records
    ):
        raise RuntimeError(
            "Explicit-science fixture did not normalize all 13 review records"
        )
    return fixture


def add_report_table_approvals(
    fixture: RunSummaryFixture,
    *,
    roles: Sequence[str] = (
        "candidate_selection",
        "candidate_adjudication",
    ),
    display_limits: Mapping[str, int | None] | None = None,
) -> RunSummaryFixture:
    """Attach exact run-bound approvals for published Step 09c artifacts."""

    run_contract = json.loads(
        fixture.adapter_fixture.run_contract.read_text(encoding="utf-8")
    )
    limits = dict(display_limits or {})
    rows: list[dict[str, str]] = []
    for role in roles:
        expected_adapter = f"step09c_{role}_v1"
        matching = [
            row
            for row in fixture.adapter_fixture.inventory_rows
            if row["adapter"] == expected_adapter
        ]
        if len(matching) != 1:
            raise RuntimeError(
                f"Expected one fixture artifact for {expected_adapter}"
            )
        artifact_id = matching[0]["artifact_id"]
        record = ADAPTER.contracts.load_json_object(
            fixture.adapter_fixture.records_dir / f"{artifact_id}.json",
            f"approval fixture artifact {artifact_id}",
        )
        source = record["source"]
        if (
            record["completion_status"] != "complete"
            or source is None
            or source["media_type"] != "text/tab-separated-values"
            or source["row_count"] is None
        ):
            raise RuntimeError(
                f"Approval fixture artifact is not a complete TSV: {artifact_id}"
            )
        display_limit = limits.get(role)
        rows.append(
            {
                "run_id": fixture.run_id,
                "run_contract_sha256": run_contract[
                    "run_contract_sha256"
                ],
                "table_id": f"synthetic_{role}",
                "artifact_id": artifact_id,
                "role": role,
                "title": f"Synthetic {role.replace('_', ' ')}",
                "path": source["path"],
                "sha256": source["sha256"],
                "row_count": str(source["row_count"]),
                "display_row_limit": (
                    "NA" if display_limit is None else str(display_limit)
                ),
                "approval_status": "approved",
                "approval_policy_version": "synthetic_report_policy_v1",
                "approved_by": "synthetic_scientific_owner",
                "approved_at": "2023-11-14T22:13:20Z",
            }
        )
    approvals_path = fixture.root / "report_table_approvals.tsv"
    write_tsv(
        approvals_path,
        REPORT_TABLE_APPROVALS_HEADER,
        rows,
    )
    return replace(
        fixture,
        report_table_approvals=approvals_path,
    )


def build_approved_science_fixture(
    root: Path,
    *,
    science_status: str = "evidence_incomplete",
    roles: Sequence[str] = (
        "candidate_selection",
        "candidate_adjudication",
    ),
    display_limits: Mapping[str, int | None] | None = None,
    header_only_roles: Sequence[str] = (),
) -> RunSummaryFixture:
    fixture = build_explicit_science_fixture(
        root,
        science_status=science_status,
        empty_candidate_selection=(
            "candidate_selection" in header_only_roles
        ),
    )
    unsupported_header_only = set(header_only_roles) - {
        "candidate_selection"
    }
    if unsupported_header_only:
        raise ValueError(
            "Unsupported header-only fixture roles: "
            + ", ".join(sorted(unsupported_header_only))
        )
    return add_report_table_approvals(
        fixture,
        roles=roles,
        display_limits=display_limits,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an artifact-run-summary synthetic fixture."
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument(
        "--science-status",
        choices=("none", *STEP09C_FIXTURE.SCIENCE_STATUSES),
        default="none",
    )
    arguments = parser.parse_args()
    if arguments.science_status == "none":
        fixture = build_fixture(arguments.root)
    else:
        fixture = build_explicit_science_fixture(
            arguments.root,
            science_status=arguments.science_status,
        )
    print(f"Artifact receipt: {fixture.artifact_receipt}")
    print(f"Run-summary output root: {fixture.output_root}")
    if fixture.science_review_summary is not None:
        print(f"Science-review summary: {fixture.science_review_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
