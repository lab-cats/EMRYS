"""Focused protections for the immutable Analysis/Plan/Run seam."""

from __future__ import annotations

import copy
import json

import pytest

from emrys.contracts.orchestration import api as contracts
from emrys.contracts.orchestration import application_model as model
from tests.contracts.orchestration.test_orchestration_contracts import (
    execution as historical_execution,
)
from tests.contracts.orchestration.test_orchestration_contracts import lifecycle_records
from tests.contracts.orchestration.test_orchestration_contracts import (
    profile as historical_profile,
)

ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64


def analysis_inputs() -> dict[str, object]:
    return {
        "samples": [
            {
                "sample_id": "PUM1-1",
                "condition": "PUM1",
                "replicate": "1",
                "strandedness": "reverse",
                "r1_fastq_sha256": ZERO_HASH,
                "r2_fastq_sha256": ONE_HASH,
            },
            {
                "sample_id": "EV-1",
                "condition": "EV",
                "replicate": "1",
                "strandedness": "reverse",
                "r1_fastq_sha256": ONE_HASH,
                "r2_fastq_sha256": ZERO_HASH,
            },
            {
                "sample_id": "PUM1-2",
                "condition": "PUM1",
                "replicate": "2",
                "strandedness": "reverse",
                "r1_fastq_sha256": ZERO_HASH,
                "r2_fastq_sha256": ONE_HASH,
            },
            {
                "sample_id": "EV-2",
                "condition": "EV",
                "replicate": "2",
                "strandedness": "reverse",
                "r1_fastq_sha256": ONE_HASH,
                "r2_fastq_sha256": ZERO_HASH,
            },
        ],
        "partitions": [
            {
                "partition_id": "curated",
                "selector_type": "regions_file",
                "selector_file_sha256": TWO_HASH,
            },
            {
                "partition_id": "chr1",
                "selector_type": "region",
                "selector_value": "chr1:1-1000",
            },
        ],
        "reference": {
            "fasta_sha256": ZERO_HASH,
            "gtf_sha256": ONE_HASH,
        },
        "scientific_policy": {
            "control_condition": "EV",
            "treatment_condition": "PUM1",
            "background_condition": None,
            "rna_ref": "A",
            "rna_alt": "G",
            "min_sample_dp": 10,
            "mean_dp_threshold": 50,
            "fdr_threshold": 0.05,
            "common_or_threshold": 1.2,
            "absolute_difference_threshold": 0.01,
            "background_max_fraction": 0.01,
        },
    }


def analysis_revision() -> model.AnalysisRevision:
    return model.build_analysis_revision(**analysis_inputs())


def functional_specification() -> dict[str, object]:
    return {
        "owner_tasks": [
            {
                "machine_key": "bam_qc",
                "step_id": "02b",
                "scope_type": "sample",
            },
            {
                "machine_key": "star_index",
                "step_id": "00a",
                "scope_type": "reference",
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
                "adapter": "step02b_qc_v1",
                "source_path_template": "results/{sample_id}/qc.tsv",
                "required": True,
            }
        ],
    }


def implementation_digest() -> str:
    return model.implementation_content_sha256(
        [
            {
                "role": "scientific_computation",
                "logical_name": "workflow",
                "content_sha256": ZERO_HASH,
            },
            {
                "role": "artifact_admission",
                "logical_name": "task-validator",
                "content_sha256": ONE_HASH,
            },
        ]
    )


def execution_plan() -> model.ExecutionPlan:
    return model.build_execution_plan(
        functional_specification=functional_specification(),
        scientific_stopping_owner_keys=["bam_qc", "star_index"],
        implementation_content_sha256=implementation_digest(),
        toolchain=[
            {
                "kind": "environment",
                "logical_name": "renv",
                "content_sha256": TWO_HASH,
            },
            {
                "kind": "tool",
                "logical_name": "STAR",
                "content_sha256": ONE_HASH,
            },
        ],
        backend="local",
        engine="snakemake",
        backend_semantics_sha256=ZERO_HASH,
        star_index={"sjdb_overhang": 149, "genome_sa_index_nbases": 14},
        computational_resources={
            "workflow_cores": 4,
            "workflow_memory_mb": "allocation",
            "stage_concurrency": {"02": 2, "01": 1},
            "step_threads": {"02": 4, "00a": 4},
            "stage_memory_mb": {"02": 4096, "00a": "workflow"},
        },
    )


