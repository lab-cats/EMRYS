import gzip
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "jobs"
DATA_CHECKS = ROOT / "tests" / "data_checks"
UTILITY_JOBS = (
    "template.slurm",
    "tool_check.slurm",
    "validate_manifest.slurm",
)


def write_executable(path: Path, body: str) -> Path:
    path.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body)
    path.chmod(0o755)
    return path


def make_fake_tool_bin(tmp_path: Path) -> Path:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    write_executable(
        fake_bin / "module",
        'printf "module %s\\n" "$*"\n',
    )
    write_executable(fake_bin / "python", 'printf "Python 3.fixture\\n"\n')
    write_executable(fake_bin / "STAR", 'printf "STAR_2.fixture\\n"\n')
    write_executable(
        fake_bin / "samtools",
        'printf "samtools fixture\\nsecond line\\n"\n',
    )
    write_executable(
        fake_bin / "java",
        """
if [[ "${1:-}" == "-version" ]]; then
    printf 'openjdk version "17.fixture"\\n' >&2
else
    printf 'MarkDuplicates fixture\\n'
fi
""",
    )
    return fake_bin


def run_job(
    job_name: str,
    tmp_path: Path,
    *,
    fake_bin: Path,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}:{env['PATH']}",
            "PICARD": str(tmp_path / "picard.jar"),
            "SLURM_JOB_ID": "12345",
            "SLURM_JOB_NAME": f"fixture-{job_name}",
            "TMPDIR": str(tmp_path),
        }
    )
    return subprocess.run(
        ["bash", str(JOBS / job_name)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("job_name", UTILITY_JOBS)
def test_utility_jobs_keep_shell_log_and_context_contracts(job_name: str) -> None:
    text = (JOBS / job_name).read_text()

    assert text.startswith(("#!/bin/bash\n", "#!/usr/bin/env bash\n"))
    assert "set -euo pipefail" in text
    assert "#SBATCH --output=logs/%x-%j.out" in text
    assert "#SBATCH --error=logs/%x-%j.err" in text
    assert "module list 2>&1 || true" in text
    for label in (
        "Job ID:",
        "Job name:",
        "Node:",
        "Started:",
        "Working directory:",
        "TMPDIR:",
    ):
        assert label in text


def test_validate_manifest_job_delegates_to_the_example_contract() -> None:
    text = (JOBS / "validate_manifest.slurm").read_text()

    assert "python scripts/validate_manifest.py" in text
    assert "--manifest samples.example.tsv" in text
    assert "--base-dir ." in text
    assert "--check-files" not in text


def test_validate_manifest_job_executes_with_a_mocked_module_command(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    write_executable(fake_bin / "module", 'printf "module %s\\n" "$*"\n')
    (fake_bin / "python").symlink_to(sys.executable)

    result = run_job("validate_manifest.slurm", tmp_path, fake_bin=fake_bin)

    assert result.returncode == 0, result.stderr
    assert "module load python39" in result.stdout
    assert "Manifest validation passed." in result.stdout
    assert "Samples: 2" in result.stdout
    assert "Finished:" in result.stdout


@pytest.mark.parametrize("job_name", ("template.slurm", "tool_check.slurm"))
def test_tool_inspection_jobs_run_with_tiny_mocked_tools(
    job_name: str,
    tmp_path: Path,
) -> None:
    fake_bin = make_fake_tool_bin(tmp_path)

    result = run_job(job_name, tmp_path, fake_bin=fake_bin)

    assert result.returncode == 0, result.stderr
    assert "Job ID: 12345" in result.stdout
    assert f"Job name: fixture-{job_name}" in result.stdout
    assert "module load star/2.7.11b" in result.stdout
    assert "Python 3.fixture" in result.stdout
    assert "STAR_2.fixture" in result.stdout
    assert "samtools fixture" in result.stdout
    assert "Finished:" in result.stdout


def write_fastq(
    path: Path,
    read_ids: list[str],
    mate: int,
    *,
    compressed: bool = False,
) -> Path:
    content = "".join(
        f"@{read_id}/{mate}\nACGT\n+\n!!!!\n" for read_id in read_ids
    )
    if compressed:
        with gzip.open(path, "wt") as handle:
            handle.write(content)
    else:
        path.write_text(content)
    return path


def run_fastq_check(
    tmp_path: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(DATA_CHECKS / "check_fastq_pairs.sh"), *args],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )


def test_fastq_pair_check_accepts_matching_plain_files(tmp_path: Path) -> None:
    r1 = write_fastq(tmp_path / "r1.fastq", ["read-1", "read-2"], 1)
    r2 = write_fastq(tmp_path / "r2.fastq", ["read-1", "read-2"], 2)

    result = run_fastq_check(
        tmp_path,
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--sample-id",
        "sample_fixture",
        "--num-reads",
        "2",
    )

    assert result.returncode == 0, result.stderr
    assert "Sample ID: sample_fixture" in result.stdout
    assert "R1 total reads: 2" in result.stdout
    assert "R2 total reads: 2" in result.stdout
    assert "PASS: FASTQ pair check succeeded for 2 read IDs" in result.stdout


def test_fastq_pair_check_accepts_matching_gzip_files(tmp_path: Path) -> None:
    r1 = write_fastq(
        tmp_path / "r1.fastq.gz",
        ["read-1", "read-2"],
        1,
        compressed=True,
    )
    r2 = write_fastq(
        tmp_path / "r2.fastq.gz",
        ["read-1", "read-2"],
        2,
        compressed=True,
    )

    result = run_fastq_check(
        tmp_path,
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--num-reads",
        "2",
    )

    assert result.returncode == 0, result.stderr
    assert "PASS: FASTQ pair check succeeded" in result.stdout


def test_fastq_pair_check_rejects_mismatched_read_ids(tmp_path: Path) -> None:
    r1 = write_fastq(tmp_path / "r1.fastq", ["read-1", "read-2"], 1)
    r2 = write_fastq(tmp_path / "r2.fastq", ["read-1", "other"], 2)

    result = run_fastq_check(
        tmp_path,
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--num-reads",
        "2",
    )

    assert result.returncode == 1
    assert "FAIL: FASTQ read IDs mismatch" in result.stderr
    assert "Record number: 2" in result.stderr


def test_fastq_pair_check_rejects_count_and_shape_mismatches(
    tmp_path: Path,
) -> None:
    r1 = write_fastq(tmp_path / "r1.fastq", ["read-1", "read-2"], 1)
    r2 = write_fastq(tmp_path / "r2.fastq", ["read-1"], 2)

    count_result = run_fastq_check(
        tmp_path,
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--num-reads",
        "1",
    )
    assert count_result.returncode == 1
    assert "FASTQ read counts differ: R1=2 R2=1" in count_result.stderr

    malformed = tmp_path / "malformed.fastq"
    malformed.write_text("@read-1/2\nACGT\n+\n")
    shape_result = run_fastq_check(
        tmp_path,
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(malformed),
        "--num-reads",
        "1",
    )
    assert shape_result.returncode == 1
    assert "R2 FASTQ line count is not divisible by 4: 3" in shape_result.stderr


@pytest.mark.parametrize("num_reads", ("0", "-1", "not-a-number"))
def test_fastq_pair_check_rejects_invalid_num_reads(
    tmp_path: Path,
    num_reads: str,
) -> None:
    r1 = write_fastq(tmp_path / "r1.fastq", ["read-1"], 1)
    r2 = write_fastq(tmp_path / "r2.fastq", ["read-1"], 2)

    result = run_fastq_check(
        tmp_path,
        "--r1-fastq",
        str(r1),
        "--r2-fastq",
        str(r2),
        "--num-reads",
        num_reads,
    )

    assert result.returncode == 1
    assert "--num-reads must be a positive integer" in result.stderr


def make_fake_samtools(tmp_path: Path) -> Path:
    return write_executable(
        tmp_path / "samtools",
        """
case "${1:-}" in
    quickcheck)
        [[ "${FAKE_QUICKCHECK_FAIL:-0}" == "0" ]]
        ;;
    view)
        if [[ "${2:-}" == "-H" ]]; then
            printf '@HD\\tVN:1.6\\tSO:coordinate\\n'
            printf '@RG\\tID:S1\\tSM:S1\\tLB:S1\\tPL:ILLUMINA\\n'
        else
            exit 2
        fi
        ;;
    *)
        exit 2
        ;;
esac
""",
    )


def run_step05_data_check(
    tmp_path: Path,
    samtools: Path,
    *args: str,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "SAMTOOLS": str(samtools),
            "OUTPUT_TSV": str(tmp_path / "results" / "qc" / "step05.tsv"),
        }
    )
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(DATA_CHECKS / "validate_step05_outputs.sh"), *args],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )


