"""Read-only validation contracts for complete reporting transactions."""

from __future__ import annotations

import argparse
import copy
import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from emrys import analyses
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.libraries.source_authority import (
    ArtifactSourceRoot,
    SourceCheckout,
)
from emrys.reporting import report, transaction_validation
from emrys.reporting._run_report import publication as report_publication
from emrys.reporting._run_report import receipt
from emrys.reporting._run_summary import builder as summary_builder
from emrys.reporting._run_summary import publication as summary_publication
from tests.contracts.orchestration.test_application_model_contracts import (
    successor_run_fixture,
)
from tests.orchestration.local_pilot.fixtures import workflow as workflow_fixture
from tests.reporting.fixtures.artifact_adapters_v1 import (
    build_fixture as adapter_fixture,
)
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as fixture

REPO_ROOT = Path(__file__).resolve().parents[2]


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
    fixture.publish_run_summary(built)


def _publish_report(arguments: argparse.Namespace) -> None:
    context = report.prepare_report(arguments)
    report_publication.publish_report(context, report.default_publication_ops())


def _publish_summary_with_commit(built: Any, commit: str) -> None:
    previous, _epoch = fixture.fixed_epoch()
    try:
        context = summary_builder.prepare_context(
            argparse.Namespace(
                run_id=built.run_id,
                artifact_receipt=built.artifact_receipt,
                output_root=built.output_root,
                execute=True,
            ),
            source_checkout=SourceCheckout(root=REPO_ROOT),
            artifact_source_root=ArtifactSourceRoot(root=built.root),
            deps=summary_builder.RunSummaryBuildDeps(
                matching_checkout_head_commit=lambda **_kwargs: commit,
            ),
        )
        summary_publication.publish_context(context)
    finally:
        fixture.restore_epoch(previous)


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
    _publish_report(arguments)
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
        profile=adapter_fixture.analysis_profile_v1(),
        receipt_ops=_fixture_receipt_ops(),
    )
    summary = transaction_validation.validate_run_summary_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_id=built.run_id,
        artifact_receipt=built.artifact_receipt,
        output_root=built.output_root,
        profile=adapter_fixture.analysis_profile_v1(),
        receipt_ops=_fixture_receipt_ops(),
    )
    rendered = transaction_validation.validate_report_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        output_root=report_root,
        profile=adapter_fixture.analysis_profile_v1(),
        receipt_ops=_fixture_receipt_ops(),
    )

    assert adapter.receipt_path == built.artifact_receipt
    assert summary.receipt_path == built.summary_receipt_path
    assert rendered.receipt_path.name == f"{built.run_id}.report_outputs.tsv"
    assert all(len(item.receipt_sha256) == 64 for item in (adapter, summary, rendered))
    assert adapter.verified_report_locations == ()
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
        relocated.receipt_path,
        relocated.output_root,
        relocated,
    )
    _publish_summary(built)

    validated = transaction_validation.validate_run_summary_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=root,
        run_id=built.run_id,
        artifact_receipt=built.artifact_receipt,
        output_root=built.output_root,
        profile=adapter_fixture.analysis_profile_v1(),
        receipt_ops=_fixture_receipt_ops(),
    )

    assert validated.receipt_path == built.summary_receipt_path


