"""Focused integration and transaction tests for artifact-run-summary."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from norad import __main__ as norad_cli
from norad.reporting._artifact_index import api as ARTIFACT_INDEX_API
from norad.reporting._artifact_index import source_checkout as _source_checkout_owner
from norad.reporting._run_summary import science_evidence as SCIENCE_EVIDENCE
from norad.reporting._run_summary import science_models as SCIENCE_MODELS
from norad.reporting._run_summary import science_package as SCIENCE_PACKAGE
from norad.reporting._run_summary import science_projection as SCIENCE

if TYPE_CHECKING:
    import argparse

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_BUILDER = (
    REPO_ROOT
    / "tests"
    / "reporting"
    / "fixtures"
    / "artifact_run_summary_v1"
    / "build_fixture.py"
)
FIXED_EPOCH = "1700000000"
CLI_USAGE_ERROR = 2


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
RUN_SUMMARY = importlib.import_module("norad.reporting._run_summary.builder")
CONTRACTS = RUN_SUMMARY.contracts
SOURCE_CHECKOUT = RUN_SUMMARY.adapter.SourceCheckout(root=REPO_ROOT)


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
            sys.executable,
            "-I",
            "-m",
            "norad",
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
    return norad_cli.build_parser().parse_args(
        ["build", "run-summary", *arguments],
    )


def test_run_summary_uses_shared_private_owner_identities() -> None:
    assert (
        RUN_SUMMARY.adapter
        is RUN_SUMMARY._models.adapter
        is RUN_SUMMARY._publication.adapter
        is ARTIFACT_INDEX_API
    )
    assert RUN_SUMMARY.science is RUN_SUMMARY._publication.science is SCIENCE
    assert RUN_SUMMARY.contracts is SCIENCE.contracts is SCIENCE_PACKAGE.contracts
    assert (
        RUN_SUMMARY._models.review_package
        is SCIENCE.review_package
        is SCIENCE_PACKAGE.review_package
    )
    assert FIXTURE.ADAPTER.review_package is SCIENCE.review_package
    assert FIXTURE.REVIEW_PACKAGE is SCIENCE.review_package
    assert SCIENCE_EVIDENCE.contracts is SCIENCE.contracts
    assert (
        SCIENCE.RunSummaryScienceError
        is SCIENCE_MODELS.RunSummaryScienceError
        is SCIENCE_PACKAGE.RunSummaryScienceError
    )
    assert ARTIFACT_INDEX_API.SourceCheckout is _source_checkout_owner.SourceCheckout
    assert (
        ARTIFACT_INDEX_API.SourceCheckoutError
        is _source_checkout_owner.SourceCheckoutError
    )
    assert (
        ARTIFACT_INDEX_API.admit_source_checkout
        is _source_checkout_owner.admit_source_checkout
    )


def test_run_summary_science_has_no_private_step09c_dependency() -> None:
    source = Path(SCIENCE.__file__).read_text(encoding="utf-8")
    assert "norad.evidence.scientific_review_package" not in source
    assert not hasattr(SCIENCE, "step09c")


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


def context_for(fixture: Any) -> Any:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    try:
        arguments = _parse_run_summary_arguments(fixture.command_args(execute=True))
        return RUN_SUMMARY.prepare_context(
            arguments,
            source_checkout=SOURCE_CHECKOUT,
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
    admitted = ARTIFACT_INDEX_API.SourceCheckout(root=REPO_ROOT)
    expected_package_root = Path(RUN_SUMMARY.__file__).resolve().parents[2]
    real_load_input_transaction = RUN_SUMMARY._load_input_transaction
    events: list[str] = []
    observed_contexts: list[RUN_SUMMARY.BuildContext] = []

    def admit_source_checkout(
        *,
        root: Path,
        package_root: Path,
    ) -> ARTIFACT_INDEX_API.SourceCheckout:
        assert root == REPO_ROOT
        assert package_root == expected_package_root
        events.append("admit")
        return admitted

    def load_input_transaction(*, source_root: Path, **kwargs: Any) -> object:
        assert source_root == admitted.root
        events.append("load")
        return real_load_input_transaction(
            source_root=source_root,
            **kwargs,
        )

    def observe_context(context: RUN_SUMMARY.BuildContext) -> None:
        events.append("print")
        observed_contexts.append(context)

    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "admit_source_checkout",
        admit_source_checkout,
    )
    monkeypatch.setattr(
        RUN_SUMMARY,
        "_load_input_transaction",
        load_input_transaction,
    )
    monkeypatch.setattr(RUN_SUMMARY, "print_context", observe_context)
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=False),
    )

    status = RUN_SUMMARY.build_from_args(arguments)

    assert status == 0
    assert events == ["admit", "load", "print"]
    assert len(observed_contexts) == 1
    assert observed_contexts[0].source_checkout is admitted


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
        norad_cli,
        "_build_run_summary_from_args",
        unexpected_dispatch,
    )

    with pytest.raises(SystemExit) as termination:
        norad_cli.main(["build", "run-summary", *arguments])

    assert not dispatch_attempted
    assert termination.value.code == expected_status


def test_grouped_cli_requires_explicit_source_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing checkout authority fails parsing before builder dispatch."""
    monkeypatch.setattr(
        norad_cli,
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
        norad_cli.main(arguments)

    assert termination.value.code == CLI_USAGE_ERROR
    captured = capsys.readouterr()
    assert not captured.out
    assert "--source-checkout" in captured.err


def test_prepare_context_threads_one_explicit_source_checkout_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One explicit root reaches preparation, science, and approval seams."""
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "authority",
        roles=("candidate_selection",),
    )
    authority = ARTIFACT_INDEX_API.SourceCheckout(root=fixture.root)
    root_calls: Counter[str] = Counter()
    real_get_git_commit = RUN_SUMMARY.adapter.get_git_commit

    def get_git_commit(
        *,
        source_root: Path,
        sanitize_git_routing: bool,
    ) -> str:
        assert source_root == authority.root
        assert sanitize_git_routing is True
        root_calls["git"] += 1
        return real_get_git_commit(
            source_root=REPO_ROOT,
            sanitize_git_routing=True,
        )

    def unexpected_admission(**_kwargs: Any) -> None:
        pytest.fail("explicit SourceCheckout triggered a second admission")

    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "foreign.git"))
    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "admit_source_checkout",
        unexpected_admission,
    )
    monkeypatch.setattr(RUN_SUMMARY.adapter, "get_git_commit", get_git_commit)
    for owner, attribute, label in (
        (CONTRACTS, "validate_inventory", "inventory"),
        (
            RUN_SUMMARY.adapter,
            "validate_published_transaction",
            "published_transaction",
        ),
        (CONTRACTS, "resolve_contract_path", "science_contract"),
        (
            RUN_SUMMARY.science,
            "normalize_scientific_review",
            "science_normalization",
        ),
        (RUN_SUMMARY, "_normalize_report_table_approvals", "approvals"),
        (CONTRACTS, "validate_run_summary_semantics", "document_semantics"),
        (CONTRACTS, "reconcile_document_inventory", "document_inventory"),
    ):
        monkeypatch.setattr(
            owner,
            attribute,
            _source_root_spy(
                getattr(owner, attribute),
                authority.root,
                root_calls,
                label,
            ),
        )
    arguments = _parse_run_summary_arguments(fixture.command_args(execute=False))

    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=authority,
    )

    expected_single_calls = 1
    expected_prepare_rechecks = 2
    assert context.source_checkout is authority
    assert root_calls["git"] == expected_single_calls
    assert root_calls["inventory"] == expected_single_calls
    assert root_calls["published_transaction"] == expected_prepare_rechecks
    assert root_calls["science_contract"] > 0
    assert root_calls["science_normalization"] == expected_prepare_rechecks
    assert root_calls["approvals"] == expected_single_calls
    assert root_calls["document_semantics"] == expected_single_calls
    assert root_calls["document_inventory"] == expected_single_calls


def test_explicit_checkout_root_reaches_predecessor_and_post_publish_rechecks(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Publication retains the prepared authority through its success checks."""
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    authority = ARTIFACT_INDEX_API.SourceCheckout(root=run_summary_fixture.root)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True),
    )
    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=SOURCE_CHECKOUT,
    )
    # A distinct sentinel makes any fallback to the module default observable.
    context.source_checkout = authority
    root_calls: Counter[str] = Counter()
    for owner, attribute, label in (
        (RUN_SUMMARY.adapter, "validate_published_transaction", "recheck"),
        (RUN_SUMMARY._publication, "_validate_document", "post_publish_document"),
        (RUN_SUMMARY._publication, "_validate_existing_summary", "predecessor"),
        (CONTRACTS, "validate_run_summary_semantics", "semantic_validation"),
    ):
        monkeypatch.setattr(
            owner,
            attribute,
            _source_root_spy(
                getattr(owner, attribute),
                authority.root,
                root_calls,
                label,
            ),
        )

    RUN_SUMMARY.publish_context(context)

    expected_rechecks = 2
    expected_predecessor_and_published_checks = 2
    expected_semantic_checks = 3
    assert root_calls["recheck"] == expected_rechecks
    assert root_calls["post_publish_document"] == 1
    assert root_calls["predecessor"] == expected_predecessor_and_published_checks
    assert root_calls["semantic_validation"] == expected_semantic_checks
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_explicit_checkout_root_reaches_restored_rollback_validation(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rollback validates the restored predecessor with the retained root."""
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = summary_snapshot(run_summary_fixture)
    authority = ARTIFACT_INDEX_API.SourceCheckout(root=run_summary_fixture.root)
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True),
    )
    context = RUN_SUMMARY.prepare_context(
        arguments,
        source_checkout=SOURCE_CHECKOUT,
    )
    # A distinct sentinel makes any fallback to the module default observable.
    context.source_checkout = authority
    real_replace = RUN_SUMMARY.os.replace
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
        RUN_SUMMARY._publication,
        "_validate_existing_summary",
        _source_root_spy(
            RUN_SUMMARY._publication._validate_existing_summary,
            authority.root,
            root_calls,
            "restored_predecessor",
        ),
    )
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
    monkeypatch.setattr(RUN_SUMMARY.os, "replace", fail_qc_publication)

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="injected authority rollback failure",
    ):
        RUN_SUMMARY.publish_context(context)

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
    ) -> ARTIFACT_INDEX_API.SourceCheckout:
        assert root == REPO_ROOT
        assert package_root == expected_package_root
        message = "injected run-summary checkout rejection"
        raise ARTIFACT_INDEX_API.SourceCheckoutError(message)

    def unexpected_input_load(**_kwargs: Any) -> None:
        pytest.fail("input diagnostics ran before admission")

    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "admit_source_checkout",
        reject_source_checkout,
    )
    monkeypatch.setattr(
        RUN_SUMMARY,
        "_load_input_transaction",
        unexpected_input_load,
    )

    assert (
        norad_cli.main(
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
            sys.executable,
            "-I",
            "-m",
            "norad",
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
        "--science-review-summary",
        "--report-table-approvals",
        "--execute",
    ):
        assert option in help_result.stdout
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout.lower()
    assert run_summary_fixture.run_id in result.stdout
    assert "receipt" in result.stdout.lower()
    assert_no_summary_outputs(run_summary_fixture)


def test_live_run_summary_header_owner_controls_serialized_bytes(
    run_summary_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = RUN_SUMMARY.RUN_SUMMARY_HEADER
    mutated = (original[1], original[0], *original[2:])
    monkeypatch.setattr(RUN_SUMMARY, "RUN_SUMMARY_HEADER", mutated)

    context = context_for(run_summary_fixture)

    assert context.summary_tsv_bytes.splitlines()[0] == ("\t".join(mutated).encode())
    assert context.summary_tsv_bytes != RUN_SUMMARY.adapter.tsv_bytes(
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
    assert document["approved_report_tables"] == []
    assert document["parameters"]["report_table_approvals"] is None
    assert_no_summary_residue_after_success(run_summary_fixture)


def test_explicit_report_table_approvals_are_normalized_and_provenanced(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "approved",
        science_status="evidence_incomplete",
    )

    dry_run = run_cli(fixture)

    assert dry_run.returncode == 0, dry_run.stderr
    assert str(fixture.report_table_approvals) in dry_run.stdout
    assert "Approved report tables: 2" in dry_run.stdout
    assert_no_summary_outputs(fixture)

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    document = validate_summary_document(fixture)
    approvals = document["approved_report_tables"]
    assert [row["role"] for row in approvals] == [
        "candidate_selection",
        "candidate_adjudication",
    ]
    assert [row["table_id"] for row in approvals] == [
        "synthetic_candidate_selection",
        "synthetic_candidate_adjudication",
    ]
    assert all(row["approval"]["status"] == "approved" for row in approvals)
    assert all(
        row["approval"]["policy_version"] == "synthetic_report_policy_v1"
        for row in approvals
    )
    assert all(
        row["approval"]["approved_by"] == "synthetic_scientific_owner"
        for row in approvals
    )
    artifact_index = {
        artifact["artifact_id"]: artifact for artifact in document["artifacts"]
    }
    for approval in approvals:
        source = artifact_index[approval["artifact_id"]]["source"]
        assert approval["path"] == source["path"]
        assert approval["sha256"] == source["sha256"]
        assert approval["row_count"] == source["row_count"]
    approval_source = document["parameters"]["report_table_approvals"]
    assert approval_source == {
        "path": str(fixture.report_table_approvals),
        "sha256": sha256_file(fixture.report_table_approvals),
        "size_bytes": fixture.report_table_approvals.stat().st_size,
        "row_count": 2,
        "media_type": "text/tab-separated-values",
    }
    receipt = read_tsv(fixture.summary_receipt_path)[0]
    assert receipt["producer_version"] == RUN_SUMMARY.PRODUCER_VERSION
    assert receipt["run_summary_json_sha256"] == sha256_file(fixture.summary_json_path)
    assert document["science_status"] == "evidence_incomplete"
    assert_no_summary_residue_after_success(fixture)


def test_header_only_report_table_is_a_valid_explicit_approval(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "header-only",
        roles=("candidate_selection",),
        header_only_roles=("candidate_selection",),
    )
    rows = read_tsv(fixture.report_table_approvals)
    assert rows[0]["row_count"] == "0"

    result = run_cli(fixture, execute=True)

    assert result.returncode == 0, result.stderr
    approval = validate_summary_document(fixture)["approved_report_tables"][0]
    assert approval["row_count"] == 0
    assert approval["display_row_limit"] is None


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("run_id", "wrong_run", "wrong run_id"),
        (
            "run_contract_sha256",
            "f" * 64,
            "wrong run_contract_sha256",
        ),
        ("approval_status", "pending", "approval_status"),
        ("display_row_limit", "", "canonical non-negative"),
        ("row_count", "00", "canonical non-negative"),
    ],
)
def test_report_table_approvals_fail_closed_on_identity_and_scalar_errors(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / field,
        roles=("candidate_selection",),
    )
    rows = read_tsv(fixture.report_table_approvals)
    rows[0][field] = value
    write_tsv(
        fixture.report_table_approvals,
        RUN_SUMMARY.REPORT_TABLE_APPROVALS_HEADER,
        rows,
    )

    result = run_cli(fixture)

    assert result.returncode != 0
    assert message in result.stderr
    assert_no_summary_outputs(fixture)


def test_report_table_approvals_reject_empty_duplicate_and_decoy_inputs(
    tmp_path: Path,
) -> None:
    empty = FIXTURE.build_approved_science_fixture(
        tmp_path / "empty",
        roles=("candidate_selection",),
    )
    write_tsv(
        empty.report_table_approvals,
        RUN_SUMMARY.REPORT_TABLE_APPROVALS_HEADER,
        [],
    )
    empty_result = run_cli(empty)
    assert empty_result.returncode != 0
    assert "must contain at least one" in empty_result.stderr
    assert_no_summary_outputs(empty)

    duplicate = FIXTURE.build_approved_science_fixture(
        tmp_path / "duplicate",
        roles=("candidate_selection",),
    )
    rows = read_tsv(duplicate.report_table_approvals)
    write_tsv(
        duplicate.report_table_approvals,
        RUN_SUMMARY.REPORT_TABLE_APPROVALS_HEADER,
        [rows[0], rows[0]],
    )
    duplicate_result = run_cli(duplicate)
    assert duplicate_result.returncode != 0
    assert "Duplicate" in duplicate_result.stderr
    assert_no_summary_outputs(duplicate)

    decoy = FIXTURE.build_explicit_science_fixture(tmp_path / "decoy")
    decoy_path = decoy.output_dir / "report_table_approvals.tsv"
    decoy_path.write_text("not\tdiscovered\n", encoding="utf-8")
    omitted = run_cli(decoy, execute=True)
    assert omitted.returncode == 0, omitted.stderr
    document = validate_summary_document(decoy)
    assert document["approved_report_tables"] == []
    assert document["parameters"]["report_table_approvals"] is None
    assert decoy_path.read_text(encoding="utf-8") == "not\tdiscovered\n"


def test_report_table_approval_header_role_source_and_time_fail_closed(
    tmp_path: Path,
) -> None:
    bad_header = FIXTURE.build_approved_science_fixture(
        tmp_path / "header",
        roles=("candidate_selection",),
    )
    rows = read_tsv(bad_header.report_table_approvals)
    write_tsv(
        bad_header.report_table_approvals,
        RUN_SUMMARY.REPORT_TABLE_APPROVALS_HEADER[:-1],
        [
            {
                field: rows[0][field]
                for field in RUN_SUMMARY.REPORT_TABLE_APPROVALS_HEADER[:-1]
            }
        ],
    )
    header_result = run_cli(bad_header)
    assert header_result.returncode != 0
    assert "invalid TSV header" in header_result.stderr
    assert_no_summary_outputs(bad_header)

    mutations = (
        ("role", "candidate_adjudication", "artifact contract"),
        ("sha256", "0" * 64, "hash or row count"),
        ("row_count", "999", "hash or row count"),
        ("display_row_limit", "999", "must not exceed"),
        ("approved_at", "2999-01-01T00:00:00Z", "must not be later"),
    )
    for index, (field, value, message) in enumerate(mutations):
        fixture = FIXTURE.build_approved_science_fixture(
            tmp_path / f"mutation-{index}",
            roles=("candidate_selection",),
        )
        approval_rows = read_tsv(fixture.report_table_approvals)
        approval_rows[0][field] = value
        write_tsv(
            fixture.report_table_approvals,
            RUN_SUMMARY.REPORT_TABLE_APPROVALS_HEADER,
            approval_rows,
        )
        result = run_cli(fixture)
        assert result.returncode != 0
        assert message in result.stderr
        assert_no_summary_outputs(fixture)


def test_report_table_approvals_require_exact_science_and_non_symlink_manifest(
    tmp_path: Path,
) -> None:
    no_science = FIXTURE.build_approved_science_fixture(
        tmp_path / "no-science",
        roles=("candidate_selection",),
    )
    arguments = no_science.command_args(
        include_science=False,
        include_approvals=True,
    )
    result = run_cli(no_science, arguments=arguments)
    assert result.returncode != 0
    assert "require the exact committed Step 09c" in result.stderr
    assert_no_summary_outputs(no_science)

    symlinked = FIXTURE.build_approved_science_fixture(
        tmp_path / "symlinked",
        roles=("candidate_selection",),
    )
    link = symlinked.root / "approval-link.tsv"
    link.symlink_to(symlinked.report_table_approvals)
    arguments = symlinked.command_args()
    arguments[arguments.index("--report-table-approvals") + 1] = str(link)
    result = run_cli(symlinked, arguments=arguments)
    assert result.returncode != 0
    assert "symbolic link" in result.stderr
    assert_no_summary_outputs(symlinked)


def test_fixed_approval_retry_is_deterministic_and_supersedes(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "retry",
        roles=("candidate_selection",),
    )
    first = run_cli(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = {path.name: path.read_bytes() for path in fixture.summary_paths[:3]}
    first_receipt = read_tsv(fixture.summary_receipt_path)[0]

    second = run_cli(fixture, execute=True)

    assert second.returncode == 0, second.stderr
    assert {
        path.name: path.read_bytes() for path in fixture.summary_paths[:3]
    } == before
    second_receipt = read_tsv(fixture.summary_receipt_path)[0]
    assert (
        second_receipt["supersedes_run_summary_attempt_id"]
        == (first_receipt["run_summary_attempt_id"])
    )
    assert second_receipt["run_summary_attempt_history"].split(",") == [
        first_receipt["run_summary_attempt_id"],
        second_receipt["run_summary_attempt_id"],
    ]
    validate_summary_document(fixture)


def test_changed_approval_policy_creates_a_new_summary_attempt(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "changed",
        roles=("candidate_selection",),
    )
    first = run_cli(fixture, execute=True)
    assert first.returncode == 0, first.stderr
    first_json = fixture.summary_json_path.read_bytes()
    first_receipt = read_tsv(fixture.summary_receipt_path)[0]
    rows = read_tsv(fixture.report_table_approvals)
    rows[0]["display_row_limit"] = "1"
    rows[0]["approval_policy_version"] = "synthetic_report_policy_v2"
    write_tsv(
        fixture.report_table_approvals,
        RUN_SUMMARY.REPORT_TABLE_APPROVALS_HEADER,
        rows,
    )

    second = run_cli(fixture, execute=True)

    assert second.returncode == 0, second.stderr
    assert fixture.summary_json_path.read_bytes() != first_json
    document = validate_summary_document(fixture)
    approval = document["approved_report_tables"][0]
    assert approval["display_row_limit"] == 1
    assert approval["approval"]["policy_version"] == ("synthetic_report_policy_v2")
    second_receipt = read_tsv(fixture.summary_receipt_path)[0]
    assert (
        second_receipt["supersedes_run_summary_attempt_id"]
        == (first_receipt["run_summary_attempt_id"])
    )


def test_legacy_empty_approval_summary_can_be_safely_superseded(
    run_summary_fixture: Any,
) -> None:
    first = run_cli(run_summary_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    document = read_json(run_summary_fixture.summary_json_path)
    document["provenance"]["producer_version"] = RUN_SUMMARY.LEGACY_PRODUCER_VERSION
    document["parameters"].pop("report_table_approvals")
    legacy_json = canonical_json_bytes(document)
    run_summary_fixture.summary_json_path.write_bytes(legacy_json)
    receipt = read_tsv(run_summary_fixture.summary_receipt_path)[0]
    receipt["producer_version"] = RUN_SUMMARY.LEGACY_PRODUCER_VERSION
    receipt["run_summary_json_sha256"] = hashlib.sha256(legacy_json).hexdigest()
    receipt["run_summary_json_size_bytes"] = str(len(legacy_json))
    write_tsv(
        run_summary_fixture.summary_receipt_path,
        RUN_SUMMARY.RUN_SUMMARY_RECEIPT_HEADER,
        [receipt],
    )

    replacement = run_cli(run_summary_fixture, execute=True)

    assert replacement.returncode == 0, replacement.stderr
    current = validate_summary_document(run_summary_fixture)
    assert current["provenance"]["producer_version"] == (RUN_SUMMARY.PRODUCER_VERSION)
    assert current["parameters"]["report_table_approvals"] is None
    current_receipt = read_tsv(run_summary_fixture.summary_receipt_path)[0]
    assert current_receipt["producer_version"] == (RUN_SUMMARY.PRODUCER_VERSION)
    assert (
        current_receipt["supersedes_run_summary_attempt_id"]
        == (receipt["run_summary_attempt_id"])
    )


def test_report_table_approval_manifest_and_table_mutation_fail_closed(
    tmp_path: Path,
) -> None:
    manifest_fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "manifest-mutation",
        roles=("candidate_selection",),
    )
    manifest_context = context_for(manifest_fixture)
    manifest_fixture.report_table_approvals.write_bytes(
        manifest_fixture.report_table_approvals.read_bytes() + b"\n"
    )
    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="changed after its immutable snapshot",
    ):
        RUN_SUMMARY.publish_context(manifest_context)
    assert_no_summary_outputs(manifest_fixture)

    table_fixture = FIXTURE.build_approved_science_fixture(
        tmp_path / "table-mutation",
        roles=("candidate_selection",),
    )
    table_context = context_for(table_fixture)
    table_path = Path(table_context.document["approved_report_tables"][0]["path"])
    table_path.write_bytes(table_path.read_bytes() + b"\n")
    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="Approved report table",
    ):
        RUN_SUMMARY.publish_context(table_context)
    assert_no_summary_outputs(table_fixture)


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


def test_unrelated_files_and_decoy_science_are_ignored_and_preserved(
    run_summary_fixture: Any,
) -> None:
    unrelated = run_summary_fixture.output_dir / "unrelated.run_summary.json"
    unrelated_payload = b'{"unrelated":true}\n'
    unrelated.write_bytes(unrelated_payload)
    decoy = run_summary_fixture.output_dir / "decoy.step09c_review_summary.tsv"
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
    assert review["source"]["sha256"] == sha256_file(fixture.science_review_summary)
    assert review["record"]["run_id"] == fixture.run_id
    assert review["record"]["run_contract"] == document["run_contract"]
    assert review["record"]["scientific_state"]["overall_status"] == (science_status)
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
    assert record["review_metadata"]["decision_owner"] == "Scientific Review Team"
    assert record["review_metadata"]["git_commit"] == "local_build"
    assert all(row["reviewer"] == "Jane Doe" for row in record["evidence_records"])
    assert all(
        row["owner"] == "Scientific Review Team" for row in record["evidence_records"]
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


def test_reporting_reader_does_not_reconstruct_step09c_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "no-reconstruction",
        science_status="evidence_incomplete",
    )
    summary_row = read_tsv(fixture.science_review_summary)[0]

    def reject_reconstruction(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("reporting attempted Step 09c reconstruction")

    monkeypatch.setattr(
        FIXTURE.STEP09C_CONTEXT,
        "build_context",
        reject_reconstruction,
    )

    context, tables = SCIENCE_PACKAGE._read_committed_review_package(
        summary_path=fixture.science_review_summary,
        summary_row=summary_row,
        source_root=REPO_ROOT,
    )

    assert context.plan["review_id"] == fixture.step09c_fixture.review_id
    assert tuple(tables) == tuple(
        key for key, _suffix in SCIENCE.review_package.OUTPUT_SUFFIXES
    )


def test_science_normalization_does_not_require_private_step09c_inputs(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "private-inputs-removed",
        science_status="evidence_incomplete",
    )
    artifacts = [
        read_json(Path(row["record_path"]))
        for row in read_tsv(fixture.adapter_fixture.artifacts_path)
    ]
    run_contract = read_json(fixture.adapter_fixture.run_contract)
    arguments = {
        "summary_path": fixture.science_review_summary,
        "artifacts": artifacts,
        "run_id": fixture.run_id,
        "run_contract": run_contract,
        "generated_at": "2020-01-01T00:00:00Z",
        "git_commit": "a" * 40,
    }
    before = SCIENCE.normalize_scientific_review(**arguments)

    private_inputs = (
        fixture.step09c_fixture.review_plan,
        fixture.step09c_fixture.evidence_manifest,
        fixture.step09c_fixture.step08_sites,
    )
    for path in private_inputs:
        path.unlink()

    after = SCIENCE.normalize_scientific_review(**arguments)

    assert all(not path.exists() for path in private_inputs)
    assert canonical_json_bytes(after) == canonical_json_bytes(before)


def test_science_normalization_requires_the_fixed_indexed_package_roster(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "missing-package-record",
        science_status="evidence_incomplete",
    )
    artifacts = [
        read_json(Path(row["record_path"]))
        for row in read_tsv(fixture.adapter_fixture.artifacts_path)
    ]
    artifacts = [
        artifact
        for artifact in artifacts
        if artifact["adapter"] != "step09c_decisions_v1"
    ]

    with pytest.raises(
        SCIENCE.RunSummaryScienceError,
        match="exactly the 13 fixed",
    ):
        SCIENCE.normalize_scientific_review(
            summary_path=fixture.science_review_summary,
            artifacts=artifacts,
            run_id=fixture.run_id,
            run_contract=read_json(fixture.adapter_fixture.run_contract),
            generated_at="2020-01-01T00:00:00Z",
            git_commit="a" * 40,
        )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    (
        ("scope", "exactly the 13 fixed"),
        ("science-state", "mismatched propagated science state"),
    ),
)
def test_science_normalization_rejects_wrong_package_identity_or_state(
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / mutation,
        science_status="evidence_incomplete",
    )
    artifacts = [
        read_json(Path(row["record_path"]))
        for row in read_tsv(fixture.adapter_fixture.artifacts_path)
    ]
    target = next(
        artifact
        for artifact in artifacts
        if artifact["adapter"] == "step09c_decisions_v1"
    )
    if mutation == "scope":
        target["scope"]["scope_id"] = "foreign_review"
    else:
        target["scientific_state"]["review_id"] = "foreign_review"

    with pytest.raises(
        SCIENCE.RunSummaryScienceError,
        match=expected_error,
    ):
        SCIENCE.normalize_scientific_review(
            summary_path=fixture.science_review_summary,
            artifacts=artifacts,
            run_id=fixture.run_id,
            run_contract=read_json(fixture.adapter_fixture.run_contract),
            generated_at="2020-01-01T00:00:00Z",
            git_commit="a" * 40,
        )


def test_committed_public_review_package_mutation_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "public-package-mutation",
        science_status="evidence_incomplete",
    )
    decisions_path = fixture.science_review_summary.with_name(
        f"{fixture.step09c_fixture.review_id}.step09c_decisions.tsv"
    )
    decisions = read_tsv(decisions_path)
    decisions[0]["rationale"] += " mutated"
    write_tsv(decisions_path, read_tsv_header(decisions_path), decisions)

    result = run_cli(fixture)

    assert result.returncode != 0
    assert (
        "Published Step 09c decisions rows differ from reconstruction." in result.stderr
    )
    assert_no_summary_outputs(fixture)


def test_committed_public_review_package_change_during_normalization_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "public-package-in-flight-mutation",
        science_status="evidence_incomplete",
    )
    artifacts = [
        read_json(Path(row["record_path"]))
        for row in read_tsv(fixture.adapter_fixture.artifacts_path)
    ]
    decisions_path = fixture.science_review_summary.with_name(
        f"{fixture.step09c_fixture.review_id}.step09c_decisions.tsv"
    )
    real_normalize = SCIENCE._normalize_limitations
    mutated = False

    def normalize_then_mutate(
        context: Any,
    ) -> list[dict[str, Any]]:
        nonlocal mutated
        normalized = real_normalize(context)
        decisions_path.write_bytes(decisions_path.read_bytes() + b"\n")
        mutated = True
        return normalized

    monkeypatch.setattr(SCIENCE, "_normalize_limitations", normalize_then_mutate)

    with pytest.raises(
        SCIENCE.RunSummaryScienceError,
        match="changed during normalization",
    ):
        SCIENCE.normalize_scientific_review(
            summary_path=fixture.science_review_summary,
            artifacts=artifacts,
            run_id=fixture.run_id,
            run_contract=read_json(fixture.adapter_fixture.run_contract),
            generated_at="2020-01-01T00:00:00Z",
            git_commit="a" * 40,
        )

    assert mutated


@pytest.mark.parametrize("target_kind", ("wrapper", "nested-payload"))
def test_referenced_computational_evidence_mutation_fails_closed(
    tmp_path: Path,
    target_kind: str,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / target_kind,
        science_status="evidence_incomplete",
        computational_scope_bundle=True,
    )
    evidence_index_path = fixture.science_review_summary.with_name(
        f"{fixture.step09c_fixture.review_id}.step09c_evidence_index.tsv"
    )
    computational = next(
        row
        for row in read_tsv(evidence_index_path)
        if row["evidence_category"] == "computational_validation"
        and row["evidence_status"] == "complete"
    )
    wrapper_path = Path(computational["source_path"])
    if target_kind == "wrapper":
        target = wrapper_path
    else:
        payload = next(
            row for row in read_tsv(wrapper_path) if row["evidence_path"] != "NA"
        )
        target = Path(payload["evidence_path"])
    target.write_bytes(target.read_bytes() + b"mutated\n")

    result = run_cli(fixture)

    assert result.returncode != 0
    assert "hash differs" in result.stderr
    assert_no_summary_outputs(fixture)


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
    assert computational["e_computational_not_applicable"]["evidence_date"] is None
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
    original_handlers = {signum: signal.getsignal(signum) for signum in watched}
    real_signal = signal.signal
    call_count = 0

    def fail_second_install(signum: int, handler: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RUN_SUMMARY.adapter.ArtifactIndexError(
                "injected partial signal install failure"
            )
        return real_signal(signum, handler)

    monkeypatch.setattr(signal, "signal", fail_second_install)

    with pytest.raises(
        RUN_SUMMARY.adapter.ArtifactIndexError,
        match="injected partial",
    ):
        RUN_SUMMARY.adapter.install_publication_signal_handlers()

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
        path.name.endswith(".previous") and "run_summary_receipt.tsv" in path.name
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
                run_summary_fixture.adapter_fixture.artifacts_path.read_bytes() + b"\n"
            )
            mutated = True

    monkeypatch.setattr(
        RUN_SUMMARY.adapter,
        "validate_published_transaction",
        validate_then_mutate,
    )
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True)
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="immutable snapshot",
    ):
        RUN_SUMMARY.prepare_context(
            arguments,
            source_checkout=SOURCE_CHECKOUT,
        )

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
    arguments = _parse_run_summary_arguments(
        run_summary_fixture.command_args(execute=True)
    )

    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="immutable snapshot",
    ):
        RUN_SUMMARY.prepare_context(
            arguments,
            source_checkout=SOURCE_CHECKOUT,
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
    context, _tables = SCIENCE_PACKAGE._read_committed_review_package(
        summary_path=fixture.science_review_summary,
        summary_row=summary_row,
        source_root=REPO_ROOT,
    )
    index_rows = read_tsv(fixture.adapter_fixture.artifacts_path)
    artifacts = [read_json(Path(row["record_path"])) for row in index_rows]
    target = next(
        artifact for artifact in artifacts if artifact["adapter"] == "step08_sites_v1"
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

    normalized = SCIENCE_EVIDENCE._normalize_input_artifacts(
        context=context,
        artifacts=artifacts,
        review_id=summary_row["review_id"],
        run_contract=run_contract,
        source_root=REPO_ROOT,
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
    assert context.receipt_row["science_review_summary_path"] == (alternate_summary)
    RUN_SUMMARY.publish_context(context)

    RUN_SUMMARY.validate_published_run_summary(context)
    receipt = read_tsv(fixture.summary_receipt_path)[0]
    document = read_json(fixture.summary_json_path)
    assert receipt["science_review_summary_path"] == alternate_summary
    assert document["scientific_review"]["source"]["path"] == alternate_summary
    assert_no_summary_residue_after_success(fixture)


def test_pending_science_decision_with_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_explicit_science_fixture(
        tmp_path / "pending-decision",
        science_status="evidence_incomplete",
    )
    summary_row = read_tsv(fixture.science_review_summary)[0]
    context, _tables = SCIENCE_PACKAGE._read_committed_review_package(
        summary_path=fixture.science_review_summary,
        summary_row=summary_row,
        source_root=REPO_ROOT,
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
    context, _tables = SCIENCE_PACKAGE._read_committed_review_package(
        summary_path=fixture.science_review_summary,
        summary_row=summary_row,
        source_root=REPO_ROOT,
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
        fixture.adapter_fixture.records_dir / "sample.SYNTH_A.canonical_bai.json"
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

    attempts, superseded = RUN_SUMMARY._build_attempts(artifacts)

    assert [attempt["attempt_id"] for attempt in attempts] == [
        "attempt-a1",
        "attempt-a2",
        "attempt-b1",
    ]
    assert superseded == ["attempt-a1"]

    conflicting = copy.deepcopy(artifacts)
    conflicting[1]["attempts"][1]["finished_at"] = "2000-01-01T00:00:06Z"
    with pytest.raises(
        RUN_SUMMARY.RunSummaryError,
        match="conflicting definitions",
    ):
        RUN_SUMMARY._build_attempts(conflicting)
