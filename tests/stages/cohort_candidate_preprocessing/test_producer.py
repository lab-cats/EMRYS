"""Scientific computation checks for the private Step 08 worker."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
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
        "--sites-output",
        str(paths["output"] / "cohort/cohort.step08_sites.tsv"),
        "--inputs-output",
        str(paths["output"] / "cohort/cohort.step08_inputs.tsv"),
        "--summary-output",
        str(paths["qc"] / "cohort.step08_summary.tsv"),
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


def _inject_process(
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: int = 0,
    mutate: Callable[[], None] | None = None,
) -> list[list[str]]:
    commands: list[list[str]] = []

    def run(command: list[str]) -> Any:
        commands.append(command)
        if not status:
            _outputs(command)
            if mutate is not None:
                mutate()
        return SimpleNamespace(returncode=status)

    monkeypatch.setattr(producer.subprocess, "run", run)
    return commands


def _finals(paths: dict[str, Path]) -> tuple[Path, Path, Path]:
    return (
        paths["output"] / "cohort/cohort.step08_sites.tsv",
        paths["qc"] / "cohort.step08_summary.tsv",
        paths["output"] / "cohort/cohort.step08_inputs.tsv",
    )


def test_worker_computes_all_scientific_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    commands = _inject_process(monkeypatch)
    assert producer.main(arguments) == 0
    assert len(commands) == 1
    values = dict(zip(commands[0][2::2], commands[0][3::2], strict=True))
    assert tuple(
        Path(values[key])
        for key in ("--sites-output", "--summary-output", "--inputs-output")
    ) == _finals(paths)
    assert all(path.is_file() for path in _finals(paths))


@pytest.mark.parametrize("fault", ("r-failure", "bad-count"))
def test_worker_rejects_r_failure_or_invalid_scientific_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    arguments, paths = _fixture(tmp_path)

    def corrupt_summary() -> None:
        path = _finals(paths)[1]
        header, rows = producer.report.read_tsv(path)
        rows[0]["published_candidate_count"] = "99"
        _write_tsv(path, tuple(header), rows)

    _inject_process(
        monkeypatch,
        status=73 if fault == "r-failure" else 0,
        mutate=corrupt_summary if fault == "bad-count" else None,
    )
    assert producer.main(arguments) == 1


def test_step07_receipt_rejects_blank_physical_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments, paths = _fixture(tmp_path)
    receipt = paths["step07"] / "cohort/p1/cohort.p1.step07_outputs.tsv"
    lines = receipt.read_text().splitlines(keepends=True)
    receipt.write_text("".join((lines[0], "\n", *lines[1:])))
    monkeypatch.setattr(
        producer.subprocess, "run", lambda *_a, **_k: pytest.fail("R invoked")
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

    assert producer.main(relative_arguments) == 0
    _, inputs = producer.report.read_tsv(_finals(paths)[2])
    _, summary = producer.report.read_tsv(_finals(paths)[1])
    assert {row["annotation_gtf"] for row in inputs} == {"./annotation.gtf"}
    assert summary[0]["annotation_gtf"] == "./annotation.gtf"
