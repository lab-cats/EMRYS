"""Focused contract tests for the closed local-pilot schema registry."""

from __future__ import annotations

import copy
import json
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from norad.contracts import orchestration
from norad.contracts.orchestration import projection as reporting_projection

ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
WORKFLOW_ATTEMPT_ID = "workflow-20260812T120000Z-" + "a" * 32
TASK_ATTEMPT_ID = "task-20260812T120100Z-" + "b" * 32


def snapshot(path: str, digest: str = ZERO_HASH) -> dict[str, Any]:
    return {"path": path, "size_bytes": 4, "sha256": digest}


def record_reference(path: str, digest: str = ZERO_HASH) -> dict[str, str]:
    return {"path": path, "sha256": digest}


def policy() -> dict[str, Any]:
    return {
        "schema_version": "norad.analysis-policy.v1",
        "analysis_id": "analysis-1",
        "control_condition": "EV",
        "treatment_condition": "PUM1",
        "rna_ref": "A",
        "rna_alt": "G",
        "min_sample_dp": 1,
        "mean_dp_threshold": 50,
        "fdr_threshold": 0.05,
        "common_or_threshold": 1.2,
        "absolute_difference_threshold": 0.005,
        "background_condition": None,
        "background_max_fraction": 0.01,
    }


def request() -> dict[str, Any]:
    result = copy.deepcopy(policy())
    result["id"] = result.pop("analysis_id")
    result.pop("schema_version")
    return {
        "schema_version": "norad.request.v1",
        "label": "tiny local run",
        "profile": "norad.profile.local_cmh.v1",
        "sample_manifest": "samples.tsv",
        "partition_manifest": "partitions.tsv",
        "reference": {
            "id": "ref-1",
            "fasta": "reference/genome.fa",
            "gtf": "reference/genome.gtf",
            "star_index": {
                "sjdb_overhang": 149,
                "genome_sa_index_nbases": 14,
            },
        },
        "cohort_id": "cohort-1",
        "analysis": result,
    }


def profile() -> dict[str, Any]:
    return {
        "schema_version": "norad.profile.v1",
        "profile_id": "norad.profile.local_cmh",
        "profile_version": "v1",
        "semantic_owner_keys": ["star_index", "bam_qc", "scientific_review"],
        "owner_tasks": [
            {
                "machine_key": "star_index",
                "rule_name": "construct_STAR_index",
                "step_id": "00a",
                "scope_type": "reference",
                "scope_selector": "reference",
            },
            {
                "machine_key": "bam_qc",
                "rule_name": "collect_canonical_BAM_QC_evidence",
                "step_id": "02b",
                "scope_type": "sample",
                "scope_selector": "samples",
            },
            {
                "machine_key": "scientific_review",
                "rule_name": "assemble_scientific_review_evidence_package",
                "step_id": "09c",
                "scope_type": "scientific_review",
                "scope_selector": "scientific_review",
            },
        ],
        "direct_edges": [
            {
                "producer": "star_index",
                "consumer": "bam_qc",
                "artifact": "star_genome_index",
                "semantics": "reference index consumed by sample work",
            }
        ],
        "required_owner_keys": ["star_index", "bam_qc"],
        "evidence_owner_keys": ["bam_qc"],
        "excluded_owner_keys": ["scientific_review"],
        "artifact_templates": [
            {
                "artifact_id_template": "bam-qc.{sample_id}",
                "step_id": "02b",
                "scope_type": "sample",
                "scope_selector": "samples",
                "adapter": "step02b_qc_v1",
                "source_path_template": "results/{sample_id}/qc.tsv",
                "required": True,
            }
        ],
    }


def reference() -> dict[str, Any]:
    return {
        "schema_version": "norad.reference.v1",
        "reference_id": "ref-1",
        "fasta": snapshot("/data/genome.fa"),
        "gtf": snapshot("/data/genome.gtf", ONE_HASH),
        "star_index": {
            "sjdb_overhang": 149,
            "genome_sa_index_nbases": 14,
        },
    }


