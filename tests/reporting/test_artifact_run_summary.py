"""Focused integration and transaction tests for artifact-run-summary."""

from __future__ import annotations

import copy
import csv
import dataclasses
import hashlib
import importlib
import json
import os
import signal
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from emrys import __main__ as emrys_cli
from emrys.contracts.artifacts import api as CONTRACTS
from emrys.libraries import source_authority as SOURCE_AUTHORITY
from emrys.libraries.source_authority import controlled_python_argv
from emrys.reporting import transaction_validation as REPORTING_VALIDATION
from emrys.reporting._artifact_index import api as ARTIFACT_INDEX_API
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as FIXTURE

if TYPE_CHECKING:
    import argparse

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_EPOCH = "1700000000"
CLI_USAGE_ERROR = 2

RUN_SUMMARY = importlib.import_module("emrys.reporting._run_summary.builder")
RUN_SUMMARY_DOCUMENT = importlib.import_module("emrys.reporting._run_summary.document")
RUN_SUMMARY_MODELS = importlib.import_module("emrys.reporting._run_summary.models")
RUN_SUMMARY_PROJECTION = importlib.import_module(
    "emrys.reporting._run_summary.projection"
)
RUN_SUMMARY_PUBLICATION = importlib.import_module(
    "emrys.reporting._run_summary.publication"
)
RUN_SUMMARY_TRANSACTION = importlib.import_module(
    "emrys.reporting._run_summary.transaction"
)
SOURCE_CHECKOUT = SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT)


def build_deps(**overrides: Any) -> Any:
    return dataclasses.replace(
        RUN_SUMMARY.DEFAULT_RUN_SUMMARY_BUILD_DEPS,
        **overrides,
    )


