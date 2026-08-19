#!/usr/bin/env python3
"""Deterministic no-science backend for the generic local task boundary."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HEADER = (
    "step_id",
    "scope_id",
    "check_id",
    "status",
    "observed",
    "expected",
    "detail",
)


def _publish(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _output(value: str) -> tuple[str, Path]:
    try:
        role, raw_path = value.split("=", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("output must use ROLE=/absolute/path") from exc
    path = Path(raw_path)
    if not role or not path.is_absolute():
        raise argparse.ArgumentTypeError("output must use ROLE=/absolute/path")
    return role, path


def _produce(arguments: argparse.Namespace) -> int:
    for index, (role, path) in enumerate(arguments.output, start=1):
        data = f"NORAD local task test double\nrole={role}\n".encode()
        _publish(path, data)
        if arguments.fail_after == index:
            print(f"producer failed after {role}", file=sys.stderr)
            return arguments.failure_exit
    if arguments.native_receipt is not None:
        receipt = {
            "schema_version": "norad.test-native-receipt.v1",
            "status": "succeeded",
        }
        _publish(
            arguments.native_receipt,
            json.dumps(receipt, separators=(",", ":"), sort_keys=True).encode(),
        )
    if arguments.mutate_input is not None:
        with arguments.mutate_input.open("ab") as stream:
            stream.write(b"mutated-by-test-double\n")
            stream.flush()
            os.fsync(stream.fileno())
    print("producer stdout complete")
    print("producer stderr complete", file=sys.stderr)
    return 0


def _validate(arguments: argparse.Namespace) -> int:
    row = (
        arguments.step_id,
        arguments.scope_id,
        "test_double_contract",
        arguments.status,
        arguments.status,
        "pass",
        "deterministic test-double validation",
    )
    lines = ("\t".join(HEADER), "\t".join(row))
    _publish(arguments.report, ("\n".join(lines) + "\n").encode())
    print("validator stdout complete")
    print("validator stderr complete", file=sys.stderr)
    return arguments.exit_code


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    producer = subparsers.add_parser("producer")
    producer.add_argument("--output", action="append", type=_output, required=True)
    producer.add_argument("--native-receipt", type=Path)
    producer.add_argument("--fail-after", type=int, default=0)
    producer.add_argument("--failure-exit", type=int, default=23)
    producer.add_argument("--mutate-input", type=Path)
    producer.set_defaults(action=_produce)

    validator = subparsers.add_parser("validator")
    validator.add_argument("--report", required=True, type=Path)
    validator.add_argument("--step-id", required=True)
    validator.add_argument("--scope-id", required=True)
    validator.add_argument("--status", choices=("pass", "fail"), default="pass")
    validator.add_argument("--exit-code", type=int, default=0)
    validator.set_defaults(action=_validate)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    return int(arguments.action(arguments))


if __name__ == "__main__":
    raise SystemExit(main())
