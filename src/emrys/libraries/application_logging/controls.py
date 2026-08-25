"""Side-effect-free application-log controls."""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal

from emrys.libraries.source_authority import SourceCheckout

EMRYS_LOG_LEVEL = "EMRYS_LOG_LEVEL"
EMRYS_LOG_ROOT = "EMRYS_LOG_ROOT"
ControlSource = Literal["command_line", "environment", "default"]


class LogControlError(ValueError):
    """A logging control is empty, unknown, or unsafe."""


class LogLevel(StrEnum):
    """Supported console detail levels."""

    NORMAL = "normal"
    VERBOSE = "verbose"
    DEBUG = "debug"


@dataclass(frozen=True, slots=True)
class LogControls:
    """Resolved controls passed from an operation owner to its delegates."""

    level: LogLevel
    root: Path
    level_source: ControlSource
    root_source: ControlSource

    def __post_init__(self) -> None:
        if not isinstance(self.level, LogLevel):
            raise LogControlError("log level must be resolved")
        if not isinstance(self.root, Path):
            raise LogControlError("log root must be resolved")
        _absolute_path(self.root)
        sources = ("command_line", "environment", "default")
        if self.level_source not in sources or self.root_source not in sources:
            raise LogControlError("log-control source is invalid")

    def scheduler_environment(self) -> dict[str, str]:
        """Return only the two controls a scheduler delegate may inherit."""
        return {EMRYS_LOG_LEVEL: self.level.value, EMRYS_LOG_ROOT: str(self.root)}


class _UniqueControl(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f"{option_string} may be specified only once")
        setattr(namespace, self.dest, values)


def add_log_arguments(parser: argparse.ArgumentParser) -> None:
    """Add unresolved, side-effect-free logging flags to a leaf parser."""

    parser.add_argument(
        "--log-level",
        choices=tuple(level.value for level in LogLevel),
        default=None,
        action=_UniqueControl,
    )
    parser.add_argument(
        "--log-root",
        default=None,
        type=_nonempty,
        action=_UniqueControl,
        metavar="PATH",
    )


def resolve_log_controls(
    *,
    source_checkout: SourceCheckout,
    cli_level: str | None = None,
    cli_root: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
) -> LogControls:
    """Resolve command line, environment, then repository-derived defaults."""

    if not isinstance(source_checkout, SourceCheckout):
        raise LogControlError("logging defaults require an admitted SourceCheckout")
    checkout_root = _absolute_path(source_checkout.root)
    environ = dict(os.environ if environment is None else environment)
    level_value, level_source = _select(
        cli_level, environ.get(EMRYS_LOG_LEVEL), LogLevel.NORMAL.value
    )
    root_value, root_source = _select(
        cli_root, environ.get(EMRYS_LOG_ROOT), checkout_root / "logs" / "application"
    )
    try:
        level = LogLevel(_nonempty(level_value))
    except (ValueError, argparse.ArgumentTypeError):
        raise LogControlError("log level must be normal, verbose, or debug") from None
    return LogControls(level, _absolute_path(root_value), level_source, root_source)


def _select(
    cli: object | None, env: object | None, default: object
) -> tuple[object, ControlSource]:
    if cli is not None:
        return cli, "command_line"
    return (env, "environment") if env is not None else (default, "default")


def _nonempty(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise argparse.ArgumentTypeError("must not be empty")
    return value


def _absolute_path(value: object) -> Path:
    if not isinstance(value, (str, Path)) or not value:
        raise LogControlError("log root must be a nonempty filesystem path")
    path = Path(value)
    rendered = str(path)
    try:
        rendered.encode("utf-8")
    except UnicodeEncodeError:
        raise LogControlError("log root must be safe UTF-8 text") from None
    safe = all(character.isprintable() for character in rendered)
    if not path.is_absolute() or not safe:
        raise LogControlError("log root must be an absolute, console-safe path")
    return path
