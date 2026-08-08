"""Shared dry-run and publication lifecycle for step validators."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from norad.libraries.validation.inputs import Snapshot, require_unchanged
from norad.libraries.validation.publication import publish


@dataclass(frozen=True)
class Runtime:
    step_id: str
    scope_id: str
    check_ids: set[str]
    output: Path
    execute: bool
    published_label: str


def finish(
    runtime: Runtime,
    data: bytes,
    snapshots: dict[Path, Snapshot],
    *,
    before_report: Callable[[], None] | None = None,
) -> int:
    """Print evidence and optionally publish it without changing exit semantics."""

    if before_report is not None:
        before_report()
    print(data.decode(), end="")
    if not runtime.execute:
        print("Dry-run complete; no output was written.")
        return 0
    require_unchanged(snapshots)
    publish(
        runtime.output,
        data,
        runtime.scope_id,
        step_id=runtime.step_id,
        check_ids=runtime.check_ids,
    )
    print(f"Published {runtime.published_label} validation report: {runtime.output}")
    return 0
