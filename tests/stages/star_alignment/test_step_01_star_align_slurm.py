"""Real-owner wrapper evidence for the Step 01 hash-runtime boundary."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
JOB = (
    REPO_ROOT
    / "src"
    / "norad"
    / "stages"
    / "star_alignment"
    / "step_01_star_align.slurm"
)
OWNER = JOB.with_suffix(".sh")
CHECKOUT_IMPLEMENTATION = (
    OWNER,
    REPO_ROOT / "src/norad/libraries/argument_parsing.sh",
    REPO_ROOT / "src/norad/libraries/file_checks.sh",
    REPO_ROOT / "src/norad/libraries/executable_resolution.sh",
    REPO_ROOT / "src/norad/libraries/signal_traps.sh",
)
CONTROLLED_HASH_PREFIX = ("-X", "pycache_prefix=/dev/null", "-I", "-c")


@dataclass(slots=True)
class WrapperContext:
    submit: Path
    launch: Path
    spool_job: Path
    environment: dict[str, str]
    module_log: Path
    hash_log_dir: Path
    hash_count: Path
    r1: Path
    r2: Path
    index_member: Path
    output_dir: Path


def write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def install_guarded_python(path: Path) -> None:
    write_executable(
        path,
        """#!/bin/bash
set -euo pipefail
count=0
if [[ -f "${HASH_PYTHON_COUNT:?}" ]]; then
    read -r count < "$HASH_PYTHON_COUNT"
fi
count=$((count + 1))
printf '%s\n' "$count" > "$HASH_PYTHON_COUNT"
{
    printf '%s\\0' "$0"
    printf '%s\\0' "$@"
} > "${HASH_PYTHON_LOG_DIR:?}/$count.args"
printf '%s\\0%s\\0' \
    "${NORAD_SHA256_PYTHON:-}" \
    "${NORAD_REQUIRE_BOUND_SHA256:-}" \
    > "$HASH_PYTHON_LOG_DIR/$count.env"
exec "${REAL_PYTHON:?}" "$@"
""",
    )


def prepare_wrapper(tmp_path: Path) -> WrapperContext:
    submit = tmp_path / "submit"
    launch = tmp_path / "alternate-launch"
    spool = tmp_path / "slurm-spool"
    fake_bin = tmp_path / "fake-bin"
    runtime_tmp = tmp_path / "runtime-tmp"
    hash_log_dir = tmp_path / "hash-python"
    for path in (submit, launch, spool, fake_bin, runtime_tmp, hash_log_dir):
        path.mkdir()

    spool_job = spool / "slurm_script"
    shutil.copy2(JOB, spool_job)
    for source in CHECKOUT_IMPLEMENTATION:
        destination = submit / source.relative_to(REPO_ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    module_log = tmp_path / "module.log"
    write_executable(
        fake_bin / "module",
        """#!/bin/bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_MODULE_LOG:?}"
