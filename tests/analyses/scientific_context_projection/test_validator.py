"""Focused checks for the one-row scientific-context validator."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pytest
from emrys.analyses.scientific_context_projection import validator
from emrys.contracts.scientific_evidence import scientific_context
from tests import scientific_context_test_support as CONTEXT_FIXTURE
from tests import scientific_evidence_test_support as STEP_FIXTURE


def _transaction(tmp_path: Path) -> CONTEXT_FIXTURE.ContextFixture:
    built = STEP_FIXTURE.build_fixture(tmp_path / "step09")
    analysis_id = STEP_FIXTURE.PRIMARY_ANALYSIS_ID
    analysis_dir = built.step09_analysis_dir
    return CONTEXT_FIXTURE.build_transaction(
        tmp_path / "context",
        analysis_id=analysis_id,
        step09_all_sites=analysis_dir / f"{analysis_id}.cmh_all_sites.tsv",
        step09_significant_sites=(
            analysis_dir / f"{analysis_id}.cmh_significant_sites.tsv"
        ),
        step09_summary=analysis_dir / f"{analysis_id}.cmh_summary.tsv",
    )


def _rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(data.decode().splitlines(), delimiter="\t"))


def test_validator_calls_one_transaction_admission_and_emits_one_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transaction = _transaction(tmp_path)
    arguments = argparse.Namespace(
        receipt=transaction.receipt,
        output=tmp_path / "validation.tsv",
        execute=False,
    )
    admission_calls = 0
    discovery_calls = 0
    real_admission = scientific_context.validate_scientific_context_transaction
    real_discovery = validator._discover_bound_paths

    def counted_admission(receipt: Path):
        nonlocal admission_calls
        admission_calls += 1
        return real_admission(receipt)

    def counted_discovery(receipt: Path):
        nonlocal discovery_calls
        discovery_calls += 1
        return real_discovery(receipt)

    monkeypatch.setattr(
        scientific_context,
        "validate_scientific_context_transaction",
        counted_admission,
    )
    monkeypatch.setattr(validator, "_discover_bound_paths", counted_discovery)

    assert validator.validate_from_args(arguments) == 0
    assert admission_calls == 1
    assert discovery_calls == 1
    assert not arguments.output.exists()


def test_validator_reports_one_failed_transaction_check_for_stale_payload(
    tmp_path: Path,
) -> None:
    transaction = _transaction(tmp_path)
    transaction.motif_hits.write_bytes(transaction.motif_hits.read_bytes() + b"stale\n")

    data, input_snapshots = validator.build_validation_report(
        argparse.Namespace(
            receipt=transaction.receipt,
            output=tmp_path / "validation.tsv",
            execute=False,
        )
    )
    rows = _rows(data)
    assert len(rows) == 1
    assert len(input_snapshots) == 11
    assert rows[0]["step_id"] == "10"
    assert rows[0]["scope_id"] == STEP_FIXTURE.PRIMARY_ANALYSIS_ID
    assert rows[0]["check_id"] == "scientific_context_transaction"
    assert rows[0]["status"] == "fail"
    assert "sha256 is stale" in rows[0]["observed"]


def test_validator_rejects_an_unreadable_receipt_without_a_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "missing.context_receipt.tsv"
    status = validator.validate_from_args(
        argparse.Namespace(
            receipt=missing,
            output=tmp_path / "validation.tsv",
            execute=False,
        )
    )

    captured = capsys.readouterr()
    assert status == 2
    assert "ERROR: Could not inspect scientific-context receipt paths" in captured.err
    assert "Traceback" not in captured.err
