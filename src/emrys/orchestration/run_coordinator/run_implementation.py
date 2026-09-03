"""Content identities for the Run-bound local workflow implementation."""

from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from emrys.analyses import (
    AnalysisModuleLoadError,
    BUILTIN_PAIRED_CMH_MODULE_ID,
    LoadedAnalysisModuleV1,
    load_analysis_module,
    module_admission_record,
)
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.application_model import (
    AnalysisRevision,
    ExecutionPlan,
    execution_owner_keys,
    implementation_content_sha256,
)

BACKEND_TARGET = "cohort_slice"
SNAKEFILE_RELATIVE = Path("workflow/Snakefile")
WORKFLOW_PROFILE_RELATIVE = Path("workflow/profiles/local/profile.v9+.yaml")
BACKEND_OPERATION_FLAGS = {
    "execute": (),
    "resume": ("--rerun-triggers", "input", "--ignore-incomplete"),
}

_SCIENTIFIC_ROOTS = (
    ".Rprofile",
    "src/emrys/evidence/canonical_bam_qc",
    "src/emrys/evidence/rseqc_orientation",
    "src/emrys/ingestion",
    "src/emrys/libraries/alignments",
    "src/emrys/libraries/evidence",
    "src/emrys/libraries/argument_parsing.sh",
    "src/emrys/libraries/executable_resolution.sh",
    "src/emrys/libraries/file_checks.sh",
    "src/emrys/libraries/gatk_invocation.sh",
    "src/emrys/libraries/input_contract.R",
    "src/emrys/libraries/quality",
    "src/emrys/libraries/references",
    "src/emrys/libraries/signal_traps.sh",
    "src/emrys/libraries/validation",
    "src/emrys/libraries/process_environment.py",
    "src/emrys/orchestration/run_coordinator/materialization.py",
    "src/emrys/stages",
    "uv.lock",
    "renv.lock",
)
_PROCESSING_ROOTS = (
    "src/emrys/evidence/canonical_bam_qc",
    "src/emrys/evidence/rseqc_orientation",
    "src/emrys/libraries/alignments",
    "src/emrys/libraries/evidence",
    "src/emrys/libraries/quality",
    "src/emrys/libraries/references",
    "src/emrys/libraries/argument_parsing.sh",
    "src/emrys/libraries/executable_resolution.sh",
    "src/emrys/libraries/file_checks.sh",
    "src/emrys/libraries/gatk_invocation.sh",
    "src/emrys/libraries/process_environment.py",
    "src/emrys/libraries/signal_traps.sh",
    "src/emrys/libraries/validation/__init__.py",
    "src/emrys/libraries/validation/errors.py",
    "src/emrys/libraries/validation/inputs.py",
    "src/emrys/libraries/validation/publication.py",
    "src/emrys/libraries/validation/report.py",
    "src/emrys/libraries/validation/runtime.py",
    "src/emrys/libraries/validation/tsv.py",
    "src/emrys/orchestration/run_coordinator/materialization.py",
    "src/emrys/stages/canonical_bam",
    "src/emrys/stages/duplicate_marking",
    "src/emrys/stages/fasta_sidecars",
    "src/emrys/stages/gtf_to_bed12",
    "src/emrys/stages/mechanical_orientation",
    "src/emrys/stages/split_n_cigar",
    "src/emrys/stages/star_alignment",
    "src/emrys/stages/star_index",
)
_ADMISSION_ROOTS = (
    "src/emrys/analyses/__init__.py",
    "src/emrys/contracts/artifacts",
    "src/emrys/contracts/orchestration/api.py",
    "src/emrys/contracts/orchestration/application_model.py",
    "src/emrys/contracts/orchestration/artifact_inventory.py",
    "src/emrys/contracts/schemas/orchestration/v1/application_model.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/attempt_receipt.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/common.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/execution.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/policy.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/reference.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/run_lock.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/task_attempt.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/task_start.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/verified_task.schema.json",
    "src/emrys/contracts/schemas/orchestration/v1/workflow_attempt.schema.json",
    "src/emrys/contracts/schemas/orchestration/v2/attempt_receipt.schema.json",
    "src/emrys/contracts/schemas/orchestration/v2/profile.schema.json",
    "src/emrys/contracts/schemas/orchestration/v3/resource_config.schema.json",
    "src/emrys/contracts/scientific_evidence",
    "src/emrys/libraries/installed_package_identity.py",
    "src/emrys/libraries/source_authority.py",
    "src/emrys/orchestration/run_coordinator/_inspection_admission.py",
    "src/emrys/orchestration/run_coordinator/_inspection_attempts.py",
    "src/emrys/orchestration/run_coordinator/_inspection_evidence.py",
    "src/emrys/orchestration/run_coordinator/all_pass.py",
    "src/emrys/orchestration/run_coordinator/inspection.py",
    "src/emrys/orchestration/run_coordinator/lifecycle.py",
    "src/emrys/orchestration/run_coordinator/run_implementation.py",
    "src/emrys/orchestration/run_coordinator/task.py",
    "workflow/contracts/local_cmh_v2.json",
)
_IMPLEMENTATION_SUFFIXES = {
    ".awk",
    ".json",
    ".py",
    ".R",
    ".sh",
    ".toml",
    ".tsv",
    ".yaml",
}


class RunImplementationError(RuntimeError):
    """The Run-bound implementation could not be identified exactly."""


