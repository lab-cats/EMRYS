"""Focused parity and transaction tests for the private Step 07 producer."""

from __future__ import annotations

import gzip
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from emrys.libraries.alignments.orientation import ORIENTATIONS
from emrys.libraries.validation import mpileup, sha256_file
from emrys.stages.partitioned_cohort_mpileup import producer


FAKE_BCFTOOLS = r"""#!/bin/bash
set -euo pipefail

command_name="${1:-}"
shift || true

if [[ -n "${FAKE_BCFTOOLS_LOG:-}" ]]; then
    rendered="$command_name"
    for argument in "$@"; do
        printf -v quoted '%q' "$argument"
        rendered+=" $quoted"
    done
    printf '%s\n' "$rendered" >>"$FAKE_BCFTOOLS_LOG"
fi

case "$command_name" in
    mpileup)
        orientation=unknown
        for argument in "$@"; do
            case "$argument" in
                *.FWD_like.bam) orientation=FWD_like ;;
                *.REV_like.bam) orientation=REV_like ;;
            esac
        done
        if [[ "${FAKE_FAIL_STAGE:-}" == "mpileup_${orientation}" ]]; then
            exit 41
        fi
        printf 'ORIENTATION=%s\n' "$orientation"
        ;;
    filter)
        output=""
        while [[ $# -gt 0 ]]; do
            if [[ "$1" == -o ]]; then
                output="$2"
                shift 2
            else
                shift
            fi
        done
        [[ -n "$output" ]] || exit 42
        stream="$(cat)"
        orientation="${stream#ORIENTATION=}"
        orientation="${orientation%%$'\n'*}"
        if [[ "${FAKE_FAIL_STAGE:-}" == "filter_${orientation}" ]]; then
            exit 43
        fi
        IFS=',' read -r -a samples <<<"${FAKE_SAMPLES:-sample_A,sample_B}"
        {
            printf '##fileformat=VCFv4.2\n'
            printf '##INFO=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            printf '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Depth">\n'
            printf '##FORMAT=<ID=AD,Number=R,Type=Integer,Description="Allele depth">\n'
            printf '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT'
            for sample in "${samples[@]}"; do printf '\t%s' "$sample"; done
            printf '\n'
            if [[ "${FAKE_HEADER_ONLY:-0}" != 1 ]]; then
                printf 'chr1\t10\t.\tA\tG\t60\tPASS\tAD=20,4\tDP:AD'
                for _sample in "${samples[@]}"; do printf '\t12:10,2'; done
                printf '\n'
            fi
        } >"$output"
        ;;
    view)
        mode="${1:-}"
        path="${2:-}"
        [[ -s "$path" ]] || exit 44
        if [[ "$mode" == -h && -n "${FAKE_OBSERVE_FWD:-}" &&
              "$path" == "$FAKE_OBSERVE_FWD" ]]; then
            [[ -s "${FAKE_OBSERVE_REV:?}" ]]
            [[ ! -e "${FAKE_OBSERVE_RECEIPT:?}" ]]
            printf 'fwd-rev-validated-before-receipt\n' >"${FAKE_OBSERVATION:?}"
        fi
        case "$mode" in
            -h) awk '/^#/' "$path" ;;
            -H) awk '!/^#/' "$path" ;;
            *) exit 45 ;;
        esac
        ;;
    query)
        [[ "${1:-}" == -l ]] || exit 46
        awk -F '\t' '/^#CHROM/ { for (i = 10; i <= NF; i++) print $i; found=1 }
            END { if (!found) exit 1 }' "${2:-}"
        ;;
    --version)
        printf 'bcftools 1.21-fake\n'
        ;;
    *) exit 47 ;;
esac
"""


