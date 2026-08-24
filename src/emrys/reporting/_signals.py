"""Shared publication signal-handler installation and rollback."""

from __future__ import annotations

import signal
from collections.abc import Mapping
from typing import Any


def install(
    error_type: type[Exception],
    interrupt_subject: str,
    restore_subject: str,
) -> dict[int, Any]:
    """Install publication interrupts, restoring partial installs on failure."""
    previous: dict[int, Any] = {}

    def interrupt(signum: int, _frame: Any) -> None:
        try:
            name = signal.Signals(signum).name
        except ValueError:
            name = str(signum)
        raise error_type(
            f"{interrupt_subject} publication interrupted by signal {name}"
        )

    try:
        for signum in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, interrupt)
    except BaseException as exc:
        try:
            restore(previous)
        except BaseException as restore_exc:
            raise error_type(
                f"Could not restore partially installed {restore_subject} "
                f"signal handlers: {restore_exc}"
            ) from exc
        raise
    return previous


def restore(previous: Mapping[int, Any]) -> None:
    for signum, handler in previous.items():
        signal.signal(signum, handler)
