from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path

import pytest

from emrys.contracts.artifacts import api as artifact_contracts
from emrys.contracts.orchestration import api as orchestration_contracts
from emrys.contracts.orchestration.projection import project_reporting
from tests.orchestration.local_pilot import fixture


def test_reporting_projection_is_exact_deterministic_and_legacy_compatible(
    tmp_path: Path,
) -> None:
    _request, execution, _execution_bytes = fixture.build_legacy_execution(
        tmp_path / "request-root"
    )
    bundle = project_reporting(execution, fixture.profile())

    assert tuple(bundle.reporting_run_contract) == (
        "run_contract_sha256",
        *artifact_contracts.RUN_CONTRACT_COMPONENT_FIELDS,
    )
    artifact_contracts.validate_run_contract(
        bundle.reporting_run_contract, "B2 projection test"
    )
    assert bundle.reporting_run_contract["reference_contract_sha256"] == (
        hashlib.sha256(bundle.reference_contract_bytes).hexdigest()
    )
    assert bundle.reporting_run_contract["primary_analysis_policy_sha256"] == (
        hashlib.sha256(bundle.primary_analysis_policy_bytes).hexdigest()
    )
    assert bundle.projection_references == execution["reporting_projection"]
    assert bundle.artifact_inventory_bytes.endswith(b"\n")
    assert b"\t09c\t" not in bundle.artifact_inventory_bytes
    assert b"scientific_review" not in bundle.artifact_inventory_bytes


def test_execution_rejects_profile_identity_that_only_matches_digest(
    tmp_path: Path,
) -> None:
    profile = fixture.profile()
    _request, execution, _execution_bytes = fixture.build_legacy_execution(
        tmp_path / "request-root", profile
    )
    mutated = json.loads(json.dumps(execution))
    mutated["profile"]["profile_id"] = "wrong.profile"
    mutated["profile"]["profile_version"] = "wrong"
    mutated["identity_envelope"]["profile"] = mutated["profile"]
    digest = orchestration_contracts.canonical_sha256(mutated["identity_envelope"])
    mutated["identity_envelope_sha256"] = digest
    mutated["run_id"] = f"run-{digest}"

    with pytest.raises(
        orchestration_contracts.ContractValidationError,
        match="profile identity does not match",
    ):
        orchestration_contracts.validate_record(
            "execution",
            mutated,
            profile=profile,
        )


def test_inventory_expansion_keeps_each_logical_scope_contiguous(
    tmp_path: Path,
) -> None:
    _request, execution, _execution_bytes = fixture.build_legacy_execution(
        tmp_path / "request-root"
    )
    bundle = project_reporting(execution, fixture.profile())
    inventory = tmp_path / "artifact_inventory.tsv"
    inventory.write_bytes(bundle.artifact_inventory_bytes)

    rows = artifact_contracts.validate_inventory(
        inventory, source_root=tmp_path / "run-root"
    )
    sample_rows = [row for row in rows if row["scope_type"] == "sample"]
    assert [row["scope_id"] for row in sample_rows] == [
        "EV_1",
        "EV_1",
        "PUM1_1",
        "PUM1_1",
        "EV_2",
        "EV_2",
        "PUM1_2",
        "PUM1_2",
    ]
    assert len({row["artifact_id"] for row in rows}) == len(rows)
    assert (
        orchestration_contracts.canonical_json_bytes(bundle.reporting_run_contract)
        == bundle.reporting_run_contract_bytes
    )


def test_inventory_bytes_preserve_row_and_scope_semantics_without_publication(
    tmp_path: Path,
) -> None:
    _request, execution, _execution_bytes = fixture.build_legacy_execution(
        tmp_path / "request-root"
    )
    bundle = project_reporting(execution, fixture.profile())
    reader = csv.DictReader(
        io.StringIO(bundle.artifact_inventory_bytes.decode("utf-8"), newline=""),
        delimiter="\t",
    )
    rows = list(reader)

    assert tuple(reader.fieldnames or ()) == artifact_contracts.INVENTORY_HEADER
    assert rows == list(bundle.artifact_inventory_rows)
    closed: set[tuple[str, str, str]] = set()
    active: tuple[str, str, str] | None = None
    for row in rows:
        scope = artifact_contracts.scope_key(row)
        if scope == active:
            continue
        assert scope not in closed
        if active is not None:
            closed.add(active)
        active = scope


def test_reference_sidecar_templates_can_bind_stationary_external_paths(
    tmp_path: Path,
) -> None:
    profile = fixture.profile()
    profile["artifact_templates"].extend(
        [
            {
                "artifact_id_template": "ref.{reference_id}.fasta",
                "step_id": "00c",
                "scope_type": "reference",
                "scope_selector": "reference",
                "adapter": "step00c_reference_fasta_v1",
                "source_path_template": "{reference_fasta_path}",
                "required": True,
            },
            {
                "artifact_id_template": "ref.{reference_id}.dict",
                "step_id": "00c",
                "scope_type": "reference",
                "scope_selector": "reference",
                "adapter": "step00c_reference_dict_v1",
                "source_path_template": "{reference_dict_path}",
                "required": True,
            },
        ]
    )
    request, execution, _execution_bytes = fixture.build_legacy_execution(
        tmp_path / "request-root", profile
    )
    bundle = project_reporting(execution, profile)
    by_id = {row["artifact_id"]: row for row in bundle.artifact_inventory_rows}

    fasta = request.parent / "reference" / "genome.fa"
    assert by_id["ref.synthetic_ref.fasta"]["source_path"] == str(fasta)
    assert by_id["ref.synthetic_ref.dict"]["source_path"] == str(
        fasta.with_name("genome.dict")
    )
