"""Independent local characterization of every tracked SLURM entry point."""

from __future__ import annotations

import os
import stat
import subprocess
from dataclasses import dataclass, fields
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
JOBS_ROOT = REPO_ROOT / "jobs"
JOB_PATHS = {
    "step_00a_build_novogene_star_index.slurm": Path(
        "src/norad/stages/construct_STAR_index/"
        "step_00a_build_novogene_star_index.slurm"
    ),
    "step_00b_gtf_to_bed12.slurm": Path(
        "src/norad/stages/convert_GTF_to_BED12/step_00b_gtf_to_bed12.slurm"
    ),
    "step_00c_prepare_gatk_reference.slurm": Path(
        "src/norad/stages/construct_FASTA_sidecars/"
        "step_00c_prepare_gatk_reference.slurm"
    ),
    "step_01_star_align.slurm": Path(
        "src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.slurm"
    ),
    "step_02_sort_index_bam.slurm": Path(
        "src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.slurm"
    ),
    "step_02b_bam_qc.slurm": Path(
        "src/norad/evidence/collect_canonical_BAM_QC_evidence/"
        "step_02b_bam_qc.slurm"
    ),
    "step_03_infer_strandedness_and_orientation.slurm": Path(
        "jobs/step_03_infer_strandedness_and_orientation.slurm"
    ),
    "step_04_mark_duplicates.slurm": Path("jobs/step_04_mark_duplicates.slurm"),
    "step_05_split_n_cigar_reads.slurm": Path(
        "jobs/step_05_split_n_cigar_reads.slurm"
    ),
    "step_06_split_bam_by_read_orientation.slurm": Path(
        "jobs/step_06_split_bam_by_read_orientation.slurm"
    ),
    "step_07_bcftools_mpileup_by_chrom_and_strand.slurm": Path(
        "jobs/step_07_bcftools_mpileup_by_chrom_and_strand.slurm"
    ),
    "step_08_vcf_preprocessing.slurm": Path("jobs/step_08_vcf_preprocessing.slurm"),
    "step_09_cmh_editing_site_calling.slurm": Path(
        "jobs/step_09_cmh_editing_site_calling.slurm"
    ),
    "template.slurm": Path("jobs/template.slurm"),
    "tool_check.slurm": Path("jobs/tool_check.slurm"),
    "validate_manifest.slurm": Path("jobs/validate_manifest.slurm"),
}


def job_path(name: str) -> Path:
    return REPO_ROOT / JOB_PATHS[name]


@dataclass(frozen=True)
class WrapperContract:
    default: str
    execute: str
    invalid_mode: str
    module_policy: str
    module_calls: tuple[str, ...]
    submit_cwd: str
    delegation: str
    output_validation: str
    exit_propagation: str


