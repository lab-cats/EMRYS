#!/usr/bin/env python3
# ruff: noqa: EXE001 - public contract is explicit-interpreter only
"""Measure explicit storage roots and record retention policy without mutation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

if (src_root := str(Path(__file__).resolve().parents[3])) not in sys.path:
    sys.path.insert(0, src_root)

from norad.evidence.storage_inventory import _storage_contract as _contract
from norad.evidence.storage_inventory import _storage_measurement as _measurement
from norad.evidence.storage_inventory import _storage_publication as _publication

# Preserve the established direct-import surface and shared identities.
report = _contract.report
ROOT_HEADER = _contract.ROOT_HEADER
POLICY_HEADER = _contract.POLICY_HEADER
INVENTORY_HEADER = _contract.INVENTORY_HEADER
SUMMARY_HEADER = _contract.SUMMARY_HEADER
SAFE_ID = _contract.SAFE_ID
ACTIONS = _contract.ACTIONS
StorageError = _contract.StorageError
Root = _contract.Root
Policy = _contract.Policy
fail = _contract.fail
table = _contract.table
load_roots = _contract.load_roots
parse_utc = _contract.parse_utc
load_policy = _contract.load_policy

os = _measurement.os
hashlib = _measurement.hashlib
stat = _measurement.stat
measure = _measurement.measure
render_tsv = _measurement.render_tsv
outputs = _measurement.outputs
validate = _measurement.validate

uuid = _publication.uuid
publish = _publication.publish


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", required=True, type=Path)
    parser.add_argument("--retention-policy", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        roots_data, roots = load_roots(args.roots)
        policy_data, policies = load_policy(
            args.retention_policy, {root.storage_id for root in roots}
        )
        generated = outputs(roots_data, policy_data, roots, policies)
        validate(generated["inventory"], INVENTORY_HEADER, len(roots))
        validate(generated["policy"], POLICY_HEADER, len(policies))
        validate(generated["summary"], SUMMARY_HEADER, 1)
        print(f"Storage roots: {args.roots}")
        print(f"Retention policy: {args.retention_policy}")
        print(f"Output root: {args.output_root}")
        print(
            "Evidence boundary: read-only measurement and policy recording; no storage is altered."
        )
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        if report.read_bytes(args.roots, "Storage roots") != roots_data:
            fail("Storage roots changed after measurement")
        if report.read_bytes(args.retention_policy, "Retention policy") != policy_data:
            fail("Retention policy changed after measurement")
        publish(args.output_root, generated)
        print(f"Published storage/retention report: {args.output_root}")
        return 0
    except StorageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
