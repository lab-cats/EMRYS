"""Strict parsing for the explicit reference-provenance inventory."""

from __future__ import annotations

import csv
from pathlib import Path

from emrys.evidence.reference_provenance._reference_model import (
    PROFILE_HEADER,
    ROLES,
    SAFE_ID,
    SHA256,
    SINGLETON_ROLES,
    Item,
    fail,
)
from emrys.libraries import validation as report


def load_inventory(path: Path, base_dir: Path) -> tuple[bytes, list[Item]]:
    raw = report.read_bytes(path, "Reference inventory")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"Reference inventory is not UTF-8: {exc}")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != PROFILE_HEADER:
        fail("Reference inventory header must be exactly: " + "\t".join(PROFILE_HEADER))
    rows = list(reader)
    if not rows:
        fail("Reference inventory must contain data rows")
    if not base_dir.is_dir() or base_dir.is_symlink():
        fail(f"Reference base directory must be a real directory: {base_dir}")
    base = base_dir.resolve()
    items: list[Item] = []
    ids: set[str] = set()
    paths: set[Path] = set()
    role_counts: dict[str, int] = {}
    reference_id = ""
    for number, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            fail(f"Inventory row {number} has an invalid shape")
        if any(
            "\x00" in value or "\r" in value or "\n" in value for value in row.values()
        ):
            fail(f"Inventory row {number} contains unsafe characters")
        current_id = row["reference_id"]
        if not SAFE_ID.fullmatch(current_id):
            fail(f"Inventory row {number} has invalid reference_id")
        if reference_id and current_id != reference_id:
            fail("Reference inventory must describe exactly one reference_id")
        reference_id = current_id
        artifact_id = row["artifact_id"]
        if not SAFE_ID.fullmatch(artifact_id) or artifact_id in ids:
            fail(f"Inventory row {number} has invalid or duplicate artifact_id")
        ids.add(artifact_id)
        role = row["role"]
        if role not in ROLES:
            fail(f"Inventory row {number} has unsupported role: {role}")
        role_counts[role] = role_counts.get(role, 0) + 1
        required = row["required"]
        if required not in {"true", "false"}:
            fail(f"Inventory row {number} required must be true or false")
        declared = row["path"]
        if not declared or any(token in declared for token in ("*", "?", "[", "]")):
            fail(f"Inventory row {number} path must be explicit")
        declared_path = Path(declared)
        if ".." in declared_path.parts or "." in declared_path.parts:
            fail(f"Inventory row {number} path must not contain traversal components")
        resolved = (
            declared_path if declared_path.is_absolute() else (base / declared_path)
        )
        resolved = resolved.resolve()
        if resolved in paths:
            fail(f"Inventory row {number} resolves to a duplicate path")
        paths.add(resolved)
        expected = row["expected_sha256"]
        if expected != "NA" and not SHA256.fullmatch(expected):
            fail(
                f"Inventory row {number} expected_sha256 must be NA or lowercase SHA-256"
            )
        for field in ("provenance_source", "provenance_release", "notes"):
            if not row[field]:
                fail(f"Inventory row {number} {field} must be nonempty")
        items.append(
            Item(
                reference_id,
                artifact_id,
                role,
                declared,
                resolved,
                required == "true",
                expected,
                row["provenance_source"],
                row["provenance_release"],
                row["notes"],
            )
        )
    for role in SINGLETON_ROLES:
        if role_counts.get(role) != 1:
            fail(f"Reference inventory requires exactly one {role} row")
    if role_counts.get("star_index_file", 0) < 1:
        fail("Reference inventory requires at least one star_index_file row")
    return raw, items
