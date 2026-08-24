#!/usr/bin/env python3
"""Render a deterministic read-only view of the compact EMRYS backlog."""

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
    result = {card_id: [] for card_id in cards}
    for target, card in cards.items():
        for blocker in card.blockers:
            result[blocker].append(target)
    for targets in result.values():
        targets.sort()
    return result


def readiness(card: TaskCard) -> str:
    if card.kind != "actionable" or card.state == "active":
        return "—"
    return "yes" if not card.blockers else "no"


def render_markdown(root: Path, cards: Mapping[str, TaskCard]) -> str:
    reverse = reverse_dependencies(cards)
    lines = [
        "# Task status",
        "",
        "Generated from the compact backlog and JIT cards; this output is not registry authority.",
        "",
        "| ID | Kind | State | Ready | Blocked by | Unblocks | Detail |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for card_id in sorted(cards):
        card = cards[card_id]
        blockers = ", ".join(sorted(card.blockers)) or "—"
        unblocks = ", ".join(reverse[card_id]) or "—"
        detail = (
            card.path.relative_to(root).as_posix() if card.state == "active" else "—"
        )
        lines.append(
            f"| {card_id} | {card.kind} | {card.state} | {readiness(card)} | "
            f"{blockers} | {unblocks} | {detail} |"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render deterministic EMRYS backlog status."
    )
    parser.add_argument("--repo", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        root = repository_root(args.repo)
        problems: list[str] = []
        cards = validate_cards(root, problems)
        if problems:
            raise DocumentationError("Task registry failures:\n" + "\n".join(problems))
    except DocumentationError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(render_markdown(root, cards), end="")


if __name__ == "__main__":
    main()
