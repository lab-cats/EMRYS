"""Focused contract tests for the closed run-coordinator schema registry."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from emrys.contracts import orchestration
from emrys.analyses import load_analysis_module, module_identity_record
from emrys.contracts.orchestration import application_model
from emrys.contracts.orchestration import artifact_inventory

ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
WORKFLOW_ATTEMPT_ID = "workflow-20260812T120000Z-" + "a" * 32
TASK_ATTEMPT_ID = "task-20260812T120100Z-" + "b" * 32


def snapshot(path: str, digest: str = ZERO_HASH) -> dict[str, Any]:
    return {"path": path, "size_bytes": 4, "sha256": digest}


def record_reference(path: str, digest: str = ZERO_HASH) -> dict[str, str]:
    return {"path": path, "sha256": digest}


def policy() -> dict[str, Any]:
    loaded = load_analysis_module("emrys.paired-cmh")
    return {
        "schema_version": "emrys.analysis-module-policy.v1",
        "analysis_id": "analysis-1",
        "module": module_identity_record(loaded),
        "implementation_sha256": loaded.provider.package.sha256,
        "configuration": {
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
        },
    }


def project() -> dict[str, Any]:
    return {
        "schema_version": "emrys.project.v1",
        "dataset": {"samples": "samples.tsv"},
        "reference": {
            "fasta": "reference/genome.fa",
            "gtf": "reference/genome.gtf",
            "star_index": {
                "sjdb_overhang": 149,
                "genome_sa_index_nbases": 14,
            },
        },
        "analyses": {
            "primary": {
                "partitions": "partitions.tsv",
                "control_condition": "EV",
                "treatment_condition": "PUM1",
                "target_change": "A>G",
                "min_sample_dp": 1,
                "mean_dp_threshold": 50,
                "fdr_threshold": 0.05,
                "common_or_threshold": 1.2,
                "absolute_difference_threshold": 0.005,
                "background_condition": None,
                "background_max_fraction": 0.01,
            }
        },
    }


def resource_config() -> dict[str, Any]:
    return {
        "schema_version": "emrys.local-pilot-resources.v1",
        "workflow_cores": 4,
        "workflow_memory_mb": "allocation",
        "stage_concurrency": {"01": 2, "06": 4},
        "step_threads": {"00a": 4, "01": 2},
        "stage_memory_mb": {"00a": "workflow", "01": 2048},
    }


def execution_profile() -> dict[str, Any]:
    resources = resource_config()
    return {
        "schema_version": "emrys.execution-profile.v1",
        "resources": resources,
        "placement": {"kind": "direct"},
    }


def profile() -> dict[str, Any]:
    return {
        "schema_version": "emrys.profile.v2",
        "profile_id": "emrys.profile.local_cmh",
        "profile_version": "v2",
        "semantic_owner_keys": ["star_index", "bam_qc"],
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
        "schema_version": "emrys.reference.v1",
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
        "profile_id": "emrys.profile.local_cmh",
        "profile_version": "v2",
        "profile_sha256": orchestration.canonical_sha256(profile()),
    }
    analysis = {
        "cohort_id": "cohort-1",
        "primary_analysis_id": "analysis-1",
        "policy": analysis_policy,
        "policy_sha256": orchestration.canonical_sha256(analysis_policy),
    }
    return {
        "profile": profile_identity,
        "samples": samples,
        "partitions": partitions,
        "reference": reference(),
        "analysis": analysis,
        "run_id": f"run-{ZERO_HASH}",
    }


def lifecycle_records() -> dict[str, dict[str, Any]]:
    run_id = f"run-{ZERO_HASH}"
    scope = {"scope_type": "sample", "scope_id": "EV-1"}
    command = {"argv": ["emrys-owner", "--execute"], "exit_code": 0}
    workflow_attempt = {
        "schema_version": "emrys.workflow-attempt.v2",
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
            "name": "emrys",
            "version": "0.1.0",
            "path": "/checkout/.venv/bin/python",
            "resolved_path": "/checkout/.venv/bin/python",
            "sha256": ZERO_HASH,
        },
        "workspace": "/workspace",
        "scratch": None,
        "installed_package": {
            "path": "/installed/emrys",
            "distribution": "emrys-rna-workflow",
            "version": "0.1.0.dev0",
            "content_sha256": ZERO_HASH,
            "git_commit": "a" * 40,
            "git_dirty": False,
            "python_lock_sha256": ZERO_HASH,
        },
        "executor": "local",
        "execution_mode": "test-double",
        "snakemake_argv": [
            "/checkout/.venv/bin/python",
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "snakemake",
            "--",
            "cohort_slice",
        ],
        "workflow": {
            "reference_contract_path": record_reference("contract/reference.json"),
            "primary_analysis_policy_path": record_reference("contract/policy.json"),
            "reporting_run_contract_path": record_reference("contract/reporting.json"),
            "artifact_inventory_path": record_reference("contract/inventory.tsv"),
            "resource_policy": {},
        },
        "tasks": {},
        "host": "localhost",
        "process_id": 42,
        "owner_token": "owner-token-1",
        "cores": 2,
        "required_tools": [
            {
                "name": "python",
                "version": "3.14.5",
                "path": "/checkout/.venv/bin/python",
                "resolved_path": "/checkout/.venv/bin/python",
                "sha256": ZERO_HASH,
            },
            {
                "name": "snakemake",
                "version": "9.25.1",
                "path": "/checkout/.venv/bin/python",
                "resolved_path": "/checkout/.venv/bin/python",
                "sha256": ZERO_HASH,
            },
        ],
    }
    task_start_reference = record_reference(
        "state/task-starts/star_alignment/EV-1.json"
    )
    task_start = {
        "schema_version": "emrys.task-start.v2",
        "run_id": run_id,
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "task_attempt_id": TASK_ATTEMPT_ID,
        "machine_key": "star_alignment",
        "scope": scope,
        "owner_run_token": "owner-run-1",
        "workflow_attempt_record": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/attempt.json"
        ),
        "run_lock": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/released-run-lock.json"
        ),
        "created_at": "2026-08-12T12:01:30Z",
    }
    task_attempt = {
        "schema_version": "emrys.task-attempt.v2",
        "run_id": run_id,
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "task_attempt_id": TASK_ATTEMPT_ID,
        "machine_key": "star_alignment",
        "scope": scope,
        "owner_run_token": "owner-run-1",
        "task_start_record": task_start_reference,
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
        "stdout_log": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/tasks/star_alignment/EV-1/stdout.log"
        ),
        "stderr_log": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/tasks/star_alignment/EV-1/stderr.log"
        ),
        "failure_message": None,
    }
    task_attempt.update(
        inputs=[{"role": "fastq", **snapshot("/data/EV-1.fastq")}],
        outputs=[{"role": "bam", **snapshot("/workspace/results/EV-1.bam", ONE_HASH)}],
        native_receipt=None,
    )
    verified_task = {
        "schema_version": "emrys.verified-task.v2",
        "task_attempt_record": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/tasks/star_alignment/EV-1/task-attempt.json"
        ),
    }
    attempt_receipt = {
        "schema_version": "emrys.attempt-receipt.v2",
        "run_id": run_id,
        "execution_contract_sha256": ZERO_HASH,
        "profile_sha256": ONE_HASH,
        "workflow_attempt_id": WORKFLOW_ATTEMPT_ID,
        "attempt_record": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/attempt.json"
        ),
        "released_run_lock": record_reference(
            f"attempts/{WORKFLOW_ATTEMPT_ID}/released-run-lock.json"
        ),
        "status": "succeeded",
        "finished_at": "2026-08-12T12:03:00Z",
        "snakemake_exit_code": 0,
        "termination_signal": None,
        "preentry_task_attempt_records": [],
        "task_start_records": [
            {
                "machine_key": "star_alignment",
                "scope": scope,
                "record": record_reference(
                    "state/task-starts/star_alignment/EV-1.json"
                ),
            }
        ],
        "verified_tasks": [
            {
                "machine_key": "star_alignment",
                "scope": scope,
                "record": record_reference("state/verified/star_alignment/EV-1.json"),
            }
        ],
        "blockers": [],
        "message": None,
    }
    return {
        "workflow-attempt": workflow_attempt,
        "task-start": task_start,
        "task-attempt": task_attempt,
        "verified-task": verified_task,
        "attempt-receipt": attempt_receipt,
    }


def test_registry_is_closed_and_every_schema_is_draft_2020_12() -> None:
    schemas, _ = orchestration.load_schema_registry()

    assert tuple(schemas) == (
        "common",
        *orchestration.SCHEMA_NAMES,
    )
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
                    assert reference_value.startswith(("urn:emrys:", "#"))
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)


@pytest.mark.parametrize(
    ("name", "directory", "identifier_version"),
    (
        ("execution-profile", "v3", "v1"),
        ("project", "v1", "v1"),
    ),
)
def test_versioned_schema_registration_is_exact(
    name: str,
    directory: str,
    identifier_version: str,
) -> None:
    assert (
        orchestration.SCHEMA_PATHS[name].name == f"{name.replace('-', '_')}.schema.json"
    )
    assert orchestration.SCHEMA_PATHS[name].parent.name == directory
    assert orchestration.SCHEMA_IDS[name] == (
        f"urn:emrys:schema:orchestration:{name}:{identifier_version}"
    )


def test_unknown_schema_selector_and_nonstandard_json_constant_are_rejected(
    tmp_path: Path,
) -> None:
    for name in ("unknown", "attempt-receipt-v2"):
        with pytest.raises(
            orchestration.ContractValidationError,
            match="Unknown orchestration schema",
        ):
            orchestration.schema_validator(name)

    record_path = tmp_path / "record.json"
    record_path.write_bytes(b'{"value":NaN}')
    with pytest.raises(
        orchestration.ContractValidationError,
        match="Non-standard JSON numeric constant",
    ):
        orchestration.load_json_object(record_path)


def test_project_resource_execution_profile_and_run_records_pass() -> None:
    records = {
        "project": project(),
        "resource-config": resource_config(),
        "execution-profile": execution_profile(),
        "profile": profile(),
        "reference": reference(),
        "policy": policy(),
    }
    for name, record in records.items():
        orchestration.validate_record(
            name,
            record,
        )

    project_without_background = project()
    project_without_background["analyses"]["primary"].pop("background_condition")
    project_without_background["analyses"]["secondary"] = {
        **project_without_background["analyses"]["primary"],
        "target_change": "C>T",
        "sample_ids": ["EV-1", "PUM1-1", "EV-2", "PUM1-2"],
    }
    orchestration.validate_record("project", project_without_background)


@pytest.mark.parametrize(
    "sample_ids",
    ([], ["EV-1", "EV-1"], ["unsafe sample"], [1]),
)
def test_project_rejects_invalid_analysis_sample_ids(
    sample_ids: list[object],
) -> None:
    record = project()
    record["analyses"]["primary"]["sample_ids"] = sample_ids

    with pytest.raises(orchestration.ContractValidationError):
        orchestration.validate_record("project", record)


def test_lifecycle_and_verified_records_pass() -> None:
    for name, record in lifecycle_records().items():
        orchestration.validate_record(name, record)


def test_workflow_attempt_accepts_closed_direct_and_slurm_placement() -> None:
    direct = lifecycle_records()["workflow-attempt"]
    direct["placement"] = {
        "kind": "direct",
        "source": {"path": "/profiles/direct.yaml", "sha256": ZERO_HASH},
        "effective_sha256": ONE_HASH,
        "request": {"kind": "direct"},
        "scheduler_job_id": None,
    }
    orchestration.validate_record("workflow-attempt", direct)

    scheduled = lifecycle_records()["workflow-attempt"]
    scheduled["placement"] = {
        "kind": "slurm",
        "source": {"path": "/profiles/site.yaml", "sha256": ZERO_HASH},
        "effective_sha256": ONE_HASH,
        "request": {
            "kind": "slurm",
            "account": "research",
            "partition": "compute",
            "qos": None,
            "cpus_per_task": 8,
            "memory_mb": None,
            "time": "02:00:00",
            "exclusive": True,
            "nodelist": None,
            "scratch_parent": "/scratch",
            "modules": {"mode": "none", "init": "", "load": []},
        },
        "scheduler_job_id": "700123",
    }
    orchestration.validate_record("workflow-attempt", scheduled)

    malformed_source = copy.deepcopy(direct)
    malformed_source["placement"]["source"]["unexpected"] = True
    with pytest.raises(orchestration.ContractValidationError, match="Additional"):
        orchestration.validate_record("workflow-attempt", malformed_source)

    mismatched_kind = copy.deepcopy(scheduled)
    mismatched_kind["placement"]["kind"] = "direct"
    with pytest.raises(orchestration.ContractValidationError):
        orchestration.validate_record("workflow-attempt", mismatched_kind)


@pytest.mark.parametrize("job_id", ("0", "00", "01", "-1", 1, True))
def test_workflow_attempt_rejects_noncanonical_scheduler_job_ids(
    job_id: object,
) -> None:
    attempt = lifecycle_records()["workflow-attempt"]
    attempt["placement"] = {
        "kind": "direct",
        "source": {"path": "/profiles/direct.yaml", "sha256": ZERO_HASH},
        "effective_sha256": ONE_HASH,
        "request": {"kind": "direct"},
        "scheduler_job_id": job_id,
    }

    with pytest.raises(
        orchestration.ContractValidationError,
        match="scheduler_job_id",
    ):
        orchestration.validate_record("workflow-attempt", attempt)


@pytest.mark.parametrize(
    ("name", "mutate", "message"),
    [
        (
            "project",
            lambda record: record.__setitem__("unknown", True),
            "Additional properties",
        ),
        (
            "project",
            lambda record: record["analyses"]["primary"].__setitem__(
                "target_change", "A>A"
            ),
            "rna_ref and rna_alt",
        ),
        (
            "project",
            lambda record: record["reference"].__setitem__("id", "retired-alias"),
            "Additional properties",
        ),
        (
            "project",
            lambda record: record["analyses"].__setitem__(
                "unsafe name", record["analyses"].pop("primary")
            ),
            "does not match",
        ),
        (
            "profile",
            lambda record: record["required_owner_keys"].append("not-an-owner"),
            "semantic_owner_keys",
        ),
    ],
)
def test_closed_and_semantic_record_mutations_fail(
    name: str,
    mutate: Any,
    message: str,
) -> None:
    base = {"project": project(), "profile": profile(), **lifecycle_records()}[name]
    mutate(base)
    with pytest.raises(orchestration.ContractValidationError, match=message):
        orchestration.validate_record(name, base)


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
    records = {"project": project()}
    for name, record in records.items():
        target = record["analyses"]["primary"]
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
    with pytest.raises(orchestration.ContractValidationError, match="required"):
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
    with pytest.raises(orchestration.ContractValidationError, match="Invalid"):
        orchestration.validate_record("task-attempt", task_attempt)

    verified = records["verified-task"]
    verified.pop("task_attempt_record")
    with pytest.raises(orchestration.ContractValidationError, match="required"):
        orchestration.validate_record("verified-task", verified)


def test_task_attempt_distinguishes_preentry_failure_from_started_work() -> None:
    successful = lifecycle_records()["task-attempt"]
    successful["task_start_record"] = None
    with pytest.raises(orchestration.ContractValidationError, match="Invalid"):
        orchestration.validate_record("task-attempt", successful)

    preentry = lifecycle_records()["task-attempt"]
    preentry.update(
        status="failed",
        task_start_record=None,
        inputs=[],
        outputs=[],
        producer=None,
        validator=None,
        semantic_all_pass=None,
        stable_inputs_rechecked=False,
        validation_report=None,
        failure_message="declared destination already exists",
    )
    orchestration.validate_record("task-attempt", preentry)

    preentry["producer"] = {"argv": ["must-not-run"], "exit_code": 1}
    with pytest.raises(orchestration.ContractValidationError, match="Invalid"):
        orchestration.validate_record("task-attempt", preentry)


def test_task_attempt_logs_are_closed_content_references() -> None:
    attempt = lifecycle_records()["task-attempt"]
    attempt["stdout_path"] = attempt.pop("stdout_log")["path"]
    with pytest.raises(
        orchestration.ContractValidationError,
        match="stdout_log.*required|stdout_path.*unexpected",
    ):
        orchestration.validate_record("task-attempt", attempt)

    attempt = lifecycle_records()["task-attempt"]
    attempt["stderr_log"].pop("sha256")
    with pytest.raises(orchestration.ContractValidationError, match="sha256.*required"):
        orchestration.validate_record("task-attempt", attempt)


def test_attempt_receipt_terminal_semantics_and_unique_scope_references() -> None:
    receipt = lifecycle_records()["attempt-receipt"]
    receipt["verified_tasks"].append(copy.deepcopy(receipt["verified_tasks"][0]))
    with pytest.raises(orchestration.ContractValidationError, match="unique owner"):
        orchestration.validate_record("attempt-receipt", receipt)

    receipt = lifecycle_records()["attempt-receipt"]
    receipt["task_start_records"].append(
        copy.deepcopy(receipt["task_start_records"][0])
    )
    with pytest.raises(orchestration.ContractValidationError, match="unique owner"):
        orchestration.validate_record("attempt-receipt", receipt)

    receipt = lifecycle_records()["attempt-receipt"]
    receipt["task_start_records"] = []
    with pytest.raises(
        orchestration.ContractValidationError, match="corresponding task starts"
    ):
        orchestration.validate_record("attempt-receipt", receipt)

    receipt = lifecycle_records()["attempt-receipt"]
    receipt["verified_tasks"] = []
    receipt.update(
        status="failed",
        snakemake_exit_code=0,
        message="zero exit with incomplete task state",
    )
    with pytest.raises(orchestration.ContractValidationError, match="every task start"):
        orchestration.validate_record("attempt-receipt", receipt)

    receipt = lifecycle_records()["attempt-receipt"]
    receipt.update(
        status="blocked",
        snakemake_exit_code=None,
        blockers=[],
        message="blocked without declared facts",
    )
    with pytest.raises(orchestration.ContractValidationError, match="at least one"):
        orchestration.validate_record("attempt-receipt", receipt)

    receipt = lifecycle_records()["attempt-receipt"]
    receipt.update(
        status="failed",
        snakemake_exit_code=0,
        blockers=["ambiguous residue"],
        message="not clean",
    )
    with pytest.raises(orchestration.ContractValidationError, match="Only blocked"):
        orchestration.validate_record("attempt-receipt", receipt)


def test_attempt_receipt_v2_closes_science_without_reporting_fields() -> None:
    receipt = lifecycle_records()["attempt-receipt"]

    validator = orchestration.schema_validator("attempt-receipt")
    assert validator.is_valid(receipt)
    orchestration.validate_record("attempt-receipt", receipt)

    for retired_field in ("reporting_completion_records", "local_pipeline_complete"):
        incompatible = copy.deepcopy(receipt)
        incompatible[retired_field] = True
        assert not validator.is_valid(incompatible)
        with pytest.raises(
            orchestration.ContractValidationError,
            match=f"{retired_field}.*unexpected",
        ):
            orchestration.validate_record("attempt-receipt", incompatible)


@pytest.mark.parametrize(
    ("field", "value", "diagnostic"),
    (
        ("status", "unknown", "$.status: 'unknown' is not one of"),
        ("finished_at", 0, "$.finished_at: 0 is not of type 'string'"),
        (
            "attempt_record",
            {"path": "attempt.json", "sha256": "bad"},
            "$.attempt_record.sha256:",
        ),
        (
            "schema_version",
            "emrys.attempt-receipt.v99",
            "$.schema_version: 'emrys.attempt-receipt.v2' was expected",
        ),
    ),
)
def test_attempt_receipt_public_validator_preserves_field_diagnostics(
    field: str,
    value: Any,
    diagnostic: str,
) -> None:
    receipt = lifecycle_records()["attempt-receipt"]
    validator = orchestration.schema_validator("attempt-receipt")
    assert validator.is_valid(receipt)
    receipt[field] = value

    assert not validator.is_valid(receipt)
    assert any(
        error.startswith(diagnostic)
        for error in orchestration.schema_errors("attempt-receipt", receipt)
    )
    with pytest.raises(orchestration.ContractValidationError):
        orchestration.validate_record("attempt-receipt", receipt)


@pytest.mark.parametrize("record", ({}, [], None))
def test_attempt_receipt_public_validator_rejects_missing_version_and_nonobjects(
    record: Any,
) -> None:
    assert not orchestration.schema_validator("attempt-receipt").is_valid(record)
    assert orchestration.schema_errors("attempt-receipt", record)


def test_workflow_attempt_requires_package_identity_and_named_tools() -> None:
    attempt = lifecycle_records()["workflow-attempt"]
    attempt["installed_package"]["content_sha256"] = "not-a-sha256"
    with pytest.raises(orchestration.ContractValidationError, match="does not match"):
        orchestration.validate_record("workflow-attempt", attempt)

    attempt = lifecycle_records()["workflow-attempt"]
    attempt["required_tools"].append(copy.deepcopy(attempt["required_tools"][0]))
    with pytest.raises(orchestration.ContractValidationError, match="unique"):
        orchestration.validate_record("workflow-attempt", attempt)

    attempt = lifecycle_records()["workflow-attempt"]
    attempt["required_tools"].insert(
        0,
        {
            "name": "z-tool",
            "version": "1",
            "path": "/tools/z-tool",
            "resolved_path": "/tools/z-tool",
            "sha256": ONE_HASH,
        },
    )
    with pytest.raises(orchestration.ContractValidationError, match="normalized"):
        orchestration.validate_record("workflow-attempt", attempt)

    attempt = lifecycle_records()["workflow-attempt"]
    attempt["required_tools"][1]["sha256"] = ONE_HASH
    with pytest.raises(
        orchestration.ContractValidationError, match="same executable bytes"
    ):
        orchestration.validate_record("workflow-attempt", attempt)

    attempt = lifecycle_records()["workflow-attempt"]
    attempt["execution_mode"] = "local-science-tools"
    with pytest.raises(
        orchestration.ContractValidationError, match="controlled Python SHA-256"
    ):
        orchestration.validate_record("workflow-attempt", attempt)

    attempt = lifecycle_records()["workflow-attempt"]
    attempt["required_tools"].insert(
        1,
        {
            "name": "sha256_python",
            "version": "sha256",
            "path": "/checkout/.venv/bin/python",
            "resolved_path": "/checkout/.venv/bin/python",
            "sha256": ONE_HASH,
        },
    )
    with pytest.raises(
        orchestration.ContractValidationError, match="exact Python executable bytes"
    ):
        orchestration.validate_record("workflow-attempt", attempt)


def test_local_science_attempt_requires_storage_qualification() -> None:
    attempt = lifecycle_records()["workflow-attempt"]
    attempt["execution_mode"] = "local-science-tools"
    python = next(
        item for item in attempt["required_tools"] if item["name"] == "python"
    )
    attempt["required_tools"].append(
        {
            **copy.deepcopy(python),
            "name": "sha256_python",
            "version": "sha256",
        }
    )
    attempt["required_tools"].sort(key=lambda item: item["name"])

    with pytest.raises(
        orchestration.ContractValidationError,
        match="storage qualification",
    ):
        orchestration.validate_record("workflow-attempt", attempt)

    attempt["required_tools"].append(
        {
            "name": "storage_qualification",
            "version": "b" * 64,
            "path": "/evidence/storage.qualified.json",
            "resolved_path": "/evidence/storage.qualified.json",
            "sha256": ONE_HASH,
        }
    )
    attempt["required_tools"].sort(key=lambda item: item["name"])
    orchestration.validate_record("workflow-attempt", attempt)


def test_workflow_attempt_requires_exact_internal_resume_controls() -> None:
    initial = lifecycle_records()["workflow-attempt"]
    initial["snakemake_argv"].insert(-2, "--ignore-incomplete")
    with pytest.raises(
        orchestration.ContractValidationError,
        match="Initial execution",
    ):
        orchestration.validate_record("workflow-attempt", initial)

    resume = lifecycle_records()["workflow-attempt"]
    resume.update(
        workflow_attempt_id="workflow-20260812T130000Z-" + "c" * 32,
        supersedes_workflow_attempt_id=WORKFLOW_ATTEMPT_ID,
        operation="resume",
        created_at="2026-08-12T13:00:00Z",
        snakemake_argv=[
            "/checkout/.venv/bin/python",
            "-X",
            "pycache_prefix=/dev/null",
            "-I",
            "-m",
            "snakemake",
            "--rerun-triggers",
            "input",
            "--ignore-incomplete",
            "--",
            "cohort_slice",
        ],
    )
    orchestration.validate_record("workflow-attempt", resume)

    missing_ignore = copy.deepcopy(resume)
    missing_ignore["snakemake_argv"].remove("--ignore-incomplete")
    with pytest.raises(
        orchestration.ContractValidationError,
        match="Resume must use exactly",
    ):
        orchestration.validate_record("workflow-attempt", missing_ignore)

    duplicate_ignore = copy.deepcopy(resume)
    duplicate_ignore["snakemake_argv"].insert(6, "--ignore-incomplete")
    with pytest.raises(
        orchestration.ContractValidationError,
        match="Resume must use exactly",
    ):
        orchestration.validate_record("workflow-attempt", duplicate_ignore)


def test_attempt_ids_bind_utc_context_and_128_random_bits() -> None:
    attempt = lifecycle_records()["workflow-attempt"]
    attempt["workflow_attempt_id"] = "workflow-20260812T120001Z-" + "a" * 32
    with pytest.raises(orchestration.ContractValidationError, match="UTC context"):
        orchestration.validate_record("workflow-attempt", attempt)

    task = lifecycle_records()["task-attempt"]
    task["task_attempt_id"] = "task-20260812T120100Z-" + "b" * 31
    with pytest.raises(orchestration.ContractValidationError, match="does not match"):
        orchestration.validate_record("task-attempt", task)


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("unsupported-selector", "Unsupported profile scope_selector"),
        ("unresolved-template", "Unresolved template syntax"),
        ("empty", "projects no artifact inventory rows"),
        ("unsafe-id", "artifact_id is not a safe ID"),
        ("duplicate", "duplicate artifact_id"),
        ("scope-mismatch", "scope_selector/scope_type mismatch"),
    ),
)
def test_artifact_inventory_rejects_invalid_projection(
    case: str,
    message: str,
) -> None:
    candidate = profile()
    template = candidate["artifact_templates"][0]
    if case == "unsupported-selector":
        template["scope_selector"] = "unsupported"
    elif case == "unresolved-template":
        template["artifact_id_template"] = "{{sample_id}}"
    elif case == "empty":
        candidate["artifact_templates"] = []
    elif case == "unsafe-id":
        template["artifact_id_template"] = "bad id.{sample_id}"
    elif case == "duplicate":
        candidate["artifact_templates"].append(copy.deepcopy(template))
    else:
        template["scope_type"] = "analysis"

    with pytest.raises(orchestration.ContractValidationError, match=message):
        source = execution()
        artifact_inventory.project_rows(
            source,
            candidate,
            application_model.analysis_revision_from_execution_fields(source),
        )


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
