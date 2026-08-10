"""Owner-local characterization of the Step 00b scheduler entry point."""

from __future__ import annotations

import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
JOB_PATH = (
    REPO_ROOT
    / "src"
    / "norad"
    / "stages"
    / "gtf_to_bed12"
    / "step_00b_gtf_to_bed12.slurm"
)
PRODUCER_ARGUMENTS = "-I\t-m\tnorad\tconvert\tgtf-to-bed12"
VALID_BED = "chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n"
VALID_BED_BYTES = VALID_BED.encode()


@dataclass(slots=True)
class JobContext:
    submit: Path
    launch: Path
    environment: dict[str, str]
    gtf: Path
    unsorted_bed: Path
    bed: Path


@dataclass(frozen=True, slots=True)
class ExecutionCase:
    name: str
    failed_tool: str
    bad_bed: bool
    expected_exit: int
    bedtools_called: bool
    expected_unsorted: bytes | None
    expected_bed: bytes | None
    stdout_fragments: tuple[str, ...] = ()


EXECUTION_CASES = (
    ExecutionCase(
        name="success",
        failed_tool="",
        bad_bed=False,
        expected_exit=0,
        bedtools_called=True,
        expected_unsorted=VALID_BED_BYTES,
        expected_bed=VALID_BED_BYTES,
        stdout_fragments=(
            "BED12 field-count check passed",
            "Finished GTF to BED12 reference prep.",
        ),
    ),
    ExecutionCase(
        name="converter_failure",
        failed_tool="python-step00b",
        bad_bed=False,
        expected_exit=37,
        bedtools_called=False,
        expected_unsorted=None,
        expected_bed=None,
    ),
    ExecutionCase(
        name="bedtools_failure",
        failed_tool="bedtools",
        bad_bed=False,
        expected_exit=37,
        bedtools_called=True,
        expected_unsorted=VALID_BED_BYTES,
        expected_bed=b"",
    ),
    ExecutionCase(
        name="bad_field",
        failed_tool="",
        bad_bed=True,
        expected_exit=1,
        bedtools_called=True,
        expected_unsorted=VALID_BED_BYTES,
        expected_bed=b"not-bed12\n",
        stdout_fragments=(
            "ERROR: bad BED12 field count at line 1",
            "BED12 field-count check passed",
        ),
    ),
)


def write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def read_lines(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(path.read_text(encoding="utf-8").splitlines())


def install_fakes(fake_bin: Path) -> None:
    write_executable(
        fake_bin / "module",
        """#!/bin/bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_MODULE_LOG:?}"
exit "${FAKE_MODULE_EXIT:-0}"
""",
    )
    write_executable(
        fake_bin / "python-step00b",
        """#!/bin/bash
set -euo pipefail
{
    printf 'python-step00b'
    printf '\t%s' "$@"
    printf '\n'
} >> "${FAKE_TOOL_LOG:?}"
[[ "${FAKE_FAIL_TOOL:-}" == "python-step00b" ]] && exit "${FAKE_TOOL_EXIT:-37}"
bed=''
while (($#)); do
    if [[ "$1" == "--bed" ]]; then
        bed="$2"
        shift 2
    else
        shift
    fi
done
mkdir -p "$(dirname "$bed")"
printf 'chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n' > "$bed"
""",
    )
    write_executable(
        fake_bin / "bedtools",
        """#!/bin/bash
set -euo pipefail
{
    printf 'bedtools'
    printf '\t%s' "$@"
    printf '\n'
} >> "${FAKE_TOOL_LOG:?}"
[[ "${FAKE_FAIL_TOOL:-}" == "bedtools" ]] && exit "${FAKE_TOOL_EXIT:-37}"
input=''
while (($#)); do
    if [[ "$1" == "-i" ]]; then
        input="$2"
        shift 2
    else
        shift
    fi
done
if [[ "${FAKE_BAD_BED:-0}" == "1" ]]; then
    printf 'not-bed12\n'
else
    cat "$input"
fi
""",
    )


def prepare_job(tmp_path: Path) -> JobContext:
    submit = tmp_path / "submit"
    launch = tmp_path / "alternate-launch"
    fake_bin = tmp_path / "fake-bin"
    runtime_tmp = tmp_path / "runtime-tmp"
    for path in (submit, launch, fake_bin, runtime_tmp):
        path.mkdir()
    install_fakes(fake_bin)
    gtf = submit / "inputs" / "genes.gtf"
    gtf.parent.mkdir()
    gtf.write_text("fixture\n", encoding="utf-8")
    unsorted_bed = submit / "outputs" / "genes.unsorted.bed"
    bed = submit / "outputs" / "genes.bed"
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": os.pathsep.join((str(fake_bin), "/usr/bin", "/bin")),
            "TMPDIR": str(runtime_tmp),
            "SLURM_JOB_ID": "local-wrapper-test",
            "SLURM_JOB_NAME": "local-wrapper-test",
            "SLURMD_NODENAME": "local-mock-node",
            "FAKE_MODULE_LOG": str(tmp_path / "module.log"),
            "FAKE_MODULE_EXIT": "0",
            "FAKE_TOOL_LOG": str(tmp_path / "tool.log"),
            "FAKE_TOOL_EXIT": "37",
            "FAKE_FAIL_TOOL": "",
            "FAKE_BAD_BED": "0",
            "SLURM_SUBMIT_DIR": str(submit),
            "GTF": str(gtf),
            "UNSORTED_BED": str(unsorted_bed),
            "BED": str(bed),
            "PYTHON_BIN": str(fake_bin / "python-step00b"),
        }
    )
    return JobContext(
        submit=submit,
        launch=launch,
        environment=environment,
        gtf=gtf,
        unsorted_bed=unsorted_bed,
        bed=bed,
    )


