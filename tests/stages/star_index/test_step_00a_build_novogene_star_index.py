"""Owner-local mocked behavior for the embedded Step 00a STAR-index job."""

from __future__ import annotations

import gzip
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
JOB = (
    REPO_ROOT
    / "src"
    / "norad"
    / "stages"
    / "star_index"
    / "step_00a_build_novogene_star_index.slurm"
)
EXPECTED_MODULE_CALLS = ("load star/2.7.11b", "list")
EXPECTED_STAR_CALL = (
    "STAR\t--runThreadN\t{threads}\t--runMode\tgenomeGenerate"
    "\t--genomeDir\trefs/novogene_star_index"
    "\t--genomeFastaFiles\trefs/novogene_ref/genome.fa"
    "\t--sjdbGTFfile\trefs/novogene_ref/genome.gtf"
    "\t--sjdbOverhang\t149"
)


def write_executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


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
        printf 'mock STAR index\n' > "${args[$((i + 1))]}/Genome"
    fi
done
""",
    )


def prepared_environment(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    submit = tmp_path / "submit"
    fake_bin = tmp_path / "fake-bin"
    runtime_tmp = tmp_path / "runtime-tmp"
    submit.mkdir()
    fake_bin.mkdir()
    runtime_tmp.mkdir()
    install_fakes(fake_bin)
    environment = os.environ.copy()
    environment.update(
        {
            "PATH": os.pathsep.join((str(fake_bin), "/usr/bin", "/bin")),
            "TMPDIR": str(runtime_tmp),
            "SLURM_JOB_ID": "local-step00a-test",
            "SLURM_JOB_NAME": "local-step00a-test",
            "SLURMD_NODENAME": "local-mock-node",
            "SLURM_CPUS_PER_TASK": "3",
            "FAKE_MODULE_LOG": str(tmp_path / "module.log"),
            "FAKE_MODULE_EXIT": "0",
            "FAKE_TOOL_LOG": str(tmp_path / "tool.log"),
            "FAKE_TOOL_EXIT": "37",
            "FAKE_FAIL_TOOL": "",
        }
    )
    return submit, environment


def write_compressed_inputs(submit: Path) -> None:
    reference_dir = submit / "data/raw/novogene_remora/04.Ref"
    reference_dir.mkdir(parents=True)
    with gzip.open(reference_dir / "genome.fa.gz", "wt", encoding="utf-8") as handle:
        handle.write(">chr1\nACGT\n")
    with gzip.open(reference_dir / "genome.gtf.gz", "wt", encoding="utf-8") as handle:
        handle.write('chr1\ttest\texon\t1\t4\t.\t+\t.\tgene_id "g1";\n')


def run_job(
    submit: Path,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(JOB)],
        cwd=submit,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def read_lines(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(path.read_text(encoding="utf-8").splitlines())


def test_mocked_star_success_preserves_exact_arguments_and_incomplete_output(
    tmp_path: Path,
) -> None:
    submit, environment = prepared_environment(tmp_path)
    write_compressed_inputs(submit)

    result = run_job(submit, environment)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert read_lines(Path(environment["FAKE_MODULE_LOG"])) == EXPECTED_MODULE_CALLS
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == (
        EXPECTED_STAR_CALL.format(threads="3"),
    )
    assert (submit / "refs/novogene_ref/genome.fa").read_bytes() == b">chr1\nACGT\n"
    assert (submit / "refs/novogene_ref/genome.gtf").read_bytes().endswith(b"\n")
    index_members = sorted(
        path.name for path in (submit / "refs/novogene_star_index").iterdir()
    )
    assert index_members == ["Genome"]
    assert "STAR index build complete." in result.stdout


def test_existing_references_are_reused_byte_for_byte_with_default_threads(
    tmp_path: Path,
) -> None:
    submit, environment = prepared_environment(tmp_path)
    prepared = submit / "refs/novogene_ref"
    prepared.mkdir(parents=True)
    fasta_bytes = b">prepared\nAAAA\n"
    gtf_bytes = b'prepared\tfixture\tgene\t1\t4\t.\t+\t.\tgene_id "p";\n'
    (prepared / "genome.fa").write_bytes(fasta_bytes)
    (prepared / "genome.gtf").write_bytes(gtf_bytes)
    environment.pop("SLURM_CPUS_PER_TASK")

    result = run_job(submit, environment)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (prepared / "genome.fa").read_bytes() == fasta_bytes
    assert (prepared / "genome.gtf").read_bytes() == gtf_bytes
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == (
        EXPECTED_STAR_CALL.format(threads="8"),
    )
    assert (submit / "refs/novogene_star_index/Genome").is_file()


def test_module_failure_precedes_reference_and_output_directory_creation(
    tmp_path: Path,
) -> None:
    submit, environment = prepared_environment(tmp_path)
    environment["FAKE_MODULE_EXIT"] = "23"

    result = run_job(submit, environment)

    assert result.returncode == 23
    assert read_lines(Path(environment["FAKE_MODULE_LOG"])) == ("load star/2.7.11b",)
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == ()
    assert not (submit / "refs").exists()


def test_star_failure_retains_prepared_references_and_created_directories(
    tmp_path: Path,
) -> None:
    submit, environment = prepared_environment(tmp_path)
    write_compressed_inputs(submit)
    environment["FAKE_FAIL_TOOL"] = "STAR"

    result = run_job(submit, environment)

    assert result.returncode == 37
    assert read_lines(Path(environment["FAKE_MODULE_LOG"])) == EXPECTED_MODULE_CALLS
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == (
        EXPECTED_STAR_CALL.format(threads="3"),
    )
    assert (submit / "refs/novogene_ref/genome.fa").read_bytes() == b">chr1\nACGT\n"
    assert (submit / "refs/novogene_ref/genome.gtf").is_file()
    assert (submit / "refs/novogene_star_index").is_dir()
    assert list((submit / "refs/novogene_star_index").iterdir()) == []
    assert "STAR index build complete." not in result.stdout