def execution() -> dict[str, Any]:
    analysis_policy = policy()
    samples = {
        "manifest": snapshot("/requests/samples.tsv"),
        "rows": [
            {
                "sample_id": "EV-1",
                "condition": "EV",
                "replicate": "1",
                "strandedness": "reverse",
                "r1_fastq": snapshot("/data/EV-1.R1.fastq"),
                "r2_fastq": snapshot("/data/EV-1.R2.fastq"),
            },
            {
                "sample_id": "PUM1-1",
                "condition": "PUM1",
                "replicate": "1",
                "strandedness": "reverse",
                "r1_fastq": snapshot("/data/PUM1-1.R1.fastq"),
                "r2_fastq": snapshot("/data/PUM1-1.R2.fastq"),
            },
            {
                "sample_id": "EV-2",
                "condition": "EV",
                "replicate": "2",
                "strandedness": "reverse",
                "r1_fastq": snapshot("/data/EV-2.R1.fastq"),
                "r2_fastq": snapshot("/data/EV-2.R2.fastq"),
            },
            {
                "sample_id": "PUM1-2",
                "condition": "PUM1",
                "replicate": "2",
                "strandedness": "reverse",
                "r1_fastq": snapshot("/data/PUM1-2.R1.fastq"),
                "r2_fastq": snapshot("/data/PUM1-2.R2.fastq"),
            },
        ],
    }
    partitions = {
        "manifest": snapshot("/requests/partitions.tsv"),
        "rows": [
            {
                "partition_id": "chr1",
                "selector_type": "region",
                "selector_value": "chr1",
                "selector_file": None,
            }
        ],
    }
    profile_identity = {
        "profile_id": "norad.profile.local_cmh",
        "profile_version": "v1",
        "profile_sha256": orchestration.canonical_sha256(profile()),
    }
    analysis = {
        "cohort_id": "cohort-1",
        "primary_analysis_id": "analysis-1",
        "policy": analysis_policy,
        "policy_sha256": orchestration.canonical_sha256(analysis_policy),
    }
    envelope = {
        "schema_version": "norad.identity-envelope.v1",
        "profile": profile_identity,
        "samples": samples,
        "partitions": partitions,
        "reference": reference(),
        "analysis": analysis,
    }
    digest = orchestration.canonical_sha256(envelope)
    record = {
        "schema_version": "norad.execution.v1",
        "profile": profile_identity,
        "samples": samples,
        "partitions": partitions,
        "reference": reference(),
        "analysis": analysis,
        "identity_envelope": envelope,
        "identity_envelope_sha256": digest,
        "run_id": f"run-{digest}",
        "reporting_projection": {},
    }
    bundle = reporting_projection.build_reporting_bundle(record, profile())
    record["reporting_projection"] = bundle.projection_references
    return record


