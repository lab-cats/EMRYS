import subprocess
import sys
from pathlib import Path

from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
MEMBERS = (
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
)


def build_validation_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    reference = tmp_path / "reference"
    reference.mkdir()
    fasta = reference / "genome.fa"
    fasta.write_text(">1\nACGT\n>MT\nAA\n", encoding="utf-8")
    gtf = reference / "genome.gtf"
    gtf.write_text(
        '1\tfixture\tgene\t1\t4\t.\t+\t.\tgene_id "G1";\n',
        encoding="utf-8",
    )
    index = tmp_path / "index"
    index.mkdir()
    for name in MEMBERS:
        (index / name).write_text("fixture\n", encoding="utf-8")
    (index / "chrName.txt").write_text("1\nMT\n", encoding="utf-8")
    (index / "chrLength.txt").write_text("4\n2\n", encoding="utf-8")
    (index / "genomeParameters.txt").write_text(
        f"genomeFastaFiles {fasta}\nsjdbGTFfile {gtf}\nsjdbOverhang 149\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output = output_dir / "novogene_ref.validation.tsv"
    return index, fasta, gtf, output


def run_validator(
    index: Path,
    fasta: Path,
    gtf: Path,
    output: Path,
    *extra: str,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad",
            "validate",
            "star-index",
            "--scope-id",
            "novogene_ref",
            "--index-dir",
            str(index),
            "--reference-fasta",
            str(fasta),
            "--reference-gtf",
            str(gtf),
            "--parameter-path-base",
            str(index.parent),
            "--expected-sjdb-overhang",
            "149",
            "--output",
            str(output),
            *extra,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    index, fasta, gtf, output = build_validation_fixture(tmp_path)
    result = run_validator(index, fasta, gtf, output)
    assert result.returncode == 0, result.stderr
    assert "Dry-run complete" in result.stdout
    assert not output.exists()
    assert not list(output.parent.glob(".*validation*"))


def test_execute_publishes_five_passing_checks(tmp_path: Path) -> None:
    index, fasta, gtf, output = build_validation_fixture(tmp_path)
    result = run_validator(index, fasta, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(output)
    assert_exact_check_roster(rows, "00a")
    assert {row["status"] for row in rows} == {"pass"}
    first = output.read_bytes()
    assert run_validator(index, fasta, gtf, output, "--execute").returncode == 0
    assert output.read_bytes() == first


def test_full_dry_run_and_execute_repeat_are_cwd_independent(tmp_path: Path) -> None:
    index, fasta, gtf, output = build_validation_fixture(tmp_path)
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    before = tuple(invocation_cwd.iterdir())

    dry_run = run_validator(index, fasta, gtf, output, cwd=invocation_cwd)

    assert dry_run.returncode == 0, dry_run.stderr
    assert dry_run.stderr == ""
    assert dry_run.stdout.endswith("Dry-run complete; no output was written.\n")
    assert not output.exists()
    assert tuple(invocation_cwd.iterdir()) == before

    first = run_validator(index, fasta, gtf, output, "--execute", cwd=invocation_cwd)

    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    first_bytes = output.read_bytes()
    dry_prefix = dry_run.stdout.removesuffix(
        "Dry-run complete; no output was written.\n"
    )
    assert first.stdout == (
        dry_prefix + f"Published Step 00a validation report: {output}\n"
    )
    assert first_bytes.decode("utf-8") in dry_prefix
    assert tuple(invocation_cwd.iterdir()) == before

    repeated = run_validator(index, fasta, gtf, output, "--execute", cwd=invocation_cwd)

    assert repeated.returncode == 0, repeated.stderr
    assert repeated.stderr == ""
    assert repeated.stdout == first.stdout
    assert output.read_bytes() == first_bytes
    assert not list(output.parent.glob(".*validation*"))
    assert tuple(invocation_cwd.iterdir()) == before


def test_scientific_mismatches_are_reported_not_repaired(tmp_path: Path) -> None:
    index, fasta, gtf, output = build_validation_fixture(tmp_path)
    (index / "chrLength.txt").write_text("4\n3\n", encoding="utf-8")
    parameters = (index / "genomeParameters.txt").read_text(encoding="utf-8")
    (index / "genomeParameters.txt").write_text(
        parameters.replace("sjdbOverhang 149", "sjdbOverhang 99"),
        encoding="utf-8",
    )
    result = run_validator(index, fasta, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    statuses = {row["check_id"]: row["status"] for row in report_rows(output)}
    assert statuses["contig_names_lengths"] == "fail"
    assert statuses["sjdb_overhang"] == "fail"
    assert fasta.read_text(encoding="utf-8") == ">1\nACGT\n>MT\nAA\n"


def test_invalid_contract_and_missing_member_fail_closed(tmp_path: Path) -> None:
    index, fasta, gtf, output = build_validation_fixture(tmp_path)
    (index / "Genome").unlink()
    result = run_validator(index, fasta, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    member = next(
        row for row in report_rows(output) if row["check_id"] == "index_members"
    )
    assert member["status"] == "fail"
    bad_output = output.parent / "wrong.tsv"
    result = run_validator(index, fasta, gtf, bad_output, "--execute")
    assert result.returncode == 2
    assert not bad_output.exists()


def test_foreign_lock_and_invalid_predecessor_are_preserved(tmp_path: Path) -> None:
    index, fasta, gtf, output = build_validation_fixture(tmp_path)
    lock = output.parent / f".{output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    result = run_validator(index, fasta, gtf, output, "--execute")
    assert result.returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"
    lock.unlink()
    output.write_text("foreign\n", encoding="utf-8")
    result = run_validator(index, fasta, gtf, output, "--execute")
    assert result.returncode == 2
    assert output.read_text(encoding="utf-8") == "foreign\n"