def publication_ops(**overrides: Any) -> Any:
    return dataclasses.replace(
        RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS,
        **overrides,
    )


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
        [
            *controlled_python_argv(sys.executable, "-m", "emrys"),
            "build",
            "run-summary",
            *cli_arguments,
        ],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def _parse_run_summary_arguments(
    arguments: Sequence[str],
) -> argparse.Namespace:
    return emrys_cli.build_parser().parse_args(
        ["build", "run-summary", *arguments],
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
        arguments = _parse_run_summary_arguments(fixture.command_args(execute=True))
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


def test_grouped_builder_admits_before_loading_inputs_and_retains_token(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The grouped builder admits its checkout before reading run inputs."""
    admitted = SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT)
    artifact_root = SOURCE_AUTHORITY.ArtifactSourceRoot(root=run_summary_fixture.root)
    expected_package_root = Path(RUN_SUMMARY.__file__).resolve().parents[2]
    real_load_input_transaction = RUN_SUMMARY_TRANSACTION._load_input_transaction
    events: list[str] = []
    observed_contexts: list[RUN_SUMMARY_MODELS.BuildContext] = []

    def admit_source_checkout(
        *,
        root: Path,
        package_root: Path,
    ) -> SOURCE_AUTHORITY.SourceCheckout:
        assert root == REPO_ROOT
        assert package_root == expected_package_root
        events.append("admit")
        return admitted

    def admit_artifact_source_root(
        *, root: Path
    ) -> SOURCE_AUTHORITY.ArtifactSourceRoot:
        assert root == run_summary_fixture.root
        events.append("admit-artifacts")
        return artifact_root

    def load_input_transaction(*, source_root: Path, **kwargs: Any) -> object:
        assert source_root == artifact_root.root
        events.append("load")
        return real_load_input_transaction(
            source_root=source_root,
            **kwargs,
        )

    def observe_context(context: RUN_SUMMARY_MODELS.BuildContext) -> None:
        events.append("print")
        observed_contexts.append(context)

    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    monkeypatch.setattr(
        RUN_SUMMARY,
        "admit_source_checkout",
        admit_source_checkout,
    )
    monkeypatch.setattr(
        RUN_SUMMARY,
        "admit_artifact_source_root",
        admit_artifact_source_root,
    )
    monkeypatch.setattr(RUN_SUMMARY, "print_context", observe_context)
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=False),
    )

    status = RUN_SUMMARY.build_from_args(
        arguments,
        deps=build_deps(load_input_transaction=load_input_transaction),
    )

    assert status == 0
    assert events == ["admit", "admit-artifacts", "load", "print"]
    assert len(observed_contexts) == 1
    assert observed_contexts[0].source_checkout == admitted
    assert observed_contexts[0].artifact_source_root == artifact_root


@pytest.mark.parametrize(
    ("arguments", "expected_status"),
    [(["--help"], 0), ([], 2)],
)
def test_parser_termination_precedes_lazy_run_summary_builder_import(
    arguments: list[str],
    expected_status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Help and parse failures terminate before the lazy builder handler."""
    dispatch_attempted = False

    def unexpected_dispatch(_arguments: argparse.Namespace) -> int:
        nonlocal dispatch_attempted
        dispatch_attempted = True
        pytest.fail("run-summary builder was imported before parsing terminated")

    monkeypatch.setattr(
        emrys_cli,
        "_build_run_summary_from_args",
        unexpected_dispatch,
    )

    with pytest.raises(SystemExit) as termination:
        emrys_cli.main(["build", "run-summary", *arguments])

    assert not dispatch_attempted
    assert termination.value.code == expected_status


def test_grouped_cli_requires_explicit_source_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing checkout authority fails parsing before builder dispatch."""
    monkeypatch.setattr(
        emrys_cli,
        "_build_run_summary_from_args",
        lambda _arguments: pytest.fail("run-summary builder was dispatched"),
    )
    arguments = [
        "build",
        "run-summary",
        "--run-id",
        "synthetic-run",
        "--artifact-receipt",
        str(tmp_path / "artifact-receipt.tsv"),
        "--output-root",
        str(tmp_path / "output"),
    ]

    with pytest.raises(SystemExit) as termination:
        emrys_cli.main(arguments)

    assert termination.value.code == CLI_USAGE_ERROR
    captured = capsys.readouterr()
    assert not captured.out
    assert "--source-checkout" in captured.err


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
    validate_artifact_transaction = _source_root_spy(
        RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.validate_artifact_transaction,
        artifact_root.root,
        root_calls,
        "published_transaction",
    )
    recheck_ops = publication_ops(
        validate_artifact_transaction=validate_artifact_transaction,
    )

    def recheck_inputs(context: Any) -> None:
        REPORTING_VALIDATION.recheck_run_summary_inputs(context, ops=recheck_ops)

    arguments = _parse_run_summary_arguments(fixture.command_args(execute=False))

    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=source_checkout,
        artifact_source_root=artifact_root,
        deps=build_deps(
            recheck_inputs=recheck_inputs,
            matching_checkout_head_commit=matching_checkout_head_commit,
        ),
    )

    expected_single_calls = 1
    expected_prepare_rechecks = 1
    assert context.source_checkout == source_checkout
    assert context.artifact_source_root == artifact_root
    assert root_calls["git"] == expected_single_calls
    assert root_calls["inventory"] == expected_single_calls
    assert root_calls["published_transaction"] == expected_prepare_rechecks
    assert root_calls["document_semantics"] == expected_single_calls
    assert root_calls["document_inventory"] == expected_single_calls


def test_prepare_context_uses_local_build_for_unattributable_package(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=False)
    )
    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=SOURCE_CHECKOUT,
        artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
            root=run_summary_fixture.root
        ),
        deps=build_deps(matching_checkout_head_commit=lambda **_kwargs: None),
    )

    assert context.git_commit == "local_build"
    assert context.document["provenance"]["git_commit"] == "local_build"


def test_explicit_artifact_root_reaches_predecessor_and_post_publish_rechecks(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Publication retains the prepared authority through its success checks."""
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    authority = SOURCE_AUTHORITY.ArtifactSourceRoot(root=run_summary_fixture.root)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True),
    )
    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=SOURCE_CHECKOUT,
        artifact_source_root=authority,
    )
    root_calls: Counter[str] = Counter()
    monkeypatch.setattr(
        CONTRACTS,
        "validate_run_summary_semantics",
        _source_root_spy(
            CONTRACTS.validate_run_summary_semantics,
            authority.root,
            root_calls,
            "semantic_validation",
        ),
    )
    default_ops = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS
    ops = publication_ops(
        validate_artifact_transaction=_source_root_spy(
            default_ops.validate_artifact_transaction,
            authority.root,
            root_calls,
            "recheck",
        ),
        validate_document=_source_root_spy(
            default_ops.validate_document,
            authority.root,
            root_calls,
            "post_publish_document",
        ),
        validate_existing_summary=_source_root_spy(
            default_ops.validate_existing_summary,
            authority.root,
            root_calls,
            "predecessor",
        ),
    )

    RUN_SUMMARY_PUBLICATION.publish_context(context, ops=ops)

    expected_rechecks = 2
    expected_predecessor_and_published_checks = 2
    expected_semantic_checks = 3
    assert root_calls["recheck"] == expected_rechecks
    assert root_calls["post_publish_document"] == 1
    assert root_calls["predecessor"] == expected_predecessor_and_published_checks
    assert root_calls["semantic_validation"] == expected_semantic_checks
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_explicit_artifact_root_reaches_restored_rollback_validation(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rollback validates the restored predecessor with the retained root."""
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = summary_snapshot(run_summary_fixture)
    authority = SOURCE_AUTHORITY.ArtifactSourceRoot(root=run_summary_fixture.root)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True),
    )
    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=SOURCE_CHECKOUT,
        artifact_source_root=authority,
    )
    default_ops = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS
    real_replace = default_ops.replace
    root_calls: Counter[str] = Counter()
    failed = False

    def fail_qc_publication(source: Any, destination: Any) -> None:
        nonlocal failed
        if (
            not failed
            and Path(destination) == run_summary_fixture.qc_summary_path
            and ".tmp" in Path(source).name
        ):
            failed = True
            message = "injected authority rollback failure"
            raise OSError(message)
        real_replace(source, destination)

    monkeypatch.setattr(
        CONTRACTS,
        "validate_run_summary_semantics",
        _source_root_spy(
            CONTRACTS.validate_run_summary_semantics,
            authority.root,
            root_calls,
            "restored_semantics",
        ),
    )
    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="injected authority rollback failure",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(
                replace=fail_qc_publication,
                validate_existing_summary=_source_root_spy(
                    default_ops.validate_existing_summary,
                    authority.root,
                    root_calls,
                    "restored_predecessor",
                ),
            ),
        )

    expected_predecessor_and_restored_checks = 2
    assert failed
    assert (
        root_calls["restored_predecessor"] == expected_predecessor_and_restored_checks
    )
    assert root_calls["restored_semantics"] == expected_predecessor_and_restored_checks
    assert summary_snapshot(run_summary_fixture) == before
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_source_checkout_admission_error_precedes_input_diagnostics(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Grouped admission failures are controlled before any input is loaded."""
    expected_package_root = Path(RUN_SUMMARY.__file__).resolve().parents[2]

    def reject_source_checkout(
        *,
        root: Path,
        package_root: Path,
    ) -> SOURCE_AUTHORITY.SourceCheckout:
        assert root == REPO_ROOT
        assert package_root == expected_package_root
        message = "injected run-summary checkout rejection"
        raise SOURCE_AUTHORITY.SourceCheckoutError(message)

    monkeypatch.setattr(
        RUN_SUMMARY,
        "admit_source_checkout",
        reject_source_checkout,
    )
    monkeypatch.setattr(emrys_cli, "require_controlled_python_runtime", lambda: None)
    assert (
        emrys_cli.main(
            [
                "build",
                "run-summary",
                *run_summary_fixture.command_args(execute=False),
            ],
        )
        == 1
    )
    captured = capsys.readouterr()
    assert not captured.out
    assert captured.err == "ERROR: injected run-summary checkout rejection\n"
    assert_no_summary_outputs(run_summary_fixture)


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
        [
            *controlled_python_argv(sys.executable, "-m", "emrys"),
            "build",
            "run-summary",
            "--help",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    result = run_cli(run_summary_fixture)

    assert help_result.returncode == 0, help_result.stderr
    for option in (
        "--source-checkout",
        "--run-id",
        "--artifact-receipt",
        "--output-root",
        "--execute",
    ):
        assert option in help_result.stdout
    assert "science-review" not in help_result.stdout
    assert "report-table-approvals" not in help_result.stdout
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout.lower()
    assert run_summary_fixture.run_id in result.stdout
    assert "receipt" in result.stdout.lower()
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
        context.summary_rows,
    )


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


def test_fixed_epoch_rerender_keeps_json_and_views_byte_identical(
    run_summary_fixture: Any,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = {
        path.name: path.read_bytes() for path in run_summary_fixture.summary_paths[:3]
    }

    second = run_cli(run_summary_fixture, execute=True)

    assert second.returncode == 0, second.stderr
    assert {
        path.name: path.read_bytes() for path in run_summary_fixture.summary_paths[:3]
    } == before
    validate_summary_document(run_summary_fixture)


def test_unrelated_files_are_ignored_and_preserved(
    run_summary_fixture: Any,
) -> None:
    unrelated = run_summary_fixture.output_dir / "unrelated.run_summary.json"
    unrelated_payload = b'{"unrelated":true}\n'
    unrelated.write_bytes(unrelated_payload)
    decoy = run_summary_fixture.output_dir / "decoy.tsv"
    decoy_payload = b"unrelated\nvalue\n"
    decoy.write_bytes(decoy_payload)

    result = run_cli(run_summary_fixture, execute=True)

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


def test_qc_view_keeps_all_repeated_metrics_but_json_ids_are_unique(
    run_summary_fixture: Any,
) -> None:
    result = run_cli(run_summary_fixture, execute=True)
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
    assert document["interpretation_boundary"].endswith(
        "biological_validation_outside_emrys"
    )


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
    real_replace = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.replace
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

    with pytest.raises(
        Exception,
        match="injected run-summary replacement failure",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(replace=fail_qc_publication),
        )

    assert failed
    assert summary_snapshot(run_summary_fixture) == before
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_publication_installs_and_restores_signal_handlers(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    watched = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    original = {signum: signal.getsignal(signum) for signum in watched}
    default_ops = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS
    real_install = default_ops.install_signal_handlers
    real_restore = default_ops.restore_signal_handlers
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
    RUN_SUMMARY_PUBLICATION.publish_context(
        context,
        ops=publication_ops(
            install_signal_handlers=track_install,
            restore_signal_handlers=track_restore,
        ),
    )

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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="Could not install",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(install_signal_handlers=fail_install),
        )

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
    real_remove_owned = (
        RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.remove_owned
    )
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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="cleanup failed",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(remove_owned=interrupt_first_temp_cleanup),
        )

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
    real_replace = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.replace
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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="interrupted by signal SIGTERM",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(replace=interrupt_after_receipt_backup),
        )

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
    real_replace = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.replace
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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="rollback was incomplete",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(replace=fail_then_corrupt_restored_receipt),
        )

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
        path.name.endswith(".previous") and "run_summary_receipt.tsv" in path.name
        for path in run_summary_fixture.output_dir.iterdir()
    )