@dataclass(frozen=True)
class Fixture:
    arguments: tuple[str, ...]
    sample_manifest: Path
    partition_manifest: Path
    reference: Path
    orientation_root: Path
    output_root: Path
    bcftools: Path
    log: Path

    @property
    def output_dir(self) -> Path:
        return self.output_root / "cohort_A/part_A"

    @property
    def outputs(self) -> tuple[Path, Path, Path]:
        stem = self.output_dir / "cohort_A.part_A"
        return (
            Path(f"{stem}.FWD_like.mpileup.vcf"),
            Path(f"{stem}.REV_like.mpileup.vcf"),
            Path(f"{stem}.step07_outputs.tsv"),
        )

    @property
    def canonical_vcfs(self) -> tuple[Path, Path]:
        return tuple(
            self.output_root.parent / "published" / path.name
            for path in self.outputs[:2]
        )

    def roster(self, selector: Path | None = None) -> tuple[Path, ...]:
        paths = [
            self.sample_manifest,
            self.partition_manifest,
            self.reference,
            Path(f"{self.reference}.fai"),
        ]
        if selector is not None:
            paths.append(selector)
        for sample in ("sample_A", "sample_B"):
            for orientation in ORIENTATIONS:
                bam = self.orientation_root / sample / f"{sample}.{orientation}.bam"
                paths.extend((bam, Path(f"{bam}.bai")))
        return tuple(paths)


@pytest.fixture
def step07(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Fixture:
    sample_manifest = tmp_path / "samples.tsv"
    partition_manifest = tmp_path / "partitions.tsv"
    reference = tmp_path / "reference.fa"
    orientation_root = tmp_path / "orientation"
    output_root = tmp_path / "output"
    bcftools = tmp_path / "fake-bcftools"
    log = tmp_path / "bcftools.log"
    sample_manifest.write_text(
        "sample_id\tcondition\nsample_A\tcontrol\nsample_B\ttreatment\n"
    )
    partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\npart_A\tregion\tchr1\n"
    )
    reference.write_text(">chr1\n" + "A" * 100 + "\n")
    Path(f"{reference}.fai").write_text("chr1\t100\t6\t100\t101\n")
    for sample in ("sample_A", "sample_B"):
        directory = orientation_root / sample
        directory.mkdir(parents=True)
        for orientation in ORIENTATIONS:
            bam = directory / f"{sample}.{orientation}.bam"
            bam.write_text("fake bam\n")
            Path(f"{bam}.bai").write_text("fake bai\n")
    bcftools.write_text(FAKE_BCFTOOLS)
    bcftools.chmod(0o755)
    monkeypatch.setenv("FAKE_BCFTOOLS_LOG", str(log))
    for name in (
        "FAKE_FAIL_STAGE",
        "FAKE_HEADER_ONLY",
        "FAKE_OBSERVATION",
        "FAKE_OBSERVE_FWD",
        "FAKE_OBSERVE_REV",
        "FAKE_OBSERVE_RECEIPT",
        "FAKE_SAMPLES",
    ):
        monkeypatch.delenv(name, raising=False)
    destination = output_root / "cohort_A/part_A"
    destination.mkdir(parents=True)
    stem = "cohort_A.part_A"
    arguments = (
        "--cohort-id",
        "cohort_A",
        "--sample-manifest",
        str(sample_manifest),
        "--partition-manifest",
        str(partition_manifest),
        "--partition-id",
        "part_A",
        "--orientation-root",
        str(orientation_root),
        "--reference-fasta",
        str(reference),
        "--fwd-vcf-output",
        str(destination / f"{stem}.FWD_like.mpileup.vcf"),
        "--rev-vcf-output",
        str(destination / f"{stem}.REV_like.mpileup.vcf"),
        "--receipt-output",
        str(destination / f"{stem}.step07_outputs.tsv"),
        "--fwd-vcf-final",
        str(tmp_path / "published" / f"{stem}.FWD_like.mpileup.vcf"),
        "--rev-vcf-final",
        str(tmp_path / "published" / f"{stem}.REV_like.mpileup.vcf"),
        "--bcftools-bin",
        str(bcftools),
    )
    return Fixture(
        arguments,
        sample_manifest,
        partition_manifest,
        reference,
        orientation_root,
        output_root,
        bcftools,
        log,
    )


