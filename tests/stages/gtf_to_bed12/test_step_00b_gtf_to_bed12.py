"""Owner-local characterization of the Step 00b scheduler entry point."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
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
    bed: Path


@dataclass(frozen=True, slots=True)
class ExecutionCase:
    name: str
    failed_tool: str
    bad_bed: bool
    empty_bed: bool
    expected_exit: int
    expected_bed: bytes | None
    stdout_fragments: tuple[str, ...] = ()
    stderr_fragments: tuple[str, ...] = ()


EXECUTION_CASES = (
    ExecutionCase(
        name="success",
        failed_tool="",
        bad_bed=False,
        empty_bed=False,
        expected_exit=0,
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
        empty_bed=False,
        expected_exit=37,
        expected_bed=None,
    ),
    ExecutionCase(
        name="bad_field",
        failed_tool="",
        bad_bed=True,
        empty_bed=False,
        expected_exit=1,
        expected_bed=b"not-bed12\n",
        stderr_fragments=("ERROR: bad BED12 field count at line 1",),
    ),
    ExecutionCase(
        name="empty_output",
        failed_tool="",
        bad_bed=False,
        empty_bed=True,
        expected_exit=1,
        expected_bed=b"",
        stderr_fragments=("ERROR: BED12 output is empty",),
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
run_token=''
execute=0
while (($#)); do
    if [[ "$1" == "--bed" ]]; then
        bed="$2"
        shift 2
    elif [[ "$1" == "--run-token" ]]; then
        run_token="$2"
        shift 2
    elif [[ "$1" == "--execute" ]]; then
        execute=1
        shift
    else
        shift
    fi
done
[[ "$execute" == "1" ]] || exit 78
[[ -n "$run_token" ]] || exit 79
mkdir -p "$(dirname "$bed")"
if [[ "${FAKE_BAD_BED:-0}" == "1" ]]; then
    printf 'not-bed12\n' > "$bed"
elif [[ "${FAKE_EMPTY_BED:-0}" == "1" ]]; then
    : > "$bed"
else
    printf 'chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n' > "$bed"
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

    helper_source = REPO_ROOT / "src" / "norad" / "libraries" / "argument_parsing.sh"
    helper_target = submit / "src" / "norad" / "libraries" / "argument_parsing.sh"
    helper_target.parent.mkdir(parents=True, exist_ok=True)
    helper_target.write_bytes(helper_source.read_bytes())

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
            "FAKE_EMPTY_BED": "0",
            "SLURM_SUBMIT_DIR": str(submit),
            "GTF": str(gtf),
            "BED": str(bed),
            "PYTHON_BIN": str(fake_bin / "python-step00b"),
        }
    )
    return JobContext(
        submit=submit,
        launch=launch,
        environment=environment,
        gtf=gtf,
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


def expected_producer_call(job: JobContext, token: str) -> str:
    return (
        f"python-step00b\t{PRODUCER_ARGUMENTS}\t"
        f"--gtf\t{job.gtf}\t--bed\t{job.bed}\t"
        f"--run-token\t{token}\t--execute"
    )


def test_scheduler_runs_from_slurm_spool_copy(tmp_path: Path) -> None:
    job = prepare_job(tmp_path)

    # sbatch executes a copied script from SLURM's spool directory rather than
    # the original repository path.
    spool_dir = tmp_path / "slurm-spool"
    spool_dir.mkdir()
    spool_script = spool_dir / "slurm_script"
    spool_script.write_bytes(JOB_PATH.read_bytes())

    result = subprocess.run(
        ["/bin/bash", str(spool_script)],
        cwd=job.launch,
        env=job.environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == (
        expected_producer_call(job, "local-wrapper-test"),
    )
    assert_file_bytes(job.bed, VALID_BED_BYTES)
    assert list(job.launch.iterdir()) == []


def configure_preflight_failure(job: JobContext, scenario: str) -> str:
    if scenario == "missing_submit":
        job.environment.pop("SLURM_SUBMIT_DIR")
        return "SLURM_SUBMIT_DIR is required"
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
    if scenario == "unsafe_run_token":
        job.environment["NORAD_RUN_TOKEN"] = "unsafe/token"
        return "ERROR: Unsafe Step 00b publication token: unsafe/token\n"
    raise AssertionError(f"Unknown preflight scenario: {scenario}")


def assert_file_bytes(path: Path, expected: bytes | None) -> None:
    if expected is None:
        assert not path.exists()
    else:
        assert path.read_bytes() == expected


@pytest.mark.parametrize(
    "scenario",
    ("missing_submit", "missing_gtf", "nonexecutable_python", "unsafe_run_token"),
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
    assert not job.bed.parent.exists()
    assert read_lines(Path(job.environment["FAKE_MODULE_LOG"])) == ()
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == ()
    assert list(job.launch.iterdir()) == []


def test_module_listing_failure_is_tolerated(tmp_path: Path) -> None:
    job = prepare_job(tmp_path)
    job.environment["FAKE_MODULE_EXIT"] = "23"

    result = run_job(job)

    assert JOB_PATH.stat().st_mode & stat.S_IXUSR
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert (job.submit / "logs").is_dir()
    assert job.bed.parent.is_dir()
    assert f"  Working dir: {job.submit}" in result.stdout
    assert read_lines(Path(job.environment["FAKE_MODULE_LOG"])) == ("list",)
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == (
        expected_producer_call(job, "local-wrapper-test"),
    )
    assert_file_bytes(job.bed, VALID_BED_BYTES)
    assert list(job.launch.iterdir()) == []


def test_explicit_run_token_takes_precedence_over_slurm_job_id(
    tmp_path: Path,
) -> None:
    job = prepare_job(tmp_path)
    job.environment["NORAD_RUN_TOKEN"] = "explicit-owner-token"

    result = run_job(job)

    assert result.returncode == 0, result.stdout + result.stderr
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == (
        expected_producer_call(job, "explicit-owner-token"),
    )
    assert "  Run token:   explicit-owner-token" in result.stdout
    assert_file_bytes(job.bed, VALID_BED_BYTES)


def test_direct_execution_uses_safe_process_id_token_fallback(
    tmp_path: Path,
) -> None:
    job = prepare_job(tmp_path)
    job.environment.pop("NORAD_RUN_TOKEN", None)
    job.environment.pop("SLURM_JOB_ID")

    result = run_job(job)

    assert result.returncode == 0, result.stdout + result.stderr
    calls = read_lines(Path(job.environment["FAKE_TOOL_LOG"]))
    assert len(calls) == 1
    arguments = calls[0].split("\t")
    run_token = arguments[arguments.index("--run-token") + 1]
    assert run_token.isdecimal()
    assert int(run_token) > 0
    assert calls == (expected_producer_call(job, run_token),)
    assert "  Job ID:      unknown" in result.stdout
    assert f"  Run token:   {run_token}" in result.stdout
    assert_file_bytes(job.bed, VALID_BED_BYTES)


@pytest.mark.parametrize("case", EXECUTION_CASES, ids=lambda case: case.name)
def test_scheduler_execution_outcomes(
    tmp_path: Path,
    case: ExecutionCase,
) -> None:
    job = prepare_job(tmp_path)
    job.environment["FAKE_FAIL_TOOL"] = case.failed_tool
    job.environment["FAKE_BAD_BED"] = str(int(case.bad_bed))
    job.environment["FAKE_EMPTY_BED"] = str(int(case.empty_bed))

    result = run_job(job)

    assert JOB_PATH.stat().st_mode & stat.S_IXUSR
    assert result.returncode == case.expected_exit, result.stdout + result.stderr
    if case.stderr_fragments:
        for fragment in case.stderr_fragments:
            assert fragment in result.stderr
    else:
        assert result.stderr == ""
    assert (job.submit / "logs").is_dir()
    assert job.bed.parent.is_dir()
    assert f"  Working dir: {job.submit}" in result.stdout
    assert read_lines(Path(job.environment["FAKE_MODULE_LOG"])) == ("list",)
    assert read_lines(Path(job.environment["FAKE_TOOL_LOG"])) == (
        expected_producer_call(job, "local-wrapper-test"),
    )
    assert_file_bytes(job.bed, case.expected_bed)
    for fragment in case.stdout_fragments:
        assert fragment in result.stdout
    if case.expected_exit:
        assert "Finished GTF to BED12 reference prep." not in result.stdout
    assert list(job.launch.iterdir()) == []


def test_scheduler_preserves_transactional_no_clobber(tmp_path: Path) -> None:
    job = prepare_job(tmp_path)
    job.gtf.write_text(
        'chr1\tsource\texon\t1\t4\t.\t+\t.\tgene_id "g1"; transcript_id "tx1";\n',
        encoding="utf-8",
    )
    job.environment["PYTHON_BIN"] = sys.executable

    first = run_job(job)

    assert first.returncode == 0, first.stdout + first.stderr
    assert_file_bytes(job.bed, VALID_BED_BYTES)
    published = job.bed.read_bytes()
    lock = job.bed.parent / f".{job.bed.name}.step00b.lock"
    staging = tuple(job.bed.parent.glob(f".{job.bed.name}.step00b.*.tmp"))
    assert not lock.exists()
    assert staging == ()

    second = run_job(job)

    assert second.returncode == 1, second.stdout + second.stderr
    assert "BED12 output already exists; refusing to replace" in second.stderr
    assert job.bed.read_bytes() == published
    assert not lock.exists()
    assert tuple(job.bed.parent.glob(f".{job.bed.name}.step00b.*.tmp")) == ()
