#!/usr/bin/env python3
"""Build temporary computational artifact/run-summary fixtures."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from norad.contracts.artifacts import api as ARTIFACT_CONTRACTS
from norad.libraries.source_authority import ArtifactSourceRoot, SourceCheckout
from norad.reporting._artifact_index import context as ARTIFACT_CONTEXT
from norad.reporting._artifact_index import core as ARTIFACT_CORE
from norad.reporting._artifact_index import models as ARTIFACT_MODELS
from norad.reporting._artifact_index import publication as ARTIFACT_PUBLICATION
from tests.reporting.fixtures.artifact_adapters_v1 import (
    build_fixture as ADAPTER_FIXTURE,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXED_EPOCH = "1700000000"


@dataclass(frozen=True)
class RunSummaryFixture:
    """Paths for one committed artifact transaction and its summary outputs."""

    root: Path
    run_id: str
    artifact_receipt: Path
    output_root: Path
    adapter_fixture: Any

    @property
    def output_dir(self) -> Path:
        return self.output_root / self.run_id

    @property
    def summary_json_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.run_summary.json"

    @property
    def summary_tsv_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.run_summary.tsv"

    @property
    def qc_summary_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.qc_summary.tsv"

    @property
    def summary_receipt_path(self) -> Path:
        return self.output_dir / f"{self.run_id}.run_summary_receipt.tsv"

    @property
    def lock_path(self) -> Path:
        return self.output_dir / f".{self.run_id}.run-summary.lock"

    @property
    def summary_paths(self) -> tuple[Path, ...]:
        return (
            self.summary_json_path,
            self.summary_tsv_path,
            self.qc_summary_path,
            self.summary_receipt_path,
        )

    def command_args(self, *, execute: bool = False) -> list[str]:
        arguments = [
            "--source-checkout",
            str(REPO_ROOT),
            "--artifact-source-root",
            str(self.root),
            "--run-id",
            self.run_id,
            "--artifact-receipt",
            str(self.artifact_receipt),
            "--output-root",
            str(self.output_root),
        ]
        if execute:
            arguments.append("--execute")
        return arguments


def fixed_epoch() -> tuple[str | None, str]:
    previous = os.environ.get("SOURCE_DATE_EPOCH")
    os.environ["SOURCE_DATE_EPOCH"] = FIXED_EPOCH
    return previous, FIXED_EPOCH


def restore_epoch(previous: str | None) -> None:
    if previous is None:
        os.environ.pop("SOURCE_DATE_EPOCH", None)
    else:
        os.environ["SOURCE_DATE_EPOCH"] = previous


def publish_adapter_fixture(fixture: Any) -> None:
    previous, _ = fixed_epoch()
    try:
        context = ARTIFACT_CONTEXT.prepare_context(
            argparse.Namespace(
                run_id=fixture.run_id,
                run_contract=fixture.run_contract,
                inventory=fixture.inventory,
                output_root=fixture.output_root,
                execute=True,
            ),
            source_checkout=SourceCheckout(root=REPO_ROOT),
            artifact_source_root=ArtifactSourceRoot(root=fixture.root),
            identity_ops=ARTIFACT_CONTEXT.ArtifactIdentityOps(
                matching_clean_checkout_head_commit=(
                    lambda **_kwargs: ARTIFACT_CORE.get_git_commit(
                        source_root=REPO_ROOT,
                        sanitize_git_routing=True,
                    )
                )
            ),
        )
        ARTIFACT_PUBLICATION.publish_context(context)
    finally:
        restore_epoch(previous)


def _fixture_from_adapter(root: Path, adapter_fixture: Any) -> RunSummaryFixture:
    publish_adapter_fixture(adapter_fixture)
    return RunSummaryFixture(
        root=root,
        run_id=adapter_fixture.run_id,
        artifact_receipt=adapter_fixture.receipt_path,
        output_root=adapter_fixture.output_root,
        adapter_fixture=adapter_fixture,
    )


def build_fixture(
    root: Path,
    *,
    run_id: str = "synthetic_run",
) -> RunSummaryFixture:
    """Build the default 68-record computational artifact transaction."""

    root = root.resolve()
    return _fixture_from_adapter(
        root,
        ADAPTER_FIXTURE.build_fixture(root / "adapter_fixture", run_id=run_id),
    )


def build_failed_fixture(
    root: Path,
    *,
    run_id: str = "failed_validation_run",
) -> RunSummaryFixture:
    """Build an artifact transaction with one failed Step 01 check."""

    root = root.resolve()
    adapter_fixture = ADAPTER_FIXTURE.build_fixture(
        root / "adapter_fixture",
        run_id=run_id,
    )
    validation_path = adapter_fixture.source_for("sample.SYNTH_A.star_validation")
    validation_rows = read_tsv(validation_path)
    validation_rows[0].update(
        {
            "status": "fail",
            "observed": "mismatch",
            "detail": "synthetic failed validation",
        }
    )
    write_tsv(
        validation_path,
        ARTIFACT_MODELS.VALIDATION_REPORT_HEADER,
        validation_rows,
    )
    return _fixture_from_adapter(root, adapter_fixture)


def build_missing_fixture(
    root: Path,
    *,
    run_id: str = "missing_artifact_run",
    artifact_id: str = "sample.SYNTH_A.canonical_bai",
) -> RunSummaryFixture:
    """Build an artifact transaction with one required source missing."""

    root = root.resolve()
    adapter_fixture = ADAPTER_FIXTURE.build_fixture(
        root / "adapter_fixture",
        run_id=run_id,
    )
    adapter_fixture.source_for(artifact_id).unlink()
    return _fixture_from_adapter(root, adapter_fixture)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_tsv(
    path: Path,
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(header),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a computational artifact/run-summary fixture."
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--run-id", default="synthetic_run")
    arguments = parser.parse_args()
    fixture = build_fixture(arguments.root, run_id=arguments.run_id)
    print(f"Artifact receipt: {fixture.artifact_receipt}")
    print(f"Run-summary output root: {fixture.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
