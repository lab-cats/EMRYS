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