def successor_run_fixture() -> tuple[
    model.AnalysisRevision,
    model.ExecutionPlan,
    model.RunBinding,
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    profile = historical_profile()
    execution = historical_execution()
    analysis = model.analysis_revision_from_execution_fields(execution)
    attempt = lifecycle_records()["workflow-attempt"]
    resources = {
        "workflow_cores": 2,
        "workflow_memory_mb": "allocation",
        "stage_concurrency": {"02b": 1},
        "step_threads": {"00a": 2},
        "stage_memory_mb": {"00a": "workflow", "02b": 1024},
    }
    plan = model.build_execution_plan(
        functional_specification=(model.functional_specification_from_profile(profile)),
        scientific_stopping_owner_keys=profile["required_owner_keys"],
        implementation_content_sha256=implementation_digest(),
        toolchain=model.toolchain_from_required_tools(attempt["required_tools"]),
        backend="local",
        engine="snakemake",
        backend_semantics_sha256=ZERO_HASH,
        star_index=execution["reference"]["star_index"],
        computational_resources=resources,
    )
    run = model.bind_run(analysis, plan)
    attempt["run_id"] = run.run_id
    attempt["execution_contract_sha256"] = run.record_sha256
    attempt["profile_sha256"] = contracts.canonical_sha256(profile)
    effective = {
        "schema_version": "emrys.local-pilot-resources.v1",
        "workflow_cores": 2,
        "workflow_memory_mb": 4096,
        "stage_concurrency": {"02b": 1},
        "step_threads": {"00a": 2},
        "stage_memory_mb": {"00a": 4096, "02b": 1024},
        "reporting_memory_mb": {},
    }
    resource_policy = {
        "symbolic": {
            **effective,
            **resources,
        },
        "symbolic_sha256": contracts.canonical_sha256(
            {
                **effective,
                **resources,
            }
        ),
        "effective": effective,
        "effective_sha256": contracts.canonical_sha256(effective),
        "allocation": {"cores": 2, "memory_mb": 4096, "source": "test"},
        "sources": {
            "default_sha256": ZERO_HASH,
            "config_path": None,
            "config_sha256": None,
            "cli_overrides": [],
        },
    }
    return analysis, plan, run, profile, attempt, resource_policy


def test_analysis_revision_is_order_neutral_closed_and_deeply_immutable() -> None:
    inputs = analysis_inputs()
    first = model.build_analysis_revision(**inputs)
    inputs["samples"].reverse()  # type: ignore[union-attr]
    inputs["partitions"].reverse()  # type: ignore[union-attr]
    second = model.build_analysis_revision(**inputs)
    assert first.canonical_bytes == second.canonical_bytes

    mutable_projection = first.record
    mutable_projection["identity"]["samples"][0]["condition"] = "changed"
    assert first.record["identity"]["samples"][0]["condition"] == "EV"

    invalid = analysis_inputs()
    invalid["reference"]["path"] = "/relocation/is/not/identity"  # type: ignore[index]
    with pytest.raises(contracts.ContractValidationError, match="unexpected path"):
        model.build_analysis_revision(**invalid)


def test_analysis_content_and_versioned_scope_formulas_are_bound() -> None:
    first = analysis_revision()
    changed_inputs = analysis_inputs()
    changed_inputs["samples"][0]["r1_fastq_sha256"] = TWO_HASH  # type: ignore[index]
    changed = model.build_analysis_revision(**changed_inputs)
    assert changed.analysis_revision_id != first.analysis_revision_id
    assert changed.scope_id("cohort") != first.scope_id("cohort")
    assert first.scope_id("sample", "EV-1") == "EV-1"
    assert first.scope_id("reference").startswith("scope-reference-")
    assert first.scope_id("cohort_partition", "chr1").startswith(
        "scope-cohort-partition-"
    )


def test_module_analysis_identity_binds_method_and_canonical_configuration() -> None:
    inputs = analysis_inputs()
    common = {key: inputs[key] for key in ("samples", "partitions", "reference")}
    first = model.build_module_analysis_revision(
        **common,
        module_id="example.differential",
        interface_version="emrys.analysis-module.v1",
        module_version="v1",
        config_schema_sha256=ZERO_HASH,
        configuration={"contrast": ["treated", "control"], "fdr": 0.05},
    )
    reordered = model.build_module_analysis_revision(
        **common,
        module_id="example.differential",
        interface_version="emrys.analysis-module.v1",
        module_version="v1",
        config_schema_sha256=ZERO_HASH,
        configuration={"fdr": 0.05, "contrast": ["treated", "control"]},
    )
    changed = model.build_module_analysis_revision(
        **common,
        module_id="example.differential",
        interface_version="emrys.analysis-module.v1",
        module_version="v2",
        config_schema_sha256=ZERO_HASH,
        configuration={"contrast": ["treated", "control"], "fdr": 0.05},
    )
    schema_changed = model.build_module_analysis_revision(
        **common,
        module_id="example.differential",
        interface_version="emrys.analysis-module.v1",
        module_version="v1",
        config_schema_sha256=ONE_HASH,
        configuration={"contrast": ["treated", "control"], "fdr": 0.05},
    )

    assert first.canonical_bytes == reordered.canonical_bytes
    assert first.record["schema_version"] == "emrys.analysis-revision.v2"
    assert first != changed
    assert first != schema_changed
    assert model.read_application_record(first.canonical_bytes) == first


def test_execution_plan_canonicalizes_sets_graphs_tools_and_resource_maps() -> None:
    first = execution_plan()
    functional = functional_specification()
    functional["owner_tasks"].reverse()  # type: ignore[union-attr]
    functional["required_owner_keys"].reverse()  # type: ignore[union-attr]
    second = model.build_execution_plan(
        functional_specification=functional,
        scientific_stopping_owner_keys=["star_index", "bam_qc"],
        implementation_content_sha256=implementation_digest(),
        toolchain=list(reversed(first.record["identity"]["toolchain"])),
        backend="local",
        engine="snakemake",
        backend_semantics_sha256=ZERO_HASH,
        star_index={"genome_sa_index_nbases": 14, "sjdb_overhang": 149},
        computational_resources={
            "workflow_cores": 4,
            "workflow_memory_mb": "allocation",
            "stage_concurrency": {"01": 1, "02": 2},
            "step_threads": {"00a": 4, "02": 4},
            "stage_memory_mb": {"00a": "workflow", "02": 4096},
        },
    )
    assert first.canonical_bytes == second.canonical_bytes


def test_execution_plan_admits_only_predecessor_closed_stopping_owners() -> None:
    full = execution_plan()
    assert model.execution_plan_boundary(full) == "analysis"

    partial_record = full.record
    partial_record["identity"]["scientific_stopping_owner_keys"] = ["star_index"]
    partial_record["execution_plan_id"] = "plan-" + contracts.canonical_sha256(
        partial_record["identity"]
    )
    partial = model.ExecutionPlan.from_record(partial_record)
    assert model.execution_plan_boundary(partial) == "partial"

    missing_predecessor = full.record
    missing_predecessor["identity"]["scientific_stopping_owner_keys"] = ["bam_qc"]
    missing_predecessor["execution_plan_id"] = "plan-" + contracts.canonical_sha256(
        missing_predecessor["identity"]
    )
    with pytest.raises(
        contracts.ContractValidationError,
        match="predecessor-closed; missing star_index",
    ):
        model.ExecutionPlan.from_record(missing_predecessor)

    empty = full.record
    empty["identity"]["scientific_stopping_owner_keys"] = []
    empty["execution_plan_id"] = "plan-" + contracts.canonical_sha256(empty["identity"])
    with pytest.raises(contracts.ContractValidationError):
        model.ExecutionPlan.from_record(empty)

    not_required = full.record
    not_required["identity"]["functional_specification"]["required_owner_keys"] = [
        "star_index"
    ]
    not_required["identity"]["functional_specification"]["evidence_owner_keys"] = []
    not_required["execution_plan_id"] = "plan-" + contracts.canonical_sha256(
        not_required["identity"]
    )
    with pytest.raises(
        contracts.ContractValidationError,
        match="must reference required owners",
    ):
        model.ExecutionPlan.from_record(not_required)


def test_processing_boundary_requires_the_exact_processing_step_roster() -> None:
    identity = execution_plan().record["identity"]

    def plan(
        sample_step: str,
        *,
        processing_source: dict[str, str] | None = None,
        complete: bool = False,
    ) -> model.ExecutionPlan:
        functional = copy.deepcopy(identity["functional_specification"])
        functional["owner_tasks"][0]["step_id"] = sample_step
        functional["owner_tasks"].append(
            {"machine_key": "downstream", "step_id": "07", "scope_type": "cohort"}
        )
        functional["direct_edges"].append(
            {
                "producer": "bam_qc",
                "consumer": "downstream",
                "artifact": "sample evidence",
                "semantics": "cohort input",
            }
        )
        functional["required_owner_keys"].append("downstream")
        return model.build_execution_plan(
            functional_specification=functional,
            scientific_stopping_owner_keys=(
                functional["required_owner_keys"]
                if complete
                else ["bam_qc", "star_index"]
            ),
            implementation_content_sha256=identity["implementation_content_sha256"],
            toolchain=identity["toolchain"],
            backend="local",
            engine="snakemake",
            backend_semantics_sha256=ZERO_HASH,
            star_index=identity["star_index"],
            computational_resources=identity["computational_resources"],
            processing_source=processing_source,
        )

    assert model.execution_plan_boundary(plan("06")) == "processing"
    assert model.execution_plan_boundary(plan("07")) == "partial"

    source = {
        "source_run_id": "run-" + ZERO_HASH,
        "workflow_attempt_id": "workflow-20260831T120000Z-" + "1" * 32,
        "attempt_receipt_sha256": TWO_HASH,
    }
    downstream = plan("06", processing_source=source, complete=True)
    assert downstream.record["identity"]["processing_source"] == source
    assert model.execution_owner_keys(downstream) == ("downstream",)
    assert downstream.execution_plan_id != plan("06", complete=True).execution_plan_id
    with pytest.raises(
        contracts.ContractValidationError,
        match="only for a complete downstream Analysis plan",
    ):
        plan("06", processing_source=source)


def test_plan_contract_excludes_adapter_reporting_and_realization_fields() -> None:
    with pytest.raises(contracts.ContractValidationError, match="Implementation role"):
        model.implementation_content_sha256(
            [
                {
                    "role": "reporting",
                    "logical_name": "html-template",
                    "content_sha256": ZERO_HASH,
                }
            ]
        )

    functional = functional_specification()
    functional["owner_tasks"][0]["rule_name"] = "backend_adapter"  # type: ignore[index]
    with pytest.raises(contracts.ContractValidationError, match="rule_name"):
        model.build_execution_plan(
            functional_specification=functional,
            scientific_stopping_owner_keys=["bam_qc"],
            implementation_content_sha256=implementation_digest(),
            toolchain=[
                {
                    "kind": "tool",
                    "logical_name": "STAR",
                    "content_sha256": ONE_HASH,
                }
            ],
            backend="local",
            engine="snakemake",
            backend_semantics_sha256=ZERO_HASH,
            star_index={"sjdb_overhang": 149, "genome_sa_index_nbases": 14},
            computational_resources={
                "workflow_cores": 4,
                "workflow_memory_mb": "allocation",
                "stage_concurrency": {},
                "step_threads": {},
                "stage_memory_mb": {},
            },
        )


def test_run_binding_uses_only_the_two_domain_separated_identity_digests() -> None:
    analysis = analysis_revision()
    plan = execution_plan()
    run = model.bind_run(analysis, plan)
    binding = {
        "identity_domain": "emrys.run-identity.v1",
        "analysis_revision_sha256": analysis.identity_sha256,
        "execution_plan_sha256": plan.identity_sha256,
    }
    assert run.record["binding"] == binding
    assert run.run_id == f"run-{contracts.canonical_sha256(binding)}"

    tampered = run.record
    tampered["binding"]["execution_plan_sha256"] = ZERO_HASH
    with pytest.raises(contracts.ContractValidationError, match="Run ID"):
        model.RunBinding.from_record(tampered)


def test_version_aware_reader_preserves_historical_execution_bytes() -> None:
    legacy = historical_execution()
    source_bytes = json.dumps(legacy, indent=2, sort_keys=False).encode("utf-8")
    recognized = model.read_application_record(source_bytes)
    assert isinstance(recognized, model.LegacyExecution)
    assert recognized.source_bytes == source_bytes
    assert not recognized.profile_validated

    admitted = model.read_application_record(
        source_bytes,
        legacy_profile=historical_profile(),
    )
    assert isinstance(admitted, model.LegacyExecution)
    assert admitted.profile_validated


@pytest.mark.parametrize("version", (None, [], {}))
def test_version_aware_reader_rejects_non_string_schema_versions(
    version: object,
) -> None:
    with pytest.raises(
        contracts.ContractValidationError,
        match="schema_version must be a string",
    ):
        model.read_application_record(
            contracts.canonical_json_bytes({"schema_version": version})
        )


def test_execution_view_accepts_only_historical_execution_v1() -> None:
    legacy = historical_execution()
    profile = historical_profile()
    retired_projection = {"schema_version": "emrys.execution-projection.v1"}

    model.validate_execution_view(legacy, profile=profile)
    with pytest.raises(contracts.ContractValidationError, match="Unsupported"):
        model.validate_execution_view(retired_projection, profile=profile)
    with pytest.raises(contracts.ContractValidationError, match="Invalid"):
        contracts.validate_record("application-model", retired_projection)
    with pytest.raises(contracts.ContractValidationError, match="Unsupported"):
        model.read_application_record(
            contracts.canonical_json_bytes(retired_projection)
        )


def test_analysis_admission_requires_present_conditions_and_paired_replicates() -> None:
    missing_condition = analysis_inputs()
    missing_condition["scientific_policy"]["treatment_condition"] = "missing"  # type: ignore[index]
    with pytest.raises(contracts.ContractValidationError, match="must exist"):
        model.build_analysis_revision(**missing_condition)

    incomplete_pair = analysis_inputs()
    incomplete_pair["samples"] = [  # type: ignore[assignment]
        row
        for row in incomplete_pair["samples"]  # type: ignore[union-attr]
        if row["sample_id"] != "PUM1-2"
    ]
    with pytest.raises(contracts.ContractValidationError, match="replicate strata"):
        model.build_analysis_revision(**incomplete_pair)


def test_plan_admission_rejects_rehashed_noncanonical_functional_lists() -> None:
    functional = functional_specification()
    functional["owner_tasks"].append(  # type: ignore[union-attr]
        {
            "machine_key": "variant_call",
            "step_id": "03",
            "scope_type": "cohort_partition",
        }
    )
    functional["direct_edges"].append(  # type: ignore[union-attr]
        {
            "producer": "bam_qc",
            "consumer": "variant_call",
            "artifact": "canonical_bam",
            "semantics": "QC-admitted BAM consumed by variant calling",
        }
    )
    functional["artifact_templates"].append(  # type: ignore[union-attr]
        {
            "artifact_id_template": "variants.{partition_id}",
            "step_id": "03",
            "scope_type": "cohort_partition",
            "adapter": "step03_variants_v1",
            "source_path_template": "results/{partition_id}/variants.vcf",
            "required": True,
        }
    )
    plan = model.build_execution_plan(
        functional_specification=functional,
        scientific_stopping_owner_keys=["bam_qc", "star_index"],
        implementation_content_sha256=implementation_digest(),
        toolchain=execution_plan().record["identity"]["toolchain"],
        backend="local",
        engine="snakemake",
        backend_semantics_sha256=ZERO_HASH,
        star_index={"sjdb_overhang": 149, "genome_sa_index_nbases": 14},
        computational_resources=execution_plan().record["identity"][
            "computational_resources"
        ],
    )
    for field in ("owner_tasks", "direct_edges", "artifact_templates"):
        tampered = plan.record
        tampered["identity"]["functional_specification"][field].reverse()
        tampered["execution_plan_id"] = "plan-" + contracts.canonical_sha256(
            tampered["identity"]
        )
        with pytest.raises(contracts.ContractValidationError, match=field):
            model.ExecutionPlan.from_record(tampered)


def test_successor_run_proves_authority_and_optional_attempt_observations() -> None:
    analysis, plan, run, profile, attempt, resource_policy = successor_run_fixture()
    model.validate_successor_run(
        analysis=analysis,
        plan=plan,
        run=run,
        profile=profile,
        attempt=attempt,
        resource_policy=resource_policy,
        observed_implementation_content_sha256=implementation_digest(),
        observed_backend_semantics_sha256=ZERO_HASH,
    )
    scheduled_resources = copy.deepcopy(resource_policy)
    scheduled_resources["allocation"]["slurm_job_id"] = "9" * 5000
    model.validate_successor_run(
        analysis=analysis,
        plan=plan,
        run=run,
        profile=profile,
        attempt=attempt,
        resource_policy=scheduled_resources,
    )


@pytest.mark.parametrize(
    ("path", "value", "rehash", "message"),
    (
        (("unexpected",), True, None, "policy fields must be closed"),
        (("symbolic",), [], None, "requires symbolic.*mappings"),
        (("symbolic_sha256",), TWO_HASH, None, "symbolic resource digest differs"),
        (("effective_sha256",), TWO_HASH, None, "resource policy digest differs"),
        (
            ("sources", "default_sha256"),
            "not-a-digest",
            None,
            "default_sha256 must be a SHA-256 digest",
        ),
        (
            ("sources", "cli_overrides"),
            [3],
            None,
            "cli_overrides must be a string list",
        ),
        (
            ("allocation", "cores"),
            0,
            None,
            "Allocation cores must be a positive integer",
        ),
        (
            ("allocation", "slurm_job_id"),
            "0",
            None,
            "Slurm job ID must be a positive decimal",
        ),
        (("effective", "workflow_cores"), 1, "effective", "workflow cores differ"),
        (
            ("effective", "workflow_memory_mb"),
            2048,
            "effective",
            "workflow memory differs",
        ),
        (("allocation", "cores"), 1, None, "exceed the observed allocation"),
        (("effective", "stage_concurrency"), {}, "effective", "stage_concurrency"),
        (
            ("effective", "reporting_memory_mb"),
            {"html_report": 8192},
            "effective",
            "reporting memory html_report exceeds",
        ),
    ),
)
def test_successor_run_rejects_invalid_resource_resolution(
    path: tuple[str, ...],
    value: object,
    rehash: str | None,
    message: str,
) -> None:
    analysis, plan, run, profile, _, resource_policy = successor_run_fixture()
    changed = copy.deepcopy(resource_policy)
    target = changed
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    if rehash is not None:
        changed[f"{rehash}_sha256"] = contracts.canonical_sha256(changed[rehash])
    with pytest.raises(contracts.ContractValidationError, match=message):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            resource_policy=changed,
        )