def _identity_file(path: Path, source_root: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise RunImplementationError(
            f"Run-bound implementation file is unavailable: {path}"
        )
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise RunImplementationError(
            f"Could not read Run-bound implementation file: {path}: {exc}"
        ) from exc
    return {
        "path": path.relative_to(source_root).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _component(source_root: Path, roots: tuple[str, ...], domain: str) -> str:
    files: set[Path] = set()
    for relative in roots:
        path = source_root / relative
        if path.is_dir() and not path.is_symlink():
            files.update(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file()
                and not candidate.is_symlink()
                and candidate.suffix in _IMPLEMENTATION_SUFFIXES
                and "__pycache__" not in candidate.parts
            )
        elif path.name in {".Rprofile", "Snakefile", "uv.lock", "renv.lock"} or (
            path.suffix in _IMPLEMENTATION_SUFFIXES
        ):
            files.add(path)
        else:
            raise RunImplementationError(
                f"Run-bound implementation root is unavailable: {path}"
            )
    rows = [_identity_file(path, source_root) for path in sorted(files)]
    if not rows:
        raise RunImplementationError(
            f"Run-bound implementation closure is empty: {domain}"
        )
    return orchestration_contracts.canonical_sha256(
        {"identity_domain": domain, "files": rows}
    )


def _shared_components(source_root: Path) -> tuple[dict[str, str], ...]:
    return (
        {
            "role": "scientific_computation",
            "logical_name": "local-shared-computation-v1",
            "content_sha256": _component(
                source_root,
                _SCIENTIFIC_ROOTS,
                "emrys.local-shared-scientific-content.v1",
            ),
        },
        {
            "role": "artifact_admission",
            "logical_name": "local-cmh-artifact-admission-v1",
            "content_sha256": _component(
                source_root,
                _ADMISSION_ROOTS,
                "emrys.local-cmh-artifact-admission-content.v1",
            ),
        },
    )


def processing_implementation_identity(source_root: Path) -> str:
    """Identify only executable owner content used through Step 06."""

    return implementation_content_sha256(
        (
            {
                "role": "scientific_computation",
                "logical_name": "local-processing-computation-v1",
                "content_sha256": _component(
                    source_root,
                    _PROCESSING_ROOTS,
                    "emrys.local-processing-scientific-content.v1",
                ),
            },
        )
    )


def _analysis_module_component(module: LoadedAnalysisModuleV1) -> str:
    return orchestration_contracts.canonical_sha256(
        {
            "identity_domain": "emrys.selected-analysis-module.v1",
            "admission": module_admission_record(module),
        }
    )


def implementation_identity(
    source_root: Path,
    module_id: str | None = None,
    *,
    loaded_module: LoadedAnalysisModuleV1 | None = None,
) -> str:
    """Identify shared content plus a selected module only when it executes."""

    components = list(_shared_components(source_root))
    if module_id is not None:
        try:
            module = loaded_module or load_analysis_module(module_id)
        except AnalysisModuleLoadError as exc:
            raise RunImplementationError(str(exc)) from exc
        if module.descriptor.module_id != module_id:
            raise RunImplementationError(
                f"Loaded analysis module differs from selection: {module_id}"
            )
        components.append(
            {
                "role": "scientific_computation",
                "logical_name": f"selected-analysis-module:{module_id}",
                "content_sha256": _analysis_module_component(module),
            }
        )
    return implementation_content_sha256(components)


def execution_module_id(
    analysis: AnalysisRevision,
    plan: ExecutionPlan,
) -> str | None:
    """Return the selected module only when this Run executes its tail."""

    functional = plan.record["identity"]["functional_specification"]
    steps = {
        str(owner["machine_key"]): str(owner["step_id"])
        for owner in functional["owner_tasks"]
    }
    if not any(
        steps.get(owner_key) in {"09", "10"}
        for owner_key in execution_owner_keys(plan)
    ):
        return None
    module = analysis.record["identity"].get("analysis_module")
    return (
        str(module["module_id"])
        if isinstance(module, dict)
        else BUILTIN_PAIRED_CMH_MODULE_ID
    )


def backend_semantics_identity(source_root: Path) -> str:
    """Identify the effective local Snakemake backend semantics."""

    path = source_root / WORKFLOW_PROFILE_RELATIVE
    if path.is_symlink() or not path.is_file():
        raise RunImplementationError(f"Workflow profile is unavailable: {path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise RunImplementationError(
            f"Could not admit workflow profile: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise RunImplementationError("Workflow profile must contain one mapping")
    required = {"executor", "cores", "scheduler", "retries", "keep-incomplete"}
    allowed = required | {"printshellcmds", "show-failed-logs"}
    if set(value) != allowed:
        raise RunImplementationError(
            "Workflow profile fields differ from the reviewed set"
        )
    semantics = {
        key: value[key]
        for key in ("executor", "scheduler", "retries", "keep-incomplete")
    }
    if semantics["executor"] != "local":
        raise RunImplementationError(
            "Run-coordinator workflow profile must use local executor"
        )
    snakefile = _identity_file(source_root / SNAKEFILE_RELATIVE, source_root)
    return orchestration_contracts.canonical_sha256(
        {
            "identity_domain": "emrys.snakemake-backend-semantics.v1",
            **semantics,
            "snakefile_sha256": snakefile["sha256"],
            "target": BACKEND_TARGET,
            "fixed_flags": ["--nocolor"],
            "operation_flags": {
                operation: list(flags)
                for operation, flags in BACKEND_OPERATION_FLAGS.items()
            },
        }
    )


__all__ = (
    "BACKEND_OPERATION_FLAGS",
    "BACKEND_TARGET",
    "RunImplementationError",
    "SNAKEFILE_RELATIVE",
    "WORKFLOW_PROFILE_RELATIVE",
    "backend_semantics_identity",
    "execution_module_id",
    "implementation_identity",
    "processing_implementation_identity",
)