def test_explicit_module_publishes_and_readmits_v3_v5_reporting(
    tmp_path: Path,
) -> None:
    from emrys.reporting._artifact_index import context as artifact_context
    from emrys.reporting._artifact_index import core as artifact_core
    from emrys.reporting._artifact_index import publication as artifact_publication
    from emrys.reporting._run_report import receipt as report_receipt

    root = (tmp_path / "run").resolve()
    adapter = adapter_fixture.build_fixture(root, run_id="module_reporting")
    module = analyses.load_analysis_module(analyses.BUILTIN_PAIRED_CMH_MODULE_ID)
    policy = {
        "schema_version": "emrys.analysis-module-policy.v1",
        "analysis_id": adapter_fixture.PRIMARY_ANALYSIS_ID,
        "module": analyses.module_identity_record(module),
        "implementation_sha256": module.provider.package.sha256,
        "configuration": {
            "control_condition": "control",
            "treatment_condition": "treatment",
            "background_condition": None,
            "rna_ref": "A",
            "rna_alt": "G",
            "min_sample_dp": 1,
            "mean_dp_threshold": 0,
            "fdr_threshold": 0.05,
            "common_or_threshold": 1.2,
            "absolute_difference_threshold": 0.005,
            "background_max_fraction": 0.01,
        },
    }
    policy_path = root / "analysis_policy.json"
    policy_bytes = orchestration_contracts.canonical_json_bytes(policy)
    policy_path.write_bytes(policy_bytes)
    policy_sha256 = hashlib.sha256(policy_bytes).hexdigest()
    run_contract = adapter_fixture.build_run_contract()
    run_contract["primary_analysis_policy_sha256"] = policy_sha256
    run_contract["run_contract_sha256"] = (
        adapter_fixture.canonical_run_contract_sha256(
            {key: value for key, value in run_contract.items() if key != "run_contract_sha256"}
        )
    )
    adapter.run_contract.write_bytes(
        orchestration_contracts.canonical_json_bytes(run_contract)
    )
    profile = adapter_fixture.analysis_profile_v1()
    artifact = artifact_context.prepare_context(
        argparse.Namespace(
            run_id=adapter.run_id,
            run_contract=adapter.run_contract,
            analysis_policy=policy_path,
            profile=profile,
            inventory=adapter.inventory,
            output_root=adapter.output_root,
            execute=True,
        ),
        source_checkout=SourceCheckout(root=REPO_ROOT),
        artifact_source_root=ArtifactSourceRoot(root=root),
        identity_ops=artifact_context.ArtifactIdentityOps(
            matching_clean_checkout_head_commit=lambda **_kwargs: (
                artifact_core.get_git_commit(
                    source_root=REPO_ROOT,
                    sanitize_git_routing=True,
                )
            )
        ),
    )
    artifact_publication.publish_context(artifact)
    built = fixture.RunSummaryFixture(
        root,
        adapter.run_id,
        adapter.receipt_path,
        adapter.output_root,
        adapter,
    )
    summary = summary_builder.prepare_context(
        argparse.Namespace(
            run_id=built.run_id,
            artifact_receipt=built.artifact_receipt,
            analysis_policy=policy_path,
            output_root=built.output_root,
        ),
        source_checkout=SourceCheckout(root=REPO_ROOT),
        artifact_source_root=ArtifactSourceRoot(root=root),
    )
    summary_publication.publish_context(summary)
    summary_document = orchestration_contracts.load_json_object(
        built.summary_json_path
    )
    assert summary_document["schema_version"] == "3.0.0"
    assert summary_document["analysis_policy"] == {
        "path": str(policy_path),
        "sha256": policy_sha256,
        "size_bytes": len(policy_bytes),
    }

    report_root = root / "reports"
    report_arguments = argparse.Namespace(
        source_checkout=REPO_ROOT,
        artifact_source_root=root,
        run_summary=built.summary_json_path,
        analysis_policy=policy_path,
        output_root=report_root,
        execute=True,
    )
    report_context = report.prepare_report(report_arguments)
    report_publication.publish_report(
        report_context,
        report.default_publication_ops(),
    )
    document = report_receipt.read_receipt_tsv(report_context.output_receipt)
    assert document["schema_version"] == "5.0.0"
    assert document["scientific_renderer"]["module_id"] == "emrys.paired-cmh"
    assert document["scientific_renderer"]["content_sha256"] == (
        report_context.scientific_renderer["content_sha256"]
    )
    assert document["scientific_renderer"]["core_support"]["content_sha256"] == (
        report_context.render_metadata["renderer_package_sha256"]
    )
    assert document["evidence_renderer"]["content_sha256"] == (
        report_context.render_metadata["renderer_package_sha256"]
    )
    assert len(document["outputs"]) == 3
    validated = transaction_validation.validate_report_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=root,
        run_summary=built.summary_json_path,
        analysis_policy=policy_path,
        profile=profile,
        output_root=report_root,
        receipt_ops=_fixture_receipt_ops(),
    )
    assert validated.receipt_path == report_context.output_receipt


