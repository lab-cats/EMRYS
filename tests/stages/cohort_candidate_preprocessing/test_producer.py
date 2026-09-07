"""Focused transaction tests for the private Step 08 Python producer."""

from __future__ import annotations

import os
import signal
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from emrys.contracts.scientific_evidence import step08
from emrys.libraries.alignments.orientation import ORIENTATIONS
from emrys.libraries.validation.mpileup import RECEIPT_HEADER
from emrys.libraries.validation.tsv import write_rows
from emrys.stages.cohort_candidate_preprocessing import producer


def _write_tsv(path: Path, header: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as stream:
        write_rows(stream, header, rows)


def _fixture(tmp_path: Path) -> tuple[list[str], dict[str, Path]]:
    sample = tmp_path / "samples.tsv"
    partition = tmp_path / "partitions.tsv"
    annotation = tmp_path / "annotation.gtf"
    r_script = tmp_path / "step08.R"
    sample.write_text(
        "sample_id\tr1_fastq\tr2_fastq\tstrandedness\tcondition\treplicate\n"
        "S1\tr1.fq.gz\tr2.fq.gz\tforward\tcontrol\t1\n"
    )
    partition.write_text(
        "partition_id\tselector_type\tselector_value\np1\tregion\tchr1\n"
    )
    annotation.write_text('chr1\ttest\tgene\t1\t100\t.\t+\t.\tgene_id "g1";\n')
    r_script.write_text("# test-owned stand-in; subprocess is injected\n")
    step07 = tmp_path / "step07" / "cohort" / "p1"
    step07.mkdir(parents=True)
    vcfs: list[Path] = []
    vcf_text = (
        "##fileformat=VCFv4.2\n"
        "##INFO=<ID=AD,Number=R,Type=Integer,Description=AD>\n"
        "##FORMAT=<ID=DP,Number=1,Type=Integer,Description=DP>\n"
        "##FORMAT=<ID=AD,Number=R,Type=Integer,Description=AD>\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\n"
        "chr1\t10\t.\tA\tG\t60\tPASS\tAD=8,2\tDP:AD\t10:8,2\n"
    )
    for orientation in ORIENTATIONS:
        path = step07 / f"cohort.p1.{orientation}.mpileup.vcf"
        path.write_text(vcf_text)
        vcfs.append(path)
    sample_hash, partition_hash = producer.digest(sample), producer.digest(partition)
    receipt = step07 / "cohort.p1.step07_outputs.tsv"
    _write_tsv(
        receipt,
        RECEIPT_HEADER,
        [
            {
                "cohort_id": "cohort",
                "partition_id": "p1",
                "selector_type": "region",
                "selector_value": "chr1",
                "orientation": orientation,
                "vcf_path": str(vcf),
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_sha256": partition_hash,
                "sample_count": "1",
                "vcf_record_count": "1",
            }
            for orientation, vcf in zip(ORIENTATIONS, vcfs, strict=True)
        ],
    )
    paths = {
        "sample": sample,
        "partition": partition,
        "annotation": annotation,
        "r_script": r_script,
        "step07": tmp_path / "step07",
        "output": tmp_path / "results",
        "qc": tmp_path / "qc",
    }
    arguments = [
        "--cohort-id",
        "cohort",
        "--sample-manifest",
        str(sample),
        "--partition-manifest",
        str(partition),
        "--step07-root",
        str(paths["step07"]),
        "--annotation-gtf",
        str(annotation),
        "--output-root",
        str(paths["output"]),
        "--qc-root",
        str(paths["qc"]),
        "--rscript-bin",
        "/usr/bin/true",
        "--r-script",
        str(r_script),
    ]
    return arguments, paths


def _outputs(command: list[str]) -> None:
    values = dict(zip(command[2::2], command[3::2], strict=True))
    sample_hash = values["--sample-manifest-sha256"]
    partition_hash = values["--partition-manifest-sha256"]
    annotation_hash = values["--annotation-gtf-sha256"]
    receipt_spelling = (
        f"{values['--step07-root']}/cohort/p1/cohort.p1.step07_outputs.tsv"
    )
    receipt = Path(receipt_spelling)
    receipt_hash = producer.digest(receipt)
    sites_rows: list[dict[str, str]] = []
    input_rows: list[dict[str, str]] = []
    for index, orientation in enumerate(ORIENTATIONS, start=1):
        vcf_spelling = (
            f"{values['--step07-root']}/cohort/p1/cohort.p1.{orientation}.mpileup.vcf"
        )
        vcf = Path(vcf_spelling)
        sites_rows.append(
            {
                "partition_id": "p1",
                "candidate_id": f"candidate-{index}",
                "orientation": orientation,
                "chromosome": "chr1",
                "position": "10",
                "alt_index": "1",
                "genomic_ref": "A",
                "genomic_alt": "G",
                "rna_ref": "A",
                "rna_alt": "G",
                "annotation_strand": "+",
                "gene_ids": "g1",
                "transcript_ids": "tx1",
                "is_cds": "TRUE",
                "is_five_prime_utr": "FALSE",
                "is_three_prime_utr": "FALSE",
                "is_exon": "TRUE",
                "is_intron": "FALSE",
                "qual": "60",
                "filter": "PASS",
                "info_alt_depth": "2",
                "orientation_policy": "legacy_provisional_v1",
                "DP__S1": "10",
                "AD__S1": "2",
                "AF__S1": "0.2",
            }
        )
        input_rows.append(
            {
                "cohort_id": "cohort",
                "partition_id": "p1",
                "selector_type": "region",
                "selector_value": "chr1",
                "orientation": orientation,
                "step07_receipt_path": receipt_spelling,
                "step07_receipt_sha256": receipt_hash,
                "vcf_path": vcf_spelling,
                "vcf_sha256": producer.digest(vcf),
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_sha256": partition_hash,
                "annotation_gtf": values["--annotation-gtf"],
                "annotation_gtf_sha256": annotation_hash,
                "sample_count": "1",
                "declared_vcf_record_count": "1",
                "observed_vcf_record_count": "1",
                "observed_alt_allele_count": "1",
                "supported_snv_count": "1",
                "skipped_symbolic_count": "0",
                "skipped_non_snv_count": "0",
                "published_candidate_count": "1",
                "orientation_policy": "legacy_provisional_v1",
            }
        )
    _write_tsv(
        Path(values["--sites-output"]),
        step08.sample_block_header(step08.STEP08_METADATA_HEADER, ["S1"]),
        sites_rows,
    )
    _write_tsv(Path(values["--inputs-output"]), step08.STEP08_INPUTS_HEADER, input_rows)
    summary = {
        "cohort_id": "cohort",
        "partition_count": "1",
        "step07_receipt_count": "1",
        "input_vcf_count": "2",
        "sample_count": "1",
        "observed_vcf_record_count": "2",
        "observed_alt_allele_count": "2",
        "supported_snv_count": "2",
        "skipped_symbolic_count": "0",
        "skipped_non_snv_count": "0",
        "published_candidate_count": "2",
        "sample_manifest_sha256": sample_hash,
        "partition_manifest_sha256": partition_hash,
        "annotation_gtf": values["--annotation-gtf"],
        "annotation_gtf_sha256": annotation_hash,
        "orientation_policy": "legacy_provisional_v1",
    }
    _write_tsv(
        Path(values["--summary-output"]), step08.STEP08_SUMMARY_HEADER, [summary]
    )


class FakeProcess:
    def __init__(
        self,
        command: list[str],
        *,
        status: int = 0,
        interrupt: bool = False,
        mutate: Callable[[], None] | None = None,
    ) -> None:
        self.status, self.terminated = status, False
        if not status and not interrupt:
            _outputs(command)
            if mutate is not None:
                mutate()
        self.interrupt = interrupt

    def wait(self) -> int:
        if self.interrupt:
            os.kill(os.getpid(), signal.SIGTERM)
        return self.status

    def poll(self) -> int | None:
        return None if not self.terminated else -signal.SIGTERM

    def send_signal(self, _signum: int) -> None:
        self.terminated = True


def _inject_process(
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: int = 0,
    interrupt: bool = False,
    mutate: Callable[[], None] | None = None,
) -> list[FakeProcess]:
    processes: list[FakeProcess] = []

    def launch(command: list[str], **_kwargs: Any) -> FakeProcess:
        process = FakeProcess(
            command,
            status=status,
            interrupt=interrupt,
            mutate=mutate,
        )
        processes.append(process)
        return process

    monkeypatch.setattr(producer.subprocess, "Popen", launch)
    return processes


def _finals(paths: dict[str, Path]) -> tuple[Path, Path, Path]:
    return (
        paths["output"] / "cohort/cohort.step08_sites.tsv",
        paths["qc"] / "cohort.step08_summary.tsv",
        paths["output"] / "cohort/cohort.step08_inputs.tsv",
    )


def test_dry_run_validates_without_writing_or_invoking_r(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )
    assert producer.main(arguments) == 0
    assert not paths["output"].exists()
    assert not paths["qc"].exists()


def test_execute_and_no_clobber_preserve_receipt_last_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    _inject_process(monkeypatch)
    links: list[str] = []
    original_link = os.link

    def record_link(source: Path, destination: Path) -> None:
        links.append(Path(destination).name)
        original_link(source, destination)

    monkeypatch.setattr(producer.os, "link", record_link)
    assert producer.main([*arguments, "--no-clobber", "--execute"]) == 0
    assert links == [
        "cohort.step08_sites.tsv",
        "cohort.step08_summary.tsv",
        "cohort.step08_inputs.tsv",
    ]
    assert all(path.is_file() for path in _finals(paths))
    assert not list(paths["output"].rglob(".*.step08.*"))
    assert not list(paths["qc"].glob(".*.step08.*"))


def test_complete_no_clobber_set_is_unchanged_without_r(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    _inject_process(monkeypatch)
    assert producer.main([*arguments, "--execute"]) == 0
    before = [path.read_bytes() for path in _finals(paths)]
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )
    assert producer.main([*arguments, "--no-clobber", "--execute"]) == 1
    assert [path.read_bytes() for path in _finals(paths)] == before


def test_publication_failure_restores_complete_predecessor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    _inject_process(monkeypatch)
    assert producer.main([*arguments, "--execute"]) == 0
    before = [path.read_bytes() for path in _finals(paths)]
    original_replace = Path.replace

    def fail_summary(source: Path, destination: Path) -> Path:
        if source.name.endswith("summary.tmp.tsv"):
            raise OSError("injected publication failure")
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "replace", fail_summary)
    assert producer.main([*arguments, "--execute"]) == 1
    assert [path.read_bytes() for path in _finals(paths)] == before
    assert not list(paths["output"].rglob(".*.step08.*"))


