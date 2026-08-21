"""Layering and environment-admission contracts for launcher configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from norad.orchestration.local_pilot import launcher_config
from norad.orchestration.local_pilot.launcher_config import (
    LauncherOverrides,
    load_launcher_plan,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CSU_VIKING_EV_PUM1_LAUNCHER = (
    REPO_ROOT / "configs/local_pilot_launcher.csu_viking_ev_pum1.yaml"
)


@dataclass(frozen=True, slots=True)
class LauncherFixture:
    source_checkout: Path
    launcher_root: Path
    config: Path
    log_dir: Path
    request: Path
    workspace: Path
    runtime_profile: Path
    scratch_parent: Path


def _fixture(tmp_path: Path) -> LauncherFixture:
    source_checkout = tmp_path / "checkout"
    source_checkout.mkdir()
    launcher_root = tmp_path / "launcher"
    launcher_root.mkdir()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    scratch_parent = tmp_path / "scratch"
    scratch_parent.mkdir()
    request = tmp_path / "request.yaml"
    request.write_text("request placeholder\n", encoding="utf-8")
    runtime_profile = tmp_path / "runtime.tsv"
    runtime_profile.write_text("runtime placeholder\n", encoding="utf-8")
    return LauncherFixture(
        source_checkout=source_checkout,
        launcher_root=launcher_root,
        config=launcher_root / "norad.launcher.yaml",
        log_dir=log_dir,
        request=request,
        workspace=tmp_path / "workspace",
        runtime_profile=runtime_profile,
        scratch_parent=scratch_parent,
    )


def _write_config(fixture: LauncherFixture, fragment: str = "") -> Path:
    fixture.config.write_text(
        "schema_version: norad.local-pilot-launcher.v1\n" + fragment,
        encoding="utf-8",
    )
    return fixture.config


def _environment(fixture: LauncherFixture) -> dict[str, str]:
    """Return a complete deterministic environment for packaged env defaults."""

    return {
        "NORAD_SLURM_ACCOUNT": "default-account",
        "NORAD_SLURM_PARTITION": "default-partition",
        "NORAD_SLURM_QOS": "default-qos",
        "NORAD_SLURM_CPUS": "4",
        "NORAD_SLURM_MEMORY": "site-default",
        "NORAD_SLURM_TIME": "00:30:00",
        "NORAD_SLURM_EXCLUSIVE": "0",
        "NORAD_SLURM_NODELIST": "",
        "NORAD_LOG_DIR": str(fixture.log_dir),
        "NORAD_REQUEST": str(fixture.request),
        "NORAD_WORKSPACE": str(fixture.workspace),
        "NORAD_RUNTIME_PROFILE": str(fixture.runtime_profile),
        "NORAD_MODULE_MODE": "none",
        "NORAD_MODULE_INIT": "",
        "NORAD_MODULES": "",
        "NORAD_SCRATCH_PARENT": str(fixture.scratch_parent),
    }


def _load(
    fixture: LauncherFixture,
    *,
    environment: dict[str, str] | None = None,
    overrides: LauncherOverrides = LauncherOverrides(),
):
    return load_launcher_plan(
        launcher_root=fixture.launcher_root,
        source_checkout=fixture.source_checkout,
        environment=_environment(fixture) if environment is None else environment,
        overrides=overrides,
    )


def _write_dotenv(
    fixture: LauncherFixture,
    text: str,
    *,
    mode: int = 0o600,
) -> Path:
    dotenv = fixture.source_checkout / ".env"
    dotenv.write_text(text, encoding="utf-8")
    dotenv.chmod(mode)
    return dotenv


def test_missing_adjacent_launcher_config_uses_packaged_defaults(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)

    plan = _load(fixture)

    assert not fixture.config.exists()
    assert plan.account == "default-account"
    assert plan.partition == "default-partition"
    assert plan.exclusive is False
    assert plan.nodelist is None


def test_tracked_csu_viking_ev_pum1_launcher_matches_outer_allocation(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)

    plan = load_launcher_plan(
        launcher_root=fixture.launcher_root,
        source_checkout=fixture.source_checkout,
        environment=_environment(fixture),
        config_path=CSU_VIKING_EV_PUM1_LAUNCHER,
    )

    assert plan.account == "default-account"
    assert plan.partition == "default-partition"
    assert plan.qos == "default-qos"
    assert plan.cpus_per_task == 256
    assert plan.memory == "site-default"
    assert plan.time == "12:00:00"
    assert plan.exclusive is True
    assert plan.nodelist is None
    assert plan.module_mode == "none"
    assert plan.modules == ()
    assert plan.config_path == CSU_VIKING_EV_PUM1_LAUNCHER.resolve(strict=True)

    command = launcher_config._submission_command(
        plan,
        wrapper=fixture.launcher_root / "run-in-slurm.sh",
        source_checkout=fixture.source_checkout,
        workflow_python=fixture.source_checkout / ".venv/bin/python",
        execute=True,
        live_uid=1234,
        live_user="test-user",
        sbatch="/usr/bin/sbatch",
    )

    assert not any(argument.startswith("--mem=") for argument in command)


def test_launcher_policy_layers_defaults_yaml_and_explicit_parameters(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_config(
        fixture,
        "slurm:\n"
        "  account: yaml-account\n"
        "  memory: 8G\n"
        "  exclusive: true\n",
    )

    plan = _load(
        fixture,
        overrides=LauncherOverrides(account="explicit-account", exclusive=False),
    )

    assert plan.account == "explicit-account"
    assert plan.memory == "8G"
    assert plan.exclusive is False
    assert plan.nodelist is None


def test_launcher_env_refs_prefer_process_environment_then_repo_dotenv(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_config(
        fixture,
        "slurm:\n"
        "  account: {env: NORAD_SLURM_ACCOUNT}\n"
        "  partition: {env: NORAD_SLURM_PARTITION}\n"
        "  exclusive: {env: NORAD_SLURM_EXCLUSIVE}\n"
        "  nodelist: {env: NORAD_SLURM_NODELIST}\n",
    )
    _write_dotenv(
        fixture,
        "NORAD_SLURM_ACCOUNT=dotenv-account\n"
        "NORAD_SLURM_PARTITION=dotenv-partition\n"
        "NORAD_SLURM_EXCLUSIVE=true\n"
        "NORAD_SLURM_NODELIST=compute-test[01-02]\n",
    )
    environment = _environment(fixture)
    environment["NORAD_SLURM_ACCOUNT"] = "process-account"
    environment.pop("NORAD_SLURM_PARTITION")
    environment.pop("NORAD_SLURM_EXCLUSIVE")
    environment.pop("NORAD_SLURM_NODELIST")

    plan = _load(fixture, environment=environment)

    assert plan.account == "process-account"
    assert plan.partition == "dotenv-partition"
    assert plan.exclusive is True
    assert plan.nodelist == "compute-test[01-02]"


def test_absent_repo_dotenv_is_allowed_when_process_env_satisfies_refs(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_config(
        fixture,
        "slurm:\n"
        "  account: {env: NORAD_SLURM_ACCOUNT}\n",
    )

    plan = _load(fixture)

    assert not (fixture.source_checkout / ".env").exists()
    assert plan.account == "default-account"


@pytest.mark.parametrize(
    ("fragment", "message"),
    (
        (
            "slurm:\n"
            "  account: first-account\n"
            "  account: second-account\n",
            "Duplicate YAML",
        ),
        ("unknown_launcher_field: value\n", "Additional properties|unknown"),
        (
            "slurm:\n"
            "  account: {env: NORAD_SLURM_ACCOUNT, fallback: unsafe}\n",
            "Additional properties|environment reference",
        ),
        (
            "slurm:\n"
            "  account: {env: bad-name}\n",
            "environment variable|environment reference",
        ),
    ),
)
def test_launcher_yaml_rejects_duplicate_unknown_and_malformed_env_refs(
    tmp_path: Path,
    fragment: str,
    message: str,
) -> None:
    fixture = _fixture(tmp_path)
    _write_config(fixture, fragment)

    with pytest.raises(ValueError, match=message):
        _load(fixture)


def test_shell_shaped_scalar_is_never_interpolated_or_executed(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    sentinel = tmp_path / "interpolated"
    _write_config(
        fixture,
        "slurm:\n"
        f'  account: "$(touch {sentinel})"\n',
    )

    with pytest.raises(ValueError) as failure:
        _load(fixture)

    assert not sentinel.exists()
    assert "default-account" not in str(failure.value)


@pytest.mark.parametrize(
    ("contents", "message"),
    (
        (
            "NORAD_SLURM_ACCOUNT=first\nNORAD_SLURM_ACCOUNT=second\n",
            "duplicate|Duplicate",
        ),
        ("NORAD_UNSUPPORTED_VALUE=private-value\n", "unknown|unsupported"),
        ("export NORAD_SLURM_ACCOUNT=private-value\n", "NAME=VALUE|variable"),
        ("NORAD_SLURM_ACCOUNT=private-value\r\n", "carriage return|CRLF"),
    ),
)
def test_repo_dotenv_rejects_duplicate_unknown_and_shell_syntax(
    tmp_path: Path,
    contents: str,
    message: str,
) -> None:
    fixture = _fixture(tmp_path)
    _write_config(
        fixture,
        "slurm:\n"
        "  account: {env: NORAD_SLURM_ACCOUNT}\n",
    )
    _write_dotenv(fixture, contents)
    environment = _environment(fixture)
    environment.pop("NORAD_SLURM_ACCOUNT")

    with pytest.raises(ValueError, match=message) as failure:
        _load(fixture, environment=environment)

    assert "private-value" not in str(failure.value)


def test_repo_dotenv_must_be_a_private_real_file(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_config(
        fixture,
        "slurm:\n"
        "  account: {env: NORAD_SLURM_ACCOUNT}\n",
    )
    environment = _environment(fixture)
    environment.pop("NORAD_SLURM_ACCOUNT")

    _write_dotenv(
        fixture,
        "NORAD_SLURM_ACCOUNT=world-readable\n",
        mode=0o644,
    )
    with pytest.raises(ValueError, match="permissions|mode") as failure:
        _load(fixture, environment=environment)
    assert "world-readable" not in str(failure.value)

    (fixture.source_checkout / ".env").unlink()
    target = tmp_path / "outside.env"
    target.write_text("NORAD_SLURM_ACCOUNT=linked-value\n", encoding="utf-8")
    target.chmod(0o600)
    (fixture.source_checkout / ".env").symlink_to(target)
    with pytest.raises(ValueError, match="symlink|real regular file") as failure:
        _load(fixture, environment=environment)
    assert "linked-value" not in str(failure.value)


def test_missing_referenced_environment_value_fails_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_config(
        fixture,
        "slurm:\n"
        "  account: {env: NORAD_SLURM_ACCOUNT}\n",
    )
    environment = _environment(fixture)
    environment.pop("NORAD_SLURM_ACCOUNT")

    with pytest.raises(ValueError, match="NORAD_SLURM_ACCOUNT"):
        _load(fixture, environment=environment)


def test_log_directory_rejects_slurm_percent_expansion(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    percent_log_dir = tmp_path / "logs-%j"
    percent_log_dir.mkdir()

    with pytest.raises(ValueError, match="percent|%"):
        _load(
            fixture,
            overrides=LauncherOverrides(log_dir=percent_log_dir),
        )


@pytest.mark.parametrize(
    "fragment",
    (
        "execute: true\n",
        "slurm:\n  account: {env: NORAD_EXECUTE}\n",
    ),
)
def test_launcher_yaml_cannot_author_execution(fragment: str, tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    _write_config(fixture, fragment)
    environment = _environment(fixture)
    environment["NORAD_EXECUTE"] = "1"

    with pytest.raises(ValueError, match="execute|NORAD_EXECUTE|environment"):
        _load(fixture, environment=environment)


def test_norad_execute_is_excluded_from_dotenv_process_env_and_overrides(
    tmp_path: Path,
) -> None:
    fixture = _fixture(tmp_path)
    _write_config(fixture)
    environment = _environment(fixture)
    environment["NORAD_EXECUTE"] = "1"

    plan = _load(fixture, environment=environment)

    assert not hasattr(plan, "execute")
    with pytest.raises(TypeError):
        LauncherOverrides(execute=True)  # type: ignore[call-arg]

    _write_dotenv(fixture, "NORAD_EXECUTE=1\n")
    with pytest.raises(ValueError, match="NORAD_EXECUTE|unknown|unsupported"):
        _load(fixture, environment=environment)
