"""Focused integration and transaction tests for artifact-run-summary."""

from __future__ import annotations

import argparse
import copy
import csv
import dataclasses
import hashlib
import importlib
import io
import json
import os
import signal
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from emrys.contracts.artifacts import api as CONTRACTS
from emrys.libraries import source_authority as SOURCE_AUTHORITY
from emrys.reporting import transaction_validation as REPORTING_VALIDATION
from emrys.reporting._artifact_index import api as ARTIFACT_INDEX_API
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_EPOCH = "1700000000"

RUN_SUMMARY = importlib.import_module("emrys.reporting._run_summary.builder")
RUN_SUMMARY_DOCUMENT = importlib.import_module("emrys.reporting._run_summary.document")
RUN_SUMMARY_MODELS = importlib.import_module("emrys.reporting._run_summary.models")
RUN_SUMMARY_PROJECTION = importlib.import_module(
    "emrys.reporting._run_summary.projection"
)
RUN_SUMMARY_PUBLICATION = importlib.import_module(
    "emrys.reporting._run_summary.publication"
)
SOURCE_CHECKOUT = SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT)


def build_deps(**overrides: Any) -> Any:
    return dataclasses.replace(
        RUN_SUMMARY.DEFAULT_RUN_SUMMARY_BUILD_DEPS,
        **overrides,
    )


@pytest.fixture
def run_summary_fixture(tmp_path: Path) -> Any:
    return FIXTURE.build_fixture(tmp_path / "fixture")


def run_summary_arguments(
    fixture: Any,
    *,
    execute: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        source_checkout=REPO_ROOT,
        artifact_source_root=fixture.root,
        run_id=fixture.run_id,
        artifact_receipt=fixture.artifact_receipt,
        output_root=fixture.output_root,
        execute=execute,
    )


@dataclasses.dataclass(frozen=True)
class DirectTransactionResult:
    """Prepared context or typed producer error from a direct transaction."""

    context: Any | None = None
    error: Exception | None = None

    @property
    def returncode(self) -> int:
        return int(self.error is not None)

    @property
    def stderr(self) -> str:
        return "" if self.error is None else str(self.error)


def run_builder(
    fixture: Any,
    *,
    execute: bool = False,
    arguments: argparse.Namespace | None = None,
) -> DirectTransactionResult:
    prepared_arguments = arguments or run_summary_arguments(
        fixture,
        execute=execute,
    )
    previous_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    try:
        try:
            context = RUN_SUMMARY.prepare_context(
                prepared_arguments,
                source_checkout=SOURCE_CHECKOUT,
                artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
                    root=prepared_arguments.artifact_source_root
                ),
            )
            if prepared_arguments.execute:
                RUN_SUMMARY_PUBLICATION.publish_context(context)
            return DirectTransactionResult(context=context)
        except (
            RUN_SUMMARY_MODELS.RunSummaryError,
            ARTIFACT_INDEX_API.ArtifactIndexError,
            SOURCE_AUTHORITY.ArtifactSourceRootError,
            SOURCE_AUTHORITY.SourceCheckoutError,
            CONTRACTS.ContractValidationError,
            OSError,
            ValueError,
        ) as exc:
            return DirectTransactionResult(error=exc)
    finally:
        if previous_epoch is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous_epoch


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
        path.name: path.read_bytes() for path in fixture.summary_paths if path.is_file()
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


def context_for(fixture: Any, *, deps: Any | None = None) -> Any:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    try:
        arguments = run_summary_arguments(fixture, execute=True)
        return RUN_SUMMARY.prepare_context(
            arguments,
            source_checkout=SOURCE_CHECKOUT,
            artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(root=fixture.root),
            **({} if deps is None else {"deps": deps}),
        )
    finally:
        if previous is None:
            os.environ.pop("SOURCE_DATE_EPOCH", None)
        else:
            os.environ["SOURCE_DATE_EPOCH"] = previous


def _source_root_spy(
    real_call: Any,
    expected_root: Path,
    calls: Counter[str],
    label: str,
) -> Any:
    def rooted_call(
        *args: Any,
        source_root: Path,
        **kwargs: Any,
    ) -> Any:
        assert source_root == expected_root
        calls[label] += 1
        return real_call(*args, source_root=source_root, **kwargs)

    return rooted_call