def lifecycle_records() -> dict[str, dict[str, Any]]:
    run_id = f"run-{ZERO_HASH}"
    scope = {"scope_type": "sample", "scope_id": "EV-1"}
    command = {"argv": ["norad-owner", "--execute"], "exit_code": 0}
    workflow_attempt = {
        "schema_version": "norad.workflow-attempt.v1",
        "run_id": run_id,
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "supersedes_workflow_attempt_id": None,
        "operation": "execute",
        "created_at": "2026-08-12T12:00:00Z",
        "request": snapshot("/requests/run.yaml"),
        "request_label": "tiny local run",
        "authored_paths": {
            "request": "/requests/run.yaml",
            "sample_manifest": "samples.tsv",
            "partition_manifest": "partitions.tsv",
            "reference_fasta": "reference/genome.fa",
            "reference_gtf": "reference/genome.gtf",
            "analysis_policy": None,
        },
        "normalizer": {
            "name": "norad",
            "version": "0.1.0",
            "path": "/checkout/.venv/bin/norad",
        },
        "workspace": "/workspace",
        "scratch": None,
        "source_checkout": {
            "path": "/checkout",
            "commit": "a" * 40,
            "clean": True,
        },
        "executor": "local",
        "host": "localhost",
        "process_id": 42,
        "owner_token": "owner-token-1",
        "cores": 2,
        "required_tools": [
            {
                "name": "python",
                "version": "3.14.5",
                "path": "/checkout/.venv/bin/python",
            }
        ],
    }
    task_attempt = {
        "schema_version": "norad.task-attempt.v1",
        "run_id": run_id,
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "task_attempt_id": TASK_ATTEMPT_ID,
        "machine_key": "star_alignment",
        "scope": scope,
        "owner_run_token": "owner-run-1",
        "status": "succeeded",
        "started_at": "2026-08-12T12:01:00Z",
        "finished_at": "2026-08-12T12:02:00Z",
        "producer": command,
        "validator": command,
        "semantic_all_pass": command,
        "stable_inputs_rechecked": True,
        "validation_report": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/tasks/star_alignment/EV-1/validation.tsv"
        ),
        "stdout_path": (
            f"attempts/{WORKFLOW_ATTEMPT_ID}/tasks/star_alignment/EV-1/stdout.log"
        ),
        "stderr_path": (
            f"attempts/{WORKFLOW_ATTEMPT_ID}/tasks/star_alignment/EV-1/stderr.log"
        ),
        "failure_message": None,
    }
    verified_task = {
        "schema_version": "norad.verified-task.v1",
        "run_id": run_id,
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "task_attempt_id": TASK_ATTEMPT_ID,
        "task_attempt_record": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/tasks/star_alignment/EV-1/task-attempt.json"
        ),
        "machine_key": "star_alignment",
        "scope": scope,
        "owner_run_token": "owner-run-1",
        "commands": {
            "producer": command,
            "validator": command,
            "semantic_all_pass": command,
        },
        "inputs": [
            {
                "role": "fastq",
                "path": "/data/EV-1.fastq",
                "size_bytes": 4,
                "sha256": ZERO_HASH,
            }
        ],
        "outputs": [
            {
                "role": "bam",
                "path": "/workspace/results/EV-1.bam",
                "size_bytes": 4,
                "sha256": ONE_HASH,
            }
        ],
        "native_receipt": None,
        "validation_report": {
            "path": "results/qc/EV-1.validation.tsv",
            "sha256": ZERO_HASH,
            "all_pass": True,
        },
        "stable_inputs_rechecked": True,
        "all_pass": True,
        "created_at": "2026-08-12T12:02:00Z",
    }
    attempt_receipt = {
        "schema_version": "norad.attempt-receipt.v1",
        "run_id": run_id,
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "attempt_record": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/attempt.json"
        ),
        "status": "succeeded",
        "finished_at": "2026-08-12T12:03:00Z",
        "verified_tasks": [
            {
                "machine_key": "star_alignment",
                "scope": scope,
                "record": record_reference("state/verified/star_alignment/EV-1.json"),
            }
        ],
        "reporting_records": {
            "artifact_index": record_reference("products/artifact-index.json"),
            "run_summary": record_reference("products/run-summary.json"),
            "html_report": record_reference("products/report.receipt.json"),
        },
        "blockers": [],
        "message": None,
        "local_pipeline_complete": True,
    }
    return {
        "workflow-attempt": workflow_attempt,
        "task-attempt": task_attempt,
        "verified-task": verified_task,
        "attempt-receipt": attempt_receipt,
    }


def test_registry_is_closed_and_every_schema_is_draft_2020_12() -> None:
    schemas, _ = orchestration.load_schema_registry()

    assert tuple(schemas) == ("common", *orchestration.SCHEMA_NAMES)
    assert set(schemas) == set(orchestration.SCHEMA_IDS)
    for name, schema in schemas.items():
        assert schema["$id"] == orchestration.SCHEMA_IDS[name]
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        Draft202012Validator.check_schema(schema)
        stack: list[Any] = [schema]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                reference_value = value.get("$ref")
                if reference_value is not None:
                    assert reference_value.startswith(("urn:norad:", "#"))
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)


def test_request_profile_reference_policy_and_execution_records_pass() -> None:
    records = {
        "request": request(),
        "profile": profile(),
        "reference": reference(),
        "policy": policy(),
        "execution": execution(),
    }
    for name, record in records.items():
        orchestration.validate_record(
            name,
            record,
            profile=profile() if name == "execution" else None,
        )

    request_without_background = request()
    request_without_background["analysis"].pop("background_condition")
    orchestration.validate_record("request", request_without_background)


def test_lifecycle_and_verified_records_pass() -> None:
    for name, record in lifecycle_records().items():
        orchestration.validate_record(name, record)


