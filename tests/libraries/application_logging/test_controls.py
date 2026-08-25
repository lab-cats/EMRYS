from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from emrys.libraries.application_logging.controls import (
    EMRYS_LOG_LEVEL,
    EMRYS_LOG_ROOT,
    LogControlError,
    LogControls,
    LogLevel,
    add_log_arguments,
    resolve_log_controls,
)
from emrys.libraries.source_authority import SourceCheckout


def parser() -> argparse.ArgumentParser:
    selected = argparse.ArgumentParser(prog="emrys operation")
    add_log_arguments(selected)
    return selected


def test_parser_is_side_effect_free_for_valid_and_help_responses(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "logs"
    absent = parser().parse_args([])
    selected = parser().parse_args(["--log-level", "debug", "--log-root", str(root)])
    assert (absent.log_level, absent.log_root) == (None, None)
    assert (selected.log_level, selected.log_root) == ("debug", str(root))
    with pytest.raises(SystemExit) as raised:
        parser().parse_args(["--help"])
    assert raised.value.code == 0
    assert "--log-level {normal,verbose,debug}" in capsys.readouterr().out
    assert not root.exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["--log-level", "quiet"],
        ["--log-root", ""],
        ["--log-level", "normal", "--log-level", "debug"],
        ["--log-root", "/one", "--log-root", "/two"],
    ],
)
def test_parser_rejects_invalid_or_repeated_controls(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        parser().parse_args(arguments)
    assert raised.value.code == 2


def test_resolution_precedence_default_and_scheduler_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = SourceCheckout(tmp_path / "repository")
    environment = {
        EMRYS_LOG_LEVEL: "verbose",
        EMRYS_LOG_ROOT: str(tmp_path / "environment"),
        "SECRET": "ignored",
    }
    cli = resolve_log_controls(
        source_checkout=checkout,
        cli_level="debug",
        cli_root=tmp_path / "cli",
        environment=environment,
    )
    env = resolve_log_controls(source_checkout=checkout, environment=environment)
    unrelated = tmp_path / "cwd"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    default = resolve_log_controls(source_checkout=checkout, environment={})

    assert cli == LogControls(
        LogLevel.DEBUG, tmp_path / "cli", "command_line", "command_line"
    )
    assert env == LogControls(
        LogLevel.VERBOSE, tmp_path / "environment", "environment", "environment"
    )
    assert default.root == checkout.root / "logs" / "application"
    assert default.level is LogLevel.NORMAL
    assert cli.scheduler_environment() == {
        EMRYS_LOG_LEVEL: "debug",
        EMRYS_LOG_ROOT: str(tmp_path / "cli"),
    }
    assert list(unrelated.iterdir()) == []
    with pytest.raises(LogControlError):
        resolve_log_controls(source_checkout=object(), environment={})  # type: ignore[arg-type]
    for invalid in (
        (LogLevel.NORMAL, tmp_path / "logs", "invalid", "default"),
        (LogLevel.NORMAL, tmp_path / "logs", "default", "invalid"),
        ("normal", tmp_path / "logs", "default", "default"),
        (LogLevel.NORMAL, "/logs", "default", "default"),
    ):
        level, root, level_source, root_source = invalid
        with pytest.raises(LogControlError):
            LogControls(level, root, level_source, root_source)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("level", "root"),
    [
        ("", "/logs"),
        ("trace", "/logs"),
        ("normal", ""),
        ("normal", "relative"),
        ("normal", "/logs\x1b"),
    ],
)
def test_resolution_rejects_invalid_controls_without_writes(
    level: str, root: str, tmp_path: Path
) -> None:
    with pytest.raises(LogControlError):
        resolve_log_controls(
            source_checkout=SourceCheckout(tmp_path / "repository"),
            cli_level=level,
            cli_root=root,
            environment={},
        )
    assert list(tmp_path.iterdir()) == []
