"""Owner-local characterization of the Step 00b scheduler entry point."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
JOB_PATH = (
    REPO_ROOT
    / "src"
    / "norad"
    / "stages"
    / "convert_GTF_to_BED12"
    / "step_00b_gtf_to_bed12.slurm"
)
PRODUCER_ARGUMENT = "src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py"
VALID_BED = "chr1\t0\t4\ttx1|g1\t0\t+\t0\t4\t0\t1\t4,\t0,\n"


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


def prepare_job(
    tmp_path: Path,
) -> tuple[Path, Path, dict[str, str], Path, Path, Path]:
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
    return submit, launch, environment, gtf, unsorted_bed, bed


def run_job(
    launch: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(JOB_PATH)],
        cwd=launch,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("scenario", "expected_exit"),
    (
        ("success", 0),
        ("missing_submit", 1),
        ("colliding_outputs", 1),
        ("missing_gtf", 1),
        ("nonexecutable_python", 1),
        ("module_failure", 23),
        ("converter_failure", 37),
        ("bedtools_failure", 37),
        ("bad_field", 1),
    ),
)
def test_isolated_scheduler_scenarios(
    tmp_path: Path,
    scenario: str,
    expected_exit: int,
) -> None:
    submit, launch, environment, gtf, unsorted_bed, bed = prepare_job(tmp_path)
    if scenario == "missing_submit":
        environment.pop("SLURM_SUBMIT_DIR")
    elif scenario == "colliding_outputs":
        environment["BED"] = str(unsorted_bed)
        bed = unsorted_bed
    elif scenario == "missing_gtf":
        environment["GTF"] = str(submit / "inputs" / "missing.gtf")
    elif scenario == "nonexecutable_python":
        nonexecutable = tmp_path / "python-nonexecutable"
        nonexecutable.write_text("#!/bin/bash\n", encoding="utf-8")
        nonexecutable.chmod(0o644)
        environment["PYTHON_BIN"] = str(nonexecutable)
    elif scenario == "module_failure":
        environment["FAKE_MODULE_EXIT"] = "23"
    elif scenario == "converter_failure":
        environment["FAKE_FAIL_TOOL"] = "python-step00b"
    elif scenario == "bedtools_failure":
        environment["FAKE_FAIL_TOOL"] = "bedtools"
    elif scenario == "bad_field":
        environment["FAKE_BAD_BED"] = "1"

    result = run_job(launch, environment)

    assert JOB_PATH.stat().st_mode & stat.S_IXUSR
    assert result.returncode == expected_exit, result.stdout + result.stderr
    module_calls = read_lines(Path(environment["FAKE_MODULE_LOG"]))
    tool_calls = read_lines(Path(environment["FAKE_TOOL_LOG"]))
    preflight_failures = {
        "missing_submit",
        "colliding_outputs",
        "missing_gtf",
        "nonexecutable_python",
    }
    if scenario in preflight_failures:
        assert not (submit / "logs").exists()
        assert not unsorted_bed.parent.exists()
        assert module_calls == ()
        assert tool_calls == ()
    else:
        assert (submit / "logs").is_dir()
        assert unsorted_bed.parent.is_dir()
        assert f"  Working dir:     {submit}" in result.stdout

    if scenario == "missing_submit":
        assert "SLURM_SUBMIT_DIR: unbound variable" in result.stderr
    elif scenario == "colliding_outputs":
        assert result.stderr == (
            "ERROR: UNSORTED_BED and BED must be different paths.\n"
        )
    elif scenario == "missing_gtf":
        assert result.stderr == f"ERROR: GTF not found: {environment['GTF']}\n"
    elif scenario == "nonexecutable_python":
        assert result.stderr == (
            "ERROR: Python executable not found or not executable: "
            f"{environment['PYTHON_BIN']}\n"
        )
    elif scenario == "module_failure":
        assert result.stderr == ""
        assert module_calls == ("list", "load bedtools/2.31.1")
        assert tool_calls == ()
        assert not unsorted_bed.exists()
        assert not bed.exists()
    else:
        assert result.stderr == ""
        assert module_calls == ("list", "load bedtools/2.31.1", "list")
        producer_call = (
            f"python-step00b\t{PRODUCER_ARGUMENT}\t--gtf\t{gtf}"
            f"\t--bed\t{unsorted_bed}"
        )
        if scenario == "converter_failure":
            assert tool_calls == (producer_call,)
            assert not unsorted_bed.exists()
            assert not bed.exists()
        else:
            assert tool_calls == (
                producer_call,
                f"bedtools\tsort\t-i\t{unsorted_bed}",
            )
            assert unsorted_bed.read_text(encoding="utf-8") == VALID_BED

    if scenario == "bedtools_failure":
        assert bed.is_file()
        assert bed.read_bytes() == b""
    elif scenario == "bad_field":
        assert bed.read_bytes() == b"not-bed12\n"
        assert "ERROR: bad BED12 field count at line 1" in result.stdout
        assert "BED12 field-count check passed" in result.stdout
    elif scenario == "success":
        assert bed.read_text(encoding="utf-8") == VALID_BED
        assert "BED12 field-count check passed" in result.stdout
        assert "Finished GTF to BED12 reference prep." in result.stdout

    assert list(launch.iterdir()) == []
