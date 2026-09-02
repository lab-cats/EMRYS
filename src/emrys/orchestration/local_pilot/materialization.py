"""Canonical production materializer for the fixed local CMH workflow."""

from __future__ import annotations

import hashlib
import os
import re
import socket
import sys
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from emrys import __version__
from emrys import analyses as analysis_modules
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration import artifact_inventory
from emrys.contracts.orchestration.application_model import (
    AnalysisRevision,
    ExecutionPlan,
    RunBinding,
    bind_run,
    build_execution_plan,
    execution_plan_boundary,
    functional_specification_from_profile,
    processing_compatibility_sha256,
    processing_stopping_owner_keys,
    toolchain_from_required_tools,
    validate_successor_run,
)
from emrys.libraries.source_authority import controlled_python_argv
from emrys.orchestration.local_pilot import (
    doctor,
    inspection,
    lifecycle,
    reporting_boundary,
)
from emrys.orchestration.local_pilot.normalization import AnalysisAdmission
from emrys.orchestration.local_pilot.resource_policy import (
    ComputationalResourceDeclaration,
    THREAD_CAPABLE_STAGE_IDS,
    ResourcePlan,
)
from emrys.orchestration.local_pilot.run_implementation import (
    BACKEND_TARGET,
    SNAKEFILE_RELATIVE,
    WORKFLOW_PROFILE_RELATIVE,
    RunImplementationError,
    backend_semantics_identity,
    execution_module_id,
    implementation_identity,
    processing_implementation_identity,
)
from emrys.libraries.process_environment import (
    R_SELECTOR_PREFIXES,
    R_STARTUP_VARIABLES,
    guarded_r_environment,
)

Operation = Literal["execute", "resume"]
_SAFE_ROLE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class MaterializationError(RuntimeError):
    """One admitted-profile attempt could not be planned or published safely."""


@dataclass(frozen=True, slots=True)
class PlannedFile:
    """One create-exclusive file in an immutable attempt plan."""

    path: Path
    data: bytes


@dataclass(frozen=True, slots=True)
class RunCandidate:
    """One complete immutable Run value before filesystem admission."""

    analysis: AnalysisAdmission
    execution_plan: ExecutionPlan
    run_binding: RunBinding

    @property
    def run_id(self) -> str:
        return self.run_binding.run_id


@dataclass(frozen=True, slots=True)
class HistoricalRun:
    """Exact existing execution.v1 authority retained only for resume."""

    analysis: AnalysisAdmission
    run_id: str
    execution_projection_bytes: bytes

    @property
    def execution_projection(self) -> dict[str, Any]:
        return orchestration_contracts.load_json_object_bytes(
            self.execution_projection_bytes,
            "historical execution.v1",
        )


MaterializedRun = RunCandidate | HistoricalRun


@dataclass(frozen=True, slots=True)
class AttemptPlan:
    """Pure, complete publication and command plan for one workflow attempt."""

    run: MaterializedRun
    readiness: doctor.DoctorResult
    resources: ResourcePlan
    operation: Operation
    workspace: Path
    run_root: Path
    workflow_attempt_id: str
    attempt_record_bytes: bytes
    fixed_files: tuple[PlannedFile, ...]
    attempt_files: tuple[PlannedFile, ...]
    new_dispatch_files: tuple[PlannedFile, ...]
    directories: tuple[Path, ...]
    dispatch_count: int

    @property
    def attempt_record(self) -> dict[str, Any]:
        """Return a fresh view of the immutable prepared Attempt record."""

        return orchestration_contracts.load_json_object_bytes(
            self.attempt_record_bytes,
            "prepared workflow Attempt",
        )

    @property
    def config_path(self) -> Path:
        return self.run_root / str(self.attempt_record["workflow_config"]["path"])

    @property
    def lifecycle_request(self) -> lifecycle.LifecycleRequest:
        """Project the exact immutable Attempt into the lifecycle owner."""

        return lifecycle.LifecycleRequest(
            run_root=self.run_root,
            execution_path=self.execution_path,
            profile_path=self.profile_path,
            workflow_config_path=self.config_path,
            snakefile=self.readiness.source_root / SNAKEFILE_RELATIVE,
            python_executable=Path(sys.executable),
            workflow_profile=self.readiness.source_root / WORKFLOW_PROFILE_RELATIVE,
            target=BACKEND_TARGET,
            operation=self.operation,
            attempt_record_bytes=self.attempt_record_bytes,
            request_source_path=self.run.analysis.source_path,
        )

    @property
    def execution_path(self) -> Path:
        return _execution_path(self.run, self.run_root)

    @property
    def profile_path(self) -> Path:
        return self.run_root / "contract" / "profile.json"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def _frozen_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _frozen_json(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_frozen_json(item) for item in value)
    return value


def build_run_candidate(
    analysis: AnalysisAdmission,
    readiness: doctor.DoctorResult,
    declaration: ComputationalResourceDeclaration,
    *,
    scientific_stopping_owner_keys: Sequence[str] | None = None,
    processing_source: Mapping[str, Any] | None = None,
) -> RunCandidate:
    """Construct the complete Run before allocation or Attempt identity exists."""

    required_tools = doctor.required_tool_identities(
        readiness.inspection,
        bindings=readiness.bindings,
        python_executable=Path(sys.executable),
    )
    source = analysis.workflow_inputs
    functional = functional_specification_from_profile(analysis.profile)
    stopping_owner_keys = (
        analysis.profile["required_owner_keys"]
        if scientific_stopping_owner_keys is None
        else scientific_stopping_owner_keys
    )
    module_owner_keys = {task.owner_key for task in analysis.module.descriptor.tasks}
    executes_module = bool(module_owner_keys & set(stopping_owner_keys))
    try:
        implementation_sha256 = implementation_identity(
            readiness.source_root,
            analysis.module.descriptor.module_id if executes_module else None,
            loaded_module=analysis.module if executes_module else None,
        )
        processing_implementation_sha256 = processing_implementation_identity(
            readiness.source_root
        )
        backend_sha256 = backend_semantics_identity(readiness.source_root)
    except RunImplementationError as exc:
        raise MaterializationError(str(exc)) from exc
    toolchain = toolchain_from_required_tools(required_tools)
    resources = declaration.identity_document()
    plan = build_execution_plan(
        functional_specification=functional,
        scientific_stopping_owner_keys=stopping_owner_keys,
        implementation_content_sha256=implementation_sha256,
        toolchain=toolchain,
        backend="local",
        engine="snakemake",
        backend_semantics_sha256=backend_sha256,
        star_index=source["reference"]["star_index"],
        computational_resources=resources,
        processing_compatibility_sha256=processing_compatibility_sha256(
            functional_specification=functional,
            processing_implementation_sha256=processing_implementation_sha256,
            toolchain=toolchain,
            backend="local",
            engine="snakemake",
            star_index=source["reference"]["star_index"],
            computational_resources=resources,
        ),
        processing_source=processing_source,
    )
    return RunCandidate(analysis, plan, bind_run(analysis.revision, plan))


def _execution_path(run: MaterializedRun, root: Path) -> Path:
    name = "run.json" if isinstance(run, RunCandidate) else "normalized.json"
    return root / "contract" / name


