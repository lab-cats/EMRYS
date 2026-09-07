"""Focused parity and transaction tests for the private Step 07 producer."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from emrys.libraries.alignments.orientation import ORIENTATIONS
from emrys.libraries.validation import mpileup, sha256_file
from emrys.stages.partitioned_cohort_mpileup import producer


FAKE_BCFTOOLS = r"""#!/bin/bash
set -euo pipefail

command_name="${1:-}"
shift || true

[[ -z "${EMRYS_STEP07_INPUT_IDENTITY_SHA256:-}" ]] || exit 48

if [[ -n "${FAKE_BCFTOOLS_LOG:-}" ]]; then
    rendered="$command_name"
    for argument in "$@"; do
        printf -v quoted '%q' "$argument"
        rendered+=" $quoted"
    done
    printf '%s\n' "$rendered" >>"$FAKE_BCFTOOLS_LOG"
fi

terminated() {
    if [[ -n "${FAKE_TERM_LOG:-}" ]]; then
        printf '%s\n' "$command_name" >>"$FAKE_TERM_LOG"
    fi
    exit 143
}
trap terminated TERM

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
        if [[ -n "${FAKE_MUTATE_PATH:-}" &&
              "${FAKE_MUTATE_ORIENTATION:-FWD_like}" == "$orientation" ]]; then
            printf '# controlled mutation\n' >>"$FAKE_MUTATE_PATH"
        fi
        if [[ -n "${FAKE_BARRIER_READY:-}" && "$orientation" == FWD_like ]]; then
            printf 'ready\n' >"$FAKE_BARRIER_READY"
            while [[ ! -e "${FAKE_BARRIER_RELEASE:-}" ]]; do
                sleep 0.02
            done
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
        if [[ -n "${FAKE_FILTER_READY:-}" ]]; then
            printf 'ready\n' >"$FAKE_FILTER_READY"
        fi
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
        if [[ "${FAKE_FAIL_FINAL_VIEW:-0}" == 1 && "$mode" == -h &&
              "$path" != *.tmp.vcf ]]; then
            exit 49
        fi
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
    def finals(self) -> tuple[Path, Path, Path]:
        stem = self.output_dir / "cohort_A.part_A"
        return (
            Path(f"{stem}.FWD_like.mpileup.vcf"),
            Path(f"{stem}.REV_like.mpileup.vcf"),
            Path(f"{stem}.step07_outputs.tsv"),
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
        producer.INPUT_IDENTITY_ENV,
        "EMRYS_REQUIRE_BOUND_SHA256",
        "EMRYS_RUN_TOKEN",
        "SLURM_JOB_ID",
        "FAKE_BARRIER_READY",
        "FAKE_BARRIER_RELEASE",
        "FAKE_FAIL_STAGE",
        "FAKE_FAIL_FINAL_VIEW",
        "FAKE_FILTER_READY",
        "FAKE_HEADER_ONLY",
        "FAKE_MUTATE_PATH",
        "FAKE_MUTATE_ORIENTATION",
        "FAKE_OBSERVATION",
        "FAKE_OBSERVE_FWD",
        "FAKE_OBSERVE_REV",
        "FAKE_OBSERVE_RECEIPT",
        "FAKE_SAMPLES",
        "FAKE_TERM_LOG",
    ):
        monkeypatch.delenv(name, raising=False)
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
        "--output-root",
        str(output_root),
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


def _identity(paths: tuple[Path, ...]) -> str:
    digest = hashlib.sha256(b"emrys.step07-input-identity.v1\0")
    for path in paths:
        digest.update(os.fsencode(f"{path}\0{sha256_file(path)}\0"))
    return digest.hexdigest()


def _assert_clean(fixture: Fixture) -> None:
    assert not any(path.exists() for path in fixture.finals)
    if fixture.output_dir.is_dir():
        assert not list(fixture.output_dir.glob(".cohort_A.part_A.step07.*"))


