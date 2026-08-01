import csv
import subprocess
import sys
from pathlib import Path

from validation_roster_expectations import assert_exact_check_roster


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_00b_bed12.py"


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


def run(bed: Path, gtf: Path, output: Path, *extra: str):
    return subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "--scope-id", "novogene_ref",
            "--bed12", str(bed),
            "--source-gtf", str(gtf),
            "--output", str(output),
            *extra,
        ],
        cwd=ROOT,
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
