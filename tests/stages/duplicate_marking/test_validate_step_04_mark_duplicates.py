from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.stage_validator_test_support import load_roster_oracle
from tests.stage_validator_test_support import read_tsv as report_rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
FAKE_TOOL_ENVIRONMENT_KEYS = (
    "MUTATE_PATH",
    "QUICKCHECK_EXIT",
    "RG_ID",
    "RG_SM",
    "SORT_ORDER",
    "VIEW_EXIT",
)


@dataclass(frozen=True, slots=True)
class DuplicateMarkingEvidence:
    bam: Path
    bai: Path
    metrics: Path
    samtools: Path
    output: Path


def build_validation_fixture(root: Path) -> DuplicateMarkingEvidence:
    root.mkdir(parents=True, exist_ok=True)
    bam = root / "S.markdup.bam"
    bam.write_bytes(b"BAM\x01synthetic")
    bai = root / "S.markdup.bam.bai"
    bai.write_bytes(b"BAI\x01synthetic")
    metrics = root / "S.markdup.metrics.txt"
    metrics.write_text(
        "## METRICS CLASS picard.sam.DuplicationMetrics\n"
        "LIBRARY\tREAD_PAIRS_EXAMINED\tREAD_PAIR_DUPLICATES\t"
        "PERCENT_DUPLICATION\tESTIMATED_LIBRARY_SIZE\n"
        "S\t10\t2\t0.2\t\n"
        "\n"
        "## HISTOGRAM\tjava.lang.Double\n"
        "set_size\tall_sets\tnon_optical_sets\n"
        "1.0\t8\t8\n"
        "2.0\t2\t2\n",
        encoding="utf-8",
    )
    samtools = root / "samtools"
    samtools.write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\n"
        'case "$1 $2" in\n'
        " 'quickcheck -v') exit \"${QUICKCHECK_EXIT:-0}\" ;;\n"
        " 'view -H')\n"
        '   if [[ "${VIEW_EXIT:-0}" != 0 ]]; then\n'
        "     printf 'fake samtools header failure\\n' >&2\n"
        '     exit "$VIEW_EXIT"\n'
        "   fi\n"
        "   printf '@HD\\tVN:1.6\\tSO:%s\\n@RG\\tID:%s\\tSM:%s\\n' "
        '"${SORT_ORDER:-coordinate}" "${RG_ID:-S}" "${RG_SM:-S}"\n'
        '   if [[ -n "${MUTATE_PATH:-}" ]]; then\n'
        "     printf 'mutated-after-build\\n' >> \"$MUTATE_PATH\"\n"
        "   fi ;;\n"
        " *) exit 9 ;;\nesac\n",
        encoding="utf-8",
    )
    samtools.chmod(0o755)
    output_directory = root / "out"
    output_directory.mkdir()
    return DuplicateMarkingEvidence(
        bam=bam,
        bai=bai,
        metrics=metrics,
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
    evidence: DuplicateMarkingEvidence,
    *extra: str,
) -> list[str]:
    return [
        "--scope-id",
        "S",
        "--bam",
        str(evidence.bam),
        "--bai",
        str(evidence.bai),
        "--metrics",
        str(evidence.metrics),
        "--samtools-bin",
        str(evidence.samtools),
        "--output",
        str(evidence.output),
        *extra,
    ]