@pytest.mark.parametrize(
    ("name", "mutate", "message"),
    [
        (
            "request",
            lambda record: record.__setitem__("unknown", True),
            "Additional properties",
        ),
        (
            "profile",
            lambda record: record["required_owner_keys"].append("not-an-owner"),
            "semantic_owner_keys",
        ),
        (
            "attempt-receipt",
            lambda record: record.__setitem__("local_pipeline_complete", False),
            "True was expected",
        ),
        (
            "verified-task",
            lambda record: record.__setitem__("all_pass", False),
            "True was expected",
        ),
    ],
)
def test_closed_and_semantic_record_mutations_fail(
    name: str,
    mutate: Any,
    message: str,
) -> None:
    base = {"request": request(), "profile": profile(), **lifecycle_records()}[name]
    mutate(base)
    with pytest.raises(orchestration.ContractValidationError, match=message):
        orchestration.validate_record(name, base)


def test_execution_policy_digest_mutation_fails() -> None:
    record = execution()
    record["analysis"]["policy_sha256"] = ZERO_HASH
    record["identity_envelope"]["analysis"]["policy_sha256"] = ZERO_HASH
    envelope_hash = orchestration.canonical_sha256(record["identity_envelope"])
    record["identity_envelope_sha256"] = envelope_hash
    record["run_id"] = f"run-{envelope_hash}"

    with pytest.raises(orchestration.ContractValidationError, match="policy_sha256"):
        orchestration.validate_record("execution", record, profile=profile())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("min_sample_dp", 0),
        ("common_or_threshold", 1),
        ("background_max_fraction", 0),
        ("background_max_fraction", 1),
    ],
)
def test_step09_threshold_boundaries_match_owner_semantics(
    field: str,
    value: int,
) -> None:
    records = {"request": request(), "policy": policy()}
    for name, record in records.items():
        target = record["analysis"] if name == "request" else record
        target[field] = value
        with pytest.raises(orchestration.ContractValidationError, match=field):
            orchestration.validate_record(name, record)


def test_profile_owner_task_projection_is_exact() -> None:
    record = profile()
    record["owner_tasks"][0]["scope_selector"] = "samples"
    with pytest.raises(orchestration.ContractValidationError, match="owner_task"):
        orchestration.validate_record("profile", record)

    record = profile()
    record["owner_tasks"].pop()
    with pytest.raises(orchestration.ContractValidationError, match="exactly one"):
        orchestration.validate_record("profile", record)

    record = profile()
    record["required_owner_keys"].remove("bam_qc")
    record["evidence_owner_keys"].clear()
    with pytest.raises(orchestration.ContractValidationError, match="classified"):
        orchestration.validate_record("profile", record)

    record = profile()
    record["owner_tasks"][1]["rule_name"] = record["owner_tasks"][0]["rule_name"]
    with pytest.raises(orchestration.ContractValidationError, match="rule_name"):
        orchestration.validate_record("profile", record)


def test_profile_rejects_duplicate_and_cyclic_direct_edges() -> None:
    record = profile()
    record["direct_edges"].append(copy.deepcopy(record["direct_edges"][0]))
    with pytest.raises(orchestration.ContractValidationError, match="must not repeat"):
        orchestration.validate_record("profile", record)

    record = profile()
    record["direct_edges"].append(
        {
            "producer": "bam_qc",
            "consumer": "star_index",
            "artifact": "invalid reverse dependency",
            "semantics": "would create a cycle",
        }
    )
    with pytest.raises(orchestration.ContractValidationError, match="acyclic"):
        orchestration.validate_record("profile", record)


def test_profile_rejects_reopened_artifact_logical_scope_groups() -> None:
    record = profile()
    first = record["artifact_templates"][0]
    record["artifact_templates"] = [
        first,
        {
            "artifact_id_template": "ref.{reference_id}.index",
            "step_id": "00a",
            "scope_type": "reference",
            "scope_selector": "reference",
            "adapter": "step00a_star_index_v1",
            "source_path_template": "results/reference/{reference_id}/Genome",
            "required": True,
        },
        {
            **first,
            "artifact_id_template": "bam-qc-validation.{sample_id}",
            "source_path_template": "results/{sample_id}/qc.validation.tsv",
        },
    ]

    with pytest.raises(
        orchestration.ContractValidationError,
        match="logical scope group reopens",
    ):
        orchestration.validate_record("profile", record)


