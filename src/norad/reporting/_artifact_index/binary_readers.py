"""Strict binary artifact readers for BAM, BAI, and PDF sources."""

from __future__ import annotations

import re
import struct
import zlib
from pathlib import Path
from typing import Any

from .models import ArtifactIndexError

BGZF_EOF_BLOCK = bytes.fromhex(
    "1f8b08040000000000ff0600424302001b0003000000000000000000"
)
MAX_BAM_HEADER_BYTES = 64 * 1024 * 1024


def read_exact_binary(stream: Any, size: int, label: str) -> bytes:
    value = stream.read(size)
    if len(value) != size:
        raise ArtifactIndexError(f"{label} is truncated")
    return value


def read_bgzf_block(stream: Any) -> bytes:
    header = read_exact_binary(stream, 12, "BGZF header")
    if (
        header[:3] != b"\x1f\x8b\x08"
        or header[3] != 4
        or struct.unpack("<H", header[10:12])[0] < 6
    ):
        raise ArtifactIndexError("BAM does not contain a valid BGZF header")
    extra_length = struct.unpack("<H", header[10:12])[0]
    extra = read_exact_binary(stream, extra_length, "BGZF extra field")
    block_size: int | None = None
    cursor = 0
    while cursor < len(extra):
        if cursor + 4 > len(extra):
            raise ArtifactIndexError("BGZF extra field is malformed")
        subfield_id = extra[cursor : cursor + 2]
        subfield_length = struct.unpack("<H", extra[cursor + 2 : cursor + 4])[0]
        cursor += 4
        if cursor + subfield_length > len(extra):
            raise ArtifactIndexError("BGZF subfield is truncated")
        if subfield_id == b"BC":
            if subfield_length != 2 or block_size is not None:
                raise ArtifactIndexError("BGZF BC subfield is invalid")
            block_size = (
                struct.unpack(
                    "<H",
                    extra[cursor : cursor + subfield_length],
                )[0]
                + 1
            )
        cursor += subfield_length
    if block_size is None:
        raise ArtifactIndexError("BGZF block lacks the required BC subfield")
    consumed = 12 + extra_length
    remaining = block_size - consumed
    if remaining < 8 or block_size > 65536:
        raise ArtifactIndexError("BGZF block size is invalid")
    body = read_exact_binary(stream, remaining, "BGZF block")
    compressed = body[:-8]
    expected_crc, expected_size = struct.unpack("<II", body[-8:])
    try:
        uncompressed = zlib.decompress(compressed, wbits=-15)
    except zlib.error as exc:
        raise ArtifactIndexError(f"BGZF deflate payload is invalid: {exc}") from exc
    if (
        len(uncompressed) != expected_size
        or zlib.crc32(uncompressed) & 0xFFFFFFFF != expected_crc
    ):
        raise ArtifactIndexError("BGZF CRC or uncompressed size is invalid")
    return uncompressed


def parse_bam_header_buffer(
    value: bytes,
) -> tuple[int, int, int] | None:
    if len(value) < 8:
        return None
    if value[:4] != b"BAM\x01":
        raise ArtifactIndexError("Decompressed BAM magic is invalid")
    header_text_bytes = struct.unpack("<i", value[4:8])[0]
    if not 0 <= header_text_bytes <= 16 * 1024 * 1024:
        raise ArtifactIndexError("BAM header text length is invalid")
    cursor = 8 + header_text_bytes
    if len(value) < cursor + 4:
        return None
    reference_count = struct.unpack("<i", value[cursor : cursor + 4])[0]
    cursor += 4
    if not 0 <= reference_count <= 1_000_000:
        raise ArtifactIndexError("BAM reference count is invalid")
    for _reference_index in range(reference_count):
        if len(value) < cursor + 4:
            return None
        name_length = struct.unpack("<i", value[cursor : cursor + 4])[0]
        cursor += 4
        if not 2 <= name_length <= 1_048_576:
            raise ArtifactIndexError("BAM reference-name length is invalid")
        if len(value) < cursor + name_length + 4:
            return None
        name = value[cursor : cursor + name_length]
        if name[-1:] != b"\x00" or b"\x00" in name[:-1]:
            raise ArtifactIndexError("BAM reference name is invalid")
        cursor += name_length
        reference_length = struct.unpack("<i", value[cursor : cursor + 4])[0]
        cursor += 4
        if reference_length <= 0:
            raise ArtifactIndexError("BAM reference length is invalid")
    return cursor, header_text_bytes, reference_count


