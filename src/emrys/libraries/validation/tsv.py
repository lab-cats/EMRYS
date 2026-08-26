"""Shared TSV validation helpers."""

from __future__ import annotations

import codecs
import csv
import hashlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from io import StringIO, TextIOWrapper
from pathlib import Path
from typing import BinaryIO, NoReturn, TextIO, TypeVar

from emrys.libraries.validation.report import clean

T = TypeVar("T")


def write_rows(
    stream: TextIO,
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> None:
    """Write rows with the deterministic TSV dialect used by EMRYS contracts."""
    writer = csv.DictWriter(
        stream,
        fieldnames=list(header),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)


def tsv_bytes(
    header: Sequence[str],
    rows: Iterable[Mapping[str, str]],
) -> bytes:
    """Serialize deterministic UTF-8 TSV bytes without platform newlines."""
    stream = StringIO(newline="")
    write_rows(stream, header, rows)
    return stream.getvalue().encode("utf-8")


def read_header(path: Path) -> tuple[str, ...]:
    """Return the first row of a TSV file as a header tuple."""
    with path.open(encoding="utf-8", newline="") as stream:
        return tuple(next(csv.reader(stream, delimiter="\t")))


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """Read a TSV into a header list and row dictionaries."""
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        return list(reader.fieldnames or ()), list(reader)


def read_strict_tsv(
    label: str,
    path: Path,
    expected_header: Sequence[str] | None,
    fail: Callable[[str], NoReturn],
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """Parse a validated path with EMRYS's strict tabular diagnostics."""
    try:
        with path.open("rb") as byte_stream:
            _preflight_utf8(byte_stream)
            byte_stream.seek(0)
            with TextIOWrapper(
                byte_stream,
                encoding="utf-8",
                newline="",
            ) as stream:
                return _parse_strict_tsv_stream(
                    label,
                    stream,
                    str(path),
                    expected_header,
                    fail,
                )
    except (OSError, UnicodeError, csv.Error) as exc:
        fail(f"Could not read {label} as UTF-8 TSV ({path}): {exc}")


def parse_strict_tsv_bytes(
    label: str,
    data: bytes,
    source: str | Path,
    expected_header: Sequence[str] | None,
    fail: Callable[[str], NoReturn],
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """Parse exact admitted UTF-8 TSV bytes without reopening their pathname."""
    source_label = str(source)
    try:
        with StringIO(data.decode("utf-8"), newline="") as stream:
            return _parse_strict_tsv_stream(
                label,
                stream,
                source_label,
                expected_header,
                fail,
            )
    except (UnicodeError, csv.Error) as exc:
        fail(f"Could not read {label} as UTF-8 TSV ({source_label}): {exc}")


def _preflight_utf8(stream: BinaryIO) -> None:
    """Validate a complete UTF-8 stream with bounded transient memory."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    byte_offset = 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        buffered_prefix, _ = decoder.getstate()
        try:
            decoder.decode(chunk)
        except UnicodeDecodeError as exc:
            _raise_absolute_unicode_error(
                exc,
                byte_offset - len(buffered_prefix),
            )
        byte_offset += len(chunk)
    buffered_prefix, _ = decoder.getstate()
    try:
        decoder.decode(b"", final=True)
    except UnicodeDecodeError as exc:
        _raise_absolute_unicode_error(
            exc,
            byte_offset - len(buffered_prefix),
        )


def _raise_absolute_unicode_error(
    error: UnicodeDecodeError,
    base_offset: int,
) -> NoReturn:
    """Raise a standard decode diagnostic using absolute stream offsets."""
    start = base_offset + error.start
    end = base_offset + error.end
    if end == start + 1:
        location = f"byte 0x{error.object[error.start]:02x} in position {start}"
    else:
        location = f"bytes in position {start}-{end - 1}"
    raise UnicodeError(
        f"'{error.encoding}' codec can't decode {location}: {error.reason}"
    ) from error


def _parse_strict_tsv_stream(
    label: str,
    stream: TextIO,
    source_label: str,
    expected_header: Sequence[str] | None,
    fail: Callable[[str], NoReturn],
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    """Materialize strict rows from a text stream without retaining raw rows."""
    reader = csv.reader(stream, delimiter="\t", strict=True)
    try:
        header = tuple(next(reader))
    except StopIteration:
        fail(f"{label} is empty: {source_label}")

    header_error: str | None = None
    if any(not column for column in header):
        header_error = f"{label} contains an empty header field: {source_label}"
    elif len(header) != len(set(header)):
        header_error = f"{label} contains duplicate header fields: {source_label}"
    elif expected_header is not None and header != tuple(expected_header):
        header_error = (
            f"{label} header is invalid: {source_label}\n"
            f"Expected: {' | '.join(expected_header)}\n"
            f"Observed: {' | '.join(header)}"
        )

    rows: list[dict[str, str]] = []
    row_error: str | None = None
    for index, values in enumerate(reader, start=2):
        if len(values) != len(header):
            if row_error is None:
                row_error = (
                    f"{label} row {index} has {len(values)} fields; "
                    f"expected {len(header)}: {source_label}"
                )
                rows.clear()
            continue
        if header_error is None and row_error is None:
            rows.append(dict(zip(header, values, strict=True)))

    # The previous whole-file parser completed UTF-8 and CSV lexing before it
    # reported EMRYS-owned header or row-shape failures. Defer those failures
    # until the reader is exhausted so a later lexical failure still wins.
    if header_error is not None:
        fail(header_error)
    if row_error is not None:
        fail(row_error)
    return header, rows


def sha256_file(path: Path) -> str:
    """Compute a stable SHA-256 digest for the file contents."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def attempt(
    function: Callable[[], T],
    catches: tuple[type[BaseException], ...] = (OSError, UnicodeError, csv.Error),
) -> tuple[T | None, str]:
    try:
        return function(), "validated"
    except catches as exc:
        return None, clean(exc)
