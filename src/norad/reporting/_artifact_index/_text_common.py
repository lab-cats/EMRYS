"""Shared UTF-8 line admission for artifact-index text readers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .models import ArtifactIndexError


def iter_text_lines(path: Path) -> Iterable[tuple[int, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                if "\x00" in raw_line:
                    raise ArtifactIndexError(
                        f"Text line {line_number} contains a NUL byte"
                    )
                if "\r" in raw_line:
                    raise ArtifactIndexError(
                        f"Text line {line_number} contains a carriage return"
                    )
                line = raw_line.removesuffix("\n")
                yield line_number, line
    except ArtifactIndexError:
        raise
    except (OSError, UnicodeError) as exc:
        raise ArtifactIndexError(f"Could not read UTF-8 text: {exc}") from exc


def inspect_nonempty_text(path: Path) -> tuple[int, dict[str, Any]]:
    count = 0
    has_content = False
    for _line_number, line in iter_text_lines(path):
        count += 1
        has_content = has_content or bool(line.strip())
    if not has_content:
        raise ArtifactIndexError("Text file is empty")
    return count, {}
