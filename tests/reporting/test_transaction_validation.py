"""Read-only validation contracts for complete reporting transactions."""

from __future__ import annotations

import argparse
import copy
import hashlib
from dataclasses import replace
from contextlib import contextmanager
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from emrys import analyses
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.source_authority import (
    PACKAGE_ROOT,
    ArtifactSourceRoot,
    admit_installed_package,
)
from emrys.reporting import transaction_validation
from emrys.reporting._artifact_index import context as artifact_context
from emrys.reporting._run_report import context as report_context_owner
from emrys.reporting._run_report import publication as report_publication
from emrys.reporting._run_report import receipt
from tests.contracts.orchestration.test_application_model_contracts import (
    successor_run_fixture,
)
from tests.orchestration.run_coordinator.fixtures import workflow as workflow_fixture
from tests.reporting.fixtures.artifact_adapters_v1 import (
    build_fixture as adapter_fixture,
)
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as fixture

REPO_ROOT = Path(__file__).resolve().parents[2]


@contextmanager
def fault_before_validation(
    receipt_path: Path,
    fault: Callable[[tuple[Path, ...]], None],
) -> Iterator[None]:
    original = transaction_validation._validated_result
    reached = False

    def validate(snapshot: Any, roster: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal reached
        if snapshot.path == receipt_path:
            reached = True
            fault(tuple(item.path for item in roster.files))
        return original(snapshot, roster, *args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(transaction_validation, "_validated_result", validate)
        yield
        assert reached, f"Target receipt did not reach final validation: {receipt_path}"


def _publish_report(arguments: argparse.Namespace) -> None:
    context = report_context_owner.prepare_context(arguments)
    report_publication.publish_report(context)


@pytest.fixture
def complete_reporting(tmp_path: Path) -> tuple[Any, Path]:
    built = fixture.build_fixture(tmp_path / "run")
    report_root = built.root / "reports"
    arguments = argparse.Namespace(
        package_root=PACKAGE_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        analysis_policy=built.adapter_fixture.analysis_policy,
        output_root=report_root,
        execute=True,
    )
    _publish_report(arguments)
    return built, report_root


def test_direct_validators_recheck_each_complete_transaction(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    summary = transaction_validation.validate_run_summary_transaction(
        package_root=PACKAGE_ROOT,
        artifact_source_root=built.root,
        run_id=built.run_id,
        run_contract=built.adapter_fixture.run_contract,
        inventory=built.adapter_fixture.inventory,
        analysis_policy=built.adapter_fixture.analysis_policy,
        output_root=built.output_root,
        profile=adapter_fixture.analysis_profile_v1(),
    )
    rendered = transaction_validation.validate_report_transaction(
        package_root=PACKAGE_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        analysis_policy=built.adapter_fixture.analysis_policy,
        output_root=report_root,
        profile=adapter_fixture.analysis_profile_v1(),
    )

    assert summary.receipt_path == built.summary_json_path
    assert rendered.receipt_path.name == f"{built.run_id}.report_outputs.tsv"
    assert all(len(item.receipt_sha256) == 64 for item in (summary, rendered))
    assert summary.verified_report_locations == ()
    assert rendered.verified_report_locations == (
        (
            "scientific-report-html",
            report_root / built.run_id / f"{built.run_id}.scientific_report.html",
        ),
        (
            "evidence-report-html",
            report_root / built.run_id / f"{built.run_id}.evidence_report.html",
        ),
    )


def test_summary_revalidates_relative_artifacts_from_admitted_root(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "run").resolve()
    adapter = adapter_fixture.build_fixture(root, run_id="nested_contract")
    contract = root / "contract"
    contract.mkdir()
    inventory = contract / "artifact_inventory.tsv"
    rows = tuple(
        {
            **row,
            "source_path": Path(row["source_path"]).relative_to(root).as_posix(),
        }
        for row in adapter.inventory_rows
    )
    adapter_fixture.write_tsv(inventory, adapter_fixture.INVENTORY_HEADER, rows)
    run_contract = contract / "run.json"
    run_contract.write_bytes(adapter.run_contract.read_bytes())
    relocated = replace(
        adapter,
        inventory=inventory,
        run_contract=run_contract,
        inventory_rows=rows,
    )
    fixture.publish_adapter_fixture(relocated)
    built = fixture.RunSummaryFixture(
        root,
        relocated.run_id,
        relocated.output_root,
        relocated,
    )

    validated = transaction_validation.validate_run_summary_transaction(
        package_root=PACKAGE_ROOT,
        artifact_source_root=root,
        run_id=built.run_id,
        run_contract=built.adapter_fixture.run_contract,
        inventory=built.adapter_fixture.inventory,
        analysis_policy=built.adapter_fixture.analysis_policy,
        output_root=built.output_root,
        profile=adapter_fixture.analysis_profile_v1(),
    )

    assert validated.receipt_path == built.summary_json_path


def test_report_validator_rechecks_bound_reference_identity_without_rereading(
    complete_reporting: tuple[Any, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    built, report_root = complete_reporting
    reference = built.adapter_fixture.source_for("ref.fasta")
    real_snapshot = transaction_validation._snapshot_bound_file
    hash_modes: list[bool] = []

    def observe_snapshot(path: Path, *, hash_content: bool = True) -> Any:
        if path == reference:
            hash_modes.append(hash_content)
        return real_snapshot(path, hash_content=hash_content)

    monkeypatch.setattr(
        transaction_validation,
        "_snapshot_bound_file",
        observe_snapshot,
    )
    transaction_validation.validate_report_transaction(
        package_root=PACKAGE_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        analysis_policy=built.adapter_fixture.analysis_policy,
        output_root=report_root,
        profile=adapter_fixture.analysis_profile_v1(),
    )

    assert True in hash_modes
    assert hash_modes[-1] is False
    assert hash_modes.count(False) == 1


def test_fixed_dispatcher_accepts_successor_run_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis, plan, run, profile, attempt, _resources = successor_run_fixture()
    attempt["installed_package"] = admit_installed_package().record
    run_root = (tmp_path / run.run_id).resolve()
    contract = run_root / "contract"
    contract.mkdir(parents=True)
    for path, data in (
        (contract / "analysis.json", analysis.canonical_bytes),
        (contract / "execution-plan.json", plan.canonical_bytes),
        (contract / "run.json", run.canonical_bytes),
    ):
        path.write_bytes(data)
    receipt_path = (
        run_root
        / "products"
        / "artifact-summary"
        / run.run_id
        / f"{run.run_id}.run_summary.json"
    )
    expected = transaction_validation.ValidatedTransaction(
        receipt_path=receipt_path,
        receipt_sha256="c" * 64,
    )
    reporting_root = f"contract/reporting-inputs/{attempt['workflow_attempt_id']}"
    config = {
        "reporting_run_contract_path": {
            "path": f"{reporting_root}/reporting_run_contract.json"
        },
        "artifact_inventory_path": {"path": f"{reporting_root}/artifact_inventory.tsv"},
        "primary_analysis_policy_path": {
            "path": f"{reporting_root}/primary_analysis_policy.json"
        },
    }
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        transaction_validation,
        "validate_run_summary_transaction",
        lambda **kwargs: observed.update(kwargs) or expected,
    )

    assert (
        transaction_validation.validate_receipt(
            "run_summary",
            receipt_path,
            run_root,
            run.record,
            profile,
            attempt,
            config,
        )
        == expected
    )
    assert (
        observed["run_contract"]
        == run_root / config["reporting_run_contract_path"]["path"]
    )
    assert observed["inventory"] == run_root / config["artifact_inventory_path"]["path"]
    assert observed["analysis_policy"] == (
        run_root / config["primary_analysis_policy_path"]["path"]
    )
    assert observed["profile"] == profile
    assert observed["package_root"] == PACKAGE_ROOT


@pytest.mark.parametrize(
    ("fault", "message"),
    (
        ("native", "roster changed during semantic validation"),
        ("residue", "run_summary transaction retains owner control residue"),
    ),
)
def test_fixed_dispatcher_rechecks_cached_predecessor(
    tmp_path: Path,
    fault: str,
    message: str,
) -> None:
    _analysis, _plan, run, profile, attempt, _resources = successor_run_fixture()
    run_root = (tmp_path / run.run_id).resolve()
    output_dir = run_root / "products" / "artifact-summary" / run.run_id
    manifest = output_dir / f"{run.run_id}.run_summary.json"
    native = run_root / "products" / "native" / "evidence.tsv"
    for path, data in (
        (manifest, b"Run result manifest\n"),
        (native, b"admitted native evidence\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    roster = transaction_validation._snapshot_bound_roster(
        (manifest, native), (output_dir,)
    )
    predecessor = transaction_validation._validated_result(
        transaction_validation._snapshot_receipt(manifest),
        roster,
        lambda: transaction_validation._reject_reporting_control_residue(
            kind="run_summary",
            output_dir=output_dir,
            run_id=run.run_id,
        ),
    )
    summary_receipt = (
        transaction_validation.report_output_root(run_root, profile)
        / run.run_id
        / f"{run.run_id}.report_outputs.tsv"
    )
    assert predecessor._recheck is not None
    predecessor._recheck()
    if fault == "native":
        native.write_bytes(b"mutated native evidence\n")
    else:
        (output_dir / f".{run.run_id}.artifact-index.lock").write_bytes(b"locked\n")

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match=message,
    ):
        transaction_validation.validate_receipt(
            "html_report",
            summary_receipt,
            run_root,
            run.record,
            profile,
            attempt,
            {},
            validated_predecessor=predecessor,
        )


@pytest.mark.parametrize(
    "mutation",
    ("native_source", "producer_commit", "inventory_binding", "noncanonical"),
)
def test_manifest_rejects_mutation(
    complete_reporting: tuple[Any, Path], mutation: str
) -> None:
    built, _ = complete_reporting
    if mutation == "native_source":
        built.adapter_fixture.source_for("sample.SYNTH_A.star_log").write_text(
            "mutated after reporting\n"
        )
    else:
        document = orchestration_contracts.load_json_object(built.summary_json_path)
        if mutation == "producer_commit":
            document["provenance"]["git_commit"] = "f" * 40
        elif mutation == "inventory_binding":
            document["run_contract_file"]["sha256"] = "f" * 64
        payload = fixture.ARTIFACT_CORE.canonical_json_bytes(document)
        built.summary_json_path.write_bytes(
            payload + (b"\n" if mutation == "noncanonical" else b"")
        )
    with pytest.raises(
        transaction_validation.ReportingTransactionError, match="differs from current"
    ):
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
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
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=report_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )


def test_receipt_identity_replacement_during_validation_fails_closed(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, _report_root = complete_reporting

    def replace_receipt(paths: tuple[Path, ...]) -> None:
        path = built.summary_json_path
        assert path in paths
        replacement = path.with_name(f".{path.name}.replacement")
        replacement.write_bytes(path.read_bytes())
        replacement.replace(path)

    with (
        fault_before_validation(built.summary_json_path, replace_receipt),
        pytest.raises(
            transaction_validation.ReportingTransactionError,
            match="changed during semantic validation",
        ),
    ):
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.adapter_fixture.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )


def test_each_validator_rejects_nonreceipt_and_upstream_mutation_faults(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    native_source = built.adapter_fixture.source_for("sample.SYNTH_A.star_log")
    mutation_spectrum = built.adapter_fixture.source_for(
        "analysis.synthetic.mutation_spectrum_tsv"
    )
    reference_fasta = built.adapter_fixture.source_for("ref.fasta")
    scientific_html = (
        report_root / built.run_id / f"{built.run_id}.scientific_report.html"
    )
    evidence_html = report_root / built.run_id / f"{built.run_id}.evidence_report.html"

    def validate_artifact() -> None:
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.adapter_fixture.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )

    def validate_summary() -> None:
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )

    def validate_report() -> None:
        transaction_validation.validate_report_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=report_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )

    report_receipt = report_root / built.run_id / f"{built.run_id}.report_outputs.tsv"
    cases = (
        (validate_summary, built.summary_json_path, built.summary_tsv_path),
        (validate_summary, built.summary_json_path, built.qc_summary_path),
        (validate_summary, built.summary_json_path, native_source),
        (validate_summary, built.summary_json_path, built.adapter_fixture.inventory),
        (
            validate_summary,
            built.summary_json_path,
            built.adapter_fixture.analysis_policy,
        ),
        (validate_report, report_receipt, scientific_html),
        (validate_report, report_receipt, evidence_html),
        (validate_report, report_receipt, native_source),
        (validate_report, report_receipt, mutation_spectrum),
        (validate_report, report_receipt, reference_fasta),
    )
    for validator, receipt_path, target in cases:
        original = target.read_bytes()

        def mutate(paths: tuple[Path, ...], *, selected: Path = target) -> None:
            assert selected in paths
            selected.write_bytes(original + b"mutation-fault\n")

        with (
            fault_before_validation(receipt_path, mutate),
            pytest.raises(
                transaction_validation.ReportingTransactionError,
                match="roster changed during semantic validation",
            ),
        ):
            validator()
        target.write_bytes(original)


def test_artifact_validator_rejects_roster_membership_fault(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, _report_root = complete_reporting
    parent = built.summary_json_path.parent
    unexpected = parent / "unexpected.json"

    def add_record(paths: tuple[Path, ...]) -> None:
        assert built.summary_json_path in paths
        unexpected.write_text("{}\n", encoding="utf-8")

    with (
        fault_before_validation(built.summary_json_path, add_record),
        pytest.raises(
            transaction_validation.ReportingTransactionError,
            match="roster changed during semantic validation",
        ),
    ):
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.adapter_fixture.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
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

    validated = transaction_validation.validate_run_summary_transaction(
        package_root=PACKAGE_ROOT,
        artifact_source_root=adapter.root,
        run_id=adapter.run_id,
        run_contract=adapter.run_contract,
        inventory=adapter.inventory,
        analysis_policy=adapter.analysis_policy,
        output_root=adapter.output_root,
        profile=adapter_fixture.analysis_profile_v1(),
    )
    assert validated.receipt_path == adapter.manifest_path

    def create_intermediate_parent(paths: tuple[Path, ...]) -> None:
        assert missing in paths
        missing_parent.mkdir()

    with (
        fault_before_validation(adapter.manifest_path, create_intermediate_parent),
        pytest.raises(
            transaction_validation.ReportingTransactionError,
            match="roster changed during semantic validation",
        ),
    ):
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=adapter.root,
            run_id=adapter.run_id,
            run_contract=adapter.run_contract,
            inventory=adapter.inventory,
            analysis_policy=adapter.analysis_policy,
            output_root=adapter.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )


def test_each_validator_rejects_control_residue_injected_before_return(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    token = "123-" + "a" * 32
    artifact_dir = built.summary_json_path.parent
    report_dir = report_root / built.run_id

    def validate_artifact() -> None:
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.adapter_fixture.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )

    def validate_summary() -> None:
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )

    def validate_report() -> None:
        transaction_validation.validate_report_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=report_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )

    cases = (
        (
            validate_summary,
            built.summary_json_path,
            artifact_dir / f".artifact-index.{token}.RECOVERY.txt",
            False,
        ),
        (
            validate_report,
            report_dir / f"{built.run_id}.report_outputs.tsv",
            report_dir / f".run-report.{token}.tmp",
            True,
        ),
    )
    for validator, receipt_path, residue, is_directory in cases:

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

        with (
            fault_before_validation(receipt_path, inject_residue),
            pytest.raises(
                transaction_validation.ReportingTransactionError,
                match="owner control residue",
            ),
        ):
            validator()
        if is_directory:
            residue.rmdir()
        else:
            residue.unlink()


def test_preexisting_reporting_control_residue_fails_closed(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, _report_root = complete_reporting
    residue = built.summary_json_path.parent / f".{built.run_id}.artifact-index.lock"
    residue.write_text("foreign lock\n", encoding="utf-8")

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="owner control residue",
    ):
        transaction_validation.validate_run_summary_transaction(
            package_root=PACKAGE_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            analysis_policy=built.adapter_fixture.analysis_policy,
            output_root=built.adapter_fixture.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
        )