def test_successful_task_records_bind_all_three_commands() -> None:
    records = lifecycle_records()
    task_attempt = records["task-attempt"]
    task_attempt["semantic_all_pass"] = True
    with pytest.raises(orchestration.ContractValidationError, match="not valid"):
        orchestration.validate_record("task-attempt", task_attempt)

    verified = records["verified-task"]
    verified["commands"].pop("semantic_all_pass")
    with pytest.raises(orchestration.ContractValidationError, match="required"):
        orchestration.validate_record("verified-task", verified)


def test_workflow_attempt_requires_clean_checkout_and_named_tools() -> None:
    attempt = lifecycle_records()["workflow-attempt"]
    attempt["source_checkout"]["clean"] = False
    with pytest.raises(
        orchestration.ContractValidationError, match="True was expected"
    ):
        orchestration.validate_record("workflow-attempt", attempt)

    attempt = lifecycle_records()["workflow-attempt"]
    attempt["required_tools"].append(copy.deepcopy(attempt["required_tools"][0]))
    with pytest.raises(orchestration.ContractValidationError, match="unique"):
        orchestration.validate_record("workflow-attempt", attempt)


def test_attempt_ids_bind_utc_context_and_128_random_bits() -> None:
    attempt = lifecycle_records()["workflow-attempt"]
    attempt["workflow_attempt_id"] = "workflow-20260812T120001Z-" + "a" * 32
    with pytest.raises(orchestration.ContractValidationError, match="UTC context"):
        orchestration.validate_record("workflow-attempt", attempt)

    task = lifecycle_records()["task-attempt"]
    task["task_attempt_id"] = "task-20260812T120100Z-" + "b" * 31
    with pytest.raises(orchestration.ContractValidationError, match="does not match"):
        orchestration.validate_record("task-attempt", task)


def test_execution_identity_digest_run_id_and_envelope_are_enforced() -> None:
    record = execution()
    record["identity_envelope_sha256"] = ZERO_HASH
    with pytest.raises(
        orchestration.ContractValidationError, match="canonical content"
    ):
        orchestration.validate_record("execution", record, profile=profile())

    record = execution()
    record["run_id"] = f"run-{ZERO_HASH}"
    with pytest.raises(orchestration.ContractValidationError, match="run_id"):
        orchestration.validate_record("execution", record, profile=profile())

    record = execution()
    record["samples"]["rows"].reverse()
    with pytest.raises(
        orchestration.ContractValidationError, match="identity_envelope"
    ):
        orchestration.validate_record("execution", record, profile=profile())


def test_reporting_projection_is_contract_relative_and_workspace_independent() -> None:
    record = execution()
    record["reporting_projection"]["reference_contract"]["path"] = (
        "/workspace/contract/reference_contract.json"
    )
    with pytest.raises(
        orchestration.ContractValidationError,
        match="reference_contract.json",
    ):
        orchestration.validate_record("execution", record, profile=profile())


def test_execution_requires_profile_and_complete_projection_match() -> None:
    record = execution()
    with pytest.raises(orchestration.ContractValidationError, match="exact profile"):
        orchestration.validate_record("execution", record)

    record = execution()
    record["reporting_projection"]["reporting_run_contract"]["sha256"] = ZERO_HASH
    with pytest.raises(orchestration.ContractValidationError, match="projection"):
        orchestration.validate_record("execution", record, profile=profile())

    record = execution()
    record["reporting_projection"]["artifact_inventory"]["sha256"] = ONE_HASH
    with pytest.raises(orchestration.ContractValidationError, match="projection"):
        orchestration.validate_record("execution", record, profile=profile())


def test_strict_json_loader_rejects_duplicate_keys_and_non_object(
    tmp_path: Any,
) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"run_id":"one","run_id":"two"}\n', encoding="utf-8")
    with pytest.raises(orchestration.ContractValidationError, match="Duplicate"):
        orchestration.load_json_object(duplicate)

    sequence = tmp_path / "sequence.json"
    sequence.write_text(json.dumps([1, 2]) + "\n", encoding="utf-8")
    with pytest.raises(orchestration.ContractValidationError, match="one object"):
        orchestration.load_json_object(sequence)


def test_canonical_json_is_stable_and_rejects_non_finite_numbers() -> None:
    assert orchestration.canonical_json_bytes({"b": 2, "a": "é"}) == (
        b'{"a":"\xc3\xa9","b":2}'
    )
    with pytest.raises(orchestration.ContractValidationError, match="canonical"):
        orchestration.canonical_json_bytes({"bad": float("nan")})
