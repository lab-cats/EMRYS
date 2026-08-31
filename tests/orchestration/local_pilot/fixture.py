"""Small deterministic B2 intake fixture used without a workflow engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def profile() -> dict[str, Any]:
    owners = (
        "emrys.stage.construct_STAR_index.v1",
        "emrys.stage.align_RNA_reads_with_STAR.v1",
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


def build(root: Path) -> Path:
    reads = root / "reads"
    reference = root / "reference"
    reads.mkdir(parents=True)
    reference.mkdir()
    for sample in ("EV_1", "PUM1_1", "EV_2", "PUM1_2"):
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
        'chrSynthetic\tfixture\texon\t1\t12\t.\t+\t.\t'
        'gene_id "g1"; transcript_id "t1";\n',
        encoding="utf-8",
    )
    (root / "samples.tsv").write_text(
        "sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\treplicate\n"
        "EV_1\treads/EV_1_R1.fastq\treads/EV_1_R2.fastq\treverse\tEV\t1\n"
        "PUM1_1\treads/PUM1_1_R1.fastq\treads/PUM1_1_R2.fastq\treverse\tPUM1\t1\n"
        "EV_2\treads/EV_2_R1.fastq\treads/EV_2_R2.fastq\treverse\tEV\t2\n"
        "PUM1_2\treads/PUM1_2_R1.fastq\treads/PUM1_2_R2.fastq\treverse\tPUM1\t2\n",
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
    (root / "emrys.execution.yaml").write_text(
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
        "  reporting_memory_mb:\n"
        "    artifact_index: 1024\n"
        "    run_summary: 1024\n"
        "    html_report: 1024\n"
        "placement:\n"
        "  kind: direct\n",
        encoding="utf-8",
    )
    return project


def build_legacy(root: Path) -> Path:
    """Build the exact request-v3 shape retained only by historical tests."""

    project = build(root)
    project.unlink()
    request = root / "request.yaml"
    request.write_text(
        "schema_version: emrys.request.v3\n"
        "label: first label\n"
        "profile: emrys.profile.local_cmh.v2\n"
        "sample_manifest: samples.tsv\n"
        "partition_manifest: partitions.tsv\n"
        "reference:\n"
        "  id: synthetic_ref\n"
        "  fasta: reference/genome.fa\n"
        "  gtf: reference/genome.gtf\n"
        "  star_index:\n"
        "    sjdb_overhang: 74\n"
        "    genome_sa_index_nbases: 3\n"
        "cohort_id: synthetic_cohort\n"
        "analysis:\n"
        "  id: synthetic_analysis\n"
        "  control_condition: EV\n"
        "  treatment_condition: PUM1\n"
        "  rna_ref: A\n"
        "  rna_alt: G\n"
        "  min_sample_dp: 1\n"
        "  mean_dp_threshold: 50\n"
        "  fdr_threshold: 0.05\n"
        "  common_or_threshold: 1.2\n"
        "  absolute_difference_threshold: 0.005\n"
        "  background_condition: null\n"
        "  background_max_fraction: 0.01\n",
        encoding="utf-8",
    )
    return request


def build_legacy_execution(
    root: Path,
    selected_profile: dict[str, Any] | None = None,
) -> tuple[Path, dict[str, Any], bytes]:
    """Build and admit the one exact historical execution fixture."""

    from emrys.orchestration.local_pilot.normalization import (
        _historical_execution_v1,
        admit_project,
    )

    request = build_legacy(root)
    admitted = admit_project(
        request,
        profile() if selected_profile is None else selected_profile,
        allow_legacy=True,
    ).select_analysis()
    execution, execution_bytes = _historical_execution_v1(admitted)
    return request, execution, execution_bytes
