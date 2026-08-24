from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path

from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
FAKE_TOOL_ENVIRONMENT_KEYS = (
    "HEADER_EXIT",
    "MUTATE_PATH",
    "QUICKCHECK_EXIT",
    "RG_ID",
    "RG_SM",
    "SORT_ORDER",
)


@dataclass(frozen=True, slots=True)
class SplitNCigarEvidence:
    bam: Path
    bai: Path
    fasta: Path
    fai: Path
    dictionary: Path
    samtools: Path
    output: Path


def build_validation_fixture(root: Path) -> SplitNCigarEvidence:
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.split_ncigar.bam"
    bam.write_bytes(b"BAM\x01synthetic")
    bai = root / "S.split_ncigar.bam.bai"
    bai.write_bytes(b"BAI\x01synthetic")
    fasta = root / "genome.fa"
    fasta.write_text(">1\nACGT\n", encoding="utf-8")
    fai = root / "genome.fa.fai"
    fai.write_text("1\t4\t3\t4\t5\n", encoding="utf-8")
    dictionary = root / "genome.dict"
    dictionary.write_text("@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n", encoding="utf-8")
    samtools = root / "samtools"
    samtools.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'case "$1 $2" in\n'
        " 'quickcheck -v') exit \"${QUICKCHECK_EXIT:-0}\" ;;\n"
        " 'view -H')\n"
        '   if [[ "${HEADER_EXIT:-0}" != 0 ]]; then\n'
        "     printf 'forced header failure\\n' >&2\n"
        '     exit "$HEADER_EXIT"\n'
        "   fi\n"
        '   if [[ -n "${MUTATE_PATH:-}" ]]; then\n'
        "     printf 'post-build mutation\\n' >> \"$MUTATE_PATH\"\n"
        "   fi\n"
        "   printf '@HD\\tVN:1.6\\tSO:%s\\n@RG\\tID:%s\\tSM:%s\\n' "
        '"${SORT_ORDER:-coordinate}" "${RG_ID:-S}" "${RG_SM:-S}" ;;\n'
        " *) exit 9 ;;\nesac\n",
        encoding="utf-8",
    )
    samtools.chmod(0o755)
    output_directory = root / "out"
    output_directory.mkdir()
    return SplitNCigarEvidence(
        bam=bam,
        bai=bai,
        fasta=fasta,
        fai=fai,
        dictionary=dictionary,
        samtools=samtools,
        output=output_directory / "S.validation.tsv",
    )


def fake_tool_environment(**overrides: str) -> dict[str, str]:
    environment = os.environ.copy()
    for key in FAKE_TOOL_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    environment.update(overrides)
    return environment


def validator_arguments(
    evidence: SplitNCigarEvidence,
    *extra: str,
) -> list[str]:
    return [
        "--scope-id",
        "S",
        "--bam",
        str(evidence.bam),
        "--bai",
        str(evidence.bai),
        "--reference-fasta",
        str(evidence.fasta),
        "--reference-fai",
        str(evidence.fai),
        "--reference-dict",
        str(evidence.dictionary),
        "--samtools-bin",
        str(evidence.samtools),
        "--output",
        str(evidence.output),
        *extra,
    ]


def run_validator(
    evidence: SplitNCigarEvidence,
    *extra: str,
    cwd: Path = ROOT,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad",
            "validate",
            "split-n-cigar",
            *validator_arguments(evidence, *extra),
        ],
        cwd=cwd,
        env=environment if environment is not None else fake_tool_environment(),
        text=True,
        capture_output=True,
        check=False,
    )