def _calls(path: Path) -> list[list[str]]:
    return [shlex.split(line) for line in path.read_text().splitlines()]


def test_worker_preserves_pipeline_arguments_and_final_path_receipt(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    fwd, rev, receipt = step07.outputs
    observation = step07.output_root.parent / "publication-observation"
    monkeypatch.setenv("FAKE_OBSERVE_FWD", str(fwd))
    monkeypatch.setenv("FAKE_OBSERVE_REV", str(rev))
    monkeypatch.setenv("FAKE_OBSERVE_RECEIPT", str(receipt))
    monkeypatch.setenv("FAKE_OBSERVATION", str(observation))

    assert producer.main(step07.arguments) == 0

    calls = _calls(step07.log)
    pileups = [call for call in calls if call[0] == "mpileup"]
    filters = [call for call in calls if call[0] == "filter"]
    assert len(pileups) == len(filters) == 2
    for index, orientation in enumerate(ORIENTATIONS):
        expected_bams = [
            str(step07.orientation_root / sample / f"{sample}.{orientation}.bam")
            for sample in ("sample_A", "sample_B")
        ]
        assert pileups[index] == [
            "mpileup",
            "-Ou",
            "-f",
            str(step07.reference),
            "-r",
            "chr1",
            "-d",
            "10000000",
            "-I",
            "-a",
            producer.ANNOTATIONS,
            *expected_bams,
        ]
        assert filters[index][:5] == [
            "filter",
            "-i",
            producer.DEFAULT_FILTER,
            "-Ov",
            "-o",
        ]
        assert filters[index][-1] == "-"
    assert observation.read_text() == "fwd-rev-validated-before-receipt\n"
    assert all(path.is_file() for path in step07.outputs)
    lines = receipt.read_text().splitlines()
    assert tuple(lines[0].split("\t")) == mpileup.RECEIPT_HEADER
    rows = [line.split("\t") for line in lines[1:]]
    assert [row[4] for row in rows] == list(ORIENTATIONS)
    assert [row[5] for row in rows] == [str(path) for path in step07.canonical_vcfs]
    assert not any(path.exists() for path in step07.canonical_vcfs)
    assert {row[6] for row in rows} == {sha256_file(step07.sample_manifest)}
    assert {row[7] for row in rows} == {sha256_file(step07.partition_manifest)}
    assert [row[8:] for row in rows] == [["2", "1"], ["2", "1"]]
    assert not list(step07.output_dir.glob(".cohort_A.part_A.step07.*"))


@pytest.mark.parametrize(
    "failure",
    (
        "mpileup_FWD_like",
        "filter_FWD_like",
        "mpileup_REV_like",
        "filter_REV_like",
    ),
)
def test_either_pipeline_process_failure_rejects_scientific_completion(
    step07: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    unrelated = step07.output_dir / "unrelated.txt"
    unrelated.write_text("preserve\n")
    monkeypatch.setenv("FAKE_FAIL_STAGE", failure)

    assert producer.main(step07.arguments) == 1

    assert not step07.outputs[2].exists()
    assert unrelated.read_text() == "preserve\n"


@pytest.mark.parametrize("failure", ("spawn", "exit"))
def test_filter_failure_returns_to_runner_without_waiting_for_upstream(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    source = MagicMock()
    source.__enter__.return_value = source
    source.wait.side_effect = AssertionError("worker waited for failed pipeline")
    source.__exit__.side_effect = lambda *_arguments: source.wait()
    consumer = MagicMock()
    consumer.wait.return_value = 1
    monkeypatch.setattr(
        producer.subprocess,
        "Popen",
        Mock(
            side_effect=[
                source,
                OSError("filter spawn failed") if failure == "spawn" else consumer,
            ]
        ),
    )

    assert producer.main(step07.arguments) == 1
    source.stdout.close.assert_called_once()
    source.wait.assert_not_called()
    assert not step07.outputs[2].exists()


def test_header_only_and_gzip_regions_file_are_valid(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = step07.partition_manifest.parent / "selectors/target.bed.gz"
    selector.parent.mkdir()
    with gzip.open(selector, "wt") as stream:
        stream.write("chr1\t0\t100\n")
    step07.partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\n"
        "part_A\tregions_file\tselectors/target.bed.gz\n"
    )
    monkeypatch.setenv("FAKE_HEADER_ONLY", "1")

    assert producer.main(step07.arguments) == 0

    pileups = [call for call in _calls(step07.log) if call[0] == "mpileup"]
    assert all(
        call[call.index("-R") + 1] == str(selector.resolve()) for call in pileups
    )
    rows = [line.split("\t") for line in step07.outputs[2].read_text().splitlines()[1:]]
    assert {row[3] for row in rows} == {"selectors/target.bed.gz"}
    assert {row[9] for row in rows} == {"0"}


@pytest.mark.parametrize(
    "invalid",
    (
        "fai_zero",
        "unselected_partition",
        "bed_bounds",
        "bed_unicode_digit",
        "blank_sample_row",
        "truncated_gzip",
    ),
)
def test_rejects_invalid_reference_partition_or_selector_state(
    step07: Fixture, invalid: str
) -> None:
    if invalid == "fai_zero":
        Path(f"{step07.reference}.fai").write_text("chr1\t0\t6\t100\t101\n")
    elif invalid == "unselected_partition":
        step07.partition_manifest.write_text(
            "partition_id\tselector_type\tselector_value\n"
            "part_A\tregion\tchr1\n"
            "duplicate\tregion\tchr1\n"
            "duplicate\tregion\tchr1\n"
        )
    elif invalid == "bed_bounds":
        selector = step07.partition_manifest.parent / "target.bed"
        selector.write_text("chr1\t0\t101\n")
        step07.partition_manifest.write_text(
            "partition_id\tselector_type\tselector_value\n"
            "part_A\tregions_file\ttarget.bed\n"
        )
    elif invalid == "bed_unicode_digit":
        selector = step07.partition_manifest.parent / "target.bed"
        selector.write_text("chr1\t²\t3\n")
        step07.partition_manifest.write_text(
            "partition_id\tselector_type\tselector_value\n"
            "part_A\tregions_file\ttarget.bed\n"
        )
    elif invalid == "blank_sample_row":
        step07.sample_manifest.write_text(
            "sample_id\tcondition\nsample_A\tcontrol\n\nsample_B\ttreatment\n"
        )
    else:
        selector = step07.partition_manifest.parent / "target.bed.gz"
        selector.write_bytes(gzip.compress(b"chr1\t0\t100\n")[:-5])
        step07.partition_manifest.write_text(
            "partition_id\tselector_type\tselector_value\n"
            "part_A\tregions_file\ttarget.bed.gz\n"
        )

    assert producer.main(step07.arguments) == 1
    assert not any(path.exists() for path in step07.outputs)
    assert not step07.log.exists()


@pytest.mark.parametrize("index", (4, 5))
def test_rejects_missing_bam_or_index(step07: Fixture, index: int) -> None:
    step07.roster()[index].unlink()

    assert producer.main(step07.arguments) == 1
    assert not any(path.exists() for path in step07.outputs)
    assert not step07.log.exists()


@pytest.mark.parametrize("state", ("missing", "nonexecutable", "relative"))
def test_rejects_unusable_explicit_tool(step07: Fixture, state: str) -> None:
    arguments = step07.arguments
    if state == "missing":
        step07.bcftools.unlink()
    elif state == "nonexecutable":
        step07.bcftools.chmod(0o644)
    else:
        arguments = (*arguments[:-1], step07.bcftools.name)

    assert producer.main(arguments) == 1
    assert not any(path.exists() for path in step07.outputs)


def test_vcf_sample_order_mismatch_prevents_receipt(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_SAMPLES", "sample_B,sample_A")

    assert producer.main(step07.arguments) == 1

    assert not step07.outputs[2].exists()