def test_dry_run_is_no_write_and_prints_the_exact_plan(
    step07: Fixture,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMRYS_RUN_TOKEN", "dryrun001")
    assert producer.main(step07.arguments) == 0

    output = capsys.readouterr().out
    assert "Mode: dry-run" in output
    assert "Maximum depth: 10000000" in output
    assert producer.DEFAULT_FILTER in output
    assert producer.ANNOTATIONS in output
    assert output.count("bcftools mpileup") == 2
    assert " -r chr1 " in output
    fwd, rev, receipt = step07.finals
    report = step07.output_dir / "cohort_A.part_A.step07_validation.tsv"
    validate_prefix = ("emrys", "validate")
    validator_bindings = (
        ("--cohort-id", "cohort_A"),
        ("--partition-id", "part_A"),
        ("--sample-manifest", step07.sample_manifest),
        ("--partition-manifest", step07.partition_manifest),
        ("--reference-fai", Path(f"{step07.reference}.fai")),
        ("--fwd-vcf", fwd),
        ("--rev-vcf", rev),
        ("--receipt", receipt),
        ("--output", report),
    )
    validator = shlex.join(
        (
            *validate_prefix,
            "partitioned-cohort-mpileup",
            *(str(item) for pair in validator_bindings for item in pair),
            "--execute",
        )
    )
    all_pass = shlex.join(
        (
            *validate_prefix,
            "all-pass",
            "--report",
            str(report),
            "--step-id",
            "07",
            "--scope-id",
            "cohort_A__part_A",
        )
    )
    assert f"Post-execution validator command:\n  {validator}" in output
    assert f"Semantic all-pass gate:\n  {all_pass}" in output
    prefix = step07.output_dir / ".cohort_A.part_A.step07.dryrun001"
    for path in (
        Path(f"{prefix}.FWD_like.tmp.vcf"),
        Path(f"{prefix}.REV_like.tmp.vcf"),
        Path(f"{prefix}.outputs.tmp.tsv"),
        Path(f"{prefix}.previous.FWD_like.vcf"),
        Path(f"{prefix}.previous.REV_like.vcf"),
        Path(f"{prefix}.previous.outputs.tsv"),
    ):
        assert str(path) in output
    assert "no directories or files were created" in output
    assert not step07.output_root.exists()
    assert not step07.log.exists()


@pytest.mark.parametrize("file_selector", (False, True))
def test_scientific_input_roster_is_exact(step07: Fixture, file_selector: bool) -> None:
    selector = None
    if file_selector:
        selector = step07.partition_manifest.parent / "target.bed"
        selector.write_text("chr1\t0\t100\n")
        step07.partition_manifest.write_text(
            "partition_id\tselector_type\tselector_value\n"
            "part_A\tregions_file\ttarget.bed\n"
        )
    parser = argparse.ArgumentParser()
    producer.configure_parser(parser)
    context = producer.build_context(parser.parse_args(step07.arguments))

    assert tuple(path for _label, path in context.scientific_inputs) == step07.roster(
        selector
    )


def test_streaming_execution_preserves_argv_receipt_and_receipt_last(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    fwd, rev, receipt = step07.finals
    observation = step07.output_root.parent / "publication-observation"
    monkeypatch.setenv("FAKE_OBSERVE_FWD", str(fwd))
    monkeypatch.setenv("FAKE_OBSERVE_REV", str(rev))
    monkeypatch.setenv("FAKE_OBSERVE_RECEIPT", str(receipt))
    monkeypatch.setenv("FAKE_OBSERVATION", str(observation))

    assert producer.main([*step07.arguments, "--no-clobber", "--execute"]) == 0

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
    assert all(path.is_file() for path in step07.finals)
    lines = receipt.read_text().splitlines()
    assert tuple(lines[0].split("\t")) == mpileup.RECEIPT_HEADER
    rows = [line.split("\t") for line in lines[1:]]
    assert [row[4] for row in rows] == list(ORIENTATIONS)
    assert [row[5] for row in rows] == [str(fwd), str(rev)]
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
def test_any_pipeline_process_failure_cleans_only_owned_state(
    step07: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    step07.output_dir.mkdir(parents=True)
    unrelated = step07.output_dir / "unrelated.txt"
    unrelated.write_text("preserve\n")
    monkeypatch.setenv("FAKE_FAIL_STAGE", failure)

    assert producer.main([*step07.arguments, "--execute"]) == 1

    _assert_clean(step07)
    assert unrelated.read_text() == "preserve\n"


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

    assert producer.main([*step07.arguments, "--execute"]) == 0

    pileups = [call for call in _calls(step07.log) if call[0] == "mpileup"]
    assert all(
        call[call.index("-R") + 1] == str(selector.resolve()) for call in pileups
    )
    rows = [line.split("\t") for line in step07.finals[2].read_text().splitlines()[1:]]
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
    assert not step07.output_root.exists()
    assert not step07.log.exists()


@pytest.mark.parametrize("index", (4, 5))
def test_rejects_missing_bam_or_index(step07: Fixture, index: int) -> None:
    step07.roster()[index].unlink()

    assert producer.main(step07.arguments) == 1
    assert not step07.output_root.exists()
    assert not step07.log.exists()


@pytest.mark.parametrize("state", ("missing", "nonexecutable"))
def test_rejects_unusable_explicit_tool(step07: Fixture, state: str) -> None:
    if state == "missing":
        step07.bcftools.unlink()
    else:
        step07.bcftools.chmod(0o644)

    assert producer.main(step07.arguments) == 1
    assert not step07.output_root.exists()


@pytest.mark.parametrize("source", ("environment", "path"))
def test_tool_fallback_precedence(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    arguments = step07.arguments[:-2]
    if source == "environment":
        monkeypatch.setenv("BCFTOOLS_BIN_OVERRIDE", str(step07.bcftools))
    else:
        bcftools = step07.bcftools.with_name("bcftools")
        step07.bcftools.rename(bcftools)
        monkeypatch.delenv("BCFTOOLS_BIN_OVERRIDE", raising=False)
        monkeypatch.setenv("PATH", str(bcftools.parent))

    assert producer.main(arguments) == 0


def test_bound_identity_includes_relative_selector_and_is_scrubbed(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector = step07.partition_manifest.parent / "target.bed"
    selector.write_text("chr1\t0\t100\n")
    step07.partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\n"
        "part_A\tregions_file\ttarget.bed\n"
    )
    monkeypatch.setenv("EMRYS_REQUIRE_BOUND_SHA256", "1")
    monkeypatch.setenv(producer.INPUT_IDENTITY_ENV, _identity(step07.roster(selector)))

    assert producer.main([*step07.arguments, "--no-clobber", "--execute"]) == 0
    assert producer.INPUT_IDENTITY_ENV not in os.environ


@pytest.mark.parametrize("bound", (False, True))
def test_no_clobber_rejects_direct_and_bound_input_mutation(
    step07: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    bound: bool,
) -> None:
    bam = step07.roster()[4]
    if bound:
        monkeypatch.setenv("EMRYS_REQUIRE_BOUND_SHA256", "1")
        monkeypatch.setenv(producer.INPUT_IDENTITY_ENV, _identity(step07.roster()))
    monkeypatch.setenv("FAKE_MUTATE_PATH", str(bam))

    assert producer.main([*step07.arguments, "--no-clobber", "--execute"]) == 1

    _assert_clean(step07)
    assert "controlled mutation" in bam.read_text()


@pytest.mark.parametrize("manifest_name", ("sample_manifest", "partition_manifest"))
def test_manifest_mutation_is_always_rejected(
    step07: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    manifest_name: str,
) -> None:
    manifest = getattr(step07, manifest_name)
    monkeypatch.setenv("FAKE_MUTATE_PATH", str(manifest))

    assert producer.main([*step07.arguments, "--execute"]) == 1

    _assert_clean(step07)
    assert "controlled mutation" in manifest.read_text()


def test_replace_mode_retains_the_manifest_only_stability_boundary(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    bam = step07.roster()[4]
    monkeypatch.setenv("FAKE_MUTATE_PATH", str(bam))

    assert producer.main([*step07.arguments, "--execute"]) == 0

    assert all(path.is_file() for path in step07.finals)
    assert "controlled mutation" in bam.read_text()


def test_complete_no_clobber_set_is_unchanged_without_tool_reentry(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert producer.main([*step07.arguments, "--execute"]) == 0
    before = tuple(path.read_bytes() for path in step07.finals)
    step07.log.unlink()
    monkeypatch.setenv("FAKE_FAIL_STAGE", "mpileup_FWD_like")

    assert producer.main([*step07.arguments, "--no-clobber", "--execute"]) == 1

    assert tuple(path.read_bytes() for path in step07.finals) == before
    assert not step07.log.exists()


def test_foreign_lock_residue_and_incomplete_set_are_preserved(
    step07: Fixture,
) -> None:
    step07.output_dir.mkdir(parents=True)
    lock = step07.output_dir / ".cohort_A.part_A.step07.lock"
    lock.mkdir()
    owner = lock / "owner"
    owner.write_text("run_token\tforeign\npid\t99\n")
    assert producer.main([*step07.arguments, "--execute"]) == 1
    assert owner.read_text().startswith("run_token\tforeign")
    assert not step07.log.exists()
    owner.unlink()
    lock.rmdir()

    residue = step07.output_dir / ".cohort_A.part_A.step07.abandoned.tmp.vcf"
    residue.write_text("operator evidence\n")
    assert producer.main([*step07.arguments, "--no-clobber"]) == 1
    assert residue.read_text() == "operator evidence\n"
    residue.unlink()

    step07.finals[0].write_text("partial predecessor\n")
    assert producer.main([*step07.arguments, "--execute"]) == 1
    assert step07.finals[0].read_text() == "partial predecessor\n"
    assert not step07.log.exists()


@pytest.mark.parametrize("failed_restore", (False, True))
def test_publication_failure_restores_or_retains_recovery_state(
    step07: Fixture,
    monkeypatch: pytest.MonkeyPatch,
    failed_restore: bool,
) -> None:
    assert producer.main([*step07.arguments, "--execute"]) == 0
    previous = (b"previous fwd\n", b"previous rev\n", b"previous receipt\n")
    for path, content in zip(step07.finals, previous, strict=True):
        path.write_bytes(content)
    original_replace = Path.replace

    def injected_replace(source: Path, destination: Path) -> Path:
        if source.name.endswith("outputs.tmp.tsv"):
            raise OSError("injected receipt publication failure")
        if failed_restore and source.name.endswith("previous.FWD_like.vcf"):
            raise OSError("injected FWD restore failure")
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "replace", injected_replace)

    assert producer.main([*step07.arguments, "--execute"]) == 1

    lock = step07.output_dir / ".cohort_A.part_A.step07.lock"
    if failed_restore:
        token = str(os.getpid())
        backup = step07.output_dir / (
            f".cohort_A.part_A.step07.{token}.previous.FWD_like.vcf"
        )
        assert not step07.finals[0].exists()
        assert backup.read_bytes() == previous[0]
        assert (lock / "owner").is_file()
        assert step07.finals[1].read_bytes() == previous[1]
        assert step07.finals[2].read_bytes() == previous[2]
    else:
        assert tuple(path.read_bytes() for path in step07.finals) == previous
        assert not lock.exists()
        assert not list(step07.output_dir.glob(".cohort_A.part_A.step07.*"))


def test_postpublication_validation_failure_restores_previous_set(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert producer.main([*step07.arguments, "--execute"]) == 0
    previous = (b"previous fwd\n", b"previous rev\n", b"previous receipt\n")
    for path, content in zip(step07.finals, previous, strict=True):
        path.write_bytes(content)
    monkeypatch.setenv("FAKE_FAIL_FINAL_VIEW", "1")

    assert producer.main([*step07.arguments, "--execute"]) == 1
    assert tuple(path.read_bytes() for path in step07.finals) == previous
    assert not list(step07.output_dir.glob(".cohort_A.part_A.step07.*"))


def test_interruption_during_publication_restores_the_previous_set(
    step07: Fixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert producer.main([*step07.arguments, "--execute"]) == 0
    previous = (b"previous fwd\n", b"previous rev\n", b"previous receipt\n")
    for path, content in zip(step07.finals, previous, strict=True):
        path.write_bytes(content)
    original_replace = Path.replace
    interrupted = False

    def interrupt_after_first_final(source: Path, destination: Path) -> Path:
        nonlocal interrupted
        result = original_replace(source, destination)
        if not interrupted and source.name.endswith("FWD_like.tmp.vcf"):
            interrupted = True
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
        return result

    monkeypatch.setattr(Path, "replace", interrupt_after_first_final)

    assert producer.main([*step07.arguments, "--execute"]) == 143

    assert tuple(path.read_bytes() for path in step07.finals) == previous
    assert not list(step07.output_dir.glob(".cohort_A.part_A.step07.*"))


def test_same_scope_lock_and_term_stop_both_pipeline_children(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    ready = step07.output_root.parent / "pipeline.ready"
    filter_ready = step07.output_root.parent / "filter.ready"
    release = step07.output_root.parent / "pipeline.release"
    term_log = step07.output_root.parent / "terminated.log"
    environment = dict(os.environ)
    environment.update(
        {
            "FAKE_BARRIER_READY": str(ready),
            "FAKE_BARRIER_RELEASE": str(release),
            "FAKE_FILTER_READY": str(filter_ready),
            "FAKE_TERM_LOG": str(term_log),
            "FAKE_BCFTOOLS_LOG": str(step07.log),
        }
    )
    command = [
        sys.executable,
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "emrys.stages.partitioned_cohort_mpileup.producer",
        *step07.arguments,
        "--execute",
    ]
    running = subprocess.Popen(
        command,
        cwd=Path(__file__).resolve().parents[3],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 5
        while (
            not (ready.exists() and filter_ready.exists())
            and running.poll() is None
            and time.monotonic() < deadline
        ):
            time.sleep(0.02)
        assert ready.exists() and filter_ready.exists(), running.communicate(timeout=1)
        owner = step07.output_dir / ".cohort_A.part_A.step07.lock/owner"
        before = owner.read_bytes()

        assert producer.main([*step07.arguments, "--execute"]) == 1
        assert owner.read_bytes() == before

        running.send_signal(signal.SIGTERM)
        stdout, stderr = running.communicate(timeout=5)
        assert running.returncode == 143, stdout + stderr
    finally:
        if running.poll() is None:
            release.touch()
            running.kill()
            running.wait()

    assert set(term_log.read_text().splitlines()) == {"mpileup", "filter"}
    _assert_clean(step07)


def test_vcf_sample_order_mismatch_never_publishes(
    step07: Fixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_SAMPLES", "sample_B,sample_A")

    assert producer.main([*step07.arguments, "--execute"]) == 1

    _assert_clean(step07)