def test_input_mutation_during_r_refuses_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    _inject_process(
        monkeypatch,
        mutate=lambda: paths["annotation"].write_text("mutated annotation\n"),
    )

    assert producer.main([*arguments, "--execute"]) == 1
    assert not any(path.exists() for path in _finals(paths))
    assert not list(paths["output"].rglob(".*.step08.*"))


def test_postpublication_validation_failure_restores_predecessor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    _inject_process(monkeypatch)
    assert producer.main([*arguments, "--execute"]) == 0
    before = [path.read_bytes() for path in _finals(paths)]
    original_validate = producer.validate_outputs

    def fail_final(context: producer.Context, prefix: str = "") -> None:
        original_validate(context, prefix)
        if not prefix:
            raise producer.ProducerError("injected postpublication failure")

    monkeypatch.setattr(producer, "validate_outputs", fail_final)
    assert producer.main([*arguments, "--execute"]) == 1
    assert [path.read_bytes() for path in _finals(paths)] == before
    assert not list(paths["output"].rglob(".*.step08.*"))


def test_failed_restore_retains_lock_and_backup_for_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    _inject_process(monkeypatch)
    assert producer.main([*arguments, "--execute"]) == 0
    original_replace = Path.replace

    def fail_publication_and_restore(source: Path, destination: Path) -> Path:
        if source.name.endswith("summary.tmp.tsv") or (
            source.name.endswith("previous.sites.tsv")
            and destination.name.endswith("step08_sites.tsv")
        ):
            raise OSError("injected unrecoverable move")
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "replace", fail_publication_and_restore)
    assert producer.main([*arguments, "--execute"]) == 1
    token = str(os.getpid())
    cohort = paths["output"] / "cohort"
    assert (cohort / ".cohort.step08.lock/owner").is_file()
    assert (cohort / f".cohort.step08.{token}.previous.sites.tsv").is_file()