def test_historical_artifact_validation_uses_recorded_producer_roster(
    complete_reporting: tuple[Any, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.reporting._artifact_index import api as artifact_api
    from emrys.reporting._artifact_index import records as artifact_records

    built, _report_root = complete_reporting
    summary = fixture.ARTIFACT_CONTRACTS.load_json_object(
        built.summary_json_path,
        "run summary",
    )
    recorded_producer = REPO_ROOT / artifact_records.STEP_PRODUCERS["08"]
    monkeypatch.setitem(
        artifact_records.STEP_PRODUCERS,
        "08",
        "src/emrys/reporting/transaction_validation.py",
    )

    def reject_live_producer_binding(paths: tuple[Path, ...]) -> None:
        assert recorded_producer not in paths

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
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=_fixture_receipt_ops(),
        )

    historical_artifact = (
        transaction_validation._validate_historical_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=_fixture_receipt_ops(
                before_final_snapshot=reject_live_producer_binding,
            ),
        )
    )
    historical_summary = transaction_validation.validate_run_summary_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_id=built.run_id,
        artifact_receipt=built.artifact_receipt,
        output_root=built.output_root,
        profile=adapter_fixture.analysis_profile_v1(),
        receipt_ops=_fixture_receipt_ops(
            before_final_snapshot=reject_live_producer_binding,
        ),
        recorded_producer_commit=str(summary["provenance"]["git_commit"]),
        expected_run_contract=built.adapter_fixture.run_contract,
        expected_inventory=built.adapter_fixture.inventory,
    )

    assert historical_artifact.receipt_path == built.artifact_receipt
    assert historical_summary.receipt_path == built.summary_receipt_path
    artifact_receipt = artifact_api.read_exact_tsv(
        built.artifact_receipt,
        artifact_api.ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    index_rows = artifact_api.read_exact_tsv(
        Path(artifact_receipt["artifacts_index_path"]),
        artifact_api.ARTIFACT_INDEX_HEADER,
    )
    step08 = next(row for row in index_rows if row["step_id"] == "08")
    recorded = fixture.ARTIFACT_CONTRACTS.load_json_object(
        Path(step08["record_path"]),
        "Step 08 artifact record",
    )
    assert recorded["implementation"]["evidence"][0]["path"].endswith(
        "/cohort_candidate_preprocessing/producer.py"
    )


def test_historical_artifact_validation_binds_one_record_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.reporting._artifact_index import api as artifact_api
    from emrys.reporting._artifact_index import validation as artifact_validation

    built = fixture.build_fixture(tmp_path / "run")
    receipt_row = artifact_api.read_exact_tsv(
        built.artifact_receipt,
        artifact_api.ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    index_rows = artifact_api.read_exact_tsv(
        Path(receipt_row["artifacts_index_path"]),
        artifact_api.ARTIFACT_INDEX_HEADER,
    )
    record_path = Path(index_rows[0]["record_path"])
    admitted = record_path.read_bytes()
    validate = artifact_validation.validate_published_transaction

    def swap_live_record(**kwargs: Any) -> None:
        assert kwargs["admitted_bytes"][record_path] == admitted
        record_path.write_bytes(b"{}\n")
        try:
            validate(**kwargs)
        finally:
            record_path.write_bytes(admitted)

    monkeypatch.setattr(
        artifact_validation,
        "validate_published_transaction",
        swap_live_record,
    )
    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="roster changed during semantic validation",
    ):
        transaction_validation._validate_historical_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=_fixture_receipt_ops(),
        )