def create_step05_pair(tmp_path: Path) -> None:
    output_dir = tmp_path / "results" / "split_ncigar" / "S1"
    output_dir.mkdir(parents=True)
    (output_dir / "S1.split_ncigar.bam").write_bytes(b"BAM fixture\n")
    (output_dir / "S1.split_ncigar.bam.bai").write_bytes(b"BAI fixture\n")


def test_step05_data_check_writes_one_stable_pass_row(tmp_path: Path) -> None:
    samtools = make_fake_samtools(tmp_path)
    create_step05_pair(tmp_path)

    result = run_step05_data_check(tmp_path, samtools, "S1")

    assert result.returncode == 0, result.stderr
    report = tmp_path / "results" / "qc" / "step05.tsv"
    lines = [line for line in report.read_text().splitlines() if line]
    assert len(lines) == 2
    assert lines[0].startswith("sample_id\tjob_id\tjob_state")
    assert lines[1].startswith("S1\tNA\tNA\t")
    assert lines[1].endswith("\tPASS")
    assert "Summary: PASS=1 PENDING_OR_RUNNING=0 FAIL=0" in result.stderr


def test_step05_data_check_reports_validation_failure(tmp_path: Path) -> None:
    samtools = make_fake_samtools(tmp_path)
    create_step05_pair(tmp_path)

    result = run_step05_data_check(
        tmp_path,
        samtools,
        "S1",
        extra_env={"FAKE_QUICKCHECK_FAIL": "1"},
    )

    assert result.returncode == 1
    report = (tmp_path / "results" / "qc" / "step05.tsv").read_text()
    assert "\tno\tyes\tyes\t0\tFAIL\n" in report
    assert "Summary: PASS=0 PENDING_OR_RUNNING=0 FAIL=1" in result.stderr


