"""Side-effect-free application-log controls."""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

EMRYS_LOG_ROOT = "EMRYS_LOG_ROOT"
ControlSource = Literal["command_line", "environment", "default"]


class LogControlError(ValueError):
    """A logging control is empty, unknown, or unsafe."""


@dataclass(frozen=True, slots=True)
class LogControls:
    """Resolved controls passed from an operation owner to its delegates."""

    verbose: bool
    root: Path
    root_source: ControlSource

    def __post_init__(self) -> None:
        if not isinstance(self.verbose, bool):
            raise LogControlError("verbose control must be resolved")
        if not isinstance(self.root, Path):
            raise LogControlError("log root must be resolved")
        _absolute_path(self.root)
        if self.root_source not in ("command_line", "environment", "default"):
            raise LogControlError("log-control source is invalid")


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

    add_verbose_argument(parser)
    add_log_root_argument(parser)


def add_verbose_argument(parser: argparse.ArgumentParser) -> None:
    """Add the sole public switch for expanded human-readable output."""
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show operational paths, identities, commands, and diagnostic detail.",
    )


def add_log_root_argument(parser: argparse.ArgumentParser) -> None:
    """Add only the log-root selector for read-only diagnostic consumers."""

    parser.add_argument(
        "--log-root",
        default=None,
        type=_nonempty,
        action=_UniqueControl,
        metavar="PATH",
    )


def resolve_log_controls(
    *,
    verbose: bool = False,
    cli_root: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
    default_root: Path,
) -> LogControls:
    """Resolve command line, environment, then the operation-owned default."""

    default_root = _absolute_path(default_root)
    root, root_source = resolve_log_root(
        cli_root=cli_root, environment=environment, default_root=default_root
    )
    return LogControls(verbose, root, root_source)


def resolve_log_root(
    *,
    cli_root: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
    default_root: Path,
) -> tuple[Path, ControlSource]:
    """Resolve one search or writing root without inspecting or creating it."""

    environ = os.environ if environment is None else environment
    if cli_root is not None:
        return _absolute_path(cli_root), "command_line"
    if (environment_root := environ.get(EMRYS_LOG_ROOT)) is not None:
        return _absolute_path(environment_root), "environment"
    return _absolute_path(default_root), "default"


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