def test_historical_artifact_validation_never_opens_index_selected_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.reporting._artifact_index import api as artifact_api
    from emrys.reporting._artifact_index import records as artifact_records

    built = fixture.build_fixture(tmp_path / "run")
    receipt = artifact_api.read_exact_tsv(
        built.artifact_receipt,
        artifact_api.ARTIFACT_RECEIPT_HEADER,
        exact_rows=1,
    )[0]
    index_path = Path(receipt["artifacts_index_path"])
    index_rows = artifact_api.read_exact_tsv(
        index_path,
        artifact_api.ARTIFACT_INDEX_HEADER,
    )
    outside = (tmp_path / "outside.json").resolve()
    outside.write_text("not an artifact record\n", encoding="utf-8")
    index_rows[0]["record_path"] = str(outside)
    index_bytes = artifact_records.tsv_bytes(
        artifact_api.ARTIFACT_INDEX_HEADER,
        index_rows,
    )
    index_path.write_bytes(index_bytes)
    receipt["artifacts_index_sha256"] = hashlib.sha256(index_bytes).hexdigest()
    built.artifact_receipt.write_bytes(
        artifact_records.tsv_bytes(
            artifact_api.ARTIFACT_RECEIPT_HEADER,
            [receipt],
        )
    )
    snapshot = transaction_validation._snapshot_receipt

    def reject_outside(path: Path) -> Any:
        assert path != outside
        return snapshot(path)

    monkeypatch.setattr(transaction_validation, "_snapshot_receipt", reject_outside)
    with pytest.raises(
        artifact_api.ArtifactIndexError,
        match="Published record path is invalid",
    ):
        transaction_validation._validate_historical_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            receipt_ops=_fixture_receipt_ops(),
        )


def test_historical_report_admission_preserves_noncurrent_verified_bytes(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    output_dir = report_root / built.run_id
    scientific = output_dir / f"{built.run_id}.scientific_report.html"
    receipt_path = output_dir / f"{built.run_id}.report_outputs.tsv"
    scientific.write_bytes(scientific.read_bytes() + b"\n<!-- legacy 5.1.0 -->\n")
    document = receipt.read_receipt_tsv(receipt_path)
    document["provenance"]["producer_version"] = "5.1.0"
    descriptor = next(
        output
        for output in document["outputs"]
        if output["output_id"] == "scientific-report-html"
    )
    descriptor["sha256"] = hashlib.sha256(scientific.read_bytes()).hexdigest()
    descriptor["size_bytes"] = scientific.stat().st_size
    receipt_path.write_bytes(receipt.receipt_tsv_bytes(document))

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="current deterministic projection",
    ):
        transaction_validation.validate_report_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            output_root=report_root,
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=_fixture_receipt_ops(),
        )

    admitted = transaction_validation._validate_historical_report_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_id=built.run_id,
        run_summary=built.summary_json_path,
        output_root=report_root,
        expected_source_commit=document["provenance"]["git_commit"],
        expected_run_contract=built.adapter_fixture.run_contract,
        expected_inventory=built.adapter_fixture.inventory,
        receipt_ops=_fixture_receipt_ops(),
    )
    assert admitted.receipt_path == receipt_path
    assert admitted.verified_report_locations == (
        ("scientific-report-html", scientific),
        (
            "evidence-report-html",
            output_dir / f"{built.run_id}.evidence_report.html",
        ),
    )


