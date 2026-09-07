from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from emrys.orchestration.run_coordinator import execution_profile
from emrys.orchestration.run_coordinator.execution_profile import (
    DirectPlacement,
    ExecutionProfileError,
    SlurmPlacement,
    load_execution_profile,
)
from emrys.orchestration.run_coordinator.resource_policy import ResourceOverrides

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


def test_project_profile_selection_is_default_named_or_absolute(tmp_path: Path) -> None:
    project = tmp_path / "project.yaml"
    default = tmp_path / "runtime/profiles/default.yaml"
    named = tmp_path / "runtime/profiles/viking.yaml"
    absolute = tmp_path / "external.yaml"
    assert execution_profile.project_execution_profile_path(project, None) == default
    assert execution_profile.project_execution_profile_path(project, "viking") == named
    assert execution_profile.project_execution_profile_path(project, absolute) == absolute
    for invalid in ("nested/viking", "viking.yaml"):
        with pytest.raises(ExecutionProfileError, match="safe Project profile"):
            execution_profile.project_execution_profile_path(project, invalid)

    default.parent.mkdir(parents=True)
    default.write_bytes(execution_profile.PROJECT_DEFAULT_PROFILE_BYTES)
    profile = load_execution_profile(config_path=default)
    assert isinstance(profile.placement, DirectPlacement)
    assert profile.resource_policy.declaration.workflow_cores == 4
    assert profile.source_path == default
    assert not profile.computational_resources_explicit
    assert profile.document()["placement"] == {"kind": "direct"}


def test_default_project_profile_rejects_retired_adjacent_configuration(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project.yaml"
    retired = ("emrys.resources.yaml", "norad.launcher.yaml")
    for name in retired:
        (tmp_path / name).write_text("retired: true\n", encoding="utf-8")

    with pytest.raises(ExecutionProfileError, match="requires migration") as caught:
        execution_profile.project_execution_profile_path(project, None)
    assert all(name in str(caught.value) for name in retired)
    assert execution_profile.project_execution_profile_path(project, "default") == (
        tmp_path / "runtime/profiles/default.yaml"
    )


def test_selected_resource_fragment_then_explicit_overrides(tmp_path: Path) -> None:
    default_sha256 = load_execution_profile().resource_policy.default_sha256
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
    assert profile.resource_policy.default_sha256 == default_sha256
    assert (
        profile.resource_policy.config_sha256
        == hashlib.sha256(selected.read_bytes()).hexdigest()
    )


def test_placement_only_profile_does_not_change_resource_policy(
    tmp_path: Path,
) -> None:
    direct = load_execution_profile()
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": _slurm_placement(tmp_path),
        },
    )

    scheduled = load_execution_profile(config_path=selected)

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
    direct = load_execution_profile()

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
    scheduled = load_execution_profile(config_path=selected)

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
    profile = load_execution_profile(config_path=selected)

    with pytest.raises(ExecutionProfileError, match="canonical positive decimal"):
        profile.attempt_placement(job_id)  # type: ignore[arg-type]


def test_selected_source_binding_is_admitted(tmp_path: Path) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {
            "schema_version": execution_profile.SCHEMA_VERSION,
            "placement": {"kind": "direct"},
        },
    )
    admitted = load_execution_profile(config_path=selected)

    profile = load_execution_profile(
        config_path=selected,
        expected_binding_sha256=admitted.binding_sha256,
    )

    assert profile.binding_sha256 == admitted.binding_sha256
    assert profile.source_path == selected
    assert (
        profile.source_raw_sha256 == hashlib.sha256(selected.read_bytes()).hexdigest()
    )
    with pytest.raises(ExecutionProfileError, match="SHA-256 differs"):
        load_execution_profile(
            config_path=selected,
            expected_binding_sha256="0" * 64,
        )
    with pytest.raises(ExecutionProfileError, match="64 lowercase hex"):
        load_execution_profile(
            config_path=selected,
            expected_binding_sha256="invalid",
        )

    selected.write_bytes(selected.read_bytes() + b"# equivalent rewrite\n")
    rewritten = load_execution_profile(config_path=selected)
    assert rewritten.sha256 == admitted.sha256
    with pytest.raises(ExecutionProfileError, match="binding SHA-256 differs"):
        load_execution_profile(
            config_path=selected,
            expected_binding_sha256=admitted.binding_sha256,
        )


def test_builtin_source_digest_can_be_bound(tmp_path: Path) -> None:
    expected = load_execution_profile().binding_sha256

    profile = load_execution_profile(expected_binding_sha256=expected)

    assert profile.binding_sha256 == expected


def test_selected_profile_must_be_one_stable_real_file(tmp_path: Path) -> None:
    selected = _write_profile(
        tmp_path / "profile.yaml",
        {"schema_version": execution_profile.SCHEMA_VERSION},
    )
    link = tmp_path / "profile-link.yaml"
    link.symlink_to(selected)

    with pytest.raises(ExecutionProfileError, match="canonical and nonsymlink"):
        load_execution_profile(config_path=link)


@pytest.mark.parametrize(
    ("text", "message"),
    (
        (
            "schema_version: emrys.execution-profile.v1\n"
            "schema_version: emrys.execution-profile.v1\n",
            "Duplicate YAML mapping key",
        ),
        (
            "schema_version: emrys.execution-profile.v1\nbase: &base\n  kind: direct\nplacement:\n  <<: *base\n",
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
        load_execution_profile(config_path=selected)


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
    profile = load_execution_profile(config_path=REPO_ROOT / relative_path)

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

    profile = load_execution_profile(config_path=selected)

    assert isinstance(profile.placement, SlurmPlacement)
    assert profile.placement.module_init == Path("/etc/profile.d/modules.sh")
    assert profile.placement.modules == ("STAR/2.7.11b", "samtools/1.19.2")