def test_successor_run_rejects_binding_and_profile_drift_but_admits_partial() -> None:
    analysis, plan, run, profile, _, _ = successor_run_fixture()
    mismatched_run = model.bind_run(analysis_revision(), plan)
    with pytest.raises(contracts.ContractValidationError, match="Run binding differs"):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=mismatched_run,
            profile=profile,
        )

    changed_plan_record = plan.record
    changed_plan_record["identity"]["functional_specification"][
        "evidence_owner_keys"
    ] = []
    changed_plan_record["execution_plan_id"] = "plan-" + contracts.canonical_sha256(
        changed_plan_record["identity"]
    )
    changed_plan = model.ExecutionPlan.from_record(changed_plan_record)
    changed_run = model.bind_run(analysis, changed_plan)
    with pytest.raises(contracts.ContractValidationError, match="Profile functional"):
        model.validate_successor_run(
            analysis=analysis,
            plan=changed_plan,
            run=changed_run,
            profile=profile,
        )

    changed_plan_record = plan.record
    changed_plan_record["identity"]["scientific_stopping_owner_keys"] = ["star_index"]
    changed_plan_record["execution_plan_id"] = "plan-" + contracts.canonical_sha256(
        changed_plan_record["identity"]
    )
    changed_plan = model.ExecutionPlan.from_record(changed_plan_record)
    changed_run = model.bind_run(analysis, changed_plan)
    model.validate_successor_run(
        analysis=analysis,
        plan=changed_plan,
        run=changed_run,
        profile=profile,
    )


