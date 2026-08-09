#!/usr/bin/env python3
"""Inventory and reconcile one explicit reference bundle without repairing it."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path

src_root = str(Path(__file__).resolve().parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]
from norad.evidence.reference_provenance._reference_contigs import (
    agreement,
    collect_contigs,
    observe,
    parse_names,
    parse_star,
    reference_contigs,
    role_path,
)
from norad.evidence.reference_provenance._reference_inventory import load_inventory
from norad.evidence.reference_provenance._reference_model import (
    ARTIFACT_HEADER,
    CONTIG_HEADER,
    CONTIG_ROLES,
    OUTPUT_SPECS,
    PROFILE_HEADER,
    ROLES,
    SAFE_ID,
    SHA256,
    SINGLETON_ROLES,
    SUMMARY_HEADER,
    Item,
    Observation,
    ProvenanceError,
    fail,
)
from norad.evidence.reference_provenance._reference_render import render, tsv
from norad.libraries import validation as report

__all__ = [
    "ARTIFACT_HEADER",
    "CONTIG_HEADER",
    "CONTIG_ROLES",
    "OUTPUT_SPECS",
    "PROFILE_HEADER",
    "ROLES",
    "SAFE_ID",
    "SHA256",
    "SINGLETON_ROLES",
    "SUMMARY_HEADER",
    "Item",
    "Observation",
    "ProvenanceError",
    "agreement",
    "collect_contigs",
    "fail",
    "load_inventory",
    "main",
    "observe",
    "parse_args",
    "parse_names",
    "parse_star",
    "publish",
    "reference_contigs",
    "render",
    "role_path",
    "tsv",
    "validate_output",
]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument(
        "--base-dir",
        type=Path,
        required=True,
        help="Explicit base for relative inventory paths.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def validate_output(
    data: bytes, header: tuple[str, ...], rows: int | None = None
) -> None:
    reader = csv.DictReader(data.decode().splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != header:
        fail("Generated reference output has invalid header")
    body = list(reader)
    if rows is not None and len(body) != rows:
        fail("Generated reference output has invalid row count")
    if any(None in row or any(value is None for value in row.values()) for row in body):
        fail("Generated reference output has invalid row shape")


def publish(output_root: Path, reference_id: str, outputs: dict[str, bytes]) -> None:
    if not output_root.exists() or output_root.is_symlink() or not output_root.is_dir():
        fail(f"Output root must be an existing real directory: {output_root}")
    destination = output_root / reference_id
    destination.mkdir(mode=0o755, exist_ok=True)
    if destination.is_symlink() or not destination.is_dir():
        fail(f"Reference output directory is unsafe: {destination}")
    finals = {
        key: destination / f"{reference_id}.{filename}"
        for key, filename, _header, _rows in OUTPUT_SPECS
    }
    present = [path.exists() for path in finals.values()]
    if any(present) and not all(present):
        fail("Existing reference provenance outputs are incomplete")
    lock = destination / f".{reference_id}.reference-provenance.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        fail(f"Reference provenance lock already exists: {lock}")
    token = uuid.uuid4().hex
    staged = {
        key: destination / f".{reference_id}.{filename}.{token}.tmp"
        for key, filename, _header, _rows in OUTPUT_SPECS
    }
    backups = {
        key: destination / f".{reference_id}.{filename}.{token}.previous"
        for key, filename, _header, _rows in OUTPUT_SPECS
    }
    try:
        os.write(descriptor, f"pid={os.getpid()}\nrun_token={token}\n".encode())
        os.fsync(descriptor)
        if all(present):
            for key, _filename, header, expected_rows in OUTPUT_SPECS:
                validate_output(
                    report.read_bytes(finals[key], f"prior {key}"),
                    header,
                    expected_rows,
                )
        for key, _filename, *_rest in OUTPUT_SPECS:
            with staged[key].open("xb") as handle:
                handle.write(outputs[key])
                handle.flush()
                os.fsync(handle.fileno())
        for key, _filename, header, expected_rows in OUTPUT_SPECS:
            validate_output(
                report.read_bytes(staged[key], f"staged {key}"),
                header,
                expected_rows,
            )
        if all(present):
            for key, _filename, *_rest in OUTPUT_SPECS:
                os.replace(finals[key], backups[key])
        published: list[str] = []
        try:
            for key, _filename, *_rest in OUTPUT_SPECS:
                os.replace(staged[key], finals[key])
                published.append(key)
        except BaseException:
            for key in published:
                if finals[key].exists():
                    finals[key].unlink()
            for key, final in finals.items():
                if backups[key].exists():
                    os.replace(backups[key], final)
            raise
        for path in backups.values():
            if path.exists():
                path.unlink()
    finally:
        for path in staged.values():
            if path.exists() and not path.is_symlink():
                path.unlink()
        os.close(descriptor)
        if lock.exists() and not lock.is_symlink():
            lock.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw, items = load_inventory(args.inventory, args.base_dir)
        observations = observe(items)
        outputs = render(raw, observations)
        for key, _filename, header, rows in OUTPUT_SPECS:
            validate_output(outputs[key], header, rows)
        reference_id = items[0].reference_id
        print(f"Reference inventory: {args.inventory}")
        print(f"Reference base directory: {args.base_dir}")
        print(f"Reference ID: {reference_id}")
        print(f"Output root: {args.output_root}")
        for observation in observations:
            print(f"{observation.item.artifact_id}: {observation.status}")
        print(
            "Evidence boundary: read-only provenance reconciliation; no files are repaired."
        )
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        if (
            hashlib.sha256(
                report.read_bytes(args.inventory, "Reference inventory")
            ).digest()
            != hashlib.sha256(raw).digest()
        ):
            fail("Reference inventory changed after inspection")
        refreshed = observe(items)
        snapshots = [(item.status, item.digest, item.size) for item in observations]
        refreshed_snapshots = [
            (item.status, item.digest, item.size) for item in refreshed
        ]
        if refreshed_snapshots != snapshots:
            fail("A reference artifact changed after inspection")
        publish(args.output_root, reference_id, outputs)
        print(f"Published reference provenance: {args.output_root / reference_id}")
        return 0
    except ProvenanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except report.ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