def test_ambiguous_lock_and_incomplete_set_are_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    cohort = paths["output"] / "cohort"
    lock = cohort / ".cohort.step08.lock"
    lock.mkdir(parents=True)
    (lock / "owner").write_text("run_token\tforeign\npid\t99\n")
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )
    assert producer.main([*arguments, "--execute"]) == 1
    assert (lock / "owner").read_text().startswith("run_token\tforeign")
    (lock / "owner").unlink()
    lock.rmdir()
    _finals(paths)[0].write_text("foreign\n")
    assert producer.main([*arguments, "--execute"]) == 1
    assert _finals(paths)[0].read_text() == "foreign\n"


def test_term_cleans_owned_state_and_returns_143(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    processes = _inject_process(monkeypatch, interrupt=True)
    assert producer.main([*arguments, "--execute"]) == 143
    assert processes[0].terminated
    assert not list(paths["output"].rglob(".*.step08.*"))


def test_term_during_child_spawn_is_deferred_and_forwarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    child: FakeProcess | None = None

    def launch(command: list[str], **_kwargs: Any) -> FakeProcess:
        nonlocal child
        child = FakeProcess(command)
        os.kill(os.getpid(), signal.SIGTERM)
        return child

    monkeypatch.setattr(producer.subprocess, "Popen", launch)

    assert producer.main([*arguments, "--execute"]) == 143
    assert child is not None and child.terminated
    assert not list(paths["output"].rglob(".*.step08.*"))


def test_no_clobber_residue_fails_in_dry_run_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    cohort = paths["output"] / "cohort"
    cohort.mkdir(parents=True)
    residue = cohort / ".cohort.step08.abandoned.sites.tmp.tsv"
    residue.write_text("operator evidence\n")
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )
    assert producer.main([*arguments, "--no-clobber"]) == 1
    assert residue.read_text() == "operator evidence\n"


