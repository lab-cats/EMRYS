"""Characterization tests for shared strict TSV parsing."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import pytest

from emrys.libraries.validation import tsv as TSV


class StrictTsvError(RuntimeError):
    """Test-only failure raised through the parser's injected boundary."""


def fail(message: str) -> NoReturn:
    raise StrictTsvError(message)


def parse(
    mode: str,
    path: Path,
    data: bytes,
    expected_header: tuple[str, ...] | None = None,
) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    if mode == "path":
        path.write_bytes(data)
        return TSV.read_strict_tsv("Table", path, expected_header, fail)
    return TSV.parse_strict_tsv_bytes("Table", data, path, expected_header, fail)


def test_path_reader_streams_without_read_bytes_and_preserves_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "quoted.tsv"
    path.write_bytes(b'left\tright\r\n"line\r\nbreak"\tvalue\r\nlast\trow\r\n')

    def reject_read_bytes(_path: Path) -> bytes:
        pytest.fail("strict path parsing must not materialize the file as bytes")

    monkeypatch.setattr(Path, "read_bytes", reject_read_bytes)

    assert TSV.read_strict_tsv("Table", path, ("left", "right"), fail) == (
        ("left", "right"),
        [
            {"left": "line\r\nbreak", "right": "value"},
            {"left": "last", "right": "row"},
        ],
    )


def test_exact_byte_parser_does_not_reopen_its_source(tmp_path: Path) -> None:
    source = tmp_path / "absent.tsv"

    assert TSV.parse_strict_tsv_bytes(
        "Table",
        b"left\tright\nvalue\tother\n",
        source,
        ("left", "right"),
        fail,
    ) == (
        ("left", "right"),
        [{"left": "value", "right": "other"}],
    )
    assert not source.exists()


@pytest.mark.parametrize("mode", ("path", "bytes"))
@pytest.mark.parametrize(
    ("suffix", "expected"),
    (
        (b'"unterminated\n', "unexpected end of data"),
        (b"\xff\n", "can't decode byte 0xff"),
    ),
)
def test_late_lexical_failure_precedes_earlier_row_shape_failure(
    mode: str,
    suffix: bytes,
    expected: str,
    tmp_path: Path,
) -> None:
    path = tmp_path / f"{mode}.tsv"

    with pytest.raises(StrictTsvError) as caught:
        parse(mode, path, b"left\tright\nshort\n" + suffix)

    detail = str(caught.value)
    assert detail.startswith(f"Could not read Table as UTF-8 TSV ({path}): ")
    assert expected in detail
    assert "row 2 has 1 fields" not in detail


@pytest.mark.parametrize("mode", ("path", "bytes"))
@pytest.mark.parametrize(
    ("suffix", "expected"),
    (
        (b'"unterminated\n', "unexpected end of data"),
        (b"\xff\n", "can't decode byte 0xff"),
    ),
)
def test_late_lexical_failure_precedes_earlier_header_failure(
    mode: str,
    suffix: bytes,
    expected: str,
    tmp_path: Path,
) -> None:
    path = tmp_path / f"{mode}.tsv"

    with pytest.raises(StrictTsvError) as caught:
        parse(mode, path, b"observed\n" + suffix, ("expected",))

    detail = str(caught.value)
    assert detail.startswith(f"Could not read Table as UTF-8 TSV ({path}): ")
    assert expected in detail
    assert "header is invalid" not in detail


@pytest.mark.parametrize(
    ("prefix", "gap_row", "expected_header", "expected_position"),
    (
        (b'a\tb\n"a"x\tb\n', b"good\trow\n", None, 1_800_011),
        (b"observed\nvalue\n", b"good\n", ("expected",), 1_000_015),
        (b"a\tb\nshort\n", b"good\trow\n", None, 1_800_010),
    ),
)
def test_late_utf8_failure_across_a_large_gap_precedes_earlier_defects(
    prefix: bytes,
    gap_row: bytes,
    expected_header: tuple[str, ...] | None,
    expected_position: int,
    tmp_path: Path,
) -> None:
    path = tmp_path / "large-gap.tsv"
    path.write_bytes(prefix + gap_row * 200_000 + b"\xff\n")

    with pytest.raises(StrictTsvError) as caught:
        TSV.read_strict_tsv("Table", path, expected_header, fail)

    detail = str(caught.value)
    assert detail == (
        f"Could not read Table as UTF-8 TSV ({path}): "
        "'utf-8' codec can't decode byte 0xff in position "
        f"{expected_position}: invalid start byte"
    )


def test_utf8_error_range_is_absolute_across_a_chunk_boundary(
    tmp_path: Path,
) -> None:
    chunk_size = 1024 * 1024
    path = tmp_path / "split-sequence.tsv"
    path.write_bytes(b"a" * (chunk_size - 1) + b"\xe2\x82(")

    with pytest.raises(StrictTsvError) as caught:
        TSV.read_strict_tsv("Table", path, None, fail)

    assert str(caught.value) == (
        f"Could not read Table as UTF-8 TSV ({path}): "
        "'utf-8' codec can't decode bytes in position "
        f"{chunk_size - 1}-{chunk_size}: invalid continuation byte"
    )


def test_truncated_utf8_range_is_absolute_at_end_of_stream(
    tmp_path: Path,
) -> None:
    chunk_size = 1024 * 1024
    path = tmp_path / "truncated-sequence.tsv"
    path.write_bytes(b"a" * (chunk_size - 1) + b"\xe2\x82")

    with pytest.raises(StrictTsvError) as caught:
        TSV.read_strict_tsv("Table", path, None, fail)

    assert str(caught.value) == (
        f"Could not read Table as UTF-8 TSV ({path}): "
        "'utf-8' codec can't decode bytes in position "
        f"{chunk_size - 1}-{chunk_size}: unexpected end of data"
    )


@pytest.mark.parametrize("mode", ("path", "bytes"))
def test_header_failure_precedes_row_shape_failure(
    mode: str,
    tmp_path: Path,
) -> None:
    path = tmp_path / f"{mode}.tsv"

    with pytest.raises(StrictTsvError) as caught:
        parse(
            mode,
            path,
            b"observed\nfirst\textra\n",
            ("expected",),
        )

    assert str(caught.value) == (
        f"Table header is invalid: {path}\nExpected: expected\nObserved: observed"
    )


@pytest.mark.parametrize("mode", ("path", "bytes"))
def test_first_row_shape_failure_is_retained_after_complete_lexing(
    mode: str,
    tmp_path: Path,
) -> None:
    path = tmp_path / f"{mode}.tsv"

    with pytest.raises(StrictTsvError) as caught:
        parse(
            mode,
            path,
            b"left\tright\nshort\nlong\textra\tfield\n",
        )

    assert str(caught.value) == f"Table row 2 has 1 fields; expected 2: {path}"
