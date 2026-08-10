"""Focused contract and transaction tests for artifact-adapters-v1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORTING_ROOT = REPO_ROOT / "src" / "norad" / "reporting"
ROSTER_ORACLE = (
    REPO_ROOT
    / "tests"
    / "contract_integration"
    / "validation_rosters"
    / "validation_roster_expectations.py"
)
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "reporting_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = REPORTING_ROOT / "build_artifact_index.py"
FIXTURE_BUILDER = (
    REPO_ROOT
    / "tests"
    / "reporting"
    / "fixtures"
    / "artifact_adapters_v1"
    / "build_fixture.py"
)
FIXED_EPOCH = "1700000000"
EXPECTED_PRODUCER_EVIDENCE = {
    "00a": (
        "src/norad/stages/construct_STAR_index/"
        "step_00a_build_novogene_star_index.slurm",
        "f27924e80fee3b8f207a41fd7af472897ad51f06aa2e4c670973eb51f25b5fcc",
    ),
    "00b": (
        "src/norad/stages/convert_GTF_to_BED12/gtf_to_bed12.py",
        "ddca3b0f11bb690fdee60f99b8885be74b64000b02dd250d7740ab9db47a9a79",
    ),
    "00c": (
        "src/norad/stages/construct_FASTA_sidecars/step_00c_prepare_gatk_reference.sh",
        "a78a5769d47a638e486d1ef82582331f91689baad99fef01962d16e6d3f991bf",
    ),
    "01": (
        "src/norad/stages/align_RNA_reads_with_STAR/step_01_star_align.sh",
        "dd275a60c7ed6d5f74d9d5e3296c15e0fddb0ff93b6b1f0ea09e83483360e2d0",
    ),
    "02": (
        "src/norad/stages/construct_canonical_BAM/step_02_sort_index_bam.sh",
        "3e8cd58d7d6d0fea34c9e5e3b283394886db787c236965b529a482ab9f735b6d",
    ),
    "02b": (
        "src/norad/evidence/collect_canonical_BAM_QC_evidence/step_02b_bam_qc.sh",
        "43730e4c06aaaf7f6d9d48ef1177bbc3b90f82ca16606b63fd3aa3aa81c1d5a9",
    ),
    "03": (
        "src/norad/evidence/collect_RSeQC_paired_orientation_evidence/"
        "step_03_infer_strandedness_and_orientation.sh",
        "0ee478b58419ba1a1b535d8397fd107fc0f8610afb45e43adffc3b57dd2406c7",
    ),
    "04": (
        "src/norad/stages/mark_BAM_duplicates_with_Picard/step_04_mark_duplicates.sh",
        "d99ab505094595c233ba3a9b37a08a06d214d0501aa634b842f57f88217bf733",
    ),
    "05": (
        "src/norad/stages/split_N_cigar_reads_with_GATK/step_05_split_n_cigar_reads.sh",
        "e4d1b5f16bb42b670bfb617455f61e969fdd0b3012cccfe93344ea24a0b4e5e4",
    ),
    "06": (
        "src/norad/stages/partition_BAM_by_mechanical_read_orientation/"
        "step_06_split_bam_by_read_orientation.sh",
        "f3b4e11b65b469ab45bff0359b87ba87c5d6c6a68564c045426dc291cce9c6a0",
    ),
    "07": (
        "src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/"
        "step_07_bcftools_mpileup_by_chrom_and_strand.sh",
        "715791da0337cc4561eeb71bb30c2518c0de7c53e2c21d3d4418551349c29858",
    ),
    "08": (
        "src/norad/stages/preprocess_and_annotate_cohort_candidates/"
        "step_08_vcf_preprocessing.sh",
        "7389b26302241ed1f8f075dd220e363223f4735a029380d564d3b02fd6e94769",
    ),
    "09": (
        "src/norad/analyses/rank_cohort_candidates_with_paired_CMH/"
        "step_09_cmh_editing_site_calling.sh",
        "9311dc4a847e8f749c3fe033112070279b9d7beb0ff5dfaf69f67702b81f15bc",
    ),
    "09c": (
        "src/norad/evidence/assemble_scientific_review_evidence_package/"
        "step_09c_scientific_validation.py",
        "cfb0da6323094cc5d02c007fb6e67dcbebfed68b7d852df895c23ae0d5073490",
    ),
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
}


def load_fixture_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "norad_artifact_adapter_fixture_builder",
        FIXTURE_BUILDER,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load fixture builder: {FIXTURE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FIXTURE = load_fixture_module()
ADAPTER = FIXTURE.ADAPTER
ARTIFACT_CONTEXT = importlib.import_module("norad.reporting._artifact_index.context")
ARTIFACT_VALIDATION = importlib.import_module(
    "norad.reporting._artifact_index.validation"
)


@pytest.fixture
def artifact_fixture(tmp_path: Path) -> Any:
    return FIXTURE.build_fixture(tmp_path / "fixture")


def run_cli(
    fixture: Any,
    *,
    execute: bool = False,
    extra_env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    if extra_env:
        environment.update(extra_env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *fixture.command_args(execute=execute)],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


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
    return ADAPTER.prepare_context(
        argparse.Namespace(
            run_id=fixture.run_id,
            run_contract=fixture.run_contract,
            inventory=fixture.inventory,
            output_root=fixture.output_root,
            execute=True,
        )
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
    schemas, registry = ADAPTER.contracts.load_schema_registry()
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
        ADAPTER.contracts.validate_artifact_semantics(record)
        ADAPTER.contracts.reconcile_artifact_inventory_row(
            record,
            rows_by_id[record["artifact_id"]],
        )
        assert path.read_bytes() == ADAPTER.canonical_json_bytes(record)


def test_fixture_covers_exact_tracked_inventory_and_adapter_registry(
    artifact_fixture: Any,
) -> None:
    rows = artifact_fixture.inventory_rows

    assert len(rows) == 81
    assert [row["artifact_id"] for row in rows] == [
        row["artifact_id"] for row in FIXTURE.read_inventory_template()
    ]
    assert {row["adapter"] for row in rows} == set(ADAPTER.ADAPTER_REGISTRY)
    assert len(artifact_fixture.source_paths) == 81
    assert all(path.is_file() for path in artifact_fixture.source_paths.values())
    assert not artifact_fixture.output_root.exists()


def test_migrated_implementation_evidence_uses_final_paths_and_frozen_bytes() -> None:
    git_commit = "a" * 40

    evidence = ADAPTER.producer_evidence(git_commit)

    assert tuple(evidence) == tuple(EXPECTED_PRODUCER_EVIDENCE)
    assert tuple(ADAPTER.STEP_PRODUCERS) == tuple(EXPECTED_PRODUCER_EVIDENCE)
    for step_id, (expected_path, expected_sha256) in EXPECTED_PRODUCER_EVIDENCE.items():
        record = evidence[step_id]
        assert record["status"] == "implemented"
        assert record["git_commit"] == git_commit
        implementation_rows = record["evidence"]
        assert len(implementation_rows) == 1
        row = implementation_rows[0]
        assert row["evidence_id"] == f"implementation_{step_id}"
        assert row["role"] == "implementation"
        assert row["path"] == expected_path
        assert row["sha256"] == expected_sha256


def test_contract_modules_are_shared_package_identities() -> None:
    assert ADAPTER.step09.step08 is ADAPTER.step08
    assert ADAPTER.review_package is ADAPTER._contract_owners.review_package


def test_artifact_index_has_no_private_step09c_dependency() -> None:
    source = Path(ADAPTER.__file__).read_text(encoding="utf-8")
    assert "step_09c_scientific_validation.py" not in source
    assert not hasattr(ADAPTER, "step09c")


def test_help_and_dry_run_validate_all_sources_without_writing(
    artifact_fixture: Any,
) -> None:
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    result = run_cli(artifact_fixture)

    assert help_result.returncode == 0, help_result.stderr
    for option in (
        "--run-id",
        "--run-contract",
        "--inventory",
        "--output-root",
        "--execute",
    ):
        assert option in help_result.stdout
    assert result.returncode == 0, result.stderr
    assert "Mode: dry-run" in result.stdout
    assert "Inventory artifacts: 81" in result.stdout
    assert "present=81" in result.stdout
    assert "complete=81" in result.stdout
    assert "Receipt (published last)" in result.stdout
    assert "Dry-run only" in result.stdout
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
    assert context.index_bytes != ADAPTER.tsv_bytes(original, context.index_rows)


def test_execute_publishes_inventory_ordered_schema_valid_transaction(
    artifact_fixture: Any,
) -> None:
    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    assert "Published receipt last" in result.stdout
    index_rows = read_tsv(artifact_fixture.artifacts_path)
    receipt_rows = read_tsv(artifact_fixture.receipt_path)
    assert len(index_rows) == 81
    assert len(receipt_rows) == 1
    receipt = receipt_rows[0]
    assert [row["artifact_id"] for row in index_rows] == [
        row["artifact_id"] for row in artifact_fixture.inventory_rows
    ]
    assert {row["availability_status"] for row in index_rows} == {"present"}
    assert {row["completion_status"] for row in index_rows} == {"complete"}
    assert receipt["inventory_row_count"] == "81"
    assert receipt["artifact_record_count"] == "81"
    assert receipt["present_artifact_count"] == "81"
    assert receipt["complete_artifact_count"] == "81"
    assert receipt["required_missing_artifact_count"] == "0"
    assert receipt["warning_count"] == "0"
    assert receipt["error_count"] == "0"
    assert receipt["published_output_count"] == "83"
    assert receipt["transaction_state"] == "complete"
    assert receipt["artifacts_index_sha256"] == sha256_file(
        artifact_fixture.artifacts_path
    )
    assert len(list(artifact_fixture.records_dir.glob("*.json"))) == 81

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
    first = run_cli(artifact_fixture, execute=True)
    assert first.returncode == 0, first.stderr
    first_record_bytes = {
        path.name: path.read_bytes()
        for path in sorted(artifact_fixture.records_dir.glob("*.json"))
    }
    first_index = artifact_fixture.artifacts_path.read_bytes()
    first_receipt = read_tsv(artifact_fixture.receipt_path)[0]

    second = run_cli(artifact_fixture, execute=True)
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

    result = run_cli(artifact_fixture, execute=True)

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
    assert receipt["present_artifact_count"] == "80"
    assert receipt["missing_artifact_count"] == "1"
    assert receipt["complete_artifact_count"] == "75"
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

    result = run_cli(artifact_fixture, execute=True)

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

    result = run_cli(artifact_fixture, execute=True)

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

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(artifact_fixture, artifact_id)
    assert record["completion_status"] == "complete"
    assert record["errors"] == []


def test_same_run_id_rejects_changed_run_contract_without_touching_outputs(
    artifact_fixture: Any,
) -> None:
    initial = run_cli(artifact_fixture, execute=True)
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
    ordered_contract = {field: contract[field] for field in ADAPTER.RUN_CONTRACT_FIELDS}
    artifact_fixture.run_contract.write_text(
        json.dumps(ordered_contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    collision = run_cli(artifact_fixture, execute=True)

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

    first = run_cli(artifact_fixture, execute=True)
    second = run_cli(artifact_fixture, execute=True)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert unrelated.read_bytes() == unrelated_payload
    index_rows = read_tsv(artifact_fixture.artifacts_path)
    assert len(index_rows) == 81
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

    locked_result = run_cli(locked, execute=True)

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

    partial_result = run_cli(partial, execute=True)

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
    real_replace = ADAPTER.os.replace

    def fail_index_publication(source: Any, destination: Any) -> None:
        if (
            Path(destination) == context.artifacts_path
            and ".tmp.tsv" in Path(source).name
        ):
            raise OSError("injected index publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(ADAPTER.os, "replace", fail_index_publication)

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="injected index publication failure",
    ):
        ADAPTER.publish_context(context)

    assert_no_owned_outputs(artifact_fixture)


def test_replacement_rename_failure_restores_prior_transaction_byte_for_byte(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ADAPTER.publish_context(context_for(artifact_fixture))
    before = owned_snapshot(artifact_fixture)
    replacement = context_for(artifact_fixture)
    real_replace = ADAPTER.os.replace
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

    monkeypatch.setattr(ADAPTER.os, "replace", fail_replacement_index)

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="injected replacement index failure",
    ):
        ADAPTER.publish_context(replacement)

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
        ADAPTER.ArtifactIndexError,
        match="changed after initial inspection",
    ):
        ADAPTER.publish_context(context)

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
            raise ADAPTER.ArtifactIndexError("injected live stat-source failure")
        return real_stat_source(path, hash_content=hash_content)

    monkeypatch.setattr(ARTIFACT_CONTEXT, "stat_source", fail_target_recheck)

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="injected live stat-source failure",
    ):
        ADAPTER.recheck_inputs(context)

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
    reordered = run_cli(artifact_fixture)
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
    duplicate = run_cli(artifact_fixture)
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
    nan_result = run_cli(artifact_fixture)
    assert nan_result.returncode != 0
    assert "Non-standard JSON numeric constant" in nan_result.stderr
    assert not artifact_fixture.output_root.exists()


def test_semantically_identical_moved_run_contract_can_retry(
    artifact_fixture: Any,
) -> None:
    first = run_cli(artifact_fixture, execute=True)
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
    arguments = artifact_fixture.command_args(execute=True)
    arguments[arguments.index("--run-contract") + 1] = str(moved_contract)
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = FIXED_EPOCH

    second = subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=REPO_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
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
        ADAPTER.contracts.INVENTORY_HEADER,
        rows,
    )

    result = run_cli(artifact_fixture, execute=True)

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

    escaped_result = run_cli(escaped, execute=True)

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

    owned_result = run_cli(owned, execute=True)

    assert owned_result.returncode != 0
    assert "records path is not a regular owned directory" in owned_result.stderr
    assert list(records_target.iterdir()) == []


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
        ADAPTER.ArtifactIndexError,
        match="changed after initial inspection",
    ):
        ADAPTER.publish_context(context)

    assert_no_owned_outputs(artifact_fixture)


def test_native_receipt_mismatch_is_published_as_explicit_failure(
    artifact_fixture: Any,
) -> None:
    receipt_path = artifact_fixture.source_for("cohort.synthetic.p1.receipt")
    rows = read_tsv(receipt_path)
    rows[0]["vcf_record_count"] = "2"
    FIXTURE.write_tsv(receipt_path, ADAPTER.STEP07_RECEIPT_HEADER, rows)

    result = run_cli(artifact_fixture, execute=True)

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

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    record = record_for(artifact_fixture, "sample.SYNTH_A.star_log")
    assert record["availability_status"] == "externally_unavailable"
    assert record["completion_status"] == "incomplete"
    assert record["source"] is None
    assert [entry["code"] for entry in record["warnings"]] == [
        "source_externally_unavailable"
    ]


def test_reserved_biological_ready_state_is_rejected(
    artifact_fixture: Any,
) -> None:
    for artifact_id in (
        "review.synthetic.review_plan",
        "review.synthetic.review_summary",
    ):
        path = artifact_fixture.source_for(artifact_id)
        rows = read_tsv(path)
        rows[0]["overall_science_status"] = "biological_interpretation_ready"
        header = (
            ADAPTER.review_package.REVIEW_PLAN_HEADER
            if artifact_id.endswith("review_plan")
            else ADAPTER.review_package.REVIEW_SUMMARY_HEADER
        )
        FIXTURE.write_tsv(path, header, rows)
    review_summary_path = artifact_fixture.source_for("review.synthetic.review_summary")
    review_summary_rows = read_tsv(review_summary_path)
    review_summary_rows[0]["review_plan_sha256"] = sha256_file(
        artifact_fixture.source_for("review.synthetic.review_plan")
    )
    FIXTURE.write_tsv(
        review_summary_path,
        ADAPTER.review_package.REVIEW_SUMMARY_HEADER,
        review_summary_rows,
    )

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = record_for(artifact_fixture, "review.synthetic.review_summary")
    assert summary["completion_status"] == "failed"
    assert summary["scientific_state"] is None
    assert [entry["code"] for entry in summary["errors"]] == ["science_status_invalid"]
    assert all(
        record_for(artifact_fixture, row["artifact_id"])["scientific_state"] is None
        for row in artifact_fixture.inventory_rows
        if row["step_id"] == "09c"
    )


def test_tampered_receipt_and_extra_record_entry_block_retry(
    artifact_fixture: Any,
) -> None:
    published = run_cli(artifact_fixture, execute=True)
    assert published.returncode == 0, published.stderr
    original_receipt = artifact_fixture.receipt_path.read_bytes()
    rows = read_tsv(artifact_fixture.receipt_path)
    rows[0]["complete_artifact_count"] = "0"
    FIXTURE.write_tsv(
        artifact_fixture.receipt_path,
        ADAPTER.ARTIFACT_RECEIPT_HEADER,
        rows,
    )

    tampered = run_cli(artifact_fixture)

    assert tampered.returncode != 0
    assert "receipt rollup is invalid" in tampered.stderr
    artifact_fixture.receipt_path.write_bytes(original_receipt)
    record_path = artifact_fixture.records_dir / "sample.SYNTH_A.star_log.json"
    original_record = record_path.read_bytes()
    record_path.write_text("{}\n", encoding="utf-8")

    bad_record = run_cli(artifact_fixture)

    assert bad_record.returncode != 0
    assert "record hash is invalid" in bad_record.stderr
    record_path.write_bytes(original_record)
    unexpected = artifact_fixture.records_dir / "unexpected"
    unexpected.mkdir()

    extra_entry = run_cli(artifact_fixture)

    assert extra_entry.returncode != 0
    assert "missing or unexpected files" in extra_entry.stderr
    assert unexpected.is_dir()
    unexpected.rmdir()
    target = artifact_fixture.root / "record_target.json"
    target.write_bytes(original_record)
    record_path.unlink()
    record_path.symlink_to(target)

    symlinked_record = run_cli(artifact_fixture)

    assert symlinked_record.returncode != 0
    assert "non-regular owned entry" in symlinked_record.stderr


def test_stale_predecessor_context_cannot_overwrite_newer_retry(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ADAPTER.publish_context(context_for(artifact_fixture))
    stale = context_for(artifact_fixture)
    ADAPTER.publish_context(context_for(artifact_fixture))
    before = owned_snapshot(artifact_fixture)

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="predecessor changed",
    ):
        ADAPTER.publish_context(stale)

    assert owned_snapshot(artifact_fixture) == before
    assert not artifact_fixture.lock_path.exists()


def test_prepare_context_uses_live_predecessor_validation_owner(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ADAPTER.publish_context(context_for(artifact_fixture))
    real_validate = ARTIFACT_VALIDATION.validate_published_transaction
    reached_predecessor = False

    def fail_predecessor_validation(**kwargs: Any) -> None:
        nonlocal reached_predecessor
        if not kwargs["require_current_source_locations"]:
            reached_predecessor = True
            raise ADAPTER.ArtifactIndexError(
                "injected live predecessor-validation failure"
            )
        real_validate(**kwargs)

    monkeypatch.setattr(
        ARTIFACT_VALIDATION,
        "validate_published_transaction",
        fail_predecessor_validation,
    )

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
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
    real_validate = ADAPTER.validate_published_transaction
    source = artifact_fixture.source_for("sample.SYNTH_A.star_log")
    mutated = False

    def mutate_after_validation(**kwargs: Any) -> None:
        nonlocal mutated
        real_validate(**kwargs)
        if kwargs["require_current_source_locations"] and not mutated:
            source.write_text("mutated after publication\n", encoding="utf-8")
            mutated = True

    monkeypatch.setattr(
        ADAPTER,
        "validate_published_transaction",
        mutate_after_validation,
    )

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="changed after initial inspection",
    ):
        ADAPTER.publish_context(context)

    assert mutated
    assert_no_owned_outputs(artifact_fixture)


def test_post_commit_backup_cleanup_failure_preserves_new_transaction(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ADAPTER.publish_context(context_for(artifact_fixture))
    prior_receipt = read_tsv(artifact_fixture.receipt_path)[0]
    replacement = context_for(artifact_fixture)
    real_remove_owned = ADAPTER.remove_owned
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

    monkeypatch.setattr(
        ADAPTER,
        "remove_owned",
        fail_backup_index_cleanup,
    )

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="cleanup failed",
    ):
        ADAPTER.publish_context(replacement)

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


def test_native_metrics_and_science_state_are_conservative(
    artifact_fixture: Any,
) -> None:
    result = run_cli(artifact_fixture, execute=True)
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
    review = record_for(
        artifact_fixture,
        "review.synthetic.review_summary",
    )
    assert review["scientific_state"]["overall_status"] == ("evidence_incomplete")
    assert review["runtime_validation"]["status"] == "not_run"
    assert review["cluster_validation"]["proof_status"] == "not_run"
    assert review["attempts"] == []
    assert review["selected_attempt_id"] is None


def test_all_missing_sources_publish_complete_index_transaction(
    artifact_fixture: Any,
) -> None:
    for path in artifact_fixture.source_paths.values():
        path.unlink()

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    receipt = read_tsv(artifact_fixture.receipt_path)[0]
    assert receipt["missing_artifact_count"] == "81"
    assert receipt["incomplete_artifact_count"] == "81"
    assert receipt["required_missing_artifact_count"] == "81"
    assert receipt["transaction_state"] == "complete"


def test_incomplete_replacement_rollback_retains_lock_and_recovery(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    ADAPTER.publish_context(context_for(artifact_fixture))
    replacement = context_for(artifact_fixture)
    real_replace = ADAPTER.os.replace
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

    monkeypatch.setattr(
        ADAPTER.os,
        "replace",
        fail_publication_and_restoration,
    )

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="rollback was incomplete",
    ):
        ADAPTER.publish_context(replacement)

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
    ADAPTER.publish_context(context_for(artifact_fixture))
    replacement = context_for(artifact_fixture)
    real_validate = ADAPTER.validate_published_transaction
    prior_validation_count = 0

    def fail_new_and_restored_validation(**kwargs: Any) -> None:
        nonlocal prior_validation_count
        if kwargs["require_current_source_locations"]:
            raise ADAPTER.ArtifactIndexError(
                "injected new-transaction validation failure"
            )
        prior_validation_count += 1
        if prior_validation_count == 2:
            raise ADAPTER.ArtifactIndexError(
                "injected restored-transaction validation failure"
            )
        real_validate(**kwargs)

    monkeypatch.setattr(
        ADAPTER,
        "validate_published_transaction",
        fail_new_and_restored_validation,
    )

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="rollback was incomplete",
    ):
        ADAPTER.publish_context(replacement)

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
            "cohort.synthetic.step08_summary",
            "cohort.synthetic.step08_sites",
        ),
        (
            "09",
            "analysis.synthetic.cmh_summary",
            "analysis.synthetic.cmh_all_sites",
        ),
        (
            "09c",
            "review.synthetic.review_summary",
            "review.synthetic.review_plan",
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
        FIXTURE.write_tsv(path, ADAPTER.STEP06_COUNTS_HEADER, rows)
    elif step_id == "08":
        path = artifact_fixture.source_for("cohort.synthetic.step08_summary")
        rows = read_tsv(path)
        rows[0]["published_candidate_count"] = "5"
        FIXTURE.write_tsv(
            path,
            ADAPTER.step08.STEP08_SUMMARY_HEADER,
            rows,
        )
    elif step_id == "09":
        path = artifact_fixture.source_for("analysis.synthetic.mutation_spectrum_tsv")
        rows = read_tsv(path)
        rows[0]["candidate_count"] = "5"
        FIXTURE.write_tsv(
            path,
            ADAPTER.step09.STEP09_MUTATION_HEADER,
            rows,
        )
    else:
        path = artifact_fixture.source_for("review.synthetic.review_summary")
        rows = read_tsv(path)
        rows[0]["step09_summary_sha256"] = "9" * 64
        FIXTURE.write_tsv(
            path,
            ADAPTER.review_package.REVIEW_SUMMARY_HEADER,
            rows,
        )

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    marker = record_for(artifact_fixture, marker_artifact)
    sibling = record_for(artifact_fixture, sibling_artifact)
    assert marker["completion_status"] == "failed"
    assert [entry["code"] for entry in marker["errors"]] == [
        "native_transaction_inconsistent"
    ]
    assert sibling["completion_status"] == "incomplete"
    if step_id == "09c":
        assert marker["scientific_state"] is None
        assert sibling["scientific_state"] is None


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
        ADAPTER.publish_context(context_for(artifact_fixture))
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
    with pytest.raises(ADAPTER.ArtifactIndexError, match=expected):
        ADAPTER.publish_context(context)

    if replacement:
        assert owned_snapshot(artifact_fixture) == before
        assert not artifact_fixture.lock_path.exists()
    else:
        assert_no_owned_outputs(artifact_fixture)


def test_inventory_revision_creates_new_attempt_without_changing_run_identity(
    artifact_fixture: Any,
) -> None:
    first = run_cli(artifact_fixture, execute=True)
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
        ADAPTER.contracts.INVENTORY_HEADER,
        revised,
    )

    second = run_cli(artifact_fixture, execute=True)

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
        ADAPTER.contracts.INVENTORY_HEADER,
        reordered,
    )
    receipt_path = artifact_fixture.source_for("cohort.synthetic.p1.receipt")
    receipt_rows = read_tsv(receipt_path)
    receipt_rows[0]["sample_count"] = "2"
    FIXTURE.write_tsv(
        receipt_path,
        ADAPTER.STEP07_RECEIPT_HEADER,
        receipt_rows,
    )

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    step07 = record_for(
        artifact_fixture,
        "cohort.synthetic.p1.receipt",
    )
    step08 = record_for(
        artifact_fixture,
        "cohort.synthetic.step08_summary",
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

    result = run_cli(artifact_fixture, execute=True)

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

    result = run_cli(artifact_fixture, execute=True)

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
    FIXTURE.write_tsv(counts, ADAPTER.STEP06_COUNTS_HEADER, rows)

    result = run_cli(artifact_fixture, execute=True)

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

    result = run_cli(artifact_fixture, execute=True)

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

    first = run_cli(artifact_fixture, execute=True)

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
        ADAPTER.step09.STEP09_MUTATION_HEADER,
        spectrum_rows,
    )

    second = run_cli(second_fixture, execute=True)

    assert second.returncode == 0, second.stderr
    assert (
        record_for(
            second_fixture,
            "analysis.synthetic.cmh_summary",
        )["completion_status"]
        == "failed"
    )


def test_step09c_cannot_self_declare_exploratory_completion(
    artifact_fixture: Any,
) -> None:
    plan_path = artifact_fixture.source_for("review.synthetic.review_plan")
    plan_rows = read_tsv(plan_path)
    plan_rows[0]["overall_science_status"] = "science_review_complete_exploratory"
    plan_rows[0]["review_completed_date"] = "2026-01-01"
    FIXTURE.write_tsv(
        plan_path,
        ADAPTER.review_package.REVIEW_PLAN_HEADER,
        plan_rows,
    )
    summary_path = artifact_fixture.source_for("review.synthetic.review_summary")
    summary_rows = read_tsv(summary_path)
    summary_rows[0]["overall_science_status"] = "science_review_complete_exploratory"
    summary_rows[0]["review_completed_date"] = "2026-01-01"
    summary_rows[0]["review_plan_sha256"] = sha256_file(plan_path)
    FIXTURE.write_tsv(
        summary_path,
        ADAPTER.review_package.REVIEW_SUMMARY_HEADER,
        summary_rows,
    )

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = record_for(
        artifact_fixture,
        "review.synthetic.review_summary",
    )
    assert summary["completion_status"] == "failed"
    assert summary["scientific_state"] is None


def test_step09c_requires_every_explicit_evidence_category(
    artifact_fixture: Any,
) -> None:
    evidence_index = artifact_fixture.source_for("review.synthetic.evidence_index")
    evidence_rows = read_tsv(evidence_index)[:1]
    FIXTURE.write_tsv(
        evidence_index,
        ADAPTER.review_package.EVIDENCE_INDEX_HEADER,
        evidence_rows,
    )
    summary_path = artifact_fixture.source_for("review.synthetic.review_summary")
    summary_rows = read_tsv(summary_path)
    summary_rows[0]["evidence_record_count"] = "1"
    summary_rows[0]["evidence_manifest_row_count"] = "1"
    FIXTURE.write_tsv(
        summary_path,
        ADAPTER.review_package.REVIEW_SUMMARY_HEADER,
        summary_rows,
    )

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = record_for(
        artifact_fixture,
        "review.synthetic.review_summary",
    )
    assert summary["completion_status"] == "failed"
    assert summary["scientific_state"] is None


def test_step09c_complete_evidence_cannot_point_to_empty_payload(
    artifact_fixture: Any,
) -> None:
    evidence_index = artifact_fixture.source_for("review.synthetic.evidence_index")
    evidence_rows = read_tsv(evidence_index)
    orientation = evidence_rows[0]
    assert orientation["evidence_category"] == "orientation_locus_audit"
    orientation.update(
        {
            "source_path": "/synthetic/orientation.tsv",
            "declared_sha256": "a" * 64,
            "observed_sha256": "a" * 64,
            "declared_row_count": "0",
            "observed_row_count": "0",
            "evidence_status": "complete",
            "evidence_date": "2026-01-01",
        }
    )
    FIXTURE.write_tsv(
        evidence_index,
        ADAPTER.review_package.EVIDENCE_INDEX_HEADER,
        evidence_rows,
    )
    summary_path = artifact_fixture.source_for("review.synthetic.review_summary")
    summary_rows = read_tsv(summary_path)
    summary_rows[0]["orientation_locus_audit_status"] = "complete"
    summary_rows[0]["evidence_source_count"] = "1"
    FIXTURE.write_tsv(
        summary_path,
        ADAPTER.review_package.REVIEW_SUMMARY_HEADER,
        summary_rows,
    )

    result = run_cli(artifact_fixture, execute=True)

    assert result.returncode == 0, result.stderr
    summary = record_for(
        artifact_fixture,
        "review.synthetic.review_summary",
    )
    assert summary["completion_status"] == "failed"
    assert summary["scientific_state"] is None


def test_first_publication_rollback_fsync_failure_retains_recovery_lock(
    artifact_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", FIXED_EPOCH)
    context = context_for(artifact_fixture)
    real_validate = ADAPTER.validate_published_transaction
    real_fsync_directory = ADAPTER.fsync_directory
    output_sync_count = 0

    def fail_post_publication_validation(**kwargs: Any) -> None:
        if kwargs["require_current_source_locations"]:
            raise ADAPTER.ArtifactIndexError(
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

    monkeypatch.setattr(
        ADAPTER,
        "validate_published_transaction",
        fail_post_publication_validation,
    )
    monkeypatch.setattr(ADAPTER, "fsync_directory", fail_rollback_sync)

    with pytest.raises(
        ADAPTER.ArtifactIndexError,
        match="rollback was incomplete",
    ):
        ADAPTER.publish_context(context)

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
    real_sha256_file = ADAPTER.contracts.sha256_file
    rehashed_sources: list[Path] = []

    def track_hash(path: Path) -> str:
        resolved = Path(path).resolve()
        if resolved in source_paths:
            rehashed_sources.append(resolved)
        return real_sha256_file(path)

    monkeypatch.setattr(ADAPTER.contracts, "sha256_file", track_hash)

    ADAPTER.publish_context(context)

    assert rehashed_sources == []
