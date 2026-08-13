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
PRODUCER = JOB.with_name("step_00a_build_star_index.sh")
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
EXPECTED_MODULE_CALLS = ("load star/2.7.11b", "list")
EXPECTED_STAR_CALL = (
    "STAR\t--runThreadN\t{threads}\t--runMode\tgenomeGenerate"
    "\t--genomeDir\trefs/.novogene_star_index.step00a.local-step00a-test.tmp"
    "\t--genomeFastaFiles\trefs/novogene_ref/genome.fa"
    "\t--sjdbGTFfile\trefs/novogene_ref/genome.gtf"
    "\t--sjdbOverhang\t149"
    "\t--genomeSAindexNbases\t14"
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
            "FAKE_INCOMPLETE_STAR": "0",
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


def test_mocked_star_success_delegates_and_publishes_complete_output(
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
    index_members = {
        path.name for path in (submit / "refs/novogene_star_index").iterdir()
    }
    assert index_members == REQUIRED_MEMBERS
    assert not (submit / "refs/.novogene_star_index.step00a.lock").exists()
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
    assert not (submit / "refs/novogene_star_index").exists()
    assert not (
        submit / "refs/.novogene_star_index.step00a.local-step00a-test.tmp"
    ).exists()
    assert not (submit / "refs/.novogene_star_index.step00a.lock").exists()
    assert "STAR index build complete." not in result.stdout


def test_public_producer_dry_run_is_side_effect_free_from_arbitrary_cwd(
    tmp_path: Path,
) -> None:
    _, environment = prepared_environment(tmp_path)
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
    assert "Dry-run only" in result.stdout
    assert "--runMode genomeGenerate" in result.stdout
    assert not index.parent.exists()
    assert read_lines(Path(environment["FAKE_TOOL_LOG"])) == ()
    assert list(invocation_cwd.iterdir()) == []


def test_public_producer_execute_publishes_declared_members_without_replacement(
    tmp_path: Path,
) -> None:
    _, environment = prepared_environment(tmp_path)
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
    _, environment = prepared_environment(tmp_path)
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
    _, environment = prepared_environment(tmp_path)
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
    _, environment = prepared_environment(tmp_path)
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
    _, environment = prepared_environment(tmp_path)
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
    _, environment = prepared_environment(tmp_path)
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
    _, environment = prepared_environment(tmp_path)
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
    _, environment = prepared_environment(tmp_path)
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
