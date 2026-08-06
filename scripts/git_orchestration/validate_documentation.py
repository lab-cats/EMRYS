#!/usr/bin/env python3
"""Validate live documentation, surviving task cards, and Mermaid sources."""

from __future__ import annotations

import argparse
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


CARD_SECTIONS = (
    "Objective",
    "Why this exists",
    "Fixed decisions",
    "Blocked by",
    "Completion unblocks",
    "Prerequisites",
    "Required context",
    "Questions owned by this card",
    "In scope",
    "Out of scope",
    "Deliverables",
    "Acceptance evidence",
    "Canonical documentation updates",
    "Escalation conditions",
    "Completion record",
)
UNREFINED_SECTIONS = (
    "Proposal",
    "Why preserve it",
    "Settled boundaries",
    "Questions before refinement",
    "Promotion conditions",
)
CARD_STATE_BY_DIRECTORY = {
    "TODO": "planned",
    "IN_PROGRESS": "planned",
    "INTEGRATION_REVIEW": "review",
}
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "data:")
TASK_H1_PATTERN = re.compile(r"^([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+) — .+$")
UNREFINED_STATE_PATTERN = re.compile(
    r"State: \[`UNREFINED` proposal\]\(README\.md\)\.(?: .+)?"
)


class DocumentationError(RuntimeError):
    """Raised when the documentation gate cannot run or finds failures."""


@dataclass(frozen=True)
class TaskCard:
    card_id: str
    path: Path
    state: str
    blockers: frozenset[str]
    unblocks: dict[str, str]