def test_step05_data_check_reports_missing_outputs_as_pending(
    tmp_path: Path,
) -> None:
    samtools = make_fake_samtools(tmp_path)

    result = run_step05_data_check(tmp_path, samtools, "S1")

    assert result.returncode == 2
    report = (tmp_path / "results" / "qc" / "step05.tsv").read_text()
    assert "\tno\tno\t0\t0\tNA\tNA\tNA\t0\tPENDING\n" in report


def test_step05_data_check_uses_explicit_job_state(tmp_path: Path) -> None:
    samtools = make_fake_samtools(tmp_path)
    jobs = tmp_path / "jobs.tsv"
    jobs.write_text("S1 999\n")
    fake_bin = tmp_path / "scheduler-bin"
    fake_bin.mkdir()
    write_executable(fake_bin / "squeue", 'printf "RUNNING\\n"\n')
    write_executable(fake_bin / "sacct", "exit 2\n")

    result = run_step05_data_check(
        tmp_path,
        samtools,
        "--jobs",
        str(jobs),
        "S1",
        extra_env={"PATH": f"{fake_bin}:{os.environ['PATH']}"},
    )

    assert result.returncode == 2
    report = (tmp_path / "results" / "qc" / "step05.tsv").read_text()
    assert "S1\t999\tRUNNING\t" in report
    assert report.rstrip().endswith("\tRUNNING")


def test_step05_data_check_rejects_missing_job_file(tmp_path: Path) -> None:
    samtools = make_fake_samtools(tmp_path)
    missing = tmp_path / "missing-jobs.tsv"

    result = run_step05_data_check(
        tmp_path,
        samtools,
        "--jobs",
        str(missing),
        "S1",
    )

    assert result.returncode == 1
    assert f"ERROR: job file does not exist or is not a file: {missing}" in result.stderr


@pytest.mark.parametrize("option", ("--jobs", "--output"))
def test_step05_data_check_rejects_missing_option_values(
    tmp_path: Path,
    option: str,
) -> None:
    samtools = make_fake_samtools(tmp_path)

    result = run_step05_data_check(tmp_path, samtools, option)

    assert result.returncode == 1
    assert f"ERROR: {option} requires a value" in result.stderr


def test_step05_data_check_rejects_unknown_options(tmp_path: Path) -> None:
    samtools = make_fake_samtools(tmp_path)

    result = run_step05_data_check(tmp_path, samtools, "--unknown")

    assert result.returncode == 1
    assert "ERROR: unknown option: --unknown" in result.stderr


def test_step05_data_check_has_one_output_setup_path() -> None:
    text = (DATA_CHECKS / "validate_step05_outputs.sh").read_text()

    assert text.count("mkdir -p") == 1
    assert 'exec > >(tee "$OUTPUT_TSV")' not in text
    assert text.count(': > "$OUTPUT_TSV"') == 1