def test_successor_run_rejects_attempt_resource_and_observed_digest_drift() -> None:
    analysis, plan, run, profile, attempt, resource_policy = successor_run_fixture()
    for field, value, message in (
        ("run_id", f"run-{TWO_HASH}", "Attempt Run ID"),
        ("profile_sha256", TWO_HASH, "Attempt profile digest"),
    ):
        changed_attempt = copy.deepcopy(attempt)
        changed_attempt[field] = value
        with pytest.raises(contracts.ContractValidationError, match=message):
            model.validate_successor_run(
                analysis=analysis,
                plan=plan,
                run=run,
                profile=profile,
                attempt=changed_attempt,
            )

    changed_attempt = copy.deepcopy(attempt)
    changed_attempt["execution_contract_sha256"] = TWO_HASH
    with pytest.raises(contracts.ContractValidationError, match="Run binding digest"):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            attempt=changed_attempt,
        )

    changed_attempt = copy.deepcopy(attempt)
    changed_attempt["cores"] = 1
    with pytest.raises(contracts.ContractValidationError, match="Attempt cores"):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            attempt=changed_attempt,
            resource_policy=resource_policy,
        )

    changed_attempt = copy.deepcopy(attempt)
    changed_attempt["required_tools"].append(
        {
            "name": "STAR",
            "version": "2.7.11b",
            "path": "/tools/STAR",
            "resolved_path": "/tools/STAR",
            "sha256": ONE_HASH,
        }
    )
    changed_attempt["required_tools"].sort(key=lambda item: item["name"])
    with pytest.raises(contracts.ContractValidationError, match="tool content"):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            attempt=changed_attempt,
        )

    changed_resources = copy.deepcopy(resource_policy)
    changed_resources["effective"]["stage_memory_mb"]["02b"] = 512
    changed_resources["effective_sha256"] = contracts.canonical_sha256(
        changed_resources["effective"]
    )
    with pytest.raises(contracts.ContractValidationError, match="stage_memory_mb"):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            resource_policy=changed_resources,
        )

    changed_resources = copy.deepcopy(resource_policy)
    changed_resources["symbolic"]["workflow_memory_mb"] = 4096
    changed_resources["symbolic_sha256"] = contracts.canonical_sha256(
        changed_resources["symbolic"]
    )
    with pytest.raises(
        contracts.ContractValidationError,
        match="Symbolic computational resources",
    ):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            resource_policy=changed_resources,
        )

    with pytest.raises(contracts.ContractValidationError, match="implementation"):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            observed_implementation_content_sha256=TWO_HASH,
        )

    with pytest.raises(contracts.ContractValidationError, match="backend semantics"):
        model.validate_successor_run(
            analysis=analysis,
            plan=plan,
            run=run,
            profile=profile,
            observed_backend_semantics_sha256=TWO_HASH,
        )

    changed_plan_record = plan.record
    changed_plan_record["identity"]["backend"]["backend"] = "slurm"
    changed_plan_record["execution_plan_id"] = "plan-" + contracts.canonical_sha256(
        changed_plan_record["identity"]
    )
    changed_plan = model.ExecutionPlan.from_record(changed_plan_record)
    changed_run = model.bind_run(analysis, changed_plan)
    changed_attempt = copy.deepcopy(attempt)
    changed_attempt["run_id"] = changed_run.run_id
    changed_attempt["execution_contract_sha256"] = changed_run.record_sha256
    with pytest.raises(contracts.ContractValidationError, match="executor"):
        model.validate_successor_run(
            analysis=analysis,
            plan=changed_plan,
            run=changed_run,
            profile=profile,
            attempt=changed_attempt,
        )
