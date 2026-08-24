"""Exact contract tests for the fixed local paired-CMH profile."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import pytest

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.projection import build_reporting_bundle
from emrys.orchestration.local_pilot.normalization import normalize_request
from tests.orchestration.local_pilot.fixture import build

REPO_ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = REPO_ROOT / "workflow" / "contracts" / "local_cmh_v2.json"
STAGE_MAP_PATH = REPO_ROOT / "src" / "emrys" / "contracts" / "STAGE_MAP.md"
PUBLIC_INVENTORY_PATH = REPO_ROOT / "configs" / "artifact_inventory.example.tsv"

EXPECTED_TASKS = (
    (
        "emrys.stage.construct_STAR_index.v1",
        "construct_STAR_index",
        "00a",
        "reference",
        "reference",
    ),
    (
        "emrys.stage.convert_GTF_to_BED12.v1",
        "convert_GTF_to_BED12",
        "00b",
        "reference",
        "reference",
    ),
    (
        "emrys.stage.construct_FASTA_sidecars.v1",
        "construct_FASTA_sidecars",
        "00c",
        "reference",
        "reference",
    ),
    (
        "emrys.stage.align_RNA_reads_with_STAR.v1",
        "align_RNA_reads_with_STAR",
        "01",
        "sample",
        "samples",
    ),
    (
        "emrys.stage.construct_canonical_BAM.v1",
        "construct_canonical_BAM",
        "02",
        "sample",
        "samples",
    ),
    (
        "emrys.evidence.collect_canonical_BAM_QC_evidence.v1",
        "collect_canonical_BAM_QC_evidence",
        "02b",
        "sample",
        "samples",
    ),
    (
        "emrys.evidence.collect_RSeQC_paired_orientation_evidence.v1",
        "collect_RSeQC_paired_orientation_evidence",
        "03",
        "sample",
        "samples",
    ),
    (
        "emrys.stage.mark_BAM_duplicates_with_Picard.v1",
        "mark_BAM_duplicates_with_Picard",
        "04",
        "sample",
        "samples",
    ),
    (
        "emrys.stage.split_N_cigar_reads_with_GATK.v1",
        "split_N_cigar_reads_with_GATK",
        "05",
        "sample",
        "samples",
    ),
    (
        "emrys.stage.partition_BAM_by_mechanical_read_orientation.v1",
        "partition_BAM_by_mechanical_read_orientation",
        "06",
        "sample",
        "samples",
    ),
    (
        "emrys.stage.generate_partitioned_cohort_mpileup_VCFs.v1",
        "generate_partitioned_cohort_mpileup_VCFs",
        "07",
        "cohort_partition",
        "partitions",
    ),
    (
        "emrys.stage.preprocess_and_annotate_cohort_candidates.v1",
        "preprocess_and_annotate_cohort_candidates",
        "08",
        "cohort",
        "cohort",
    ),
    (
        "emrys.analysis.rank_cohort_candidates_with_paired_CMH.v1",
        "rank_cohort_candidates_with_paired_CMH",
        "09",
        "analysis",
        "analysis",
    ),
    (
        "emrys.analysis.project_candidate_scientific_context.v1",
        "project_candidate_scientific_context",
        "10",
        "analysis",
        "analysis",
    ),
)

# Independent compact representation of every exact public artifact template.
# Fields are artifact ID, step, scope type, selector, adapter, path, required.
EXPECTED_ARTIFACT_ROWS = """
ref.star_index.genome_parameters|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/genomeParameters.txt|true
ref.star_index.genome|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/Genome|true
ref.star_index.sa|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/SA|true
ref.star_index.saindex|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/SAindex|true
ref.star_index.chr_length|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/chrLength.txt|true
ref.star_index.chr_name|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/chrName.txt|true
ref.star_index.chr_name_length|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/chrNameLength.txt|true
ref.star_index.chr_start|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/chrStart.txt|true
ref.star_index.exon_getr_info|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/exonGeTrInfo.tab|true
ref.star_index.exon_info|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/exonInfo.tab|true
ref.star_index.gene_info|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/geneInfo.tab|true
ref.star_index.sjdb_info|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/sjdbInfo.txt|true
ref.star_index.sjdb_from_gtf|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/sjdbList.fromGTF.out.tab|true
ref.star_index.sjdb_list|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/sjdbList.out.tab|true
ref.star_index.transcript_info|00a|reference|reference|step00a_star_index_v1|results/star/{reference_id}/index/transcriptInfo.tab|true
ref.star_index.validation|00a|reference|reference|step00a_validation_report_v1|results/qc/validation/00a/{reference_id}.validation.tsv|true
ref.bed12|00b|reference|reference|step00b_bed12_v1|results/qc/reference/{reference_id}.bed|true
ref.bed12.validation|00b|reference|reference|step00b_validation_report_v1|results/qc/validation/00b/{reference_id}.validation.tsv|true
ref.fasta|00c|reference|reference|step00c_reference_fasta_v1|{reference_fasta_path}|true
ref.fai|00c|reference|reference|step00c_reference_fai_v1|{reference_fasta_path}.fai|true
ref.dict|00c|reference|reference|step00c_reference_dict_v1|{reference_dict_path}|true
ref.sidecars.validation|00c|reference|reference|step00c_validation_report_v1|results/qc/validation/00c/{reference_id}.validation.tsv|true
sample.{sample_id}.star_bam|01|sample|samples|step01_star_bam_v1|results/star/{sample_id}/{sample_id}.Aligned.sortedByCoord.out.bam|true
sample.{sample_id}.star_log_final|01|sample|samples|step01_star_log_final_v1|results/star/{sample_id}/{sample_id}.Log.final.out|true
sample.{sample_id}.star_log|01|sample|samples|step01_star_log_v1|results/star/{sample_id}/{sample_id}.Log.out|true
sample.{sample_id}.star_log_progress|01|sample|samples|step01_star_log_progress_v1|results/star/{sample_id}/{sample_id}.Log.progress.out|true
sample.{sample_id}.star_sj|01|sample|samples|step01_star_sj_v1|results/star/{sample_id}/{sample_id}.SJ.out.tab|true
sample.{sample_id}.star_validation|01|sample|samples|step01_validation_report_v1|results/qc/validation/01/{sample_id}.validation.tsv|true
sample.{sample_id}.canonical_bam|02|sample|samples|step02_canonical_bam_v1|results/bam/{sample_id}/{sample_id}.sorted.bam|true
sample.{sample_id}.canonical_bai|02|sample|samples|step02_canonical_bai_v1|results/bam/{sample_id}/{sample_id}.sorted.bam.bai|true
sample.{sample_id}.canonical_validation|02|sample|samples|step02_validation_report_v1|results/qc/validation/02/{sample_id}.validation.tsv|true
sample.{sample_id}.quickcheck|02b|sample|samples|step02b_quickcheck_v1|results/qc/bam/{sample_id}.quickcheck.txt|true
sample.{sample_id}.flagstat|02b|sample|samples|step02b_flagstat_v1|results/qc/bam/{sample_id}.flagstat.txt|true
sample.{sample_id}.bam_qc_validation|02b|sample|samples|step02b_validation_report_v1|results/qc/validation/02b/{sample_id}.validation.tsv|true
sample.{sample_id}.strand|03|sample|samples|step03_rseqc_infer_v1|results/qc/strandedness/{sample_id}.infer_experiment.txt|true
sample.{sample_id}.strand_validation|03|sample|samples|step03_validation_report_v1|results/qc/validation/03/{sample_id}.validation.tsv|true
sample.{sample_id}.markdup_bam|04|sample|samples|step04_markdup_bam_v1|results/markdup/{sample_id}/{sample_id}.markdup.bam|true
sample.{sample_id}.markdup_bai|04|sample|samples|step04_markdup_bai_v1|results/markdup/{sample_id}/{sample_id}.markdup.bam.bai|true
sample.{sample_id}.markdup_metrics|04|sample|samples|step04_markdup_metrics_v1|results/qc/markdup/{sample_id}.markdup.metrics.txt|true
sample.{sample_id}.markdup_validation|04|sample|samples|step04_validation_report_v1|results/qc/validation/04/{sample_id}.validation.tsv|true
sample.{sample_id}.split_bam|05|sample|samples|step05_split_bam_v1|results/split_ncigar/{sample_id}/{sample_id}.split_ncigar.bam|true
sample.{sample_id}.split_bai|05|sample|samples|step05_split_bai_v1|results/split_ncigar/{sample_id}/{sample_id}.split_ncigar.bam.bai|true
sample.{sample_id}.split_validation|05|sample|samples|step05_validation_report_v1|results/qc/validation/05/{sample_id}.validation.tsv|true
sample.{sample_id}.fwd_bam|06|sample|samples|step06_fwd_bam_v1|results/orientation/{sample_id}/{sample_id}.FWD_like.bam|true
sample.{sample_id}.fwd_bai|06|sample|samples|step06_fwd_bai_v1|results/orientation/{sample_id}/{sample_id}.FWD_like.bam.bai|true
sample.{sample_id}.rev_bam|06|sample|samples|step06_rev_bam_v1|results/orientation/{sample_id}/{sample_id}.REV_like.bam|true
sample.{sample_id}.rev_bai|06|sample|samples|step06_rev_bai_v1|results/orientation/{sample_id}/{sample_id}.REV_like.bam.bai|true
sample.{sample_id}.orientation_counts|06|sample|samples|step06_orientation_counts_v1|results/qc/orientation/{sample_id}.orientation_counts.tsv|true
sample.{sample_id}.orientation_validation|06|sample|samples|step06_validation_report_v1|results/qc/validation/06/{sample_id}.validation.tsv|true
cohort.{cohort_id}.{partition_id}.fwd_vcf|07|cohort_partition|partitions|step07_mpileup_vcf_v1|results/mpileup/{cohort_id}/{partition_id}/{cohort_id}.{partition_id}.FWD_like.mpileup.vcf|true
cohort.{cohort_id}.{partition_id}.rev_vcf|07|cohort_partition|partitions|step07_mpileup_vcf_v1|results/mpileup/{cohort_id}/{partition_id}/{cohort_id}.{partition_id}.REV_like.mpileup.vcf|true
cohort.{cohort_id}.{partition_id}.receipt|07|cohort_partition|partitions|step07_mpileup_receipt_v1|results/mpileup/{cohort_id}/{partition_id}/{cohort_id}.{partition_id}.step07_outputs.tsv|true
cohort.{cohort_id}.{partition_id}.validation|07|cohort_partition|partitions|step07_validation_report_v1|results/qc/validation/07/{cohort_id}__{partition_id}.validation.tsv|true
cohort.{cohort_id}.step08_sites|08|cohort|cohort|step08_sites_v1|results/vcf_preprocessed/{cohort_id}/{cohort_id}.step08_sites.tsv|true
cohort.{cohort_id}.step08_inputs|08|cohort|cohort|step08_inputs_v1|results/vcf_preprocessed/{cohort_id}/{cohort_id}.step08_inputs.tsv|true
cohort.{cohort_id}.step08_summary|08|cohort|cohort|step08_summary_v1|results/qc/vcf_preprocessing/{cohort_id}.step08_summary.tsv|true
cohort.{cohort_id}.step08_validation|08|cohort|cohort|step08_validation_report_v1|results/qc/validation/08/{cohort_id}.validation.tsv|true
analysis.{analysis_id}.cmh_all_sites|09|analysis|analysis|step09_cmh_all_sites_v1|results/editing/{analysis_id}/{analysis_id}.cmh_all_sites.tsv|true
analysis.{analysis_id}.cmh_significant_sites|09|analysis|analysis|step09_cmh_significant_sites_v1|results/editing/{analysis_id}/{analysis_id}.cmh_significant_sites.tsv|true
analysis.{analysis_id}.cmh_summary|09|analysis|analysis|step09_cmh_summary_v1|results/editing/{analysis_id}/{analysis_id}.cmh_summary.tsv|true
analysis.{analysis_id}.mutation_spectrum_tsv|09|analysis|analysis|step09_mutation_spectrum_tsv_v1|results/editing/{analysis_id}/{analysis_id}.mutation_spectrum.tsv|true
analysis.{analysis_id}.mutation_spectrum_pdf|09|analysis|analysis|step09_mutation_spectrum_pdf_v1|results/editing/{analysis_id}/{analysis_id}.mutation_spectrum.pdf|true
analysis.{analysis_id}.depth_delta_pdf|09|analysis|analysis|step09_depth_delta_pdf_v1|results/editing/{analysis_id}/{analysis_id}.depth_delta.pdf|true
analysis.{analysis_id}.cmh_validation|09|analysis|analysis|step09_validation_report_v1|results/qc/validation/09/{analysis_id}.validation.tsv|true
analysis.{analysis_id}.candidate_context|10|analysis|analysis|step10_candidate_context_v1|results/scientific_context/{analysis_id}/{analysis_id}.candidate_context.tsv|true
analysis.{analysis_id}.motif_hits|10|analysis|analysis|step10_motif_hits_v1|results/scientific_context/{analysis_id}/{analysis_id}.motif_hits.tsv|true
analysis.{analysis_id}.sequence_logo|10|analysis|analysis|step10_sequence_logo_v1|results/scientific_context/{analysis_id}/{analysis_id}.sequence_logo.tsv|true
analysis.{analysis_id}.motif_statistics|10|analysis|analysis|step10_motif_statistics_v1|results/scientific_context/{analysis_id}/{analysis_id}.motif_statistics.tsv|true
analysis.{analysis_id}.context_receipt|10|analysis|analysis|step10_context_receipt_v1|results/scientific_context/{analysis_id}/{analysis_id}.context_receipt.tsv|true
analysis.{analysis_id}.context_validation|10|analysis|analysis|step10_validation_report_v1|results/qc/validation/10/{analysis_id}.validation.tsv|true
""".strip().splitlines()


@pytest.fixture(scope="module")
def profile() -> dict[str, object]:
    return orchestration_contracts.load_json_object(PROFILE_PATH)


def _expected_templates() -> list[dict[str, object]]:
    rows = []
    for raw in EXPECTED_ARTIFACT_ROWS:
        artifact_id, step, scope, selector, adapter, path, required = raw.split("|")
        rows.append(
            {
                "artifact_id_template": artifact_id,
                "step_id": step,
                "scope_type": scope,
                "scope_selector": selector,
                "adapter": adapter,
                "source_path_template": path,
                "required": required == "true",
            }
        )
    return rows


def _stage_map_tables() -> tuple[list[tuple[str, str, str]], list[dict[str, str]]]:
    text = STAGE_MAP_PATH.read_text(encoding="utf-8")
    identity_text = text.split("## Identity map\n", 1)[1].split("## Edge semantics", 1)[
        0
    ]
    identities = []
    slug_to_key = {}
    for line in identity_text.splitlines():
        fields = [
            field.strip().strip("`") for field in line.strip().strip("|").split("|")
        ]
        if len(fields) != 5 or fields[0] not in {"stage", "analysis", "evidence"}:
            continue
        _, _, slug, key, alias = fields
        identities.append((key, slug, alias))
        slug_to_key[slug] = key

    edge_text = text.split("## Direct DAG edges\n", 1)[1].split(
        "## Current operational coupling", 1
    )[0]
    edges = []
    for line in edge_text.splitlines():
        fields = [
            field.strip().strip("`") for field in line.strip().strip("|").split("|")
        ]
        if len(fields) != 4 or fields[0] not in slug_to_key:
            continue
        producer, consumer, artifact, semantics = fields
        edges.append(
            {
                "producer": slug_to_key[producer],
                "consumer": slug_to_key[consumer],
                "artifact": artifact,
                "semantics": semantics,
            }
        )
    return identities, edges


def test_profile_is_schema_valid_and_exactly_matches_stage_map(
    profile: dict[str, object],
) -> None:
    orchestration_contracts.validate_record("profile", profile)
    identities, edges = _stage_map_tables()
    tasks = profile["owner_tasks"]
    observed_tasks = [
        (
            task["machine_key"],
            task["rule_name"],
            task["step_id"],
            task["scope_type"],
            task["scope_selector"],
        )
        for task in tasks
    ]
    assert observed_tasks == list(EXPECTED_TASKS)
    assert [(key, slug, alias) for key, slug, alias in identities] == [
        (key, rule, step) for key, rule, step, _, _ in EXPECTED_TASKS
    ]
    assert profile["semantic_owner_keys"] == [key for key, _, _ in identities]
    assert profile["direct_edges"] == edges


def test_profile_has_exact_70_artifact_templates(profile: dict[str, object]) -> None:
    expected = _expected_templates()
    assert len(expected) == 70
    assert profile["artifact_templates"] == expected


def test_profile_covers_exact_public_adapter_roster_with_only_declared_reuse(
    profile: dict[str, object],
) -> None:
    templates = profile["artifact_templates"]
    counts = Counter(template["adapter"] for template in templates)
    with PUBLIC_INVENTORY_PATH.open(encoding="utf-8", newline="") as stream:
        public_rows = list(csv.DictReader(stream, delimiter="\t"))
    public_adapters = {row["adapter"] for row in public_rows}
    assert len(counts) == 55
    assert set(counts) == public_adapters
    assert {adapter: count for adapter, count in counts.items() if count > 1} == {
        "step00a_star_index_v1": 15,
        "step07_mpileup_vcf_v1": 2,
    }


def test_profile_expands_to_exact_formula_and_contiguous_scopes(
    tmp_path: Path,
    profile: dict[str, object],
) -> None:
    request = build(tmp_path)
    execution = normalize_request(request, profile).execution_contract
    bundle = build_reporting_bundle(execution, profile)
    rows = bundle.artifact_inventory_rows
    sample_count = len(execution["samples"]["rows"])
    partition_count = len(execution["partitions"]["rows"])
    assert len(rows) == 39 + (27 * sample_count) + (4 * partition_count)

    inventory_path = tmp_path / "artifact_inventory.tsv"
    inventory_path.write_bytes(bundle.artifact_inventory_bytes)
    assert artifact_contracts.validate_inventory(
        inventory_path, source_root=tmp_path
    ) == list(rows)

    closed = set()
    active = None
    for row in rows:
        scope = (row["step_id"], row["scope_type"], row["scope_id"])
        if scope != active:
            assert scope not in closed
            if active is not None:
                closed.add(active)
            active = scope


def test_every_profile_owner_is_required_without_an_exclusion_surface(
    profile: dict[str, object],
) -> None:
    assert "excluded_owner_keys" not in profile
    assert profile["required_owner_keys"] == profile["semantic_owner_keys"]
    assert all(
        template["step_id"] != "09c" for template in profile["artifact_templates"]
    )


def test_only_stationary_step00c_native_artifacts_are_absolute_templates(
    profile: dict[str, object],
) -> None:
    absolute_templates = [
        template
        for template in profile["artifact_templates"]
        if template["source_path_template"].startswith("{")
    ]
    assert [template["artifact_id_template"] for template in absolute_templates] == [
        "ref.fasta",
        "ref.fai",
        "ref.dict",
    ]
    assert [template["source_path_template"] for template in absolute_templates] == [
        "{reference_fasta_path}",
        "{reference_fasta_path}.fai",
        "{reference_dict_path}",
    ]
    assert all(
        template["source_path_template"].startswith("results/")
        for template in profile["artifact_templates"]
        if template not in absolute_templates
    )


def test_step09_keeps_native_diagnostic_pdfs(profile: dict[str, object]) -> None:
    step09_paths = {
        template["source_path_template"]
        for template in profile["artifact_templates"]
        if template["step_id"] == "09"
    }
    assert {
        "results/editing/{analysis_id}/{analysis_id}.mutation_spectrum.pdf",
        "results/editing/{analysis_id}/{analysis_id}.depth_delta.pdf",
    } <= step09_paths