""",
    )
    write_executable(fake_bin / "STAR", "#!/bin/bash\nexit 0\n")

    r1 = submit / "inputs/sample_R1.fastq"
    r2 = submit / "inputs/sample_R2.fastq"
    index_member = submit / "refs/star-index/Genome"
    for path, content in (
        (r1, "read one\n"),
        (r2, "read two\n"),
        (index_member, "STAR index\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    output_dir = submit / "outputs/step01"

    environment = os.environ.copy()
    for name in (
        "EXECUTE",
        "NORAD_REQUIRE_BOUND_SHA256",
        "NORAD_SHA256_PYTHON",
    ):
        environment.pop(name, None)
    environment.update(
        {
            "PATH": os.pathsep.join((str(fake_bin), "/usr/bin", "/bin")),
            "TMPDIR": str(runtime_tmp),
            "USER": "norad-test",
            "SLURM_JOB_ID": "local-step01-wrapper-test",
            "SLURM_JOB_NAME": "local-step01-wrapper-test",
            "SLURMD_NODENAME": "local-mock-node",
            "SLURM_CPUS_PER_TASK": "3",
            "SLURM_SUBMIT_DIR": str(submit),
            "SAMPLE_ID": "sample-test",
            "R1_FASTQ": str(r1),
            "R2_FASTQ": str(r2),
            "STAR_INDEX": str(index_member.parent),
            "OUTPUT_DIR": str(output_dir),
            "EXECUTE": "0",
            "FAKE_MODULE_LOG": str(module_log),
            "HASH_PYTHON_COUNT": str(tmp_path / "hash-python.count"),
            "HASH_PYTHON_LOG_DIR": str(hash_log_dir),
            "REAL_PYTHON": sys.executable,
        }
    )
    return WrapperContext(
        submit=submit,
        launch=launch,
        spool_job=spool_job,
        environment=environment,
        module_log=module_log,
        hash_log_dir=hash_log_dir,
        hash_count=Path(environment["HASH_PYTHON_COUNT"]),
        r1=r1,
        r2=r2,
        index_member=index_member,
        output_dir=output_dir,
    )


def run_wrapper(context: WrapperContext) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(context.spool_job)],
        cwd=context.launch,
        env=context.environment,
        text=True,
        capture_output=True,
        check=False,
    )


def read_nul_fields(path: Path) -> tuple[str, ...]:
    fields = path.read_bytes().split(b"\0")
    assert fields[-1] == b""
    return tuple(field.decode() for field in fields[:-1])


@pytest.mark.parametrize("binding", ("checkout_default", "explicit_override"))
def test_wrapper_real_owner_uses_controlled_hash_python(
    tmp_path: Path,
    binding: str,
) -> None:
    context = prepare_wrapper(tmp_path)
    if binding == "checkout_default":
        launcher = context.submit / ".venv/bin/python"
    else:
        launcher = tmp_path / "operator-python"
        context.environment["NORAD_SHA256_PYTHON"] = str(launcher)
    install_guarded_python(launcher)

    result = run_wrapper(context)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert f"Controlled SHA-256 Python: {launcher}" in result.stdout
    assert "STAR alignment context" in result.stdout
    assert "No-clobber transaction: true" in result.stdout
    assert context.hash_count.read_text(encoding="utf-8") == "3\n"
    expected_paths = (str(context.r1), str(context.r2), str(context.index_member))
    for number, expected_path in enumerate(expected_paths, 1):
        argv = read_nul_fields(context.hash_log_dir / f"{number}.args")
        assert argv[0] == str(launcher)
        assert argv[1:5] == CONTROLLED_HASH_PREFIX
        assert "hashlib.sha256()" in argv[5]
        assert argv[6] == expected_path
        assert read_nul_fields(context.hash_log_dir / f"{number}.env") == (
            str(launcher),
            "1",
        )
    assert not context.output_dir.exists()
    assert not (context.launch / "logs").exists()
    assert not (context.spool_job.parent / "logs").exists()


@pytest.mark.parametrize("binding", ("relative", "nonexecutable"))
def test_wrapper_rejects_unusable_hash_python_before_mutation(
    tmp_path: Path,
    binding: str,
) -> None:
    context = prepare_wrapper(tmp_path)
    for name in ("SAMPLE_ID", "R1_FASTQ", "R2_FASTQ", "STAR_INDEX", "OUTPUT_DIR"):
        context.environment.pop(name)
    if binding == "relative":
        launcher = Path("relative/python")
        expected = f"must be an absolute path: {launcher}"
    else:
        launcher = tmp_path / "nonexecutable-python"
        launcher.write_text("#!/bin/bash\n", encoding="utf-8")
        launcher.chmod(0o644)
        expected = f"is not executable: {launcher}"
    context.environment["NORAD_SHA256_PYTHON"] = str(launcher)

    result = run_wrapper(context)

    assert result.returncode == 1, result.stdout + result.stderr
    assert expected in result.stderr
    assert not context.module_log.exists()
    assert not context.hash_count.exists()
    assert list(context.hash_log_dir.iterdir()) == []
    assert not (context.submit / "data/test").exists()
    assert not (context.submit / "refs/test_star_index").exists()
    assert not (context.submit / "results").exists()
    assert not (context.submit / "logs").exists()
    assert list(context.launch.iterdir()) == []
