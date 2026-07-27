import csv
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_step_00a_star_index.py"
SPEC = importlib.util.spec_from_file_location("step00a_validator", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)
MEMBERS = (
    "genomeParameters.txt", "Genome", "SA", "SAindex", "chrLength.txt",
    "chrName.txt", "chrNameLength.txt", "chrStart.txt", "exonGeTrInfo.tab",
    "exonInfo.tab", "geneInfo.tab", "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab", "sjdbList.out.tab", "transcriptInfo.tab",
)


def fixture(tmp_path: Path):
    reference = tmp_path / "reference"
    reference.mkdir()
    fasta = reference / "genome.fa"
    fasta.write_text(">1\nACGT\n>MT\nAA\n")
    gtf = reference / "genome.gtf"
    gtf.write_text('1\tfixture\tgene\t1\t4\t.\t+\t.\tgene_id "G1";\n')
    index = tmp_path / "index"
    index.mkdir()
    for name in MEMBERS:
        (index / name).write_text("fixture\n")
    (index / "chrName.txt").write_text("1\nMT\n")
    (index / "chrLength.txt").write_text("4\n2\n")
    (index / "genomeParameters.txt").write_text(
        f"genomeFastaFiles {fasta}\n"
        f"sjdbGTFfile {gtf}\n"
        "sjdbOverhang 149\n"
    )
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    output = output_dir / "novogene_ref.validation.tsv"
    return index, fasta, gtf, output


def run(index: Path, fasta: Path, gtf: Path, output: Path, *extra: str):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            *arguments(index, fasta, gtf, output, *extra),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def arguments(index: Path, fasta: Path, gtf: Path, output: Path, *extra: str):
    return [
        "--scope-id", "novogene_ref",
        "--index-dir", str(index),
        "--reference-fasta", str(fasta),
        "--reference-gtf", str(gtf),
        "--parameter-path-base", str(index.parent),
        "--expected-sjdb-overhang", "149",
        "--output", str(output),
        *extra,
    ]