def _within(path: Path, root: Path, label: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise MaterializationError(f"{label} must be beneath run_root: {path}") from exc


def _runtime_path(observations: Mapping[str, Any], name: str) -> str:
    return str(observations[name].check.target)


def _one(paths: Mapping[str, list[Path]], adapter: str) -> Path:
    values = paths.get(adapter, [])
    if len(values) != 1:
        raise MaterializationError(
            f"Fixed profile expected one {adapter} path; observed {len(values)}"
        )
    return values[0]


def _scope_ids(
    source: Mapping[str, Any], analysis: AnalysisRevision | None
) -> tuple[str, str, str]:
    if analysis is not None:
        return tuple(
            analysis.scope_id(scope)
            for scope in ("reference", "cohort", "analysis")
        )
    return (
        str(source["reference"]["reference_id"]),
        str(source["analysis"]["cohort_id"]),
        str(source["analysis"]["primary_analysis_id"]),
    )


def _readmit_execution_module(
    run: MaterializedRun,
    source: Mapping[str, Any],
) -> analysis_modules.LoadedAnalysisModuleV1:
    try:
        policy = source["analysis"]["policy"]
        loaded = analysis_modules.readmit_analysis_module(policy)
        if (
            isinstance(run, RunCandidate)
            and policy.get("schema_version") == "emrys.analysis-module-policy.v1"
        ):
            module = policy["module"]
            revision_module = run.analysis.revision.record["identity"][
                "analysis_module"
            ]
            expected = {
                key: module[key]
                for key in ("module_id", "interface_version", "module_version")
            }
            expected["configuration"] = policy["configuration"]
            if revision_module != expected:
                raise analysis_modules.AnalysisModuleLoadError(
                    "Analysis revision differs from persisted module policy"
                )
        return loaded
    except (analysis_modules.AnalysisModuleLoadError, KeyError, TypeError) as exc:
        raise MaterializationError(str(exc)) from exc


def _validator(
    *arguments: str,
) -> tuple[str, ...]:
    return controlled_python_argv(
        sys.executable,
        "-m",
        "emrys",
        "validate",
        *arguments,
        "--execute",
    )


def _r_owner_command(
    bash: str,
    source_root: Path,
    renv_library: Path,
    command: Sequence[str],
) -> tuple[str, ...]:
    selected = guarded_r_environment(source_root, renv_library, base_environment={})
    names = tuple(selected)
    assignments = " ".join(
        f'{name}="${{{index}}}"' for index, name in enumerate(names, start=1)
    )
    patterns = "|".join(
        (*(f"{prefix}*" for prefix in R_SELECTOR_PREFIXES), *R_STARTUP_VARIABLES)
    )
    bootstrap = (
        "for emrys_env_name in $(compgen -A variable); do "
        f'case "$emrys_env_name" in {patterns}) unset "$emrys_env_name";; esac; '
        "done; "
        f'export {assignments}; shift {len(names)}; exec "$@"'
    )
    return (
        bash,
        "-c",
        bootstrap,
        "emrys-r",
        *(selected[name] for name in names),
        *command,
    )


def _task_commands(
    *,
    step_id: str,
    scope_id: str,
    paths: Mapping[str, list[Path]],
    source: Mapping[str, Any],
    analysis_revision: AnalysisRevision | None,
    run_root: Path,
    source_root: Path,
    runtime: Mapping[str, Any],
    all_paths: Mapping[tuple[str, str], Mapping[str, list[Path]]],
    threads: int | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[Path, ...]]:
    sample_rows = {str(row["sample_id"]): row for row in source["samples"]["rows"]}
    partition_rows = {
        str(row["partition_id"]): row for row in source["partitions"]["rows"]
    }
    reference = source["reference"]
    analysis = source["analysis"]
    sample_manifest = Path(str(source["samples"]["manifest"]["path"]))
    partition_manifest = Path(str(source["partitions"]["manifest"]["path"]))
    fasta = Path(str(reference["fasta"]["path"]))
    gtf = Path(str(reference["gtf"]["path"]))
    reference_id = (
        analysis_revision.scope_id("reference")
        if analysis_revision is not None
        else str(reference["reference_id"])
    )
    cohort_id = (
        analysis_revision.scope_id("cohort")
        if analysis_revision is not None
        else str(analysis["cohort_id"])
    )
    partition_scopes = {
        partition_id: (
            analysis_revision.scope_id("cohort_partition", partition_id)
            if analysis_revision is not None
            else f"{cohort_id}__{partition_id}"
        )
        for partition_id in partition_rows
    }
    bash = _runtime_path(runtime, "bash")
    star = _runtime_path(runtime, "star")
    samtools = _runtime_path(runtime, "samtools")
    java = _runtime_path(runtime, "java")
    gatk = _runtime_path(runtime, "gatk")
    picard_jar = _runtime_path(runtime, "picard_jar")
    bcftools = _runtime_path(runtime, "bcftools")
    infer_experiment = _runtime_path(runtime, "infer_experiment")
    gunzip = _runtime_path(runtime, "gunzip")
    rscript = _runtime_path(runtime, "rscript")
    renv_library = Path(_runtime_path(runtime, "renv_library"))
    validation = next(
        (
            path
            for adapter, values in paths.items()
            if adapter.endswith("_validation_report_v1")
            for path in values
        ),
        None,
    )
    if validation is None:
        raise MaterializationError(
            f"No validation report for Step {step_id}/{scope_id}"
        )

    def declared_threads() -> int:
        if threads is None:
            raise MaterializationError(
                f"Step {step_id} has no declared thread allocation"
            )
        return threads

    if step_id == "00a":
        index_members = paths.get("step00a_star_index_v1", [])
        if (
            len(index_members) != 15
            or len({path.parent for path in index_members}) != 1
        ):
            raise MaterializationError(
                "Step 00a requires exactly 15 index members under one directory"
            )
        index_dir = index_members[0].parent
        producer = (
            bash,
            str(
                source_root / "src/emrys/stages/star_index/step_00a_build_star_index.sh"
            ),
            "--reference-fasta",
            str(fasta),
            "--reference-gtf",
            str(gtf),
            "--index-dir",
            str(index_dir),
            "--threads",
            str(declared_threads()),
            "--sjdb-overhang",
            str(reference["star_index"]["sjdb_overhang"]),
            "--genome-sa-index-nbases",
            str(reference["star_index"]["genome_sa_index_nbases"]),
            "--star-bin",
            star,
            "--execute",
        )
        validator = _validator(
            "star-index",
            "--scope-id",
            reference_id,
            "--index-dir",
            str(index_dir),
            "--reference-fasta",
            str(fasta),
            "--reference-gtf",
            str(gtf),
            "--parameter-path-base",
            str(run_root),
            "--expected-sjdb-overhang",
            str(reference["star_index"]["sjdb_overhang"]),
            "--expected-genome-sa-index-nbases",
            str(reference["star_index"]["genome_sa_index_nbases"]),
            "--output",
            str(validation),
        )
        return producer, validator, (fasta, gtf)

    if step_id == "00b":
        bed = _one(paths, "step00b_bed12_v1")
        producer = controlled_python_argv(
            sys.executable,
            "-m",
            "emrys",
            "convert",
            "gtf-to-bed12",
            "--gtf",
            str(gtf),
            "--bed",
            str(bed),
            "--execute",
        )
        validator = _validator(
            "bed12",
            "--scope-id",
            reference_id,
            "--bed12",
            str(bed),
            "--source-gtf",
            str(gtf),
            "--output",
            str(validation),
        )
        return producer, validator, (gtf,)

    if step_id == "00c":
        fai = _one(paths, "step00c_reference_fai_v1")
        dictionary = _one(paths, "step00c_reference_dict_v1")
        producer = (
            bash,
            str(
                source_root
                / "src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh"
            ),
            "--reference-fasta",
            str(fasta),
            "--samtools-bin",
            samtools,
            "--gatk-bin",
            gatk,
            "--java-bin",
            java,
            "--execute",
        )
        validator = _validator(
            "fasta-sidecars",
            "--scope-id",
            reference_id,
            "--reference-fasta",
            str(fasta),
            "--reference-fai",
            str(fai),
            "--reference-dict",
            str(dictionary),
            "--output",
            str(validation),
        )
        return producer, validator, (fasta,)

    if step_id in {"01", "02", "02b", "03", "04", "05", "06"}:
        sample = sample_rows[scope_id]
        star_bam = _one(all_paths["01", scope_id], "step01_star_bam_v1")
        canonical_bam = _one(all_paths["02", scope_id], "step02_canonical_bam_v1")
        canonical_bai = _one(all_paths["02", scope_id], "step02_canonical_bai_v1")
        if step_id == "01":
            index_paths = tuple(all_paths["00a", reference_id]["step00a_star_index_v1"])
            index_dir = index_paths[0].parent
            bam = _one(paths, "step01_star_bam_v1")
            log_final = _one(paths, "step01_star_log_final_v1")
            log_out = _one(paths, "step01_star_log_v1")
            log_progress = _one(paths, "step01_star_log_progress_v1")
            sj_out = _one(paths, "step01_star_sj_v1")
            producer = (
                bash,
                str(
                    source_root
                    / "src/emrys/stages/star_alignment/step_01_star_align.sh"
                ),
                "--sample-id",
                scope_id,
                "--r1-fastq",
                str(sample["r1_fastq"]["path"]),
                "--r2-fastq",
                str(sample["r2_fastq"]["path"]),
                "--star-index",
                str(index_dir),
                "--output-dir",
                str(bam.parent),
                "--threads",
                str(declared_threads()),
                "--star-bin",
                star,
                "--gunzip-bin",
                gunzip,
                "--no-clobber",
                "--execute",
            )
            validator = _validator(
                "star-alignment",
                "--scope-id",
                scope_id,
                "--bam",
                str(bam),
                "--log-final",
                str(log_final),
                "--log-out",
                str(log_out),
                "--log-progress",
                str(log_progress),
                "--sj-out",
                str(sj_out),
                "--output",
                str(validation),
            )
            return (
                producer,
                validator,
                (
                    Path(str(sample["r1_fastq"]["path"])),
                    Path(str(sample["r2_fastq"]["path"])),
                    *index_paths,
                ),
            )
        if step_id == "02":
            bam = _one(paths, "step02_canonical_bam_v1")
            bai = _one(paths, "step02_canonical_bai_v1")
            producer = (
                bash,
                str(
                    source_root
                    / "src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh"
                ),
                "--sample-id",
                scope_id,
                "--input-alignment",
                str(star_bam),
                "--output-dir",
                str(bam.parent),
                "--threads",
                str(declared_threads()),
                "--samtools-bin",
                samtools,
                "--no-clobber",
                "--execute",
            )
            validator = _validator(
                "canonical-bam",
                "--scope-id",
                scope_id,
                "--bam",
                str(bam),
                "--bai",
                str(bai),
                "--samtools-bin",
                samtools,
                "--output",
                str(validation),
            )
            return producer, validator, (star_bam,)
        if step_id == "02b":
            quickcheck = _one(paths, "step02b_quickcheck_v1")
            flagstat = _one(paths, "step02b_flagstat_v1")
            producer = (
                bash,
                str(
                    source_root
                    / "src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh"
                ),
                "--sample-id",
                scope_id,
                "--bam",
                str(canonical_bam),
                "--output-dir",
                str(quickcheck.parent),
                "--samtools-bin",
                samtools,
                "--no-clobber",
                "--execute",
            )
            validator = _validator(
                "canonical-bam-qc",
                "--scope-id",
                scope_id,
                "--quickcheck",
                str(quickcheck),
                "--flagstat",
                str(flagstat),
                "--output",
                str(validation),
            )
            return producer, validator, (canonical_bam, canonical_bai)
        if step_id == "03":
            infer = _one(paths, "step03_rseqc_infer_v1")
            bed = _one(all_paths["00b", reference_id], "step00b_bed12_v1")
            producer = (
                bash,
                str(
                    source_root
                    / "src/emrys/evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh"
                ),
                "--sample-id",
                scope_id,
                "--input-bam",
                str(canonical_bam),
                "--bed12",
                str(bed),
                "--output-dir",
                str(infer.parent),
                "--infer-experiment-bin",
                infer_experiment,
                "--no-clobber",
                "--execute",
            )
            validator = _validator(
                "rseqc-orientation",
                "--scope-id",
                scope_id,
                "--infer-report",
                str(infer),
                "--output",
                str(validation),
            )
            return producer, validator, (canonical_bam, canonical_bai, bed)
        if step_id == "04":
            bam = _one(paths, "step04_markdup_bam_v1")
            bai = _one(paths, "step04_markdup_bai_v1")
            metrics = _one(paths, "step04_markdup_metrics_v1")
            producer = (
                bash,
                str(
                    source_root
                    / "src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh"
                ),
                "--sample-id",
                scope_id,
                "--input-bam",
                str(canonical_bam),
                "--output-dir",
                str(bam.parent),
                "--metrics-dir",
                str(metrics.parent),
                "--picard-jar",
                picard_jar,
                "--java-bin",
                java,
                "--samtools-bin",
                samtools,
                "--no-clobber",
                "--execute",
            )
            validator = _validator(
                "duplicate-marking",
                "--scope-id",
                scope_id,
                "--bam",
                str(bam),
                "--bai",
                str(bai),
                "--metrics",
                str(metrics),
                "--samtools-bin",
                samtools,
                "--output",
                str(validation),
            )
            return producer, validator, (canonical_bam, canonical_bai, Path(picard_jar))
        if step_id == "05":
            markdup_bam = _one(all_paths["04", scope_id], "step04_markdup_bam_v1")
            markdup_bai = _one(all_paths["04", scope_id], "step04_markdup_bai_v1")
            bam = _one(paths, "step05_split_bam_v1")
            bai = _one(paths, "step05_split_bai_v1")
            fai = _one(all_paths["00c", reference_id], "step00c_reference_fai_v1")
            dictionary = _one(
                all_paths["00c", reference_id], "step00c_reference_dict_v1"
            )
            producer = (
                bash,
                str(
                    source_root
                    / "src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"
                ),
                "--sample-id",
                scope_id,
                "--input-bam",
                str(markdup_bam),
                "--reference-fasta",
                str(fasta),
                "--output-dir",
                str(bam.parent),
                "--gatk-bin",
                gatk,
                "--samtools-bin",
                samtools,
                "--java-bin",
                java,
                "--no-clobber",
                "--execute",
            )
            validator = _validator(
                "split-n-cigar",
                "--scope-id",
                scope_id,
                "--bam",
                str(bam),
                "--bai",
                str(bai),
                "--reference-fasta",
                str(fasta),
                "--reference-fai",
                str(fai),
                "--reference-dict",
                str(dictionary),
                "--samtools-bin",
                samtools,
                "--output",
                str(validation),
            )
            return (
                producer,
                validator,
                (markdup_bam, markdup_bai, fasta, fai, dictionary),
            )
        split_bam = _one(all_paths["05", scope_id], "step05_split_bam_v1")
        split_bai = _one(all_paths["05", scope_id], "step05_split_bai_v1")
        fwd = _one(paths, "step06_fwd_bam_v1")
        fwd_bai = _one(paths, "step06_fwd_bai_v1")
        rev = _one(paths, "step06_rev_bam_v1")
        rev_bai = _one(paths, "step06_rev_bai_v1")
        counts = _one(paths, "step06_orientation_counts_v1")
        producer = controlled_python_argv(
            sys.executable,
            "-m",
            "emrys.stages.mechanical_orientation.producer",
            "--sample-id",
            scope_id,
            "--input-bam",
            str(split_bam),
            "--output-dir",
            str(fwd.parent),
            "--qc-dir",
            str(counts.parent),
            "--threads",
            str(declared_threads()),
            "--samtools-bin",
            samtools,
            "--no-clobber",
            "--execute",
        )
        validator = _validator(
            "mechanical-orientation",
            "--scope-id",
            scope_id,
            "--fwd-bam",
            str(fwd),
            "--fwd-bai",
            str(fwd_bai),
            "--rev-bam",
            str(rev),
            "--rev-bai",
            str(rev_bai),
            "--counts",
            str(counts),
            "--output",
            str(validation),
        )
        return producer, validator, (split_bam, split_bai)

    if step_id == "07":
        try:
            partition_id = next(
                key for key, value in partition_scopes.items() if value == scope_id
            )
        except StopIteration as exc:
            raise MaterializationError(
                f"Unknown content-bound partition scope: {scope_id}"
            ) from exc
        partition = partition_rows[partition_id]
        vcf_paths = paths["step07_mpileup_vcf_v1"]
        if len(vcf_paths) != 2:
            raise MaterializationError("Step 07 requires exactly two orientation VCFs")
        fwd, rev = vcf_paths
        if "REV_like" in fwd.name:
            fwd, rev = rev, fwd
        receipt = _one(paths, "step07_mpileup_receipt_v1")
        orientation_inputs: list[Path] = []
        for sample_id in sample_rows:
            orientation = all_paths["06", sample_id]
            orientation_inputs.extend(
                (
                    _one(orientation, "step06_fwd_bam_v1"),
                    _one(orientation, "step06_fwd_bai_v1"),
                    _one(orientation, "step06_rev_bam_v1"),
                    _one(orientation, "step06_rev_bai_v1"),
                )
            )
        orientation_root = orientation_inputs[0].parents[1]
        mpileup_root = fwd.parents[2]
        fai = _one(all_paths["00c", reference_id], "step00c_reference_fai_v1")
        producer = controlled_python_argv(
            sys.executable,
            "-m",
            "emrys.stages.partitioned_cohort_mpileup.producer",
            "--cohort-id",
            cohort_id,
            "--sample-manifest",
            str(sample_manifest),
            "--partition-manifest",
            str(partition_manifest),
            "--partition-id",
            partition_id,
            "--orientation-root",
            str(orientation_root),
            "--reference-fasta",
            str(fasta),
            "--output-root",
            str(mpileup_root),
            "--bcftools-bin",
            bcftools,
            "--no-clobber",
            "--execute",
        )
        validator = _validator(
            "partitioned-cohort-mpileup",
            "--scope-id",
            scope_id,
            "--cohort-id",
            cohort_id,
            "--partition-id",
            partition_id,
            "--sample-manifest",
            str(sample_manifest),
            "--partition-manifest",
            str(partition_manifest),
            "--reference-fai",
            str(fai),
            "--fwd-vcf",
            str(fwd),
            "--rev-vcf",
            str(rev),
            "--receipt",
            str(receipt),
            "--output",
            str(validation),
        )
        selector = partition.get("selector_file")
        selector_inputs = () if selector is None else (Path(str(selector["path"])),)
        return (
            producer,
            validator,
            (
                sample_manifest,
                partition_manifest,
                fasta,
                fai,
                *selector_inputs,
                *orientation_inputs,
            ),
        )

    if step_id == "08":
        sites = _one(paths, "step08_sites_v1")
        inputs = _one(paths, "step08_inputs_v1")
        summary = _one(paths, "step08_summary_v1")
        step07_inputs = tuple(
            path
            for partition_id in partition_rows
            for adapter in ("step07_mpileup_vcf_v1", "step07_mpileup_receipt_v1")
            for path in all_paths["07", partition_scopes[partition_id]][adapter]
        )
        step07_root = step07_inputs[0].parents[2]
        arguments = (
            "--cohort-id",
            cohort_id,
            "--sample-manifest",
            str(sample_manifest),
            "--partition-manifest",
            str(partition_manifest),
            "--step07-root",
            str(step07_root),
            "--annotation-gtf",
            str(gtf),
            "--output-root",
            str(sites.parents[1]),
            "--qc-root",
            str(summary.parent),
            "--threads",
            str(declared_threads()),
            "--rscript-bin",
            rscript,
            "--r-script",
            str(
                source_root
                / "src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R"
            ),
            "--no-clobber",
            "--execute",
        )
        producer = _r_owner_command(
            bash,
            source_root,
            renv_library,
            controlled_python_argv(
                sys.executable,
                "-m",
                "emrys.stages.cohort_candidate_preprocessing.producer",
                *arguments,
            ),
        )
        validator = _validator(
            "cohort-candidate-preprocessing",
            "--cohort-id",
            cohort_id,
            "--sample-manifest",
            str(sample_manifest),
            "--partition-manifest",
            str(partition_manifest),
            "--annotation-gtf",
            str(gtf),
            "--sites",
            str(sites),
            "--inputs",
            str(inputs),
            "--summary",
            str(summary),
            "--output",
            str(validation),
        )
        return (
            producer,
            validator,
            (sample_manifest, partition_manifest, gtf, *step07_inputs),
        )

    raise MaterializationError(f"Unsupported core processing Step: {step_id}")


def _dispatches(
    run: MaterializedRun,
    source: Mapping[str, Any],
    readiness: doctor.DoctorResult,
    run_root: Path,
    attempt_id: str,
    compact_time: str,
    retained: Mapping[tuple[str, str], dict[str, str]],
    resources: ResourcePlan,
    processing_source_root: Path | None,
    bound_input_snapshots: Mapping[Path, Mapping[str, Any]],
) -> tuple[
    tuple[PlannedFile, ...], dict[str, dict[str, dict[str, str]]], tuple[Path, ...]
]:
    successor = isinstance(run, RunCandidate)
    analysis_revision = run.analysis.revision if successor else None
    profile = run.analysis.profile
    inventory: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in artifact_inventory.project_rows(
        source,
        profile,
        analysis_revision,
        processing_source_root,
    ):
        item = dict(row)
        path = Path(str(row["source_path"]))
        item["path"] = path if path.is_absolute() else run_root / path
        inventory.setdefault((str(row["step_id"]), str(row["scope_id"])), []).append(item)
    paths_by_scope: dict[tuple[str, str], dict[str, list[Path]]] = {}
    for key, rows in inventory.items():
        adapters: dict[str, list[Path]] = {}
        for row in rows:
            adapters.setdefault(str(row["adapter"]), []).append(row["path"])
        paths_by_scope[key] = adapters
    runtime = {
        item.check.check_id: item for item in readiness.inspection.observations
    }
    planned: list[PlannedFile] = []
    references: dict[str, dict[str, dict[str, str]]] = {}
    directories: set[Path] = set()
    authority = (
        run.execution_projection
        if isinstance(run, HistoricalRun)
        else inspection.SuccessorRunAuthority(
            run.analysis.revision, run.execution_plan, run.run_binding
        )
    )
    expected = inspection.expected_tasks(authority, profile)
    owners = {str(item["machine_key"]): item for item in profile["owner_tasks"]}
    if readiness.source_commit is None:
        raise MaterializationError("Task planning requires an admitted source commit")
    module = run.analysis.module.descriptor
    module_tasks = {task.owner_key: task for task in module.tasks}
    scheduled_module_owners = {
        task.machine_key for task in expected if task.machine_key in module_tasks
    }
    if scheduled_module_owners:
        module = _readmit_execution_module(run, source).descriptor
        module_tasks = {task.owner_key: task for task in module.tasks}
        for owner_key in scheduled_module_owners:
            requirement = module_tasks[owner_key]
            minimum = (
                resources.workflow_memory_mb
                if requirement.stage_memory_mb == "workflow"
                else requirement.stage_memory_mb
            )
            if dict(resources.stage_memory_mb)[requirement.step_id] < minimum:
                raise MaterializationError(
                    f"Analysis module Step {requirement.step_id} requires at least "
                    f"{minimum} MiB"
                )
            if resources.threads_for(requirement.step_id) < requirement.minimum_threads:
                raise MaterializationError(
                    f"Analysis module Step {requirement.step_id} requires at least "
                    f"{requirement.minimum_threads} threads"
                )
    reference_id, cohort_id, analysis_id = _scope_ids(source, analysis_revision)
    analysis_identity = (
        None if analysis_revision is None else analysis_revision.record["identity"]
    )
    scope_ids = {
        "reference": (reference_id,),
        "sample": tuple(
            str(row["sample_id"])
            for row in (
                source["samples"]["rows"]
                if analysis_identity is None
                else analysis_identity["samples"]
            )
        ),
        "cohort_partition": tuple(
            (
                f"{cohort_id}__{row['partition_id']}"
                if analysis_revision is None
                else analysis_revision.scope_id(
                    "cohort_partition", str(row["partition_id"])
                )
            )
            for row in source["partitions"]["rows"]
        ),
        "cohort": (cohort_id,),
        "analysis": (analysis_id,),
    }
    policy = source["analysis"]["policy"]
    configuration = (
        dict(policy["configuration"])
        if policy["schema_version"] == "emrys.analysis-module-policy.v1"
        else {
            key: value
            for key, value in policy.items()
            if key not in {"schema_version", "analysis_id"}
        }
    )
    for index, task in enumerate(expected, start=1):
        identity = (task.machine_key, task.scope_id)
        references.setdefault(task.machine_key, {})
        if identity in retained:
            references[task.machine_key][task.scope_id] = dict(retained[identity])
            continue
        owner = owners[task.machine_key]
        step_id = str(owner["step_id"])
        adapters = paths_by_scope[step_id, task.scope_id]
        module_task = module_tasks.get(task.machine_key)
        validation_adapter = (
            next(
                output.adapter
                for output in module_task.outputs
                if output.kind == "validation_report"
            )
            if module_task is not None
            else next(
                adapter
                for adapter in adapters
                if adapter.endswith("_validation_report_v1")
            )
        )
        validation = _one(adapters, validation_adapter)
        outputs = tuple(
            path
            for adapter, values in adapters.items()
            if adapter != validation_adapter and adapter != "step00c_reference_fasta_v1"
            for path in values
        )
        if module_task is None:
            producer, validator, input_paths = _task_commands(
                step_id=step_id,
                scope_id=task.scope_id,
                paths=adapters,
                source=source,
                analysis_revision=analysis_revision,
                run_root=run_root,
                source_root=readiness.source_root,
                runtime=runtime,
                all_paths=paths_by_scope,
                threads=(
                    resources.threads_for(step_id)
                    if step_id in THREAD_CAPABLE_STAGE_IDS
                    else None
                ),
            )
            planned_inputs = tuple(
                (f"input_{input_index:03d}", path)
                for input_index, path in enumerate(input_paths, start=1)
            )
            planned_outputs = tuple(
                (f"output_{output_index:03d}", path)
                for output_index, path in enumerate(outputs, start=1)
            )
        else:
            declared_inputs: dict[str, tuple[Path, ...]] = {}
            for predecessor in module_task.inputs:
                producer_owner = owners.get(predecessor.producer)
                if producer_owner is None:
                    raise MaterializationError(
                        f"Analysis module predecessor is absent: {predecessor.producer}"
                    )
                predecessor_step = str(producer_owner["step_id"])
                predecessor_scopes = scope_ids[str(producer_owner["scope_type"])]
                for adapter in predecessor.adapters:
                    if adapter in declared_inputs:
                        raise MaterializationError(
                            f"Analysis module repeats input adapter {adapter}"
                        )
                    try:
                        declared_inputs[adapter] = tuple(
                            path
                            for scope in predecessor_scopes
                            for path in paths_by_scope[
                                predecessor_step, scope
                            ][adapter]
                        )
                    except KeyError as exc:
                        raise MaterializationError(
                            "Analysis module predecessor artifact is absent: "
                            f"{predecessor.producer}:{adapter}"
                        ) from exc
            declared_outputs = {
                output.adapter: _one(adapters, output.adapter)
                for output in module_task.outputs
            }
            planning_configuration = orchestration_contracts.load_json_object_bytes(
                orchestration_contracts.canonical_json_bytes(configuration),
                "analysis-module planning configuration",
            )
            context = analysis_modules.TaskPlanningContextV1(
                reference_id=reference_id,
                cohort_id=cohort_id,
                analysis_id=analysis_id,
                sample_manifest=Path(str(source["samples"]["manifest"]["path"])),
                partition_manifest=Path(
                    str(source["partitions"]["manifest"]["path"])
                ),
                reference_fasta=Path(str(source["reference"]["fasta"]["path"])),
                reference_gtf=Path(str(source["reference"]["gtf"]["path"])),
                source_commit=str(readiness.source_commit),
                configuration=_frozen_json(planning_configuration),
                inputs=MappingProxyType(declared_inputs),
                outputs=MappingProxyType(declared_outputs),
                runtime_paths=MappingProxyType(
                    {
                        check_id: _runtime_path(runtime, check_id)
                        for check_id in analysis_modules.dependency_ids(module)
                    }
                ),
                python_command=lambda command: controlled_python_argv(
                    sys.executable, *command
                ),
                r_owner_command=lambda command: _r_owner_command(
                    _runtime_path(runtime, "bash"),
                    readiness.source_root,
                    Path(_runtime_path(runtime, "renv_library")),
                    command,
                ),
                validator_command=lambda command: _validator(*command),
                threads=resources.threads_for(step_id),
            )
            try:
                commands = module_task.plan(context)
            except (analysis_modules.AnalysisTaskPlanningError, KeyError) as exc:
                raise MaterializationError(
                    f"Analysis module task planning failed for {task.machine_key}: {exc}"
                ) from exc
            if not isinstance(commands, analysis_modules.TaskCommandPlanV1):
                raise MaterializationError(
                    f"Analysis module returned no task plan for {task.machine_key}"
                )
            producer, validator, module_inputs = commands
            if any(
                not isinstance(argv, tuple)
                or not argv
                or any(not isinstance(value, str) or not value for value in argv)
                for argv in (producer, validator)
            ) or any(
                not isinstance(item, analysis_modules.TaskInputV1)
                or _SAFE_ROLE_RE.fullmatch(item.role) is None
                or not isinstance(item.path, Path)
                for item in module_inputs
            ):
                raise MaterializationError(
                    f"Analysis module returned an invalid task plan for {task.machine_key}"
                )
            occupied_paths = {item.path for item in module_inputs}
            module_inputs = (
                *module_inputs,
                *(
                    analysis_modules.TaskInputV1(
                        f"dependency.{dependency.dependency_id}",
                        Path(dependency.target),
                    )
                    for dependency in sorted(
                        module.dependencies,
                        key=lambda item: item if isinstance(item, str) else item.dependency_id,
                    )
                    if isinstance(dependency, analysis_modules.AnalysisDependencyV1)
                    and dependency.kind in {"executable", "file"}
                    and Path(dependency.target) not in occupied_paths
                ),
            )
            input_roles = [item.role for item in module_inputs]
            input_paths = [item.path for item in module_inputs]
            output_roles = [
                output.adapter
                for output in module_task.outputs
                if output.adapter != validation_adapter
            ]
            if (
                len(set(input_roles)) != len(input_roles)
                or len(set(input_paths)) != len(input_paths)
                or set(input_roles) & set(output_roles)
            ):
                raise MaterializationError(
                    f"Analysis module task {task.machine_key} repeats a provenance role or path"
                )
            required_inputs = {
                path for paths in declared_inputs.values() for path in paths
            }
            if not required_inputs <= set(input_paths):
                raise MaterializationError(
                    f"Analysis module task {task.machine_key} omitted declared inputs"
                )
            planned_inputs = tuple(module_inputs)
            planned_outputs = tuple(
                (output.adapter, declared_outputs[output.adapter])
                for output in module_task.outputs
                if output.adapter != validation_adapter
            )
        suffix = hashlib.sha256(
            f"{attempt_id}:{task.machine_key}:{task.scope_id}".encode()
        ).hexdigest()[:32]
        owner_run_token = f"owner-{suffix}"
        if step_id == "00b":
            producer = (*producer, "--run-token", owner_run_token)
        producer = (
            _runtime_path(runtime, "bash"), "-c",
            'export EMRYS_RUN_TOKEN="$1" EMRYS_SHA256_PYTHON="$2" '
            'EMRYS_REQUIRE_BOUND_SHA256=1; shift 2; exec "$@"',
            "emrys-owner",
            owner_run_token,
            _runtime_path(runtime, "sha256_python"),
            *producer,
        )
        task_id = f"task-{compact_time}-{suffix}"
        task_root = (
            run_root
            / "attempts"
            / attempt_id
            / "tasks"
            / task.machine_key
            / task.scope_id
        )
        dispatch_path = (
            run_root
            / "contract"
            / "dispatch"
            / attempt_id
            / task.machine_key
            / f"{task.scope_id}.json"
        )
        input_declarations = []
        for role, path in planned_inputs:
            declaration = {
                "role": role,
                "path": str(path),
            }
            snapshot = bound_input_snapshots.get(path)
            if (
                processing_source_root is not None
                and path.is_relative_to(processing_source_root)
                and snapshot is None
            ):
                raise MaterializationError(
                    f"Reused processing input lacks an admitted source snapshot: {path}"
                )
            if snapshot is not None:
                declaration.update(
                    {
                        "size_bytes": int(snapshot["size_bytes"]),
                        "sha256": str(snapshot["sha256"]),
                    }
                )
            input_declarations.append(declaration)
        record = {
            "schema_version": "emrys.local-task-dispatch.v1",
            "run_root": str(run_root),
            "execution_path": str(_execution_path(run, run_root)),
            "profile_path": str(run_root / "contract/profile.json"),
            "workflow_attempt_id": attempt_id,
            "task_attempt_id": task_id,
            "owner_run_token": owner_run_token,
            "machine_key": task.machine_key,
            "scope": task.scope,
            "producer_argv": list(producer),
            "validator_argv": list(validator),
            "inputs": input_declarations,
            "outputs": [
                {"role": role, "path": str(path)}
                for role, path in planned_outputs
            ],
            "validation_report_path": str(validation),
            "native_receipt_path": None,
            "task_start_path": str(
                run_root
                / "state"
                / "task-starts"
                / task.machine_key
                / f"{task.scope_id}.json"
            ),
            "task_attempt_path": str(task_root / "task-attempt.json"),
            "verified_task_path": str(
                run_root
                / "state"
                / "verified"
                / task.machine_key
                / f"{task.scope_id}.json"
            ),
            "stdout_path": str(task_root / "stdout.log"),
            "stderr_path": str(task_root / "stderr.log"),
        }
        data = orchestration_contracts.canonical_json_bytes(record)
        planned.append(PlannedFile(dispatch_path, data))
        references[task.machine_key][task.scope_id] = {
            "path": str(dispatch_path),
            "sha256": _sha256(data),
        }
        output_directories = {
            path.parent for path in outputs if run_root in path.parents
        }
        if step_id == "00a":
            if len(output_directories) != 1:
                raise MaterializationError(
                    "Step 00a requires one create-absent STAR index directory"
                )
            output_directories = {next(iter(output_directories)).parent}
        directories.update(
            {
                dispatch_path.parent,
                validation.parent,
                *output_directories,
                run_root / "state" / "task-starts" / task.machine_key,
                run_root / "state" / "verified" / task.machine_key,
            }
        )
    return tuple(planned), references, tuple(sorted(directories))


def build_attempt_plan(
    run: MaterializedRun,
    readiness: doctor.DoctorResult,
    workspace: Path,
    *,
    resources: ResourcePlan,
    operation: Operation,
    placement: Mapping[str, Any] | None = None,
    supersedes_workflow_attempt_id: str | None = None,
    retained_dispatches: Mapping[tuple[str, str], dict[str, str]] | None = None,
    retained_runtime_profile_path: Path | None = None,
    processing_source: inspection.ProcessingSourceAdmission | None = None,
) -> AttemptPlan:
    """Build one complete attempt without touching the filesystem."""

    analysis = run.analysis
    successor = isinstance(run, RunCandidate)
    executor = (
        str(run.execution_plan.record["identity"]["backend"]["backend"])
        if successor
        else "local"
    )
    execution_bytes = (
        run.run_binding.canonical_bytes if successor else run.execution_projection_bytes
    )
    resource_policy_record = resources.policy_record()
    workflow_cores = resources.workflow_cores
    now = datetime.now(UTC).replace(microsecond=0)
    compact = now.strftime("%Y%m%dT%H%M%SZ")
    created_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    suffix = uuid.uuid4().hex
    attempt_id = f"workflow-{compact}-{suffix}"
    owner_token = f"workflow-owner-{suffix}"
    workspace_path = _absolute(workspace)
    run_root = workspace_path / "runs" / run.run_id
    source = (
        run.execution_projection
        if isinstance(run, HistoricalRun)
        else {**run.analysis.workflow_inputs, "run_id": run.run_id}
    )
    selected_sample_manifest = analysis.selected_sample_manifest_bytes
    selected_sample_file = None
    if (
        successor
        and selected_sample_manifest is not None
        and execution_plan_boundary(run.execution_plan) == "analysis"
    ):
        selected_sample_path = (
            run_root
            / "contract"
            / "workflow-inputs"
            / attempt_id
            / "samples.tsv"
        )
        source = {
            **source,
            "samples": {
                **source["samples"],
                "manifest": {
                    "path": str(selected_sample_path),
                    "size_bytes": len(selected_sample_manifest),
                    "sha256": _sha256(selected_sample_manifest),
                },
            },
        }
        selected_sample_file = PlannedFile(
            selected_sample_path,
            selected_sample_manifest,
        )
    plan_source = (
        run.execution_plan.record["identity"].get("processing_source")
        if isinstance(run, RunCandidate)
        else None
    )
    if (plan_source is None) != (processing_source is None) or (
        processing_source is not None and processing_source.binding != plan_source
    ):
        raise MaterializationError(
            "Attempt processing-source admission differs from its immutable Run"
        )
    processing_source_root = (
        None if processing_source is None else processing_source.root
    )
    bound_input_snapshots = {
        Path(str(snapshot["path"])): snapshot
        for snapshot in (
            () if processing_source is None else processing_source.artifact_snapshots
        )
    }
    if selected_sample_file is not None:
        bound_input_snapshots[selected_sample_file.path] = source["samples"][
            "manifest"
        ]
    source_root = readiness.source_root
    if retained_runtime_profile_path is not None:
        if successor or operation != "resume":
            raise MaterializationError(
                "Only a historical resume may retain its predecessor runtime profile"
            )
        runtime_profile_path = _absolute(retained_runtime_profile_path)
    else:
        runtime_profile_path = (
            run_root / "contract" / "runtime-profiles" / f"{attempt_id}.tsv"
        )
    required_tools = doctor.required_tool_identities(
        readiness.inspection,
        bindings=readiness.bindings,
        python_executable=Path(sys.executable),
        runtime_profile_path=runtime_profile_path,
    )
    python_identity = next(item for item in required_tools if item["name"] == "python")
    normalizer_identity = {
        **python_identity,
        "name": "emrys",
        "version": __version__,
    }
    retained = {} if retained_dispatches is None else dict(retained_dispatches)
    dispatch_files, dispatch_references, dispatch_directories = _dispatches(
        run,
        source,
        readiness,
        run_root,
        attempt_id,
        compact,
        retained,
        resources,
        processing_source_root,
        bound_input_snapshots,
    )
    reporting_files, reporting_config, reporting_directories = (
        reporting_boundary._attempt_reporting_materialization(
            source,
            analysis.profile,
            run_root,
            analysis=(analysis.revision if successor else None),
            attempt_id=(attempt_id if successor else None),
            processing_source_root=processing_source_root,
        )
    )
    fixed_files = [
        PlannedFile(
            run_root / "contract/profile.json",
            orchestration_contracts.canonical_json_bytes(analysis.profile),
        ),
    ]
    if not successor:
        fixed_files.extend(
            (
                PlannedFile(
                    run_root / "contract/normalized.json",
                    run.execution_projection_bytes,
                ),
                *(PlannedFile(path, data) for path, data in reporting_files),
            )
        )
    config = {
        "run_root": str(run_root),
        "python_executable": sys.executable,
        "execution_path": str(_execution_path(run, run_root)),
        "profile_path": str(run_root / "contract/profile.json"),
        "workflow_attempt_id": attempt_id,
        "source_checkout": str(source_root),
        **reporting_config,
        "resource_policy": resource_policy_record,
        "dispatch_paths": dispatch_references,
    }
    config_data = orchestration_contracts.canonical_json_bytes(config)
    config_path = run_root / "contract" / "workflow-configs" / f"{attempt_id}.json"
    attempt_argv = lifecycle.build_snakemake_argv(
        python_executable=Path(sys.executable),
        snakefile=source_root / SNAKEFILE_RELATIVE,
        workflow_profile=source_root / WORKFLOW_PROFILE_RELATIVE,
        configfile=config_path,
        run_root=run_root,
        target=BACKEND_TARGET,
        operation=operation,
        cores=workflow_cores,
        resource_limits=resources.scheduler_limits(),
    )
    authored_paths = analysis.authored_paths
    attempt = {
        "schema_version": "emrys.workflow-attempt.v1",
        "run_id": run.run_id,
        "execution_contract_sha256": _sha256(execution_bytes),
        "profile_sha256": _sha256(
            orchestration_contracts.canonical_json_bytes(analysis.profile)
        ),
        "workflow_attempt_id": attempt_id,
        "supersedes_workflow_attempt_id": supersedes_workflow_attempt_id,
        "operation": operation,
        "created_at": created_at,
        "request": {
            "path": str(run_root / "attempts" / attempt_id / "request.yaml"),
            "size_bytes": len(analysis.source_bytes),
            "sha256": hashlib.sha256(analysis.source_bytes).hexdigest(),
        },
        "request_label": analysis.evidence_label,
        "authored_paths": {
            "request": str(analysis.source_path),
            **authored_paths,
        },
        "normalizer": normalizer_identity,
        "workspace": str(workspace_path),
        "scratch": None,
        "source_checkout": {
            "path": str(source_root),
            "commit": readiness.source_commit,
            "clean": True,
        },
        "executor": executor,
        "execution_mode": "local-science-tools",
        "snakemake_argv": list(attempt_argv),
        "workflow_config": {
            "path": config_path.relative_to(run_root).as_posix(),
            "sha256": _sha256(config_data),
        },
        "host": socket.gethostname(),
        "process_id": os.getpid(),
        "owner_token": owner_token,
        "cores": workflow_cores,
        "required_tools": list(required_tools),
    }
    if placement is not None:
        attempt["placement"] = dict(placement)
    if successor:
        selected_module_id = execution_module_id(
            run.analysis.revision, run.execution_plan
        )
        try:
            validate_successor_run(
                analysis=analysis.revision,
                plan=run.execution_plan,
                run=run.run_binding,
                profile=analysis.profile,
                attempt=attempt,
                resource_policy=resource_policy_record,
                observed_implementation_content_sha256=implementation_identity(
                    source_root,
                    selected_module_id,
                    loaded_module=(
                        analysis.module if selected_module_id is not None else None
                    ),
                ),
                observed_backend_semantics_sha256=backend_semantics_identity(
                    source_root
                ),
            )
        except (
            orchestration_contracts.ContractValidationError,
            RunImplementationError,
        ) as exc:
            raise MaterializationError(
                f"Attempt differs from immutable Run: {exc}"
            ) from exc
    orchestration_contracts.validate_record("workflow-attempt", attempt)
    runtime_profile_files = (
        ()
        if retained_runtime_profile_path is not None
        else (PlannedFile(runtime_profile_path, readiness.inspection.profile_bytes),)
    )
    attempt_files = (
        *dispatch_files,
        *(PlannedFile(path, data) for path, data in reporting_files if successor),
        *((selected_sample_file,) if selected_sample_file is not None else ()),
        PlannedFile(config_path, config_data),
        *runtime_profile_files,
    )
    directories = {
        run_root / "contract",
        run_root / "contract" / "workflow-configs",
        run_root / "contract" / "dispatch" / attempt_id,
        *reporting_directories,
        *dispatch_directories,
        *(item.path.parent for item in fixed_files),
        *(item.path.parent for item in attempt_files),
    }
    return AttemptPlan(
        run=run,
        readiness=readiness,
        resources=resources,
        operation=operation,
        workspace=workspace_path,
        run_root=run_root,
        workflow_attempt_id=attempt_id,
        attempt_record_bytes=orchestration_contracts.canonical_json_bytes(attempt),
        fixed_files=tuple(fixed_files),
        attempt_files=tuple(attempt_files),
        new_dispatch_files=tuple(dispatch_files),
        directories=tuple(sorted(directories)),
        dispatch_count=sum(len(scopes) for scopes in dispatch_references.values()),
    )


def _validate_pristine_committed_run(root: Path, candidate: RunCandidate) -> None:
    try:
        authority = inspection.admit_successor_run(root)
    except inspection.InspectionError as exc:
        raise MaterializationError(
            f"Run root contains invalid committed authority: {root}: {exc}"
        ) from exc
    if authority is None:
        raise MaterializationError(
            f"Run root has no committed successor authority: {root}"
        )
    if (
        authority.analysis_revision.canonical_bytes
        != candidate.analysis.revision.canonical_bytes
        or authority.execution_plan.canonical_bytes
        != candidate.execution_plan.canonical_bytes
        or authority.run_binding.canonical_bytes
        != candidate.run_binding.canonical_bytes
    ):
        raise MaterializationError(
            "Existing Run authority differs from the planned Run"
        )
    attempts = root / "attempts"
    if (
        attempts.exists()
        and not attempts.is_symlink()
        and attempts.is_dir()
        and any(attempts.iterdir())
    ):
        raise MaterializationError(
            "Run root already exists; inspect or resume it instead"
        )
    allowed_root = {"contract", "attempts", "locks", "state"}
    if {item.name for item in root.iterdir()} - allowed_root:
        raise MaterializationError(
            "Committed Run contains unexpected pre-Attempt state"
        )
    contract = root / "contract"
    if {item.name for item in contract.iterdir()} != {
        "analysis.json",
        "execution-plan.json",
        "run.json",
    }:
        raise MaterializationError("Committed Run already contains backend adapters")
    for name in ("attempts", "locks", "state"):
        namespace = root / name
        if not (namespace.exists() or namespace.is_symlink()):
            continue
        if namespace.is_symlink() or not namespace.is_dir() or any(namespace.iterdir()):
            raise MaterializationError(
                f"Committed Run contains non-pristine {name} state"
            )


def validate_run_destination(
    root: Path,
    *,
    candidate: RunCandidate | None = None,
) -> None:
    """Accept an absent destination or only provably evidence-free Run residue."""

    if not (root.exists() or root.is_symlink()):
        return
    if root.is_symlink() or not root.is_dir():
        raise MaterializationError(
            f"Uncommitted Run residue is not a real directory: {root}"
        )
    run_path = root / "contract" / "run.json"
    if run_path.exists() or run_path.is_symlink():
        if candidate is not None:
            _validate_pristine_committed_run(root, candidate)
            return
        raise MaterializationError(
            "Run root already exists; inspect or resume it instead"
        )
    contract = root / "contract"
    allowed_root = {"contract"}
    if {item.name for item in root.iterdir()} - allowed_root:
        raise MaterializationError(
            f"Run root contains ambiguous or evidence-bearing residue: {root}"
        )
    allowed_contract = {"analysis.json", "execution-plan.json"}
    if contract.exists() or contract.is_symlink():
        if contract.is_symlink() or not contract.is_dir():
            raise MaterializationError(
                f"Run contract residue is not a real directory: {contract}"
            )
        for item in contract.iterdir():
            if (
                item.name not in allowed_contract
                or item.is_symlink()
                or not item.is_file()
            ):
                raise MaterializationError(
                    f"Run contract contains ambiguous residue: {item}"
                )


def _quarantine_uncommitted_run(
    plan: AttemptPlan,
    ops: lifecycle.LifecycleOps,
) -> Path:
    root = plan.run_root
    validate_run_destination(root)
    quarantine = root.with_name(
        f"{root.name}.uncommitted-{plan.workflow_attempt_id.removeprefix('workflow-')}"
    )
    if quarantine.exists() or quarantine.is_symlink():
        raise MaterializationError(
            f"Run-residue quarantine already exists: {quarantine}"
        )
    try:
        root.rename(quarantine)
    except OSError as exc:
        raise MaterializationError(
            f"Could not quarantine uncommitted Run residue: {root}"
        ) from exc
    ops.sync_directory(root.parent, "workspace runs directory after quarantine")
    return quarantine


def admit_run(plan: AttemptPlan, *, ops: lifecycle.LifecycleOps) -> None:
    """Durably publish Analysis and Plan, then commit the Run binding last."""

    if plan.operation != "execute":
        raise MaterializationError("Only an initial execution may admit a Run")
    if not isinstance(plan.run, RunCandidate):
        raise MaterializationError("Historical Runs cannot be newly admitted")
    for directory in (plan.workspace, plan.workspace / "runs"):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            if directory.is_symlink() or not directory.is_dir():
                raise MaterializationError(
                    f"Run parent is not a real directory: {directory}"
                )
    run_path = plan.run_root / "contract" / "run.json"
    if plan.run_root.exists() or plan.run_root.is_symlink():
        if run_path.exists() or run_path.is_symlink():
            _validate_pristine_committed_run(plan.run_root, plan.run)
        else:
            _quarantine_uncommitted_run(plan, ops)
    if not plan.run_root.exists():
        plan.run_root.mkdir(mode=0o700)
        contract = plan.run_root / "contract"
        contract.mkdir(mode=0o700)
        ops.sync_directory(contract, "new Run contract namespace")
        ops.sync_directory(plan.run_root, "new Run root")
        ops.sync_directory(plan.run_root.parent, "workspace runs directory")
        try:
            ops.publish_bytes(
                contract / "analysis.json",
                plan.run.analysis.revision.canonical_bytes,
            )
            ops.publish_bytes(
                contract / "execution-plan.json",
                plan.run.execution_plan.canonical_bytes,
            )
            ops.publish_bytes(run_path, plan.run.run_binding.canonical_bytes)
        except BaseException:
            if not run_path.exists() and not run_path.is_symlink():
                _quarantine_uncommitted_run(plan, ops)
            raise
    for directory in (
        plan.run_root / "attempts",
        plan.run_root / "locks",
        plan.run_root / "state",
    ):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            if directory.is_symlink() or not directory.is_dir():
                raise MaterializationError(
                    f"Run namespace is not a real directory: {directory}"
                )
        else:
            ops.sync_directory(directory, "new Run namespace")
    ops.sync_directory(plan.run_root, "admitted Run root")


def _create_directory(path: Path, run_root: Path, ops: lifecycle.LifecycleOps) -> None:
    _within(path, run_root, "Materialized directory")
    missing: list[Path] = []
    cursor = path
    while cursor != run_root and not cursor.exists() and not cursor.is_symlink():
        missing.append(cursor)
        cursor = cursor.parent
    if cursor.is_symlink() or not cursor.is_dir():
        raise MaterializationError(f"Directory ancestor is not real: {cursor}")
    for directory in reversed(missing):
        directory.mkdir(mode=0o700)
        ops.sync_directory(directory, "materialized workflow directory")
        ops.sync_directory(directory.parent, "materialized workflow parent")
    if path.is_symlink() or not path.is_dir():
        raise MaterializationError(f"Materialized path is not a real directory: {path}")


def _verify_file(path: Path, expected: bytes) -> None:
    if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
        raise MaterializationError(f"Immutable run contract differs: {path}")


def publish_attempt(
    plan: AttemptPlan,
    *,
    ops: lifecycle.LifecycleOps,
) -> None:
    """Publish the plan under an already-owned lifecycle run lock."""

    for directory in plan.directories:
        _create_directory(directory, plan.run_root, ops)
    for item in plan.fixed_files:
        if item.path.exists() or item.path.is_symlink():
            _verify_file(item.path, item.data)
        else:
            ops.publish_bytes(item.path, item.data)
    for item in plan.attempt_files:
        if item.path.exists() or item.path.is_symlink():
            raise MaterializationError(
                f"Attempt-specific path already exists: {item.path}"
            )
        ops.publish_bytes(item.path, item.data)


__all__ = (
    "AttemptPlan",
    "MaterializationError",
    "HistoricalRun",
    "PlannedFile",
    "RunCandidate",
    "admit_run",
    "build_attempt_plan",
    "build_run_candidate",
    "processing_stopping_owner_keys",
    "publish_attempt",
    "validate_run_destination",
)
