import csv
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import reference_provenance


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reference_provenance.py"
HEADER = ["reference_id", "artifact_id", "role", "path", "required", "expected_sha256", "provenance_source", "provenance_release", "notes"]


def make_fixture(root: Path, *, mismatch: bool = False, missing: bool = False) -> Path:
    ref = root / "ref"; star = root / "star"
    ref.mkdir(); star.mkdir()
    (ref / "genome.fa").write_text(">1\nACGT\n>MT\nAAA\n")
    (ref / "genome.fa.fai").write_text("1\t4\t0\t4\t5\nMT\t3\t8\t3\t4\n")
    (ref / "genome.dict").write_text("@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n@SQ\tSN:MT\tLN:3\n")
    (ref / "genome.gtf").write_text("1\ts\tgene\t1\t4\t.\t+\t.\tgene_id \"g\";\n")
    (ref / "genome.bed").write_text("1\t0\t4\tg\t0\t+\t0\t4\t0\t1\t4\t0\n")
    (star / "chrName.txt").write_text("1\nMT\n")
    (star / "chrLength.txt").write_text("4\n" + ("4\n" if mismatch else "3\n"))
    (star / "Genome").write_bytes(b"index")
    rows = [
        ["ref1", "fasta", "fasta", "ref/genome.fa", "true", "NA", "source", "release1", "fasta"],
        ["ref1", "fai", "fai", "ref/genome.fa.fai", "true", "NA", "source", "release1", "fai"],
        ["ref1", "dict", "dict", "ref/genome.dict", "true", "NA", "source", "release1", "dict"],
        ["ref1", "gtf", "gtf", "ref/genome.gtf", "true", "NA", "source", "release1", "gtf"],
        ["ref1", "bed", "bed12", "ref/genome.bed", "true", "NA", "derived", "release1", "bed"],
        ["ref1", "names", "star_chr_name", "star/chrName.txt", "true", "NA", "STAR", "2.7", "names"],
        ["ref1", "lengths", "star_chr_length", "star/chrLength.txt", "true", "NA", "STAR", "2.7", "lengths"],
        ["ref1", "genome", "star_index_file", "star/Genome", "true", "NA", "STAR", "2.7", "index"],
    ]
    if missing:
        rows[-1][3] = "star/missing"
    inventory = root / "inventory.tsv"
    inventory.write_text("\t".join(HEADER) + "\n" + "\n".join("\t".join(row) for row in rows) + "\n")
    return inventory


def run(inventory: Path, output: Path, *args: str):
    return subprocess.run([sys.executable, str(SCRIPT), "--inventory", str(inventory), "--base-dir", str(inventory.parent), "--output-root", str(output), *args], cwd=ROOT, text=True, capture_output=True)


def rows(path: Path):
    with path.open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_help_and_dry_run_side_effect_free(tmp_path):
    assert subprocess.run([sys.executable, str(SCRIPT), "--help"], capture_output=True, text=True).returncode == 0
    inventory = make_fixture(tmp_path)
    output = tmp_path / "missing"
    result = run(inventory, output)
    assert result.returncode == 0
    assert "Dry-run complete" in result.stdout
    assert not output.exists()


def test_execute_publishes_summary_last_contract(tmp_path):
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"; output.mkdir()
    result = run(inventory, output, "--execute")
    assert result.returncode == 0, result.stderr
    directory = output / "ref1"
    artifacts = rows(directory / "ref1.reference_artifacts.tsv")
    contigs = rows(directory / "ref1.reference_contigs.tsv")
    summary = rows(directory / "ref1.reference_summary.tsv")[0]
    assert len(artifacts) == 8
    assert {row["source_role"] for row in contigs} == {"fasta", "fai", "dict", "gtf", "bed12", "star"}
    assert summary["overall_status"] == "pass"
    assert summary["star_agreement"] == "pass"
    original = {path.name: path.read_bytes() for path in directory.iterdir()}
    assert run(inventory, output, "--execute").returncode == 0
    assert original == {path.name: path.read_bytes() for path in directory.iterdir()}


def test_reports_mismatch_missing_and_hash_mismatch(tmp_path):
    inventory = make_fixture(tmp_path, mismatch=True, missing=True)
    text = inventory.read_text()
    digest = hashlib.sha256((tmp_path / "ref/genome.fa").read_bytes()).hexdigest()
    inventory.write_text(text.replace("\tNA\tsource\trelease1\tfasta", "\t" + "0" * 64 + "\tsource\trelease1\tfasta", 1))
    output = tmp_path / "out"; output.mkdir()
    assert run(inventory, output, "--execute").returncode == 0
    artifacts = {row["artifact_id"]: row for row in rows(output / "ref1/ref1.reference_artifacts.tsv")}
    summary = rows(output / "ref1/ref1.reference_summary.tsv")[0]
    assert artifacts["fasta"]["status"] == "hash_mismatch"
    assert artifacts["fasta"]["observed_sha256"] == digest
    assert artifacts["genome"]["status"] == "missing_required"
    assert summary["star_agreement"] == "fail"
    assert summary["overall_status"] == "fail"