CONTRACTS = {
    "step_00a_build_novogene_star_index.slurm": WrapperContract(
        default="legacy_implicit_execute",
        execute="implicit_only",
        invalid_mode="not_applicable",
        module_policy="strict",
        module_calls=("load star/2.7.11b", "list"),
        submit_cwd="caller",
        delegation="embedded_star",
        output_validation="none_after_child_success",
        exit_propagation="strict",
    ),
    "step_00b_gtf_to_bed12.slurm": WrapperContract(
        default="legacy_implicit_execute",
        execute="implicit_only",
        invalid_mode="not_applicable",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("list", "load bedtools/2.31.1", "list"),
        submit_cwd="required",
        delegation="embedded_python_and_bedtools",
        output_validation="bed12_field_count",
        exit_propagation="strict",
    ),
    "step_00c_prepare_gatk_reference.slurm": WrapperContract(
        default="dry_run_with_bash32_empty_array_defect",
        execute="explicit",
        invalid_mode="reject",
        module_policy="tolerated",
        module_calls=("list", "load samtools/1.19.2", "list"),
        submit_cwd="fallback",
        delegation=(
            "src/norad/stages/construct_FASTA_sidecars/"
            "step_00c_prepare_gatk_reference.sh"
        ),
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_01_star_align.slurm": WrapperContract(
        default="dry_run_with_fixture_side_effects",
        execute="explicit",
        invalid_mode="reject",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("list", "load star/2.7.11b", "list"),
        submit_cwd="caller",
        delegation=(
            "src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh"
        ),
        output_validation="delegate_only",
        exit_propagation="strict",
    ),
    "step_02_sort_index_bam.slurm": WrapperContract(
        default="dry_run_creates_output_directory_with_bash32_empty_array_defect",
        execute="explicit",
        invalid_mode="reject",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("list", "load samtools/1.19.2", "list"),
        submit_cwd="caller",
        delegation=(
            "src/norad/stages/construct_canonical_BAM/"
            "step_02_sort_index_bam.sh"
        ),
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_02b_bam_qc.slurm": WrapperContract(
        default="dry_run_creates_output_directory_with_bash32_empty_array_defect",
        execute="explicit",
        invalid_mode="reject",
        module_policy="strict_loads_tolerated_lists",
        module_calls=("load samtools/1.19.2", "list"),
        submit_cwd="required",
        delegation=(
            "src/norad/evidence/collect_canonical_BAM_QC_evidence/"
            "step_02b_bam_qc.sh"
        ),
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_03_infer_strandedness_and_orientation.slurm": WrapperContract(
        default="dry_run_with_bash32_empty_array_defect",
        execute="explicit",
        invalid_mode="reject",
        module_policy="tolerated",
        module_calls=("list",),
        submit_cwd="fallback",
        delegation="scripts/step_03_infer_strandedness_and_orientation.sh",
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_04_mark_duplicates.slurm": WrapperContract(
        default="dry_run_with_bash32_empty_array_defect",
        execute="explicit",
        invalid_mode="reject",
        module_policy="strict_loads_tolerated_lists",
        module_calls=(
            "list",
            "load picard/3.1.1",
            "load samtools/1.19.2",
            "list",
        ),
        submit_cwd="fallback",
        delegation="scripts/step_04_mark_duplicates.sh",
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_05_split_n_cigar_reads.slurm": WrapperContract(
        default="dry_run_with_bash32_empty_array_defect",
        execute="explicit",
        invalid_mode="reject",
        module_policy="tolerated",
        module_calls=("list", "load samtools/1.19.2", "list"),
        submit_cwd="fallback",
        delegation="scripts/step_05_split_n_cigar_reads.sh",
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_06_split_bam_by_read_orientation.slurm": WrapperContract(
        default="dry_run_with_bash32_empty_array_defect",
        execute="explicit",
        invalid_mode="reject",
        module_policy="tolerated",
        module_calls=("list", "load samtools/1.19.2", "list"),
        submit_cwd="fallback",
        delegation="scripts/step_06_split_bam_by_read_orientation.sh",
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_07_bcftools_mpileup_by_chrom_and_strand.slurm": WrapperContract(
        default="dry_run",
        execute="explicit",
        invalid_mode="reject",
        module_policy="tolerated",
        module_calls=("list", "load CBI bcftools/1.21", "list"),
        submit_cwd="fallback",
        delegation="scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh",
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_08_vcf_preprocessing.slurm": WrapperContract(
        default="dry_run",
        execute="explicit",
        invalid_mode="reject",
        module_policy="tolerated",
        module_calls=("list",),
        submit_cwd="fallback",
        delegation="scripts/step_08_vcf_preprocessing.sh",
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "step_09_cmh_editing_site_calling.slurm": WrapperContract(
        default="dry_run",
        execute="explicit",
        invalid_mode="reject",
        module_policy="tolerated",
        module_calls=("list",),
        submit_cwd="fallback",
        delegation="scripts/step_09_cmh_editing_site_calling.sh",
        output_validation="wrapper_files",
        exit_propagation="strict",
    ),
    "template.slurm": WrapperContract(
        default="lightweight_probe",
        execute="not_applicable",
        invalid_mode="not_applicable",
        module_policy="strict_loads_tolerated_lists",
        module_calls=(
            "list",
            "load star/2.7.11b",
            "load samtools/1.19.2",
            "load picard/3.1.1",
            "load python39",
            "list",
        ),
        submit_cwd="caller",
        delegation="future_template_placeholder",
        output_validation="probe_only",
        exit_propagation="strict",
    ),
    "tool_check.slurm": WrapperContract(
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
        delegation="tool_version_probes",
        output_validation="probe_only",
        exit_propagation="strict_except_optional_picard_probe",
    ),
    "validate_manifest.slurm": WrapperContract(
        default="lightweight_validation",
        execute="not_applicable",
        invalid_mode="not_applicable",
        module_policy="strict",
        module_calls=("load python39",),
        submit_cwd="caller",
        delegation="scripts/validate_manifest.py",
        output_validation="child_exit_only",
        exit_propagation="strict",
    ),
}


SBATCH_DIRECTIVES = {
    "step_00a_build_novogene_star_index.slurm": (
        "#SBATCH --job-name=norad-build-star-index",
        "#SBATCH --partition=long",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
        "#SBATCH --time=08:00:00",
        "#SBATCH --cpus-per-task=8",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
    ),
    "step_00b_gtf_to_bed12.slurm": (
        "#SBATCH --job-name=norad-gtf-bed12",
        "#SBATCH --partition=short",
        "#SBATCH --time=00:30:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_00c_prepare_gatk_reference.slurm": (
        "#SBATCH --job-name=norad-gatk-ref",
        "#SBATCH --partition=short",
        "#SBATCH --time=00:30:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_01_star_align.slurm": (
        "#SBATCH --job-name=norad-star-align",
        "#SBATCH --partition=long",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
        "#SBATCH --time=08:00:00",
        "#SBATCH --cpus-per-task=8",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
    ),
    "step_02_sort_index_bam.slurm": (
        "#SBATCH --job-name=norad-sort-index-bam",
        "#SBATCH --partition=short",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
        "#SBATCH --time=01:00:00",
        "#SBATCH --cpus-per-task=8",
    ),
    "step_02b_bam_qc.slurm": (
        "#SBATCH --job-name=norad-bam-qc",
        "#SBATCH --partition=short",
        "#SBATCH --time=00:30:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_03_infer_strandedness_and_orientation.slurm": (
        "#SBATCH --job-name=norad-infer-strandedness",
        "#SBATCH --partition=short",
        "#SBATCH --time=00:30:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_04_mark_duplicates.slurm": (
        "#SBATCH --job-name=norad-markdup",
        "#SBATCH --partition=short",
        "#SBATCH --time=02:00:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_05_split_n_cigar_reads.slurm": (
        "#SBATCH --job-name=norad-split-n-cigar",
        "#SBATCH --partition=short",
        "#SBATCH --time=02:00:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_06_split_bam_by_read_orientation.slurm": (
        "#SBATCH --job-name=norad-split-orientation",
        "#SBATCH --partition=short",
        "#SBATCH --time=02:00:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_07_bcftools_mpileup_by_chrom_and_strand.slurm": (
        "#SBATCH --job-name=norad-mpileup",
        "#SBATCH --partition=long",
        "#SBATCH --time=08:00:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_08_vcf_preprocessing.slurm": (
        "#SBATCH --job-name=norad-vcf-preprocess",
        "#SBATCH --partition=long",
        "#SBATCH --time=08:00:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "step_09_cmh_editing_site_calling.slurm": (
        "#SBATCH --job-name=norad-cmh",
        "#SBATCH --partition=long",
        "#SBATCH --time=08:00:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
    ),
    "template.slurm": (
        "#SBATCH --export=ALL,TMPDIR=/tmp",
        "#SBATCH --job-name=norad-template",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
        "#SBATCH --time=01:00:00",
        "#SBATCH --cpus-per-task=4",
    ),
    "tool_check.slurm": (
        "#SBATCH --job-name=norad-tool-check",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
        "#SBATCH --time=00:05:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
    ),
    "validate_manifest.slurm": (
        "#SBATCH --job-name=norad-validate-manifest",
        "#SBATCH --output=logs/%x-%j.out",
        "#SBATCH --error=logs/%x-%j.err",
        "#SBATCH --time=00:05:00",
        "#SBATCH --cpus-per-task=1",
        "#SBATCH --export=ALL,TMPDIR=/tmp",
    ),
}


ENV_BASH_JOBS = frozenset(
    {
        "step_00a_build_novogene_star_index.slurm",
        "step_00b_gtf_to_bed12.slurm",
        "step_00c_prepare_gatk_reference.slurm",
        "step_01_star_align.slurm",
        "step_02b_bam_qc.slurm",
        "step_03_infer_strandedness_and_orientation.slurm",
        "step_04_mark_duplicates.slurm",
        "step_05_split_n_cigar_reads.slurm",
        "step_06_split_bam_by_read_orientation.slurm",
        "step_07_bcftools_mpileup_by_chrom_and_strand.slurm",
        "step_08_vcf_preprocessing.slurm",
        "step_09_cmh_editing_site_calling.slurm",
    }
)
EXECUTABLE_JOBS = frozenset(
    {
        "step_00b_gtf_to_bed12.slurm",
        "step_00c_prepare_gatk_reference.slurm",
        "step_06_split_bam_by_read_orientation.slurm",
        "step_09_cmh_editing_site_calling.slurm",
    }
)
DELEGATED_JOBS = tuple(
    name for name, contract in CONTRACTS.items() if contract.execute == "explicit"
)
NO_EXPLICIT_MODE_JOBS = tuple(
    name for name, contract in CONTRACTS.items() if contract.execute != "explicit"
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


@dataclass
class PreparedWrapper:
    name: str
    submit: Path
    launch: Path
    environment: dict[str, str]
    expected_args: tuple[str, ...]
    outputs: tuple[Path, ...]
    output_directories: tuple[Path, ...]
    delegate_log: Path
    delegate_cwd_log: Path
    module_log: Path


def write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def touch(path: Path, content: str = "fixture\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def install_module_fake(fake_bin: Path) -> None:
    write_executable(
        fake_bin / "module",
        """#!/bin/bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_MODULE_LOG:?}"
exit "${FAKE_MODULE_EXIT:-0}"
""",
    )


def install_tool_fakes(fake_bin: Path) -> None:
    body = """#!/bin/bash
set -euo pipefail
tool="${0##*/}"
{
    printf '%s' "$tool"
    printf '\t%s' "$@"
    printf '\n'
} >> "${FAKE_TOOL_LOG:?}"
if [[ "${FAKE_FAIL_TOOL:-}" == "$tool" ]]; then
    exit "${FAKE_TOOL_EXIT:-37}"
fi
if [[ "$tool" == "java" && "${1:-}" == "-jar" && "${FAKE_FAIL_JAVA_JAR:-0}" == "1" ]]; then
    exit "${FAKE_TOOL_EXIT:-37}"
fi
case "$tool" in
    java)
        printf 'openjdk version "17.0.14"\n' >&2
        ;;
    STAR)
        printf 'STAR_2.7.11b\n'
        args=("$@")
        for ((i = 0; i < ${#args[@]}; i++)); do
            if [[ "${args[$i]}" == "--genomeDir" ]]; then
                mkdir -p "${args[$((i + 1))]}"
                printf 'mock STAR index\n' > "${args[$((i + 1))]}/Genome"
            fi
        done
        ;;
    samtools)
        printf 'samtools 1.19.2\n'
        ;;
    gatk)
        printf 'GATK 4.6.1.0\n'
        ;;
    bcftools)
        printf 'bcftools 1.21\n'
        ;;
    Rscript)
        printf 'Rscript 4.6.1\n'
        ;;
    python)
        printf 'Python 3.11.0\n'
        ;;
esac
"""
    for name in (
        "STAR",
        "samtools",
        "gatk",
        "bcftools",
        "Rscript",
        "infer_experiment.py",
        "python",
        "java",
    ):
        write_executable(fake_bin / name, body)


def install_delegate_stub(path: Path) -> None:
    write_executable(
        path,
        """#!/bin/bash
set -euo pipefail
printf '%s\n' "$@" > "${FAKE_DELEGATE_LOG:?}"
printf '%s\n' "$PWD" > "${FAKE_DELEGATE_CWD_LOG:?}"
if [[ "${FAKE_CHILD_EXIT:-0}" != "0" ]]; then
    exit "$FAKE_CHILD_EXIT"
fi
execute=0
for argument in "$@"; do
    [[ "$argument" == "--execute" ]] && execute=1
done
if [[ "$execute" == "1" && "${FAKE_SKIP_OUTPUTS:-0}" != "1" ]]; then
    while IFS= read -r output; do
        [[ -n "$output" ]] || continue
        mkdir -p "$(dirname "$output")"
        printf 'mock wrapper output\n' > "$output"
    done < "${FAKE_OUTPUT_LIST:?}"
fi
""",
    )


def base_environment(root: Path, fake_bin: Path) -> dict[str, str]:
    runtime_tmp = root / "runtime-tmp"
    runtime_tmp.mkdir(parents=True, exist_ok=True)
    module_log = root / "module.log"
    tool_log = root / "tool.log"
    picard = touch(root / "picard.jar", "mock jar\n")
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": os.pathsep.join((str(fake_bin), "/usr/bin", "/bin")),
            "TMPDIR": str(runtime_tmp),
            "USER": "norad-test",
            "SLURM_JOB_ID": "local-wrapper-test",
            "SLURM_JOB_NAME": "local-wrapper-test",
            "SLURMD_NODENAME": "local-mock-node",
            "SLURM_CPUS_PER_TASK": "3",
            "JAVA_HOME": "",
            "PICARD": str(picard),
            "FAKE_MODULE_LOG": str(module_log),
            "FAKE_MODULE_EXIT": "0",
            "FAKE_TOOL_LOG": str(tool_log),
            "FAKE_TOOL_EXIT": "37",
            "FAKE_FAIL_TOOL": "",
            "FAKE_FAIL_JAVA_JAR": "0",
        }
    )
    environment.pop("EXECUTE", None)
    return environment


def prepare_delegated(name: str, tmp_path: Path) -> PreparedWrapper:
    contract = CONTRACTS[name]
    submit = tmp_path / "submit"
    launch = tmp_path / "alternate-launch"
    fake_bin = tmp_path / "fake-bin"
    submit.mkdir()
    launch.mkdir()
    fake_bin.mkdir()
    install_module_fake(fake_bin)
    install_tool_fakes(fake_bin)
    install_delegate_stub(submit / contract.delegation)

    environment = base_environment(tmp_path, fake_bin)
    environment["SLURM_SUBMIT_DIR"] = str(submit)
    environment["FAKE_DELEGATE_LOG"] = str(tmp_path / "delegate.args")
    environment["FAKE_DELEGATE_CWD_LOG"] = str(tmp_path / "delegate.cwd")
    environment["FAKE_CHILD_EXIT"] = "0"
    environment["FAKE_SKIP_OUTPUTS"] = "0"

    outputs: tuple[Path, ...]
    output_directories: tuple[Path, ...]

    if name == "step_00c_prepare_gatk_reference.slurm":
        fasta = touch(submit / "refs" / "genome.fa", ">chr1\nACGT\n")
        environment.update(
            {
                "REFERENCE_FASTA": str(fasta),
                "SAMTOOLS_BIN_OVERRIDE": str(fake_bin / "samtools"),
                "GATK_BIN_OVERRIDE": str(fake_bin / "gatk"),
                "JAVA_BIN_OVERRIDE": str(fake_bin / "java"),
            }
        )
        expected_args = (
            "--reference-fasta",
            str(fasta),
            "--samtools-bin",
            str(fake_bin / "samtools"),
            "--gatk-bin",
            str(fake_bin / "gatk"),
            "--java-bin",
            str(fake_bin / "java"),
        )
        outputs = (Path(f"{fasta}.fai"), fasta.parent / "genome.dict")
        output_directories = ()
    elif name == "step_01_star_align.slurm":
        r1 = touch(submit / "inputs" / "sample_R1.fastq.gz")
        r2 = touch(submit / "inputs" / "sample_R2.fastq.gz")
        star_index = submit / "refs" / "star-index"
        star_index.mkdir(parents=True)
        output_dir = submit / "outputs" / "step01"
        environment.update(
            {
                "SAMPLE_ID": "sample-test",
                "R1_FASTQ": str(r1),
                "R2_FASTQ": str(r2),
                "STAR_INDEX": str(star_index),
                "OUTPUT_DIR": str(output_dir),
            }
        )
        expected_args = (
            "--sample-id",
            "sample-test",
            "--r1-fastq",
            str(r1),
            "--r2-fastq",
            str(r2),
            "--star-index",
            str(star_index),
            "--output-dir",
            str(output_dir),
            "--threads",
            "3",
        )
        outputs = ()
        output_directories = (output_dir,)
    elif name == "step_02_sort_index_bam.slurm":
        input_alignment = touch(submit / "inputs" / "aligned.bam")
        output_dir = submit / "outputs" / "step02"
        environment.update(
            {
                "SAMPLE_ID": "sample02",
                "INPUT_ALIGNMENT": str(input_alignment),
                "OUTPUT_DIR": str(output_dir),
                "THREADS": "4",
            }
        )
        expected_args = (
            "--sample-id",
            "sample02",
            "--input-alignment",
            str(input_alignment),
            "--output-dir",
            str(output_dir),
            "--threads",
            "4",
        )
        output_bam = output_dir / "sample02.sorted.bam"
        outputs = (output_bam, Path(f"{output_bam}.bai"))
        output_directories = (output_dir,)
    elif name == "step_02b_bam_qc.slurm":
        bam = touch(submit / "inputs" / "sample02b.bam")
        output_dir = submit / "outputs" / "step02b"
        environment.update(
            {
                "SAMPLE_ID": "sample02b",
                "BAM": str(bam),
                "OUTPUT_DIR": str(output_dir),
            }
        )
        expected_args = (
            "--sample-id",
            "sample02b",
            "--bam",
            str(bam),
            "--output-dir",
            str(output_dir),
        )
        outputs = (
            output_dir / "sample02b.quickcheck.txt",
            output_dir / "sample02b.flagstat.txt",
        )
        output_directories = (output_dir,)
    elif name == "step_03_infer_strandedness_and_orientation.slurm":
        bam = touch(submit / "inputs" / "sample03.bam")
        bed = touch(submit / "refs" / "genes.bed")
        output_dir = submit / "outputs" / "step03"
        environment.update(
            {
                "SAMPLE_ID": "sample03",
                "BAM": str(bam),
                "BED12": str(bed),
                "OUTPUT_DIR": str(output_dir),
                "INFER_EXPERIMENT_BIN": str(fake_bin / "infer_experiment.py"),
            }
        )
        expected_args = (
            "--sample-id",
            "sample03",
            "--input-bam",
            str(bam),
            "--bed12",
            str(bed),
            "--output-dir",
            str(output_dir),
            "--infer-experiment-bin",
            str(fake_bin / "infer_experiment.py"),
        )
        outputs = (output_dir / "sample03.infer_experiment.txt",)
        output_directories = (output_dir,)
    elif name == "step_04_mark_duplicates.slurm":
        bam = touch(submit / "inputs" / "sample04.bam")
        output_dir = submit / "outputs" / "step04"
        metrics_dir = submit / "outputs" / "step04-qc"
        picard = touch(fake_bin / "picard.jar", "mock jar\n")
        environment.update(
            {
                "SAMPLE_ID": "sample04",
                "INPUT_BAM": str(bam),
                "OUTPUT_DIR": str(output_dir),
                "METRICS_DIR": str(metrics_dir),
                "PICARD": str(picard),
                "JAVA_BIN_OVERRIDE": str(fake_bin / "java"),
            }
        )
        expected_args = (
            "--sample-id",
            "sample04",
            "--input-bam",
            str(bam),
            "--output-dir",
            str(output_dir),
            "--metrics-dir",
            str(metrics_dir),
            "--picard-jar",
            str(picard),
            "--java-bin",
            str(fake_bin / "java"),
        )
        output_bam = output_dir / "sample04.markdup.bam"
        outputs = (
            output_bam,
            Path(f"{output_bam}.bai"),
            metrics_dir / "sample04.markdup.metrics.txt",
        )
        output_directories = (output_dir, metrics_dir)
    elif name == "step_05_split_n_cigar_reads.slurm":
        bam = touch(submit / "inputs" / "sample05.bam")
        fasta = touch(submit / "refs" / "genome.fa", ">chr1\nACGT\n")
        output_dir = submit / "outputs" / "step05"
        environment.update(
            {
                "SAMPLE_ID": "sample05",
                "INPUT_BAM": str(bam),
                "REFERENCE_FASTA": str(fasta),
                "OUTPUT_DIR": str(output_dir),
                "GATK_BIN_OVERRIDE": str(fake_bin / "gatk"),
                "SAMTOOLS_BIN_OVERRIDE": str(fake_bin / "samtools"),
                "JAVA_BIN_OVERRIDE": str(fake_bin / "java"),
            }
        )
        expected_args = (
            "--sample-id",
            "sample05",
            "--input-bam",
            str(bam),
            "--reference-fasta",
            str(fasta),
            "--output-dir",
            str(output_dir),
            "--gatk-bin",
            str(fake_bin / "gatk"),
            "--samtools-bin",
            str(fake_bin / "samtools"),
            "--java-bin",
            str(fake_bin / "java"),
        )
        output_bam = output_dir / "sample05.split_ncigar.bam"
        outputs = (output_bam, Path(f"{output_bam}.bai"))
        output_directories = (output_dir,)
    elif name == "step_06_split_bam_by_read_orientation.slurm":
        bam = touch(submit / "inputs" / "sample06.bam")
        output_dir = submit / "outputs" / "step06"
        qc_dir = submit / "outputs" / "step06-qc"
        environment.update(
            {
                "SAMPLE_ID": "sample06",
                "INPUT_BAM": str(bam),
                "OUTPUT_DIR": str(output_dir),
                "QC_DIR": str(qc_dir),
                "THREADS": "2",
                "SAMTOOLS_BIN_OVERRIDE": str(fake_bin / "samtools"),
            }
        )
        expected_args = (
            "--sample-id",
            "sample06",
            "--input-bam",
            str(bam),
            "--output-dir",
            str(output_dir),
            "--qc-dir",
            str(qc_dir),
            "--threads",
            "2",
            "--samtools-bin",
            str(fake_bin / "samtools"),
        )
        fwd_bam = output_dir / "sample06.FWD_like.bam"
        rev_bam = output_dir / "sample06.REV_like.bam"
        outputs = (
            fwd_bam,
            Path(f"{fwd_bam}.bai"),
            rev_bam,
            Path(f"{rev_bam}.bai"),
            qc_dir / "sample06.orientation_counts.tsv",
        )
        output_directories = (output_dir, qc_dir)
    elif name == "step_07_bcftools_mpileup_by_chrom_and_strand.slurm":
        sample_manifest = touch(submit / "inputs" / "samples.tsv")
        partition_manifest = touch(submit / "inputs" / "partitions.tsv")
        orientation_root = submit / "inputs" / "orientation"
        reference = touch(submit / "refs" / "genome.fa", ">chr1\nACGT\n")
        output_root = submit / "outputs" / "step07"
        filter_expression = "INFO/AD[1-]>7 & MAX(FORMAT/DP)>31"
        environment.update(
            {
                "COHORT_ID": "cohort07",
                "SAMPLE_MANIFEST": str(sample_manifest),
                "PARTITION_MANIFEST": str(partition_manifest),
                "PARTITION_ID": "part-A",
                "ORIENTATION_ROOT": str(orientation_root),
                "REFERENCE_FASTA": str(reference),
                "OUTPUT_ROOT": str(output_root),
                "MAX_DEPTH": "123",
                "FILTER_EXPRESSION": filter_expression,
                "BCFTOOLS_BIN_OVERRIDE": str(fake_bin / "bcftools"),
            }
        )
        expected_args = (
            "--cohort-id",
            "cohort07",
            "--sample-manifest",
            str(sample_manifest),
            "--partition-manifest",
            str(partition_manifest),
            "--partition-id",
            "part-A",
            "--orientation-root",
            str(orientation_root),
            "--reference-fasta",
            str(reference),
            "--output-root",
            str(output_root),
            "--max-depth",
            "123",
            "--filter-expression",
            filter_expression,
            "--bcftools-bin",
            str(fake_bin / "bcftools"),
        )
        partition_output = output_root / "cohort07" / "part-A"
        outputs = (
            partition_output / "cohort07.part-A.FWD_like.mpileup.vcf",
            partition_output / "cohort07.part-A.REV_like.mpileup.vcf",
            partition_output / "cohort07.part-A.step07_outputs.tsv",
        )
        output_directories = (partition_output,)
    elif name == "step_08_vcf_preprocessing.slurm":
        sample_manifest = touch(submit / "inputs" / "samples.tsv")
        partition_manifest = touch(submit / "inputs" / "partitions.tsv")
        annotation = touch(submit / "refs" / "genes.gtf")
        step07_root = submit / "inputs" / "step07"
        output_root = submit / "outputs" / "step08"
        qc_root = submit / "outputs" / "step08-qc"
        r_script = touch(submit / "implementation" / "step08.R")
        environment.update(
            {
                "COHORT_ID": "cohort08",
                "SAMPLE_MANIFEST": str(sample_manifest),
                "PARTITION_MANIFEST": str(partition_manifest),
                "STEP07_ROOT": str(step07_root),
                "ANNOTATION_GTF": str(annotation),
                "OUTPUT_ROOT": str(output_root),
                "QC_ROOT": str(qc_root),
                "RSCRIPT_BIN_OVERRIDE": str(fake_bin / "Rscript"),
                "STEP08_R_SCRIPT": str(r_script),
            }
        )
        expected_args = (
            "--cohort-id",
            "cohort08",
            "--sample-manifest",
            str(sample_manifest),
            "--partition-manifest",
            str(partition_manifest),
            "--step07-root",
            str(step07_root),
            "--annotation-gtf",
            str(annotation),
            "--output-root",
            str(output_root),
            "--qc-root",
            str(qc_root),
            "--rscript-bin",
            str(fake_bin / "Rscript"),
            "--r-script",
            str(r_script),
        )
        outputs = (
            output_root / "cohort08" / "cohort08.step08_sites.tsv",
            output_root / "cohort08" / "cohort08.step08_inputs.tsv",
            qc_root / "cohort08.step08_summary.tsv",
        )
        output_directories = (output_root / "cohort08", qc_root)
    elif name == "step_09_cmh_editing_site_calling.slurm":
        sample_manifest = touch(submit / "inputs" / "samples.tsv")
        partition_manifest = touch(submit / "inputs" / "partitions.tsv")
        step08_root = submit / "inputs" / "step08"
        output_root = submit / "outputs" / "step09"
        r_script = touch(submit / "implementation" / "step09.R")
        environment.update(
            {
                "ANALYSIS_ID": "analysis09",
                "COHORT_ID": "cohort09",
                "SAMPLE_MANIFEST": str(sample_manifest),
                "PARTITION_MANIFEST": str(partition_manifest),
                "STEP08_ROOT": str(step08_root),
                "OUTPUT_ROOT": str(output_root),
                "CONTROL_CONDITION": "control",
                "TREATMENT_CONDITION": "treatment",
                "RNA_REF": "C",
                "RNA_ALT": "T",
                "MIN_SAMPLE_DP": "2",
                "MEAN_DP_THRESHOLD": "42",
                "FDR_THRESHOLD": "0.1",
                "COMMON_OR_THRESHOLD": "1.5",
                "ABSOLUTE_DIFFERENCE_THRESHOLD": "0.02",
                "BACKGROUND_CONDITION": "background",
                "BACKGROUND_MAX_FRACTION": "0.03",
                "RSCRIPT_BIN_OVERRIDE": str(fake_bin / "Rscript"),
                "STEP09_R_SCRIPT": str(r_script),
            }
        )
        expected_args = (
            "--analysis-id",
            "analysis09",
            "--cohort-id",
            "cohort09",
            "--sample-manifest",
            str(sample_manifest),
            "--partition-manifest",
            str(partition_manifest),
            "--step08-root",
            str(step08_root),
            "--output-root",
            str(output_root),
            "--control-condition",
            "control",
            "--treatment-condition",
            "treatment",
            "--rna-ref",
            "C",
            "--rna-alt",
            "T",
            "--min-sample-dp",
            "2",
            "--mean-dp-threshold",
            "42",
            "--fdr-threshold",
            "0.1",
            "--common-or-threshold",
            "1.5",
            "--absolute-difference-threshold",
            "0.02",
            "--background-max-fraction",
            "0.03",
            "--rscript-bin",
            str(fake_bin / "Rscript"),
            "--r-script",
            str(r_script),
            "--background-condition",
            "background",
        )
        analysis_dir = output_root / "analysis09"
        outputs = tuple(
            analysis_dir / f"analysis09.{suffix}"
            for suffix in (
                "cmh_all_sites.tsv",
                "cmh_significant_sites.tsv",
                "cmh_summary.tsv",
                "mutation_spectrum.tsv",
                "mutation_spectrum.pdf",
                "depth_delta.pdf",
            )
        )
        output_directories = (analysis_dir,)
    else:  # pragma: no cover - exact inventory tests make this unreachable
        raise AssertionError(f"missing delegated fixture for {name}")

    output_list = tmp_path / "outputs.list"
    output_list.write_text(
        "".join(f"{output}\n" for output in outputs),
        encoding="utf-8",
    )
    environment["FAKE_OUTPUT_LIST"] = str(output_list)
    return PreparedWrapper(
        name=name,
        submit=submit,
        launch=launch,
        environment=environment,
        expected_args=expected_args,
        outputs=outputs,
        output_directories=output_directories,
        delegate_log=Path(environment["FAKE_DELEGATE_LOG"]),
        delegate_cwd_log=Path(environment["FAKE_DELEGATE_CWD_LOG"]),
        module_log=Path(environment["FAKE_MODULE_LOG"]),
    )


def run_prepared(
    prepared: PreparedWrapper,
    *,
    execute: str | None = None,
    environment_updates: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = prepared.environment.copy()
    if execute is None:
        environment.pop("EXECUTE", None)
    else:
        environment["EXECUTE"] = execute
    if environment_updates:
        environment.update(environment_updates)
    contract = CONTRACTS[prepared.name]
    if cwd is None:
        cwd = prepared.submit if contract.submit_cwd == "caller" else prepared.launch
    return subprocess.run(
        ["/bin/bash", str(job_path(prepared.name))],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def read_nul_args(path: Path) -> tuple[str, ...]:
    return tuple(path.read_text(encoding="utf-8").splitlines())


def local_bash_major() -> int:
    result = subprocess.run(
        ["/bin/bash", "-c", "printf '%s' \"${BASH_VERSINFO[0]}\""],
        text=True,
        capture_output=True,
        check=True,
    )
    return int(result.stdout)


def read_lines(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(path.read_text(encoding="utf-8").splitlines())


def test_inventory_and_contract_decisions_cover_every_live_wrapper() -> None:
    live_flat_jobs = {
        Path("jobs") / path.name for path in JOBS_ROOT.glob("*.slurm")
    }
    expected_flat_jobs = {
        path for path in JOB_PATHS.values() if path.parent == Path("jobs")
    }

    assert live_flat_jobs == expected_flat_jobs
    assert set(JOB_PATHS) == set(CONTRACTS) == set(SBATCH_DIRECTIVES)
    assert all(job_path(name).is_file() for name in CONTRACTS)
    assert len(set(JOB_PATHS.values())) == len(CONTRACTS) == 16
    for contract in CONTRACTS.values():
        assert all(getattr(contract, field.name) for field in fields(contract))


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_sbatch_shebang_strict_mode_and_file_mode_are_exact(name: str) -> None:
    job = job_path(name)
    lines = job.read_text(encoding="utf-8").splitlines()
    directives = tuple(line for line in lines if line.startswith("#SBATCH "))

    assert directives == SBATCH_DIRECTIVES[name]
    assert lines[0] == ("#!/usr/bin/env bash" if name in ENV_BASH_JOBS else "#!/bin/bash")
    assert "set -euo pipefail" in lines
    mode = job.stat().st_mode
    is_executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
    assert is_executable is (name in EXECUTABLE_JOBS)


@pytest.mark.parametrize("name", sorted(CONTRACTS))
def test_submit_directory_decision_is_literal(name: str) -> None:
    source = job_path(name).read_text(encoding="utf-8")
    decision = CONTRACTS[name].submit_cwd

    if decision == "required":
        assert 'cd "$SLURM_SUBMIT_DIR"' in source
        assert 'cd "${SLURM_SUBMIT_DIR:-$PWD}"' not in source
    elif decision == "fallback":
        assert 'cd "${SLURM_SUBMIT_DIR:-$PWD}"' in source
    else:
        assert "SLURM_SUBMIT_DIR" not in source


@pytest.mark.parametrize("name", sorted(NO_EXPLICIT_MODE_JOBS))
def test_legacy_and_utility_jobs_have_no_execute_mode(name: str) -> None:
    source = job_path(name).read_text(encoding="utf-8")

    assert "EXECUTE" not in source
    assert CONTRACTS[name].invalid_mode == "not_applicable"


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_default_is_mocked_dry_run_with_exact_contract(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(prepared)

    assert read_lines(prepared.module_log) == CONTRACTS[name].module_calls
    assert all(not output.exists() for output in prepared.outputs)
    for output_directory in prepared.output_directories:
        if name in {
            "step_02_sort_index_bam.slurm",
            "step_02b_bam_qc.slurm",
        }:
            assert output_directory.is_dir()
        else:
            assert not output_directory.exists()
    if name in EMPTY_ARRAY_DRY_RUN_DEFECTS and local_bash_major() < 4:
        assert result.returncode != 0
        assert "execute_args[@]: unbound variable" in result.stderr
        assert not prepared.delegate_log.exists()
        return

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args
    assert prepared.delegate_cwd_log.read_text(encoding="utf-8").strip() == str(
        prepared.submit
    )


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_execute_forwards_exact_args_and_checks_applicable_outputs(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + ("--execute",)
    assert all(output.is_file() and output.stat().st_size > 0 for output in prepared.outputs)


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_invalid_mode_fails_before_modules_or_child(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(prepared, execute="unsafe")

    assert result.returncode != 0
    assert "EXECUTE must be 0 or 1" in result.stderr
    assert not prepared.delegate_log.exists()
    assert not prepared.module_log.exists()


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_child_exit_is_propagated(name: str, tmp_path: Path) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_CHILD_EXIT": "37"},
    )

    assert result.returncode == 37, result.stdout + result.stderr


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_output_validation_decision_is_observable(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    if CONTRACTS[name].output_validation == "wrapper_files":
        assert result.returncode != 0
        assert "Expected" in result.stderr
    else:
        assert CONTRACTS[name].output_validation == "delegate_only"
        assert result.returncode == 0, result.stdout + result.stderr


def test_step_02b_bam_qc_stale_named_outputs_mask_missing_child_outputs(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_02b_bam_qc.slurm", tmp_path)
    stale_bytes = (
        b"stale quickcheck evidence\n",
        b"stale flagstat evidence\n",
    )
    for output, content in zip(prepared.outputs, stale_bytes, strict=True):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(content)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + ("--execute",)
    assert tuple(output.read_bytes() for output in prepared.outputs) == stale_bytes
    assert "Validated Step 02b QC outputs:" in result.stdout


def test_step_03_prefers_repository_venv_and_sources_activation(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )
    prepared.environment.pop("INFER_EXPERIMENT_BIN")
    venv_bin = prepared.submit / ".venv" / "bin"
    write_executable(venv_bin / "infer_experiment.py", "#!/bin/bash\nexit 0\n")
    activation_log = tmp_path / "activation.log"
    (venv_bin / "activate").write_text(
        'printf \'activated\\n\' > "${FAKE_ACTIVATION_LOG:?}"\n',
        encoding="utf-8",
    )
    prepared.environment["FAKE_ACTIVATION_LOG"] = str(activation_log)

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert activation_log.read_text(encoding="utf-8") == "activated\n"
    assert read_nul_args(prepared.delegate_log) == (
        prepared.expected_args[:-1]
        + (".venv/bin/infer_experiment.py", "--execute")
    )
    assert all(output.is_file() and output.stat().st_size > 0 for output in prepared.outputs)


def test_step_03_without_repository_venv_delegates_path_command(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )
    prepared.environment.pop("INFER_EXPERIMENT_BIN")

    result = run_prepared(prepared, execute="1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_nul_args(prepared.delegate_log) == (
        prepared.expected_args[:-1] + ("infer_experiment.py", "--execute")
    )


def test_step_03_dry_run_creates_logs_but_no_scientific_output(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )

    result = run_prepared(prepared)

    assert (prepared.submit / "logs").is_dir()
    assert all(not output.exists() for output in prepared.outputs)
    assert all(not directory.exists() for directory in prepared.output_directories)
    if local_bash_major() < 4:
        assert result.returncode != 0
        assert "execute_args[@]: unbound variable" in result.stderr
        assert not prepared.delegate_log.exists()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert read_nul_args(prepared.delegate_log) == prepared.expected_args


def test_step_03_stale_named_report_masks_missing_child_output(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(
        "step_03_infer_strandedness_and_orientation.slurm",
        tmp_path,
    )
    stale_bytes = b"stale paired-orientation evidence\n"
    prepared.outputs[0].parent.mkdir(parents=True, exist_ok=True)
    prepared.outputs[0].write_bytes(stale_bytes)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_SKIP_OUTPUTS": "1"},
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert read_nul_args(prepared.delegate_log) == prepared.expected_args + ("--execute",)
    assert prepared.outputs[0].read_bytes() == stale_bytes
    assert "Validated Step 03 strandedness output:" in result.stdout


@pytest.mark.parametrize("name", sorted(DELEGATED_JOBS))
def test_delegated_module_failure_policy_is_observable(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(
        prepared,
        execute="1",
        environment_updates={"FAKE_MODULE_EXIT": "23"},
    )

    if CONTRACTS[name].module_policy == "tolerated":
        assert result.returncode == 0, result.stdout + result.stderr
        assert prepared.delegate_log.exists()
    else:
        assert CONTRACTS[name].module_policy == "strict_loads_tolerated_lists"
        assert result.returncode == 23
        assert not prepared.delegate_log.exists()


@pytest.mark.parametrize(
    "name",
    ("step_01_star_align.slurm", "step_02_sort_index_bam.slurm"),
)
def test_caller_cwd_wrappers_do_not_honor_submit_directory(
    name: str,
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated(name, tmp_path)

    result = run_prepared(prepared, execute="1", cwd=prepared.launch)

    assert result.returncode != 0
    assert not prepared.delegate_log.exists()


def test_step01_default_fixture_mode_creates_its_current_dry_run_placeholders(
    tmp_path: Path,
) -> None:
    prepared = prepare_delegated("step_01_star_align.slurm", tmp_path)
    for key in ("SAMPLE_ID", "R1_FASTQ", "R2_FASTQ", "STAR_INDEX", "OUTPUT_DIR"):
        prepared.environment.pop(key)

    result = run_prepared(prepared)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (prepared.submit / "data/test/sample_001_R1.fastq.gz").is_file()
    assert (prepared.submit / "data/test/sample_001_R2.fastq.gz").is_file()
    assert (prepared.submit / "refs/test_star_index").is_dir()
    assert read_nul_args(prepared.delegate_log) == (
        "--sample-id",
        "sample_001",
        "--r1-fastq",
        "data/test/sample_001_R1.fastq.gz",
        "--r2-fastq",
        "data/test/sample_001_R2.fastq.gz",
        "--star-index",
        "refs/test_star_index",
        "--output-dir",
        "results/test/sample_001/star",
        "--threads",
        "3",
    )


def prepare_legacy_environment(tmp_path: Path) -> tuple[Path, Path, dict[str, str]]:
    submit = tmp_path / "submit"
    launch = tmp_path / "alternate-launch"
    fake_bin = tmp_path / "fake-bin"
    submit.mkdir()
    launch.mkdir()
    fake_bin.mkdir()
    install_module_fake(fake_bin)
    install_tool_fakes(fake_bin)
    return submit, launch, base_environment(tmp_path, fake_bin)


UTILITY_JOBS = (
    "template.slurm",
    "tool_check.slurm",
    "validate_manifest.slurm",
)
UTILITY_TOOL_CALLS = {
    "template.slurm": (
        "python\t--version",
        "STAR\t--version",
        "samtools\t--version",
        "java\t-version",
    ),
    "tool_check.slurm": (
        "python\t--version",
        "STAR\t--version",
        "samtools\t--version",
        "java\t-version",
        "java\t-jar\t{picard}\tMarkDuplicates\t--version",
    ),
    "validate_manifest.slurm": (
        "python\t--version",
        "python\tscripts/validate_manifest.py\t--manifest\tsamples.example.tsv\t--base-dir\t.",
    ),
}


@pytest.mark.parametrize("name", UTILITY_JOBS)
def test_utility_job_mocked_probe_arguments_modules_and_exit(
    name: str,
    tmp_path: Path,
) -> None:
    submit, _, environment = prepare_legacy_environment(tmp_path)
    touch(submit / "samples.example.tsv")
    picard = Path(environment["PICARD"])

    result = subprocess.run(
        ["/bin/bash", str(job_path(name))],
        cwd=submit,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_lines(Path(environment["FAKE_MODULE_LOG"])) == CONTRACTS[name].module_calls
    expected_calls = tuple(
        call.format(picard=picard) for call in UTILITY_TOOL_CALLS[name]
    )
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == expected_calls

    child_environment = environment.copy()
    child_environment["FAKE_FAIL_TOOL"] = "python"
    child_failed = subprocess.run(
        ["/bin/bash", str(job_path(name))],
        cwd=submit,
        env=child_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert child_failed.returncode == 37

    module_environment = environment.copy()
    module_environment["FAKE_MODULE_EXIT"] = "23"
    module_failed = subprocess.run(
        ["/bin/bash", str(job_path(name))],
        cwd=submit,
        env=module_environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert module_failed.returncode == 23


def test_tool_check_tolerates_only_its_optional_picard_version_probe(
    tmp_path: Path,
) -> None:
    submit, _, environment = prepare_legacy_environment(tmp_path)
    environment["FAKE_FAIL_JAVA_JAR"] = "1"

    result = subprocess.run(
        ["/bin/bash", str(job_path("tool_check.slurm"))],
        cwd=submit,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
