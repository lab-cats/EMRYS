"""Owner-local mocked behavior for the Step 00a STAR-index producer."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCER = (
    REPO_ROOT
    / "src"
    / "emrys"
    / "stages"
    / "star_index"
    / "step_00a_build_star_index.sh"
)
REQUIRED_MEMBERS = {
    "genomeParameters.txt",
    "Genome",
    "SA",
    "SAindex",
    "chrLength.txt",
    "chrName.txt",
    "chrNameLength.txt",
    "chrStart.txt",
    "exonGeTrInfo.tab",
    "exonInfo.tab",
    "geneInfo.tab",
    "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab",
    "sjdbList.out.tab",
    "transcriptInfo.tab",
}


def write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def install_fakes(fake_bin: Path) -> None:
    write_executable(
        fake_bin / "STAR",
        """#!/bin/bash
set -euo pipefail
{
    printf 'STAR'
    printf '\t%s' "$@"
    printf '\n'
} >> "${FAKE_TOOL_LOG:?}"
if [[ "${FAKE_FAIL_TOOL:-}" == "STAR" ]]; then
    exit "${FAKE_TOOL_EXIT:-37}"
fi
args=("$@")
for ((i = 0; i < ${#args[@]}; i++)); do
    if [[ "${args[$i]}" == "--genomeDir" ]]; then
        mkdir -p "${args[$((i + 1))]}"
        if [[ "${FAKE_INCOMPLETE_STAR:-0}" == "1" ]]; then
            printf 'mock incomplete STAR index\n' > "${args[$((i + 1))]}/Genome"
            continue
        fi
        for member in \
            genomeParameters.txt Genome SA SAindex chrLength.txt chrName.txt \
            chrNameLength.txt chrStart.txt exonGeTrInfo.tab exonInfo.tab \
            geneInfo.tab sjdbInfo.txt sjdbList.fromGTF.out.tab \
            sjdbList.out.tab transcriptInfo.tab; do
            printf 'mock STAR index member %s\n' "$member" > "${args[$((i + 1))]}/$member"
        done
        if [[ -n "${FAKE_LATE_INDEX_PATH:-}" ]]; then
            mkdir -p "${FAKE_LATE_INDEX_PATH}"
            printf 'foreign index\n' > "${FAKE_LATE_INDEX_PATH}/foreign-marker"
        fi
    fi
done
""",
    )


def prepared_environment(tmp_path: Path) -> dict[str, str]:
    fake_bin = tmp_path / "fake-bin"
    runtime_tmp = tmp_path / "runtime-tmp"
    fake_bin.mkdir()
    runtime_tmp.mkdir()
    install_fakes(fake_bin)
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": os.pathsep.join((str(fake_bin), "/usr/bin", "/bin")),
            "TMPDIR": str(runtime_tmp),
            "EMRYS_SHA256_PYTHON": sys.executable,
            "SLURM_JOB_ID": "local-step00a-test",
            "FAKE_TOOL_LOG": str(tmp_path / "tool.log"),
            "FAKE_TOOL_EXIT": "37",
            "FAKE_FAIL_TOOL": "",
            "FAKE_INCOMPLETE_STAR": "0",
        }
    )
    return environment


def run_producer(
    reference_fasta: Path,
    reference_gtf: Path,
    index_dir: Path,
    environment: dict[str, str],
    *,
    execute: bool,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    command = [
        "/bin/bash",
        str(PRODUCER),
        "--reference-fasta",
        str(reference_fasta),
        "--reference-gtf",
        str(reference_gtf),
        "--index-dir",
        str(index_dir),
        "--threads",
        "2",
        "--sjdb-overhang",
        "149",
        "--genome-sa-index-nbases",
        "14",
        "--star-bin",
        "STAR",
    ]
    if execute:
        command.append("--execute")
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def read_lines(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(path.read_text(encoding="utf-8").splitlines())


def test_public_producer_dry_run_is_side_effect_free_from_arbitrary_cwd(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text(
        'chr1\ttest\texon\t1\t4\t.\t+\t.\tgene_id "g1";\n',
        encoding="utf-8",
    )
    index = tmp_path / "outputs" / "star-index"
    invocation_cwd = tmp_path / "elsewhere"
    invocation_cwd.mkdir()
    environment["EMRYS_RUN_TOKEN"] = "explicit-owner-step00a"
    environment["SLURM_JOB_ID"] = "scheduler-step00a"

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=False,
        cwd=invocation_cwd,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert "Mode: dry-run" in result.stdout
    assert "Run token: explicit-owner-step00a" in result.stdout
    assert "Dry-run only" in result.stdout
    assert "--runMode genomeGenerate" in result.stdout
    assert not index.parent.exists()
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == ()
    assert list(invocation_cwd.iterdir()) == []


def test_public_producer_rejects_unsafe_explicit_run_token_before_mutation(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    invocation_cwd = tmp_path / "elsewhere"
    invocation_cwd.mkdir()
    environment["EMRYS_RUN_TOKEN"] = "../unsafe-owner-token"
    environment["SLURM_JOB_ID"] = "safe-scheduler-token"

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=False,
        cwd=invocation_cwd,
    )

    assert result.returncode != 0
    assert "STAR index run token must match" in result.stderr
    assert not index.parent.exists()
    assert list(invocation_cwd.iterdir()) == []


def test_public_producer_execute_publishes_declared_members_without_replacement(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    invocation_cwd = tmp_path / "elsewhere"
    invocation_cwd.mkdir()

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=True,
        cwd=invocation_cwd,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert {path.name for path in index.iterdir()} == REQUIRED_MEMBERS
    assert "STAR index publication complete" in result.stdout
    assert not (index.parent / ".star-index.step00a.lock").exists()
    assert not (index.parent / ".star-index.step00a.local-step00a-test.tmp").exists()
    assert list(invocation_cwd.iterdir()) == []


def test_public_producer_preserves_index_that_appears_during_generation(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    environment["FAKE_LATE_INDEX_PATH"] = str(index)

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "appeared during execution" in result.stderr
    assert (index / "foreign-marker").read_bytes() == b"foreign index\n"
    assert {path.name for path in index.iterdir()} == {"foreign-marker"}
    assert not (index.parent / ".star-index.step00a.lock").exists()
    assert not (index.parent / ".star-index.step00a.local-step00a-test.tmp").exists()


def test_public_producer_preserves_late_member_and_recovery_state(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    fake_bin = Path(environment["PATH"].split(os.pathsep)[0])
    write_executable(
        fake_bin / "ln",
        """#!/bin/bash
set -euo pipefail
final_arg="${!#}"
if [[ "$final_arg" == "${FAKE_LATE_MEMBER_PATH:?}" ]]; then
    printf 'foreign member\n' > "$final_arg"
fi
exec /bin/ln "$@"
""",
    )
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    environment["FAKE_LATE_MEMBER_PATH"] = str(index / "Genome")

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "member appeared during publication" in result.stderr
    assert (index / "Genome").read_bytes() == b"foreign member\n"
    lock = index.parent / ".star-index.step00a.lock"
    staged = index.parent / ".star-index.step00a.local-step00a-test.tmp"
    assert lock.is_dir()
    assert staged.is_dir()
    assert (staged / "Genome").is_file()


def test_public_producer_rejects_noncolliding_late_member(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    fake_bin = Path(environment["PATH"].split(os.pathsep)[0])
    write_executable(
        fake_bin / "ln",
        """#!/bin/bash
set -euo pipefail
final_arg="${!#}"
if [[ "$final_arg" == "${FAKE_LATE_MEMBER_TRIGGER:?}" ]]; then
    printf 'foreign extra member\n' > "${FAKE_LATE_EXTRA_PATH:?}"
fi
exec /bin/ln "$@"
""",
    )
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    environment["FAKE_LATE_MEMBER_TRIGGER"] = str(index / "Genome")
    environment["FAKE_LATE_EXTRA_PATH"] = str(index / "foreign-marker")

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "final member set changed during publication" in result.stderr
    assert (index / "foreign-marker").read_bytes() == b"foreign extra member\n"
    lock = index.parent / ".star-index.step00a.lock"
    staged = index.parent / ".star-index.step00a.local-step00a-test.tmp"
    assert lock.is_dir()
    assert staged.is_dir()
    assert (staged / "Genome").is_file()


def test_public_producer_never_replaces_existing_index(tmp_path: Path) -> None:
    environment = prepared_environment(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    index.mkdir(parents=True)
    marker = index / "foreign-marker"
    marker.write_bytes(b"preserve\n")

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "refusing to replace" in result.stderr
    assert marker.read_bytes() == b"preserve\n"
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == ()


def test_public_producer_incomplete_tool_success_rolls_back_owned_state(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    environment["FAKE_INCOMPLETE_STAR"] = "1"
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "STAR index member is missing" in result.stderr
    assert not index.exists()
    assert not (index.parent / ".star-index.step00a.lock").exists()
    assert not (index.parent / ".star-index.step00a.local-step00a-test.tmp").exists()


def test_public_producer_preserves_foreign_lock(tmp_path: Path) -> None:
    environment = prepared_environment(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    lock = index.parent / ".star-index.step00a.lock"
    lock.mkdir(parents=True)
    owner = lock / "owner"
    owner.write_text("run_token=foreign\n", encoding="utf-8")

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=True,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "publication lock already exists" in result.stderr
    assert owner.read_text(encoding="utf-8") == "run_token=foreign\n"
    assert not index.exists()
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == ()


def test_public_producer_preserves_staging_residue_from_another_attempt(
    tmp_path: Path,
) -> None:
    environment = prepared_environment(tmp_path)
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    fasta = inputs / "genome.fa"
    gtf = inputs / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "outputs" / "star-index"
    residue = index.parent / ".star-index.step00a.older-attempt.tmp"
    residue.mkdir(parents=True)
    marker = residue / "Genome"
    marker.write_bytes(b"preserve\n")

    result = run_producer(
        fasta,
        gtf,
        index,
        environment,
        execute=False,
        cwd=tmp_path,
    )

    assert result.returncode == 1
    assert "staging residue requires inspection" in result.stderr
    assert marker.read_bytes() == b"preserve\n"
    assert not index.exists()
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == ()