def test_prepare_context_keeps_checkout_and_artifact_roots_distinct(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The explicit roots reach their distinct computational authorities."""
    fixture = FIXTURE.build_fixture(tmp_path / "authority")
    source_checkout = SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT)
    artifact_root = SOURCE_AUTHORITY.ArtifactSourceRoot(root=fixture.root)
    root_calls: Counter[str] = Counter()
    real_get_git_commit = ARTIFACT_INDEX_API.get_git_commit

    def matching_checkout_head_commit(
        *,
        source_checkout: Any,
        package_root: Path,
    ) -> str:
        assert source_checkout.root == REPO_ROOT
        assert package_root == Path(RUN_SUMMARY.__file__).resolve().parents[2]
        root_calls["git"] += 1
        return real_get_git_commit(
            source_root=REPO_ROOT,
            sanitize_git_routing=True,
        )

    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "foreign.git"))
    for owner, attribute, label in (
        (CONTRACTS, "validate_inventory", "inventory"),
        (CONTRACTS, "validate_run_summary_semantics", "document_semantics"),
        (CONTRACTS, "reconcile_document_inventory", "document_inventory"),
    ):
        monkeypatch.setattr(
            owner,
            attribute,
            _source_root_spy(
                getattr(owner, attribute),
                artifact_root.root,
                root_calls,
                label,
            ),
        )
    arguments = run_summary_arguments(fixture)

    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=source_checkout,
        artifact_source_root=artifact_root,
        deps=build_deps(
            matching_checkout_head_commit=matching_checkout_head_commit,
        ),
    )

    expected_single_calls = 1
    assert context.source_checkout == source_checkout
    assert context.artifact_source_root == artifact_root
    assert root_calls["git"] == expected_single_calls
    assert root_calls["inventory"] == expected_single_calls
    assert root_calls["document_semantics"] == expected_single_calls
    assert root_calls["document_inventory"] == expected_single_calls


def test_prepare_context_uses_local_build_for_unattributable_package(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    arguments = run_summary_arguments(run_summary_fixture)
    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=SOURCE_CHECKOUT,
        artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
            root=run_summary_fixture.root
        ),
        deps=build_deps(matching_checkout_head_commit=lambda **_kwargs: None),
    )

    assert context.receipt_row["git_commit"] == "local_build"
    assert context.document["provenance"]["git_commit"] == "local_build"


def test_explicit_artifact_root_reaches_post_publish_rechecks(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    root_calls: Counter[str] = Counter()
    for owner, attribute, label in (
        (CONTRACTS, "validate_run_summary_semantics", "semantics"),
        (RUN_SUMMARY_PUBLICATION, "_validate_document", "document"),
        (RUN_SUMMARY_PUBLICATION, "_validate_existing_summary", "published"),
    ):
        monkeypatch.setattr(
            owner,
            attribute,
            _source_root_spy(
                getattr(owner, attribute), run_summary_fixture.root, root_calls, label
            ),
        )

    RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert root_calls == {"semantics": 2, "document": 1, "published": 1}
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_existing_summary_preparation_retains_predecessor_authority(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = run_builder(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = summary_snapshot(run_summary_fixture)
    calls: Counter[str] = Counter()
    monkeypatch.setattr(
        RUN_SUMMARY,
        "_validate_existing_summary",
        _source_root_spy(
            RUN_SUMMARY._validate_existing_summary,
            run_summary_fixture.root,
            calls,
            "predecessor",
        ),
    )

    context = context_for(run_summary_fixture)

    assert calls == {"predecessor": 1}
    assert (
        context.previous_receipt
        == read_tsv(run_summary_fixture.summary_receipt_path)[0]
    )
    assert summary_snapshot(run_summary_fixture) == before
    assert_no_summary_residue_after_success(run_summary_fixture)


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


def test_dry_run_validates_without_summary_writes(
    run_summary_fixture: Any,
) -> None:
    result = run_builder(run_summary_fixture)

    assert result.returncode == 0, result.stderr
    assert result.context is not None
    assert result.context.run_id == run_summary_fixture.run_id
    assert_no_summary_outputs(run_summary_fixture)


def test_live_run_summary_header_owner_controls_serialized_bytes(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = RUN_SUMMARY_MODELS.RUN_SUMMARY_HEADER
    mutated = (original[1], original[0], *original[2:])
    monkeypatch.setattr(RUN_SUMMARY_MODELS, "RUN_SUMMARY_HEADER", mutated)

    context = context_for(run_summary_fixture)

    assert context.summary_tsv_bytes.splitlines()[0] == ("\t".join(mutated).encode())
    assert context.summary_tsv_bytes != ARTIFACT_INDEX_API.tsv_bytes(
        original,
        list(
            csv.DictReader(
                io.StringIO(context.summary_tsv_bytes.decode()), delimiter="\t"
            )
        ),
    )


def test_execute_publishes_exact_canonical_schema_valid_transaction(
    run_summary_fixture: Any,
) -> None:
    result = run_builder(run_summary_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    assert all(path.is_file() for path in run_summary_fixture.summary_paths)
    document = validate_summary_document(run_summary_fixture)
    assert run_summary_fixture.summary_json_path.read_bytes() == (
        canonical_json_bytes(document)
    )
    assert read_tsv_header(run_summary_fixture.summary_tsv_path) == tuple(
        RUN_SUMMARY_MODELS.RUN_SUMMARY_HEADER
    )
    assert read_tsv_header(run_summary_fixture.qc_summary_path) == tuple(
        RUN_SUMMARY_MODELS.QC_SUMMARY_HEADER
    )
    assert read_tsv_header(run_summary_fixture.summary_receipt_path) == tuple(
        RUN_SUMMARY_MODELS.RUN_SUMMARY_RECEIPT_HEADER
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
    assert document["interpretation_boundary"] == (
        "computational_candidates_only_biological_validation_outside_emrys"
    )
    assert "scientific_review" not in document
    assert "science_status" not in document
    assert "approved_report_tables" not in document
    assert_no_summary_residue_after_success(run_summary_fixture)


def assert_no_summary_residue_after_success(fixture: Any) -> None:
    assert not fixture.lock_path.exists()
    owned_names = {path.name for path in fixture.summary_paths}
    assert not any(
        path.name not in owned_names
        and ("run-summary" in path.name or "run_summary" in path.name)
        and path.name.startswith(".")
        for path in fixture.output_dir.iterdir()
    )


def test_existing_summary_readmission_keeps_json_and_views_byte_identical(
    run_summary_fixture: Any,
) -> None:
    first = run_builder(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = summary_snapshot(run_summary_fixture)

    second = run_builder(run_summary_fixture)

    assert second.returncode == 0, second.stderr
    assert second.context is not None
    assert (
        second.context.summary_json_bytes,
        second.context.summary_tsv_bytes,
        second.context.qc_summary_bytes,
    ) == tuple(before[path.name] for path in run_summary_fixture.summary_paths[:3])
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError, match="requires absent outputs"
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(second.context)
    assert summary_snapshot(run_summary_fixture) == before
    validate_summary_document(run_summary_fixture)
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_unrelated_files_are_ignored_and_preserved(
    run_summary_fixture: Any,
) -> None:
    unrelated = run_summary_fixture.output_dir / "unrelated.run_summary.json"
    unrelated_payload = b'{"unrelated":true}\n'
    unrelated.write_bytes(unrelated_payload)
    decoy = run_summary_fixture.output_dir / "decoy.tsv"
    decoy_payload = b"unrelated\nvalue\n"
    decoy.write_bytes(decoy_payload)

    result = run_builder(run_summary_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    document = validate_summary_document(run_summary_fixture)
    assert unrelated.read_bytes() == unrelated_payload
    assert decoy.read_bytes() == decoy_payload
    assert document["interpretation_boundary"].endswith(
        "biological_validation_outside_emrys"
    )


def test_run_id_mismatch_and_tampered_artifact_receipt_fail_closed(
    tmp_path: Path,
) -> None:
    wrong_run = FIXTURE.build_fixture(tmp_path / "wrong_run")
    arguments = run_summary_arguments(wrong_run)
    arguments.run_id = "different_run"
    mismatch = run_builder(wrong_run, arguments=arguments)
    assert mismatch.returncode != 0
    assert_no_summary_outputs(wrong_run)

    tampered = FIXTURE.build_fixture(tmp_path / "tampered")
    header = read_tsv_header(tampered.artifact_receipt)
    rows = read_tsv(tampered.artifact_receipt)
    rows[0]["artifacts_index_sha256"] = "f" * 64
    write_tsv(tampered.artifact_receipt, header, rows)
    result = run_builder(tampered)
    assert result.returncode != 0
    assert_no_summary_outputs(tampered)


def test_qc_view_keeps_all_repeated_metrics_but_json_ids_are_unique(
    run_summary_fixture: Any,
) -> None:
    result = run_builder(run_summary_fixture, execute=True)
    assert result.returncode == 0, result.stderr
    document = validate_summary_document(run_summary_fixture)
    index_rows = read_tsv(run_summary_fixture.adapter_fixture.artifacts_path)
    artifact_metrics = []
    for index_row in index_rows:
        artifact = read_json(Path(index_row["record_path"]))
        artifact_metrics.extend(artifact["metrics"])

    qc_rows = read_tsv(run_summary_fixture.qc_summary_path)
    json_metric_ids = [metric["metric_id"] for metric in document["qc_metrics"]]
    source_counts = Counter(metric["metric_id"] for metric in artifact_metrics)

    assert len(qc_rows) == len(artifact_metrics)
    assert len(json_metric_ids) == len(set(json_metric_ids))
    assert source_counts["source_row_count"] > 1
    assert (
        sum(row["metric_id"] == "source_row_count" for row in qc_rows)
        == source_counts["source_row_count"]
    )
    assert all(
        row.get("source_artifact_id") or row.get("artifact_id") for row in qc_rows
    )


def test_qc_projection_preserves_domain_infinity_string() -> None:
    metric = {
        "metric_id": "mapping_speed__million_of_reads_per_hour",
        "name": "Mapping Speed  Million Of Reads Per Hour",
        "value": "Inf",
        "unit": None,
        "status": "not_assessed",
        "source_artifact_id": "sample.SYNTH_A.star_log_final",
    }
    artifact = {
        "artifact_id": "sample.SYNTH_A.star_log_final",
        "scope": {
            "step_id": "01",
            "scope_type": "sample",
            "scope_id": "SYNTH_A",
        },
        "metrics": [metric],
    }

    promoted, duplicate_ids = RUN_SUMMARY_PROJECTION._build_qc_metrics([artifact])
    rows = RUN_SUMMARY_PROJECTION._build_qc_rows(
        {"run_id": "synthetic_run", "artifacts": [artifact]}
    )

    assert promoted == [metric]
    assert duplicate_ids == set()
    assert rows[0]["value"] == '"Inf"'
    assert rows[0]["value_type"] == "string"


def test_projection_handles_no_duplicate_metrics_and_null_metric_values() -> None:
    assert RUN_SUMMARY_PROJECTION._issue_for_duplicate_metrics(set(), []) is None
    assert RUN_SUMMARY_PROJECTION._metric_value_type(None) == "null"


def test_complete_summary_preserves_required_missing_artifact_state(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_missing_fixture(tmp_path / "missing")

    result = run_builder(fixture, execute=True)

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
    assert document["interpretation_boundary"].endswith(
        "biological_validation_outside_emrys"
    )


def test_partial_prior_summary_and_foreign_lock_are_preserved(
    tmp_path: Path,
) -> None:
    partial = FIXTURE.build_fixture(tmp_path / "partial")
    partial_payload = b'{"partial":true}\n'
    partial.summary_json_path.write_bytes(partial_payload)

    partial_result = run_builder(partial, execute=True)

    assert partial_result.returncode != 0
    assert partial.summary_json_path.read_bytes() == partial_payload
    assert not any(path.exists() for path in partial.summary_paths[1:])

    locked = FIXTURE.build_fixture(tmp_path / "locked")
    lock_payload = b"foreign run-summary lock\n"
    locked.lock_path.write_bytes(lock_payload)

    locked_result = run_builder(locked, execute=True)

    assert locked_result.returncode != 0
    assert locked.lock_path.read_bytes() == lock_payload
    assert not any(path.exists() for path in locked.summary_paths)


@pytest.mark.parametrize("final_index", range(4))
@pytest.mark.parametrize("kind", ("file", "dangling_symlink", "directory"))
def test_existing_final_paths_are_rejected_without_mutation(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    final_index: int,
    kind: str,
) -> None:
    context = context_for(run_summary_fixture)
    final = run_summary_fixture.summary_paths[final_index]
    target = final.with_name("absent-target")
    if kind == "file":
        final.write_bytes(b"foreign output\n")
    elif kind == "dangling_symlink":
        final.symlink_to(target)
    else:
        final.mkdir()
        (final / "foreign").write_bytes(b"foreign output\n")
    original = final.lstat()

    def unexpected_write(*args: Any, **kwargs: Any) -> None:
        pytest.fail("present output was not refused before staging")

    monkeypatch.setattr(ARTIFACT_INDEX_API, "write_bytes_exclusive", unexpected_write)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError, match="requires absent outputs"
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert final.lstat() == original
    assert not target.exists()
    if kind == "file":
        assert final.read_bytes() == b"foreign output\n"
    elif kind == "directory":
        assert (final / "foreign").read_bytes() == b"foreign output\n"
    else:
        assert final.readlink() == target
    assert not run_summary_fixture.lock_path.exists()
    assert all(
        not os.path.lexists(path)
        for path in run_summary_fixture.summary_paths
        if path != final
    )


def test_publication_installs_and_restores_signal_handlers(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    watched = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    original = {signum: signal.getsignal(signum) for signum in watched}
    real_install = ARTIFACT_INDEX_API.install_publication_signal_handlers
    real_restore = ARTIFACT_INDEX_API.restore_signal_handlers
    events: list[tuple[str, Any]] = []

    def track_install() -> dict[int, Any]:
        assert run_summary_fixture.lock_path.is_file()
        handlers = real_install()
        events.append(("install", handlers))
        return handlers

    def track_restore(handlers: Mapping[int, Any]) -> None:
        events.append(("restore", dict(handlers)))
        real_restore(handlers)

    context = context_for(run_summary_fixture)
    monkeypatch.setattr(
        ARTIFACT_INDEX_API, "install_publication_signal_handlers", track_install
    )
    monkeypatch.setattr(ARTIFACT_INDEX_API, "restore_signal_handlers", track_restore)
    RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert [event[0] for event in events] == ["install", "restore"]
    assert events[0][1] == original
    assert events[1][1] == original
    assert {signum: signal.getsignal(signum) for signum in watched} == original
    RUN_SUMMARY_PUBLICATION.validate_published_run_summary(context)
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_signal_handler_install_failure_releases_owned_lock(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)

    def fail_install() -> dict[int, Any]:
        raise ValueError("injected signal-handler installation failure")

    monkeypatch.setattr(
        ARTIFACT_INDEX_API, "install_publication_signal_handlers", fail_install
    )
    with pytest.raises(RUN_SUMMARY_MODELS.RunSummaryError, match="Could not install"):
        RUN_SUMMARY_PUBLICATION.publish_context(context)
    assert_no_summary_outputs(run_summary_fixture)


def test_partial_signal_handler_install_restores_original_handlers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    watched = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    original_handlers = {signum: signal.getsignal(signum) for signum in watched}
    real_signal = signal.signal
    call_count = 0

    def fail_second_install(signum: int, handler: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise ARTIFACT_INDEX_API.ArtifactIndexError(
                "injected partial signal install failure"
            )
        return real_signal(signum, handler)

    monkeypatch.setattr(signal, "signal", fail_second_install)

    with pytest.raises(
        ARTIFACT_INDEX_API.ArtifactIndexError,
        match="injected partial",
    ):
        ARTIFACT_INDEX_API.install_publication_signal_handlers()

    assert {signum: signal.getsignal(signum) for signum in watched} == original_handlers


def test_cleanup_signal_restores_handlers_and_retains_recovery_state(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    original_handlers = {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    }
    real_remove_owned = ARTIFACT_INDEX_API.remove_owned
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
        ARTIFACT_INDEX_API, "remove_owned", interrupt_first_temp_cleanup
    )
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="cleanup failed",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert interrupted
    assert all(path.is_file() for path in run_summary_fixture.summary_paths)
    RUN_SUMMARY_PUBLICATION.validate_published_run_summary(context)
    assert run_summary_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in run_summary_fixture.output_dir.iterdir()
    )
    assert {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    } == original_handlers


@pytest.mark.parametrize("final_index", range(4))
def test_signal_after_final_link_rolls_back_owned_outputs(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    final_index: int,
) -> None:
    context = context_for(run_summary_fixture)
    original_handlers = {
        signum: signal.getsignal(signum)
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    }
    real_link = os.link
    interrupted = False

    def interrupt_after_link(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal interrupted
        real_link(source, destination, **kwargs)
        if Path(destination) == run_summary_fixture.summary_paths[final_index]:
            interrupted = True
            handler = signal.getsignal(signal.SIGTERM)
            assert callable(handler)
            handler(signal.SIGTERM, None)
            raise AssertionError("signal handler unexpectedly returned")

    monkeypatch.setattr(os, "link", interrupt_after_link)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError, match="interrupted by signal SIGTERM"
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert interrupted
    assert {
        signum: signal.getsignal(signum) for signum in original_handlers
    } == original_handlers
    assert_no_summary_outputs(run_summary_fixture)
    assert_no_summary_residue_after_success(run_summary_fixture)


@pytest.mark.parametrize("final_index", range(4))
@pytest.mark.parametrize("link_raises", (False, True))
def test_same_byte_foreign_final_is_preserved_during_rollback(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    final_index: int,
    link_raises: bool,
) -> None:
    context = context_for(run_summary_fixture)
    final = run_summary_fixture.summary_paths[final_index]
    real_link = os.link
    foreign_identity: tuple[int, int] | None = None
    expected_bytes = b""

    def replace_after_link(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal foreign_identity, expected_bytes
        real_link(source, destination, **kwargs)
        if Path(destination) == final:
            expected_bytes = final.read_bytes()
            foreign = final.with_name("foreign-replacement")
            foreign.write_bytes(expected_bytes)
            foreign.replace(final)
            metadata = final.lstat()
            foreign_identity = (metadata.st_dev, metadata.st_ino)
            if link_raises:
                raise OSError("injected post-link replacement")

    monkeypatch.setattr(os, "link", replace_after_link)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError, match="rollback was incomplete"
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert foreign_identity is not None
    assert (final.lstat().st_dev, final.lstat().st_ino) == foreign_identity
    assert final.read_bytes() == expected_bytes
    assert all(
        not os.path.lexists(path)
        for path in run_summary_fixture.summary_paths
        if path != final
    )
    assert run_summary_fixture.lock_path.is_file()
    assert len(list(run_summary_fixture.output_dir.glob("*.tmp"))) == 4
    assert list(run_summary_fixture.output_dir.glob("*.RECOVERY.txt"))


@pytest.mark.parametrize("final_index", range(4))
def test_first_publication_link_failure_removes_owned_outputs_and_lock(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    final_index: int,
) -> None:
    context = context_for(run_summary_fixture)
    real_link = os.link
    failed = False

    def fail_publication(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal failed
        if Path(destination) == run_summary_fixture.summary_paths[final_index]:
            failed = True
            raise OSError("injected first run-summary publication failure")
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(os, "link", fail_publication)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="injected first run-summary publication failure",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert failed
    assert_no_summary_outputs(run_summary_fixture)
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_incomplete_owned_rollback_retains_lock_and_anchors(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    real_link = os.link
    real_unlink = Path.unlink
    publication_failed = False
    rollback_failed = False

    def fail_publication(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal publication_failed
        if Path(destination) == run_summary_fixture.qc_summary_path:
            publication_failed = True
            raise OSError("injected publication failure")
        real_link(source, destination, **kwargs)

    def fail_rollback(path: Path, *args: Any, **kwargs: Any) -> None:
        nonlocal rollback_failed
        if publication_failed and path == run_summary_fixture.summary_json_path:
            rollback_failed = True
            raise OSError("injected owned-output removal failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "link", fail_publication)
    monkeypatch.setattr(Path, "unlink", fail_rollback)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError, match="rollback was incomplete"
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert publication_failed and rollback_failed
    assert (
        run_summary_fixture.summary_json_path.read_bytes() == context.summary_json_bytes
    )
    assert all(not path.exists() for path in run_summary_fixture.summary_paths[1:])
    assert run_summary_fixture.lock_path.is_file()
    assert len(list(run_summary_fixture.output_dir.glob("*.tmp"))) == 4
    assert list(run_summary_fixture.output_dir.glob("*.RECOVERY.txt"))


@pytest.mark.parametrize("unlink_raises", (False, True))
def test_mid_rollback_directory_replacement_skips_replacement_path_cleanup(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    unlink_raises: bool,
) -> None:
    context = context_for(run_summary_fixture)
    real_link = os.link
    real_unlink = Path.unlink
    publication_failed = False
    directory_replaced = False
    displaced = run_summary_fixture.output_dir.with_name("rollback-displaced")

    def fail_publication(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal publication_failed
        if Path(destination) == run_summary_fixture.qc_summary_path:
            publication_failed = True
            raise OSError("injected publication failure")
        real_link(source, destination, **kwargs)

    def replace_after_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
        nonlocal directory_replaced
        real_unlink(path, *args, **kwargs)
        if publication_failed and not directory_replaced:
            run_summary_fixture.output_dir.rename(displaced)
            run_summary_fixture.output_dir.mkdir()
            directory_replaced = True
            if unlink_raises:
                raise OSError("injected rollback failure after directory replacement")

    monkeypatch.setattr(os, "link", fail_publication)
    monkeypatch.setattr(Path, "unlink", replace_after_unlink)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="identity changed|injected rollback failure",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert publication_failed and directory_replaced
    assert list(run_summary_fixture.output_dir.iterdir()) == []
    assert (displaced / run_summary_fixture.lock_path.name).is_file()
    assert any(path.name.endswith(".tmp") for path in displaced.iterdir())


def test_post_commit_cleanup_failure_preserves_new_transaction_and_lock(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    real_remove = ARTIFACT_INDEX_API.remove_owned
    cleanup_failed = False

    def fail_temp_cleanup(path: Path) -> None:
        nonlocal cleanup_failed
        if (
            not cleanup_failed
            and path.name.endswith(".tmp")
            and "run_summary.tsv" in path.name
        ):
            cleanup_failed = True
            raise OSError("injected run-summary anchor cleanup failure")
        real_remove(path)

    monkeypatch.setattr(ARTIFACT_INDEX_API, "remove_owned", fail_temp_cleanup)
    with pytest.raises(RUN_SUMMARY_MODELS.RunSummaryError, match="cleanup failed"):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert cleanup_failed
    assert all(path.is_file() for path in run_summary_fixture.summary_paths)
    RUN_SUMMARY_PUBLICATION.validate_published_run_summary(context)
    assert (
        read_tsv(run_summary_fixture.summary_receipt_path)[0]["run_summary_attempt_id"]
        == context.receipt_row["run_summary_attempt_id"]
    )
    assert run_summary_fixture.lock_path.is_file()
    assert list(run_summary_fixture.output_dir.glob("*.RECOVERY.txt"))


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
    first = run_builder(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    header = read_tsv_header(run_summary_fixture.summary_receipt_path)
    rows = read_tsv(run_summary_fixture.summary_receipt_path)
    rows[0][field] = value
    write_tsv(run_summary_fixture.summary_receipt_path, header, rows)

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
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
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert_no_summary_outputs(run_summary_fixture)


def test_prepared_snapshot_rejects_transaction_mutated_during_validation(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mutated = False

    def mutate_then_recheck(context: Any) -> None:
        nonlocal mutated
        if not mutated:
            run_summary_fixture.adapter_fixture.artifacts_path.write_bytes(
                run_summary_fixture.adapter_fixture.artifacts_path.read_bytes() + b"\n"
            )
            mutated = True
        REPORTING_VALIDATION.recheck_run_summary_inputs(context)

    arguments = run_summary_arguments(run_summary_fixture, execute=True)

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="immutable snapshot",
    ):
        RUN_SUMMARY.prepare_context(
            arguments,
            source_checkout=SOURCE_CHECKOUT,
            artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
                root=run_summary_fixture.root
            ),
            deps=build_deps(recheck_inputs=mutate_then_recheck),
        )

    assert mutated
    assert_no_summary_outputs(run_summary_fixture)


def test_prepare_recheck_rejects_identical_byte_record_replacement(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_build_document = RUN_SUMMARY_DOCUMENT._build_document
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

    arguments = run_summary_arguments(run_summary_fixture, execute=True)

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="immutable snapshot",
    ):
        RUN_SUMMARY.prepare_context(
            arguments,
            source_checkout=SOURCE_CHECKOUT,
            artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
                root=run_summary_fixture.root
            ),
            deps=build_deps(build_document=build_then_replace_record),
        )

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
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="identity changed",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert list(run_summary_fixture.output_dir.iterdir()) == []


def test_receipt_is_the_last_published_summary_output(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    real_link = os.link
    publication_order: list[Path] = []

    def track_publication(source: Any, destination: Any, **kwargs: Any) -> None:
        publication_order.append(Path(destination))
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(os, "link", track_publication)
    RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert publication_order == list(run_summary_fixture.summary_paths)
    assert publication_order[-1] == run_summary_fixture.summary_receipt_path
    RUN_SUMMARY_PUBLICATION.validate_published_run_summary(context)
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_required_artifact_limitation_is_computational_only(tmp_path: Path) -> None:
    fixture = FIXTURE.build_missing_fixture(tmp_path / "collision")
    record = read_json(
        fixture.adapter_fixture.records_dir / "sample.SYNTH_A.canonical_bai.json"
    )
    limitations = RUN_SUMMARY_PROJECTION._build_limitations(artifacts=[record])

    assert [row["limitation_id"] for row in limitations] == [
        "required_artifacts_not_complete",
    ]
    assert "scientific" not in limitations[0]["description"].lower()


def test_attempt_aggregation_preserves_independent_chains_and_rejects_conflicts() -> (
    None
):
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

    attempts, superseded = RUN_SUMMARY_PROJECTION._build_attempts(artifacts)

    assert [attempt["attempt_id"] for attempt in attempts] == [
        "attempt-a1",
        "attempt-a2",
        "attempt-b1",
    ]
    assert superseded == ["attempt-a1"]

    conflicting = copy.deepcopy(artifacts)
    conflicting[1]["attempts"][1]["finished_at"] = "2000-01-01T00:00:06Z"
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="conflicting definitions",
    ):
        RUN_SUMMARY_PROJECTION._build_attempts(conflicting)


@pytest.mark.parametrize("final_index", range(4))
@pytest.mark.parametrize("kind", ("file", "dangling_symlink"))
def test_concurrent_final_is_not_overwritten_or_removed(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    final_index: int,
    kind: str,
) -> None:
    context = context_for(run_summary_fixture)
    final = run_summary_fixture.summary_paths[final_index]
    target = final.with_name("absent-concurrent-target")
    real_link = os.link
    foreign_identity: tuple[int, int] | None = None

    def insert_before_link(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal foreign_identity
        if Path(destination) == final:
            if kind == "file":
                final.write_bytes(b"concurrent foreign output\n")
            else:
                final.symlink_to(target)
            metadata = final.lstat()
            foreign_identity = (metadata.st_dev, metadata.st_ino)
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(os, "link", insert_before_link)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError, match="rollback was incomplete"
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert foreign_identity is not None
    assert (final.lstat().st_dev, final.lstat().st_ino) == foreign_identity
    if kind == "file":
        assert final.read_bytes() == b"concurrent foreign output\n"
    else:
        assert final.readlink() == target
        assert not target.exists()
    assert all(
        not os.path.lexists(path)
        for path in run_summary_fixture.summary_paths
        if path != final
    )
    assert run_summary_fixture.lock_path.is_file()
    assert len(list(run_summary_fixture.output_dir.glob("*.tmp"))) == 4
    assert list(run_summary_fixture.output_dir.glob("*.RECOVERY.txt"))


@pytest.mark.parametrize("anchor_fault", ("missing", "replaced"))
def test_unprovable_staging_anchor_retains_final_and_recovery(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    anchor_fault: str,
) -> None:
    context = context_for(run_summary_fixture)
    final = run_summary_fixture.summary_json_path
    real_link = os.link
    changed_anchor: Path | None = None

    def change_anchor_after_link(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal changed_anchor
        real_link(source, destination, **kwargs)
        if Path(destination) == final:
            changed_anchor = Path(source)
            changed_anchor.unlink()
            if anchor_fault == "replaced":
                changed_anchor.write_bytes(b"foreign anchor\n")
            raise OSError("injected staging-anchor mutation")

    monkeypatch.setattr(os, "link", change_anchor_after_link)
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError, match="rollback was incomplete"
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(context)

    assert changed_anchor is not None
    assert final.read_bytes() == context.summary_json_bytes
    if anchor_fault == "replaced":
        assert changed_anchor.read_bytes() == b"foreign anchor\n"
    else:
        assert not changed_anchor.exists()
    assert all(not path.exists() for path in run_summary_fixture.summary_paths[1:])
    assert run_summary_fixture.lock_path.is_file()
    assert list(run_summary_fixture.output_dir.glob("*.RECOVERY.txt"))
