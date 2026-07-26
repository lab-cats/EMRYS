"""Focused integration and transaction tests for artifact-run-summary."""

from __future__ import annotations

import csv
import copy
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence

import pytest
from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "build_run_summary.py"
FIXTURE_BUILDER = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "artifact_run_summary_v1"
    / "build_fixture.py"
)
FIXED_EPOCH = "1700000000"


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FIXTURE = load_module(
    "norad_artifact_run_summary_fixture_builder",
    FIXTURE_BUILDER,
)
RUN_SUMMARY = load_module("norad_artifact_run_summary", SCRIPT)
CONTRACTS = RUN_SUMMARY.contracts


@pytest.fixture
def run_summary_fixture(tmp_path: Path) -> Any:
    return FIXTURE.build_fixture(tmp_path / "fixture")


def run_cli(
    fixture: Any,
    *,
    execute: bool = False,
    arguments: Sequence[str] | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    if extra_env:
        environment.update(extra_env)
    cli_arguments = (
        list(arguments)
        if arguments is not None
        else fixture.command_args(execute=execute)
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT), *cli_arguments],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def read_tsv_header(path: Path) -> tuple[str, ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream, delimiter="\t")
        return tuple(next(reader))


def write_tsv(
    path: Path,
    header: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(header),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> dict[str, Any]:
    return CONTRACTS.load_json_object(path, f"test JSON {path.name}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def summary_snapshot(fixture: Any) -> dict[str, bytes]:
    return {
        path.name: path.read_bytes()
        for path in fixture.summary_paths
        if path.is_file()
    }


def assert_no_summary_outputs(fixture: Any) -> None:
    assert not any(path.exists() or path.is_symlink() for path in fixture.summary_paths)
    assert not fixture.lock_path.exists()
    assert not any(
        path.name.startswith(
            (
                ".run-summary.",
                f".{fixture.run_id}.run-summary.",
                f".{fixture.run_id}.run-summary-",
            )
        )
        for path in fixture.output_dir.iterdir()
    )


def context_for(fixture: Any) -> Any:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    try:
        arguments = RUN_SUMMARY.parse_arguments(
            fixture.command_args(execute=True)
        )
        return RUN_SUMMARY.prepare_context(arguments)
    finally:
        if previous is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous


def validate_summary_document(fixture: Any) -> dict[str, Any]:
    document = read_json(fixture.summary_json_path)
    schemas, registry = CONTRACTS.load_schema_registry()
    validator = Draft202012Validator(
        schemas["run-summary"],
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = list(validator.iter_errors(document))
    assert errors == [], "\n".join(error.message for error in errors)
    CONTRACTS.validate_run_summary_semantics(document)

    artifact_receipt = read_tsv(fixture.artifact_receipt)[0]
    inventory = Path(artifact_receipt["inventory_path"])
    rows = CONTRACTS.validate_inventory(inventory)
    CONTRACTS.reconcile_document_inventory(
        "run-summary",
        document,
        rows,
        inventory,
    )
    return document


def test_help_and_dry_run_validate_without_summary_writes(
    run_summary_fixture: Any,
) -> None:
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    result = run_cli(run_summary_fixture)

    assert help_result.returncode == 0, help_result.stderr
    for option in (
        "--run-id",
        "--artifact-receipt",
        "--output-root",
        "--science-review-summary",
        "--execute",
    ):
        assert option in help_result.stdout
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout.lower()
    assert run_summary_fixture.run_id in result.stdout
    assert "receipt" in result.stdout.lower()
    assert_no_summary_outputs(run_summary_fixture)


def test_execute_publishes_exact_canonical_schema_valid_transaction(
    run_summary_fixture: Any,
) -> None:
    result = run_cli(run_summary_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    assert all(path.is_file() for path in run_summary_fixture.summary_paths)
    document = validate_summary_document(run_summary_fixture)
    assert run_summary_fixture.summary_json_path.read_bytes() == (
        canonical_json_bytes(document)
    )
    assert read_tsv_header(run_summary_fixture.summary_tsv_path) == tuple(
        RUN_SUMMARY.RUN_SUMMARY_HEADER
    )
    assert read_tsv_header(run_summary_fixture.qc_summary_path) == tuple(
        RUN_SUMMARY.QC_SUMMARY_HEADER
    )
    assert read_tsv_header(run_summary_fixture.summary_receipt_path) == tuple(
        RUN_SUMMARY.RUN_SUMMARY_RECEIPT_HEADER
    )
    receipt_rows = read_tsv(run_summary_fixture.summary_receipt_path)
    assert len(receipt_rows) == 1
    receipt = receipt_rows[0]
    assert receipt["run_id"] == run_summary_fixture.run_id
    assert receipt["transaction_state"] == "complete"
    assert receipt["published_output_count"] == "4"
    assert receipt["run_summary_json_sha256"] == sha256_file(
        run_summary_fixture.summary_json_path
    )
    assert receipt["run_summary_tsv_sha256"] == sha256_file(
        run_summary_fixture.summary_tsv_path
    )
    assert receipt["qc_summary_tsv_sha256"] == sha256_file(
        run_summary_fixture.qc_summary_path
    )
    assert document["summary_state"] == "complete"
    assert_no_summary_residue_after_success(run_summary_fixture)


def assert_no_summary_residue_after_success(fixture: Any) -> None:
    assert not fixture.lock_path.exists()
    owned_names = {path.name for path in fixture.summary_paths}
    assert not any(
        path.name not in owned_names
        and (
            "run-summary" in path.name
            or "run_summary" in path.name
        )
        and path.name.startswith(".")
        for path in fixture.output_dir.iterdir()
    )


def test_fixed_epoch_rerender_keeps_json_and_views_byte_identical(
    run_summary_fixture: Any,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = {
        path.name: path.read_bytes()
        for path in run_summary_fixture.summary_paths[:3]
    }

    second = run_cli(run_summary_fixture, execute=True)

    assert second.returncode == 0, second.stderr
    assert {
        path.name: path.read_bytes()
        for path in run_summary_fixture.summary_paths[:3]
    } == before
    validate_summary_document(run_summary_fixture)


def test_unrelated_files_and_decoy_science_are_ignored_and_preserved(
    run_summary_fixture: Any,
) -> None:
    unrelated = run_summary_fixture.output_dir / "unrelated.run_summary.json"
    unrelated_payload = b'{"unrelated":true}\n'
    unrelated.write_bytes(unrelated_payload)
    decoy = (
        run_summary_fixture.output_dir
        / "decoy.step09c_review_summary.tsv"
    )
    decoy.write_text(
        "overall_science_status\nscience_review_complete_exploratory\n",
        encoding="utf-8",
    )

    result = run_cli(run_summary_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    document = validate_summary_document(run_summary_fixture)
    assert unrelated.read_bytes() == unrelated_payload
    assert decoy.is_file()
    assert document["science_status"] == "evidence_incomplete"
    assert document["scientific_review"]["record_state"] == "missing"
    assert document["scientific_review"]["record"] is None
    assert document["scientific_review"]["source"] is None


def test_run_id_mismatch_and_tampered_artifact_receipt_fail_closed(
    tmp_path: Path,
) -> None:
    wrong_run = FIXTURE.build_fixture(tmp_path / "wrong_run")
    arguments = wrong_run.command_args()
    arguments[arguments.index("--run-id") + 1] = "different_run"
    mismatch = run_cli(wrong_run, arguments=arguments)
    assert mismatch.returncode != 0
    assert_no_summary_outputs(wrong_run)

    tampered = FIXTURE.build_fixture(tmp_path / "tampered")
    header = read_tsv_header(tampered.artifact_receipt)
    rows = read_tsv(tampered.artifact_receipt)
    rows[0]["artifacts_index_sha256"] = "f" * 64
    write_tsv(tampered.artifact_receipt, header, rows)
    result = run_cli(tampered)
    assert result.returncode != 0
    assert_no_summary_outputs(tampered)


@pytest.mark.parametrize(
    "science_status",
    [
        "evidence_incomplete",
        "science_review_complete_exploratory",
    ],
)
def test_explicit_science_summary_is_normalized_and_identity_bound(
    tmp_path: Path,
    science_status: str,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / science_status,
        science_status=science_status,
    )

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    document = validate_summary_document(fixture)
    review = document["scientific_review"]
    assert document["science_status"] == science_status
    assert review["overall_status"] == science_status
    assert review["record_state"] == "present"
    assert review["source"]["path"] == str(fixture.science_review_summary)
    assert review["source"]["sha256"] == sha256_file(
        fixture.science_review_summary
    )
    assert review["record"]["run_id"] == fixture.run_id
    assert review["record"]["run_contract"] == document["run_contract"]
    assert review["record"]["scientific_state"]["overall_status"] == (
        science_status
    )
    assert review["record"]["review_id"] == fixture.step09c_fixture.review_id
    limitation = review["record"]["limitations"][0]
    assert limitation["category"]
    assert limitation["severity"]
    assert limitation["mitigation"]
    assert limitation["owner"]
    assert limitation["review_date"]


def test_explicit_science_preserves_human_reviewer_names(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "human-names",
        science_status="evidence_incomplete",
        human_names=True,
    )

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = validate_summary_document(fixture)["scientific_review"]["record"]
    assert record["review_metadata"]["reviewer"] == "Jane Doe"
    assert (
        record["review_metadata"]["decision_owner"]
        == "Scientific Review Team"
    )
    assert record["review_metadata"]["git_commit"] == "local_build"
    assert all(
        row["reviewer"] == "Jane Doe"
        for row in record["evidence_records"]
    )
    assert all(
        row["owner"] == "Scientific Review Team"
        for row in record["evidence_records"]
    )
    assert all(
        decision["reviewer"] == "Jane Doe"
        for decision in record["decisions"].values()
        if decision["status"] == "recorded"
    )


def test_multi_scope_computational_evidence_preserves_underlying_paths(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "computational-scope-bundle",
        science_status="evidence_incomplete",
        computational_scope_bundle=True,
    )

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = validate_summary_document(fixture)["scientific_review"]["record"]
    references = record["computational_status"]["evidence"]
    assert [reference["role"] for reference in references] == [
        "local_test",
        "runtime_log",
        "runtime_output",
        "cluster_dry_run",
        "cluster_scheduler",
        "cluster_log",
        "cluster_output",
    ]
    assert len({reference["path"] for reference in references}) == 7
    for reference in references:
        path = Path(reference["path"])
        assert path.is_file()
        assert reference["sha256"] == sha256_file(path)
        assert "computational_evidence" in path.parts


def test_explicit_missing_science_categories_remain_missing_without_invented_dates(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "missing_science",
        science_status="evidence_incomplete",
        missing_categories=True,
    )

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    document = validate_summary_document(fixture)
    record = document["scientific_review"]["record"]
    assert record is not None
    assert record["scientific_state"]["overall_status"] == "evidence_incomplete"
    assert all(
        category["status"] == "missing"
        for category in record["evidence_categories"].values()
    )
    assert all(
        len(category["evidence_ids"]) == 1
        for category in record["evidence_categories"].values()
    )
    missing_records = [
        evidence
        for evidence in record["evidence_records"]
        if evidence["category"] != "computational_validation"
    ]
    assert len(missing_records) == len(record["evidence_categories"])
    assert all(evidence["status"] == "missing" for evidence in missing_records)
    assert all(evidence["source"] is None for evidence in missing_records)
    assert all(evidence["evidence_date"] is None for evidence in missing_records)


def test_mixed_science_category_retains_source_free_evidence_provenance(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "mixed_science",
        science_status="evidence_incomplete",
        mixed_categories=True,
        mixed_computational=True,
    )

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    document = validate_summary_document(fixture)
    record = document["scientific_review"]["record"]
    category = record["evidence_categories"]["qc_funnel"]
    assert category["status"] == "incomplete"
    assert len(category["evidence_ids"]) == 3
    evidence = {
        row["evidence_id"]: row
        for row in record["evidence_records"]
        if row["category"] == "qc_funnel"
    }
    assert set(evidence) == set(category["evidence_ids"])
    missing = evidence["e_qc_funnel_missing"]
    assert missing["status"] == "missing"
    assert missing["source"] is None
    assert missing["evidence_date"] is None
    assert missing["reviewer"]
    assert missing["owner"]
    assert missing["policy_version"]
    not_applicable = evidence["e_qc_funnel_not_applicable"]
    assert not_applicable["status"] == "not_applicable"
    assert not_applicable["source"] is None
    assert not_applicable["evidence_date"] is None
    assert not_applicable["not_applicable_reason"] == (
        "Synthetic evidence dimension is not applicable."
    )
    computational = {
        row["evidence_id"]: row
        for row in record["evidence_records"]
        if row["category"] == "computational_validation"
    }
    assert set(computational) == {
        "e_computational",
        "e_computational_missing",
        "e_computational_not_applicable",
    }
    assert computational["e_computational_missing"]["evidence_date"] is None
    assert (
        computational["e_computational_not_applicable"]["evidence_date"]
        is None
    )
    assert [
        reference["evidence_id"]
        for reference in record["computational_status"]["evidence"]
    ] == ["e_computational"]


def test_qc_view_keeps_all_repeated_metrics_but_json_ids_are_unique(
    run_summary_fixture: Any,
) -> None:
    result = run_cli(run_summary_fixture, execute=True)
    assert result.returncode == 0, result.stderr
    document = validate_summary_document(run_summary_fixture)
    index_rows = read_tsv(
        run_summary_fixture.adapter_fixture.artifacts_path
    )
    artifact_metrics = []
    for index_row in index_rows:
        artifact = read_json(Path(index_row["record_path"]))
        artifact_metrics.extend(artifact["metrics"])

    qc_rows = read_tsv(run_summary_fixture.qc_summary_path)
    json_metric_ids = [
        metric["metric_id"] for metric in document["qc_metrics"]
    ]
    source_counts = Counter(
        metric["metric_id"] for metric in artifact_metrics
    )

    assert len(qc_rows) == len(artifact_metrics)
    assert len(json_metric_ids) == len(set(json_metric_ids))
    assert source_counts["source_row_count"] > 1
    assert sum(
        row["metric_id"] == "source_row_count" for row in qc_rows
    ) == source_counts["source_row_count"]
    assert all(
        row.get("source_artifact_id") or row.get("artifact_id")
        for row in qc_rows
    )


def test_complete_summary_preserves_required_missing_artifact_state(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_missing_fixture(tmp_path / "missing")

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    document = validate_summary_document(fixture)
    assert document["summary_state"] == "complete"
    assert document["computational_rollup"]["missing_artifact_count"] >= 1
    missing = [
        artifact
        for artifact in document["artifacts"]
        if artifact["availability_status"] == "missing"
    ]
    assert missing
    assert any(
        scope["aggregate_state"] in {"missing", "incomplete"}
        for scope in document["expected_scopes"]
    )
    assert document["science_status"] == "evidence_incomplete"


def test_partial_prior_summary_and_foreign_lock_are_preserved(
    tmp_path: Path,
) -> None:
    partial = FIXTURE.build_fixture(tmp_path / "partial")
    partial_payload = b'{"partial":true}\n'
    partial.summary_json_path.write_bytes(partial_payload)

    partial_result = run_cli(partial, execute=True)

    assert partial_result.returncode != 0
    assert partial.summary_json_path.read_bytes() == partial_payload
    assert not any(path.exists() for path in partial.summary_paths[1:])

    locked = FIXTURE.build_fixture(tmp_path / "locked")
    lock_payload = b"foreign run-summary lock\n"
    locked.lock_path.write_bytes(lock_payload)

    locked_result = run_cli(locked, execute=True)

    assert locked_result.returncode != 0
    assert locked.lock_path.read_bytes() == lock_payload
    assert not any(path.exists() for path in locked.summary_paths)


def test_replacement_publication_failure_restores_prior_transaction(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = summary_snapshot(run_summary_fixture)
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY.os.replace
    failed = False

    def fail_qc_publication(source: Any, destination: Any) -> None:
        nonlocal failed
        if (
            not failed
            and Path(destination) == run_summary_fixture.qc_summary_path
            and ".tmp" in Path(source).name
        ):
            failed = True
            raise OSError("injected run-summary replacement failure")
        real_replace(source, destination)

    monkeypatch.setattr(RUN_SUMMARY.os, "replace", fail_qc_publication)

    with pytest.raises(
        Exception,
        match="injected run-summary replacement failure",
    ):
        RUN_SUMMARY.publish_context(context)

    assert failed
    assert summary_snapshot(run_summary_fixture) == before
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_publication_installs_and_restores_signal_handlers(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    watched = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    original = {signum: signal.getsignal(signum) for signum in watched}
    real_install = RUN_SUMMARY.adapter.install_publication_signal_handlers
    real_restore = RUN_SUMMARY.adapter.restore_signal_handlers
    events: list[tuple[str, Any]] = []

    def track_install() -> dict[int, Any]:
        assert run_summary_fixture.lock_path.is_file()
        handlers = real_install()
        events.append(("install", handlers))
        return handlers

    def track_restore(handlers: Mapping[int, Any]) -> None:
        events.append(("restore", dict(handlers)))
        real_restore(handlers)

    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "install_publication_signal_handlers",
        track_install,
    )
    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "restore_signal_handlers",
        track_restore,
    )

    context = context_for(run_summary_fixture)
    RUN_SUMMARY.publish_context(context)

    assert [event[0] for event in events] == ["install", "restore"]
    assert events[0][1] == original
    assert events[1][1] == original
    assert {signum: signal.getsignal(signum) for signum in watched} == original
    RUN_SUMMARY.validate_published_run_summary(context)
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_signal_handler_install_failure_releases_owned_lock(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)

    def fail_install() -> dict[int, Any]:
        raise ValueError("injected signal-handler installation failure")

    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "install_publication_signal_handlers",
        fail_install,
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="Could not install",
    ):
        RUN_SUMMARY.publish_context(context)

    assert_no_summary_outputs(run_summary_fixture)


def test_partial_signal_handler_install_restores_original_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    watched = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    original_handlers = {
        signum: signal.getsignal(signum) for signum in watched
    }
    real_signal = RUN_SUMMARY.adapter.signal.signal
    call_count = 0

    def fail_second_install(signum: int, handler: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RUN_SUMMARY.adapter.ArtifactIndexError(
                "injected partial signal install failure"
            )
        return real_signal(signum, handler)

    monkeypatch.setattr(
        RUN_SUMMARY.adapter.signal,
        "signal",
        fail_second_install,
    )

    with pytest.raises(
        RUN_SUMMARY.adapter.ArtifactIndexError,
        match="injected partial",
    ):
        RUN_SUMMARY.adapter.install_publication_signal_handlers()

    assert {
        signum: signal.getsignal(signum) for signum in watched
    } == original_handlers


def test_cleanup_signal_restores_handlers_and_retains_recovery_state(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    original_handlers = {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    }
    real_remove_owned = RUN_SUMMARY.adapter.remove_owned
    interrupted = False

    def interrupt_first_temp_cleanup(path: Path) -> None:
        nonlocal interrupted
        if not interrupted and path.name.endswith(".tmp"):
            interrupted = True
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
            raise AssertionError("signal handler unexpectedly returned")
        real_remove_owned(path)

    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "remove_owned",
        interrupt_first_temp_cleanup,
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="cleanup failed",
    ):
        RUN_SUMMARY.publish_context(context)

    assert interrupted
    assert all(path.is_file() for path in run_summary_fixture.summary_paths)
    RUN_SUMMARY.validate_published_run_summary(context)
    assert run_summary_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in run_summary_fixture.output_dir.iterdir()
    )
    assert {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    } == original_handlers


def test_signal_after_receipt_backup_rename_restores_prior_transaction(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = summary_snapshot(run_summary_fixture)
    original_handlers = {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    }
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY.os.replace
    interrupted = False

    def interrupt_after_receipt_backup(source: Any, destination: Any) -> None:
        nonlocal interrupted
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not interrupted
            and source_path == run_summary_fixture.summary_receipt_path
            and destination_path.name.endswith(".previous")
        ):
            real_replace(source, destination)
            interrupted = True
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
            raise AssertionError("signal handler unexpectedly returned")
        real_replace(source, destination)

    monkeypatch.setattr(
        RUN_SUMMARY.os,
        "replace",
        interrupt_after_receipt_backup,
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="interrupted by signal SIGTERM",
    ):
        RUN_SUMMARY.publish_context(context)

    assert interrupted
    assert summary_snapshot(run_summary_fixture) == before
    assert {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    } == original_handlers
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_corrupted_restored_receipt_is_quarantined_and_retains_recovery(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = summary_snapshot(run_summary_fixture)
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY.os.replace
    publication_failed = False
    receipt_corrupted = False

    def fail_then_corrupt_restored_receipt(
        source: Any,
        destination: Any,
    ) -> None:
        nonlocal publication_failed, receipt_corrupted
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not publication_failed
            and destination_path == run_summary_fixture.qc_summary_path
            and ".tmp" in source_path.name
        ):
            publication_failed = True
            raise OSError("injected replacement publication failure")
        if (
            publication_failed
            and not receipt_corrupted
            and destination_path == run_summary_fixture.summary_receipt_path
            and source_path.name.endswith(".previous")
        ):
            header = read_tsv_header(source_path)
            rows = read_tsv(source_path)
            rows[0]["git_commit"] = "f" * 40
            write_tsv(source_path, header, rows)
            receipt_corrupted = True
        real_replace(source, destination)

    monkeypatch.setattr(
        RUN_SUMMARY.os,
        "replace",
        fail_then_corrupt_restored_receipt,
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="rollback was incomplete",
    ):
        RUN_SUMMARY.publish_context(context)

    assert publication_failed
    assert receipt_corrupted
    for path in run_summary_fixture.summary_paths[:3]:
        assert path.read_bytes() == before[path.name]
    assert not run_summary_fixture.summary_receipt_path.exists()
    assert run_summary_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in run_summary_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".previous")
        and "run_summary_receipt.tsv" in path.name
        for path in run_summary_fixture.output_dir.iterdir()
    )


def test_first_publication_failure_removes_owned_outputs_and_lock(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY.os.replace
    failed = False

    def fail_qc_publication(source: Any, destination: Any) -> None:
        nonlocal failed
        if (
            not failed
            and Path(destination) == run_summary_fixture.qc_summary_path
            and ".tmp" in Path(source).name
        ):
            failed = True
            raise OSError("injected first run-summary publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(RUN_SUMMARY.os, "replace", fail_qc_publication)

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="injected first run-summary publication failure",
    ):
        RUN_SUMMARY.publish_context(context)

    assert failed
    assert_no_summary_outputs(run_summary_fixture)


def test_incomplete_replacement_rollback_retains_lock_and_recovery_paths(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY.os.replace
    publication_failed = False
    restoration_failed = False

    def fail_publication_and_restoration(
        source: Any,
        destination: Any,
    ) -> None:
        nonlocal publication_failed, restoration_failed
        source_path = Path(source)
        destination_path = Path(destination)
        if (
            not publication_failed
            and destination_path == run_summary_fixture.qc_summary_path
            and ".tmp" in source_path.name
        ):
            publication_failed = True
            raise OSError("injected replacement publication failure")
        if (
            publication_failed
            and not restoration_failed
            and destination_path == run_summary_fixture.summary_json_path
            and source_path.name.endswith(".previous")
        ):
            restoration_failed = True
            raise OSError("injected prior-summary restoration failure")
        real_replace(source, destination)

    monkeypatch.setattr(
        RUN_SUMMARY.os,
        "replace",
        fail_publication_and_restoration,
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="rollback was incomplete",
    ):
        RUN_SUMMARY.publish_context(context)

    assert publication_failed
    assert restoration_failed
    assert run_summary_fixture.lock_path.is_file()
    assert not run_summary_fixture.summary_json_path.exists()
    assert not run_summary_fixture.summary_receipt_path.exists()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in run_summary_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".previous")
        and "run_summary_receipt.tsv" in path.name
        for path in run_summary_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".previous")
        and "run_summary.json" in path.name
        for path in run_summary_fixture.output_dir.iterdir()
    )


def test_mid_rollback_directory_replacement_skips_replacement_path_cleanup(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY.os.replace
    real_remove_owned = RUN_SUMMARY.adapter.remove_owned
    publication_failed = False
    directory_replaced = False
    displaced = (
        run_summary_fixture.output_dir.parent
        / f"{run_summary_fixture.output_dir.name}.rollback-displaced"
    )

    def fail_qc_publication(source: Any, destination: Any) -> None:
        nonlocal publication_failed
        if (
            not publication_failed
            and Path(destination) == run_summary_fixture.qc_summary_path
            and ".tmp" in Path(source).name
        ):
            publication_failed = True
            raise OSError("injected replacement publication failure")
        real_replace(source, destination)

    def replace_directory_after_first_rollback_remove(path: Path) -> None:
        nonlocal directory_replaced
        real_remove_owned(path)
        if publication_failed and not directory_replaced:
            run_summary_fixture.output_dir.rename(displaced)
            run_summary_fixture.output_dir.mkdir()
            directory_replaced = True

    monkeypatch.setattr(RUN_SUMMARY.os, "replace", fail_qc_publication)
    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "remove_owned",
        replace_directory_after_first_rollback_remove,
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="identity changed",
    ):
        RUN_SUMMARY.publish_context(context)

    assert publication_failed
    assert directory_replaced
    assert list(run_summary_fixture.output_dir.iterdir()) == []
    assert (displaced / run_summary_fixture.lock_path.name).is_file()
    assert any(path.name.endswith(".tmp") for path in displaced.iterdir())


def test_post_commit_cleanup_failure_preserves_new_transaction_and_lock(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    context = context_for(run_summary_fixture)
    real_remove_owned = RUN_SUMMARY.adapter.remove_owned
    cleanup_failed = False

    def fail_one_backup_cleanup(path: Path) -> None:
        nonlocal cleanup_failed
        if (
            not cleanup_failed
            and path.name.endswith(".previous")
            and "run_summary.tsv" in path.name
        ):
            cleanup_failed = True
            raise OSError("injected run-summary backup cleanup failure")
        real_remove_owned(path)

    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "remove_owned",
        fail_one_backup_cleanup,
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="cleanup failed",
    ):
        RUN_SUMMARY.publish_context(context)

    assert cleanup_failed
    assert all(path.is_file() for path in run_summary_fixture.summary_paths)
    RUN_SUMMARY.validate_published_run_summary(context)
    receipt = read_tsv(run_summary_fixture.summary_receipt_path)[0]
    assert receipt["run_summary_attempt_id"] == context.attempt_id
    assert run_summary_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in run_summary_fixture.output_dir.iterdir()
    )


@pytest.mark.parametrize(
    ("field", "value", "token"),
    (
        ("git_commit", "f" * 40, "Git commit"),
        (
            "artifact_adapter_attempt_id",
            "tampered-adapter-attempt",
            "adapter attempt",
        ),
    ),
)
def test_tampered_prior_receipt_provenance_is_rejected(
    run_summary_fixture: Any,
    field: str,
    value: str,
    token: str,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    header = read_tsv_header(run_summary_fixture.summary_receipt_path)
    rows = read_tsv(run_summary_fixture.summary_receipt_path)
    rows[0][field] = value
    write_tsv(run_summary_fixture.summary_receipt_path, header, rows)

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match=token,
    ):
        context_for(run_summary_fixture)


def test_artifact_receipt_mutation_after_prepare_aborts_before_publication(
    run_summary_fixture: Any,
) -> None:
    context = context_for(run_summary_fixture)
    run_summary_fixture.artifact_receipt.write_bytes(
        run_summary_fixture.artifact_receipt.read_bytes() + b"\n"
    )

    with pytest.raises(Exception, match="[Cc]hanged|[Mm]utation"):
        RUN_SUMMARY.publish_context(context)

    assert_no_summary_outputs(run_summary_fixture)


def test_prepared_snapshot_rejects_transaction_mutated_during_validation(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_validate = RUN_SUMMARY.adapter.validate_published_transaction
    mutated = False

    def validate_then_mutate(**kwargs: Any) -> None:
        nonlocal mutated
        real_validate(**kwargs)
        if not mutated:
            run_summary_fixture.adapter_fixture.artifacts_path.write_bytes(
                run_summary_fixture.adapter_fixture.artifacts_path.read_bytes()
                + b"\n"
            )
            mutated = True

    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "validate_published_transaction",
        validate_then_mutate,
    )
    arguments = RUN_SUMMARY.parse_arguments(
        run_summary_fixture.command_args(execute=True)
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="immutable snapshot",
    ):
        RUN_SUMMARY.prepare_context(arguments)

    assert mutated
    assert_no_summary_outputs(run_summary_fixture)


def test_prepare_recheck_rejects_identical_byte_record_replacement(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_build_document = RUN_SUMMARY._build_document
    replaced = False

    def build_then_replace_record(**kwargs: Any) -> Any:
        nonlocal replaced
        result = real_build_document(**kwargs)
        if not replaced:
            record_path = next(
                run_summary_fixture.adapter_fixture.records_dir.glob("*.json")
            )
            replacement = record_path.with_name(
                f".{record_path.name}.identical-replacement"
            )
            replacement.write_bytes(record_path.read_bytes())
            replacement.replace(record_path)
            replaced = True
        return result

    monkeypatch.setattr(
        RUN_SUMMARY,
        "_build_document",
        build_then_replace_record,
    )
    arguments = RUN_SUMMARY.parse_arguments(
        run_summary_fixture.command_args(execute=True)
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="immutable snapshot",
    ):
        RUN_SUMMARY.prepare_context(arguments)

    assert replaced
    assert_no_summary_outputs(run_summary_fixture)


def test_output_directory_inode_replacement_is_rejected(
    run_summary_fixture: Any,
) -> None:
    context = context_for(run_summary_fixture)
    displaced = (
        run_summary_fixture.output_dir.parent
        / f"{run_summary_fixture.output_dir.name}.displaced"
    )
    run_summary_fixture.output_dir.rename(displaced)
    run_summary_fixture.output_dir.mkdir()

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="identity changed",
    ):
        RUN_SUMMARY.publish_context(context)

    assert list(run_summary_fixture.output_dir.iterdir()) == []


def test_receipt_is_the_last_published_summary_output(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY.os.replace
    final_paths = set(run_summary_fixture.summary_paths)
    publication_order: list[Path] = []

    def track_publication(source: Any, destination: Any) -> None:
        destination_path = Path(destination)
        if destination_path in final_paths and ".tmp" in Path(source).name:
            publication_order.append(destination_path)
        real_replace(source, destination)

    monkeypatch.setattr(RUN_SUMMARY.os, "replace", track_publication)

    RUN_SUMMARY.publish_context(context)

    assert publication_order == list(run_summary_fixture.summary_paths)
    assert publication_order[-1] == run_summary_fixture.summary_receipt_path
    RUN_SUMMARY.validate_published_run_summary(context)
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_reserved_science_state_is_rejected_before_publication(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "reserved",
        science_status="evidence_incomplete",
    )
    header = read_tsv_header(fixture.science_review_summary)
    rows = read_tsv(fixture.science_review_summary)
    rows[0]["overall_science_status"] = "biological_interpretation_ready"
    write_tsv(fixture.science_review_summary, header, rows)

    result = run_cli(fixture, execute=True)

    assert result.returncode != 0
    assert "reserved" in result.stderr.lower()
    assert_no_summary_outputs(fixture)


def test_alternate_indexed_science_path_spelling_is_preserved(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "relative-science",
        science_status="evidence_incomplete",
    )
    summary_row = read_tsv(fixture.science_review_summary)[0]
    context, _tables = RUN_SUMMARY.science._rebuild_step09c(
        summary_path=fixture.science_review_summary,
        summary_row=summary_row,
    )
    index_rows = read_tsv(fixture.adapter_fixture.artifacts_path)
    artifacts = [
        read_json(Path(row["record_path"]))
        for row in index_rows
    ]
    target = next(
        artifact
        for artifact in artifacts
        if artifact["adapter"] == "step08_sites_v1"
    )
    absolute_source = CONTRACTS.resolve_contract_path(target["source"]["path"])
    source_text = str(absolute_source)
    if not source_text.startswith("/private/var/"):
        pytest.skip("No stable alternate /var spelling is available")
    alternate_source = source_text.removeprefix("/private")
    assert Path(alternate_source).resolve() == absolute_source
    target["source"]["path"] = alternate_source
    target["expectation"]["source_path"] = alternate_source
    summary_artifact = next(
        artifact
        for artifact in artifacts
        if artifact["adapter"] == "step09c_review_summary_v1"
    )
    summary_text = str(fixture.science_review_summary)
    assert summary_text.startswith("/private/var/")
    alternate_summary = summary_text.removeprefix("/private")
    assert Path(alternate_summary).resolve() == fixture.science_review_summary
    summary_artifact["source"]["path"] = alternate_summary
    summary_artifact["expectation"]["source_path"] = alternate_summary
    run_contract = read_json(fixture.adapter_fixture.run_contract)

    normalized = RUN_SUMMARY.science._normalize_input_artifacts(
        context=context,
        artifacts=artifacts,
        review_id=summary_row["review_id"],
        run_contract=run_contract,
    )
    science_record = RUN_SUMMARY.science.normalize_scientific_review(
        summary_path=fixture.science_review_summary,
        artifacts=artifacts,
        run_id=fixture.run_id,
        run_contract=run_contract,
        generated_at="2020-01-01T00:00:00Z",
        git_commit="a" * 40,
    )

    step08_sites = next(
        record for record in normalized if record["role"] == "step08_sites"
    )
    assert step08_sites["path"] == alternate_source
    assert science_record["review_summary"]["path"] == alternate_summary


def test_alternate_science_summary_spelling_publishes_consistent_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "alternate-summary-publish",
        science_status="evidence_incomplete",
    )
    summary_text = str(fixture.science_review_summary)
    if not summary_text.startswith("/private/var/"):
        pytest.skip("No stable alternate /var spelling is available")
    alternate_summary = summary_text.removeprefix("/private")
    real_normalize = RUN_SUMMARY.science.normalize_scientific_review

    def normalize_with_indexed_spelling(**kwargs: Any) -> dict[str, Any]:
        record = copy.deepcopy(real_normalize(**kwargs))
        record["review_summary"]["path"] = alternate_summary
        return record

    monkeypatch.setattr(
        RUN_SUMMARY.science,
        "normalize_scientific_review",
        normalize_with_indexed_spelling,
    )

    context = context_for(fixture)
    assert context.document["scientific_review"]["source"]["path"] == (
        alternate_summary
    )
    assert context.receipt_row["science_review_summary_path"] == (
        alternate_summary
    )
    RUN_SUMMARY.publish_context(context)

    RUN_SUMMARY.validate_published_run_summary(context)
    receipt = read_tsv(fixture.summary_receipt_path)[0]
    document = read_json(fixture.summary_json_path)
    assert receipt["science_review_summary_path"] == alternate_summary
    assert (
        document["scientific_review"]["source"]["path"]
        == alternate_summary
    )
    assert_no_summary_residue_after_success(fixture)


def test_pending_science_decision_with_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "pending-decision",
        science_status="evidence_incomplete",
    )
    summary_row = read_tsv(fixture.science_review_summary)[0]
    context, _tables = RUN_SUMMARY.science._rebuild_step09c(
        summary_path=fixture.science_review_summary,
        summary_row=summary_row,
    )
    pending = context.category_rows["decisions"][0]
    pending["decision_status"] = "pending"
    pending["supporting_evidence_ids"] = "evidence.synthetic"

    with pytest.raises(
        RUN_SUMMARY.science.RunSummaryScienceError,
        match="Pending decision",
    ):
        RUN_SUMMARY.science._normalize_decisions(context)


def test_pending_science_decision_preserves_rationale_owner_and_policy(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "pending-decision-details",
        science_status="evidence_incomplete",
    )
    summary_row = read_tsv(fixture.science_review_summary)[0]
    context, _tables = RUN_SUMMARY.science._rebuild_step09c(
        summary_path=fixture.science_review_summary,
        summary_row=summary_row,
    )
    pending = context.category_rows["decisions"][0]
    pending.update(
        {
            "decision_status": "pending",
            "decision_value": "NA",
            "decision_date": "NA",
            "supporting_evidence_ids": "NA",
        }
    )

    normalized = RUN_SUMMARY.science._normalize_decisions(context)[
        pending["decision_dimension"]
    ]

    assert normalized["status"] == "pending"
    assert normalized["detail"] == pending["rationale"]
    assert normalized["reviewer"] == pending["decision_owner"]
    assert normalized["decision_id"] == pending["decision_id"]
    assert normalized["source_evidence_id"] == pending["evidence_id"]
    assert normalized["evidence_status"] == pending["evidence_status"]
    assert normalized["policy_version"] == pending["policy_version"]
    assert normalized["rerun_required"] is False


def test_generated_limitation_id_is_collision_safe(tmp_path: Path) -> None:
    fixture = FIXTURE.build_missing_fixture(tmp_path / "collision")
    record = read_json(
        fixture.adapter_fixture.records_dir
        / "sample.SYNTH_A.canonical_bai.json"
    )
    existing = {
        "limitation_id": "required_artifacts_not_complete",
        "status": "open",
        "description": "Synthetic user-authored limitation.",
        "impact": "Synthetic impact.",
        "evidence_ids": [],
    }

    limitations = RUN_SUMMARY._build_limitations(
        artifacts=[record],
        scientific_review={
            "record": {"limitations": [existing]},
        },
    )

    assert [row["limitation_id"] for row in limitations] == [
        "required_artifacts_not_complete",
        "required_artifacts_not_complete.generated1",
    ]


def test_attempt_aggregation_preserves_independent_chains_and_rejects_conflicts(
) -> None:
    first = {
        "attempt_id": "attempt-a1",
        "state": "succeeded",
        "started_at": "2000-01-01T00:00:00Z",
        "finished_at": "2000-01-01T00:00:01Z",
        "exit_code": 0,
        "supersedes_attempt_id": None,
        "evidence": [],
        "warnings": [],
        "errors": [],
    }
    retry = {
        **first,
        "attempt_id": "attempt-a2",
        "started_at": "2000-01-01T00:00:02Z",
        "finished_at": "2000-01-01T00:00:03Z",
        "supersedes_attempt_id": "attempt-a1",
    }
    independent = {
        **first,
        "attempt_id": "attempt-b1",
        "started_at": "2000-01-01T00:00:04Z",
        "finished_at": "2000-01-01T00:00:05Z",
    }
    artifacts = [
        {"attempts": [first, retry]},
        {"attempts": [independent, copy.deepcopy(retry)]},
    ]

    attempts, superseded = RUN_SUMMARY._build_attempts(artifacts)

    assert [attempt["attempt_id"] for attempt in attempts] == [
        "attempt-a1",
        "attempt-a2",
        "attempt-b1",
    ]
    assert superseded == ["attempt-a1"]

    conflicting = copy.deepcopy(artifacts)
    conflicting[1]["attempts"][1]["finished_at"] = (
        "2000-01-01T00:00:06Z"
    )
    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="conflicting definitions",
    ):
        RUN_SUMMARY._build_attempts(conflicting)
