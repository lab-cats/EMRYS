from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from emrys.orchestration.local_pilot import execution_profile
from emrys.orchestration.local_pilot.execution_profile import (
    DirectPlacement,
    ExecutionProfileError,
    SlurmPlacement,
    load_execution_profile,
)
from emrys.orchestration.local_pilot.resource_policy import ResourceOverrides

REPO_ROOT = Path(__file__).resolve().parents[3]
RESOURCE_SCHEMA_VERSION = "emrys.local-pilot-resources.v1"


def _write_profile(path: Path, document: dict[str, object]) -> Path:
    path.write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )
    return path


def _slurm_placement(root: Path) -> dict[str, object]:
    return {
        "kind": "slurm",
        "account": "site-account",
        "partition": "compute",
        "qos": None,
        "cpus_per_task": 8,
        "memory_mb": 65536,
        "time": "04:00:00",
        "exclusive": False,
        "nodelist": None,
        "scratch_parent": str(root / "scratch"),
        "modules": {"mode": "none", "init": "", "load": []},
    }


def test_retired_adjacent_sources_require_one_explicit_profile(
    tmp_path: Path,
) -> None:
    request = tmp_path / "request.yaml"
    request.write_text("ignored by profile loading\n", encoding="utf-8")
    retired_names = (
        "emrys.resources.yaml",
        "emrys.launcher.yaml",
        "norad.resources.yaml",
        "norad.launcher.yaml",
    )
    for name in retired_names:
        (tmp_path / name).write_text("not: valid\n", encoding="utf-8")

    with pytest.raises(
        ExecutionProfileError,
        match="Retired adjacent configuration requires migration",
    ) as caught:
        load_execution_profile(request)
    assert all(name in str(caught.value) for name in retired_names)

    profile = load_execution_profile(
        request,
        config_path=execution_profile.DEFAULT_PROFILE_PATH,
    )
    assert isinstance(profile.placement, DirectPlacement)
    assert profile.resource_policy.declaration.workflow_cores == 4
    assert profile.source_path == execution_profile.DEFAULT_PROFILE_PATH
    assert profile.source_raw_sha256 == hashlib.sha256(
        execution_profile.DEFAULT_PROFILE_PATH.read_bytes()
    ).hexdigest()
    assert profile.document()["placement"] == {"kind": "direct"}


def test_selected_resource_fragment_then_explicit_overrides(tmp_path: Path) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "resources": {
                "schema_version": RESOURCE_SCHEMA_VERSION,
                "workflow_cores": 6,
                "step_threads": {"00a": 6},
            },
        },
    )

    profile = load_execution_profile(
        tmp_path / "request.yaml",
        config_path=selected,
        resource_overrides=ResourceOverrides(
            workflow_cores=8,
            step_threads=(("00a", 8),),
        ),
    )

    assert isinstance(profile.placement, DirectPlacement)
    assert profile.resource_policy.declaration.workflow_cores == 8
    assert dict(profile.resource_policy.declaration.step_threads)["00a"] == 8
    assert profile.resource_policy.override_labels == (
        "workflow_cores",
        "step_threads.00a",
    )
    assert profile.resource_policy.config_path == selected
    assert (
        profile.resource_policy.config_sha256
        == hashlib.sha256(selected.read_bytes()).hexdigest()
    )
def test_placement_only_profile_does_not_change_resource_policy(
    tmp_path: Path,
) -> None:
    direct = load_execution_profile(tmp_path / "request.yaml")
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )

    scheduled = load_execution_profile(
        tmp_path / "request.yaml",
        config_path=selected,
    )

    assert isinstance(scheduled.placement, SlurmPlacement)
    assert scheduled.placement.cpus_per_task == 8
    assert scheduled.resource_policy.document() == direct.resource_policy.document()
    assert (
        scheduled.resource_policy.declaration.identity_document()
        == direct.resource_policy.declaration.identity_document()
    )
    assert scheduled.resource_policy.config_path is None
    assert "placement" not in scheduled.resource_policy.document()
    assert scheduled.sha256 != direct.sha256


def test_attempt_placement_projects_direct_and_slurm_provenance(
    tmp_path: Path,
) -> None:
    direct = load_execution_profile(tmp_path / "request.yaml")

    assert direct.source_path.is_absolute()
    assert (
        direct.source_raw_sha256
        == hashlib.sha256(direct.source_path.read_bytes()).hexdigest()
    )
    assert direct.attempt_placement() == {
        "kind": "direct",
        "source": {
            "path": str(direct.source_path),
            "sha256": direct.source_raw_sha256,
        },
        "effective_sha256": direct.sha256,
        "request": {"kind": "direct"},
        "scheduler_job_id": None,
    }

    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )
    scheduled = load_execution_profile(
        tmp_path / "request.yaml",
        config_path=selected,
    )

    assert scheduled.source_path == selected
    assert (
        scheduled.source_raw_sha256 == hashlib.sha256(selected.read_bytes()).hexdigest()
    )
    assert scheduled.attempt_placement("700123") == {
        "kind": "slurm",
        "source": {
            "path": str(selected),
            "sha256": scheduled.source_raw_sha256,
        },
        "effective_sha256": scheduled.sha256,
        "request": scheduled.placement.document(),
        "scheduler_job_id": "700123",
    }


