"""Small deterministic B2 intake fixture used without a workflow engine."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from emrys import analyses
from emrys.analyses.paired_cmh_candidate_ranking import analysis_module_v1


REPO_ROOT = Path(__file__).resolve().parents[3]


def core_profile() -> dict[str, Any]:
    return json.loads(
        (REPO_ROOT / "workflow/contracts/local_cmh_v2.json").read_text(encoding="utf-8")
    )


def profile(core: dict[str, Any] | None = None) -> dict[str, Any]:
    return analyses.compose_profile(
        core_profile() if core is None else core, analysis_module_v1()
    )


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
    admission_profile: dict[str, Any] | None = None,
    *,
    execution_profile: dict[str, Any] | None = None,
) -> tuple[Path, dict[str, Any], bytes]:
    """Build and admit the one exact historical execution fixture."""

    from emrys.orchestration.local_pilot.normalization import (
        _historical_execution_v1,
        admit_project,
    )
    from emrys.contracts.orchestration import api as contracts

    request = build_legacy(root)
    admitted = admit_project(
        request,
        core_profile() if admission_profile is None else admission_profile,
        allow_legacy=True,
    ).select_analysis()
    if execution_profile is not None:
        workflow_inputs = admitted.workflow_inputs
        workflow_inputs["profile"] = {
            "profile_id": execution_profile["profile_id"],
            "profile_version": execution_profile["profile_version"],
            "profile_sha256": contracts.canonical_sha256(execution_profile),
        }
        admitted = replace(
            admitted,
            _profile_bytes=contracts.canonical_json_bytes(execution_profile),
            _workflow_input_bytes=contracts.canonical_json_bytes(workflow_inputs),
        )
    execution, execution_bytes = _historical_execution_v1(admitted)
    return request, execution, execution_bytes
