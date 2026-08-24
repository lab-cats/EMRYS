"""Measure explicit storage roots and record retention policy without mutation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from norad.evidence.storage_inventory import _storage_contract as _contract
from norad.evidence.storage_inventory import _storage_measurement as _measurement
from norad.evidence.storage_inventory import _storage_publication as _publication

DESCRIPTION = __doc__


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Add storage-inventory inspection arguments to ``parser``."""
    parser.add_argument("--roots", required=True, type=Path)
    parser.add_argument("--retention-policy", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")


def inspect_from_args(args: argparse.Namespace) -> int:
    """Inspect declared storage state and optionally publish evidence."""
    try:
        roots_data, roots = _contract.load_roots(args.roots)
        policy_data, policies = _contract.load_policy(
            args.retention_policy, {root.storage_id for root in roots}
        )
        generated = _measurement.outputs(
            roots_data,
            policy_data,
            roots,
            policies,
        )
        _measurement.validate(
            generated["inventory"],
            _contract.INVENTORY_HEADER,
            len(roots),
        )
        _measurement.validate(
            generated["policy"],
            _contract.POLICY_HEADER,
            len(policies),
        )
        _measurement.validate(generated["summary"], _contract.SUMMARY_HEADER, 1)
        print(f"Storage roots: {args.roots}")
        print(f"Retention policy: {args.retention_policy}")
        print(f"Output root: {args.output_root}")
        print(
            "Evidence boundary: read-only measurement and policy recording; "
            "no storage is altered."
        )
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        if _contract.report.read_bytes(args.roots, "Storage roots") != roots_data:
            _contract.fail("Storage roots changed after measurement")
        if (
            _contract.report.read_bytes(args.retention_policy, "Retention policy")
            != policy_data
        ):
            _contract.fail("Retention policy changed after measurement")
        _publication.publish(args.output_root, generated)
        print(f"Published storage/retention report: {args.output_root}")
        return 0
    except _contract.StorageError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
