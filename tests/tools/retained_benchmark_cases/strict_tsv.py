"""Retained strict-TSV materialization benchmark case."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, NoReturn

CASE_NAME = "strict-tsv-materialization"
EXTENDED_CASE_NAME = "strict-tsv-materialization-extended"
SUITE_NAME = "validation"
EXTENDED_SUITE_NAME = "validation-extended"
FIXTURE_SCHEMA = "emrys.retained-strict-tsv-fixture.v1"
OBSERVATION_SCHEMA = "emrys.retained-strict-tsv-observation.v1"
PARITY_SCHEMA = "emrys.retained-strict-tsv-parity.v1"
LABEL = "Strict TSV benchmark"

# Value = row count * 100 + sample count. Four samples produce the
# representative Step-08-shaped width: 22 metadata + 12 sample columns.
SHAPES_BY_VALUE = {
    1_000_001: (10_000, 1),
    1_000_004: (10_000, 4),
    1_000_016: (10_000, 16),
    10_000_004: (100_000, 4),
    100_000_001: (1_000_000, 1),
}
VALUES_BY_CASE = {
    CASE_NAME: (1_000_001, 1_000_004, 1_000_016, 10_000_004),
    EXTENDED_CASE_NAME: (100_000_001,),
}
CASE_NAMES = tuple(VALUES_BY_CASE)

STEP08_METADATA_HEADER = (
    "partition_id",
    "candidate_id",
    "orientation",
    "chromosome",
    "position",
    "alt_index",
    "genomic_ref",
    "genomic_alt",
    "rna_ref",
    "rna_alt",
    "annotation_strand",
    "gene_ids",
    "transcript_ids",
    "is_cds",
    "is_five_prime_utr",
    "is_three_prime_utr",
    "is_exon",
    "is_intron",
    "qual",
    "filter",
    "info_alt_depth",
    "orientation_policy",
)

DIAGNOSTICS = (
    ("empty", b"", None),
    ("invalid-utf8", b"left\tright\nshort\n\xff\n", None),
    ("malformed-quote", b'left\tright\nshort\n"unterminated\n', None),
    ("empty-header", b"left\t\nvalue\tother\n", None),
    ("duplicate-header", b"left\tleft\nvalue\tother\n", None),
    ("wrong-header", b"left\tright\nvalue\tother\n", ("first", "second")),
    ("short-row", b"left\tright\nvalue\n", None),
)

_CELL_VALUES = tuple(f"{value:03x}" for value in range(4096))


class StrictTsvBenchmarkError(RuntimeError):
    """The strict-TSV retained case is not admissible."""


class _DiagnosticFailure(RuntimeError):
    pass


def _shape(case: str, value: int) -> tuple[int, int]:
    if case not in VALUES_BY_CASE or value not in VALUES_BY_CASE[case]:
        raise StrictTsvBenchmarkError(
            f"strict TSV benchmark case/value is not registered: {case}/{value}"
        )
    return SHAPES_BY_VALUE[value]


def header_for_samples(sample_count: int) -> tuple[str, ...]:
    samples = tuple(f"sample_{index:02d}" for index in range(1, sample_count + 1))
    return STEP08_METADATA_HEADER + tuple(
        f"{prefix}__{sample}" for prefix in ("DP", "AD", "AF") for sample in samples
    )


def row_values(row_index: int, column_count: int) -> tuple[str, ...]:
    base = row_index * 131
    return tuple(
        _CELL_VALUES[(base + column_index * 17) & 0xFFF]
        for column_index in range(column_count)
    )


def _update_cell_digest(digest: Any, values: Sequence[str]) -> None:
    payload = "\0".join(values).encode("ascii")
    digest.update(len(payload).to_bytes(4, "big") + payload)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stat_identity(path: Path) -> dict[str, int]:
    state = path.stat(follow_symlinks=False)
    return {
        "size_bytes": state.st_size,
        "device": state.st_dev,
        "inode": state.st_ino,
        "mtime_ns": state.st_mtime_ns,
    }


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise StrictTsvBenchmarkError(f"{label} is not one real file")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StrictTsvBenchmarkError(f"{label} is invalid: {exc}") from exc
    if not isinstance(value, Mapping):
        raise StrictTsvBenchmarkError(f"{label} is not one object")
    return value


def _diagnostic_token(name: str) -> str:
    return f"<fixture>/diagnostics/{name}.tsv"


def _expected_diagnostic(name: str) -> str:
    source = _diagnostic_token(name)
    messages = {
        "empty": f"{LABEL} is empty: {source}",
        "invalid-utf8": (
            f"Could not read {LABEL} as UTF-8 TSV ({source}): "
            "'utf-8' codec can't decode byte 0xff in position 17: invalid start byte"
        ),
        "malformed-quote": (
            f"Could not read {LABEL} as UTF-8 TSV ({source}): unexpected end of data"
        ),
        "empty-header": f"{LABEL} contains an empty header field: {source}",
        "duplicate-header": f"{LABEL} contains duplicate header fields: {source}",
        "wrong-header": (
            f"{LABEL} header is invalid: {source}\n"
            "Expected: first | second\nObserved: left | right"
        ),
        "short-row": f"{LABEL} row 2 has 1 fields; expected 2: {source}",
    }
    return messages[name]


def _expected_diagnostics() -> list[dict[str, str]]:
    return [
        {"name": name, "message": _expected_diagnostic(name)}
        for name, _data, _header in DIAGNOSTICS
    ]


def _expected_marker(
    case: str,
    value: int,
    input_identity: Mapping[str, Any],
    ordered_cell_sha256: Any,
) -> dict[str, Any]:
    row_count, sample_count = _shape(case, value)
    header = header_for_samples(sample_count)
    return {
        "schema_version": FIXTURE_SCHEMA,
        "case": case,
        "value": value,
        "row_count": row_count,
        "sample_count": sample_count,
        "column_count": len(header),
        "header": list(header),
        "ordered_cell_sha256": ordered_cell_sha256,
        "probes": [
            {"row_index": index, "cells": list(row_values(index, len(header)))}
            for index in (0, row_count // 2, row_count - 1)
        ],
        "input": dict(input_identity),
    }


def _create_fixture(fixture: Path, case: str, value: int) -> None:
    row_count, sample_count = _shape(case, value)
    header = header_for_samples(sample_count)
    fixture.mkdir(mode=0o700)
    diagnostics = fixture / "diagnostics"
    diagnostics.mkdir(mode=0o700)
    for name, data, _expected_header in DIAGNOSTICS:
        with (diagnostics / f"{name}.tsv").open("xb") as stream:
            stream.write(data)

    cell_digest = hashlib.sha256(b"emrys.strict-tsv.ordered-cells.v1\n")
    input_digest = hashlib.sha256()
    input_path = fixture / "input.tsv"
    with input_path.open("xb") as stream:
        encoded = ("\t".join(header) + "\n").encode("ascii")
        stream.write(encoded)
        input_digest.update(encoded)
        for row_index in range(row_count):
            values = row_values(row_index, len(header))
            _update_cell_digest(cell_digest, values)
            encoded = ("\t".join(values) + "\n").encode("ascii")
            stream.write(encoded)
            input_digest.update(encoded)
    input_identity = {
        **_stat_identity(input_path),
        "sha256": input_digest.hexdigest(),
    }
    _write_json(
        fixture / "fixture.json",
        _expected_marker(case, value, input_identity, cell_digest.hexdigest()),
    )


def _admit_fixture(
    fixture: Path, case: str, value: int, *, verify_sha256: bool
) -> Mapping[str, Any]:
    authored = Path(os.path.abspath(fixture))
    if (
        authored.is_symlink()
        or not authored.is_dir()
        or authored.resolve(strict=True) != authored
        or {child.name for child in authored.iterdir()}
        != {"fixture.json", "input.tsv", "diagnostics"}
    ):
        raise StrictTsvBenchmarkError("strict TSV fixture root differs")
    marker = _load_json(authored / "fixture.json", "strict TSV fixture marker")
    input_path = authored / "input.tsv"
    if input_path.is_symlink() or not input_path.is_file():
        raise StrictTsvBenchmarkError("strict TSV input is not one real file")
    input_identity = marker.get("input")
    digest = marker.get("ordered_cell_sha256")
    if (
        not isinstance(input_identity, Mapping)
        or set(input_identity)
        != {"size_bytes", "device", "inode", "mtime_ns", "sha256"}
        or any(
            not isinstance(input_identity.get(key), int)
            for key in ("size_bytes", "device", "inode", "mtime_ns")
        )
        or not isinstance(input_identity.get("sha256"), str)
        or len(str(input_identity.get("sha256"))) != 64
        or not isinstance(digest, str)
        or len(digest) != 64
    ):
        raise StrictTsvBenchmarkError("strict TSV fixture hashes or identity differ")
    if marker != _expected_marker(case, value, input_identity, digest):
        raise StrictTsvBenchmarkError("strict TSV fixture marker differs")
    expected_stat = {
        key: input_identity[key]
        for key in ("size_bytes", "device", "inode", "mtime_ns")
    }
    if _stat_identity(input_path) != expected_stat or (
        verify_sha256 and _sha256(input_path) != input_identity["sha256"]
    ):
        raise StrictTsvBenchmarkError("strict TSV input identity changed")

    diagnostic_root = authored / "diagnostics"
    expected_names = {f"{name}.tsv" for name, _data, _header in DIAGNOSTICS}
    if (
        diagnostic_root.is_symlink()
        or not diagnostic_root.is_dir()
        or {child.name for child in diagnostic_root.iterdir()} != expected_names
    ):
        raise StrictTsvBenchmarkError("strict TSV diagnostic roster differs")
    for name, data, _expected_header in DIAGNOSTICS:
        path = diagnostic_root / f"{name}.tsv"
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
            raise StrictTsvBenchmarkError(f"strict TSV diagnostic differs: {name}")
    return marker


def setup(fixture: Path, case: str, value: int) -> None:
    _shape(case, value)
    if not fixture.exists() and not fixture.is_symlink():
        fixture.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _create_fixture(fixture, case, value)
    _admit_fixture(fixture, case, value, verify_sha256=True)


def _run_diagnostics(module: Any, fixture: Path) -> list[dict[str, str]]:
    observed = []
    for name, _data, expected_header in DIAGNOSTICS:
        path = fixture / "diagnostics" / f"{name}.tsv"

        def fail(message: str) -> NoReturn:
            raise _DiagnosticFailure(message)

        try:
            module.read_strict_tsv(LABEL, path, expected_header, fail)
        except _DiagnosticFailure as exc:
            message = str(exc)
        else:
            raise StrictTsvBenchmarkError(f"strict TSV diagnostic passed: {name}")
        if message.count(str(path)) != 1:
            raise StrictTsvBenchmarkError(f"strict TSV diagnostic path differs: {name}")
        observed.append(
            {
                "name": name,
                "message": message.replace(str(path), _diagnostic_token(name)),
            }
        )
    if observed != _expected_diagnostics():
        raise StrictTsvBenchmarkError("strict TSV accepted diagnostics differ")
    return observed


def _expected_observation(marker: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "case",
        "value",
        "row_count",
        "sample_count",
        "column_count",
        "header",
        "ordered_cell_sha256",
        "probes",
    )
    return {
        "schema_version": OBSERVATION_SCHEMA,
        **{key: marker[key] for key in fields},
        "fixture_sha256": marker["input"]["sha256"],
        "diagnostics": _expected_diagnostics(),
    }


def produce(
    trial: Path,
    fixture: Path,
    source: Path,
    case: str,
    value: int,
    load_variant_module: Callable[[Path, str, str, str], Any],
) -> None:
    marker = _admit_fixture(fixture, case, value, verify_sha256=False)
    module = load_variant_module(
        source,
        "emrys.libraries.validation.tsv",
        "emrys/libraries/validation/tsv.py",
        "strict TSV materialization producer",
    )
    input_path = fixture / "input.tsv"
    before = _stat_identity(input_path)

    def fail(message: str) -> NoReturn:
        raise StrictTsvBenchmarkError(message)

    retained_table = module.read_strict_tsv(
        LABEL, input_path, tuple(marker["header"]), fail
    )
    if (
        type(retained_table) is not tuple
        or len(retained_table) != 2
        or type(retained_table[0]) is not tuple
        or type(retained_table[1]) is not list
    ):
        raise StrictTsvBenchmarkError("strict TSV parser returned an invalid table")
    header, rows = retained_table
    digest = hashlib.sha256(b"emrys.strict-tsv.ordered-cells.v1\n")
    for row in rows:
        if type(row) is not dict or tuple(row) != header:
            raise StrictTsvBenchmarkError("strict TSV parsed row shape differs")
        _update_cell_digest(digest, tuple(row[column] for column in header))
    probes = [
        {"row_index": index, "cells": [rows[index][column] for column in header]}
        for index in (0, len(rows) // 2, len(rows) - 1)
    ]
    observation = {
        "schema_version": OBSERVATION_SCHEMA,
        "case": case,
        "value": value,
        "row_count": len(rows),
        "sample_count": marker["sample_count"],
        "column_count": len(header),
        "header": list(header),
        "ordered_cell_sha256": digest.hexdigest(),
        "probes": probes,
        "fixture_sha256": marker["input"]["sha256"],
        "diagnostics": _run_diagnostics(module, fixture),
    }
    if observation != _expected_observation(marker):
        raise StrictTsvBenchmarkError("strict TSV materialized table oracle differs")
    if _stat_identity(input_path) != before:
        raise StrictTsvBenchmarkError("strict TSV fixture changed during parsing")
    _write_json(trial / "observation.json", observation)
    if len(retained_table[1]) != marker["row_count"]:
        raise StrictTsvBenchmarkError("strict TSV retained table changed")


def validate(trial: Path, fixture: Path, case: str, value: int) -> None:
    marker = _admit_fixture(fixture, case, value, verify_sha256=True)
    observation = _load_json(trial / "observation.json", "strict TSV observation")
    if observation != _expected_observation(marker):
        raise StrictTsvBenchmarkError("strict TSV observation differs")
    _write_json(
        trial / "parity.bin",
        {"schema_version": PARITY_SCHEMA, "observation": observation},
    )
