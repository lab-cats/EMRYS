"""Public run-report format dispatch without a renderer import cycle."""

from __future__ import annotations

from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    from . import bundle

    return bundle.main(argv)
