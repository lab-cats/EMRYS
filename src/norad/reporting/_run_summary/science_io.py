"""Guarded file intake for committed scientific-review packages."""

from __future__ import annotations

import stat
from collections.abc import Mapping, Sequence
from pathlib import Path

import norad.contracts.scientific_evidence.step08 as step08
from norad.contracts.artifacts import validate_artifact_contracts as contracts
from norad.libraries.validation.tsv import read_strict_tsv as _read_strict_tsv
from norad.reporting._run_summary.inputs import _resolved_path

from .science_models import _fail


def _require_regular_file(label: str, value: str | Path) -> Path:
    path = _resolved_path(value)
    try:
        metadata = path.lstat()
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(metadata.st_mode):
        _fail(f"{label} must not be a symbolic link: {path}")
    if not stat.S_ISREG(metadata.st_mode):
        _fail(f"{label} is not a regular file: {path}")
    if metadata.st_size == 0:
        _fail(f"{label} is empty: {path}")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        _fail(f"{label} cannot be resolved: {path}: {exc}")


def _require_contract_file(label: str, value: str) -> Path:
    return _require_regular_file(label, contracts.resolve_contract_path(value))


def _read_tsv(
    label: str,
    value: str | Path,
    expected_header: Sequence[str],
) -> step08.Table:
    path = _require_regular_file(label, value)
    header, rows = _read_strict_tsv(label, path, expected_header, _fail)
    return step08.Table(header=header, rows=rows, path=path)


def _resolve_recorded_path(value: str) -> Path:
    return _resolved_path(value).resolve()


def _confirm_inputs_unchanged(input_hashes: Mapping[Path, str]) -> None:
    for path, expected_hash in input_hashes.items():
        if not path.is_file():
            _fail(f"A reporting input disappeared during normalization: {path}")
        if contracts.sha256_file(path) != expected_hash:
            _fail(f"A reporting input changed during normalization: {path}")