def test_historical_report_admission_uses_each_recorded_producer_identity(
    tmp_path: Path,
) -> None:
    built = fixture.build_fixture(tmp_path / "run")
    summary_commit = "b" * 40
    report_commit = "c" * 40
    assert summary_commit != workflow_fixture.source_checkout_commit()
    _publish_summary_with_commit(built, summary_commit)
    report_root = built.root / "reports"
    arguments = argparse.Namespace(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        output_root=report_root,
        execute=True,
    )
    _publish_report(arguments)
    receipt_path = report_root / built.run_id / f"{built.run_id}.report_outputs.tsv"
    document = receipt.read_receipt_tsv(receipt_path)
    current_report_commit = str(document["provenance"]["git_commit"])
    document["provenance"]["git_commit"] = report_commit
    document["provenance"]["producer_version"] = "5.1.0"
    for output in document["outputs"]:
        path = Path(str(output["path"]))
        path.write_bytes(
            path.read_bytes().replace(
                current_report_commit.encode("ascii"),
                report_commit.encode("ascii"),
            )
        )
        output["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        output["size_bytes"] = path.stat().st_size
    receipt_path.write_bytes(receipt.receipt_tsv_bytes(document))

    admitted = transaction_validation._validate_historical_report_transaction(
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_id=built.run_id,
        run_summary=built.summary_json_path,
        output_root=report_root,
        expected_source_commit=report_commit,
        expected_run_contract=built.adapter_fixture.run_contract,
        expected_inventory=built.adapter_fixture.inventory,
        receipt_ops=_fixture_receipt_ops(),
    )
    assert admitted.receipt_path == receipt_path


def test_historical_report_admission_rechecks_transitive_native_inputs(
    complete_reporting: tuple[Any, Path],
) -> None:
    built, report_root = complete_reporting
    native_source = built.adapter_fixture.source_for("sample.SYNTH_A.star_log")
    receipt_path = report_root / built.run_id / f"{built.run_id}.report_outputs.tsv"
    document = receipt.read_receipt_tsv(receipt_path)

    def mutate_native(paths: tuple[Path, ...]) -> None:
        assert native_source in paths
        native_source.write_text("mutated during historical read\n", encoding="utf-8")

    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="roster changed during semantic validation",
    ):
        transaction_validation._validate_historical_report_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_summary=built.summary_json_path,
            output_root=report_root,
            expected_source_commit=document["provenance"]["git_commit"],
            expected_run_contract=built.adapter_fixture.run_contract,
            expected_inventory=built.adapter_fixture.inventory,
            receipt_ops=_fixture_receipt_ops(before_final_snapshot=mutate_native),
        )


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
        source_checkout=REPO_ROOT,
        artifact_source_root=built.root,
        run_summary=built.summary_json_path,
        output_root=report_root,
        profile=adapter_fixture.analysis_profile_v1(),
        receipt_ops=_fixture_receipt_ops(),
    )

    assert True in hash_modes
    assert hash_modes[-1] is False
    assert hash_modes.count(False) == 1


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
            orchestration_contracts.load_json_object(built.config_path),
        )


