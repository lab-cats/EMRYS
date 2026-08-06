#!/usr/bin/env python3
"""Render a deterministic read-only view of NORAD task-card metadata."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path

from validate_documentation import (
    DocumentationError,
    TaskCard,
    repository_root,
    validate_cards,
)


def reverse_dependencies(cards: Mapping[str, TaskCard]) -> dict[str, list[str]]:
    """Derive reverse dependency edges from the authored Blocked by edges."""
    result = {card_id: [] for card_id in cards}
    for target, card in cards.items():
        for blocker in card.blockers:
            if blocker in result:
                result[blocker].append(target)
    for targets in result.values():
        targets.sort()
    return result


def readiness(card: TaskCard, cards: Mapping[str, TaskCard]) -> str:
    """Return readiness derived only from state and direct blocker state."""
    if card.state != "planned":
        return "—"
    return (
        "yes"
        if all(cards[blocker].state == "completed" for blocker in card.blockers)
        else "no"
    )


def render_markdown(root: Path, cards: Mapping[str, TaskCard]) -> str:
    """Render a stable Markdown projection without checkout-specific facts."""
    reverse = reverse_dependencies(cards)
    lines = [
        "# Task status",
        "",
        "Generated from card metadata; this output is a view, not registry authority.",
        "",
        "| ID | State | State source | Ready | Blocked by | Unblocks | Path |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for card_id in sorted(cards):
        card = cards[card_id]
        blockers = ", ".join(sorted(card.blockers)) or "—"
        unblocks = ", ".join(reverse[card_id]) or "—"
        source = "explicit" if card.explicit_state else "legacy path"
        path = card.path.relative_to(root).as_posix()
        lines.append(
            f"| {card_id} | {card.state} | {source} | "
            f"{readiness(card, cards)} | {blockers} | {unblocks} | {path} |"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render deterministic NORAD task state and readiness."
    )
    parser.add_argument(
        "--repo",
        required=True,
        type=Path,
        help="exact Git worktree root to inspect",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        root = repository_root(args.repo)
        problems: list[str] = []
        cards = validate_cards(root, problems)
        if problems:
            raise DocumentationError(
                "Task registry failures:\n" + "\n".join(problems)
            )
    except DocumentationError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(render_markdown(root, cards), end="")


if __name__ == "__main__":
    main()
