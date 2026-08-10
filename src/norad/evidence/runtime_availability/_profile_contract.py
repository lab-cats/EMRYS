"""Profile parsing and validation for runtime-preflight evidence."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from norad.libraries import validation as report

from ._runtime_model import (
    CHECK_TYPES,
    HASH_PROBES,
    PROFILE_HEADER,
    RUNTIME_CONTEXTS,
    SAFE_ID,
    VISIBILITY_PROBES,
    Check,
    _fail,
)


def _read_regular_file(path: Path, label: str) -> bytes:
    try:
        return report.read_bytes(path, label)
    except report.ValidationError as exc:
        _fail(str(exc).replace("a regular non-symlink file", "a symbolic link"))


def _parse_probe_args(raw: str, row_number: int) -> tuple[str, ...]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail(f"Profile row {row_number} probe_args is not valid JSON: {exc}")
    if not isinstance(value, list) or not all(
        isinstance(item, str) and "\x00" not in item for item in value
    ):
        _fail(f"Profile row {row_number} probe_args must be a JSON array of strings")
    return tuple(value)


def load_profile(path: Path) -> tuple[bytes, list[Check]]:
    data = _read_regular_file(path, "Runtime profile")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        _fail(f"Runtime profile is not UTF-8: {path}: {exc}")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if reader.fieldnames is None:
        _fail("Runtime profile is empty")
    if tuple(reader.fieldnames) != PROFILE_HEADER:
        _fail("Runtime profile header must be exactly: " + "\t".join(PROFILE_HEADER))
    checks: list[Check] = []
    seen: set[str] = set()
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            _fail(f"Runtime profile row {row_number} has extra columns")
        values = {key: value if value is not None else "" for key, value in row.items()}
        if any(
            "\x00" in value or "\n" in value or "\r" in value
            for value in values.values()
        ):
            _fail(f"Runtime profile row {row_number} contains an unsafe character")
        check_id = values["check_id"]
        if not SAFE_ID.fullmatch(check_id):
            _fail(
                f"Runtime profile row {row_number} has invalid check_id: {check_id!r}"
            )
        if check_id in seen:
            _fail(f"Runtime profile has duplicate check_id: {check_id}")
        seen.add(check_id)
        check_type = values["check_type"]
        if check_type not in CHECK_TYPES:
            _fail(
                f"Runtime profile row {row_number} has invalid check_type: {check_type}"
            )
        runtime_context = values["runtime_context"]
        if runtime_context not in RUNTIME_CONTEXTS:
            _fail(
                f"Runtime profile row {row_number} has invalid runtime_context: "
                f"{runtime_context}"
            )
        required_raw = values["required"]
        if required_raw not in {"true", "false"}:
            _fail(f"Runtime profile row {row_number} required must be true or false")
        target = values["target"]
        expected = values["expected"]
        description = values["description"]
        if not target or not expected or not description:
            _fail(
                f"Runtime profile row {row_number} target, expected, and "
                "description must be nonempty"
            )
        probe_args = _parse_probe_args(values["probe_args"], row_number)
        check = Check(
            check_id=check_id,
            check_type=check_type,
            runtime_context=runtime_context,
            required=required_raw == "true",
            target=target,
            probe_args=probe_args,
            expected=expected,
            description=description,
        )
        _validate_check_contract(check, row_number)
        checks.append(check)
    if not checks:
        _fail("Runtime profile must contain at least one check")
    return data, checks


def _validate_regex(pattern: str, row_number: int) -> None:
    try:
        re.compile(pattern)
    except re.error as exc:
        _fail(f"Runtime profile row {row_number} expected regex is invalid: {exc}")


def _validate_check_contract(check: Check, row_number: int) -> None:
    if check.check_type == "tool_version":
        if not check.probe_args:
            _fail(f"Runtime profile row {row_number} tool_version needs probe_args")
        _validate_regex(check.expected, row_number)
    elif check.check_type == "r_namespace":
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9.]*", check.target) is None:
            _fail(
                f"Runtime profile row {row_number} r_namespace target "
                "must be an R package name"
            )
        if len(check.probe_args) != 1 or not check.probe_args[0]:
            _fail(
                f"Runtime profile row {row_number} r_namespace probe_args must "
                "contain exactly one Rscript executable"
            )
        _validate_regex(check.expected, row_number)
    elif check.check_type == "hash_utility":
        if len(check.probe_args) != 1 or check.probe_args[0] not in HASH_PROBES:
            _fail(
                f"Runtime profile row {row_number} hash_utility probe_args must "
                f"contain one of: {', '.join(sorted(HASH_PROBES))}"
            )
        if check.expected != "sha256":
            _fail(
                f"Runtime profile row {row_number} hash_utility expected must be sha256"
            )
    elif check.check_type == "path_visibility":
        if not Path(check.target).is_absolute():
            _fail(
                f"Runtime profile row {row_number} path_visibility target "
                "must be absolute"
            )
        if len(check.probe_args) != 1 or check.probe_args[0] not in VISIBILITY_PROBES:
            _fail(
                f"Runtime profile row {row_number} path_visibility probe_args "
                f"must contain one of: {', '.join(sorted(VISIBILITY_PROBES))}"
            )
        expected = (
            "executable"
            if check.probe_args and check.probe_args[0] == "executable"
            else "readable"
        )
        if check.expected != expected:
            _fail(
                f"Runtime profile row {row_number} path_visibility expected "
                f"must be {expected}"
            )
