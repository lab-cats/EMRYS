"""Processing adapters plus the one analysis module selected by a Run."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from emrys import analyses
from emrys.contracts.orchestration.artifact_inventory import (
    processing_artifact_templates,
)
from emrys.contracts.scientific_evidence import step08
from emrys.libraries.alignments import orientation as alignment_orientation

from .models import (
    STEP00A_BASENAMES,
    STEP06_COUNTS_HEADER,
    STEP07_RECEIPT_HEADER,
    VALIDATION_REPORT_HEADER,
    AdapterSpec,
    ArtifactIndexError,
)

MEDIA_TYPE_BY_KIND = {
    **analyses.ANALYSIS_ARTIFACT_MEDIA_TYPES,
    "bai": "application/octet-stream",
    "bam": "application/x-bam",
    "bed12": "text/bed",
    "dict": "text/vnd.sam",
    "fai": "text/tab-separated-values",
    "fasta": "text/x-fasta",
    "flagstat": "text/plain",
    "picard_metrics": "text/plain",
    "quickcheck": "text/plain",
    "rseqc": "text/plain",
    "star_index": "application/octet-stream",
    "star_log_final": "text/plain",
    "star_sj": "text/plain",
    "text": "text/plain",
    "vcf": "text/vcf",
}


def _add_analysis_adapters(
    registry: dict[str, AdapterSpec],
    descriptor: analyses.AnalysisModuleDescriptorV1,
) -> None:
    for task in descriptor.tasks:
        for item in task.outputs:
            if item.adapter in registry:
                raise ArtifactIndexError(
                    f"Analysis module adapter collides: {item.adapter!r}"
                )
            registry[item.adapter] = AdapterSpec(
                adapter_id=item.adapter,
                step_id=task.step_id,
                scope_type="analysis",
                kind=item.kind,
                media_type=analyses.ANALYSIS_ARTIFACT_MEDIA_TYPES[item.kind],
                suffixes=(item.source_path_template.rsplit("}", 1)[-1],),
                expected_header=item.expected_header,
                exact_data_rows=item.exact_data_rows,
                allow_header_only=item.allow_header_only,
            )


def build_adapter_registry(
    descriptor: analyses.AnalysisModuleDescriptorV1,
    *,
    source_root: Path,
) -> dict[str, AdapterSpec]:
    """Combine canonical processing ownership with native reader contracts."""
    templates = {
        str(item["adapter"]): item
        for item in processing_artifact_templates(source_root)
    }
    registry: dict[str, AdapterSpec] = {}

    def add(
        adapter_id: str,
        kind: str,
        suffixes: Sequence[str] = (),
        *,
        basenames: Sequence[str] = (),
        expected_header: Sequence[str] | None = None,
        exact_data_rows: int | None = None,
        allow_header_only: bool = True,
    ) -> None:
        owner = templates[adapter_id]
        registry[adapter_id] = AdapterSpec(
            adapter_id=adapter_id,
            step_id=str(owner["step_id"]),
            scope_type=str(owner["scope_type"]),
            kind=kind,
            media_type=MEDIA_TYPE_BY_KIND[kind],
            suffixes=tuple(suffixes),
            basenames=tuple(basenames),
            expected_header=(
                tuple(expected_header) if expected_header is not None else None
            ),
            exact_data_rows=exact_data_rows,
            allow_header_only=allow_header_only,
        )

    add("step00a_star_index_v1", "star_index", basenames=STEP00A_BASENAMES)
    for adapter, kind, suffixes in (
        ("step00b_bed12_v1", "bed12", (".bed",)),
        ("step00c_reference_fasta_v1", "fasta", (".fa", ".fasta")),
        ("step00c_reference_fai_v1", "fai", (".fai",)),
        ("step00c_reference_dict_v1", "dict", (".dict",)),
        ("step01_star_bam_v1", "bam", (".bam",)),
        ("step01_star_log_final_v1", "star_log_final", (".Log.final.out",)),
        ("step01_star_log_v1", "text", (".Log.out",)),
        ("step01_star_log_progress_v1", "text", (".Log.progress.out",)),
        ("step01_star_sj_v1", "star_sj", (".SJ.out.tab",)),
        ("step02b_quickcheck_v1", "quickcheck", (".quickcheck.txt",)),
        ("step02b_flagstat_v1", "flagstat", (".flagstat.txt",)),
        ("step03_rseqc_infer_v1", "rseqc", (".infer_experiment.txt",)),
        ("step04_markdup_metrics_v1", "picard_metrics", (".markdup.metrics.txt",)),
        ("step07_mpileup_vcf_v1", "vcf", (".mpileup.vcf",)),
    ):
        add(adapter, kind, suffixes)
    for bam_adapter, bai_adapter, bam_suffix in (
        ("step02_canonical_bam_v1", "step02_canonical_bai_v1", ".sorted.bam"),
        ("step04_markdup_bam_v1", "step04_markdup_bai_v1", ".markdup.bam"),
        ("step05_split_bam_v1", "step05_split_bai_v1", ".split_ncigar.bam"),
    ):
        add(bam_adapter, "bam", (bam_suffix,))
        add(bai_adapter, "bai", (f"{bam_suffix}.bai",))
    for orientation, prefix in zip(
        alignment_orientation.ORIENTATIONS,
        alignment_orientation.ORIENTATION_PREFIXES,
    ):
        add(f"step06_{prefix}_bam_v1", "bam", (f".{orientation}.bam",))
        add(f"step06_{prefix}_bai_v1", "bai", (f".{orientation}.bam.bai",))
    for adapter, suffix, header, count in (
        (
            "step06_orientation_counts_v1",
            ".orientation_counts.tsv",
            STEP06_COUNTS_HEADER,
            1,
        ),
        (
            "step07_mpileup_receipt_v1",
            ".step07_outputs.tsv",
            STEP07_RECEIPT_HEADER,
            2,
        ),
        (
            "step08_inputs_v1",
            ".step08_inputs.tsv",
            step08.STEP08_INPUTS_HEADER,
            None,
        ),
        (
            "step08_summary_v1",
            ".step08_summary.tsv",
            step08.STEP08_SUMMARY_HEADER,
            1,
        ),
    ):
        add(
            adapter,
            "tsv",
            (suffix,),
            expected_header=header,
            exact_data_rows=count,
            allow_header_only=False,
        )
    add(
        "step08_sites_v1",
        "sample_blocks_tsv",
        (".step08_sites.tsv",),
        expected_header=step08.STEP08_METADATA_HEADER,
    )
    for adapter in templates:
        if adapter.endswith("_validation_report_v1"):
            add(
                adapter,
                "validation_report",
                (".validation.tsv",),
                expected_header=VALIDATION_REPORT_HEADER,
                exact_data_rows=6 if templates[adapter]["step_id"] == "00a" else 5,
                allow_header_only=False,
            )
    _add_analysis_adapters(registry, descriptor)
    return registry
