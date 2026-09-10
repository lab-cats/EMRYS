"""Small deterministic B2 intake fixture used without a workflow engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from emrys.libraries.source_authority import PACKAGE_ROOT


def profile() -> dict[str, Any]:
    owners = (
        "emrys.stage.construct_STAR_index.v1",
        "emrys.stage.align_RNA_reads_with_STAR.v1",
        "emrys.stage.construct_FASTA_sidecars.v1",
        "emrys.stage.preprocess_and_annotate_cohort_candidates.v1",
    )
    return {
        "schema_version": "emrys.profile.v2",
        "profile_id": "emrys.profile.local_cmh",
        "profile_version": "v2",
        "semantic_owner_keys": list(owners),
        "owner_tasks": [
            {
                "machine_key": owners[0],
                "rule_name": "construct_STAR_index",
                "step_id": "00a",
                "scope_type": "reference",
                "scope_selector": "reference",
            },
            {
                "machine_key": owners[1],
                "rule_name": "align_RNA_reads_with_STAR",
                "step_id": "01",
                "scope_type": "sample",
                "scope_selector": "samples",
            },
            {
                "machine_key": owners[2],
                "rule_name": "construct_FASTA_sidecars",
                "step_id": "00c",
                "scope_type": "reference",
                "scope_selector": "reference",
            },
            {
                "machine_key": owners[3],
                "rule_name": "preprocess_and_annotate_cohort_candidates",
                "step_id": "08",
                "scope_type": "cohort",
                "scope_selector": "cohort",
            },
        ],
        "direct_edges": [
            {
                "producer": owners[0],
                "consumer": owners[1],
                "artifact": "STAR genome-index directory",
                "semantics": "required artifact",
            }
        ],
        "required_owner_keys": list(owners),
        "evidence_owner_keys": [],
        "artifact_templates": [
            {
                "artifact_id_template": "ref.{reference_id}.index",
                "step_id": "00a",
                "scope_type": "reference",
                "scope_selector": "reference",
                "adapter": "step00a_star_index_v1",
                "source_path_template": (
                    "results/reference/{reference_id}/star/Genome"
                ),
                "required": True,
            },
            {
                "artifact_id_template": "ref.{reference_id}.validation",
                "step_id": "00a",
                "scope_type": "reference",
                "scope_selector": "reference",
                "adapter": "step00a_validation_report_v1",
                "source_path_template": (
                    "results/validation/00a/{reference_id}.validation.tsv"
                ),
                "required": True,
            },
            {
                "artifact_id_template": "sample.{sample_id}.bam",
                "step_id": "01",
                "scope_type": "sample",
                "scope_selector": "samples",
                "adapter": "step01_star_bam_v1",
                "source_path_template": (
                    "results/samples/{sample_id}/{sample_id}.Aligned.sortedByCoord.out.bam"
                ),
                "required": True,
            },
            {
                "artifact_id_template": "sample.{sample_id}.validation",
                "step_id": "01",
                "scope_type": "sample",
                "scope_selector": "samples",
                "adapter": "step01_validation_report_v1",
                "source_path_template": (
                    "results/validation/01/{sample_id}.validation.tsv"
                ),
                "required": True,
            },
        ],
    }


def build(root: Path, *, replicate_count: int = 2) -> Path:
    reads = root / "reads"
    reference = root / "reference"
    reads.mkdir(parents=True)
    reference.mkdir()
    samples = tuple(
        f"{condition}_{replicate}"
        for replicate in range(1, replicate_count + 1)
        for condition in ("EV", "PUM1")
    )
    for sample in samples:
        (reads / f"{sample}_R1.fastq").write_text(
            f"@{sample}/1\nACGT\n+\nIIII\n", encoding="utf-8"
        )
        (reads / f"{sample}_R2.fastq").write_text(
            f"@{sample}/2\nTGCA\n+\nIIII\n", encoding="utf-8"
        )
    (reference / "genome.fa").write_text(
        ">chrSynthetic\nACGTACGTACGT\n", encoding="utf-8"
    )
    (reference / "genome.gtf").write_text(
        "chrSynthetic\tfixture\texon\t1\t12\t.\t+\t.\t"
        'gene_id "g1"; transcript_id "t1";\n',
        encoding="utf-8",
    )
    (root / "samples.tsv").write_text(
        "sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\treplicate\n"
        + "".join(
            f"{sample}\treads/{sample}_R1.fastq\treads/{sample}_R2.fastq\t"
            f"reverse\t{sample.rsplit('_', 1)[0]}\t{sample.rsplit('_', 1)[1]}\n"
            for sample in samples
        ),
        encoding="utf-8",
    )
    (root / "partitions.tsv").write_text(
        "partition_id\tselector_type\tselector_value\np1\tregion\tchrSynthetic\n",
        encoding="utf-8",
    )
    project = root / "project.yaml"
    project.write_text(
        "schema_version: emrys.project.v1\n"
        "dataset:\n"
        "  samples: samples.tsv\n"
        "reference:\n"
        "  fasta: reference/genome.fa\n"
        "  gtf: reference/genome.gtf\n"
        "  star_index:\n"
        "    sjdb_overhang: 74\n"
        "    genome_sa_index_nbases: 3\n"
        "analyses:\n"
        "  primary:\n"
        "    partitions: partitions.tsv\n"
        "    control_condition: EV\n"
        "    treatment_condition: PUM1\n"
        "    target_change: A>G\n"
        "    min_sample_dp: 1\n"
        "    mean_dp_threshold: 50\n"
        "    fdr_threshold: 0.05\n"
        "    common_or_threshold: 1.2\n"
        "    absolute_difference_threshold: 0.005\n"
        "    background_condition: null\n"
        "    background_max_fraction: 0.01\n",
        encoding="utf-8",
    )
    profile = root / "runtime/profiles/default.yaml"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "schema_version: emrys.execution-profile.v1\n"
        "resources:\n"
        "  schema_version: emrys.local-pilot-resources.v1\n"
        "  workflow_cores: 1\n"
        "  workflow_memory_mb: 1024\n"
        "  stage_concurrency:\n"
        '    "01": 1\n'
        '    "02": 1\n'
        '    "02b": 1\n'
        '    "03": 1\n'
        '    "04": 1\n'
        '    "05": 1\n'
        '    "06": 1\n'
        '    "07": 1\n'
        "  step_threads:\n"
        '    "00a": 1\n'
        '    "01": 1\n'
        '    "02": 1\n'
        '    "06": 1\n'
        '    "08": 1\n'
        "  stage_memory_mb:\n"
        '    "00a": 1024\n'
        '    "00b": 1024\n'
        '    "00c": 1024\n'
        '    "01": 1024\n'
        '    "02": 1024\n'
        '    "02b": 1024\n'
        '    "03": 1024\n'
        '    "04": 1024\n'
        '    "05": 1024\n'
        '    "06": 1024\n'
        '    "07": 1024\n'
        '    "08": 1024\n'
        '    "09": 1024\n'
        '    "10": 1024\n'
        "placement:\n"
        "  kind: direct\n",
        encoding="utf-8",
    )
    return project


def build_run(
    root: Path,
    selected_profile: dict[str, Any] | None = None,
    *,
    required_tools=None,
    computational_resources: dict[str, Any] | None = None,
):
    """Build a current immutable Run through production admission and binding."""

    from emrys.contracts.orchestration.application_model import (
        bind_run,
        build_execution_plan,
        functional_specification_from_profile,
        toolchain_from_required_tools,
        processing_compatibility_sha256,
    )
    from emrys.orchestration.run_coordinator.execution_profile import (
        load_execution_profile,
    )
    from emrys.orchestration.run_coordinator.materialization import RunCandidate
    from emrys.orchestration.run_coordinator.normalization import admit_project
    from emrys.orchestration.run_coordinator.run_implementation import (
        backend_semantics_identity,
        implementation_identity,
        processing_implementation_identity,
    )

    project = build(root)
    if required_tools is None:
        import sys
        import hashlib

        python = Path(sys.executable).resolve(strict=True)
        required_tools = (
            {
                "name": "python",
                "sha256": hashlib.sha256(python.read_bytes()).hexdigest(),
            },
        )
    analysis = admit_project(
        project, profile() if selected_profile is None else selected_profile
    ).select_analysis()
    source_root = PACKAGE_ROOT
    resources = computational_resources
    if resources is None:
        resources = load_execution_profile(
            root / "runtime" / "profiles" / "default.yaml"
        ).resource_policy.declaration.identity_document()
    processing_digest = processing_compatibility_sha256(
        functional_specification=functional_specification_from_profile(
            analysis.profile
        ),
        processing_implementation_sha256=processing_implementation_identity(
            source_root
        ),
        toolchain=toolchain_from_required_tools(required_tools),
        backend="local",
        engine="snakemake",
        backend_semantics_sha256=backend_semantics_identity(source_root),
        star_index=analysis.workflow_inputs["reference"]["star_index"],
        computational_resources=resources,
    )
    plan = build_execution_plan(
        processing_compatibility_sha256=processing_digest,
        functional_specification=functional_specification_from_profile(
            analysis.profile
        ),
        scientific_stopping_owner_keys=analysis.profile["required_owner_keys"],
        implementation_content_sha256=implementation_identity(
            source_root,
            analysis.module.descriptor.module_id,
            loaded_module=analysis.module,
        ),
        toolchain=toolchain_from_required_tools(required_tools),
        backend="local",
        engine="snakemake",
        backend_semantics_sha256=backend_semantics_identity(source_root),
        star_index=analysis.workflow_inputs["reference"]["star_index"],
        computational_resources=resources,
    )
    return project, RunCandidate(analysis, plan, bind_run(analysis.revision, plan))


def publish_run(run, root: Path) -> Path:
    """Write the current Run authority and profile into one fixture namespace."""

    from emrys.contracts.orchestration.api import canonical_json_bytes

    contract = root / "contract"
    contract.mkdir(parents=True)
    for name, data in (
        ("analysis.json", run.analysis.revision.canonical_bytes),
        ("execution-plan.json", run.execution_plan.canonical_bytes),
        ("run.json", run.run_binding.canonical_bytes),
        ("profile.json", canonical_json_bytes(run.analysis.profile)),
    ):
        (contract / name).write_bytes(data)
    return contract / "run.json"
