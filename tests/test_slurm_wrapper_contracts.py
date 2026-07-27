from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "jobs"

DRY_RUN_WRAPPERS = {
    "step_00c_prepare_gatk_reference.slurm": "scripts/step_00c_prepare_gatk_reference.sh",
    "step_01_star_align.slurm": "scripts/step_01_star_align.sh",
    "step_02_sort_index_bam.slurm": "scripts/step_02_sort_index_bam.sh",
    "step_02b_bam_qc.slurm": "scripts/step_02b_bam_qc.sh",
    "step_03_infer_strandedness_and_orientation.slurm": (
        "scripts/step_03_infer_strandedness_and_orientation.sh"
    ),
    "step_04_mark_duplicates.slurm": "scripts/step_04_mark_duplicates.sh",
    "step_05_split_n_cigar_reads.slurm": "scripts/step_05_split_n_cigar_reads.sh",
    "step_06_split_bam_by_read_orientation.slurm": (
        "scripts/step_06_split_bam_by_read_orientation.sh"
    ),
    "step_07_bcftools_mpileup_by_chrom_and_strand.slurm": (
        "scripts/step_07_bcftools_mpileup_by_chrom_and_strand.sh"
    ),
    "step_08_vcf_preprocessing.slurm": "scripts/step_08_vcf_preprocessing.sh",
    "step_09_cmh_editing_site_calling.slurm": (
        "scripts/step_09_cmh_editing_site_calling.sh"
    ),
}


@pytest.mark.parametrize(
    "job",
    sorted(JOBS.glob("step_*.slurm")),
    ids=lambda path: path.name,
)
def test_step_jobs_have_strict_shell_and_stable_log_paths(job: Path) -> None:
    text = job.read_text()

    assert text.startswith(("#!/bin/bash\n", "#!/usr/bin/env bash\n"))
    assert "set -euo pipefail" in text
    assert "#SBATCH --output=logs/%x-%j.out" in text
    assert "#SBATCH --error=logs/%x-%j.err" in text


@pytest.mark.parametrize(
    ("job_name", "script_name"),
    sorted(DRY_RUN_WRAPPERS.items()),
)
def test_current_dry_run_wrappers_preserve_the_execute_gate(
    job_name: str,
    script_name: str,
) -> None:
    text = (JOBS / job_name).read_text()

    assert '${EXECUTE:-0}' in text
    assert "must be 0 or 1" in text
    assert script_name in text
    assert "--execute" in text
    assert "module list 2>&1 || true" in text


@pytest.mark.parametrize("job_name", sorted(DRY_RUN_WRAPPERS))
def test_current_dry_run_wrappers_log_required_job_context(
    job_name: str,
) -> None:
    text = (JOBS / job_name).read_text()

    for label in (
        "Job ID:",
        "Job name:",
        "Node:",
        "Started:",
        "Working directory:",
        "TMPDIR:",
    ):
        assert label in text