@pytest.mark.parametrize("job_id", ("", "0", "00", "01", "-1", "1.0", " 1", 1, True))
def test_attempt_placement_rejects_noncanonical_job_ids(
    tmp_path: Path,
    job_id: object,
) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )
    profile = load_execution_profile(
        tmp_path / "request.yaml",
        config_path=selected,
    )

    with pytest.raises(ExecutionProfileError, match="canonical positive decimal"):
        profile.attempt_placement(job_id)  # type: ignore[arg-type]


def test_selected_source_digest_is_admitted(tmp_path: Path) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": {"kind": "direct"},
        },
    )
    expected = load_execution_profile(
        tmp_path / "request.yaml",
        config_path=selected,
    ).sha256

    profile = load_execution_profile(
        tmp_path / "request.yaml",
        config_path=selected,
        expected_sha256=expected,
    )

    assert profile.sha256 == expected
    assert profile.source_path == selected
    assert profile.source_raw_sha256 == hashlib.sha256(selected.read_bytes()).hexdigest()
    with pytest.raises(ExecutionProfileError, match="SHA-256 differs"):
        load_execution_profile(
            tmp_path / "request.yaml",
            config_path=selected,
            expected_sha256="0" * 64,
        )
    with pytest.raises(ExecutionProfileError, match="64 lowercase hex"):
        load_execution_profile(
            tmp_path / "request.yaml",
            config_path=selected,
            expected_sha256="invalid",
        )


def test_builtin_source_digest_can_be_bound(tmp_path: Path) -> None:
    expected = load_execution_profile(tmp_path / "request.yaml").sha256

    profile = load_execution_profile(
        tmp_path / "request.yaml",
        expected_sha256=expected,
    )

    assert profile.sha256 == expected


def test_selected_profile_must_be_one_stable_real_file(tmp_path: Path) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {"schema_version": execution_profile.SCHEMA_VERSION},
    )
    link = tmp_path / "profile-link.yaml"
    link.symlink_to(selected)

    with pytest.raises(ExecutionProfileError, match="canonical and nonsymlink"):
        load_execution_profile(
            tmp_path / "request.yaml",
            config_path=link,
        )


@pytest.mark.parametrize(
    ("text", "message"),
    (
        (
            "schema_version: emrys.execution-profile.v1\n"
            "schema_version: emrys.execution-profile.v1\n",
            "Duplicate YAML mapping key",
        ),
        (
            "schema_version: emrys.execution-profile.v1\n"
            "base: &base\n  kind: direct\n"
            "placement:\n  <<: *base\n",
            "YAML merge keys are not allowed",
        ),
        (
            "schema_version: emrys.execution-profile.v1\nunknown: true\n",
            "execution profile",
        ),
        (
            "schema_version: emrys.execution-profile.v1\n"
            "resources:\n"
            "  schema_version: emrys.local-pilot-resources.v1\n"
            "  workflow_cores: true\n",
            "execution profile",
        ),
        (
            "schema_version: emrys.execution-profile.v1\n"
            "resources:\n"
            "  schema_version: emrys.local-pilot-resources.v1\n"
            "  workflow_cores: {env: EMRYS_SLURM_CPUS}\n",
            "execution profile",
        ),
    ),
)
def test_profile_yaml_is_closed_without_environment_references(
    tmp_path: Path,
    text: str,
    message: str,
) -> None:
    selected = tmp_path / "profile.yaml"
    selected.write_text(text, encoding="utf-8")

    with pytest.raises(ExecutionProfileError, match=message):
        load_execution_profile(
            tmp_path / "request.yaml",
            config_path=selected,
        )


@pytest.mark.parametrize(
    ("relative_path", "workflow_cores", "cpus_per_task", "exclusive"),
    (
        ("configs/execution_profile.example.yaml", 4, 4, False),
        ("configs/execution_profile.csu_viking_ev_pum1.yaml", 12, 256, True),
    ),
)
def test_tracked_execution_profile_examples_are_admissible(
    relative_path: str,
    workflow_cores: int,
    cpus_per_task: int,
    exclusive: bool,
) -> None:
    profile = load_execution_profile(
        REPO_ROOT / "configs/local_pilot_request.example.yaml",
        config_path=REPO_ROOT / relative_path,
    )

    assert isinstance(profile.placement, SlurmPlacement)
    assert profile.resource_policy.declaration.workflow_cores == workflow_cores
    assert profile.placement.cpus_per_task == cpus_per_task
    assert profile.placement.exclusive is exclusive
    assert profile.placement.memory_mb is None


def test_exact_module_realization_is_typed(tmp_path: Path) -> None:
    placement = _slurm_placement(tmp_path)
    placement["modules"] = {
        "mode": "exact",
        "init": "/etc/profile.d/modules.sh",
        "load": ["STAR/2.7.11b", "samtools/1.19.2"],
    }
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": placement,
        },
    )

    profile = load_execution_profile(
        tmp_path / "request.yaml",
        config_path=selected,
    )

    assert isinstance(profile.placement, SlurmPlacement)
    assert profile.placement.module_init == Path("/etc/profile.d/modules.sh")
    assert profile.placement.modules == ("STAR/2.7.11b", "samtools/1.19.2")
