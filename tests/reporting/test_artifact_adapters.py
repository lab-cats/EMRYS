"""Focused contract and transaction tests for artifact-adapters-v1."""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import importlib
import json
import os
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from emrys.libraries.source_authority import PACKAGE_ROOT
from jsonschema import Draft202012Validator, FormatChecker
from emrys import analyses
from emrys.contracts.artifacts import api as ARTIFACT_CONTRACTS
from emrys.contracts.scientific_evidence import step08, step09
from tests.contract_integration.validation_rosters.validation_roster_expectations import (
    assert_exact_check_roster,
)
from tests.reporting.fixtures.artifact_adapters_v1 import build_fixture as FIXTURE
from emrys.reporting import _files
from emrys.reporting._run_summary.models import RunSummaryError

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_EPOCH = "1700000000"
EXPECTED_PRODUCER_PATHS = {
    "00a": "stages/star_index/step_00a_build_star_index.sh",
    "00b": "stages/gtf_to_bed12/converter.py",
    "00c": "stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh",
    "01": "stages/star_alignment/step_01_star_align.sh",
    "02": "stages/canonical_bam/step_02_sort_index_bam.sh",
    "02b": "evidence/canonical_bam_qc/step_02b_bam_qc.sh",
    "03": ("evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh"),
    "04": "stages/duplicate_marking/step_04_mark_duplicates.sh",
    "05": "stages/split_n_cigar/step_05_split_n_cigar_reads.sh",
    "06": "stages/mechanical_orientation/producer.py",
    "07": ("stages/partitioned_cohort_mpileup/producer.py"),
    "08": "stages/cohort_candidate_preprocessing/r/preprocess_cohort.R",
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


@pytest.fixture
def artifact_fixture(tmp_path: Path) -> Any:
    return FIXTURE.build_fixture(tmp_path / "fixture")


def artifact_index_arguments(
    fixture: Any,
    *,
    execute: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        package_root=PACKAGE_ROOT,
        artifact_source_root=fixture.root,
        run_id=fixture.run_id,
        run_contract=fixture.run_contract,
        inventory=fixture.inventory,
        analysis_policy=fixture.analysis_policy,
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
            context = ARTIFACT_CONTEXT.prepare_evidence_context(
                prepared_arguments,
                installed_package=SOURCE_AUTHORITY.admit_installed_package(),
                artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
                    root=prepared_arguments.artifact_source_root
                ),
            )
            if prepared_arguments.execute:
                ARTIFACT_PUBLICATION.publish_context(context)
            return DirectTransactionResult(context=context)
        except (
            ARTIFACT_MODELS.ArtifactIndexError,
            RunSummaryError,
            SOURCE_AUTHORITY.ArtifactSourceRootError,
            SOURCE_AUTHORITY.InstalledPackageError,
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
    return next(
        record
        for record in read_json(fixture.manifest_path)["artifacts"]
        if record["artifact_id"] == artifact_id
    )


def context_for(fixture: Any) -> Any:
    return ARTIFACT_CONTEXT.prepare_evidence_context(
        argparse.Namespace(
            run_id=fixture.run_id,
            run_contract=fixture.run_contract,
            inventory=fixture.inventory,
            analysis_policy=fixture.analysis_policy,
            output_root=fixture.output_root,
            profile=FIXTURE.analysis_profile_v1(),
            execute=True,
        ),
        installed_package=SOURCE_AUTHORITY.admit_installed_package(),
        artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(root=fixture.root),
    )


def owned_snapshot(fixture: Any) -> dict[str, bytes]:
    paths = fixture.summary_paths
    return {
        str(path.relative_to(fixture.output_dir)): path.read_bytes()
        for path in paths
        if path.is_file()
    }


def assert_no_owned_outputs(fixture: Any) -> None:
    assert not any(path.exists() or path.is_symlink() for path in fixture.summary_paths)
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
    for record in read_json(fixture.manifest_path)["artifacts"]:
        errors = list(validator.iter_errors(record))
        assert errors == [], "\n".join(error.message for error in errors)
        ARTIFACT_CONTRACTS.validate_artifact_semantics(record)
        ARTIFACT_CONTRACTS.reconcile_artifact_inventory_row(
            record,
            rows_by_id[record["artifact_id"]],
        )


def test_fixture_covers_exact_tracked_inventory_and_adapter_registry(
    artifact_fixture: Any,
) -> None:
    rows = artifact_fixture.inventory_rows

    assert len(rows) == 74
    assert [row["artifact_id"] for row in rows] == [
        row["artifact_id"] for row in FIXTURE.read_inventory_template()
    ]
    registry = ARTIFACT_REGISTRY.build_adapter_registry(
        FIXTURE.analysis_module_v1(), source_root=PACKAGE_ROOT
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
            (PACKAGE_ROOT / expected_path).read_bytes()
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
    assert evidence["09"]["evidence"][0]["sha256"] == (module.provider.package.sha256)


def test_prepare_context_keeps_package_and_artifact_roots_distinct(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installed_package = SOURCE_AUTHORITY.admit_installed_package()
    artifact_source_root = SOURCE_AUTHORITY.ArtifactSourceRoot(
        root=artifact_fixture.root
    )
    root_calls: Counter[str] = Counter()
    real_admit_package = SOURCE_AUTHORITY.admit_installed_package
    real_producer_evidence = ARTIFACT_CONTEXT.producer_evidence
    real_declared_contract_path = ARTIFACT_NATIVE.declared_contract_path
    real_validate_artifact_semantics = ARTIFACT_CONTRACTS.validate_artifact_semantics

    def observe_package(*, root: Path) -> Any:
        assert root == PACKAGE_ROOT
        root_calls["package"] += 1
        return real_admit_package(root=root)

    def producer_evidence(
        git_commit: str,
        *,
        source_root: Path,
        analysis_module: Any,
    ) -> dict[str, dict[str, Any]]:
        assert source_root == installed_package.root
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

    monkeypatch.setattr(
        ARTIFACT_CONTEXT,
        "admit_installed_package",
        observe_package,
    )
    context = ARTIFACT_CONTEXT.prepare_evidence_context(
        argparse.Namespace(
            run_id=artifact_fixture.run_id,
            run_contract=artifact_fixture.run_contract,
            inventory=artifact_fixture.inventory,
            analysis_policy=artifact_fixture.analysis_policy,
            output_root=artifact_fixture.output_root,
            profile=FIXTURE.analysis_profile_v1(),
            execute=False,
        ),
        installed_package=installed_package,
        artifact_source_root=artifact_source_root,
    )

    assert context.index.installed_package == installed_package
    assert context.index.artifact_source_root == artifact_source_root
    assert root_calls["package"] == 1
    assert root_calls["producers"] == 1
    assert root_calls["native_references"] > 0
    assert root_calls["record_semantics"] == len(artifact_fixture.inventory_rows)


def test_prepare_context_rejects_changed_installed_package(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ARTIFACT_CONTEXT,
        "admit_installed_package",
        lambda **_kwargs: dataclasses.replace(
            SOURCE_AUTHORITY.admit_installed_package(), content_sha256="0" * 64
        ),
    )
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="Installed package changed before provenance attribution",
    ):
        ARTIFACT_CONTEXT.prepare_evidence_context(
            argparse.Namespace(
                run_id=artifact_fixture.run_id,
                run_contract=artifact_fixture.run_contract,
                inventory=artifact_fixture.inventory,
                analysis_policy=artifact_fixture.analysis_policy,
                output_root=artifact_fixture.output_root,
                profile=FIXTURE.analysis_profile_v1(),
                execute=False,
            ),
            installed_package=SOURCE_AUTHORITY.admit_installed_package(),
            artifact_source_root=SOURCE_AUTHORITY.ArtifactSourceRoot(
                root=artifact_fixture.root
            ),
        )


def test_publication_rechecks_source_identity_before_terminal_receipt(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(artifact_fixture)
    calls = 0

    def recheck_source_identity(_context: Any) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ARTIFACT_MODELS.ArtifactIndexError("fixture source drift")

    monkeypatch.setattr(
        ARTIFACT_PUBLICATION, "recheck_source_identity", recheck_source_identity
    )
    with pytest.raises(ARTIFACT_MODELS.ArtifactIndexError, match="source drift"):
        ARTIFACT_PUBLICATION.publish_context(
            context,
        )

    assert calls == 2
    assert not context.summary_paths.summary_json.exists()


def test_dry_run_validates_all_sources_without_writing(
    artifact_fixture: Any,
) -> None:
    result = run_builder(artifact_fixture)

    assert result.returncode == 0, result.stderr
    assert result.context is not None
    assert len(result.context.index.records) == 74
    assert not artifact_fixture.output_root.exists()


def test_execute_publishes_inventory_ordered_schema_valid_transaction(
    artifact_fixture: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    published: list[Path] = []
    real_link = os.link

    def record_publication(source: Any, destination: Any, **kwargs: Any) -> None:
        real_link(source, destination, **kwargs)
        published.append(Path(destination))

    monkeypatch.setattr(os, "link", record_publication)
    result = run_builder(artifact_fixture, execute=True)
    assert result.returncode == 0, result.stderr
    assert published == [
        *artifact_fixture.summary_paths[1:],
        artifact_fixture.manifest_path,
    ]
    assert set(artifact_fixture.output_dir.iterdir()) == set(
        artifact_fixture.summary_paths
    )
    manifest = read_json(artifact_fixture.manifest_path)
    records = manifest["artifacts"]
    assert len(records) == 74
    assert [r["artifact_id"] for r in records] == [
        r["artifact_id"] for r in artifact_fixture.inventory_rows
    ]
    assert {r["completion_status"] for r in records} == {"complete"}
    assert all(
        not {"run_id", "run_contract", "provenance"}.intersection(r) for r in records
    )
    assert manifest["publication"]["transaction_state"] == "complete"
    assert manifest["inventory"]["sha256"] == sha256_file(artifact_fixture.inventory)
    assert_published_records_are_valid(artifact_fixture)
    assert not artifact_fixture.lock_path.exists()


def test_repreparation_is_deterministic_and_preserves_existing_transaction(
    artifact_fixture: Any,
) -> None:
    first = run_builder(artifact_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    before = owned_snapshot(artifact_fixture)
    second = run_builder(artifact_fixture)
    assert second.returncode == 0, second.stderr
    assert (
        second.context.index.records
        == read_json(artifact_fixture.manifest_path)["artifacts"]
    )
    assert owned_snapshot(artifact_fixture) == before
    assert not artifact_fixture.lock_path.exists()


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

    records = read_json(artifact_fixture.manifest_path)["artifacts"]
    assert Counter(record["completion_status"] for record in records) == {
        "complete": 68,
        "incomplete": 5,
        "failed": 1,
    }
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
    assert "does not match the immutable run contract" in collision.stderr
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
    unrelated = artifact_fixture.output_dir / "unrelated.run_summary.json"
    unrelated_payload = b'{"unrelated":true}\n'
    unrelated.write_bytes(unrelated_payload)

    first = run_builder(artifact_fixture, execute=True)
    second = run_builder(artifact_fixture)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert unrelated.read_bytes() == unrelated_payload
    records = read_json(artifact_fixture.manifest_path)["artifacts"]
    assert len(records) == 74
    assert str(undeclared) not in {r["expectation"]["source_path"] for r in records}


def test_foreign_lock_and_partial_prior_transaction_are_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locked = FIXTURE.build_fixture(tmp_path / "locked")
    locked.output_dir.mkdir(parents=True)
    lock_payload = b"foreign lock\n"
    locked.lock_path.write_bytes(lock_payload)

    locked_result = run_builder(locked, execute=True)

    assert locked_result.returncode != 0
    assert "locked" in locked_result.stderr
    assert locked.lock_path.read_bytes() == lock_payload
    assert not any(path.exists() for path in locked.summary_paths)
    partial = FIXTURE.build_fixture(tmp_path / "partial")
    partial.output_dir.mkdir(parents=True)
    partial_payload = b"partial prior projection\n"
    partial.summary_paths[1].write_bytes(partial_payload)
    result = run_builder(partial, execute=True)
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert partial.summary_paths[1].read_bytes() == partial_payload
    assert not partial.manifest_path.exists()
    assert not partial.lock_path.exists()


def test_terminal_receipt_link_failure_rolls_back_combined_outputs(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    context = context_for(artifact_fixture)
    real_link = os.link

    def fail_receipt_publication(source: Any, destination: Any, **kwargs: Any) -> None:
        if Path(destination) == context.summary_paths.summary_json:
            raise OSError("injected summary receipt publication failure")
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(os, "link", fail_receipt_publication)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="injected summary receipt publication failure",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            context,
        )

    assert_no_owned_outputs(artifact_fixture)


@pytest.mark.parametrize("prepared_first", [False, True])
def test_existing_transaction_refusal_preserves_every_byte_and_inode(
    artifact_fixture: Any,
    prepared_first: bool,
) -> None:
    stale = context_for(artifact_fixture) if prepared_first else None
    ARTIFACT_PUBLICATION.publish_context(context_for(artifact_fixture))
    context = stale if stale is not None else context_for(artifact_fixture)
    before = owned_snapshot(artifact_fixture)
    paths = artifact_fixture.summary_paths
    identities = {path: (path.stat().st_dev, path.stat().st_ino) for path in paths}
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError, match="output already exists"
    ):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert owned_snapshot(artifact_fixture) == before
    assert {
        path: (path.stat().st_dev, path.stat().st_ino) for path in paths
    } == identities
    assert not artifact_fixture.lock_path.exists()


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
        ARTIFACT_CONTEXT.recheck_inputs(context.index)

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


def test_semantically_identical_moved_run_contract_can_be_prepared(
    artifact_fixture: Any,
) -> None:
    moved_contract = artifact_fixture.root / "moved_contract.json"
    moved_contract.write_text(
        json.dumps(
            dict(reversed(list(read_json(artifact_fixture.run_contract).items()))),
            separators=(",", ":"),
        )
        + "\n"
    )
    arguments = artifact_index_arguments(artifact_fixture)
    arguments.run_contract = moved_contract
    result = run_builder(artifact_fixture, arguments=arguments)
    assert result.returncode == 0, result.stderr
    assert result.context.summary_document["run_contract_file"] == {
        "path": str(moved_contract),
        "sha256": sha256_file(moved_contract),
    }


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
    target = tmp_path / "manifest-target"
    target.write_bytes(b"preserve target")
    owned.manifest_path.symlink_to(target)
    result = run_builder(owned, execute=True)
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert target.read_bytes() == b"preserve target"


@pytest.mark.parametrize("component", ("products", "artifact-summary"))
def test_publication_rejects_symlinked_output_ancestor(
    artifact_fixture: Any,
    tmp_path: Path,
    component: str,
) -> None:
    products = artifact_fixture.root / "products"
    output_root = products / "artifact-summary"
    context = context_for(
        dataclasses.replace(artifact_fixture, output_root=output_root)
    )
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
    context = context_for(
        dataclasses.replace(artifact_fixture, output_root=output_root)
    )
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


def test_post_publication_source_mutation_rolls_back(
    artifact_fixture: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = context_for(artifact_fixture)
    real_link = os.link
    source = artifact_fixture.source_for("sample.SYNTH_A.star_log")

    def mutate_after_manifest(staged: Any, final: Any, **kwargs: Any) -> None:
        real_link(staged, final, **kwargs)
        if Path(final) == context.summary_paths.summary_json:
            source.write_text("mutated after publication\n")

    monkeypatch.setattr(os, "link", mutate_after_manifest)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError, match="changed after initial inspection"
    ):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert_no_owned_outputs(artifact_fixture)


def test_post_commit_stage_cleanup_failure_preserves_new_transaction(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(artifact_fixture)
    real_remove = _files.remove_owned_stage

    def fail_stage_cleanup(
        path: Path,
        token: str,
        identity: tuple[int, int] | None,
        error_type: type[Exception],
    ) -> None:
        if path.name.endswith(".tmp.records"):
            raise OSError("injected stage cleanup failure")
        real_remove(path, token, identity, error_type)

    monkeypatch.setattr(_files, "remove_owned_stage", fail_stage_cleanup)
    with pytest.raises(ARTIFACT_MODELS.ArtifactIndexError, match="cleanup failed"):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert (
        read_json(artifact_fixture.manifest_path)["publication"]["attempt_id"]
        == context.index.attempt_id
    )
    assert_published_records_are_valid(artifact_fixture)
    assert artifact_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in artifact_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".tmp.records")
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
        for record in context.index.records
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
        for record in context.index.records
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
    document = read_json(artifact_fixture.manifest_path)
    assert {record["availability_status"] for record in document["artifacts"]} == {
        "missing"
    }
    assert document["publication"]["transaction_state"] == "complete"


def test_incomplete_first_publication_rollback_retains_lock_and_anchors(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(artifact_fixture)
    real_link, real_unlink = os.link, Path.unlink
    record = context.summary_paths.summary_tsv

    def fail_index(source: Any, destination: Any, **kwargs: Any) -> None:
        if Path(destination) == context.summary_paths.qc_summary:
            raise OSError("injected index publication failure")
        real_link(source, destination, **kwargs)

    def fail_record_cleanup(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == record:
            raise OSError("injected owned record cleanup failure")
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "link", fail_index)
    monkeypatch.setattr(Path, "unlink", fail_record_cleanup)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError, match="rollback was incomplete"
    ):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert record.is_file()
    assert not context.summary_paths.summary_json.exists()
    assert artifact_fixture.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in artifact_fixture.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".tmp.records")
        for path in artifact_fixture.output_dir.iterdir()
    )


def test_failed_published_validation_removes_receipt_before_owned_data(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(artifact_fixture)
    removed: list[Path] = []
    real_unlink = Path.unlink

    real_recheck = ARTIFACT_PUBLICATION.recheck_inputs

    def fail_validation(value: Any) -> None:
        real_recheck(value)
        if context.summary_paths.summary_json.exists():
            raise ARTIFACT_MODELS.ArtifactIndexError(
                "injected transaction validation failure"
            )

    def observe_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
        removed.append(path)
        real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(ARTIFACT_PUBLICATION, "recheck_inputs", fail_validation)
    monkeypatch.setattr(Path, "unlink", observe_unlink)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError, match="transaction validation failure"
    ):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert removed[0] == context.summary_paths.summary_json
    assert_no_owned_outputs(artifact_fixture)


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

    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="Run contract or inventory changed after admission",
    ):
        if replacement:
            ARTIFACT_CONTEXT.recheck_inputs(context.index)
        else:
            ARTIFACT_PUBLICATION.publish_context(context)

    if replacement:
        assert owned_snapshot(artifact_fixture) == before
        assert not artifact_fixture.lock_path.exists()
    else:
        assert_no_owned_outputs(artifact_fixture)


def test_inventory_revision_prepares_lineage_without_changing_existing_outputs(
    artifact_fixture: Any,
) -> None:
    first = run_builder(artifact_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    first_manifest = read_json(artifact_fixture.manifest_path)
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

    before = owned_snapshot(artifact_fixture)
    second = run_builder(artifact_fixture)

    assert second.returncode == 0, second.stderr
    second_manifest = second.context.summary_document
    assert second_manifest["run_contract"] == first_manifest["run_contract"]
    assert (
        second_manifest["inventory"]["sha256"] != first_manifest["inventory"]["sha256"]
    )
    assert [r["artifact_id"] for r in second.context.index.records] == [
        r["artifact_id"] for r in revised
    ]

    assert owned_snapshot(artifact_fixture) == before


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
    default_ops = ARTIFACT_PUBLICATION
    real_validate = default_ops.recheck_inputs
    real_fsync_directory = _files.fsync_path
    validation_failed = rollback_sync_failed = False

    def fail_post_publication_validation(value: Any) -> None:
        nonlocal validation_failed
        if context.summary_paths.summary_json.exists():
            validation_failed = True
            raise ARTIFACT_MODELS.ArtifactIndexError(
                "injected post-publication validation failure"
            )
        real_validate(value)

    def fail_rollback_sync(path: Path) -> None:
        nonlocal rollback_sync_failed
        if path == context.index.output_dir and validation_failed:
            rollback_sync_failed = True
            raise OSError("injected rollback directory fsync failure")
        real_fsync_directory(path)

    monkeypatch.setattr(
        ARTIFACT_PUBLICATION,
        "recheck_inputs",
        fail_post_publication_validation,
    )
    monkeypatch.setattr(_files, "fsync_path", fail_rollback_sync)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError,
        match="rollback was incomplete",
    ):
        ARTIFACT_PUBLICATION.publish_context(
            context,
        )

    assert rollback_sync_failed
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


def test_concurrent_file_is_preserved_when_exclusive_link_fails(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(artifact_fixture)
    selected = context.summary_paths.summary_tsv
    real_link = os.link
    foreign_identity = None

    def create_concurrent_file(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal foreign_identity
        if Path(destination) == selected:
            selected.write_bytes(b"concurrent output; preserve\n")
            foreign_identity = selected.stat().st_ino
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(os, "link", create_concurrent_file)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError, match="rollback was incomplete"
    ):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert selected.read_bytes() == b"concurrent output; preserve\n"
    assert selected.stat().st_ino == foreign_identity
    assert context.index.lock_path.is_file()
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in context.index.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".tmp.records")
        for path in context.index.output_dir.iterdir()
    )


def test_directory_replacement_preserves_foreign_namespace_and_owned_evidence(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = context_for(artifact_fixture)
    displaced = context.index.output_dir.with_name("displaced-artifact-output")
    real_link = os.link

    def replace_directory(source: Any, destination: Any, **kwargs: Any) -> None:
        if Path(destination) == context.summary_paths.qc_summary:
            context.index.output_dir.rename(displaced)
            context.index.output_dir.mkdir()
            (context.index.output_dir / "keep").write_bytes(b"foreign directory\n")
            raise OSError("injected directory replacement")
        real_link(source, destination, **kwargs)

    monkeypatch.setattr(os, "link", replace_directory)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError, match="rollback was incomplete"
    ):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert [path.name for path in context.index.output_dir.iterdir()] == ["keep"]
    assert (context.index.output_dir / "keep").read_bytes() == b"foreign directory\n"
    assert (displaced / context.index.lock_path.name).is_file()
    assert any(path.name.endswith(".tmp.records") for path in displaced.iterdir())


def test_signal_immediately_after_artifact_link_rolls_back_owned_outputs(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import signal

    context = context_for(artifact_fixture)
    real_link = os.link
    previous = signal.getsignal(signal.SIGTERM)

    def signal_after_link(source: Any, destination: Any, **kwargs: Any) -> None:
        real_link(source, destination, **kwargs)
        if Path(destination) == context.summary_paths.qc_summary:
            os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(os, "link", signal_after_link)
    with pytest.raises(ARTIFACT_MODELS.ArtifactIndexError, match="signal"):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert signal.getsignal(signal.SIGTERM) == previous
    assert_no_owned_outputs(artifact_fixture)


def test_same_byte_foreign_replacement_cannot_commit(
    artifact_fixture: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = context_for(artifact_fixture)
    selected = context.summary_paths.summary_json
    real_link = os.link
    foreign_identity = None
    expected = b""

    def replace_link(source: Any, destination: Any, **kwargs: Any) -> None:
        nonlocal foreign_identity, expected
        real_link(source, destination, **kwargs)
        if Path(destination) == selected:
            expected = selected.read_bytes()
            selected.unlink()
            selected.write_bytes(expected)
            foreign_identity = selected.stat().st_ino

    monkeypatch.setattr(os, "link", replace_link)
    with pytest.raises(
        ARTIFACT_MODELS.ArtifactIndexError, match="rollback was incomplete"
    ):
        ARTIFACT_PUBLICATION.publish_context(context)
    assert selected.read_bytes() == expected
    assert selected.stat().st_ino == foreign_identity
    assert context.index.lock_path.is_file()
    assert any(
        path.name.endswith(".tmp.records")
        for path in context.index.output_dir.iterdir()
    )
    assert any(
        path.name.endswith(".RECOVERY.txt")
        for path in context.index.output_dir.iterdir()
    )
