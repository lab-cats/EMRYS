import csv
import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "reference_provenance.py"
HEADER = ["reference_id", "artifact_id", "role", "path", "required", "expected_sha256", "provenance_source", "provenance_release", "notes"]
SPEC = importlib.util.spec_from_file_location(
    "norad_reference_provenance_faults",
    SCRIPT,
)
assert SPEC and SPEC.loader
PROVENANCE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROVENANCE
SPEC.loader.exec_module(PROVENANCE)


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


def publication_data(inventory: Path) -> dict[str, bytes]:
    raw, items = PROVENANCE.load_inventory(inventory, inventory.parent)
    return PROVENANCE.render(raw, PROVENANCE.observe(items))


def publication_paths(output_root: Path) -> dict[str, Path]:
    directory = output_root / "ref1"
    return {
        "artifacts": directory / "ref1.reference_artifacts.tsv",
        "contigs": directory / "ref1.reference_contigs.tsv",
        "summary": directory / "ref1.reference_summary.tsv",
    }


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


def test_input_mutation_after_observation_fails_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    fasta = tmp_path / "ref" / "genome.fa"
    real_observe = PROVENANCE.observe
    calls = 0

    def observe_then_mutate(items):
        nonlocal calls
        observations = real_observe(items)
        calls += 1
        if calls == 1:
            # Mutate after the first digest snapshot so the execute-time
            # refresh must reject evidence assembled from stale bytes.
            fasta.write_text(">1\nTGCA\n>MT\nAAA\n")
        return observations

    monkeypatch.setattr(PROVENANCE, "observe", observe_then_mutate)
    status = PROVENANCE.main(
        [
            "--inventory",
            str(inventory),
            "--base-dir",
            str(tmp_path),
            "--output-root",
            str(output),
            "--execute",
        ]
    )

    assert calls == 2
    assert status == 2
    assert not (output / "ref1").exists()


def test_publication_failure_restores_complete_reference_predecessor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    generated = publication_data(inventory)
    PROVENANCE.publish(output, "ref1", generated)
    finals = publication_paths(output)
    before = {key: path.read_bytes() for key, path in finals.items()}
    real_replace = PROVENANCE.os.replace
    failed = False

    def fail_second_publication(source, destination):
        nonlocal failed
        if (
            not failed
            and Path(destination) == finals["contigs"]
            and Path(source).name.endswith(".tmp")
        ):
            failed = True
            raise OSError("injected reference publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(PROVENANCE.os, "replace", fail_second_publication)
    with pytest.raises(OSError, match="reference publication"):
        PROVENANCE.publish(output, "ref1", generated)

    assert failed
    assert {key: path.read_bytes() for key, path in finals.items()} == before
    assert not [
        child for child in (output / "ref1").iterdir()
        if child.name.startswith(".")
    ]


def test_characterizes_reference_incomplete_rollback_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inventory = make_fixture(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    generated = publication_data(inventory)
    PROVENANCE.publish(output, "ref1", generated)
    finals = publication_paths(output)
    real_replace = PROVENANCE.os.replace
    publication_failed = False
    restoration_failed = False

    def fail_publication_and_restoration(source, destination):
        nonlocal publication_failed, restoration_failed
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not publication_failed
            and destination_path == finals["contigs"]
            and source_path.name.endswith(".tmp")
        ):
            publication_failed = True
            raise OSError("injected reference publication failure")
        if (
            publication_failed
            and not restoration_failed
            and destination_path == finals["artifacts"]
            and source_path.name.endswith(".previous")
        ):
            restoration_failed = True
            raise OSError("injected reference restoration failure")
        real_replace(source, destination)

    monkeypatch.setattr(
        PROVENANCE.os,
        "replace",
        fail_publication_and_restoration,
    )
    with pytest.raises(OSError, match="reference restoration"):
        PROVENANCE.publish(output, "ref1", generated)

    directory = output / "ref1"
    assert publication_failed and restoration_failed
    assert len(list(directory.glob(".*.previous"))) == 3
    # Known TG-02 gap: recovery bytes survive, but the owned lock and a
    # recovery marker are removed even though restoration was incomplete.
    assert not (directory / ".ref1.reference-provenance.lock").exists()
    assert not list(directory.glob("*.RECOVERY.txt"))