def git_paths(root: Path, pattern: str) -> list[Path]:
    """Return present tracked or untracked, non-ignored paths."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            pattern,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise DocumentationError(f"could not inventory {pattern}: {detail}")
    paths = (root / value for value in result.stdout.splitlines())
    return [path for path in paths if path.is_file()]


def repository_root(value: Path) -> Path:
    """Resolve and verify the exact root of one Git worktree."""
    try:
        root = value.resolve(strict=True)
    except OSError as exc:
        raise DocumentationError(f"repository path is unavailable: {value}: {exc}") from exc
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise DocumentationError(f"not a Git worktree: {root}: {detail}")
    if Path(result.stdout.strip()).resolve() != root:
        raise DocumentationError(f"repository path is not the worktree root: {root}")
    return root


def anchors(document: Path) -> set[str]:
    """Return GitHub-style Markdown anchors."""
    counts: dict[str, int] = {}
    result: set[str] = set()
    for line in document.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        heading = re.sub(r"<[^>]*>", "", match.group(1)).lower()
        base = re.sub(r"[^\w\- ]", "", heading).replace(" ", "-")
        number = counts.get(base, 0)
        counts[base] = number + 1
        result.add(base if number == 0 else f"{base}-{number}")
    return result


def frozen_link_source(root: Path, document: Path) -> bool:
    """Return whether link targets in this archived or temporary record are frozen."""
    parts = document.relative_to(root).parts
    if parts[:2] == ("docs", "history"):
        return True
    return (
        len(parts) >= 4
        and parts[:2] == ("docs", "tasks")
        and parts[2] in {*CARD_STATE_BY_DIRECTORY, "UNREFINED"}
        and document.name != "README.md"
    )


def validate_links(
    root: Path,
    documents: Iterable[Path],
    problems: list[str],
) -> dict[Path, set[Path]]:
    """Validate live local links and collect inbound references."""
    document_list = list(documents)
    document_anchors = {document: anchors(document) for document in document_list}
    inbound: dict[Path, set[Path]] = {}
    for document in document_list:
        if frozen_link_source(root, document):
            continue
        text = document.read_text(encoding="utf-8")
        for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            raw_target = raw_target.strip().strip("<>")
            if raw_target.startswith(EXTERNAL_SCHEMES):
                continue
            path_text, separator, fragment = raw_target.partition("#")
            path = (
                document
                if not path_text
                else (document.parent / unquote(path_text)).resolve()
            )
            if not path.exists():
                problems.append(
                    f"missing link: {document.relative_to(root)} -> {raw_target}"
                )
                continue
            inbound.setdefault(path, set()).add(document)
            if separator and path.suffix == ".md":
                if unquote(fragment).lower() not in document_anchors.get(path, set()):
                    problems.append(
                        f"missing anchor: {document.relative_to(root)} -> {raw_target}"
                    )
    return inbound


def card_section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    return text.split(marker, 1)[1].split("\n## ", 1)[0].strip()


def card_identity(path: Path, text: str, kind: str, problems: list[str]) -> str | None:
    titles = re.findall(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    match = TASK_H1_PATTERN.fullmatch(titles[0]) if len(titles) == 1 else None
    if not match:
        problems.append(f"invalid {kind} H1: {path}")
        return None
    card_id = match.group(1)
    if not path.name.startswith(f"{card_id}-"):
        problems.append(f"{kind} ID/filename mismatch: {path}")
    return card_id


def validate_proposal(root: Path, path: Path, problems: list[str]) -> str | None:
    relative = path.relative_to(root)
    text = path.read_text(encoding="utf-8")
    proposal_id = card_identity(relative, text, "proposal", problems)
    state_lines = re.findall(r"^State: .+$", text, flags=re.MULTILINE)
    if len(state_lines) != 1 or not UNREFINED_STATE_PATTERN.fullmatch(state_lines[0]):
        problems.append(f"invalid proposal state declaration: {relative}")
    headings = re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)
    prior_index = -1
    valid_heading_order = True
    for required_heading in UNREFINED_SECTIONS:
        if headings.count(required_heading) != 1:
            valid_heading_order = False
            break
        heading_index = headings.index(required_heading)
        if heading_index <= prior_index:
            valid_heading_order = False
            break
        prior_index = heading_index
    if not valid_heading_order:
        problems.append(f"proposal heading order/count: {relative}")
    if any(heading in CARD_SECTIONS for heading in headings):
        problems.append(f"actionable card heading in proposal: {relative}")
    if re.search(
        r"^- \[[A-Z0-9-]+\]\([^)]+\.md\) — (?:Required|Fully|Partially):",
        text,
        flags=re.MULTILINE,
    ):
        problems.append(f"dependency edge in proposal: {relative}")
    return proposal_id


def validate_cards(root: Path, problems: list[str]) -> dict[str, TaskCard]:
    """Validate surviving card structure and dependency semantics."""
    task_root = root / "docs" / "tasks"
    required_readmes = {
        task_root / "README.md",
        task_root / "TODO" / "README.md",
        task_root / "IN_PROGRESS" / "README.md",
        task_root / "INTEGRATION_REVIEW" / "README.md",
        task_root / "UNREFINED" / "README.md",
    }
    for readme in sorted(required_readmes):
        if not readme.is_file():
            problems.append(f"missing task-registry README: {readme.relative_to(root)}")

    cards: dict[str, TaskCard] = {}
    identifiers: set[str] = set()
    required_pattern = re.compile(
        r"^- \[([A-Z0-9-]+)\]\([^)]+\.md\) — Required: .+$"
    )
    unblock_pattern = re.compile(
        r"^- \[([A-Z0-9-]+)\]\([^)]+\.md\) — (Fully|Partially): .+$"
    )

    for path in sorted(task_root.rglob("*.md")):
        if path in required_readmes:
            continue
        relative = path.relative_to(root)
        if path.parent == task_root / "UNREFINED":
            proposal_id = validate_proposal(root, path, problems)
            if proposal_id:
                if proposal_id in identifiers:
                    problems.append(f"duplicate proposal ID: {proposal_id}")
                identifiers.add(proposal_id)
            continue
        if (
            path.parent.parent != task_root
            or path.parent.name not in CARD_STATE_BY_DIRECTORY
        ):
            problems.append(f"invalid card location: {relative}")
            continue

        text = path.read_text(encoding="utf-8")
        card_id = card_identity(relative, text, "card", problems)
        if card_id is None:
            continue
        if card_id in identifiers:
            problems.append(f"duplicate card ID: {card_id}")
        identifiers.add(card_id)

        headings = re.findall(r"^##\s+(.+)$", text, flags=re.MULTILINE)
        structurally_valid = headings == list(CARD_SECTIONS)
        if not structurally_valid:
            problems.append(f"card heading order/count: {relative}")
        if re.search(r"^State: .+$", text, flags=re.MULTILINE):
            problems.append(f"obsolete card state declaration: {relative}")

        blockers: frozenset[str] = frozenset()
        unblocks: dict[str, str] = {}
        if structurally_valid:
            blocked_text = card_section(text, "Blocked by")
            blocked_lines = [line for line in blocked_text.splitlines() if line.strip()]
            if blocked_lines != ["- None."] and not all(
                required_pattern.fullmatch(line) for line in blocked_lines
            ):
                problems.append(f"invalid Blocked by syntax: {relative}")
            blockers = frozenset(re.findall(r"\[([A-Z0-9-]+)\]\(", blocked_text))

            unblocks_text = card_section(text, "Completion unblocks")
            unblock_lines = [line for line in unblocks_text.splitlines() if line.strip()]
            if unblock_lines != ["- None."] and not all(
                unblock_pattern.fullmatch(line) for line in unblock_lines
            ):
                problems.append(f"invalid Completion unblocks syntax: {relative}")
            unblocks = {
                target: mode
                for target, mode in re.findall(
                    r"\[([A-Z0-9-]+)\]\([^)]+\) — (Fully|Partially):",
                    unblocks_text,
                )
            }

        cards[card_id] = TaskCard(
            card_id=card_id,
            path=path,
            state=CARD_STATE_BY_DIRECTORY[path.parent.name],
            blockers=blockers,
            unblocks=unblocks,
        )

    for target, card in cards.items():
        for source in card.blockers:
            if source == target:
                problems.append(f"self dependency: {target}")
            elif source in cards and target not in cards[source].unblocks:
                problems.append(f"missing reciprocal unblock: {source} -> {target}")
    for source, card in cards.items():
        for target, mode in card.unblocks.items():
            if target in cards and mode == "Fully" and cards[target].blockers != {source}:
                problems.append(f"invalid Fully relationship: {source} -> {target}")

    visiting: list[str] = []
    visited: set[str] = set()

    def visit(card_id: str) -> None:
        if card_id in visiting:
            problems.append("dependency cycle: " + " -> ".join(visiting + [card_id]))
            return
        if card_id in visited:
            return
        visiting.append(card_id)
        for dependency in cards[card_id].blockers:
            if dependency in cards:
                visit(dependency)
        visiting.pop()
        visited.add(card_id)

    for card_id in cards:
        visit(card_id)

    for card_id, card in cards.items():
        if card.state == "review":
            for dependency in card.blockers:
                if dependency in cards:
                    problems.append(
                        f"review card has incomplete blocker: {card_id} <- {dependency}"
                    )
    return cards


def validate_diagrams(
    root: Path,
    diagrams: Iterable[Path],
    inbound: dict[Path, set[Path]],
    problems: list[str],
) -> int:
    diagram_list = list(diagrams)
    for diagram in diagram_list:
        text = diagram.read_text(encoding="utf-8")
        meaningful = [line.strip() for line in text.splitlines() if line.strip()]
        if not meaningful or not re.fullmatch(
            r"flowchart (LR|RL|TB|BT|TD)", meaningful[0]
        ):
            problems.append(f"invalid Mermaid declaration: {diagram.relative_to(root)}")
        if "```" in text:
            problems.append(f"Markdown fence in Mermaid source: {diagram.relative_to(root)}")
        if not (inbound.get(diagram, set()) - {diagram}):
            problems.append(f"orphan Mermaid source: {diagram.relative_to(root)}")
    return len(diagram_list)


def validate(root: Path) -> tuple[int, int, int]:
    documents = git_paths(root, "*.md")
    diagrams = git_paths(root, "*.mmd")
    problems: list[str] = []
    inbound = validate_links(root, documents, problems)
    cards = validate_cards(root, problems)
    diagram_count = validate_diagrams(root, diagrams, inbound, problems)
    if problems:
        raise DocumentationError("Documentation gate failures:\n" + "\n".join(problems))
    return len(documents), len(cards), diagram_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate NORAD live documentation, task cards, and diagrams."
    )
    parser.add_argument("--repo", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        root = repository_root(args.repo)
        document_count, card_count, diagram_count = validate(root)
    except DocumentationError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(
        f"PASS documentation structure ({document_count} Markdown documents, "
        f"{card_count} task cards, {diagram_count} Mermaid sources)"
    )


if __name__ == "__main__":
    main()