def run_validator(
    evidence: DuplicateMarkingEvidence,
    *extra: str,
    environment: dict[str, str] | None = None,
    cwd: Path = ROOT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "norad",
            "validate",
            "duplicate-marking",
            *validator_arguments(evidence, *extra),
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=environment if environment is not None else fake_tool_environment(),
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
    assert_exact_check_roster(rows, "04")
    assert {row["status"] for row in rows} == {"pass"}


def test_bad_header_and_metrics_are_failed_evidence(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.metrics.write_text(
        "LIBRARY\tPERCENT_DUPLICATION\nS\t2\n",
        encoding="utf-8",
    )
    result = run_validator(
        evidence,
        "--execute",
        environment=fake_tool_environment(SORT_ORDER="queryname", RG_ID="wrong"),
    )
    assert result.returncode == 0, result.stderr
    status = {row["check_id"]: row["status"] for row in report_rows(evidence.output)}
    assert status["coordinate_sorting"] == "fail"
    assert status["read_group_preservation"] == "fail"
    assert status["duplication_metrics"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    evidence.metrics.unlink()
    assert run_validator(evidence, "--execute").returncode == 2
    valid_evidence = build_validation_fixture(tmp_path / "second")
    invalid_evidence = DuplicateMarkingEvidence(
        bam=valid_evidence.bam,
        bai=valid_evidence.bai,
        metrics=valid_evidence.metrics,
        samtools=valid_evidence.samtools,
        output=valid_evidence.output.parent / "wrong.tsv",
    )
    assert run_validator(invalid_evidence, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path: Path) -> None:
    evidence = build_validation_fixture(tmp_path)
    lock = evidence.output.parent / f".{evidence.output.name}.lock"
    lock.write_text("foreign\n", encoding="utf-8")
    assert run_validator(evidence, "--execute").returncode == 2
    assert lock.read_text(encoding="utf-8") == "foreign\n"


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_exact(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path / "fixture")
    invocation = tmp_path / "invocation"
    invocation.mkdir()
    inputs = (evidence.bam, evidence.bai, evidence.metrics, evidence.samtools)
    input_states = tuple((path.read_bytes(), path.stat().st_mode) for path in inputs)

    dry_run = run_validator(evidence, cwd=invocation)
    assert dry_run.returncode == 0, dry_run.stderr
    assert dry_run.stderr == ""
    assert hashlib.sha256(dry_run.stdout.encode()).hexdigest() == (
        "54fd4f2e00f6fe2ee31276830761baf5858141e0a1f35f47d3de72c736a64e1e"
    )
    assert not evidence.output.exists()
    assert list(invocation.iterdir()) == []

    first = run_validator(evidence, "--execute", cwd=invocation)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    output_bytes = evidence.output.read_bytes()
    assert len(output_bytes) == 596
    assert hashlib.sha256(output_bytes).hexdigest() == (
        "7bacb96cc5040a735396b2032e7d179b118ecd394c4ed78720a43d32189ab538"
    )
    assert dry_run.stdout.encode().startswith(output_bytes)
    assert_exact_check_roster(report_rows(evidence.output), "04")

    second = run_validator(evidence, "--execute", cwd=invocation)
    assert second.returncode == 0, second.stderr
    assert second.stdout == first.stdout
    assert evidence.output.read_bytes() == output_bytes
    assert tuple((path.read_bytes(), path.stat().st_mode) for path in inputs) == (
        input_states
    )
    assert list(invocation.iterdir()) == []


def test_quickcheck_nonzero_publishes_failed_evidence_with_exit_zero(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    result = run_validator(
        evidence,
        "--execute",
        environment=fake_tool_environment(QUICKCHECK_EXIT="17"),
    )

    assert result.returncode == 0, result.stderr
    rows_by_check = {row["check_id"]: row for row in report_rows(evidence.output)}
    assert rows_by_check["samtools_quickcheck"]["status"] == "fail"
    assert rows_by_check["samtools_quickcheck"]["observed"] == "exit=17"
    assert {
        row["status"]
        for check_id, row in rows_by_check.items()
        if check_id != "samtools_quickcheck"
    } == {"pass"}


def test_header_tool_failure_preserves_valid_predecessor_report(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    first = run_validator(evidence, "--execute")
    assert first.returncode == 0, first.stderr
    predecessor = evidence.output.read_bytes()

    failed = run_validator(
        evidence,
        "--execute",
        environment=fake_tool_environment(VIEW_EXIT="29"),
    )

    assert failed.returncode == 2
    assert failed.stdout == ""
    assert "samtools view -H failed: fake samtools header failure" in failed.stderr
    assert evidence.output.read_bytes() == predecessor


def test_post_build_input_mutation_preserves_valid_predecessor_report(
    tmp_path: Path,
) -> None:
    evidence = build_validation_fixture(tmp_path)
    first = run_validator(evidence, "--execute")
    assert first.returncode == 0, first.stderr
    predecessor = evidence.output.read_bytes()
    original_bam = evidence.bam.read_bytes()

    failed = run_validator(
        evidence,
        "--execute",
        environment=fake_tool_environment(MUTATE_PATH=str(evidence.bam)),
    )

    assert failed.returncode == 2
    assert "Input changed after validation" in failed.stderr
    assert evidence.bam.read_bytes() == original_bam + b"mutated-after-build\n"
    assert evidence.output.read_bytes() == predecessor