def test_invalid_inventory_and_symlink_fail(tmp_path):
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"; output.mkdir()
    bad = tmp_path / "bad.tsv"
    bad.write_text(
        inventory.read_text().replace(
            "\tfasta\tfasta\t",
            "\tfasta\tunsupported\t",
            1,
        )
    )
    assert run(bad, output, "--execute").returncode == 2
    link = tmp_path / "link.tsv"; link.symlink_to(inventory)
    result = run(link, output, "--execute")
    assert result.returncode == 2
    assert "non-symlink" in result.stderr


def test_partial_prior_and_foreign_lock_are_preserved(tmp_path):
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"; directory = output / "ref1"
    directory.mkdir(parents=True)
    partial = directory / "ref1.reference_artifacts.tsv"; partial.write_text("foreign\n")
    result = run(inventory, output, "--execute")
    assert result.returncode == 2
    assert partial.read_text() == "foreign\n"
    partial.unlink()
    lock = directory / ".ref1.reference-provenance.lock"; lock.write_text("foreign\n")
    result = run(inventory, output, "--execute")
    assert result.returncode == 2
    assert lock.read_text() == "foreign\n"


def test_backup_failure_restores_complete_prior_transaction(tmp_path, monkeypatch):
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"; output.mkdir()
    assert run(inventory, output, "--execute").returncode == 0
    directory = output / "ref1"
    finals = sorted(path for path in directory.iterdir() if not path.name.startswith("."))
    original = {path.name: path.read_bytes() for path in finals}
    generated = {
        "artifacts": (directory / "ref1.reference_artifacts.tsv").read_bytes(),
        "contigs": (directory / "ref1.reference_contigs.tsv").read_bytes(),
        "summary": (directory / "ref1.reference_summary.tsv").read_bytes(),
    }
    real_replace = reference_provenance.os.replace
    backup_attempts = 0

    def fail_second_backup(source, destination):
        nonlocal backup_attempts
        if Path(destination).name.endswith(".previous"):
            backup_attempts += 1
            if backup_attempts == 2:
                raise OSError("synthetic backup failure")
        return real_replace(source, destination)

    monkeypatch.setattr(reference_provenance.os, "replace", fail_second_backup)

    with pytest.raises(OSError, match="synthetic backup failure"):
        reference_provenance.publish(output, "ref1", generated)

    assert original == {
        path.name: path.read_bytes()
        for path in directory.iterdir()
        if not path.name.startswith(".")
    }
    assert not list(directory.glob(".*.tmp"))
    assert not list(directory.glob(".*.previous"))
    assert not (directory / ".ref1.reference-provenance.lock").exists()


def test_publish_failure_restores_complete_prior_transaction(tmp_path, monkeypatch):
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"; output.mkdir()
    assert run(inventory, output, "--execute").returncode == 0
    directory = output / "ref1"
    original = {
        path.name: path.read_bytes()
        for path in directory.iterdir()
        if not path.name.startswith(".")
    }
    generated = {
        "artifacts": (directory / "ref1.reference_artifacts.tsv").read_bytes(),
        "contigs": (directory / "ref1.reference_contigs.tsv").read_bytes(),
        "summary": (directory / "ref1.reference_summary.tsv").read_bytes(),
    }
    real_replace = reference_provenance.os.replace
    publication_attempts = 0

    def fail_second_publication(source, destination):
        nonlocal publication_attempts
        if Path(source).name.endswith(".tmp"):
            publication_attempts += 1
            if publication_attempts == 2:
                raise OSError("synthetic publication failure")
        return real_replace(source, destination)

    monkeypatch.setattr(
        reference_provenance.os, "replace", fail_second_publication
    )

    with pytest.raises(OSError, match="synthetic publication failure"):
        reference_provenance.publish(output, "ref1", generated)

    assert original == {
        path.name: path.read_bytes()
        for path in directory.iterdir()
        if not path.name.startswith(".")
    }
    assert not list(directory.glob(".*.tmp"))
    assert not list(directory.glob(".*.previous"))
    assert not (directory / ".ref1.reference-provenance.lock").exists()


def test_broken_output_symlink_is_rejected_and_preserved(tmp_path):
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"
    directory = output / "ref1"
    directory.mkdir(parents=True)
    broken = directory / "ref1.reference_artifacts.tsv"
    broken.symlink_to(directory / "missing-foreign-target.tsv")

    result = run(inventory, output, "--execute")

    assert result.returncode == 2
    assert "incomplete" in result.stderr
    assert broken.is_symlink()
    assert not (directory / "ref1.reference_contigs.tsv").exists()
    assert not (directory / "ref1.reference_summary.tsv").exists()