def test_fixed_dispatcher_accepts_successor_run_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis, plan, run, profile, attempt, _resources = successor_run_fixture()
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
        / f"{run.run_id}.artifact_receipt.tsv"
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
        "attest_source_checkout",
        lambda **_kwargs: "stable-source",
    )
    monkeypatch.setattr(
        transaction_validation,
        "validate_artifact_index_transaction",
        lambda **kwargs: observed.update(kwargs) or expected,
    )

    assert (
        transaction_validation.validate_receipt(
            "artifact_index",
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


def test_fixed_dispatcher_admits_historical_report_only_at_legacy_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _analysis, _plan, run, profile, attempt, _resources = successor_run_fixture()
    current_attempt = copy.deepcopy(attempt)
    legacy_profile = copy.deepcopy(profile)
    current_profile = copy.deepcopy(profile)
    for template in current_profile["artifact_templates"]:
        template["source_path_template"] = str(
            template["source_path_template"]
        ).replace("results/", "products/native/", 1)
    attempt["profile_sha256"] = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(legacy_profile)
    ).hexdigest()
    current_attempt["profile_sha256"] = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(current_profile)
    ).hexdigest()
    historical_commit = "f" * 40
    attempt["source_checkout"]["commit"] = historical_commit
    run_root = (tmp_path / run.run_id).resolve()
    receipt_path = (
        run_root
        / "products"
        / "report"
        / run.run_id
        / f"{run.run_id}.report_outputs.tsv"
    )
    expected = transaction_validation.ValidatedTransaction(
        receipt_path=receipt_path,
        receipt_sha256="c" * 64,
    )
    summary_receipt = (
        run_root
        / "products"
        / "artifact-summary"
        / run.run_id
        / f"{run.run_id}.run_summary_receipt.tsv"
    )
    summary_receipt.parent.mkdir(parents=True)
    summary_receipt.write_bytes(b"admitted summary receipt\n")
    predecessor = transaction_validation.ValidatedTransaction(
        receipt_path=summary_receipt,
        receipt_sha256=hashlib.sha256(summary_receipt.read_bytes()).hexdigest(),
    )
    reporting_root = f"contract/reporting-inputs/{attempt['workflow_attempt_id']}"
    config = {
        "reporting_run_contract_path": {
            "path": f"{reporting_root}/reporting_run_contract.json"
        },
        "artifact_inventory_path": {"path": f"{reporting_root}/artifact_inventory.tsv"},
    }
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        transaction_validation,
        "attest_source_checkout",
        lambda **_kwargs: pytest.fail(
            "historical read required the current reader to be its old producer"
        ),
    )
    monkeypatch.setattr(
        transaction_validation,
        "_validate_historical_report_transaction",
        lambda **kwargs: observed.update(kwargs) or expected,
    )

    assert (
        transaction_validation.validate_receipt(
            "html_report",
            receipt_path,
            run_root,
            run.record,
            legacy_profile,
            attempt,
            config,
            historical_read=True,
            validated_predecessor=predecessor,
        )
        == expected
    )
    assert observed["output_root"] == run_root / "products" / "report"
    assert observed["expected_source_commit"] == historical_commit

    current_receipt = (
        run_root
        / "results"
        / "reports"
        / run.run_id
        / f"{run.run_id}.report_outputs.tsv"
    )
    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="requires the bound legacy profile",
    ):
        transaction_validation.validate_receipt(
            "html_report",
            current_receipt,
            run_root,
            run.record,
            current_profile,
            current_attempt,
            config,
            historical_read=True,
        )


