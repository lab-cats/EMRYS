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
            "EMRYS_TASK_WORK_DIR": str(runtime_tmp),
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
        str(Path(environment["TMPDIR"]).parent / "fake-bin/STAR"),
    ]
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


def test_worker_builds_complete_star_index_from_arbitrary_cwd(tmp_path: Path) -> None:
    environment = prepared_environment(tmp_path)
    fasta = tmp_path / "genome.fa"
    gtf = tmp_path / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "stage" / "star-index"
    index.mkdir(parents=True)
    invocation_cwd = tmp_path / "elsewhere"
    invocation_cwd.mkdir()
    result = run_producer(fasta, gtf, index, environment, cwd=invocation_cwd)
    assert result.returncode == 0, result.stdout + result.stderr
    assert {path.name for path in index.iterdir()} == REQUIRED_MEMBERS
    tool_log = read_lines(Path(environment["FAKE_TOOL_LOG"]))[0]
    assert "--runMode\tgenomeGenerate" in tool_log
    assert "--sjdbOverhang\t149" in tool_log
    assert list(invocation_cwd.iterdir()) == []


def test_worker_rejects_incomplete_native_index(tmp_path: Path) -> None:
    environment = prepared_environment(tmp_path)
    environment["FAKE_INCOMPLETE_STAR"] = "1"
    fasta = tmp_path / "genome.fa"
    gtf = tmp_path / "genome.gtf"
    fasta.write_text(">chr1\nACGT\n", encoding="utf-8")
    gtf.write_text("fixture\n", encoding="utf-8")
    index = tmp_path / "staged-index"
    index.mkdir()
    result = run_producer(fasta, gtf, index, environment, cwd=tmp_path)
    assert result.returncode == 1
    assert "STAR index member is missing" in result.stderr
    # Worker diagnostics remain available to the runner's failure handling.
    assert (index / "Genome").is_file()
