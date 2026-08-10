"""Inventory and reconcile one explicit reference bundle without repairing it."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sys
import uuid
from pathlib import Path

from norad.evidence.reference_provenance._reference_contigs import observe
from norad.evidence.reference_provenance._reference_inventory import load_inventory
from norad.evidence.reference_provenance._reference_model import (
    OUTPUT_SPECS,
    ProvenanceError,
    fail,
)
from norad.evidence.reference_provenance._reference_render import render
from norad.libraries import validation as report

DESCRIPTION = __doc__


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the grouped reference-provenance reconciliation command."""
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument(
        "--base-dir",
        type=Path,
        required=True,
        help="Explicit base for relative inventory paths.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")


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


def reconcile_from_args(arguments: argparse.Namespace) -> int:
    """Reconcile one declared reference bundle and optionally publish evidence."""
    try:
        raw, items = load_inventory(arguments.inventory, arguments.base_dir)
        observations = observe(items)
        outputs = render(raw, observations)
        for key, _filename, header, rows in OUTPUT_SPECS:
            validate_output(outputs[key], header, rows)
        reference_id = items[0].reference_id
        print(f"Reference inventory: {arguments.inventory}")
        print(f"Reference base directory: {arguments.base_dir}")
        print(f"Reference ID: {reference_id}")
        print(f"Output root: {arguments.output_root}")
        for observation in observations:
            print(f"{observation.item.artifact_id}: {observation.status}")
        print(
            "Evidence boundary: read-only provenance reconciliation; "
            "no files are repaired."
        )
        if not arguments.execute:
            print("Dry-run complete; no output was written.")
            return 0
        if (
            hashlib.sha256(
                report.read_bytes(arguments.inventory, "Reference inventory")
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
        publish(arguments.output_root, reference_id, outputs)
        published_path = arguments.output_root / reference_id
        print(f"Published reference provenance: {published_path}")
        return 0
    except ProvenanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except report.ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