def inspect_bgzf_bam(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size <= len(BGZF_EOF_BLOCK):
            raise ArtifactIndexError("BAM is too small to contain data and EOF")
        with path.open("rb") as stream:
            stream.seek(size - len(BGZF_EOF_BLOCK))
            if stream.read(len(BGZF_EOF_BLOCK)) != BGZF_EOF_BLOCK:
                raise ArtifactIndexError(
                    "BAM lacks the canonical terminal BGZF EOF block"
                )
            stream.seek(0)
            header_buffer = bytearray()
            parsed: tuple[int, int, int] | None = None
            while parsed is None:
                header_buffer.extend(read_bgzf_block(stream))
                if len(header_buffer) > MAX_BAM_HEADER_BYTES:
                    raise ArtifactIndexError(
                        "BAM header exceeds the bounded adapter limit"
                    )
                parsed = parse_bam_header_buffer(bytes(header_buffer))
    except ArtifactIndexError:
        raise
    except OSError as exc:
        raise ArtifactIndexError(f"Could not inspect BAM: {exc}") from exc
    _header_end, header_text_bytes, reference_count = parsed
    return {
        "bgzf_eof_present": True,
        "bam_header_text_bytes": header_text_bytes,
        "reference_count": reference_count,
    }


def read_bai_uint32(stream: Any, label: str) -> int:
    return struct.unpack("<I", read_exact_binary(stream, 4, label))[0]


def inspect_bai_structure(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        with path.open("rb") as stream:
            if read_exact_binary(stream, 4, "BAI magic") != b"BAI\x01":
                raise ArtifactIndexError("BAI signature is invalid")
            reference_count = read_bai_uint32(stream, "BAI reference count")
            if reference_count > 1_000_000 or reference_count > max(0, (size - 8) // 8):
                raise ArtifactIndexError("BAI reference count is invalid")
            bin_count = 0
            chunk_count = 0
            interval_count = 0
            for _reference_index in range(reference_count):
                reference_bin_count = read_bai_uint32(
                    stream,
                    "BAI bin count",
                )
                if reference_bin_count > (size - stream.tell()) // 8:
                    raise ArtifactIndexError("BAI bin count exceeds file size")
                seen_bins: set[int] = set()
                for _bin_index in range(reference_bin_count):
                    bin_id = read_bai_uint32(stream, "BAI bin ID")
                    if bin_id in seen_bins or bin_id > 37450:
                        raise ArtifactIndexError("BAI bin ID is invalid")
                    seen_bins.add(bin_id)
                    reference_chunk_count = read_bai_uint32(
                        stream,
                        "BAI chunk count",
                    )
                    if reference_chunk_count > (size - stream.tell()) // 16:
                        raise ArtifactIndexError("BAI chunk count exceeds file size")
                    for _chunk_index in range(reference_chunk_count):
                        chunk_start, chunk_end = struct.unpack(
                            "<QQ",
                            read_exact_binary(stream, 16, "BAI chunk"),
                        )
                        if bin_id != 37450 and chunk_end < chunk_start:
                            raise ArtifactIndexError(
                                "BAI chunk virtual offsets are reversed"
                            )
                    chunk_count += reference_chunk_count
                bin_count += reference_bin_count
                reference_interval_count = read_bai_uint32(
                    stream,
                    "BAI interval count",
                )
                if reference_interval_count > (size - stream.tell()) // 8:
                    raise ArtifactIndexError("BAI interval count exceeds file size")
                read_exact_binary(
                    stream,
                    reference_interval_count * 8,
                    "BAI intervals",
                )
                interval_count += reference_interval_count
            remainder = stream.read()
            if len(remainder) not in {0, 8}:
                raise ArtifactIndexError("BAI contains trailing malformed bytes")
    except ArtifactIndexError:
        raise
    except OSError as exc:
        raise ArtifactIndexError(f"Could not inspect BAI: {exc}") from exc
    return {
        "reference_count": reference_count,
        "bin_count": bin_count,
        "chunk_count": chunk_count,
        "interval_count": interval_count,
    }


def inspect_pdf_structure(path: Path) -> dict[str, Any]:
    try:
        size = path.stat().st_size
        if size < 64:
            raise ArtifactIndexError("PDF is too small to contain its structure")
        with path.open("rb") as stream:
            prefix = stream.read(16)
            if re.match(rb"^%PDF-(?:1\.[0-9]|2\.0)(?:\r?\n)", prefix) is None:
                raise ArtifactIndexError("PDF version header is invalid")
            stream.seek(max(0, size - 65536))
            tail = stream.read()
            match = re.search(
                rb"startxref\s+([0-9]+)\s+%%EOF\s*$",
                tail,
            )
            if match is None:
                raise ArtifactIndexError("PDF lacks a terminal startxref/EOF structure")
            startxref = int(match.group(1))
            if not 0 < startxref < size:
                raise ArtifactIndexError("PDF startxref offset is invalid")
            stream.seek(startxref)
            xref = stream.read(min(65536, size - startxref))
    except ArtifactIndexError:
        raise
    except OSError as exc:
        raise ArtifactIndexError(f"Could not inspect PDF: {exc}") from exc
    if xref.startswith(b"xref"):
        if (
            re.match(rb"xref\s+[0-9]+\s+[1-9][0-9]*", xref) is None
            or b"trailer" not in xref
            or re.search(rb"/Root\s+[0-9]+\s+[0-9]+\s+R", xref) is None
        ):
            raise ArtifactIndexError("PDF cross-reference table is invalid")
        xref_kind = "table"
    elif (
        re.match(rb"[0-9]+\s+[0-9]+\s+obj\b", xref) is not None
        and re.search(rb"/Type\s*/XRef\b", xref) is not None
        and re.search(rb"/Root\s+[0-9]+\s+[0-9]+\s+R", xref) is not None
    ):
        xref_kind = "stream"
    else:
        raise ArtifactIndexError(
            "PDF startxref does not point to a valid cross-reference object"
        )
    return {"pdf_startxref": startxref, "pdf_xref_kind": xref_kind}