def report_rows(path: Path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def test_dry_run_is_side_effect_free(tmp_path):
    index, fasta, gtf, output = fixture(tmp_path)
    result = run(index, fasta, gtf, output)
    assert result.returncode == 0, result.stderr
    assert "Dry-run complete" in result.stdout
    assert not output.exists()
    assert not list(output.parent.glob(".*validation*"))


def test_execute_publishes_five_passing_checks(tmp_path):
    index, fasta, gtf, output = fixture(tmp_path)
    result = run(index, fasta, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(output)
    assert len(rows) == 5
    assert [row["check_id"] for row in rows] == [
        "index_members", "fasta_identity", "gtf_identity",
        "contig_names_lengths", "sjdb_overhang",
    ]
    assert {row["status"] for row in rows} == {"pass"}
    first = output.read_bytes()
    assert run(index, fasta, gtf, output, "--execute").returncode == 0
    assert output.read_bytes() == first


def test_scientific_mismatches_are_reported_not_repaired(tmp_path):
    index, fasta, gtf, output = fixture(tmp_path)
    (index / "chrLength.txt").write_text("4\n3\n")
    parameters = (index / "genomeParameters.txt").read_text()
    (index / "genomeParameters.txt").write_text(
        parameters.replace("sjdbOverhang 149", "sjdbOverhang 99")
    )
    result = run(index, fasta, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    statuses = {row["check_id"]: row["status"] for row in report_rows(output)}
    assert statuses["contig_names_lengths"] == "fail"
    assert statuses["sjdb_overhang"] == "fail"
    assert fasta.read_text() == ">1\nACGT\n>MT\nAA\n"


def test_invalid_contract_and_missing_member_fail_closed(tmp_path):
    index, fasta, gtf, output = fixture(tmp_path)
    (index / "Genome").unlink()
    result = run(index, fasta, gtf, output, "--execute")
    assert result.returncode == 0, result.stderr
    member = next(row for row in report_rows(output) if row["check_id"] == "index_members")
    assert member["status"] == "fail"
    bad_output = output.parent / "wrong.tsv"
    result = run(index, fasta, gtf, bad_output, "--execute")
    assert result.returncode == 2
    assert not bad_output.exists()


def test_foreign_lock_and_invalid_predecessor_are_preserved(tmp_path):
    index, fasta, gtf, output = fixture(tmp_path)
    lock = output.parent / f".{output.name}.lock"
    lock.write_text("foreign\n")
    result = run(index, fasta, gtf, output, "--execute")
    assert result.returncode == 2
    assert lock.read_text() == "foreign\n"
    lock.unlink()
    output.write_text("foreign\n")
    result = run(index, fasta, gtf, output, "--execute")
    assert result.returncode == 2
    assert output.read_text() == "foreign\n"


def test_publish_failure_restores_valid_predecessor_byte_for_byte(
    tmp_path, monkeypatch
):
    index, fasta, gtf, output = fixture(tmp_path)
    assert run(index, fasta, gtf, output, "--execute").returncode == 0
    previous = output.read_bytes()

    real_validate = VALIDATOR.validate_report
    calls = 0

    def fail_after_publication(data, scope_id, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise VALIDATOR.ValidationError("injected published-report failure")
        return real_validate(data, scope_id, **kwargs)

    monkeypatch.setattr(VALIDATOR, "validate_report", fail_after_publication)
    with pytest.raises(VALIDATOR.ValidationError, match="injected"):
        VALIDATOR.publish(output, previous, "novogene_ref")

    assert output.read_bytes() == previous
    assert not list(output.parent.glob(f".{output.name}.*.tmp"))
    assert not list(output.parent.glob(f".{output.name}.*.previous"))
    assert not (output.parent / f".{output.name}.lock").exists()


def test_first_publication_failure_cleans_owned_paths(tmp_path, monkeypatch):
    index, fasta, gtf, output = fixture(tmp_path)
    args = VALIDATOR.parse_args(arguments(index, fasta, gtf, output))
    data, _ = VALIDATOR.build_report(args)
    real_replace = VALIDATOR.os.replace

    def fail_first_publication(source, destination):
        if Path(source).name.endswith(".tmp") and Path(destination) == output:
            raise OSError("injected first-publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(VALIDATOR.os, "replace", fail_first_publication)
    with pytest.raises(OSError, match="injected first-publication"):
        VALIDATOR.publish(output, data, "novogene_ref")

    assert not output.exists()
    assert not list(output.parent.glob(f".{output.name}.*.tmp"))
    assert not list(output.parent.glob(f".{output.name}.*.previous"))
    assert not (output.parent / f".{output.name}.lock").exists()


def test_input_mutation_after_validation_aborts_before_publication(
    tmp_path, monkeypatch, capsys
):
    index, fasta, gtf, output = fixture(tmp_path)
    real_build_report = VALIDATOR.build_report

    def build_then_mutate(args):
        data, snapshots = real_build_report(args)
        fasta.write_text(">1\nACGT\n>MT\nAAA\n")
        return data, snapshots

    monkeypatch.setattr(VALIDATOR, "build_report", build_then_mutate)
    result = VALIDATOR.main(arguments(index, fasta, gtf, output, "--execute"))

    assert result == 2
    assert "Input changed after validation" in capsys.readouterr().err
    assert not output.exists()
    assert not list(output.parent.glob(".*validation*"))


def test_output_and_parent_symlink_aliases_are_preserved(tmp_path):
    index, fasta, gtf, output = fixture(tmp_path)
    foreign = tmp_path / "foreign.tsv"
    foreign.write_text("foreign\n")
    output.symlink_to(foreign)

    aliased_output = run(index, fasta, gtf, output, "--execute")
    assert aliased_output.returncode == 2
    assert "unsafe" in aliased_output.stderr
    assert output.is_symlink()
    assert foreign.read_text() == "foreign\n"

    output.unlink()
    real_parent = output.parent
    linked_parent = tmp_path / "linked-results"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    linked_output = linked_parent / output.name

    aliased_parent = run(index, fasta, gtf, linked_output, "--execute")
    assert aliased_parent.returncode == 2
    assert "existing real directory" in aliased_parent.stderr
    assert linked_parent.is_symlink()
    assert not output.exists()


def test_incomplete_rollback_retains_lock_and_predecessor(
    tmp_path, monkeypatch
):
    index, fasta, gtf, output = fixture(tmp_path)
    assert run(index, fasta, gtf, output, "--execute").returncode == 0
    previous_data = output.read_bytes()

    real_validate = VALIDATOR.validate_report
    validation_calls = 0

    def fail_after_publication(data, scope_id, **kwargs):
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 3:
            raise VALIDATOR.ValidationError("injected published-report failure")
        return real_validate(data, scope_id, **kwargs)

    real_replace = os.replace

    def fail_predecessor_restore(source, destination):
        if Path(source).name.endswith(".previous") and Path(destination) == output:
            raise OSError("injected predecessor-restore failure")
        real_replace(source, destination)

    monkeypatch.setattr(VALIDATOR, "validate_report", fail_after_publication)
    monkeypatch.setattr(VALIDATOR.os, "replace", fail_predecessor_restore)
    with pytest.raises(
        VALIDATOR.ValidationError, match="rollback was incomplete"
    ):
        VALIDATOR.publish(output, previous_data, "novogene_ref")

    lock = output.parent / f".{output.name}.lock"
    backups = list(output.parent.glob(f".{output.name}.*.previous"))
    assert lock.is_file()
    assert len(backups) == 1
    assert backups[0].read_bytes() == previous_data
    assert not output.exists()


def test_predecessor_cleanup_failure_retains_lock_and_recovery_copy(
    tmp_path, monkeypatch
):
    index, fasta, gtf, output = fixture(tmp_path)
    assert run(index, fasta, gtf, output, "--execute").returncode == 0
    previous_data = output.read_bytes()
    real_unlink = Path.unlink

    def fail_previous_cleanup(path, *args, **kwargs):
        if path.name.endswith(".previous"):
            raise OSError("injected predecessor-cleanup failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_previous_cleanup)
    with pytest.raises(
        VALIDATOR.ValidationError, match="cleanup was incomplete"
    ):
        VALIDATOR.publish(output, previous_data, "novogene_ref")

    lock = output.parent / f".{output.name}.lock"
    backups = list(output.parent.glob(f".{output.name}.*.previous"))
    assert lock.is_file()
    assert output.read_bytes() == previous_data
    assert len(backups) == 1
    assert backups[0].read_bytes() == previous_data
