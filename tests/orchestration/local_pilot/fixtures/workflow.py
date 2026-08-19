"""Materialize one no-science fixture for the fixed Snakemake projection."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from norad.contracts.orchestration import api as orchestration_contracts
from norad.contracts.orchestration.projection import build_reporting_bundle
from norad.contracts.scientific_evidence import scientific_context, step08, step09
from norad.libraries.source_authority import controlled_python_argv
from norad.orchestration.local_pilot import inspection
from norad.orchestration.local_pilot.lifecycle import build_snakemake_argv
from norad.orchestration.local_pilot.normalization import normalize_request
from norad.reporting._artifact_index.registry import ADAPTER_REGISTRY
from tests.reporting.fixtures.artifact_adapters_v1.build_fixture import (
    minimal_bai_bytes,
    minimal_bam_bytes,
    minimal_pdf_bytes,
)
from tests.orchestration.local_pilot.fixture import build as build_intake
from tests.scientific_context_test_support import build_transaction

REPO_ROOT = Path(__file__).resolve().parents[4]
PROFILE_PATH = REPO_ROOT / "workflow" / "contracts" / "local_cmh_v2.json"
SNAKEFILE = REPO_ROOT / "workflow" / "Snakefile"
WORKFLOW_PROFILE = REPO_ROOT / "workflow" / "profiles" / "local" / "profile.v9+.yaml"
TASK_DOUBLE = Path(__file__).with_name("task_double.py").resolve()
OWNER_ARTIFACT_DOUBLE = Path(__file__).with_name("owner_artifact_double.py").resolve()


def source_checkout_commit() -> str:
    """Return the live checkout commit used by source-attested child fixtures."""

    return subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@dataclass(frozen=True, slots=True)
class WorkflowFixture:
    """Paths and identities for one isolated workflow test run."""

    root: Path
    run_root: Path
    config_path: Path
    execution: dict[str, Any]
    profile: dict[str, Any]
    dispatch_paths: dict[str, dict[str, str]]
    workflow_attempt_path: Path

    @property
    def verified_root(self) -> Path:
        return self.run_root / "state" / "verified"

    @property
    def reporting_root(self) -> Path:
        return self.run_root / "state" / "reporting"

    def reporting_start(self, kind: str) -> Path:
        return self.reporting_root / kind / "start.json"

    def reporting_verified(self, kind: str) -> Path:
        return self.reporting_root / kind / "verified.json"

    @property
    def artifact_receipt(self) -> Path:
        run_id = str(self.execution["run_id"])
        return (
            self.run_root
            / "products"
            / "artifact-summary"
            / run_id
            / f"{run_id}.artifact_receipt.tsv"
        )

    @property
    def run_summary(self) -> Path:
        run_id = str(self.execution["run_id"])
        return self.artifact_receipt.parent / f"{run_id}.run_summary.json"

    @property
    def run_summary_receipt(self) -> Path:
        run_id = str(self.execution["run_id"])
        return self.artifact_receipt.parent / f"{run_id}.run_summary_receipt.tsv"

    @property
    def report_receipt(self) -> Path:
        run_id = str(self.execution["run_id"])
        return (
            self.run_root
            / "products"
            / "report"
            / run_id
            / f"{run_id}.report_outputs.tsv"
        )


def _reference(path: Path, root: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def materialize_active_run_lock(built: WorkflowFixture) -> Path:
    """Give a direct-Snakemake fixture the lifecycle lock it must prove."""

    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )
    identifier = str(attempt["workflow_attempt_id"])
    record = {
        "schema_version": "norad.run-lock.v1",
        "run_id": attempt["run_id"],
        "workflow_attempt_id": identifier,
        "attempt_record_path": f"attempts/{identifier}/attempt.json",
        "owner_token": attempt["owner_token"],
        "process_id": attempt["process_id"],
        "host": attempt["host"],
        "created_at": attempt["created_at"],
    }
    orchestration_contracts.validate_record("run-lock", record)
    locks_root = built.run_root / "locks"
    locks_root.mkdir(exist_ok=True)
    lock_path = locks_root / "run.lock"
    if lock_path.exists() or lock_path.is_symlink():
        raise AssertionError(f"Fixture run lock already exists: {lock_path}")
    lock_path.write_bytes(orchestration_contracts.canonical_json_bytes(record))
    return lock_path


def _terminalize_active_attempt(
    built: WorkflowFixture,
    *,
    finished_at: str,
) -> None:
    """Close a direct fixture attempt before materializing its resume successor."""

    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )
    identifier = str(attempt["workflow_attempt_id"])
    lock_path = built.run_root / "locks" / "run.lock"
    if not lock_path.is_file() or lock_path.is_symlink():
        raise AssertionError("Direct workflow fixture has no active real run lock")
    released_path = built.workflow_attempt_path.with_name("released-run-lock.json")
    lock_path.rename(released_path)

    expected = inspection.expected_tasks(built.execution, built.profile)
    starts = []
    for item in sorted(
        expected,
        key=lambda value: (value.machine_key, value.scope_type, value.scope_id),
    ):
        path = (
            built.run_root
            / "state"
            / "task-starts"
            / item.machine_key
            / f"{item.scope_id}.json"
        )
        if path.is_file() and not path.is_symlink():
            starts.append(
                {
                    "machine_key": item.machine_key,
                    "scope": item.scope,
                    "record": _reference(path, built.run_root),
                }
            )
    verified = []
    for item in expected:
        path = (
            built.run_root
            / "state"
            / "verified"
            / item.machine_key
            / f"{item.scope_id}.json"
        )
        if path.is_file() and not path.is_symlink():
            verified.append(
                {
                    "machine_key": item.machine_key,
                    "scope": item.scope,
                    "record": _reference(path, built.run_root),
                }
            )
    reporting = {}
    for kind in ("artifact_index", "run_summary", "html_report"):
        kind_root = built.run_root / "state" / "reporting" / kind
        reporting[kind] = {
            state: (
                _reference(kind_root / f"{state}.json", built.run_root)
                if (kind_root / f"{state}.json").is_file()
                and not (kind_root / f"{state}.json").is_symlink()
                else None
            )
            for state in ("start", "verified")
        }
    receipt = {
        "schema_version": "norad.attempt-receipt.v1",
        "run_id": attempt["run_id"],
        "execution_contract_sha256": attempt["execution_contract_sha256"],
        "profile_sha256": attempt["profile_sha256"],
        "workflow_attempt_id": identifier,
        "attempt_record": _reference(built.workflow_attempt_path, built.run_root),
        "released_run_lock": _reference(released_path, built.run_root),
        "status": "failed",
        "finished_at": finished_at,
        "snakemake_exit_code": 1,
        "termination_signal": None,
        "preentry_task_attempt_records": [],
        "task_start_records": starts,
        "verified_tasks": verified,
        "reporting_completion_records": reporting,
        "blockers": [],
        "message": "direct workflow fixture resume boundary",
        "local_pipeline_complete": False,
    }
    orchestration_contracts.validate_record("attempt-receipt", receipt)
    built.workflow_attempt_path.with_name("attempt-receipt.json").write_bytes(
        orchestration_contracts.canonical_json_bytes(receipt)
    )


def _tsv_bytes(header: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=header,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sample_header(
    base: tuple[str, ...], sample_ids: tuple[str, ...]
) -> tuple[str, ...]:
    return step08.sample_block_header(base, sample_ids)


def _candidate(
    index: int,
    *,
    partition_id: str,
    orientation: str,
    sample_ids: tuple[str, ...],
) -> dict[str, str]:
    row = {
        "partition_id": partition_id,
        "candidate_id": f"candidate_{index}",
        "orientation": orientation,
        "chromosome": "chrSynthetic",
        "position": str(index),
        "alt_index": "1",
        "genomic_ref": "T",
        "genomic_alt": "C",
        "rna_ref": "A",
        "rna_alt": "G",
        "annotation_strand": "+",
        "gene_ids": "g1",
        "transcript_ids": "tx1",
        "is_cds": "TRUE",
        "is_five_prime_utr": "FALSE",
        "is_three_prime_utr": "FALSE",
        "is_exon": "TRUE",
        "is_intron": "FALSE",
        "qual": "60",
        "filter": "PASS",
        "info_alt_depth": "4",
        "orientation_policy": "legacy_provisional_v1",
    }
    for sample_id in sample_ids:
        row[f"DP__{sample_id}"] = "10"
        row[f"AD__{sample_id}"] = "1"
        row[f"AF__{sample_id}"] = "0.1"
    return row


def _validation_bytes(row: dict[str, str]) -> bytes:
    spec = ADAPTER_REGISTRY[str(row["adapter"])]
    assert spec.expected_header is not None
    count = spec.exact_data_rows or 1
    check_ids = (
        (
            "output_transaction",
            "upstream_identity_and_candidate_order",
            "status_semantics",
            "significant_subset",
            "summary_count_reconciliation",
            "mutation_spectrum_reconciliation",
            "pdf_structure",
        )
        if row["adapter"] == "step09_validation_report_v1"
        else tuple(f"fixture_check_{index}" for index in range(1, count + 1))
    )
    assert len(check_ids) == count
    rows = [
        {
            "step_id": str(row["step_id"]),
            "scope_id": str(row["scope_id"]),
            "check_id": check_id,
            "status": "pass",
            "observed": "fixture",
            "expected": "fixture",
            "detail": "bounded no-science validation",
        }
        for check_id in check_ids
    ]
    return _tsv_bytes(tuple(spec.expected_header), rows)


def _vcf_bytes(sample_ids: tuple[str, ...]) -> bytes:
    sample_columns = "\t".join(sample_ids)
    sample_values = "\t".join("10:5,5:3,3:2,2:0" for _ in sample_ids)
    return (
        "##fileformat=VCFv4.2\n"
        '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">\n'
        '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
        '##FORMAT=<ID=ADF,Number=R,Type=Integer,Description="Forward depth">\n'
        '##FORMAT=<ID=ADR,Number=R,Type=Integer,Description="Reverse depth">\n'
        '##FORMAT=<ID=SP,Number=1,Type=Integer,Description="Strand bias">\n'
        '##INFO=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
        '##INFO=<ID=ADF,Number=R,Type=Integer,Description="Forward depth">\n'
        '##INFO=<ID=ADR,Number=R,Type=Integer,Description="Reverse depth">\n'
        f"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{sample_columns}\n"
        "chrSynthetic\t1\t.\tT\tC\t60\tPASS\tAD=5,5;ADF=3,3;ADR=2,2"
        f"\tDP:AD:ADF:ADR:SP\t{sample_values}\n"
    ).encode()


def _generic_artifact_bytes(row: dict[str, str]) -> bytes:
    spec = ADAPTER_REGISTRY[str(row["adapter"])]
    path = Path(str(row["source_path"]))
    if spec.kind == "star_index":
        if path.name in {"Genome", "SA", "SAindex"}:
            return b"\x00synthetic STAR index\n"
        if path.name == "genomeParameters.txt":
            return b"sjdbOverhang 74\n"
        return b"synthetic STAR index\n"
    if spec.kind == "bed12":
        return b"chrSynthetic\t0\t12\ttx1\t0\t+\t0\t12\t0\t1\t12,\t0,\n"
    if spec.kind == "fai":
        return b"chrSynthetic\t12\t14\t12\t13\n"
    if spec.kind == "dict":
        return b"@HD\tVN:1.6\n@SQ\tSN:chrSynthetic\tLN:12\n"
    if spec.kind == "bam":
        return minimal_bam_bytes()
    if spec.kind == "bai":
        return minimal_bai_bytes()
    if spec.kind == "quickcheck":
        return b"PASS: samtools quickcheck completed with no errors.\n"
    if spec.kind == "flagstat":
        return (
            b"10 + 0 in total (QC-passed reads + QC-failed reads)\n"
            b"8 + 0 mapped (80.00% : N/A)\n"
        )
    if spec.kind == "rseqc":
        return (
            b"Fraction of reads failed to determine: 0.01\n"
            b'Fraction of reads explained by "1++,1--,2+-,2-+": 0.97\n'
            b'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n'
        )
    if spec.kind == "star_log_final":
        return b"Number of input reads | 100\nUniquely mapped reads % | 95.00%\n"
    if spec.kind == "star_sj":
        return b"chrSynthetic\t1\t12\t1\t1\t0\t1\t0\t1\n"
    if spec.kind == "picard_metrics":
        return (
            b"## METRICS CLASS synthetic\n"
            b"LIBRARY\tREAD_PAIRS_EXAMINED\tREAD_PAIR_DUPLICATES\tPERCENT_DUPLICATION\n"
            b"synthetic\t10\t2\t0.2\n"
        )
    if spec.kind == "pdf":
        return minimal_pdf_bytes()
    if spec.kind == "text":
        return b"synthetic text output\n"
    raise AssertionError(f"Dynamic artifact kind requires an explicit fixture: {spec}")


def artifact_payloads(
    rows: tuple[dict[str, str], ...],
    execution: dict[str, Any],
    *,
    artifact_source_root: Path,
) -> dict[str, bytes]:
    sample_ids = tuple(str(row["sample_id"]) for row in execution["samples"]["rows"])
    partition_id = str(execution["partitions"]["rows"][0]["partition_id"])
    cohort_id = str(execution["analysis"]["cohort_id"])
    analysis_id = str(execution["analysis"]["primary_analysis_id"])
    sample_hash = str(execution["samples"]["manifest"]["sha256"])
    partition_hash = str(execution["partitions"]["manifest"]["sha256"])
    policy = execution["analysis"]["policy"]
    by_adapter: dict[str, list[dict[str, str]]] = {}
    payloads: dict[str, bytes] = {}
    for row in rows:
        by_adapter.setdefault(str(row["adapter"]), []).append(row)
        adapter = str(row["adapter"])
        if adapter == "step00c_reference_fasta_v1":
            continue
        if spec := ADAPTER_REGISTRY.get(adapter):
            if spec.kind == "validation_report":
                payloads[str(row["source_path"])] = _validation_bytes(row)
            elif spec.kind == "vcf":
                payloads[str(row["source_path"])] = _vcf_bytes(sample_ids)
            elif adapter not in {
                "step06_orientation_counts_v1",
                "step07_mpileup_receipt_v1",
                "step08_sites_v1",
                "step08_inputs_v1",
                "step08_summary_v1",
                "step09_cmh_all_sites_v1",
                "step09_cmh_significant_sites_v1",
                "step09_cmh_summary_v1",
                "step09_mutation_spectrum_tsv_v1",
                "step10_candidate_context_v1",
                "step10_motif_hits_v1",
                "step10_sequence_logo_v1",
                "step10_motif_statistics_v1",
                "step10_context_receipt_v1",
            }:
                payloads[str(row["source_path"])] = _generic_artifact_bytes(row)

    orientation_rows = by_adapter["step06_orientation_counts_v1"]
    for row in orientation_rows:
        payloads[str(row["source_path"])] = _tsv_bytes(
            tuple(
                ADAPTER_REGISTRY["step06_orientation_counts_v1"].expected_header or ()
            ),
            [
                {
                    "sample_id": str(row["scope_id"]),
                    "input_records": "10",
                    "flag_99_records": "3",
                    "flag_147_records": "2",
                    "flag_83_records": "2",
                    "flag_163_records": "1",
                    "fwd_like_records": "5",
                    "rev_like_records": "3",
                    "assigned_records": "8",
                    "unassigned_records": "2",
                    "assigned_fraction": "0.800000",
                }
            ],
        )

    receipt_row = by_adapter["step07_mpileup_receipt_v1"][0]
    vcf_rows = by_adapter["step07_mpileup_vcf_v1"]
    receipt_rows = []
    for vcf_row in vcf_rows:
        orientation = (
            "FWD_like" if ".FWD_like." in vcf_row["source_path"] else "REV_like"
        )
        receipt_rows.append(
            {
                "cohort_id": cohort_id,
                "partition_id": partition_id,
                "selector_type": "region",
                "selector_value": "chrSynthetic",
                "orientation": orientation,
                "vcf_path": str(vcf_row["source_path"]),
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_sha256": partition_hash,
                "sample_count": str(len(sample_ids)),
                "vcf_record_count": "1",
            }
        )
    payloads[str(receipt_row["source_path"])] = _tsv_bytes(
        tuple(ADAPTER_REGISTRY["step07_mpileup_receipt_v1"].expected_header or ()),
        receipt_rows,
    )

    candidates = [
        _candidate(
            index,
            partition_id=partition_id,
            orientation=orientation,
            sample_ids=sample_ids,
        )
        for index, orientation in enumerate(("FWD_like", "REV_like"), start=1)
    ]
    sites_row = by_adapter["step08_sites_v1"][0]
    payloads[str(sites_row["source_path"])] = _tsv_bytes(
        _sample_header(step08.STEP08_METADATA_HEADER, sample_ids),
        candidates,
    )
    inputs_rows = []
    receipt_bytes = payloads[str(receipt_row["source_path"])]
    for vcf_row in vcf_rows:
        vcf_bytes = payloads[str(vcf_row["source_path"])]
        orientation = (
            "FWD_like" if ".FWD_like." in vcf_row["source_path"] else "REV_like"
        )
        inputs_rows.append(
            {
                "cohort_id": cohort_id,
                "partition_id": partition_id,
                "selector_type": "region",
                "selector_value": "chrSynthetic",
                "orientation": orientation,
                "step07_receipt_path": str(receipt_row["source_path"]),
                "step07_receipt_sha256": _sha256(receipt_bytes),
                "vcf_path": str(vcf_row["source_path"]),
                "vcf_sha256": _sha256(vcf_bytes),
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_sha256": partition_hash,
                "annotation_gtf": str(execution["reference"]["gtf"]["path"]),
                "annotation_gtf_sha256": str(execution["reference"]["gtf"]["sha256"]),
                "sample_count": str(len(sample_ids)),
                "declared_vcf_record_count": "1",
                "observed_vcf_record_count": "1",
                "observed_alt_allele_count": "1",
                "supported_snv_count": "1",
                "skipped_symbolic_count": "0",
                "skipped_non_snv_count": "0",
                "published_candidate_count": "1",
                "orientation_policy": "legacy_provisional_v1",
            }
        )
    inputs_row = by_adapter["step08_inputs_v1"][0]
    payloads[str(inputs_row["source_path"])] = _tsv_bytes(
        step08.STEP08_INPUTS_HEADER,
        inputs_rows,
    )
    summary08_row = by_adapter["step08_summary_v1"][0]
    payloads[str(summary08_row["source_path"])] = _tsv_bytes(
        step08.STEP08_SUMMARY_HEADER,
        [
            {
                "cohort_id": cohort_id,
                "partition_count": "1",
                "step07_receipt_count": "1",
                "input_vcf_count": "2",
                "sample_count": str(len(sample_ids)),
                "observed_vcf_record_count": "2",
                "observed_alt_allele_count": "2",
                "supported_snv_count": "2",
                "skipped_symbolic_count": "0",
                "skipped_non_snv_count": "0",
                "published_candidate_count": "2",
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_sha256": partition_hash,
                "annotation_gtf": str(execution["reference"]["gtf"]["path"]),
                "annotation_gtf_sha256": str(execution["reference"]["gtf"]["sha256"]),
                "orientation_policy": "legacy_provisional_v1",
            }
        ],
    )

    result_rows = []
    for index, candidate in enumerate(candidates):
        result_rows.append(
            {
                "analysis_id": analysis_id,
                **candidate,
                "control_condition": str(policy["control_condition"]),
                "treatment_condition": str(policy["treatment_condition"]),
                "target_rna_change": "A>G",
                "replicate_count": "2",
                "test_status": "tested",
                "call_status": "significant_up" if index == 0 else "effect_not_met",
                "background_condition": "NA",
                "background_status": "disabled",
                "min_analysis_dp": "10",
                "mean_analysis_dp": "10",
                "mean_control_af": "0.1",
                "mean_treatment_af": "0.2",
                "treatment_control_difference": "0.1",
                "max_background_af": "NA",
                "cmh_statistic": "1",
                "cmh_degrees_freedom": "1",
                "cmh_p_value": "0.01",
                "cmh_fdr_bh": "0.02",
                "common_odds_ratio": "2",
            }
        )
    all_row = by_adapter["step09_cmh_all_sites_v1"][0]
    significant_row = by_adapter["step09_cmh_significant_sites_v1"][0]
    result_header = _sample_header(step09.STEP09_RESULT_HEADER, sample_ids)
    payloads[str(all_row["source_path"])] = _tsv_bytes(result_header, result_rows)
    payloads[str(significant_row["source_path"])] = _tsv_bytes(
        result_header, [result_rows[0]]
    )
    summary09_row = by_adapter["step09_cmh_summary_v1"][0]
    payloads[str(summary09_row["source_path"])] = _tsv_bytes(
        step09.STEP09_SUMMARY_HEADER,
        [
            {
                "analysis_id": analysis_id,
                "cohort_id": cohort_id,
                "control_condition": str(policy["control_condition"]),
                "treatment_condition": str(policy["treatment_condition"]),
                "background_condition": "NA",
                "target_rna_change": "A>G",
                "replicate_count": "2",
                "sample_count": str(len(sample_ids)),
                "candidate_count": "2",
                "target_candidate_count": "2",
                "successfully_tested_count": "2",
                "not_target_change_count": "0",
                "missing_counts_count": "0",
                "low_coverage_count": "0",
                "degenerate_table_count": "0",
                "below_mean_dp_count": "0",
                "background_not_passed_count": "0",
                "fdr_not_met_count": "0",
                "effect_not_met_count": "1",
                "significant_up_count": "1",
                "significant_down_count": "0",
                "sample_manifest_path": str(execution["samples"]["manifest"]["path"]),
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_path": str(
                    execution["partitions"]["manifest"]["path"]
                ),
                "partition_manifest_sha256": partition_hash,
                "step08_sites_path": str(sites_row["source_path"]),
                "step08_sites_sha256": _sha256(payloads[str(sites_row["source_path"])]),
                "step08_inputs_path": str(inputs_row["source_path"]),
                "step08_inputs_sha256": _sha256(
                    payloads[str(inputs_row["source_path"])]
                ),
                "min_sample_dp": str(policy["min_sample_dp"]),
                "mean_dp_threshold": str(policy["mean_dp_threshold"]),
                "fdr_threshold": str(policy["fdr_threshold"]),
                "common_or_threshold": str(policy["common_or_threshold"]),
                "absolute_difference_threshold": str(
                    policy["absolute_difference_threshold"]
                ),
                "background_max_fraction": str(policy["background_max_fraction"]),
                "multiple_testing_method": "BH",
                "cmh_alternative": "two.sided",
                "continuity_correction": "TRUE",
                "orientation_policy": "legacy_provisional_v1",
            }
        ],
    )
    mutation_row = by_adapter["step09_mutation_spectrum_tsv_v1"][0]
    mutation_rows = []
    for mutation in step09.CANONICAL_MUTATIONS:
        reference, alternate = mutation.split(">")
        target = mutation == "A>G"
        mutation_rows.append(
            {
                "analysis_id": analysis_id,
                "rna_ref": reference,
                "rna_alt": alternate,
                "mutation_type": mutation,
                "candidate_count": "2" if target else "0",
                "candidate_fraction": "1" if target else "0",
                "successfully_tested_count": "2" if target else "0",
                "significant_up_count": "1" if target else "0",
                "significant_down_count": "0",
            }
        )
    payloads[str(mutation_row["source_path"])] = _tsv_bytes(
        step09.STEP09_MUTATION_HEADER,
        mutation_rows,
    )

    def resolved(row: dict[str, str]) -> Path:
        path = Path(str(row["source_path"]))
        return path if path.is_absolute() else artifact_source_root / path

    with tempfile.TemporaryDirectory(prefix="norad-context-fixture-") as temporary:
        temporary_root = Path(temporary)
        temporary_all = temporary_root / "all.tsv"
        temporary_significant = temporary_root / "significant.tsv"
        temporary_summary = temporary_root / "summary.tsv"
        temporary_fai = temporary_root / "reference.fa.fai"
        temporary_all.write_bytes(payloads[str(all_row["source_path"])])
        temporary_significant.write_bytes(payloads[str(significant_row["source_path"])])
        temporary_summary.write_bytes(payloads[str(summary09_row["source_path"])])
        reference_fai_row = by_adapter["step00c_reference_fai_v1"][0]
        temporary_fai.write_bytes(payloads[str(reference_fai_row["source_path"])])
        motif_catalog = (
            REPO_ROOT
            / "src/norad/analyses/scientific_context_projection/resources/pum_motifs_v1.tsv"
        )
        context_fixture = build_transaction(
            temporary_root / "context",
            analysis_id=analysis_id,
            step09_all_sites=temporary_all,
            step09_significant_sites=temporary_significant,
            step09_summary=temporary_summary,
            reference_fasta=Path(str(execution["reference"]["fasta"]["path"])),
            reference_fai=temporary_fai,
            motif_catalog=motif_catalog,
            git_commit=source_checkout_commit(),
        )
        step10_outputs = {
            "step10_candidate_context_v1": context_fixture.candidate_context,
            "step10_motif_hits_v1": context_fixture.motif_hits,
            "step10_sequence_logo_v1": context_fixture.sequence_logo,
            "step10_motif_statistics_v1": context_fixture.motif_statistics,
        }
        for adapter, temporary_path in step10_outputs.items():
            row = by_adapter[adapter][0]
            payloads[str(row["source_path"])] = temporary_path.read_bytes()

        with context_fixture.receipt.open(encoding="utf-8", newline="") as stream:
            receipt_row = next(csv.DictReader(stream, delimiter="\t"))
        for prefix, source_row in (
            ("step09_all_sites", all_row),
            ("step09_significant_sites", significant_row),
            ("step09_summary", summary09_row),
            ("reference_fai", reference_fai_row),
        ):
            data = payloads[str(source_row["source_path"])]
            receipt_row[f"{prefix}_path"] = str(resolved(source_row))
            receipt_row[f"{prefix}_sha256"] = _sha256(data)
        reference_fasta = Path(str(execution["reference"]["fasta"]["path"]))
        receipt_row["reference_fasta_path"] = str(reference_fasta)
        receipt_row["reference_fasta_sha256"] = _sha256(reference_fasta.read_bytes())
        receipt_row["motif_catalog_path"] = str(motif_catalog)
        receipt_row["motif_catalog_sha256"] = _sha256(motif_catalog.read_bytes())
        for prefix, adapter in (
            ("candidate_context", "step10_candidate_context_v1"),
            ("motif_hits", "step10_motif_hits_v1"),
            ("sequence_logo", "step10_sequence_logo_v1"),
            ("motif_statistics", "step10_motif_statistics_v1"),
        ):
            output_row = by_adapter[adapter][0]
            data = payloads[str(output_row["source_path"])]
            receipt_row[f"{prefix}_path"] = str(resolved(output_row))
            receipt_row[f"{prefix}_sha256"] = _sha256(data)
        context_receipt_row = by_adapter["step10_context_receipt_v1"][0]
        payloads[str(context_receipt_row["source_path"])] = _tsv_bytes(
            scientific_context.SCIENTIFIC_CONTEXT_RECEIPT_HEADER,
            [receipt_row],
        )
    return payloads


def _scope_ids(task: dict[str, Any], execution: dict[str, Any]) -> tuple[str, ...]:
    selector = task["scope_selector"]
    if selector == "reference":
        return (str(execution["reference"]["reference_id"]),)
    if selector == "samples":
        return tuple(str(row["sample_id"]) for row in execution["samples"]["rows"])
    if selector == "partitions":
        cohort = str(execution["analysis"]["cohort_id"])
        return tuple(
            f"{cohort}__{row['partition_id']}"
            for row in execution["partitions"]["rows"]
        )
    if selector == "cohort":
        return (str(execution["analysis"]["cohort_id"]),)
    if selector == "analysis":
        return (str(execution["analysis"]["primary_analysis_id"]),)
    raise AssertionError(f"Fixture cannot execute selector {selector!r}")


def _task_attempt_id(index: int) -> str:
    suffix = hashlib.sha256(f"fixture-task-{index}".encode()).hexdigest()[:32]
    return f"task-20260812T120100Z-{suffix}"


def _write_dispatch(
    *,
    path: Path,
    run_root: Path,
    execution_path: Path,
    task: dict[str, Any],
    scope_id: str,
    index: int,
    fixture_input: Path,
    execution: dict[str, Any],
    inventory_rows: tuple[dict[str, str], ...],
    payloads: dict[str, bytes],
    workflow_attempt_id: str,
) -> dict[str, Any]:
    machine_key = str(task["machine_key"])
    step_id = str(task["step_id"])
    task_rows = tuple(
        row
        for row in inventory_rows
        if row["step_id"] == step_id and row["scope_id"] == scope_id
    )
    validation_rows = tuple(
        row
        for row in task_rows
        if ADAPTER_REGISTRY[row["adapter"]].kind == "validation_report"
    )
    assert len(validation_rows) == 1
    validation_row = validation_rows[0]

    def resolved(row: dict[str, str]) -> Path:
        source = Path(row["source_path"])
        return source if source.is_absolute() else run_root / source

    native_rows = tuple(
        row
        for row in task_rows
        if row is not validation_row and row["adapter"] != "step00c_reference_fasta_v1"
    )
    validation_report = resolved(validation_row)
    attempt_root = (
        run_root / "attempts" / workflow_attempt_id / "tasks" / machine_key / scope_id
    )
    task_attempt = attempt_root / "task-attempt.json"
    task_start = run_root / "state" / "task-starts" / machine_key / f"{scope_id}.json"
    verified = run_root / "state" / "verified" / machine_key / f"{scope_id}.json"
    stdout = attempt_root / "stdout.log"
    stderr = attempt_root / "stderr.log"
    manifest = path.with_suffix(".payload.json")
    for parent in {
        path.parent,
        manifest.parent,
        task_start.parent,
        verified.parent,
    }:
        parent.mkdir(parents=True, exist_ok=True)
    manifest_record = {
        "producer": [
            {
                "path": str(resolved(row)),
                "data_base64": base64.b64encode(payloads[row["source_path"]]).decode(),
            }
            for row in native_rows
        ],
        "validation": {
            "path": str(validation_report),
            "data_base64": base64.b64encode(
                payloads[validation_row["source_path"]]
            ).decode(),
        },
    }
    manifest.write_bytes(orchestration_contracts.canonical_json_bytes(manifest_record))
    producer = list(
        controlled_python_argv(
            sys.executable,
            str(OWNER_ARTIFACT_DOUBLE),
            "producer",
            "--manifest",
            str(manifest),
        )
    )
    validator = list(
        controlled_python_argv(
            sys.executable,
            str(OWNER_ARTIFACT_DOUBLE),
            "validator",
            "--manifest",
            str(manifest),
        )
    )
    input_declarations = [
        {"role": "fixture_input", "path": str(fixture_input)},
        {"role": "payload_manifest", "path": str(manifest)},
    ]
    if step_id == "00c":
        input_declarations.append(
            {
                "role": "reference_fasta",
                "path": str(execution["reference"]["fasta"]["path"]),
            }
        )
    record = {
        "schema_version": "norad.local-task-dispatch.v1",
        "run_root": str(run_root),
        "execution_path": str(execution_path),
        "profile_path": str(run_root / "contract" / "profile.json"),
        "workflow_attempt_id": workflow_attempt_id,
        "task_attempt_id": _task_attempt_id(index),
        "owner_run_token": f"test-owner-{index:03d}",
        "machine_key": machine_key,
        "scope": {
            "scope_type": str(task["scope_type"]),
            "scope_id": scope_id,
        },
        "producer_argv": producer,
        "validator_argv": validator,
        "inputs": input_declarations,
        "outputs": [
            {"role": f"artifact_{row_index:03d}", "path": str(resolved(row))}
            for row_index, row in enumerate(native_rows, start=1)
        ],
        "validation_report_path": str(validation_report),
        "native_receipt_path": None,
        "task_start_path": str(task_start),
        "task_attempt_path": str(task_attempt),
        "verified_task_path": str(verified),
        "stdout_path": str(stdout),
        "stderr_path": str(stderr),
    }
    path.write_bytes(orchestration_contracts.canonical_json_bytes(record))
    return record


def build(root: Path, *, materialize_attempt: bool = True) -> WorkflowFixture:
    """Build an immutable normalized contract plus pre-materialized dispatches."""

    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve(strict=True)
    intake_root = root / "intake"
    intake_root.mkdir()
    request_path = build_intake(intake_root)
    profile = orchestration_contracts.load_json_object(PROFILE_PATH)
    normalized = normalize_request(request_path, profile)
    execution = normalized.execution_contract

    run_root = (root / "run").resolve()
    contract_root = run_root / "contract"
    contract_root.mkdir(parents=True)
    execution_path = contract_root / "normalized.json"
    execution_path.write_bytes(normalized.normalized_bytes)
    profile_snapshot = contract_root / "profile.json"
    profile_snapshot.write_bytes(orchestration_contracts.canonical_json_bytes(profile))
    reporting = build_reporting_bundle(execution, profile)
    projection_bytes = {
        "reference_contract": reporting.reference_contract_bytes,
        "primary_analysis_policy": reporting.primary_analysis_policy_bytes,
        "reporting_run_contract": reporting.reporting_run_contract_bytes,
        "artifact_inventory": reporting.artifact_inventory_bytes,
    }
    projection_paths: dict[str, Path] = {}
    for name, reference in execution["reporting_projection"].items():
        projection_path = run_root / str(reference["path"])
        projection_path.parent.mkdir(parents=True, exist_ok=True)
        projection_path.write_bytes(projection_bytes[name])
        projection_paths[name] = projection_path
    fixture_input = run_root / "contract" / "fixture_input.txt"
    fixture_input.write_text("bounded no-science workflow fixture\n", encoding="utf-8")
    inventory_rows = tuple(dict(row) for row in reporting.artifact_inventory_rows)
    payloads = artifact_payloads(
        inventory_rows,
        execution,
        artifact_source_root=run_root,
    )

    workflow_attempt_id = "workflow-20260812T120000Z-" + "a" * 32
    workflow_attempt_path = run_root / "attempts" / workflow_attempt_id / "attempt.json"
    request_path = request_path.resolve(strict=True)
    request_bytes = request_path.read_bytes()
    attempt_request_path = workflow_attempt_path.parent / "request.yaml"
    git_commit = source_checkout_commit()
    attempt = {
        "schema_version": "norad.workflow-attempt.v1",
        "run_id": execution["run_id"],
        "execution_contract_sha256": hashlib.sha256(
            normalized.normalized_bytes
        ).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_snapshot.read_bytes()).hexdigest(),
        "workflow_attempt_id": workflow_attempt_id,
        "supersedes_workflow_attempt_id": None,
        "operation": "execute",
        "created_at": "2026-08-12T12:00:00Z",
        "request": {
            "path": str(attempt_request_path),
            "size_bytes": len(request_bytes),
            "sha256": hashlib.sha256(request_bytes).hexdigest(),
        },
        "request_label": "bounded no-science workflow fixture",
        "authored_paths": {
            "request": str(request_path),
            "sample_manifest": "samples.tsv",
            "partition_manifest": "partitions.tsv",
            "reference_fasta": "reference/genome.fa",
            "reference_gtf": "reference/genome.gtf",
            "analysis_policy": None,
        },
        "normalizer": {
            "name": "norad",
            "version": "0.1.0",
            "path": sys.executable,
            "resolved_path": str(Path(sys.executable).resolve(strict=True)),
            "sha256": hashlib.sha256(
                Path(sys.executable).resolve(strict=True).read_bytes()
            ).hexdigest(),
        },
        "workspace": str(root.resolve(strict=True)),
        "scratch": None,
        "source_checkout": {
            "path": str(REPO_ROOT.resolve(strict=True)),
            "commit": git_commit,
            "clean": True,
        },
        "executor": "local",
        "execution_mode": "test-double",
        "snakemake_argv": [],
        "host": "workflow-fixture",
        "process_id": os.getpid(),
        "owner_token": "workflow-fixture-owner",
        "cores": 1,
        "required_tools": [
            {
                "name": "python",
                "version": platform.python_version(),
                "path": sys.executable,
                "resolved_path": str(Path(sys.executable).resolve(strict=True)),
                "sha256": hashlib.sha256(
                    Path(sys.executable).resolve(strict=True).read_bytes()
                ).hexdigest(),
            },
            {
                "name": "snakemake",
                "version": "9.25.1",
                "path": sys.executable,
                "resolved_path": str(Path(sys.executable).resolve(strict=True)),
                "sha256": hashlib.sha256(
                    Path(sys.executable).resolve(strict=True).read_bytes()
                ).hexdigest(),
            },
        ],
    }
    dispatch_paths: dict[str, dict[str, str]] = {}
    dispatch_references: dict[str, dict[str, dict[str, str]]] = {}
    index = 0
    for task in profile["owner_tasks"]:
        machine_key = str(task["machine_key"])
        if machine_key not in profile["required_owner_keys"]:
            continue
        by_scope: dict[str, str] = {}
        references_by_scope: dict[str, dict[str, str]] = {}
        for scope_id in _scope_ids(task, execution):
            index += 1
            dispatch_path = (
                run_root
                / "contract"
                / "dispatch"
                / workflow_attempt_id
                / machine_key
                / f"{scope_id}.json"
            )
            _write_dispatch(
                path=dispatch_path,
                run_root=run_root,
                execution_path=execution_path,
                task=task,
                scope_id=scope_id,
                index=index,
                fixture_input=fixture_input,
                execution=execution,
                inventory_rows=inventory_rows,
                payloads=payloads,
                workflow_attempt_id=workflow_attempt_id,
            )
            by_scope[scope_id] = str(dispatch_path)
            references_by_scope[scope_id] = {
                "path": str(dispatch_path),
                "sha256": hashlib.sha256(dispatch_path.read_bytes()).hexdigest(),
            }
        dispatch_paths[machine_key] = by_scope
        dispatch_references[machine_key] = references_by_scope

    config = {
        "run_root": str(run_root),
        "python_executable": sys.executable,
        "execution_path": str(execution_path),
        "profile_path": str(profile_snapshot),
        "workflow_attempt_id": workflow_attempt_id,
        "source_checkout": str(REPO_ROOT.resolve(strict=True)),
        "artifact_source_root": str(run_root),
        "reference_contract_path": str(projection_paths["reference_contract"]),
        "primary_analysis_policy_path": str(
            projection_paths["primary_analysis_policy"]
        ),
        "reporting_run_contract_path": str(projection_paths["reporting_run_contract"]),
        "artifact_inventory_path": str(projection_paths["artifact_inventory"]),
        "step_threads": {"00a": 1, "01": 1, "02": 1, "06": 1, "08": 1},
        "sample_concurrency": 1,
        "dispatch_paths": dispatch_references,
    }
    config_path = contract_root / "workflow-configs" / f"{workflow_attempt_id}.json"
    config_path.parent.mkdir(parents=True)
    config_bytes = orchestration_contracts.canonical_json_bytes(config)
    config_path.write_bytes(config_bytes)
    attempt["snakemake_argv"] = list(
        build_snakemake_argv(
            python_executable=Path(sys.executable),
            snakefile=SNAKEFILE,
            workflow_profile=WORKFLOW_PROFILE,
            configfile=config_path,
            run_root=run_root,
            target="local_pipeline_slice",
            operation="execute",
        )
    )
    attempt["workflow_config"] = {
        "path": config_path.relative_to(run_root).as_posix(),
        "sha256": hashlib.sha256(config_bytes).hexdigest(),
    }
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    if materialize_attempt:
        workflow_attempt_path.parent.mkdir(parents=True)
        attempt_request_path.write_bytes(request_bytes)
        workflow_attempt_path.write_bytes(
            orchestration_contracts.canonical_json_bytes(attempt)
        )
    return WorkflowFixture(
        root=root,
        run_root=run_root,
        config_path=config_path,
        execution=execution,
        profile=profile,
        dispatch_paths=dispatch_paths,
        workflow_attempt_path=workflow_attempt_path,
    )


def refresh_attempt(
    built: WorkflowFixture,
    *,
    sequence: int,
    rematerialize_dispatches: bool = False,
) -> WorkflowFixture:
    """Materialize a new resume attempt and dispatch params for reuse tests."""

    if sequence < 1 or sequence > 9:
        raise ValueError("Fixture resume sequence must be between 1 and 9")
    previous_attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path, "workflow-attempt"
    )
    request_bytes = Path(previous_attempt["request"]["path"]).read_bytes()
    timestamp = f"20260812T13{sequence:02d}00Z"
    attempt_id = f"workflow-{timestamp}-" + f"{sequence:x}" * 32
    _terminalize_active_attempt(
        built,
        finished_at=f"2026-08-12T13:{sequence:02d}:00Z",
    )
    attempt = {
        **previous_attempt,
        "workflow_attempt_id": attempt_id,
        "supersedes_workflow_attempt_id": previous_attempt["workflow_attempt_id"],
        "operation": "resume",
        "created_at": f"2026-08-12T13:{sequence:02d}:00Z",
        "request": {
            **previous_attempt["request"],
            "path": str(built.run_root / "attempts" / attempt_id / "request.yaml"),
        },
        "owner_token": f"workflow-fixture-resume-{sequence}",
        "snakemake_argv": [],
    }
    attempt_path = built.run_root / "attempts" / attempt_id / "attempt.json"

    refreshed: dict[str, dict[str, str]] = {}
    refreshed_references: dict[str, dict[str, dict[str, str]]] = {}
    index = 0
    for machine_key, by_scope in built.dispatch_paths.items():
        refreshed_scopes: dict[str, str] = {}
        refreshed_scope_references: dict[str, dict[str, str]] = {}
        for scope_id, raw_path in by_scope.items():
            index += 1
            verified = built.verified_root / machine_key / f"{scope_id}.json"
            if (
                verified.exists() or verified.is_symlink()
            ) and not rematerialize_dispatches:
                refreshed_scopes[scope_id] = raw_path
                refreshed_scope_references[scope_id] = {
                    "path": raw_path,
                    "sha256": hashlib.sha256(Path(raw_path).read_bytes()).hexdigest(),
                }
                continue
            dispatch = orchestration_contracts.load_json_object(Path(raw_path))
            task_id = (
                f"task-{timestamp}-"
                + hashlib.sha256(
                    f"resume-{sequence}-{machine_key}-{scope_id}".encode()
                ).hexdigest()[:32]
            )
            task_root = (
                built.run_root
                / "attempts"
                / attempt_id
                / "tasks"
                / machine_key
                / scope_id
            )
            new_dispatch = (
                built.run_root
                / "contract"
                / "dispatch"
                / attempt_id
                / machine_key
                / f"{scope_id}.json"
            )
            new_dispatch.parent.mkdir(parents=True, exist_ok=True)
            dispatch.update(
                {
                    "workflow_attempt_id": attempt_id,
                    "task_attempt_id": task_id,
                    "owner_run_token": f"resume-{sequence}-{index:03d}",
                    "task_attempt_path": str(task_root / "task-attempt.json"),
                    "stdout_path": str(task_root / "stdout.log"),
                    "stderr_path": str(task_root / "stderr.log"),
                }
            )
            new_dispatch.write_bytes(
                orchestration_contracts.canonical_json_bytes(dispatch)
            )
            refreshed_scopes[scope_id] = str(new_dispatch)
            refreshed_scope_references[scope_id] = {
                "path": str(new_dispatch),
                "sha256": hashlib.sha256(new_dispatch.read_bytes()).hexdigest(),
            }
        refreshed[machine_key] = refreshed_scopes
        refreshed_references[machine_key] = refreshed_scope_references

    config = json.loads(built.config_path.read_text(encoding="utf-8"))
    config["workflow_attempt_id"] = attempt_id
    config["dispatch_paths"] = refreshed_references
    config_bytes = orchestration_contracts.canonical_json_bytes(config)
    config_path = (
        built.run_root / "contract" / "workflow-configs" / f"{attempt_id}.json"
    )
    config_path.write_bytes(config_bytes)
    attempt["snakemake_argv"] = list(
        build_snakemake_argv(
            python_executable=Path(sys.executable),
            snakefile=SNAKEFILE,
            workflow_profile=WORKFLOW_PROFILE,
            configfile=config_path,
            run_root=built.run_root,
            target="local_pipeline_slice",
            operation="resume",
        )
    )
    attempt["workflow_config"] = {
        "path": config_path.relative_to(built.run_root).as_posix(),
        "sha256": hashlib.sha256(config_bytes).hexdigest(),
    }
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    attempt_path.parent.mkdir(parents=True)
    Path(attempt["request"]["path"]).write_bytes(request_bytes)
    attempt_path.write_bytes(orchestration_contracts.canonical_json_bytes(attempt))
    refreshed_fixture = replace(
        built,
        config_path=config_path,
        dispatch_paths=refreshed,
        workflow_attempt_path=attempt_path,
    )
    materialize_active_run_lock(refreshed_fixture)
    return refreshed_fixture


__all__ = (
    "PROFILE_PATH",
    "REPO_ROOT",
    "OWNER_ARTIFACT_DOUBLE",
    "SNAKEFILE",
    "TASK_DOUBLE",
    "WorkflowFixture",
    "artifact_payloads",
    "build",
    "materialize_active_run_lock",
    "refresh_attempt",
)