def test_public_historical_dispatch_rejects_symlinks_before_parsing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emrys.contracts.artifacts import api as artifact_contracts
    from emrys.reporting._artifact_index import api as artifact_api

    _analysis, _plan, run, profile, attempt, _resources = successor_run_fixture()
    attempt["profile_sha256"] = hashlib.sha256(
        orchestration_contracts.canonical_json_bytes(profile)
    ).hexdigest()
    attempt["source_checkout"]["commit"] = "f" * 40
    run_root = (tmp_path / run.run_id).resolve()
    artifact_output = run_root / "products" / "artifact-summary" / run.run_id
    artifact_output.mkdir(parents=True)
    reporting_root = f"contract/reporting-inputs/{attempt['workflow_attempt_id']}"
    config = {
        "reporting_run_contract_path": {
            "path": f"{reporting_root}/reporting_run_contract.json"
        },
        "artifact_inventory_path": {"path": f"{reporting_root}/artifact_inventory.tsv"},
    }

    followed: list[Path] = []
    target_receipt = tmp_path / "outside-run-summary-receipt.tsv"
    target_receipt.write_text("outside\n", encoding="utf-8")
    summary_receipt = artifact_output / f"{run.run_id}.run_summary_receipt.tsv"
    summary_receipt.symlink_to(target_receipt)
    original_read_tsv = artifact_api.read_exact_tsv

    def track_tsv(path: Path, *args: Any, **kwargs: Any) -> Any:
        if Path(path) == summary_receipt:
            followed.append(summary_receipt)
        return original_read_tsv(path, *args, **kwargs)

    monkeypatch.setattr(artifact_api, "read_exact_tsv", track_tsv)
    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="canonical and nonsymlink",
    ):
        transaction_validation.validate_receipt(
            "run_summary",
            summary_receipt,
            run_root,
            run.record,
            profile,
            attempt,
            config,
            historical_read=True,
        )
    assert followed == []

    target_summary = tmp_path / "outside-run-summary.json"
    target_summary.write_text("{}\n", encoding="utf-8")
    run_summary = artifact_output / f"{run.run_id}.run_summary.json"
    run_summary.symlink_to(target_summary)
    report_receipt = (
        run_root
        / "products"
        / "report"
        / run.run_id
        / f"{run.run_id}.report_outputs.tsv"
    )
    original_load_json = artifact_contracts.load_json_object

    def track_json(path: Path, *args: Any, **kwargs: Any) -> Any:
        if Path(path) == run_summary:
            followed.append(run_summary)
        return original_load_json(path, *args, **kwargs)

    monkeypatch.setattr(artifact_contracts, "load_json_object", track_json)
    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="canonical and nonsymlink",
    ):
        transaction_validation.validate_receipt(
            "html_report",
            report_receipt,
            run_root,
            run.record,
            profile,
            attempt,
            config,
            historical_read=True,
        )
    assert followed == []

    run_summary.unlink()
    run_summary.write_bytes(
        orchestration_contracts.canonical_json_bytes(
            {"run_id": str((tmp_path / "outside-run").resolve())}
        )
    )
    snapshots: list[Path] = []
    original_snapshot_receipt = transaction_validation._snapshot_receipt

    def track_snapshot(path: Path) -> Any:
        snapshots.append(path)
        return original_snapshot_receipt(path)

    monkeypatch.setattr(
        transaction_validation,
        "_snapshot_receipt",
        track_snapshot,
    )
    with pytest.raises(
        transaction_validation.ReportingTransactionError,
        match="Run summary binds another Run",
    ):
        transaction_validation.validate_receipt(
            "html_report",
            report_receipt,
            run_root,
            run.record,
            profile,
            attempt,
            config,
            historical_read=True,
        )
    assert snapshots == [run_summary]


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
            profile=adapter_fixture.analysis_profile_v1(),
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
            profile=adapter_fixture.analysis_profile_v1(),
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
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=_fixture_receipt_ops(
                before_final_snapshot=replace_receipt,
            ),
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

    def validate_artifact(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_artifact_index_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            run_contract=built.adapter_fixture.run_contract,
            inventory=built.adapter_fixture.inventory,
            output_root=built.adapter_fixture.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=ops,
        )

    def validate_summary(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_run_summary_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            artifact_receipt=built.artifact_receipt,
            output_root=built.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=ops,
        )

    def validate_report(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_report_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            output_root=report_root,
            profile=adapter_fixture.analysis_profile_v1(),
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
        (validate_report, mutation_spectrum),
        (validate_report, reference_fasta),
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
            profile=adapter_fixture.analysis_profile_v1(),
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
        profile=adapter_fixture.analysis_profile_v1(),
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
            profile=adapter_fixture.analysis_profile_v1(),
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
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=ops,
        )

    def validate_summary(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_run_summary_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_id=built.run_id,
            artifact_receipt=built.artifact_receipt,
            output_root=built.output_root,
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=ops,
        )

    def validate_report(ops: transaction_validation.ReceiptValidationOps) -> None:
        transaction_validation.validate_report_transaction(
            source_checkout=REPO_ROOT,
            artifact_source_root=built.root,
            run_summary=built.summary_json_path,
            output_root=report_root,
            profile=adapter_fixture.analysis_profile_v1(),
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
            profile=adapter_fixture.analysis_profile_v1(),
            receipt_ops=_fixture_receipt_ops(),
        )
