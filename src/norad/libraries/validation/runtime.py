"""Shared dry-run and publication lifecycle for step validators."""

import argparse
import csv
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from norad.libraries.validation.errors import ValidationError
from norad.libraries.validation.inputs import Snapshot, require_unchanged
from norad.libraries.validation.publication import publish

_CAUGHT_ERRORS = (OSError, UnicodeError, csv.Error, ValidationError)


@dataclass(frozen=True)
class Runtime:
    step_id: str
    scope_id: str
    check_ids: set[str]
    output: Path
    execute: bool
    published_label: str


def finish(runtime: Runtime, data: bytes, snapshots: dict[Path, Snapshot], *, before_report: Callable[[], None] | None = None) -> int:
    if before_report is not None: before_report()
    print(data.decode(), end="")
    if not runtime.execute:
        print("Dry-run complete; no output was written.")
        return 0
    require_unchanged(snapshots)
    publish(runtime.output, data, runtime.scope_id, step_id=runtime.step_id, check_ids=runtime.check_ids)
    print(f"Published {runtime.published_label} validation report: {runtime.output}")
    return 0


def run(build: Callable[[], tuple[bytes, dict[Path, Snapshot]]], *, step_id: str, scope_id: str, check_ids: set[str], output: Path, execute: bool, published_label: str, before_report: Callable[[], None] | None = None, caught_errors: tuple[type[BaseException], ...] = _CAUGHT_ERRORS) -> int:
    try:
        return finish(Runtime(step_id, scope_id, check_ids, output, execute, published_label), *build(), before_report=before_report)
    except caught_errors as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def run_from_args(
    args: argparse.Namespace,
    build: Callable[[argparse.Namespace], tuple[bytes, dict[Path, Snapshot]]],
    step_id: str,
    check_ids: set[str],
    *,
    scope_id: str | None = None,
    before_report: Callable[[], None] | None = None,
    caught_errors: tuple[type[BaseException], ...] = _CAUGHT_ERRORS,
) -> int:
    return run(
        lambda: build(args),
        step_id=step_id,
        scope_id=scope_id if scope_id is not None else args.scope_id,
        check_ids=check_ids,
        output=args.output,
        execute=args.execute,
        published_label=f"Step {step_id}",
        before_report=before_report,
        caught_errors=caught_errors,
    )
