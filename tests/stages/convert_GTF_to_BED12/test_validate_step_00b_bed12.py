import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = (
    ROOT
    / "tests"
    / "contract_integration"
    / "validation_rosters"
    / "validation_roster_expectations.py"
)
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "convert_gtf_to_bed12_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src"
    / "norad"
    / "stages"
    / "convert_GTF_to_BED12"
    / "validate_step_00b_bed12.py"
)


def fixture(tmp_path: Path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    gtf = tmp_path / "genome.gtf"
    gtf.write_text(
        '1\tfixture\texon\t1\t4\t.\t+\t.\tgene_id "G1"; transcript_id "T1";\n'
        '1\tfixture\texon\t9\t10\t.\t+\t.\tgene_id "G1"; transcript_id "T1";\n'
        '2\tfixture\texon\t3\t5\t.\t-\t.\tgene_id "G2"; transcript_id "T2";\n'
    )
    bed = tmp_path / "genome.bed"
    bed.write_text(
        "1\t0\t10\tT1|G1\t0\t+\t0\t10\t0\t2\t4,2,\t0,8,\n"
        "2\t2\t5\tT2|G2\t0\t-\t2\t5\t0\t1\t3,\t0,\n"
    )
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    return bed, gtf, output_dir / "novogene_ref.validation.tsv"


def run(
    bed: Path,
    gtf: Path,
    output: Path,
    *extra: str,
    cwd: Path = ROOT,
):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--scope-id",
            "novogene_ref",
            "--bed12",
            str(bed),
            "--source-gtf",
            str(gtf),
            "--output",
            str(output),
            *extra,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def rows(path: Path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_dry_run_is_side_effect_free(tmp_path):
    bed, gtf, output = fixture(tmp_path)
    result = run(bed, gtf, output)
    assert result.returncode == 0, result.stderr
    assert "Dry-run complete" in result.stdout
    assert not output.exists()


def test_execute_publishes_passing_report(tmp_path):
    bed, gtf, output = fixture(tmp_path)
    result = run(bed, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(output), "00b")
    assert {row["step_id"] for row in rows(output)} == {"00b"}
    assert {row["status"] for row in rows(output)} == {"pass"}


def test_sort_block_and_gtf_mismatches_are_evidence(tmp_path):
    bed, gtf, output = fixture(tmp_path)
    lines = bed.read_text().splitlines()
    fields = lines[0].split("\t")
    fields[10] = "3,3,"
    bed.write_text(lines[1] + "\n" + "\t".join(fields) + "\n")
    result = run(bed, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    statuses = {row["check_id"]: row["status"] for row in rows(output)}
    assert statuses["coordinate_sorting"] == "fail"
    assert statuses["block_structure"] == "fail"
    assert statuses["gtf_transcript_agreement"] == "fail"


def test_malformed_bed_and_wrong_output_fail_closed(tmp_path):
    bed, gtf, output = fixture(tmp_path)
    bed.write_text("1\t0\n")
    assert run(bed, gtf, output, "--execute").returncode == 2
    bed, gtf, output = fixture(tmp_path / "second")
    bad_output = output.parent / "wrong.tsv"
    assert run(bed, gtf, bad_output, "--execute").returncode == 2


def test_foreign_lock_and_invalid_predecessor_are_preserved(tmp_path):
    bed, gtf, output = fixture(tmp_path)
    lock = output.parent / f".{output.name}.lock"
    lock.write_text("foreign\n")
    assert run(bed, gtf, output, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"
    lock.unlink()
    output.write_text("foreign\n")
    assert run(bed, gtf, output, "--execute").returncode == 2
    assert output.read_text() == "foreign\n"


def test_nonrepository_cwd_dry_run_execute_and_repeat_are_identical(tmp_path):
    bed, gtf, output = fixture(tmp_path)
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()

    dry_run = run(bed, gtf, output, cwd=invocation_cwd)

    assert dry_run.returncode == 0
    assert dry_run.stderr == ""
    assert dry_run.stdout.endswith("Dry-run complete; no output was written.\n")
    assert not output.exists()
    assert list(invocation_cwd.iterdir()) == []

    first = run(bed, gtf, output, "--execute", cwd=invocation_cwd)
    first_bytes = output.read_bytes()
    second = run(bed, gtf, output, "--execute", cwd=invocation_cwd)

    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    assert output.read_bytes() == first_bytes
    assert [row["check_id"] for row in rows(output)] == [
        "bed12_structure",
        "coordinate_sorting",
        "block_structure",
        "unique_transcript_names",
        "gtf_transcript_agreement",
    ]
    assert {row["status"] for row in rows(output)} == {"pass"}
    assert list(invocation_cwd.iterdir()) == []
    assert sorted(path.name for path in output.parent.iterdir()) == [output.name]
