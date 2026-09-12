"""Scientific summary projections and evidence from combined reporting publication."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
from emrys.libraries.source_authority import PACKAGE_ROOT
from jsonschema import Draft202012Validator, FormatChecker

from emrys.contracts.artifacts import api as CONTRACTS
from emrys.reporting import transaction_validation as REPORTING_VALIDATION
from emrys.reporting._run_summary import models as RUN_SUMMARY_MODELS
from emrys.reporting._run_summary import projection as RUN_SUMMARY_PROJECTION
from tests.reporting.fixtures.artifact_run_summary_v2 import build_fixture as FIXTURE

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def run_summary_fixture(tmp_path: Path) -> Any:
    return FIXTURE.build_fixture(tmp_path / "fixture")


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

    inventory = Path(document["inventory"]["path"])
    rows = CONTRACTS.validate_inventory(inventory)
    CONTRACTS.reconcile_document_inventory(
        "run-summary",
        document,
        rows,
        inventory,
    )
    return document


def test_execute_publishes_exact_canonical_schema_valid_transaction(
    run_summary_fixture: Any,
) -> None:
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
    assert document["tables"] == [
        {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
        }
        for path in (
            run_summary_fixture.summary_tsv_path,
            run_summary_fixture.qc_summary_path,
        )
    ]
    assert document["schema_version"] == "7.0.0"
    assert document["publication"]["transaction_state"] == "complete"
    assert set(run_summary_fixture.output_dir.iterdir()) == set(
        run_summary_fixture.summary_paths
    )
    assert "scientific_review" not in document
    assert "science_status" not in document
    assert "approved_report_tables" not in document
    assert not run_summary_fixture.lock_path.exists()


def test_qc_view_keeps_all_artifact_metrics(
    run_summary_fixture: Any,
) -> None:
    document = validate_summary_document(run_summary_fixture)
    artifact_metrics = [
        metric for artifact in document["artifacts"] for metric in artifact["metrics"]
    ]
    qc_rows = read_tsv(run_summary_fixture.qc_summary_path)
    source_counts = Counter(metric["metric_id"] for metric in artifact_metrics)
    assert len(qc_rows) == len(artifact_metrics)
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

    rows = RUN_SUMMARY_PROJECTION._build_qc_rows(
        {"run_id": "synthetic_run", "artifacts": [artifact]}
    )

    assert rows[0]["value"] == '"Inf"'
    assert rows[0]["value_type"] == "string"


def test_projection_handles_null_metric_values() -> None:
    assert RUN_SUMMARY_PROJECTION._metric_value_type(None) == "null"


def test_complete_summary_preserves_required_missing_artifact_state(
    tmp_path: Path,
) -> None:
    fixture = FIXTURE.build_missing_fixture(tmp_path / "missing")

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
    assert (
        document["analysis_policy"]["sha256"]
        == document["run_contract"]["primary_analysis_policy_sha256"]
    )


def test_required_artifact_limitation_is_computational_only(tmp_path: Path) -> None:
    fixture = FIXTURE.build_missing_fixture(tmp_path / "collision")
    record = next(
        r
        for r in read_json(fixture.summary_json_path)["artifacts"]
        if r["artifact_id"] == "sample.SYNTH_A.canonical_bai"
    )
    limitations = RUN_SUMMARY_PROJECTION._build_limitations(artifacts=[record])

    assert [row["limitation_id"] for row in limitations] == [
        "required_artifacts_not_complete",
    ]
    assert "scientific" not in limitations[0]["description"].lower()


def test_combined_readmission_keeps_summary_json_and_views_byte_identical(
    run_summary_fixture: Any,
) -> None:
    before = summary_snapshot(run_summary_fixture)

    result = REPORTING_VALIDATION.validate_run_summary_transaction(
        expected_receipt_sha256=hashlib.sha256(
            run_summary_fixture.summary_json_path.read_bytes()
        ).hexdigest(),
        package_root=PACKAGE_ROOT,
        artifact_source_root=run_summary_fixture.root,
        run_id=run_summary_fixture.run_id,
        run_contract=run_summary_fixture.adapter_fixture.run_contract,
        inventory=run_summary_fixture.adapter_fixture.inventory,
        analysis_policy=run_summary_fixture.adapter_fixture.analysis_policy,
        output_root=run_summary_fixture.output_root,
        profile=FIXTURE.ADAPTER_FIXTURE.analysis_profile_v1(),
    )

    assert result.receipt_path == run_summary_fixture.summary_json_path
    assert summary_snapshot(run_summary_fixture) == before
    validate_summary_document(run_summary_fixture)
