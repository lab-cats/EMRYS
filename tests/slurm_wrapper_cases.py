"""Declarative SLURM wrapper contracts and delegated fixture cases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WrapperContract:
    default: str = "dry_run"
    execute: str = "explicit"
    invalid_mode: str = "reject"
    module_policy: str = "tolerated"
    module_calls: tuple[str, ...] = ("list",)
    submit_cwd: str = "fallback"
    delegation: str = ""
    output_validation: str = "wrapper_files"
    exit_propagation: str = "strict"


def contract(delegation: str, **overrides: Any) -> WrapperContract:
    return WrapperContract(delegation=delegation, **overrides)


CONTRACTS = {
    "step_00a_build_novogene_star_index.slurm": contract(
        "embedded_star",
        default="legacy_implicit_execute",
        execute="implicit_only",
        invalid_mode="not_applicable",
        module_policy="strict",
        module_calls=("load star/2.7.11b", "list"),
        submit_cwd="caller",
        output_validation="none_after_child_success",
    ),
    "step_00b_gtf_to_bed12.slurm": contract(
        "embedded_python_and_bedtools",
        default="legacy_implicit_execute",
        execute="implicit_only",
        invalid_mode="not_applicable",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("list", "load bedtools/2.31.1", "list"),
        submit_cwd="required",
        output_validation="bed12_field_count",
    ),
    "step_00c_prepare_gatk_reference.slurm": contract(
        "src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh",
        default="dry_run_with_bash32_empty_array_defect",
        module_calls=("list", "load samtools/1.19.2", "list"),
    ),
    "step_01_star_align.slurm": contract(
        "src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh",
        default="dry_run_with_fixture_side_effects",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("list", "load star/2.7.11b", "list"),
        submit_cwd="caller",
        output_validation="delegate_only",
    ),
    "step_02_sort_index_bam.slurm": contract(
        "src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh",
        default="dry_run_creates_output_directory_with_bash32_empty_array_defect",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("list", "load samtools/1.19.2", "list"),
        submit_cwd="caller",
    ),
    "step_02b_bam_qc.slurm": contract(
        "src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh",
        default="dry_run_creates_output_directory_with_bash32_empty_array_defect",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("load samtools/1.19.2", "list"),
        submit_cwd="required",
    ),
    "step_03_infer_strandedness_and_orientation.slurm": contract(
        "src/norad/evidence/collect_RSeQC_paired_orientation_evidence/"
        "step_03_infer_strandedness_and_orientation.sh",
        default="dry_run_with_bash32_empty_array_defect",
    ),
    "step_04_mark_duplicates.slurm": contract(
        "src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh",
        default="dry_run_with_bash32_empty_array_defect",
        module_policy="strict_loads_tolerated_lists",
        module_calls=(
            "list",
            "load picard/3.1.1",
            "load samtools/1.19.2",
            "list",
        ),
    ),
    "step_05_split_n_cigar_reads.slurm": contract(
        "src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh",
        default="dry_run_with_bash32_empty_array_defect",
        module_calls=("list", "load samtools/1.19.2", "list"),
    ),
    "step_06_split_bam_by_read_orientation.slurm": contract(
        "src/norad/stages/partition_BAM_by_mechanical_read_orientation/"
        "step_06_split_bam_by_read_orientation.sh",
        default="dry_run_with_bash32_empty_array_defect",
        module_calls=("list", "load samtools/1.19.2", "list"),
    ),
    "step_07_bcftools_mpileup_by_chrom_and_strand.slurm": contract(
        "src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/"
        "step_07_bcftools_mpileup_by_chrom_and_strand.sh",
        module_calls=("list", "load CBI bcftools/1.21", "list"),
    ),
    "step_08_vcf_preprocessing.slurm": contract(
        "src/norad/stages/preprocess_and_annotate_cohort_candidates/"
        "step_08_vcf_preprocessing.sh"
    ),
    "step_09_cmh_editing_site_calling.slurm": contract(
        "src/norad/analyses/rank_cohort_candidates_with_paired_CMH/"
        "step_09_cmh_editing_site_calling.sh"
    ),
    "tool_check.slurm": contract(
        "tool_version_probes",
        default="lightweight_probe",
        execute="not_applicable",
        invalid_mode="not_applicable",
        module_policy="strict",
        module_calls=(
            "load python39",
            "load star/2.7.11b",
            "load samtools/1.19.2",
            "load picard/3.1.1",
            "list",
        ),
        submit_cwd="caller",
        output_validation="probe_only",
        exit_propagation="strict_except_optional_picard_probe",
    ),
    "validate_manifest.slurm": contract(
        "python -I -m norad validate manifest",
        default="lightweight_validation",
        execute="not_applicable",
        invalid_mode="not_applicable",
        module_policy="preinstalled_python",
        module_calls=(),
        submit_cwd="fallback",
        output_validation="child_exit_only",
    ),
}

JOB_PATHS = {
    name: Path(value.delegation).with_suffix(".slurm")
    for name, value in CONTRACTS.items()
    if value.delegation.endswith(".sh")
}
JOB_PATHS.update(
    {
        "step_00a_build_novogene_star_index.slurm": Path(
            "src/norad/stages/star_index/step_00a_build_novogene_star_index.slurm"
        ),
        "step_00b_gtf_to_bed12.slurm": Path(
            "src/norad/stages/gtf_to_bed12/step_00b_gtf_to_bed12.slurm"
        ),
        "tool_check.slurm": Path(
            "src/norad/evidence/runtime_preflight/tool_check.slurm"
        ),
        "validate_manifest.slurm": Path(
            "src/norad/ingestion/sample_manifest_admission/validate_manifest.slurm"
        ),
    }
)


def directives(
    job_name: str,
    time: str,
    *,
    partition: str | None = None,
    cpus: int = 1,
    export_tmp: bool = True,
    streams_first: bool = False,
) -> tuple[str, ...]:
    result = [f"#SBATCH --job-name={job_name}"]
    if partition:
        result.append(f"#SBATCH --partition={partition}")
    streams = ("#SBATCH --output=logs/%x-%j.out", "#SBATCH --error=logs/%x-%j.err")
    if streams_first:
        result.extend(streams)
    result.extend((f"#SBATCH --time={time}", f"#SBATCH --cpus-per-task={cpus}"))
    if export_tmp:
        result.append("#SBATCH --export=ALL,TMPDIR=/tmp")
    if not streams_first:
        result.extend(streams)
    return tuple(result)


SBATCH_DIRECTIVES = {
    "step_00a_build_novogene_star_index.slurm": directives(
        "norad-build-star-index",
        "08:00:00",
        partition="long",
        cpus=8,
        streams_first=True,
    ),
    "step_00b_gtf_to_bed12.slurm": directives(
        "norad-gtf-bed12", "00:30:00", partition="short"
    ),
    "step_00c_prepare_gatk_reference.slurm": directives(
        "norad-gatk-ref", "00:30:00", partition="short"
    ),
    "step_01_star_align.slurm": directives(
        "norad-star-align",
        "08:00:00",
        partition="long",
        cpus=8,
        streams_first=True,
    ),
    "step_02_sort_index_bam.slurm": directives(
        "norad-sort-index-bam",
        "01:00:00",
        partition="short",
        cpus=8,
        export_tmp=False,
        streams_first=True,
    ),
    "step_02b_bam_qc.slurm": directives("norad-bam-qc", "00:30:00", partition="short"),
    "step_03_infer_strandedness_and_orientation.slurm": directives(
        "norad-infer-strandedness", "00:30:00", partition="short"
    ),
    "step_04_mark_duplicates.slurm": directives(
        "norad-markdup", "02:00:00", partition="short"
    ),
    "step_05_split_n_cigar_reads.slurm": directives(
        "norad-split-n-cigar", "02:00:00", partition="short"
    ),
    "step_06_split_bam_by_read_orientation.slurm": directives(
        "norad-split-orientation", "02:00:00", partition="short"
    ),
    "step_07_bcftools_mpileup_by_chrom_and_strand.slurm": directives(
        "norad-mpileup", "08:00:00", partition="long"
    ),
    "step_08_vcf_preprocessing.slurm": directives(
        "norad-vcf-preprocess", "08:00:00", partition="long"
    ),
    "step_09_cmh_editing_site_calling.slurm": directives(
        "norad-cmh", "08:00:00", partition="long"
    ),
    "tool_check.slurm": directives("norad-tool-check", "00:05:00", streams_first=True),
    "validate_manifest.slurm": directives(
        "norad-validate-manifest", "00:05:00", streams_first=True
    ),
}


ENV_BASH_JOBS = frozenset(CONTRACTS) - {
    "step_02_sort_index_bam.slurm",
    "tool_check.slurm",
    "validate_manifest.slurm",
}
EXECUTABLE_JOBS = frozenset(
    {
        "step_00b_gtf_to_bed12.slurm",
        "step_00c_prepare_gatk_reference.slurm",
        "step_06_split_bam_by_read_orientation.slurm",
        "step_09_cmh_editing_site_calling.slurm",
    }
)
DELEGATED_JOBS = tuple(
    name for name, value in CONTRACTS.items() if value.execute == "explicit"
)
NO_EXPLICIT_MODE_JOBS = tuple(
    name for name, value in CONTRACTS.items() if value.execute != "explicit"
)
EMPTY_ARRAY_DRY_RUN_DEFECTS = frozenset(
    {
        "step_00c_prepare_gatk_reference.slurm",
        "step_02_sort_index_bam.slurm",
        "step_02b_bam_qc.slurm",
        "step_03_infer_strandedness_and_orientation.slurm",
        "step_04_mark_duplicates.slurm",
        "step_05_split_n_cigar_reads.slurm",
        "step_06_split_bam_by_read_orientation.slurm",
    }
)


@dataclass(frozen=True)
class FixturePath:
    name: str
    template: str
    content: str = "fixture\n"
    kind: str = "file"


@dataclass(frozen=True)
class DelegatedFixtureCase:
    paths: tuple[FixturePath, ...]
    environment: tuple[tuple[str, str], ...]
    arguments: tuple[tuple[str, str], ...]
    outputs: tuple[str, ...] = ()
    output_directories: tuple[str, ...] = ()


def path(name: str, template: str) -> FixturePath:
    return FixturePath(name, template, kind="path")


def directory(name: str, template: str) -> FixturePath:
    return FixturePath(name, template, kind="directory")


DELEGATED_FIXTURES = {
    "step_00c_prepare_gatk_reference.slurm": DelegatedFixtureCase(
        paths=(FixturePath("fasta", "{submit}/refs/genome.fa", ">chr1\nACGT\n"),),
        environment=(
            ("REFERENCE_FASTA", "{fasta}"),
            ("SAMTOOLS_BIN_OVERRIDE", "{fake_bin}/samtools"),
            ("GATK_BIN_OVERRIDE", "{fake_bin}/gatk"),
            ("JAVA_BIN_OVERRIDE", "{fake_bin}/java"),
        ),
        arguments=(
            ("--reference-fasta", "{fasta}"),
            ("--samtools-bin", "{fake_bin}/samtools"),
            ("--gatk-bin", "{fake_bin}/gatk"),
            ("--java-bin", "{fake_bin}/java"),
        ),
        outputs=("{fasta}.fai", "{submit}/refs/genome.dict"),
    ),
    "step_01_star_align.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("r1", "{submit}/inputs/sample_R1.fastq.gz"),
            FixturePath("r2", "{submit}/inputs/sample_R2.fastq.gz"),
            directory("star_index", "{submit}/refs/star-index"),
            path("output_dir", "{submit}/outputs/step01"),
        ),
        environment=(
            ("SAMPLE_ID", "sample-test"),
            ("R1_FASTQ", "{r1}"),
            ("R2_FASTQ", "{r2}"),
            ("STAR_INDEX", "{star_index}"),
            ("OUTPUT_DIR", "{output_dir}"),
        ),
        arguments=(
            ("--sample-id", "sample-test"),
            ("--r1-fastq", "{r1}"),
            ("--r2-fastq", "{r2}"),
            ("--star-index", "{star_index}"),
            ("--output-dir", "{output_dir}"),
            ("--threads", "3"),
        ),
        output_directories=("{output_dir}",),
    ),
    "step_02_sort_index_bam.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("input", "{submit}/inputs/aligned.bam"),
            path("output_dir", "{submit}/outputs/step02"),
        ),
        environment=(
            ("SAMPLE_ID", "sample02"),
            ("INPUT_ALIGNMENT", "{input}"),
            ("OUTPUT_DIR", "{output_dir}"),
            ("THREADS", "4"),
        ),
        arguments=(
            ("--sample-id", "sample02"),
            ("--input-alignment", "{input}"),
            ("--output-dir", "{output_dir}"),
            ("--threads", "4"),
        ),
        outputs=(
            "{output_dir}/sample02.sorted.bam",
            "{output_dir}/sample02.sorted.bam.bai",
        ),
        output_directories=("{output_dir}",),
    ),
    "step_02b_bam_qc.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("bam", "{submit}/inputs/sample02b.bam"),
            path("output_dir", "{submit}/outputs/step02b"),
        ),
        environment=(
            ("SAMPLE_ID", "sample02b"),
            ("BAM", "{bam}"),
            ("OUTPUT_DIR", "{output_dir}"),
        ),
        arguments=(
            ("--sample-id", "sample02b"),
            ("--bam", "{bam}"),
            ("--output-dir", "{output_dir}"),
        ),
        outputs=(
            "{output_dir}/sample02b.quickcheck.txt",
            "{output_dir}/sample02b.flagstat.txt",
        ),
        output_directories=("{output_dir}",),
    ),
    "step_03_infer_strandedness_and_orientation.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("bam", "{submit}/inputs/sample03.bam"),
            FixturePath("bed", "{submit}/refs/genes.bed"),
            path("output_dir", "{submit}/outputs/step03"),
        ),
        environment=(
            ("SAMPLE_ID", "sample03"),
            ("BAM", "{bam}"),
            ("BED12", "{bed}"),
            ("OUTPUT_DIR", "{output_dir}"),
            ("INFER_EXPERIMENT_BIN", "{fake_bin}/infer_experiment.py"),
        ),
        arguments=(
            ("--sample-id", "sample03"),
            ("--input-bam", "{bam}"),
            ("--bed12", "{bed}"),
            ("--output-dir", "{output_dir}"),
            ("--infer-experiment-bin", "{fake_bin}/infer_experiment.py"),
        ),
        outputs=("{output_dir}/sample03.infer_experiment.txt",),
        output_directories=("{output_dir}",),
    ),
    "step_04_mark_duplicates.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("bam", "{submit}/inputs/sample04.bam"),
            path("output_dir", "{submit}/outputs/step04"),
            path("metrics_dir", "{submit}/outputs/step04-qc"),
            FixturePath("picard", "{fake_bin}/picard.jar", "mock jar\n"),
        ),
        environment=(
            ("SAMPLE_ID", "sample04"),
            ("INPUT_BAM", "{bam}"),
            ("OUTPUT_DIR", "{output_dir}"),
            ("METRICS_DIR", "{metrics_dir}"),
            ("PICARD", "{picard}"),
            ("JAVA_BIN_OVERRIDE", "{fake_bin}/java"),
        ),
        arguments=(
            ("--sample-id", "sample04"),
            ("--input-bam", "{bam}"),
            ("--output-dir", "{output_dir}"),
            ("--metrics-dir", "{metrics_dir}"),
            ("--picard-jar", "{picard}"),
            ("--java-bin", "{fake_bin}/java"),
        ),
        outputs=(
            "{output_dir}/sample04.markdup.bam",
            "{output_dir}/sample04.markdup.bam.bai",
            "{metrics_dir}/sample04.markdup.metrics.txt",
        ),
        output_directories=("{output_dir}", "{metrics_dir}"),
    ),
    "step_05_split_n_cigar_reads.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("bam", "{submit}/inputs/sample05.bam"),
            FixturePath("fasta", "{submit}/refs/genome.fa", ">chr1\nACGT\n"),
            path("output_dir", "{submit}/outputs/step05"),
        ),
        environment=(
            ("SAMPLE_ID", "sample05"),
            ("INPUT_BAM", "{bam}"),
            ("REFERENCE_FASTA", "{fasta}"),
            ("OUTPUT_DIR", "{output_dir}"),
            ("GATK_BIN_OVERRIDE", "{fake_bin}/gatk"),
            ("SAMTOOLS_BIN_OVERRIDE", "{fake_bin}/samtools"),
            ("JAVA_BIN_OVERRIDE", "{fake_bin}/java"),
        ),
        arguments=(
            ("--sample-id", "sample05"),
            ("--input-bam", "{bam}"),
            ("--reference-fasta", "{fasta}"),
            ("--output-dir", "{output_dir}"),
            ("--gatk-bin", "{fake_bin}/gatk"),
            ("--samtools-bin", "{fake_bin}/samtools"),
            ("--java-bin", "{fake_bin}/java"),
        ),
        outputs=(
            "{output_dir}/sample05.split_ncigar.bam",
            "{output_dir}/sample05.split_ncigar.bam.bai",
        ),
        output_directories=("{output_dir}",),
    ),
    "step_06_split_bam_by_read_orientation.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("bam", "{submit}/inputs/sample06.bam"),
            path("output_dir", "{submit}/outputs/step06"),
            path("qc_dir", "{submit}/outputs/step06-qc"),
        ),
        environment=(
            ("SAMPLE_ID", "sample06"),
            ("INPUT_BAM", "{bam}"),
            ("OUTPUT_DIR", "{output_dir}"),
            ("QC_DIR", "{qc_dir}"),
            ("THREADS", "2"),
            ("SAMTOOLS_BIN_OVERRIDE", "{fake_bin}/samtools"),
        ),
        arguments=(
            ("--sample-id", "sample06"),
            ("--input-bam", "{bam}"),
            ("--output-dir", "{output_dir}"),
            ("--qc-dir", "{qc_dir}"),
            ("--threads", "2"),
            ("--samtools-bin", "{fake_bin}/samtools"),
        ),
        outputs=(
            "{output_dir}/sample06.FWD_like.bam",
            "{output_dir}/sample06.FWD_like.bam.bai",
            "{output_dir}/sample06.REV_like.bam",
            "{output_dir}/sample06.REV_like.bam.bai",
            "{qc_dir}/sample06.orientation_counts.tsv",
        ),
        output_directories=("{output_dir}", "{qc_dir}"),
    ),
    "step_07_bcftools_mpileup_by_chrom_and_strand.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("samples", "{submit}/inputs/samples.tsv"),
            FixturePath("partitions", "{submit}/inputs/partitions.tsv"),
            path("orientation_root", "{submit}/inputs/orientation"),
            FixturePath("reference", "{submit}/refs/genome.fa", ">chr1\nACGT\n"),
            path("output_root", "{submit}/outputs/step07"),
        ),
        environment=(
            ("COHORT_ID", "cohort07"),
            ("SAMPLE_MANIFEST", "{samples}"),
            ("PARTITION_MANIFEST", "{partitions}"),
            ("PARTITION_ID", "part-A"),
            ("ORIENTATION_ROOT", "{orientation_root}"),
            ("REFERENCE_FASTA", "{reference}"),
            ("OUTPUT_ROOT", "{output_root}"),
            ("MAX_DEPTH", "123"),
            ("FILTER_EXPRESSION", "INFO/AD[1-]>7 & MAX(FORMAT/DP)>31"),
            ("BCFTOOLS_BIN_OVERRIDE", "{fake_bin}/bcftools"),
        ),
        arguments=(
            ("--cohort-id", "cohort07"),
            ("--sample-manifest", "{samples}"),
            ("--partition-manifest", "{partitions}"),
            ("--partition-id", "part-A"),
            ("--orientation-root", "{orientation_root}"),
            ("--reference-fasta", "{reference}"),
            ("--output-root", "{output_root}"),
            ("--max-depth", "123"),
            ("--filter-expression", "INFO/AD[1-]>7 & MAX(FORMAT/DP)>31"),
            ("--bcftools-bin", "{fake_bin}/bcftools"),
        ),
        outputs=(
            "{output_root}/cohort07/part-A/cohort07.part-A.FWD_like.mpileup.vcf",
            "{output_root}/cohort07/part-A/cohort07.part-A.REV_like.mpileup.vcf",
            "{output_root}/cohort07/part-A/cohort07.part-A.step07_outputs.tsv",
        ),
        output_directories=("{output_root}/cohort07/part-A",),
    ),
    "step_08_vcf_preprocessing.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("samples", "{submit}/inputs/samples.tsv"),
            FixturePath("partitions", "{submit}/inputs/partitions.tsv"),
            FixturePath("annotation", "{submit}/refs/genes.gtf"),
            path("step07_root", "{submit}/inputs/step07"),
            path("output_root", "{submit}/outputs/step08"),
            path("qc_root", "{submit}/outputs/step08-qc"),
            FixturePath("r_script", "{submit}/implementation/step08.R"),
        ),
        environment=(
            ("COHORT_ID", "cohort08"),
            ("SAMPLE_MANIFEST", "{samples}"),
            ("PARTITION_MANIFEST", "{partitions}"),
            ("STEP07_ROOT", "{step07_root}"),
            ("ANNOTATION_GTF", "{annotation}"),
            ("OUTPUT_ROOT", "{output_root}"),
            ("QC_ROOT", "{qc_root}"),
            ("RSCRIPT_BIN_OVERRIDE", "{fake_bin}/Rscript"),
            ("STEP08_R_SCRIPT", "{r_script}"),
        ),
        arguments=(
            ("--cohort-id", "cohort08"),
            ("--sample-manifest", "{samples}"),
            ("--partition-manifest", "{partitions}"),
            ("--step07-root", "{step07_root}"),
            ("--annotation-gtf", "{annotation}"),
            ("--output-root", "{output_root}"),
            ("--qc-root", "{qc_root}"),
            ("--rscript-bin", "{fake_bin}/Rscript"),
            ("--r-script", "{r_script}"),
        ),
        outputs=(
            "{output_root}/cohort08/cohort08.step08_sites.tsv",
            "{output_root}/cohort08/cohort08.step08_inputs.tsv",
            "{qc_root}/cohort08.step08_summary.tsv",
        ),
        output_directories=("{output_root}/cohort08", "{qc_root}"),
    ),
    "step_09_cmh_editing_site_calling.slurm": DelegatedFixtureCase(
        paths=(
            FixturePath("samples", "{submit}/inputs/samples.tsv"),
            FixturePath("partitions", "{submit}/inputs/partitions.tsv"),
            path("step08_root", "{submit}/inputs/step08"),
            path("output_root", "{submit}/outputs/step09"),
            FixturePath("r_script", "{submit}/implementation/step09.R"),
        ),
        environment=(
            ("ANALYSIS_ID", "analysis09"),
            ("COHORT_ID", "cohort09"),
            ("SAMPLE_MANIFEST", "{samples}"),
            ("PARTITION_MANIFEST", "{partitions}"),
            ("STEP08_ROOT", "{step08_root}"),
            ("OUTPUT_ROOT", "{output_root}"),
            ("CONTROL_CONDITION", "control"),
            ("TREATMENT_CONDITION", "treatment"),
            ("RNA_REF", "C"),
            ("RNA_ALT", "T"),
            ("MIN_SAMPLE_DP", "2"),
            ("MEAN_DP_THRESHOLD", "42"),
            ("FDR_THRESHOLD", "0.1"),
            ("COMMON_OR_THRESHOLD", "1.5"),
            ("ABSOLUTE_DIFFERENCE_THRESHOLD", "0.02"),
            ("BACKGROUND_CONDITION", "background"),
            ("BACKGROUND_MAX_FRACTION", "0.03"),
            ("RSCRIPT_BIN_OVERRIDE", "{fake_bin}/Rscript"),
            ("STEP09_R_SCRIPT", "{r_script}"),
        ),
        arguments=(
            ("--analysis-id", "analysis09"),
            ("--cohort-id", "cohort09"),
            ("--sample-manifest", "{samples}"),
            ("--partition-manifest", "{partitions}"),
            ("--step08-root", "{step08_root}"),
            ("--output-root", "{output_root}"),
            ("--control-condition", "control"),
            ("--treatment-condition", "treatment"),
            ("--rna-ref", "C"),
            ("--rna-alt", "T"),
            ("--min-sample-dp", "2"),
            ("--mean-dp-threshold", "42"),
            ("--fdr-threshold", "0.1"),
            ("--common-or-threshold", "1.5"),
            ("--absolute-difference-threshold", "0.02"),
            ("--background-max-fraction", "0.03"),
            ("--rscript-bin", "{fake_bin}/Rscript"),
            ("--r-script", "{r_script}"),
            ("--background-condition", "background"),
        ),
        outputs=tuple(
            "{output_root}/analysis09/analysis09." + suffix
            for suffix in (
                "cmh_all_sites.tsv",
                "cmh_significant_sites.tsv",
                "cmh_summary.tsv",
                "mutation_spectrum.tsv",
                "mutation_spectrum.pdf",
                "depth_delta.pdf",
            )
        ),
        output_directories=("{output_root}/analysis09",),
    ),
}
