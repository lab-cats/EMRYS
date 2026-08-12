"""Validate and publish an explicit Step 09c scientific-review evidence set.

This program is intentionally read-only with respect to Steps 08 and 09. It
does not run R, recompute CMH statistics, discover inputs by glob, or infer
reviewer decisions. Dry-run is the default. Execute mode publishes thirteen
validated TSV files as one rollback-protected transaction, with the review
summary written last as the commit marker.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import os
import shutil
import sys
import uuid
from collections.abc import Mapping
from datetime import date
from pathlib import Path

from norad.contracts.scientific_evidence import review_package, step08
from norad.contracts.scientific_evidence.step08 import (
    ContractError,
    read_tsv,
    sha256_file,
)

from ._scientific_review.context import build_context
from ._scientific_review.intake import ReviewContext, write_tsv

DESCRIPTION = __doc__


def _confirm_inputs_unchanged(input_hashes: Mapping[Path, str]) -> None:
    for path, expected_hash in input_hashes.items():
        if not path.is_file():
            step08.fail(f"An input disappeared before publication: {path}")
        observed_hash = sha256_file(path)
        if observed_hash != expected_hash:
            step08.fail(f"An input changed before publication: {path}")


def _acquire_lock(lock_path: Path, review_id: str, run_token: str) -> None:
    metadata = (
        f"review_id\t{review_id}\n"
        f"pid\t{os.getpid()}\n"
        f"run_token\t{run_token}\n"
        f"created_date\t{date.today().isoformat()}\n"
    )
    try:
        descriptor = os.open(
            lock_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        step08.fail(
            "Step 09c output is locked; inspect and preserve the owner "
            f"metadata before recovery: {lock_path}"
        )
    except OSError as exc:
        step08.fail(f"Could not acquire Step 09c lock {lock_path}: {exc}")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(metadata)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        with contextlib.suppress(OSError):
            lock_path.unlink()
        step08.fail(f"Could not write Step 09c lock metadata: {exc}")


def _remove_owned_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _validate_staged_outputs(
    directory: Path,
    output_tables: Mapping[str, tuple[tuple[str, ...], list[dict[str, str]]]],
    output_paths: Mapping[str, Path],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for key, (header, rows) in output_tables.items():
        staged = directory / output_paths[key].name
        table = read_tsv(f"Staged Step 09c {key}", staged, header)
        if table.rows != rows:
            step08.fail(f"Staged Step 09c {key} content changed after writing.")
        hashes[key] = sha256_file(staged)
    return hashes


def _rollback_publication(
    output_paths: Mapping[str, Path],
    backup_dir: Path,
    had_previous: bool,
    previous_hashes: Mapping[str, str],
) -> list[str]:
    failures: list[str] = []
    if not had_previous:
        for key, _ in reversed(review_package.OUTPUT_SUFFIXES):
            final = output_paths[key]
            if final.exists():
                try:
                    final.unlink()
                except OSError as exc:
                    failures.append(f"remove new {final}: {exc}")
    else:
        restore_order = [
            key for key, _ in review_package.OUTPUT_SUFFIXES if key != "review_summary"
        ] + ["review_summary"]
        for key in restore_order:
            backup = backup_dir / output_paths[key].name
            final = output_paths[key]
            if not backup.exists():
                if not final.exists():
                    failures.append(
                        f"prior output and backup are both missing for {final}"
                    )
                continue
            if final.exists():
                try:
                    final.unlink()
                except OSError as exc:
                    failures.append(f"remove replacement {final}: {exc}")
                    continue
            try:
                os.replace(backup, final)
            except OSError as exc:
                failures.append(f"restore {final}: {exc}")
        for key, _ in review_package.OUTPUT_SUFFIXES:
            final = output_paths[key]
            if not final.is_file():
                failures.append(f"restored prior output is missing: {final}")
                continue
            try:
                observed = sha256_file(final)
            except ContractError as exc:
                failures.append(str(exc))
                continue
            if observed != previous_hashes.get(key):
                failures.append(f"restored prior output hash differs: {final}")
    return failures


def _publish_outputs(
    context: ReviewContext,
    output_tables: Mapping[str, tuple[tuple[str, ...], list[dict[str, str]]]],
) -> None:
    output_dir = next(iter(context.output_paths.values())).parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        step08.fail(f"Could not create Step 09c output directory {output_dir}: {exc}")
    if not output_dir.is_dir():
        step08.fail(f"Step 09c output path is not a directory: {output_dir}")

    lock_path = output_dir / f".{context.review_id}.step09c.lock"
    run_token = f"{os.getpid()}-{uuid.uuid4().hex}"
    temp_dir = output_dir / f".{context.review_id}.step09c.{run_token}.tmp"
    backup_dir = output_dir / f".{context.review_id}.step09c.{run_token}.previous"
    _acquire_lock(lock_path, context.review_id, run_token)
    keep_recovery = False
    had_previous = False
    previous_hashes: dict[str, str] = {}
    publication_started = False
    try:
        existing = {key: path.exists() for key, path in context.output_paths.items()}
        existing_count = sum(existing.values())
        if existing_count not in (0, len(context.output_paths)):
            step08.fail(
                "Refusing to replace an incomplete/partial Step 09c output "
                "transaction; "
                "preserve it for inspection."
            )
        had_previous = existing_count == len(context.output_paths)
        if had_previous:
            previous_hashes = {
                key: sha256_file(path) for key, path in context.output_paths.items()
            }
        try:
            temp_dir.mkdir()
            if had_previous:
                backup_dir.mkdir()
        except FileExistsError:
            step08.fail("Refusing to reuse an existing Step 09c run-token path.")
        except OSError as exc:
            step08.fail(f"Could not create Step 09c transaction paths: {exc}")

        for key, (header, rows) in output_tables.items():
            write_tsv(temp_dir / context.output_paths[key].name, header, rows)
        staged_hashes = _validate_staged_outputs(
            temp_dir, output_tables, context.output_paths
        )
        _confirm_inputs_unchanged(context.input_hashes)

        if had_previous:
            summary_key = "review_summary"
            os.replace(
                context.output_paths[summary_key],
                backup_dir / context.output_paths[summary_key].name,
            )
            publication_started = True
            for key, _ in review_package.OUTPUT_SUFFIXES:
                if key == summary_key:
                    continue
                os.replace(
                    context.output_paths[key],
                    backup_dir / context.output_paths[key].name,
                )
        publication_started = True
        for key, _ in review_package.OUTPUT_SUFFIXES:
            if key == "review_summary":
                continue
            os.replace(
                temp_dir / context.output_paths[key].name,
                context.output_paths[key],
            )
        os.replace(
            temp_dir / context.output_paths["review_summary"].name,
            context.output_paths["review_summary"],
        )

        for key, (header, rows) in output_tables.items():
            final = read_tsv(
                f"Published Step 09c {key}",
                context.output_paths[key],
                header,
            )
            if final.rows != rows:
                step08.fail(f"Published Step 09c {key} content is invalid.")
            if sha256_file(final.path) != staged_hashes[key]:
                step08.fail(f"Published Step 09c {key} hash is invalid.")
        _confirm_inputs_unchanged(context.input_hashes)
    except Exception as exc:
        if publication_started:
            rollback_failures = _rollback_publication(
                context.output_paths,
                backup_dir,
                had_previous,
                previous_hashes,
            )
            if rollback_failures:
                keep_recovery = True
                recovery = output_dir / (
                    f".{context.review_id}.step09c.{run_token}.RECOVERY.txt"
                )
                with contextlib.suppress(OSError):
                    recovery.write_text(
                        "Step 09c rollback was incomplete.\n"
                        + "\n".join(rollback_failures)
                        + "\n",
                        encoding="utf-8",
                    )
                step08.fail(
                    f"{exc}\nStep 09c rollback was incomplete; lock and "
                    f"recovery paths were retained: {lock_path}"
                )
        if isinstance(exc, ContractError):
            raise
        step08.fail(f"Step 09c publication failed: {exc}")
    finally:
        if not keep_recovery:
            cleanup_failures: list[str] = []
            for owned in (temp_dir, backup_dir):
                try:
                    _remove_owned_path(owned)
                except OSError as exc:
                    cleanup_failures.append(f"remove {owned}: {exc}")
            try:
                lock_path.unlink()
            except FileNotFoundError:
                cleanup_failures.append(
                    f"owned lock disappeared before cleanup: {lock_path}"
                )
            except OSError as exc:
                cleanup_failures.append(f"remove lock {lock_path}: {exc}")
            if cleanup_failures:
                raise ContractError(
                    "Step 09c cleanup was incomplete; inspect owned paths: "
                    + "; ".join(cleanup_failures)
                )


def _print_resolved_context(context: ReviewContext, execute: bool) -> None:
    print("Step 09c scientific-validation evidence package")
    print(f"Mode: {'execute' if execute else 'dry-run'}")
    print(f"Review ID: {context.review_id}")
    print(f"Primary analysis ID: {context.plan['primary_analysis_id']}")
    print(f"Overall science status: {context.plan['overall_science_status']}")
    print(
        "Computational status: "
        f"implementation={context.plan['implementation_status']}; "
        f"local_tests={context.plan['local_test_status']}; "
        f"runtime={context.plan['runtime_validation_status']}; "
        f"cluster_dry_run={context.plan['cluster_dry_run_status']}; "
        f"cluster_proof={context.plan['cluster_proof_status']}"
    )
    print("Validated immutable inputs:")
    for key in review_package.INPUT_ARTIFACT_KEYS:
        artifact = context.artifacts[key]
        print(
            f"  {key}: {artifact.path} "
            f"(sha256={artifact.sha256}, rows={artifact.row_count})"
        )
    print("Declared outputs (review summary is the final transaction marker):")
    for key, _ in review_package.OUTPUT_SUFFIXES:
        print(f"  {key}: {context.output_paths[key]}")
    if not execute:
        print("Dry-run complete; no output directory or final files were created.")


def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the grouped scientific-review package command."""
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--sample-manifest", required=True)
    parser.add_argument("--partition-manifest", required=True)
    parser.add_argument("--step08-sites", required=True)
    parser.add_argument("--step08-inputs", required=True)
    parser.add_argument("--step08-summary", required=True)
    parser.add_argument("--step09-analysis-dir", required=True)
    parser.add_argument("--review-plan", required=True)
    parser.add_argument("--evidence-manifest", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish the validated 13-file transaction.",
    )


def assemble_from_args(arguments: argparse.Namespace) -> int:
    """Validate and optionally publish one declared review package."""
    try:
        context, output_tables = build_context(arguments)
        _print_resolved_context(context, arguments.execute)
        if arguments.execute:
            _publish_outputs(context, output_tables)
            print(
                "Step 09c publication complete; review summary published last: "
                f"{context.output_paths['review_summary']}"
            )
        return 0
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"ERROR: Step 09c failed: {exc}", file=sys.stderr)
        return 1
