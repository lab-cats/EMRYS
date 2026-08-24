"""Layering and safety contracts for local-pilot execution resources."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from norad.orchestration.local_pilot.resource_policy import (
    ADJACENT_CONFIG_NAME,
    AllocationCapacity,
    ResourceConfigError,
    ResourceOverrides,
    add_resource_arguments,
    load_resource_plan,
    overrides_from_args,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CSU_VIKING_EV_PUM1_CONFIG = (
    REPO_ROOT / "configs/local_pilot_resources.csu_viking_ev_pum1.yaml"
)


def _request(tmp_path: Path) -> Path:
    request = tmp_path / "request.yaml"
    request.write_text("request placeholder\n", encoding="utf-8")
    return request


def _allocation(*, cores: int = 8, memory_mb: int = 16_384) -> AllocationCapacity:
    return AllocationCapacity(
        cores=cores,
        memory_mb=memory_mb,
        source="test allocation",
    )


def test_missing_adjacent_config_uses_packaged_conservative_defaults(
    tmp_path: Path,
) -> None:
    plan = load_resource_plan(_request(tmp_path), _allocation())

    assert plan.workflow_cores == 4
    assert plan.workflow_memory_mb == 16_384
    assert set(plan.concurrency_map().values()) == {1}
    assert plan.thread_map() == {"00a": 4, "01": 4, "02": 1, "06": 4, "08": 1}
    assert set(plan.stage_memory_map().values()) == {16_384}
    assert set(plan.reporting_memory_map().values()) == {16_384}
    assert plan.config_path is None
    assert plan.config_sha256 is None
    assert plan.override_labels == ()


def test_adjacent_config_overrides_defaults_and_cli_overrides_both(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    config = tmp_path / ADJACENT_CONFIG_NAME
    config.write_text(
        "schema_version: norad.local-pilot-resources.v1\n"
        "workflow_cores: 6\n"
        "workflow_memory_mb: 12000\n"
        "stage_concurrency:\n"
        '  "01": 2\n'
        "step_threads:\n"
        '  "01": 3\n'
        "stage_memory_mb:\n"
        '  "01": 4000\n',
        encoding="utf-8",
    )

    plan = load_resource_plan(
        request,
        _allocation(),
        overrides=ResourceOverrides(
            workflow_cores=8,
            stage_concurrency=(("01", 4),),
            step_threads=(("01", 2),),
            stage_memory_mb=(("01", 3000),),
        ),
    )

    assert plan.workflow_cores == 8
    assert plan.workflow_memory_mb == 12_000
    assert plan.concurrency_for("01") == 4
    assert plan.threads_for("01") == 2
    assert plan.memory_for("01") == 3000
    assert plan.config_path == config.resolve(strict=True)
    assert plan.override_labels == (
        "workflow_cores",
        "stage_concurrency.01",
        "step_threads.01",
        "stage_memory_mb.01",
    )


def test_tracked_csu_viking_ev_pum1_policy_matches_retained_benchmark() -> None:
    plan = load_resource_plan(
        REPO_ROOT / "configs/local_pilot_request.example.yaml",
        _allocation(cores=256, memory_mb=524_288),
        config_path=CSU_VIKING_EV_PUM1_CONFIG,
    )

    assert plan.workflow_cores == 12
    assert plan.workflow_memory_mb == 524_288
    assert plan.concurrency_map() == {
        "01": 6,
        "02": 6,
        "02b": 6,
        "03": 6,
        "04": 4,
        "05": 6,
        "06": 6,
        "07": 12,
    }
    assert plan.thread_map() == {"00a": 12, "01": 2, "02": 1, "06": 1, "08": 4}
    assert plan.stage_memory_map() == {
        "00a": 262_144,
        "00b": 16_384,
        "00c": 16_384,
        "01": 40_960,
        "02": 4_096,
        "02b": 2_048,
        "03": 4_096,
        "04": 32_768,
        "05": 16_384,
        "06": 4_096,
        "07": 8_192,
        "08": 65_536,
        "09": 16_384,
        "10": 32_768,
    }
    assert plan.reporting_memory_map() == {
        "artifact_index": 8_192,
        "run_summary": 16_384,
        "html_report": 16_384,
    }
    assert plan.sha256 == (
        "3f5767f4878cbc9878d21798ef385daea850a1e539fba66b80e8537cdfa2a2e8"
    )
    assert plan.config_sha256 == (
        "dd629f5d6d0072a2ccfa7f9114a85f13e8a2fef00f561db0831cf464fb1720c1"
    )


@pytest.mark.parametrize(
    ("allocation", "overrides", "message"),
    (
        (
            _allocation(cores=4),
            ResourceOverrides(workflow_cores=5),
            "Workflow cores exceed observed allocation: 5 > 4",
        ),
        (
            _allocation(memory_mb=8192),
            ResourceOverrides(workflow_memory_mb=8193),
            "Workflow memory exceeds observed allocation: 8193 > 8192 MiB",
        ),
    ),
)
def test_workflow_capacity_cannot_exceed_observed_allocation(
    tmp_path: Path,
    allocation: AllocationCapacity,
    overrides: ResourceOverrides,
    message: str,
) -> None:
    with pytest.raises(ResourceConfigError, match=message):
        load_resource_plan(
            _request(tmp_path),
            allocation,
            overrides=overrides,
        )


@pytest.mark.parametrize(
    ("fragment", "message"),
    (
        (
            "workflow_cores: 4\nstage_concurrency:\n  '01': 2\n"
            "step_threads:\n  '01': 3\n",
            "concurrency x threads exceeds workflow cores",
        ),
        (
            "workflow_memory_mb: 4096\nstage_concurrency:\n  '01': 2\n"
            "step_threads:\n  '01': 1\n"
            "stage_memory_mb:\n  '01': 3072\n",
            "concurrency x memory exceeds workflow memory",
        ),
    ),
)
def test_resolved_policy_rejects_stage_oversubscription(
    tmp_path: Path,
    fragment: str,
    message: str,
) -> None:
    request = _request(tmp_path)
    (tmp_path / ADJACENT_CONFIG_NAME).write_text(
        "schema_version: norad.local-pilot-resources.v1\n" + fragment,
        encoding="utf-8",
    )

    with pytest.raises(ResourceConfigError, match=message):
        load_resource_plan(request, _allocation())


def test_duplicate_cli_assignment_is_rejected() -> None:
    with pytest.raises(ResourceConfigError, match="Duplicate command-line"):
        ResourceOverrides(stage_concurrency=(("01", 2), ("01", 3)))


def test_explicit_missing_config_does_not_fall_back_to_defaults(tmp_path: Path) -> None:
    with pytest.raises(ResourceConfigError, match="Could not read resource"):
        load_resource_plan(
            _request(tmp_path),
            _allocation(),
            config_path=tmp_path / "missing.yaml",
        )


def test_resource_yaml_rejects_duplicate_and_unknown_keys(tmp_path: Path) -> None:
    request = _request(tmp_path)
    config = tmp_path / ADJACENT_CONFIG_NAME
    config.write_text(
        "schema_version: norad.local-pilot-resources.v1\n"
        "workflow_cores: 4\n"
        "workflow_cores: 5\n",
        encoding="utf-8",
    )
    with pytest.raises(ResourceConfigError, match="Duplicate YAML"):
        load_resource_plan(request, _allocation())

    config.write_text(
        "schema_version: norad.local-pilot-resources.v1\nunknown: 1\n",
        encoding="utf-8",
    )
    with pytest.raises(ResourceConfigError, match="Additional properties"):
        load_resource_plan(request, _allocation())


def test_repeatable_cli_parameters_project_as_highest_precedence_overrides() -> None:
    parser = argparse.ArgumentParser()
    add_resource_arguments(parser)

    arguments = parser.parse_args(
        [
            "--workflow-cores",
            "8",
            "--stage-concurrency",
            "01=4",
            "--step-threads",
            "01=2",
            "--stage-memory-mb",
            "01=3000",
            "--reporting-memory-mb",
            "html_report=1000",
        ]
    )

    assert overrides_from_args(arguments) == ResourceOverrides(
        workflow_cores=8,
        stage_concurrency=(("01", 4),),
        step_threads=(("01", 2),),
        stage_memory_mb=(("01", 3000),),
        reporting_memory_mb=(("html_report", 1000),),
    )