def test_dry_run_is_side_effect_free(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    assert run_validator(evidence).returncode == 0
    assert not evidence.output.exists()


def test_execute_publishes_five_passes(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    result = run_validator(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    rows = report_rows(evidence.output)
    assert_exact_check_roster(rows, "05")
    assert {row["status"] for row in rows} == {"pass"}


def test_sidecar_disagreement_is_failed_evidence(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.fai.write_text("1\t5\t3\t5\t6\n", encoding="utf-8")
    assert run_validator(evidence, "--execute").returncode == 0
    status_by_check = {
        row["check_id"]: row["status"] for row in report_rows(evidence.output)
    }
    assert status_by_check["reference_sidecars"] == "fail"


def test_reference_parsing_short_circuits_on_first_parser_error(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.fasta.write_text("sequence-before-header\n", encoding="utf-8")
    evidence.fai.write_text("also-malformed\n", encoding="utf-8")
    evidence.dictionary.write_text("@SQ\tLN:not-a-number\n", encoding="utf-8")
    result = run_validator(evidence, "--execute")
    assert result.returncode == 0, result.stderr
    rows_by_check = {row["check_id"]: row for row in report_rows(evidence.output)}
    sidecars = rows_by_check["reference_sidecars"]
    assert sidecars["status"] == "fail"
    assert sidecars["observed"] == "FASTA sequence appears before its header"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.bai.unlink()
    assert run_validator(evidence, "--execute").returncode == 2

    valid_evidence = build_validation_fixture(tmp_path / "second")
    invalid_evidence = replace(
        valid_evidence,
        output=valid_evidence.output.parent / "wrong.tsv",
    )
    assert run_validator(invalid_evidence, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(evidence, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_identical(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path / "fixture")
    invocation_directory = tmp_path / "other-cwd"
    invocation_directory.mkdir()
    input_paths = (
        evidence.bam,
        evidence.bai,
        evidence.fasta,
        evidence.fai,
        evidence.dictionary,
        evidence.samtools,
    )
    input_states = tuple(
        (path.read_bytes(), path.stat().st_mode) for path in input_paths
    )

    dry_run = run_validator(evidence, cwd=invocation_directory)
    assert dry_run.returncode == 0, dry_run.stderr
    assert dry_run.stderr == ""
    assert len(dry_run.stdout.encode()) == 636
    assert hashlib.sha256(dry_run.stdout.encode()).hexdigest() == (
        "032edf3fb44c2810658c47727bf5d266367fb6228f00cb575664f8b6714a409a"
    )
    assert not evidence.output.exists()
    assert list(invocation_directory.iterdir()) == []

    first = run_validator(evidence, "--execute", cwd=invocation_directory)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    output_bytes = evidence.output.read_bytes()
    assert len(output_bytes) == 595
    assert hashlib.sha256(output_bytes).hexdigest() == (
        "9795ad7bf2715ebfa96efc6e78f4cb1b3a836bed0ec3c38c5a79d7fce0796c5b"
    )
    assert dry_run.stdout.encode().startswith(output_bytes)
    assert_exact_check_roster(report_rows(evidence.output), "05")

    second = run_validator(evidence, "--execute", cwd=invocation_directory)
    assert second.returncode == 0, second.stderr
    assert second.stdout == first.stdout
    assert evidence.output.read_bytes() == output_bytes
    assert tuple((path.read_bytes(), path.stat().st_mode) for path in input_paths) == (
        input_states
    )
    assert list(invocation_directory.iterdir()) == []


def test_quickcheck_failure_is_published_as_failed_evidence(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    result = run_validator(
        evidence,
        "--execute",
        environment=fake_tool_environment(QUICKCHECK_EXIT="7"),
    )

    assert result.returncode == 0, result.stderr
    rows_by_check = {row["check_id"]: row for row in report_rows(evidence.output)}
    assert rows_by_check["samtools_quickcheck"]["status"] == "fail"
    assert rows_by_check["samtools_quickcheck"]["observed"] == "exit=7"


def test_header_tool_failure_exits_two_without_publication(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    result = run_validator(
        evidence,
        "--execute",
        environment=fake_tool_environment(HEADER_EXIT="8"),
    )

    assert result.returncode == 2
    assert "samtools view -H failed: forced header failure" in result.stderr
    assert not evidence.output.exists()


def test_invalid_reference_encoding_preserves_valid_predecessor(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    initial = run_validator(evidence, "--execute")
    assert initial.returncode == 0, initial.stderr
    predecessor = evidence.output.read_bytes()
    evidence.fasta.write_bytes(b"\xff")

    result = run_validator(evidence, "--execute")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "ERROR:" in result.stderr
    assert "Traceback" not in result.stderr
    assert evidence.output.read_bytes() == predecessor


def test_post_build_input_mutation_preserves_valid_predecessor(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    initial = run_validator(evidence, "--execute")
    assert initial.returncode == 0, initial.stderr
    predecessor = evidence.output.read_bytes()

    result = run_validator(
        evidence,
        "--execute",
        environment=fake_tool_environment(MUTATE_PATH=str(evidence.bam)),
    )

    assert result.returncode == 2
    assert "Input changed after validation" in result.stderr
    assert evidence.output.read_bytes() == predecessor
    assert evidence.bam.read_bytes().endswith(b"post-build mutation\n")