def run_job(job: JobContext) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(JOB_PATH)],
        cwd=job.launch,
        env=job.environment,
        text=True,
        capture_output=True,
        check=False,
    )


def configure_preflight_failure(job: JobContext, scenario: str) -> str:
    if scenario == "missing_submit":
        job.environment.pop("SLURM_SUBMIT_DIR")
        return "SLURM_SUBMIT_DIR: unbound variable"
    if scenario == "colliding_outputs":
        job.environment["BED"] = str(job.unsorted_bed)
        return "ERROR: UNSORTED_BED and BED must be different paths.\n"
    if scenario == "missing_gtf":
        missing_gtf = job.submit / "inputs" / "missing.gtf"
        job.environment["GTF"] = str(missing_gtf)
        return f"ERROR: GTF not found: {missing_gtf}\n"
    if scenario == "nonexecutable_python":
        nonexecutable = job.submit.parent / "python-nonexecutable"
        nonexecutable.write_text("#!/bin/bash\n", encoding="utf-8")
        nonexecutable.chmod(0o644)
        job.environment["PYTHON_BIN"] = str(nonexecutable)
        return (
            f"ERROR: Python executable not found or not executable: {nonexecutable}\n"
        )
    raise AssertionError(f"Unknown preflight scenario: {scenario}")


def assert_file_bytes(path: Path, expected: bytes | None) -> None:
    if expected is None:
        assert not path.exists()
    else:
        assert path.read_bytes() == expected


@pytest.mark.parametrize(
    "scenario",
    ("missing_submit", "colliding_outputs", "missing_gtf", "nonexecutable_python"),
)
def test_scheduler_preflight_failures_are_side_effect_free(
    tmp_path: Path,
    scenario: str,
) -> None:
    job = prepare_job(tmp_path)
    expected_error = configure_preflight_failure(job, scenario)

    result = run_job(job)

    assert JOB_PATH.stat().st_mode & stat.S_IXUSR
    assert result.returncode == 1, result.stdout + result.stderr
    if scenario == "missing_submit":
        assert expected_error in result.stderr
    else:
        assert result.stderr == expected_error
    assert not (job.submit / "logs").exists()
    assert not job.unsorted_bed.parent.exists()
    assert read_lines(Path(job.environment["FAKE_MODULE_LOG"])) == ()
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == ()
    assert list(job.launch.iterdir()) == []


def test_module_failure_stops_before_conversion(tmp_path: Path) -> None:
    job = prepare_job(tmp_path)
    job.environment["FAKE_MODULE_EXIT"] = "23"

    result = run_job(job)

    assert JOB_PATH.stat().st_mode & stat.S_IXUSR
    assert result.returncode == 23, result.stdout + result.stderr
    assert result.stderr == ""
    assert (job.submit / "logs").is_dir()
    assert job.unsorted_bed.parent.is_dir()
    assert f"  Working dir:     {job.submit}" in result.stdout
    assert read_lines(Path(job.environment["FAKE_MODULE_LOG"])) == (
        "list",
        "load bedtools/2.31.1",
    )
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == ()
    assert not job.unsorted_bed.exists()
    assert not job.bed.exists()
    assert list(job.launch.iterdir()) == []


@pytest.mark.parametrize("case", EXECUTION_CASES, ids=lambda case: case.name)
def test_scheduler_execution_outcomes(
    tmp_path: Path,
    case: ExecutionCase,
) -> None:
    job = prepare_job(tmp_path)
    job.environment["FAKE_FAIL_TOOL"] = case.failed_tool
    job.environment["FAKE_BAD_BED"] = str(int(case.bad_bed))

    result = run_job(job)

    assert JOB_PATH.stat().st_mode & stat.S_IXUSR
    assert result.returncode == case.expected_exit, result.stdout + result.stderr
    assert result.stderr == ""
    assert (job.submit / "logs").is_dir()
    assert job.unsorted_bed.parent.is_dir()
    assert f"  Working dir:     {job.submit}" in result.stdout
    assert read_lines(Path(job.environment["FAKE_MODULE_LOG"])) == (
        "list",
        "load bedtools/2.31.1",
        "list",
    )

    producer_call = (
        f"python-step00b\t{PRODUCER_ARGUMENTS}\t"
        f"--gtf\t{job.gtf}\t--bed\t{job.unsorted_bed}"
    )
    bedtools_calls = (
        (f"bedtools\tsort\t-i\t{job.unsorted_bed}",) if case.bedtools_called else ()
    )
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == (
        producer_call,
        *bedtools_calls,
    )
    assert_file_bytes(job.unsorted_bed, case.expected_unsorted)
    assert_file_bytes(job.bed, case.expected_bed)
    for fragment in case.stdout_fragments:
        assert fragment in result.stdout
    assert list(job.launch.iterdir()) == []