def test_step07_receipt_rejects_blank_physical_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    receipt = paths["step07"] / "cohort/p1/cohort.p1.step07_outputs.tsv"
    lines = receipt.read_text().splitlines(keepends=True)
    receipt.write_text("".join((lines[0], "\n", *lines[1:])))
    monkeypatch.setattr(
        producer.subprocess, "Popen", lambda *_a, **_k: pytest.fail("R invoked")
    )

    assert producer.main(arguments) == 1


def test_annotation_path_spelling_is_preserved_in_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    replacements = {
        str(paths["sample"]): "samples.tsv",
        str(paths["partition"]): "partitions.tsv",
        str(paths["step07"]): "./step07",
        str(paths["annotation"]): "./annotation.gtf",
        str(paths["output"]): "results",
        str(paths["qc"]): "qc",
        str(paths["r_script"]): "step08.R",
    }
    relative_arguments = [replacements.get(value, value) for value in arguments]
    _inject_process(monkeypatch)

    assert producer.main([*relative_arguments, "--execute"]) == 0
    _, inputs = producer.report.read_tsv(_finals(paths)[2])
    _, summary = producer.report.read_tsv(_finals(paths)[1])
    assert {row["annotation_gtf"] for row in inputs} == {"./annotation.gtf"}
    assert summary[0]["annotation_gtf"] == "./annotation.gtf"