def test_first_publication_failure_removes_owned_outputs_and_lock(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.replace
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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="injected first run-summary publication failure",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(replace=fail_qc_publication),
        )

    assert failed
    assert_no_summary_outputs(run_summary_fixture)


def test_incomplete_replacement_rollback_retains_lock_and_recovery_paths(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    context = context_for(run_summary_fixture)
    real_replace = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.replace
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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="rollback was incomplete",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(replace=fail_publication_and_restoration),
        )

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
        path.name.endswith(".previous") and "run_summary_receipt.tsv" in path.name
        for path in run_summary_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".previous") and "run_summary.json" in path.name
        for path in run_summary_fixture.output_dir.iterdir()
    )


def test_mid_rollback_directory_replacement_skips_replacement_path_cleanup(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(run_summary_fixture)
    default_ops = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS
    real_replace = default_ops.replace
    real_remove_owned = default_ops.remove_owned
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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="identity changed",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(
                replace=fail_qc_publication,
                remove_owned=replace_directory_after_first_rollback_remove,
            ),
        )

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
    real_remove_owned = (
        RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.remove_owned
    )
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

    with pytest.raises(
        RUN_SUMMARY_MODELS.RunSummaryError,
        match="cleanup failed",
    ):
        RUN_SUMMARY_PUBLICATION.publish_context(
            context,
            ops=publication_ops(remove_owned=fail_one_backup_cleanup),
        )

    assert cleanup_failed
    assert all(path.is_file() for path in run_summary_fixture.summary_paths)
    RUN_SUMMARY_PUBLICATION.validate_published_run_summary(context)
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
    real_validate = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.validate_artifact_transaction
    mutated = False

    def validate_then_mutate(**kwargs: Any) -> None:
        nonlocal mutated
        real_validate(**kwargs)
        if not mutated:
            run_summary_fixture.adapter_fixture.artifacts_path.write_bytes(
                run_summary_fixture.adapter_fixture.artifacts_path.read_bytes() + b"\n"
            )
            mutated = True

    recheck_ops = publication_ops(
        validate_artifact_transaction=validate_then_mutate,
    )

    def recheck_inputs(context: Any) -> None:
        REPORTING_VALIDATION.recheck_run_summary_inputs(context, ops=recheck_ops)

    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True)
    )

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
            deps=build_deps(recheck_inputs=recheck_inputs),
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

    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True)
    )

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
    real_replace = RUN_SUMMARY_PUBLICATION.DEFAULT_RUN_SUMMARY_PUBLICATION_OPS.replace
    final_paths = set(run_summary_fixture.summary_paths)
    publication_order: list[Path] = []

    def track_publication(source: Any, destination: Any) -> None:
        destination_path = Path(destination)
        if destination_path in final_paths and ".tmp" in Path(source).name:
            publication_order.append(destination_path)
        real_replace(source, destination)

    RUN_SUMMARY_PUBLICATION.publish_context(
        context,
        ops=publication_ops(replace=track_publication),
    )

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
