"""CLI-independent serialization, contract, and source snapshot helpers."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import subprocess
import uuid
from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from norad.libraries.alignments import orientation as alignment_orientation

from norad.reporting import _files
from .contracts import contracts
from .models import (
    RUN_CONTRACT_FIELDS,
    STEP00A_BASENAMES,
    ArtifactIndexError,
    SourceSnapshot,
)
from .registry import ADAPTER_REGISTRY
from .rosters import SCOPE_ADAPTER_ROSTERS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build an explicit read-only NORAD artifact index. Dry-run is "
            "the default; add --execute to publish the receipt-last "
            "transaction."
        )
    )
    parser.add_argument("--run-id", required=True, help="Immutable run ID.")
    parser.add_argument(
        "--run-contract",
        required=True,
        type=Path,
        help=(
            "Strict JSON file containing exactly the six-field canonical run contract."
        ),
    )
    parser.add_argument(
        "--inventory",
        required=True,
        type=Path,
        help="Explicit expected-artifact inventory TSV.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Parent directory under which <run-id>/ is published.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Publish records, index, and receipt. Default is dry-run.",
    )
    return parser.parse_args()


def safe_tsv(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    return " ".join(text.replace("\t", " ").splitlines()).strip()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is not None:
        try:
            timestamp = int(source_date_epoch)
        except ValueError as exc:
            raise ArtifactIndexError(
                "SOURCE_DATE_EPOCH must be an integer when set"
            ) from exc
        value = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    else:
        value = datetime.now(tz=timezone.utc)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_attempt_id(timestamp: str) -> str:
    compact = re.sub(r"[^0-9]", "", timestamp)[:14]
    return f"artifact-index-{compact}-{uuid.uuid4().hex[:12]}"


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=contracts.REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ArtifactIndexError(
            f"Could not resolve the current Git commit: {exc}"
        ) from exc
    value = result.stdout.strip()
    if not contracts.SAFE_ID_RE.fullmatch(value):
        raise ArtifactIndexError(f"Resolved Git commit is invalid: {value!r}")
    return value


def load_run_contract(path: Path) -> tuple[dict[str, Any], str]:
    resolved = path.expanduser().resolve()
    document = contracts.load_json_object(resolved, "run contract")
    if len(document) != len(RUN_CONTRACT_FIELDS) or set(document) != set(
        RUN_CONTRACT_FIELDS
    ):
        raise ArtifactIndexError(
            "Run contract must contain exactly these fields: "
            + ", ".join(RUN_CONTRACT_FIELDS)
        )
    _schemas, registry = contracts.load_schema_registry()
    wrapper_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$ref": "urn:norad:schema:artifacts:common:v1#/$defs/run_contract",
    }
    validator = Draft202012Validator(
        wrapper_schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        detail = "\n".join(
            f"- {contracts.format_json_path(error.absolute_path)}: {error.message}"
            for error in errors
        )
        raise ArtifactIndexError(f"Run contract failed validation:\n{detail}")
    try:
        contracts.validate_run_contract(document, "artifact index")
    except contracts.ContractValidationError as exc:
        raise ArtifactIndexError(str(exc)) from exc
    return document, contracts.sha256_file(resolved)


def validate_inventory_registry(rows: Sequence[dict[str, str]]) -> None:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row_number, row in enumerate(rows, start=2):
        adapter_id = row["adapter"]
        spec = ADAPTER_REGISTRY.get(adapter_id)
        if spec is None:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: unsupported adapter {adapter_id!r}"
            )
        if row["step_id"] != spec.step_id:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} belongs "
                f"to step {spec.step_id}, not {row['step_id']}"
            )
        if row["scope_type"] != spec.scope_type:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} requires "
                f"scope_type {spec.scope_type}, not {row['scope_type']}"
            )
        source_name = Path(row["source_path"]).name
        if spec.basenames and source_name not in spec.basenames:
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} does not "
                f"accept basename {source_name!r}"
            )
        if spec.suffixes and not source_name.endswith(spec.suffixes):
            raise ArtifactIndexError(
                f"Inventory row {row_number}: adapter {adapter_id!r} does not "
                f"accept source filename {source_name!r}"
            )
        grouped[contracts.scope_key(row)].append(row)

    for scope, scope_rows in grouped.items():
        step_id = scope[0]
        expected = SCOPE_ADAPTER_ROSTERS.get(step_id)
        if expected is None:
            raise ArtifactIndexError(
                f"No logical transaction roster exists for step {step_id!r}"
            )
        observed = Counter(row["adapter"] for row in scope_rows)
        if observed != expected:
            raise ArtifactIndexError(
                f"Inventory scope {scope!r} adapter roster is invalid; "
                f"observed {dict(observed)}, expected {dict(expected)}"
            )
        if step_id == "00a":
            names = {
                Path(row["source_path"]).name
                for row in scope_rows
                if row["adapter"] == "step00a_star_index_v1"
            }
            if names != set(STEP00A_BASENAMES):
                raise ArtifactIndexError(
                    f"Inventory scope {scope!r} must declare the exact 15 "
                    "STAR index basenames"
                )
        if step_id == "07":
            vcf_names = [
                Path(row["source_path"]).name
                for row in scope_rows
                if row["adapter"] == "step07_mpileup_vcf_v1"
            ]
            observed_orientations = {
                alignment_orientation.infer_orientation_from_path(name)
                for name in vcf_names
            }
            if observed_orientations != alignment_orientation.REQUIRED_ORIENTATIONS:
                raise ArtifactIndexError(
                    f"Inventory scope {scope!r} must declare one FWD_like "
                    "and one REV_like Step 07 VCF"
                )


def issue(code: str, message: str, artifact_id: str) -> dict[str, Any]:
    return {
        "code": code,
        "message": safe_tsv(message),
        "related_artifact_ids": [artifact_id],
        "evidence": [],
    }


def declared_contract_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = contracts.REPO_ROOT / path
    return Path(os.path.abspath(os.fspath(path)))


def stat_source(
    path: Path,
    *,
    hash_content: bool = True,
) -> SourceSnapshot:
    try:
        lstat_result = path.lstat()
    except FileNotFoundError:
        return SourceSnapshot("missing", None, None, "absent")
    except OSError as exc:
        status = (
            "externally_unavailable"
            if exc.errno
            in {
                errno.EACCES,
                errno.EPERM,
                errno.ESTALE,
                errno.EIO,
                errno.ENXIO,
                errno.ETIMEDOUT,
            }
            else "unknown"
        )
        return SourceSnapshot(status, None, None, f"os_error:{exc.errno}")

    link_target: str | None = None
    if path.is_symlink():
        try:
            link_target = os.readlink(path)
        except OSError as exc:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                None,
                f"symlink_read_error:{exc.errno}",
            )
        try:
            stat_result = path.stat()
        except FileNotFoundError:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                None,
                "dangling_symlink",
                link_target,
            )
        except OSError as exc:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                None,
                f"symlink_target_error:{exc.errno}",
                link_target,
            )
    else:
        stat_result = lstat_result

    if not path.is_file():
        return SourceSnapshot("unknown", None, None, "not_regular_file")
    digest: str | None = None
    if hash_content:
        try:
            digest = contracts.sha256_file(path)
        except contracts.ContractValidationError:
            return SourceSnapshot(
                "externally_unavailable",
                None,
                stat_result.st_size,
                "hash_read_error",
                link_target,
                stat_result.st_dev,
                stat_result.st_ino,
                stat_result.st_mtime_ns,
                stat_result.st_ctime_ns,
            )
        try:
            post_hash_stat = path.stat()
            post_hash_link = os.readlink(path) if link_target is not None else None
        except OSError:
            return SourceSnapshot(
                "unknown",
                None,
                None,
                "changed_during_hash",
                link_target,
            )
        before_identity = (*_files.stat_identity(stat_result), link_target)
        after_identity = (*_files.stat_identity(post_hash_stat), post_hash_link)
        if before_identity != after_identity:
            return SourceSnapshot(
                "unknown",
                None,
                post_hash_stat.st_size,
                "changed_during_hash",
                post_hash_link,
                post_hash_stat.st_dev,
                post_hash_stat.st_ino,
                post_hash_stat.st_mtime_ns,
                post_hash_stat.st_ctime_ns,
            )
    file_type = "symlink_to_regular_file" if link_target is not None else "regular_file"
    return SourceSnapshot(
        "present",
        digest,
        stat_result.st_size,
        file_type,
        link_target,
        stat_result.st_dev,
        stat_result.st_ino,
        stat_result.st_mtime_ns,
        stat_result.st_ctime_ns,
    )
