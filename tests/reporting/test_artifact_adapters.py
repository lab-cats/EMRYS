"""Focused contract and transaction tests for artifact-adapters-v1."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import importlib
import json
import os
import subprocess
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from emrys import analyses
from emrys.contracts.artifacts import api as ARTIFACT_CONTRACTS
from emrys.contracts.scientific_evidence import step08, step09
from tests.contract_integration.validation_rosters.validation_roster_expectations import (
    assert_exact_check_roster,
)
from tests.reporting.fixtures.artifact_adapters_v1 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_EPOCH = "1700000000"
GIT_ROUTING_VARIABLES = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_WORK_TREE",
    "GIT_FUTURE_ROUTING",
)
EXPECTED_PRODUCER_PATHS = {
    "00a": "src/emrys/stages/star_index/step_00a_build_star_index.sh",
    "00b": "src/emrys/stages/gtf_to_bed12/converter.py",
    "00c": "src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh",
    "01": "src/emrys/stages/star_alignment/step_01_star_align.sh",
    "02": "src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh",
    "02b": "src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh",
    "03": (
        "src/emrys/evidence/rseqc_orientation/"
        "step_03_infer_strandedness_and_orientation.sh"
    ),
    "04": "src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh",
    "05": "src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh",
    "06": "src/emrys/stages/mechanical_orientation/producer.py",
    "07": ("src/emrys/stages/partitioned_cohort_mpileup/producer.py"),
    "08": ("src/emrys/stages/cohort_candidate_preprocessing/producer.py"),
}
VALIDATION_ARTIFACT_STEPS = {
    "ref.star_index.validation": "00a",
    "ref.bed12.validation": "00b",
    "ref.sidecars.validation": "00c",
    "sample.SYNTH_A.star_validation": "01",
    "sample.SYNTH_A.canonical_validation": "02",
    "sample.SYNTH_A.bam_qc_validation": "02b",
    "sample.SYNTH_A.strand_validation": "03",
    "sample.SYNTH_A.markdup_validation": "04",
    "sample.SYNTH_A.split_validation": "05",
    "sample.SYNTH_A.orientation_validation": "06",
    "cohort.synthetic.p1.validation": "07",
    "cohort.synthetic.step08_validation": "08",
    "analysis.synthetic.cmh_validation": "09",
    "analysis.synthetic.context_validation": "10",
}


ARTIFACT_CONTEXT = importlib.import_module("emrys.reporting._artifact_index.context")
ARTIFACT_CORE = importlib.import_module("emrys.reporting._artifact_index.core")
ARTIFACT_BINARY = importlib.import_module(
    "emrys.reporting._artifact_index.binary_readers"
)
ARTIFACT_MODELS = importlib.import_module("emrys.reporting._artifact_index.models")
ARTIFACT_INSPECTION = importlib.import_module(
    "emrys.reporting._artifact_index.inspection"
)
ARTIFACT_PUBLICATION = importlib.import_module(
    "emrys.reporting._artifact_index.publication"
)
ARTIFACT_RECORDS = importlib.import_module("emrys.reporting._artifact_index.records")
ARTIFACT_REGISTRY = importlib.import_module("emrys.reporting._artifact_index.registry")
ARTIFACT_NATIVE = importlib.import_module(
    "emrys.reporting._artifact_index.reconcile_native"
)
SOURCE_AUTHORITY = importlib.import_module("emrys.libraries.source_authority")
ARTIFACT_VALIDATION = importlib.import_module(
    "emrys.reporting._artifact_index.validation"
)


def publication_ops(**overrides: Any) -> Any:
    return dataclasses.replace(
        ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS,
        **overrides,
    )


@pytest.fixture
def artifact_fixture(tmp_path: Path) -> Any:
    return FIXTURE.build_fixture(tmp_path / "fixture")


def artifact_index_arguments(
    fixture: Any,
    *,
    execute: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        source_checkout=REPO_ROOT,
        artifact_source_root=fixture.root,
        run_id=fixture.run_id,
        run_contract=fixture.run_contract,
        inventory=fixture.inventory,
        output_root=fixture.output_root,
        profile=FIXTURE.analysis_profile_v1(),
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
    prepared_arguments = arguments or artifact_index_arguments(
        fixture,
        execute=execute,
    )
    previous_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    try:
        try:
            context = ARTIFACT_CONTEXT.prepare_context(
                prepared_arguments,
                source_checkout=SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT),
                artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
                    root=prepared_arguments.artifact_source_root
                ),
                identity_ops=ARTIFACT_CONTEXT.ArtifactIdentityOps(
                    matching_clean_checkout_head_commit=(
                        lambda **_kwargs: ARTIFACT_CORE.get_git_commit(
                            source_root=REPO_ROOT,
                            sanitize_git_routing=True,
                        )
                    )
                ),
            )
            if prepared_arguments.execute:
                ARTIFACT_PUBLICATION.publish_context(context)
            return DirectTransactionResult(context=context)
        except (
            ARTIFACT_MODELS.ArtifactIndexError,
            SOURCE_AUTHORITY.ArtifactSourceRootError,
            SOURCE_AUTHORITY.SourceCheckoutError,
            ARTIFACT_CONTRACTS.ContractValidationError,
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


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    assert isinstance(value, dict)
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def record_for(fixture: Any, artifact_id: str) -> dict[str, Any]:
    return read_json(fixture.records_dir / f"{artifact_id}.json")


def context_for(fixture: Any) -> Any:
    return ARTIFACT_CONTEXT.prepare_context(
        argparse.Namespace(
            run_id=fixture.run_id,
            run_contract=fixture.run_contract,
            inventory=fixture.inventory,
            output_root=fixture.output_root,
            profile=FIXTURE.analysis_profile_v1(),
            execute=True,
        ),
        source_checkout=SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT),
        artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(root=fixture.root),
        identity_ops=ARTIFACT_CONTEXT.ArtifactIdentityOps(
            matching_clean_checkout_head_commit=(
                lambda **_kwargs: ARTIFACT_CORE.get_git_commit(
                    source_root=REPO_ROOT,
                    sanitize_git_routing=True,
                )
            )
        ),
    )


def owned_snapshot(fixture: Any) -> dict[str, bytes]:
    paths = [fixture.artifacts_path, fixture.receipt_path]
    if fixture.records_dir.is_dir():
        paths.extend(sorted(fixture.records_dir.iterdir()))
    return {
        str(path.relative_to(fixture.output_dir)): path.read_bytes()
        for path in paths
        if path.is_file()
    }


def assert_no_owned_outputs(fixture: Any) -> None:
    assert not fixture.records_dir.exists()
    assert not fixture.artifacts_path.exists()
    assert not fixture.receipt_path.exists()
    assert not fixture.lock_path.exists()
    if fixture.output_dir.exists():
        assert not any(
            path.name.startswith((".artifact-index.", ".artifact-receipt."))
            for path in fixture.output_dir.iterdir()
        )


def schema_validator() -> Draft202012Validator:
    schemas, registry = ARTIFACT_CONTRACTS.load_schema_registry()
    return Draft202012Validator(
        schemas["artifact-record"],
        registry=registry,
        format_checker=FormatChecker(),
    )


def assert_published_records_are_valid(fixture: Any) -> None:
    validator = schema_validator()
    rows_by_id = {row["artifact_id"]: row for row in fixture.inventory_rows}
    for path in sorted(fixture.records_dir.glob("*.json")):
        record = read_json(path)
        errors = list(validator.iter_errors(record))
        assert errors == [], "\n".join(error.message for error in errors)
        ARTIFACT_CONTRACTS.validate_artifact_semantics(record)
        ARTIFACT_CONTRACTS.reconcile_artifact_inventory_row(
            record,
            rows_by_id[record["artifact_id"]],
        )
        assert path.read_bytes() == ARTIFACT_CORE.canonical_json_bytes(record)


def test_fixture_covers_exact_tracked_inventory_and_adapter_registry(
    artifact_fixture: Any,
) -> None:
    rows = artifact_fixture.inventory_rows

    assert len(rows) == 74
    assert [row["artifact_id"] for row in rows] == [
        row["artifact_id"] for row in FIXTURE.read_inventory_template()
    ]
    registry = ARTIFACT_REGISTRY.build_adapter_registry(
        FIXTURE.analysis_module_v1()
    )
    assert {row["adapter"] for row in rows} == set(registry)
    assert len(artifact_fixture.source_paths) == 74
    assert all(path.is_file() for path in artifact_fixture.source_paths.values())
    assert not artifact_fixture.output_root.exists()


def test_migrated_implementation_evidence_uses_final_paths_and_current_bytes() -> None:
    git_commit = "a" * 40

    evidence = ARTIFACT_RECORDS.producer_evidence(
        git_commit,
        analysis_module=analyses.load_analysis_module(
            analyses.BUILTIN_PAIRED_CMH_MODULE_ID
        ),
    )

    assert tuple(evidence) == (*EXPECTED_PRODUCER_PATHS, "09", "10")
    assert ARTIFACT_RECORDS.STEP_PRODUCERS == EXPECTED_PRODUCER_PATHS
    for step_id, expected_path in EXPECTED_PRODUCER_PATHS.items():
        record = evidence[step_id]
        assert record["status"] == "implemented"
        assert record["git_commit"] == git_commit
        implementation_rows = record["evidence"]
        assert len(implementation_rows) == 1
        row = implementation_rows[0]
        assert row["evidence_id"] == f"implementation_{step_id}"
        assert row["role"] == "implementation"
        assert row["path"] == expected_path
        expected_sha256 = hashlib.sha256(
            (REPO_ROOT / expected_path).read_bytes()
        ).hexdigest()
        assert row["sha256"] == expected_sha256
    assert evidence["09"] == evidence["10"]
    assert evidence["09"]["evidence"][0]["evidence_id"] == "implementation_module"


def test_checkout_local_wheel_does_not_claim_the_core_commit() -> None:
    module = analyses.load_analysis_module(analyses.BUILTIN_PAIRED_CMH_MODULE_ID)
    external = dataclasses.replace(
        module,
        provider=dataclasses.replace(
            module.provider,
            package=dataclasses.replace(
                module.provider.package,
                root=(
                    REPO_ROOT
                    / ".venv/lib/python/site-packages/emrys/analyses/paired_cmh_candidate_ranking"
                ),
            ),
        ),
    )

    evidence = ARTIFACT_RECORDS.producer_evidence(
        "a" * 40,
        analysis_module=external,
    )

    assert evidence["09"]["git_commit"] is None
    assert evidence["09"]["evidence"][0]["sha256"] == (
        module.provider.package.sha256
    )


def test_git_commit_routing_sanitization_is_explicit_and_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commit = "a" * 40
    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def observe_run(
        command: list[str],
        **options: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((tuple(command), options))
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{commit}\n",
            stderr="",
        )

    for name in GIT_ROUTING_VARIABLES:
        monkeypatch.setenv(name, f"hostile-{name}")
    monkeypatch.setenv("EMRYS_GIT_ENV_SENTINEL", "retained")
    monkeypatch.setattr(ARTIFACT_CORE.subprocess, "run", observe_run)

    assert ARTIFACT_CORE.get_git_commit() == commit
    assert (
        ARTIFACT_CORE.get_git_commit(
            source_root=tmp_path,
            sanitize_git_routing=True,
        )
        == commit
    )

    expected_call_count = 2
    assert len(calls) == expected_call_count
    default_command, default_options = calls[0]
    assert default_command == ("git", "rev-parse", "--verify", "HEAD")
    assert default_options["cwd"] == ARTIFACT_CONTRACTS.REPO_ROOT
    assert default_options["env"] is None
    sanitized_command, sanitized_options = calls[1]
    assert sanitized_command == default_command
    assert sanitized_options["cwd"] == tmp_path
    assert sanitized_options["check"] is True
    assert sanitized_options["capture_output"] is True
    assert sanitized_options["text"] is True
    environment = sanitized_options["env"]
    assert isinstance(environment, dict)
    assert not any(name.startswith("GIT_") for name in environment)
    assert environment["EMRYS_GIT_ENV_SENTINEL"] == "retained"


def test_prepare_context_keeps_checkout_and_artifact_roots_distinct(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_checkout = SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT)
    artifact_source_root = SOURCE_AUTHORITY.ArtifactSourceRoot(
        root=artifact_fixture.root
    )
    root_calls: Counter[str] = Counter()
    real_get_git_commit = ARTIFACT_CORE.get_git_commit
    real_producer_evidence = ARTIFACT_CONTEXT.producer_evidence
    real_declared_contract_path = ARTIFACT_NATIVE.declared_contract_path
    real_validate_artifact_semantics = ARTIFACT_CONTRACTS.validate_artifact_semantics

    def matching_clean_checkout_head_commit(
        *,
        source_checkout: Any,
        package_root: Path,
    ) -> str:
        assert source_checkout.root == REPO_ROOT
        assert package_root == Path(ARTIFACT_CONTEXT.__file__).resolve().parents[2]
        root_calls["git"] += 1
        return real_get_git_commit(source_root=REPO_ROOT, sanitize_git_routing=True)

    def producer_evidence(
        git_commit: str,
        *,
        source_root: Path,
        analysis_module: Any,
    ) -> dict[str, dict[str, Any]]:
        assert source_root == source_checkout.root
        root_calls["producers"] += 1
        return real_producer_evidence(
            git_commit,
            source_root=source_root,
            analysis_module=analysis_module,
        )

    def declared_contract_path(value: str, *, source_root: Path) -> Path:
        assert source_root == artifact_source_root.root
        root_calls["native_references"] += 1
        return real_declared_contract_path(value, source_root=source_root)

    def validate_artifact_semantics(
        document: dict[str, Any],
        *,
        source_root: Path,
    ) -> None:
        assert source_root == artifact_source_root.root
        root_calls["record_semantics"] += 1
        real_validate_artifact_semantics(document, source_root=source_root)

    monkeypatch.setattr(ARTIFACT_CONTEXT, "producer_evidence", producer_evidence)
    monkeypatch.setattr(
        ARTIFACT_NATIVE,
        "declared_contract_path",
        declared_contract_path,
    )
    monkeypatch.setattr(
        ARTIFACT_CONTRACTS,
        "validate_artifact_semantics",
        validate_artifact_semantics,
    )

    context = ARTIFACT_CONTEXT.prepare_context(
        argparse.Namespace(
            run_id=artifact_fixture.run_id,
            run_contract=artifact_fixture.run_contract,
            inventory=artifact_fixture.inventory,
            output_root=artifact_fixture.output_root,
            profile=FIXTURE.analysis_profile_v1(),
            execute=False,
        ),
        source_checkout=source_checkout,
        artifact_source_root=artifact_source_root,
        identity_ops=ARTIFACT_CONTEXT.ArtifactIdentityOps(
            matching_clean_checkout_head_commit=(matching_clean_checkout_head_commit)
        ),
    )

    assert context.source_checkout == source_checkout
    assert context.artifact_source_root == artifact_source_root
    assert root_calls["git"] == 1
    assert root_calls["producers"] == 1
    assert root_calls["native_references"] > 0
    assert root_calls["record_semantics"] == len(artifact_fixture.inventory_rows)


def test_prepare_context_rejects_unattributable_dirty_checkout(
    artifact_fixture: Any,
) -> None:
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="requires a stable clean source checkout",
    ):
        ARTIFACT_CONTEXT.prepare_context(
            argparse.Namespace(
                run_id=artifact_fixture.run_id,
                run_contract=artifact_fixture.run_contract,
                inventory=artifact_fixture.inventory,
                output_root=artifact_fixture.output_root,
                profile=FIXTURE.analysis_profile_v1(),
                execute=False,
            ),
            source_checkout=SOURCE_AUTHORITY.SourceCheckout(root=REPO_ROOT),
            artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
                root=artifact_fixture.root
            ),
            identity_ops=ARTIFACT_CONTEXT.ArtifactIdentityOps(
                matching_clean_checkout_head_commit=lambda **_kwargs: None
            ),
        )


def test_publication_rechecks_source_identity_before_terminal_receipt(
    artifact_fixture: Any,
) -> None:
    context = context_for(artifact_fixture)
    calls = 0

    def recheck_source_identity(_context: Any) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ARTIFACT_MODELS.ArtifactIndexError("fixture source drift")

    with pytest.raises(ARTIFACT_MODELS.ArtifactIndexError, match="source drift"):
        ARTIFACT_PUBLICATION.publish_context(
            context,
            ops=publication_ops(recheck_source_identity=recheck_source_identity),
        )

    assert calls == 2
    assert not context.receipt_path.exists()


def test_dry_run_validates_all_sources_without_writing(
    artifact_fixture: Any,
) -> None:
    result = run_builder(artifact_fixture)

    assert result.returncode == 0, result.stderr
    assert result.context is not None
    assert len(result.context.records) == 74
    assert not artifact_fixture.output_root.exists()


def test_live_artifact_index_header_owner_controls_serialized_bytes(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ARTIFACT_CONTEXT.ARTIFACT_INDEX_HEADER
    mutated = (original[1], original[0], *original[2:])
    monkeypatch.setattr(ARTIFACT_CONTEXT, "ARTIFACT_INDEX_HEADER", mutated)

    context = context_for(artifact_fixture)

    assert context.index_bytes.splitlines()[0] == "\t".join(mutated).encode()
    assert context.index_bytes != ARTIFACT_RECORDS.tsv_bytes(
        original, context.index_rows
    )


def test_execute_publishes_inventory_ordered_schema_valid_transaction(
    artifact_fixture: Any,
) -> None:
    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    index_rows = read_tsv(artifact_fixture.artifacts_path)
    receipt_rows = read_tsv(artifact_fixture.receipt_path)
    assert len(index_rows) == 74
    assert len(receipt_rows) == 1
    receipt = receipt_rows[0]
    assert [row["artifact_id"] for row in index_rows] == [
        row["artifact_id"] for row in artifact_fixture.inventory_rows
    ]
    assert {row["availability_status"] for row in index_rows} == {"present"}
    assert {row["completion_status"] for row in index_rows} == {"complete"}
    assert receipt["inventory_row_count"] == "74"
    assert receipt["artifact_record_count"] == "74"
    assert receipt["present_artifact_count"] == "74"
    assert receipt["complete_artifact_count"] == "74"
    assert receipt["required_missing_artifact_count"] == "0"
    assert receipt["warning_count"] == "0"
    assert receipt["error_count"] == "0"
    assert receipt["published_output_count"] == "76"
    assert receipt["transaction_state"] == "complete"
    assert receipt["artifacts_index_sha256"] == sha256_file(
        artifact_fixture.artifacts_path
    )
    assert len(list(artifact_fixture.records_dir.glob("*.json"))) == 74

    for row in index_rows:
        record_path = Path(row["record_path"])
        assert record_path == (
            artifact_fixture.records_dir / f"{row['artifact_id']}.json"
        )
        assert row["record_sha256"] == sha256_file(record_path)
        if row["source_path"].endswith(".mpileup.vcf"):
            assert row["source_row_count"] == "1"
        if row["source_path"].endswith(".pdf"):
            assert row["source_row_count"] == ""

    assert_published_records_are_valid(artifact_fixture)
    assert not artifact_fixture.lock_path.exists()
    assert not any(
        path.name.startswith((".artifact-index.", ".artifact-receipt."))
        for path in artifact_fixture.output_dir.iterdir()
    )


def test_fixed_time_retry_keeps_records_and_index_deterministic(
    artifact_fixture: Any,
) -> None:
    first = run_builder(artifact_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    first_record_bytes = {
        path.name: path.read_bytes()
        for path in sorted(artifact_fixture.records_dir.glob("*.json"))
    }
    first_index = artifact_fixture.artifacts_path.read_bytes()
    first_receipt = read_tsv(artifact_fixture.receipt_path)[0]

    second = run_builder(artifact_fixture, execute=True)
    assert second.returncode == 0, second.stderr
    second_record_bytes = {
        path.name: path.read_bytes()
        for path in sorted(artifact_fixture.records_dir.glob("*.json"))
    }
    second_receipt = read_tsv(artifact_fixture.receipt_path)[0]

    assert second_record_bytes == first_record_bytes
    assert artifact_fixture.artifacts_path.read_bytes() == first_index
    assert second_receipt["adapter_attempt_id"] != (first_receipt["adapter_attempt_id"])
    assert (
        second_receipt["supersedes_adapter_attempt_id"]
        == (first_receipt["adapter_attempt_id"])
    )
    assert second_receipt["adapter_attempt_history"].split(",") == [
        first_receipt["adapter_attempt_id"],
        second_receipt["adapter_attempt_id"],
    ]


def test_missing_and_malformed_sources_are_explicit_and_scope_reconciled(
    artifact_fixture: Any,
) -> None:
    artifact_fixture.source_for("sample.SYNTH_A.canonical_bai").unlink()
    artifact_fixture.source_for("sample.SYNTH_A.quickcheck").write_text(
        "not a quickcheck success marker\n",
        encoding="utf-8",
    )

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    missing = record_for(artifact_fixture, "sample.SYNTH_A.canonical_bai")
    missing_sibling = record_for(
        artifact_fixture,
        "sample.SYNTH_A.canonical_bam",
    )
    malformed = record_for(artifact_fixture, "sample.SYNTH_A.quickcheck")
    malformed_sibling = record_for(
        artifact_fixture,
        "sample.SYNTH_A.flagstat",
    )
    assert (missing["availability_status"], missing["completion_status"]) == (
        "missing",
        "incomplete",
    )
    assert missing["source"] is None
    assert [entry["code"] for entry in missing["warnings"]] == [
        "required_source_missing"
    ]
    assert missing_sibling["completion_status"] == "incomplete"
    assert [entry["code"] for entry in missing_sibling["warnings"]] == [
        "scope_transaction_incomplete"
    ]
    assert (
        malformed["availability_status"],
        malformed["completion_status"],
    ) == ("present", "failed")
    assert malformed["source"] is not None
    assert [entry["code"] for entry in malformed["errors"]] == [
        "adapter_validation_failed"
    ]
    assert malformed_sibling["completion_status"] == "incomplete"

    receipt = read_tsv(artifact_fixture.receipt_path)[0]
    assert receipt["present_artifact_count"] == "73"
    assert receipt["missing_artifact_count"] == "1"
    assert receipt["complete_artifact_count"] == "68"
    assert receipt["incomplete_artifact_count"] == "5"
    assert receipt["failed_artifact_count"] == "1"
    assert receipt["required_missing_artifact_count"] == "1"
    assert receipt["warning_count"] == "5"
    assert receipt["error_count"] == "1"
    assert_published_records_are_valid(artifact_fixture)


@pytest.mark.parametrize(
    "artifact_id",
    [
        "ref.star_index.validation",
        "ref.bed12.validation",
        "ref.sidecars.validation",
        "sample.SYNTH_A.star_validation",
        "sample.SYNTH_A.canonical_validation",
        "sample.SYNTH_A.bam_qc_validation",
        "sample.SYNTH_A.strand_validation",
        "sample.SYNTH_A.markdup_validation",
        "sample.SYNTH_A.split_validation",
        "sample.SYNTH_A.orientation_validation",
        "cohort.synthetic.p1.validation",
        "cohort.synthetic.step08_validation",
        "analysis.synthetic.cmh_validation",
    ],
)
def test_validation_adapter_preserves_failed_check_status(
    artifact_fixture: Any,
    artifact_id: str,
) -> None:
    report = artifact_fixture.source_for(artifact_id)
    report.write_text(
        report.read_text(encoding="utf-8").replace(
            "\tpass\tfixture\tfixture\tsynthetic passing validation",
            "\tfail\tmismatch\tfixture\tsynthetic failed validation",
            1,
        ),
        encoding="utf-8",
    )

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(artifact_fixture, artifact_id)
    assert record["availability_status"] == "present"
    assert record["completion_status"] == "failed"
    assert record["state_reason"] == "Validation report contains failed checks."
    assert [entry["code"] for entry in record["errors"]] == ["validation_checks_failed"]


def test_validation_adapter_fixture_uses_exact_independent_rosters(
    artifact_fixture: Any,
) -> None:
    for artifact_id, step_id in VALIDATION_ARTIFACT_STEPS.items():
        assert_exact_check_roster(
            read_tsv(artifact_fixture.source_for(artifact_id)),
            step_id,
        )


@pytest.mark.parametrize("mutation", ("missing", "extra", "duplicate"))
def test_validation_adapter_rejects_roster_shape_mutations(
    artifact_fixture: Any,
    mutation: str,
) -> None:
    artifact_id = "ref.star_index.validation"
    report = artifact_fixture.source_for(artifact_id)
    rows = read_tsv(report)
    if mutation == "missing":
        rows = rows[:-1]
    elif mutation == "extra":
        rows.append({**rows[-1], "check_id": "unexpected_check"})
    else:
        rows[-1]["check_id"] = rows[0]["check_id"]
    FIXTURE.write_tsv(report, tuple(rows[0]), rows)

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(artifact_fixture, artifact_id)
    assert record["completion_status"] == "failed"
    assert [entry["code"] for entry in record["errors"]] == [
        "adapter_validation_failed"
    ]


@pytest.mark.parametrize("mutation", ("reordered", "wrong_unique_id"))
def test_validation_adapter_accepts_roster_identity_defects_as_characterized(
    artifact_fixture: Any,
    mutation: str,
) -> None:
    artifact_id = "ref.star_index.validation"
    report = artifact_fixture.source_for(artifact_id)
    rows = read_tsv(report)
    if mutation == "reordered":
        rows.reverse()
    else:
        rows[0]["check_id"] = "unexpected_check"
    FIXTURE.write_tsv(report, tuple(rows[0]), rows)

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(artifact_fixture, artifact_id)
    assert record["completion_status"] == "complete"
    assert record["errors"] == []


def test_same_run_id_rejects_changed_run_contract_without_touching_outputs(
    artifact_fixture: Any,
) -> None:
    initial = run_builder(artifact_fixture, execute=True)
    assert initial.returncode == 0, initial.stderr
    before = owned_snapshot(artifact_fixture)

    contract = read_json(artifact_fixture.run_contract)
    contract["primary_analysis_policy_sha256"] = "5" * 64
    components = {
        field: value
        for field, value in contract.items()
        if field != "run_contract_sha256"
    }
    contract["run_contract_sha256"] = FIXTURE.canonical_run_contract_sha256(components)
    ordered_contract = {
        field: contract[field] for field in ARTIFACT_MODELS.RUN_CONTRACT_FIELDS
    }
    artifact_fixture.run_contract.write_text(
        json.dumps(ordered_contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    collision = run_builder(artifact_fixture, execute=True)

    assert collision.returncode != 0
    assert "different immutable run contract" in collision.stderr
    assert owned_snapshot(artifact_fixture) == before
    assert not artifact_fixture.lock_path.exists()


def test_undeclared_source_and_unrelated_run_outputs_are_ignored_and_preserved(
    artifact_fixture: Any,
) -> None:
    undeclared = (
        artifact_fixture.source_root
        / "results"
        / "mpileup"
        / "synthetic_cohort"
        / "p1"
        / "undeclared.FWD_like.mpileup.vcf"
    )
    undeclared.write_text(
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTH_A\n",
        encoding="utf-8",
    )
    artifact_fixture.output_dir.mkdir(parents=True)
    unrelated = (
        artifact_fixture.output_dir / f"{artifact_fixture.run_id}.run_summary.json"
    )
    unrelated_payload = b'{"owned_by":"future-run-summary"}\n'
    unrelated.write_bytes(unrelated_payload)

    first = run_builder(artifact_fixture, execute=True)
    second = run_builder(artifact_fixture, execute=True)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert unrelated.read_bytes() == unrelated_payload
    index_rows = read_tsv(artifact_fixture.artifacts_path)
    assert len(index_rows) == 74
    assert str(undeclared) not in {row["source_path"] for row in index_rows}
    assert not any(
        path.name.startswith("undeclared")
        for path in artifact_fixture.records_dir.iterdir()
    )


def test_foreign_lock_and_partial_prior_transaction_are_preserved(
    tmp_path: Path,
) -> None:
    locked = FIXTURE.build_fixture(tmp_path / "locked")
    locked.output_dir.mkdir(parents=True)
    lock_payload = b"foreign lock\n"
    locked.lock_path.write_bytes(lock_payload)

    locked_result = run_builder(locked, execute=True)

    assert locked_result.returncode != 0
    assert "locked" in locked_result.stderr
    assert locked.lock_path.read_bytes() == lock_payload
    assert not locked.records_dir.exists()
    assert not locked.artifacts_path.exists()
    assert not locked.receipt_path.exists()

    partial = FIXTURE.build_fixture(tmp_path / "partial")
    partial.output_dir.mkdir(parents=True)
    partial_payload = b"partial prior index\n"
    partial.artifacts_path.write_bytes(partial_payload)

    partial_result = run_builder(partial, execute=True)

    assert partial_result.returncode != 0
    assert "output set is incomplete" in partial_result.stderr
    assert partial.artifacts_path.read_bytes() == partial_payload
    assert not partial.records_dir.exists()
    assert not partial.receipt_path.exists()
    assert not partial.lock_path.exists()


def test_first_publication_rename_failure_rolls_back_owned_outputs(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    context = context_for(artifact_fixture)
    real_replace = ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS.replace

    def fail_index_publication(source: Any, destination: Any) -> None:
        if (
            Path(destination) == context.artifacts_path
            and ".tmp.tsv" in Path(source).name
        ):
            raise OSError("injected index publication failure")
        real_replace(source, destination)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="injected index publication failure",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            context,
            ops=publication_ops(replace=fail_index_publication),
        )

    assert_no_owned_outputs(artifact_fixture)


def test_replacement_rename_failure_restores_prior_transaction_byte_for_byte(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    before = owned_snapshot(artifact_fixture)
    replacement = context_for(artifact_fixture)
    real_replace = ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS.replace
    failed = False

    def fail_replacement_index(source: Any, destination: Any) -> None:
        nonlocal failed
        if (
            not failed
            and Path(destination) == replacement.artifacts_path
            and ".tmp.tsv" in Path(source).name
        ):
            failed = True
            raise OSError("injected replacement index failure")
        real_replace(source, destination)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="injected replacement index failure",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            replacement,
            ops=publication_ops(replace=fail_replacement_index),
        )

    assert failed
    assert owned_snapshot(artifact_fixture) == before
    assert not artifact_fixture.lock_path.exists()
    assert not any(
        path.name.startswith((".artifact-index.", ".artifact-receipt."))
        for path in artifact_fixture.output_dir.iterdir()
    )


def test_source_mutation_between_inspection_and_publication_aborts_cleanly(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    context = context_for(artifact_fixture)
    artifact_fixture.source_for("sample.SYNTH_A.flagstat").write_text(
        "mutated after inspection\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="changed after initial inspection",
    ):
        ARTIFACT_PUBLICATION.publish_context(context)

    assert_no_owned_outputs(artifact_fixture)


def test_recheck_inputs_uses_live_context_stat_owner(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(artifact_fixture)
    target = artifact_fixture.source_for("sample.SYNTH_A.star_log").resolve()
    real_stat_source = ARTIFACT_CONTEXT.stat_source
    reached_target = False

    def fail_target_recheck(path: Path, *, hash_content: bool = True) -> Any:
        nonlocal reached_target
        if path.resolve() == target:
            reached_target = True
            raise ARTIFACT_MODELS.ArtifactIndexError(
                "injected live stat-source failure"
            )
        return real_stat_source(path, hash_content=hash_content)

    monkeypatch.setattr(ARTIFACT_CONTEXT, "stat_source", fail_target_recheck)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="injected live stat-source failure",
    ):
        ARTIFACT_CONTEXT.recheck_inputs(context)

    assert reached_target


def test_run_contract_is_order_independent_but_strict_json(
    artifact_fixture: Any,
) -> None:
    contract = read_json(artifact_fixture.run_contract)
    artifact_fixture.run_contract.write_text(
        json.dumps(
            dict(reversed(list(contract.items()))),
            ensure_ascii=False,
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )
    reordered = run_builder(artifact_fixture)
    assert reordered.returncode == 0, reordered.stderr

    fields = list(contract.items())
    duplicate_payload = (
        "{\n"
        + ",\n".join(
            [
                f'  "run_contract_sha256": '
                f"{json.dumps(contract['run_contract_sha256'])}",
                *[f"  {json.dumps(key)}: {json.dumps(value)}" for key, value in fields],
            ]
        )
        + "\n}\n"
    )
    artifact_fixture.run_contract.write_text(
        duplicate_payload,
        encoding="utf-8",
    )
    duplicate = run_builder(artifact_fixture)
    assert duplicate.returncode != 0
    assert "Duplicate JSON object key" in duplicate.stderr

    nonstandard = json.dumps(contract).replace(
        json.dumps(FIXTURE.PRIMARY_ANALYSIS_ID),
        "NaN",
    )
    artifact_fixture.run_contract.write_text(
        nonstandard + "\n",
        encoding="utf-8",
    )
    nan_result = run_builder(artifact_fixture)
    assert nan_result.returncode != 0
    assert "Non-standard JSON numeric constant" in nan_result.stderr
    assert not artifact_fixture.output_root.exists()


def test_semantically_identical_moved_run_contract_can_retry(
    artifact_fixture: Any,
) -> None:
    first = run_builder(artifact_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    first_receipt = read_tsv(artifact_fixture.receipt_path)[0]
    moved_contract = artifact_fixture.root / "moved_contract.json"
    contract = read_json(artifact_fixture.run_contract)
    moved_contract.write_text(
        json.dumps(
            dict(reversed(list(contract.items()))),
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    arguments = artifact_index_arguments(artifact_fixture, execute=True)
    arguments.run_contract = moved_contract

    second = run_builder(
        artifact_fixture,
        arguments=arguments,
    )

    assert second.returncode == 0, second.stderr
    receipt = read_tsv(artifact_fixture.receipt_path)[0]
    assert receipt["run_contract_path"] == str(moved_contract)
    assert receipt["run_contract_file_sha256"] == sha256_file(moved_contract)
    assert (
        receipt["supersedes_adapter_attempt_id"]
        == (first_receipt["adapter_attempt_id"])
    )


def test_unknown_adapter_fails_before_any_output(
    artifact_fixture: Any,
) -> None:
    rows = read_tsv(artifact_fixture.inventory)
    rows[0]["adapter"] = "unknown_adapter_v1"
    FIXTURE.write_tsv(
        artifact_fixture.inventory,
        ARTIFACT_CONTRACTS.INVENTORY_HEADER,
        rows,
    )

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode != 0
    assert "unsupported adapter" in result.stderr
    assert not artifact_fixture.output_root.exists()


def test_output_directory_and_owned_component_symlinks_are_rejected(
    tmp_path: Path,
) -> None:
    escaped = FIXTURE.build_fixture(tmp_path / "escaped")
    escaped.output_root.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    escaped.output_dir.symlink_to(external, target_is_directory=True)

    escaped_result = run_builder(escaped, execute=True)

    assert escaped_result.returncode != 0
    assert "must not be a symlink" in escaped_result.stderr
    assert list(external.iterdir()) == []

    owned = FIXTURE.build_fixture(tmp_path / "owned")
    owned.output_dir.mkdir(parents=True)
    owned.receipt_path.write_text("placeholder\n", encoding="utf-8")
    owned.artifacts_path.write_text("placeholder\n", encoding="utf-8")
    records_target = tmp_path / "records_target"
    records_target.mkdir()
    owned.records_dir.symlink_to(records_target, target_is_directory=True)

    owned_result = run_builder(owned, execute=True)

    assert owned_result.returncode != 0
    assert "records path is not a regular owned directory" in owned_result.stderr
    assert list(records_target.iterdir()) == []


@pytest.mark.parametrize("component", ("products", "artifact-summary"))
def test_publication_rejects_symlinked_output_ancestor(
    artifact_fixture: Any,
    tmp_path: Path,
    component: str,
) -> None:
    products = artifact_fixture.root / "products"
    output_root = products / "artifact-summary"
    context = context_for(dataclasses.replace(artifact_fixture, output_root=output_root))
    products.mkdir()
    external = tmp_path / f"external-{component}"
    external.mkdir()
    target = products if component == "products" else output_root
    if target == products:
        target.rmdir()
    target.symlink_to(external, target_is_directory=True)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="output boundary is unsafe",
    ):
        ARTIFACT_PUBLICATION.publish_context(context)

    assert list(external.iterdir()) == []


def test_publication_directory_creation_does_not_follow_swapped_ancestor(
    artifact_fixture: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    products = artifact_fixture.root / "products"
    output_root = products / "artifact-summary"
    context = context_for(dataclasses.replace(artifact_fixture, output_root=output_root))
    products.mkdir()
    displaced = artifact_fixture.root / "displaced-products"
    external = tmp_path / "external-race-target"
    external_output = external / "artifact-summary" / artifact_fixture.run_id
    external_output.mkdir(parents=True)
    real_mkdir = os.mkdir
    swapped = False

    def swap_before_create(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> None:
        nonlocal swapped
        if path == "artifact-summary" and not swapped:
            products.rename(displaced)
            products.symlink_to(external, target_is_directory=True)
            swapped = True
        real_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(ARTIFACT_PUBLICATION.os, "mkdir", swap_before_create)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="output boundary changed during admission",
    ):
        ARTIFACT_PUBLICATION.publish_context(context)

    assert swapped
    assert list(external_output.iterdir()) == []


def test_declared_source_symlink_retarget_is_detected(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    source = artifact_fixture.source_for("sample.SYNTH_A.star_log")
    payload = source.read_bytes()
    target_one = artifact_fixture.root / "target_one.log"
    target_two = artifact_fixture.root / "target_two.log"
    target_one.write_bytes(payload)
    target_two.write_bytes(payload)
    source.unlink()
    source.symlink_to(target_one)
    context = context_for(artifact_fixture)
    source.unlink()
    source.symlink_to(target_two)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="changed after initial inspection",
    ):
        ARTIFACT_PUBLICATION.publish_context(context)

    assert_no_owned_outputs(artifact_fixture)


def test_native_receipt_mismatch_is_published_as_explicit_failure(
    artifact_fixture: Any,
) -> None:
    receipt_path = artifact_fixture.source_for("cohort.synthetic.p1.receipt")
    rows = read_tsv(receipt_path)
    rows[0]["vcf_record_count"] = "2"
    FIXTURE.write_tsv(receipt_path, ARTIFACT_MODELS.STEP07_RECEIPT_HEADER, rows)

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    receipt = record_for(artifact_fixture, "cohort.synthetic.p1.receipt")
    fwd = record_for(artifact_fixture, "cohort.synthetic.p1.fwd_vcf")
    rev = record_for(artifact_fixture, "cohort.synthetic.p1.rev_vcf")
    assert receipt["completion_status"] == "failed"
    assert [entry["code"] for entry in receipt["errors"]] == [
        "native_transaction_inconsistent"
    ]
    assert "record count disagrees" in receipt["errors"][0]["message"]
    assert fwd["completion_status"] == "incomplete"
    assert rev["completion_status"] == "incomplete"


def test_dangling_declared_symlink_is_externally_unavailable(
    artifact_fixture: Any,
) -> None:
    source = artifact_fixture.source_for("sample.SYNTH_A.star_log")
    source.unlink()
    source.symlink_to(artifact_fixture.root / "absent.log")

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(artifact_fixture, "sample.SYNTH_A.star_log")
    assert record["availability_status"] == "externally_unavailable"
    assert record["completion_status"] == "incomplete"
    assert record["source"] is None
    assert [entry["code"] for entry in record["warnings"]] == [
        "source_externally_unavailable"
    ]


def test_tampered_receipt_and_extra_record_entry_block_retry(
    artifact_fixture: Any,
) -> None:
    published = run_builder(artifact_fixture, execute=True)
    assert published.returncode == 0, published.stderr
    original_receipt = artifact_fixture.receipt_path.read_bytes()
    rows = read_tsv(artifact_fixture.receipt_path)
    rows[0]["complete_artifact_count"] = "0"
    FIXTURE.write_tsv(
        artifact_fixture.receipt_path,
        ARTIFACT_MODELS.ARTIFACT_RECEIPT_HEADER,
        rows,
    )

    tampered = run_builder(artifact_fixture)

    assert tampered.returncode != 0
    assert "receipt rollup is invalid" in tampered.stderr
    artifact_fixture.receipt_path.write_bytes(original_receipt)
    record_path = artifact_fixture.records_dir / "sample.SYNTH_A.star_log.json"
    original_record = record_path.read_bytes()
    record_path.write_text("{}\n", encoding="utf-8")

    bad_record = run_builder(artifact_fixture)

    assert bad_record.returncode != 0
    assert "record hash is invalid" in bad_record.stderr
    record_path.write_bytes(original_record)
    unexpected = artifact_fixture.records_dir / "unexpected"
    unexpected.mkdir()

    extra_entry = run_builder(artifact_fixture)

    assert extra_entry.returncode != 0
    assert "missing or unexpected files" in extra_entry.stderr
    assert unexpected.is_dir()
    unexpected.rmdir()
    target = artifact_fixture.root / "record_target.json"
    target.write_bytes(original_record)
    record_path.unlink()
    record_path.symlink_to(target)

    symlinked_record = run_builder(artifact_fixture)

    assert symlinked_record.returncode != 0
    assert "non-regular owned entry" in symlinked_record.stderr


def test_stale_predecessor_context_cannot_overwrite_newer_retry(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    stale = context_for(artifact_fixture)
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    before = owned_snapshot(artifact_fixture)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="predecessor changed",
    ):
        ARTIFACT_PUBLICATION.publish_context(stale)

    assert owned_snapshot(artifact_fixture) == before
    assert not artifact_fixture.lock_path.exists()


def test_prepare_context_uses_live_predecessor_validation_owner(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    real_validate = ARTIFACT_VALIDATION.validate_published_transaction
    reached_predecessor = False

    def fail_predecessor_validation(**kwargs: Any) -> None:
        nonlocal reached_predecessor
        assert kwargs["source_root"] == artifact_fixture.root
        if not kwargs["require_current_source_locations"]:
            reached_predecessor = True
            raise ARTIFACT_MODELS.ArtifactIndexError(
                "injected live predecessor-validation failure"
            )
        real_validate(**kwargs)

    monkeypatch.setattr(
        ARTIFACT_VALIDATION,
        "validate_published_transaction",
        fail_predecessor_validation,
    )

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="injected live predecessor-validation failure",
    ):
        context_for(artifact_fixture)

    assert reached_predecessor


def test_post_publication_source_mutation_rolls_back(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    context = context_for(artifact_fixture)
    real_validate = ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS.validate_published_transaction
    source = artifact_fixture.source_for("sample.SYNTH_A.star_log")
    mutated = False

    def mutate_after_validation(**kwargs: Any) -> None:
        nonlocal mutated
        assert kwargs["source_root"] == context.artifact_source_root.root
        real_validate(**kwargs)
        if kwargs["require_current_source_locations"] and not mutated:
            source.write_text("mutated after publication\n", encoding="utf-8")
            mutated = True

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="changed after initial inspection",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            context,
            ops=publication_ops(validate_published_transaction=mutate_after_validation),
        )

    assert mutated
    assert_no_owned_outputs(artifact_fixture)


def test_post_commit_backup_cleanup_failure_preserves_new_transaction(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    prior_receipt = read_tsv(artifact_fixture.receipt_path)[0]
    replacement = context_for(artifact_fixture)
    real_remove_owned = (
        ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS.remove_owned
    )
    injected = False

    def fail_backup_index_cleanup(path: Path) -> None:
        nonlocal injected
        if (
            not injected
            and path.name.startswith(".artifact-index.")
            and path.name.endswith(".previous.tsv")
        ):
            injected = True
            raise OSError("injected backup cleanup failure")
        real_remove_owned(path)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="cleanup failed",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            replacement,
            ops=publication_ops(remove_owned=fail_backup_index_cleanup),
        )

    assert injected
    current_receipt = read_tsv(artifact_fixture.receipt_path)[0]
    assert current_receipt["adapter_attempt_id"] == replacement.attempt_id
    assert (
        current_receipt["supersedes_adapter_attempt_id"]
        == (prior_receipt["adapter_attempt_id"])
    )
    assert artifact_fixture.records_dir.is_dir()
    assert artifact_fixture.artifacts_path.is_file()
    assert artifact_fixture.receipt_path.is_file()
    assert artifact_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in artifact_fixture.output_dir.iterdir()
    )


def test_native_metrics_and_artifact_state_are_conservative(
    artifact_fixture: Any,
) -> None:
    result = run_builder(artifact_fixture, execute=True)
    assert result.returncode == 0, result.stderr

    quickcheck = record_for(artifact_fixture, "sample.SYNTH_A.quickcheck")
    assert {
        (metric["metric_id"], metric["status"]) for metric in quickcheck["metrics"]
    } >= {("quickcheck_pass", "pass")}
    flagstat = record_for(artifact_fixture, "sample.SYNTH_A.flagstat")
    flagstat_metrics = {
        metric["metric_id"]: metric["value"] for metric in flagstat["metrics"]
    }
    assert flagstat_metrics["total_reads"] == 10
    assert flagstat_metrics["mapped_reads"] == 8
    genome_parameters = record_for(
        artifact_fixture,
        "ref.star_index.genome_parameters",
    )
    assert genome_parameters["source"]["media_type"] == "text/plain"
    assert any(
        metric["metric_id"] == "sjdbOverhang" and metric["value"] == 99
        for metric in genome_parameters["metrics"]
    )
    genome = record_for(artifact_fixture, "ref.star_index.genome")
    assert genome["source"]["media_type"] == "application/octet-stream"
    assert "scientific_state" not in genome
    assert genome["runtime_validation"]["status"] == "not_run"
    assert genome["cluster_validation"]["proof_status"] == "not_run"
    assert genome["attempts"] == []
    assert genome["selected_attempt_id"] is None


def test_star_final_log_preserves_infinite_mapping_speed_as_string(
    artifact_fixture: Any,
) -> None:
    artifact_fixture.source_for("sample.SYNTH_A.star_log_final").write_text(
        "Mapping speed, Million of reads per hour | inf\n"
        "Number of input reads | 100\n"
        "Uniquely mapped reads % | 95.00%\n",
        encoding="utf-8",
    )

    context = context_for(artifact_fixture)
    record = next(
        record
        for record in context.records
        if record["artifact_id"] == "sample.SYNTH_A.star_log_final"
    )
    metrics = {metric["metric_id"]: metric for metric in record["metrics"]}
    mapping_speed = metrics["mapping_speed__million_of_reads_per_hour"]
    assert mapping_speed["value"] == "Inf"
    assert mapping_speed["status"] == "not_assessed"
    assert metrics["number_of_input_reads"]["value"] == 100.0
    assert metrics["uniquely_mapped_reads"]["value"] == 95.0


@pytest.mark.parametrize("token", ["-inf", "nan", "1e999"])
def test_star_final_log_rejects_unapproved_nonfinite_metrics(
    artifact_fixture: Any,
    token: str,
) -> None:
    artifact_fixture.source_for("sample.SYNTH_A.star_log_final").write_text(
        f"Mapping speed, Million of reads per hour | {token}\n"
        "Number of input reads | 100\n",
        encoding="utf-8",
    )

    context = context_for(artifact_fixture)
    record = next(
        record
        for record in context.records
        if record["artifact_id"] == "sample.SYNTH_A.star_log_final"
    )
    assert record["completion_status"] == "failed"
    assert record["state_reason"] == "Present source failed its registered adapter."
    assert [error["code"] for error in record["errors"]] == [
        "adapter_validation_failed"
    ]
    assert "is non-finite" in record["errors"][0]["message"]


def test_metric_projection_rejects_residual_nonfinite_values() -> None:
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="Native metric 'unexpected' is non-finite",
    ):
        ARTIFACT_INSPECTION.build_metrics(
            {"artifact_id": "sample.SYNTH_A.unexpected"},
            None,
            {"unexpected": float("inf")},
        )


def test_bgzf_eof_block_matches_the_independent_canonical_literal() -> None:
    expected = bytes.fromhex("1f8b08040000000000ff0600424302001b0003000000000000000000")

    assert len(expected) == 28
    assert ARTIFACT_BINARY.BGZF_EOF_BLOCK == expected
    assert FIXTURE.CANONICAL_BGZF_EOF_BLOCK == expected


def test_all_missing_sources_publish_complete_index_transaction(
    artifact_fixture: Any,
) -> None:
    for path in artifact_fixture.source_paths.values():
        path.unlink()

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    receipt = read_tsv(artifact_fixture.receipt_path)[0]
    assert receipt["missing_artifact_count"] == "74"
    assert receipt["incomplete_artifact_count"] == "74"
    assert receipt["required_missing_artifact_count"] == "74"
    assert receipt["transaction_state"] == "complete"


def test_incomplete_replacement_rollback_retains_lock_and_recovery(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    replacement = context_for(artifact_fixture)
    real_replace = ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS.replace
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
            and destination_path == replacement.artifacts_path
            and ".tmp.tsv" in source_path.name
        ):
            publication_failed = True
            raise OSError("injected new-index publication failure")
        if (
            not restoration_failed
            and destination_path == replacement.records_dir
            and source_path.name.endswith(".previous.records")
        ):
            restoration_failed = True
            raise OSError("injected prior-record restoration failure")
        real_replace(source, destination)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="rollback was incomplete",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            replacement,
            ops=publication_ops(replace=fail_publication_and_restoration),
        )

    assert publication_failed
    assert restoration_failed
    assert artifact_fixture.lock_path.is_file()
    assert not artifact_fixture.receipt_path.exists()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in artifact_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".previous.tsv")
        and path.name.startswith(".artifact-receipt.")
        for path in artifact_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".previous.records")
        for path in artifact_fixture.output_dir.iterdir()
    )
    assert not artifact_fixture.records_dir.exists()


def test_failed_restored_transaction_validation_requarantines_receipt(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    replacement = context_for(artifact_fixture)
    real_validate = ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS.validate_published_transaction
    prior_validation_count = 0

    def fail_new_and_restored_validation(**kwargs: Any) -> None:
        nonlocal prior_validation_count
        assert kwargs["source_root"] == replacement.artifact_source_root.root
        if kwargs["require_current_source_locations"]:
            raise ARTIFACT_MODELS.ArtifactIndexError(
                "injected new-transaction validation failure"
            )
        prior_validation_count += 1
        if prior_validation_count == 2:
            raise ARTIFACT_MODELS.ArtifactIndexError(
                "injected restored-transaction validation failure"
            )
        real_validate(**kwargs)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="rollback was incomplete",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            replacement,
            ops=publication_ops(
                validate_published_transaction=fail_new_and_restored_validation
            ),
        )

    assert prior_validation_count == 2
    assert not artifact_fixture.receipt_path.exists()
    assert artifact_fixture.lock_path.is_file()
    assert any(
        path.name.startswith(".artifact-receipt.")
        and path.name.endswith(".previous.tsv")
        for path in artifact_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in artifact_fixture.output_dir.iterdir()
    )


@pytest.mark.parametrize(
    ("step_id", "marker_artifact", "sibling_artifact"),
    [
        (
            "00c",
            "ref.dict",
            "ref.fasta",
        ),
        (
            "06",
            "sample.SYNTH_A.orientation_counts",
            "sample.SYNTH_A.fwd_bam",
        ),
        (
            "08",
            "cohort.synthetic.step08_inputs",
            "cohort.synthetic.step08_sites",
        ),
        (
            "09",
            "analysis.synthetic.cmh_summary",
            "analysis.synthetic.cmh_all_sites",
        ),
        (
            "10",
            "analysis.synthetic.context_receipt",
            "analysis.synthetic.candidate_context",
        ),
    ],
)
def test_native_transaction_reconciliation_rejects_internal_mismatch(
    artifact_fixture: Any,
    step_id: str,
    marker_artifact: str,
    sibling_artifact: str,
) -> None:
    if step_id == "00c":
        artifact_fixture.source_for("ref.fai").write_text(
            "1\t11\t3\t10\t11\n",
            encoding="utf-8",
        )
    elif step_id == "06":
        path = artifact_fixture.source_for("sample.SYNTH_A.orientation_counts")
        rows = read_tsv(path)
        rows[0]["fwd_like_records"] = "6"
        FIXTURE.write_tsv(path, ARTIFACT_MODELS.STEP06_COUNTS_HEADER, rows)
    elif step_id == "08":
        path = artifact_fixture.source_for("cohort.synthetic.step08_summary")
        rows = read_tsv(path)
        rows[0]["published_candidate_count"] = "5"
        FIXTURE.write_tsv(
            path,
            step08.STEP08_SUMMARY_HEADER,
            rows,
        )
    elif step_id == "09":
        path = artifact_fixture.source_for("analysis.synthetic.mutation_spectrum_tsv")
        rows = read_tsv(path)
        rows[0]["candidate_count"] = "5"
        FIXTURE.write_tsv(
            path,
            step09.STEP09_MUTATION_HEADER,
            rows,
        )
    elif step_id == "10":
        path = artifact_fixture.source_for("analysis.synthetic.candidate_context")
        rows = read_tsv(path)
        sequence = rows[0]["oriented_sequence"]
        rows[0]["oriented_sequence"] = ("C" if sequence[0] != "C" else "A") + sequence[
            1:
        ]
        FIXTURE.write_tsv(path, tuple(rows[0]), rows)
    else:
        raise AssertionError(f"Unhandled native transaction step: {step_id}")

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    marker = record_for(artifact_fixture, marker_artifact)
    sibling = record_for(artifact_fixture, sibling_artifact)
    assert marker["completion_status"] == "failed"
    assert [entry["code"] for entry in marker["errors"]] == [
        "native_transaction_inconsistent"
    ]
    assert sibling["completion_status"] == "incomplete"


@pytest.mark.parametrize(
    ("input_name", "replacement"),
    [
        ("run_contract", False),
        ("inventory", False),
        ("run_contract", True),
        ("inventory", True),
    ],
)
def test_contract_and_inventory_mutation_after_context_is_rejected(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
    input_name: str,
    replacement: bool,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    before: dict[str, bytes] | None = None
    if replacement:
        ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
        before = owned_snapshot(artifact_fixture)
    context = context_for(artifact_fixture)
    path = (
        artifact_fixture.run_contract
        if input_name == "run_contract"
        else artifact_fixture.inventory
    )
    path.write_bytes(path.read_bytes() + b"\n")

    expected = (
        "Run-contract file changed"
        if input_name == "run_contract"
        else "Inventory changed"
    )
    with pytest.raises(ARTIFACT_MODELS.ArtifactIndexError, match=expected):
        ARTIFACT_PUBLICATION.publish_context(context)

    if replacement:
        assert owned_snapshot(artifact_fixture) == before
        assert not artifact_fixture.lock_path.exists()
    else:
        assert_no_owned_outputs(artifact_fixture)


def test_inventory_revision_creates_new_attempt_without_changing_run_identity(
    artifact_fixture: Any,
) -> None:
    first = run_builder(artifact_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    first_receipt = read_tsv(artifact_fixture.receipt_path)[0]
    rows = list(artifact_fixture.inventory_rows)
    first_scope = (
        rows[0]["step_id"],
        rows[0]["scope_type"],
        rows[0]["scope_id"],
    )
    first_block = [
        row
        for row in rows
        if (row["step_id"], row["scope_type"], row["scope_id"]) == first_scope
    ]
    revised = [row for row in rows if row not in first_block] + first_block
    FIXTURE.write_tsv(
        artifact_fixture.inventory,
        ARTIFACT_CONTRACTS.INVENTORY_HEADER,
        revised,
    )

    second = run_builder(artifact_fixture, execute=True)

    assert second.returncode == 0, second.stderr
    second_receipt = read_tsv(artifact_fixture.receipt_path)[0]
    assert second_receipt["run_id"] == first_receipt["run_id"]
    assert (
        second_receipt["run_contract_sha256"] == (first_receipt["run_contract_sha256"])
    )
    assert second_receipt["inventory_sha256"] != (first_receipt["inventory_sha256"])
    assert (
        second_receipt["supersedes_adapter_attempt_id"]
        == (first_receipt["adapter_attempt_id"])
    )
    assert [
        row["artifact_id"] for row in read_tsv(artifact_fixture.artifacts_path)
    ] == [row["artifact_id"] for row in revised]


def test_native_dependency_order_is_independent_of_inventory_scope_order(
    artifact_fixture: Any,
) -> None:
    rows = list(artifact_fixture.inventory_rows)
    step08_rows = [row for row in rows if row["step_id"] == "08"]
    without_step08 = [row for row in rows if row["step_id"] != "08"]
    first_step07 = next(
        index for index, row in enumerate(without_step08) if row["step_id"] == "07"
    )
    reordered = (
        without_step08[:first_step07] + step08_rows + without_step08[first_step07:]
    )
    FIXTURE.write_tsv(
        artifact_fixture.inventory,
        ARTIFACT_CONTRACTS.INVENTORY_HEADER,
        reordered,
    )
    receipt_path = artifact_fixture.source_for("cohort.synthetic.p1.receipt")
    receipt_rows = read_tsv(receipt_path)
    receipt_rows[0]["sample_count"] = "2"
    FIXTURE.write_tsv(
        receipt_path,
        ARTIFACT_MODELS.STEP07_RECEIPT_HEADER,
        receipt_rows,
    )

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    step07 = record_for(
        artifact_fixture,
        "cohort.synthetic.p1.receipt",
    )
    step08 = record_for(
        artifact_fixture,
        "cohort.synthetic.step08_inputs",
    )
    assert step07["completion_status"] == "failed"
    assert step08["completion_status"] == "failed"


def test_step07_requires_all_declared_mpileup_annotation_definitions(
    artifact_fixture: Any,
) -> None:
    vcf = artifact_fixture.source_for("cohort.synthetic.p1.fwd_vcf")
    lines = vcf.read_text(encoding="utf-8").splitlines()
    vcf.write_text(
        "\n".join(line for line in lines if not line.startswith("##FORMAT=<ID=SP,"))
        + "\n",
        encoding="utf-8",
    )

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    receipt = record_for(
        artifact_fixture,
        "cohort.synthetic.p1.receipt",
    )
    assert receipt["completion_status"] == "failed"
    assert [entry["code"] for entry in receipt["errors"]] == [
        "native_transaction_inconsistent"
    ]


@pytest.mark.parametrize(
    ("artifact_id", "payload"),
    [
        ("sample.SYNTH_A.star_bam", b"\x1f\x8b\x08\x04"),
        ("sample.SYNTH_A.canonical_bai", b"BAI\x01\x01\x00\x00\x00"),
        (
            "analysis.synthetic.mutation_spectrum_pdf",
            b"%PDF-1.4\n%%EOF\n",
        ),
    ],
)
def test_binary_adapters_reject_signature_only_or_truncated_sources(
    artifact_fixture: Any,
    artifact_id: str,
    payload: bytes,
) -> None:
    artifact_fixture.source_for(artifact_id).write_bytes(payload)

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(artifact_fixture, artifact_id)
    assert record["availability_status"] == "present"
    assert record["completion_status"] == "failed"
    assert [entry["code"] for entry in record["errors"]] == [
        "adapter_validation_failed"
    ]


def test_step06_accepts_producer_six_decimal_fraction(
    artifact_fixture: Any,
) -> None:
    counts = artifact_fixture.source_for("sample.SYNTH_A.orientation_counts")
    rows = read_tsv(counts)
    rows[0].update(
        {
            "input_records": "3",
            "flag_99_records": "1",
            "flag_147_records": "0",
            "flag_83_records": "0",
            "flag_163_records": "0",
            "fwd_like_records": "1",
            "rev_like_records": "0",
            "assigned_records": "1",
            "unassigned_records": "2",
            "assigned_fraction": "0.333333",
        }
    )
    FIXTURE.write_tsv(counts, ARTIFACT_MODELS.STEP06_COUNTS_HEADER, rows)

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(
        artifact_fixture,
        "sample.SYNTH_A.orientation_counts",
    )
    assert record["completion_status"] == "complete"


def test_step09_significant_rows_must_be_full_exact_subset(
    artifact_fixture: Any,
) -> None:
    significant = artifact_fixture.source_for(
        "analysis.synthetic.cmh_significant_sites"
    )
    rows = read_tsv(significant)
    rows[0]["qual"] = "61"
    header = tuple(rows[0])
    FIXTURE.write_tsv(significant, header, rows)

    result = run_builder(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = record_for(
        artifact_fixture,
        "analysis.synthetic.cmh_summary",
    )
    assert summary["completion_status"] == "failed"


def test_step09_rejects_unknown_status_and_pairwise_spectrum_mismatch(
    artifact_fixture: Any,
) -> None:
    all_sites = artifact_fixture.source_for("analysis.synthetic.cmh_all_sites")
    all_rows = read_tsv(all_sites)
    all_rows[0]["test_status"] = "unknown_status"
    FIXTURE.write_tsv(all_sites, tuple(all_rows[0]), all_rows)

    first = run_builder(artifact_fixture, execute=True)

    assert first.returncode == 0, first.stderr
    assert (
        record_for(
            artifact_fixture,
            "analysis.synthetic.cmh_summary",
        )["completion_status"]
        == "failed"
    )

    second_fixture = FIXTURE.build_fixture(
        artifact_fixture.root.parent / "pairwise_fixture"
    )
    spectrum = second_fixture.source_for("analysis.synthetic.mutation_spectrum_tsv")
    spectrum_rows = read_tsv(spectrum)
    by_type = {row["mutation_type"]: row for row in spectrum_rows}
    for field_name in (
        "candidate_count",
        "candidate_fraction",
        "successfully_tested_count",
        "significant_up_count",
        "significant_down_count",
    ):
        by_type["A>C"][field_name] = by_type["A>G"][field_name]
        by_type["A>G"][field_name] = "0"
    FIXTURE.write_tsv(
        spectrum,
        step09.STEP09_MUTATION_HEADER,
        spectrum_rows,
    )

    second = run_builder(second_fixture, execute=True)

    assert second.returncode == 0, second.stderr
    assert (
        record_for(
            second_fixture,
            "analysis.synthetic.cmh_summary",
        )["completion_status"]
        == "failed"
    )


def test_first_publication_rollback_fsync_failure_retains_recovery_lock(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    context = context_for(artifact_fixture)
    default_ops = ARTIFACT_PUBLICATION.DEFAULT_ARTIFACT_PUBLICATION_OPS
    real_validate = default_ops.validate_published_transaction
    real_fsync_directory = default_ops.fsync_directory
    output_sync_count = 0

    def fail_post_publication_validation(**kwargs: Any) -> None:
        if kwargs["require_current_source_locations"]:
            raise ARTIFACT_MODELS.ArtifactIndexError(
                "injected post-publication validation failure"
            )
        real_validate(**kwargs)

    def fail_rollback_sync(path: Path) -> None:
        nonlocal output_sync_count
        if path == context.output_dir:
            output_sync_count += 1
            if output_sync_count == 2:
                raise OSError("injected rollback directory fsync failure")
        real_fsync_directory(path)

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="rollback was incomplete",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            context,
            ops=publication_ops(
                validate_published_transaction=fail_post_publication_validation,
                fsync_directory=fail_rollback_sync,
            ),
        )

    assert output_sync_count == 2
    assert artifact_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in artifact_fixture.output_dir.iterdir()
    )


def test_publication_rechecks_sources_by_metadata_without_rehashing(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    context = context_for(artifact_fixture)
    source_paths = {path.resolve() for path in artifact_fixture.source_paths.values()}
    real_sha256_file = ARTIFACT_CONTRACTS.sha256_file
    rehashed_sources: list[Path] = []

    def track_hash(path: Path) -> str:
        resolved = Path(path).resolve()
        if resolved in source_paths:
            rehashed_sources.append(resolved)
        return real_sha256_file(path)

    monkeypatch.setattr(ARTIFACT_CONTRACTS, "sha256_file", track_hash)

    ARTIFACT_PUBLICATION.publish_context(context)

    assert rehashed_sources == []
