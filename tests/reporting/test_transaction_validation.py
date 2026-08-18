"""Read-only validation contracts for complete reporting transactions."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from norad.contracts.orchestration import api as orchestration_contracts
from norad.libraries.source_authority import controlled_python_argv
from norad.reporting import report, transaction_validation
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as fixture

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_EPOCH = "1700000000"


def _fixture_receipt_ops(
    **overrides: Any,
) -> transaction_validation.ReceiptValidationOps:
    return transaction_validation.ReceiptValidationOps(
        matching_clean_checkout_head_commit=(
            lambda **_kwargs: workflow_fixture.source_checkout_commit()
        ),
        **overrides,
    )


def _publish_summary(built: Any) -> None:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    result = subprocess.run(
        [
            *controlled_python_argv(sys.executable, "-m", "norad"),
            "build",
            "run-summary",
            *built.command_args(execute=True),
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture
def complete_reporting(tmp_path: Path) -> tuple[Any, Path]:
    built = fixture.build_fixture(tmp_path / "run")
    _publish_summary(built)
    report_root = built.root / "reports"
    arguments = argparse.Namespace(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        output_root=report_root,
        execute=True,
    )
    assert report.build_from_args(arguments) == 0
    return built, report_root


def test_direct_validators_recheck_each_complete_transaction(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    adapter = transaction_validation.validate_artifact_index_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_id=built.run_id,
        run_contract=built.adapter_fixture.run_contract,
        inventory=built.adapter_fixture.inventory,
        output_root=built.adapter_fixture.output_root,
        receipt_ops=_fixture_receipt_ops(),
    )
    summary = transaction_validation.validate_run_summary_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_id=built.run_id,
        artifact_receipt=built.artifact_receipt,
        output_root=built.output_root,
        receipt_ops=_fixture_receipt_ops(),
    )
    rendered = transaction_validation.validate_report_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        output_root=report_root,
        receipt_ops=_fixture_receipt_ops(),
    )

    assert adapter.receipt_path == built.artifact_receipt
    assert summary.receipt_path == built.summary_receipt_path
    assert rendered.receipt_path.name == f"{built.run_id}.report_outputs.tsv"
    assert all(len(item.receipt_sha256) == 64 for item in (adapter, summary, rendered))


def test_fixed_dispatcher_attests_source_checkout_to_attempt_commit(
    tmp_path: Path,
) -> None:
    built = workflow_fixture.build(tmp_path / "workflow")
    attempt = orchestration_contracts.load_record(
        built.workflow_attempt_path,
        "workflow-attempt",
    )
    attempt["source_checkout"]["commit"] = "f" * 40

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="Source checkout HEAD differs from the workflow attempt commit",
    ):
        transaction_validation.validate_receipt(
            "artifact_index",
            built.artifact_receipt,
            built.run_root,
            built.execution,
            built.profile,
            attempt,
        )


def test_artifact_validator_rejects_native_source_mutation(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, _report_root = complete_reporting
    source = built.adapter_fixture.source_for("sample.SYNTH_A.star_log")
    source.write_text("mutated after reporting\n", encoding="utf-8")

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="current declared source",
    ):
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=_fixture_receipt_ops(),
        )


@pytest.mark.parametrize(
    "report_name",
    ("scientific_report.html", "evidence_report.html"),
)
def test_report_validator_rejects_each_receipted_html_mutation(
    complete_reporting: tuple[Any, Path],
    report_name: str,
) -> None:
    built, report_root = complete_reporting
    output = report_root / built.run_id / f"{built.run_id}.{report_name}"
    output.write_bytes(output.read_bytes() + b"\n")

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="receipt",
    ):
        transaction_validation.validate_report_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            output_root=report_root,
            receipt_ops=_fixture_receipt_ops(),
        )


def test_receipt_identity_replacement_during_validation_fails_closed(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, _report_root = complete_reporting

    def replace_receipt(paths: tuple[Path, ...]) -> None:
        path = built.artifact_receipt
        assert path in paths
        replacement = path.with_name(f".{path.name}.replacement")
        replacement.write_bytes(path.read_bytes())
        replacement.replace(path)

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="changed during semantic validation",
    ):
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=_fixture_receipt_ops(
                before_final_snapshot=replace_receipt,
            ),
        )


def test_each_validator_rejects_nonreceipt_and_upstream_mutation_faults(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    native_source = built.adapter_fixture.source_for("sample.SYNTH_A.star_log")
    scientific_html = (
        report_root / built.run_id / f"{built.run_id}.scientific_report.html"
    )
    evidence_html = (
        report_root / built.run_id / f"{built.run_id}.evidence_report.html"
    )

    def validate_artifact(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=ops,
        )

    def validate_summary(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_run_summary_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            artifact_receipt=built.artifact_receipt,
            output_root=built.output_root,
            receipt_ops=ops,
        )

    def validate_report(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_report_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            output_root=report_root,
            receipt_ops=ops,
        )

    cases = (
        (validate_artifact, built.adapter_fixture.artifacts_path),
        (validate_artifact, native_source),
        (validate_summary, built.summary_tsv_path),
        (validate_summary, native_source),
        (validate_report, scientific_html),
        (validate_report, evidence_html),
        (validate_report, native_source),
    )
    for validator, target in cases:
        original = target.read_bytes()

        def mutate(paths: tuple[Path, ...], *, selected: Path = target) -> None:
            assert selected in paths
            selected.write_bytes(original + b"mutation-fault\n")

        with pytest.raises(
            transaction_validation.ReportingTransactionError,
            match="roster changed during semantic validation",
        ):
            validator(
                _fixture_receipt_ops(
                    before_final_snapshot=mutate,
                )
            )
        target.write_bytes(original)


def test_artifact_validator_rejects_record_roster_membership_fault(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, _report_root = complete_reporting
    unexpected = built.adapter_fixture.records_dir / "unexpected.json"

    def add_record(paths: tuple[Path, ...]) -> None:
        assert built.adapter_fixture.artifacts_path in paths
        unexpected.write_text("{}\n", encoding="utf-8")

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="roster changed during semantic validation",
    ):
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=_fixture_receipt_ops(
                before_final_snapshot=add_record,
            ),
        )


def test_artifact_validator_binds_nested_missing_source_to_existing_ancestor(
    tmp_path: Path,
) -> None:
    adapter = fixture.ADAPTER_FIXTURE.build_fixture(tmp_path / "adapter")
    artifact_id = "sample.SYNTH_A.canonical_bai"
    inventory_row = next(
        row for row in adapter.inventory_rows if row["artifact_id"] == artifact_id
    )
    original_source = adapter.source_for(artifact_id)
    original_source.unlink()
    missing_parent = adapter.root / "missing"
    missing = missing_parent / "nested" / original_source.name
    inventory_row["source_path"] = str(missing)
    adapter.source_paths[artifact_id] = missing
    fixture.write_tsv(
        adapter.inventory,
        fixture.ARTIFACT_CONTRACTS.INVENTORY_HEADER,
        adapter.inventory_rows,
    )
    fixture.publish_adapter_fixture(adapter)

    validated = transaction_validation.validate_artifact_index_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=adapter.root,
        run_id=adapter.run_id,
        run_contract=adapter.run_contract,
        inventory=adapter.inventory,
        output_root=adapter.output_root,
        receipt_ops=_fixture_receipt_ops(),
    )
    assert validated.receipt_path == adapter.receipt_path

    def create_intermediate_parent(paths: tuple[Path, ...]) -> None:
        assert missing in paths
        missing_parent.mkdir()

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="roster changed during semantic validation",
    ):
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=adapter.root,
            run_id=adapter.run_id,
            run_contract=adapter.run_contract,
            inventory=adapter.inventory,
            output_root=adapter.output_root,
            receipt_ops=_fixture_receipt_ops(
                before_final_snapshot=create_intermediate_parent,
            ),
        )


def test_each_validator_rejects_control_residue_injected_before_return(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    token = "123-" + "a" * 32
    artifact_dir = built.artifact_receipt.parent
    report_dir = report_root / built.run_id

    def validate_artifact(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=ops,
        )

    def validate_summary(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_run_summary_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            artifact_receipt=built.artifact_receipt,
            output_root=built.output_root,
            receipt_ops=ops,
        )

    def validate_report(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_report_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            output_root=report_root,
            receipt_ops=ops,
        )

    cases = (
        (
            validate_artifact,
            artifact_dir / f".artifact-index.{token}.tmp.tsv",
            False,
        ),
        (
            validate_summary,
            artifact_dir / f".{built.run_id}.run-summary.{token}.RECOVERY.txt",
            False,
        ),
        (validate_report, report_dir / f".run-report.{token}.tmp", True),
    )
    for validator, residue, is_directory in cases:

        def inject_residue(
            paths: tuple[Path, ...],
            *,
            target: Path = residue,
            directory: bool = is_directory,
        ) -> None:
            assert paths
            if directory:
                target.mkdir()
            else:
                target.write_text("fault residue\n", encoding="utf-8")

        with pytest.raises(
            transaction_validation.ReportingTransactionError,
            match="owner control residue",
        ):
            validator(
                _fixture_receipt_ops(
                    before_final_snapshot=inject_residue,
                )
            )
        if is_directory:
            residue.rmdir()
        else:
            residue.unlink()


def test_preexisting_reporting_control_residue_fails_closed(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, _report_root = complete_reporting
    residue = built.artifact_receipt.parent / f".{built.run_id}.artifact-index.lock"
    residue.write_text("foreign lock\n", encoding="utf-8")

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="owner control residue",
    ):
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=_fixture_receipt_ops(),
        )
