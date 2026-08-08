#!/usr/bin/env python3
"""Validate NORAD documentation ownership and local document structure."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

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
TASK_H1_PATTERN = re.compile(r"^([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+) — .+$")
UNREFINED_STATE_PATTERN = re.compile(
    r"State: \[`UNREFINED` proposal\]\(README\.md\)\.(?: .+)?"
)

CANONICAL_DOCUMENTS = {
    "AGENTS.md": "# NORAD safety guard",
    "README.md": "# NORAD: CSU HPC RNA-seq and RNA-editing workflow",
    "docs/architecture/README.md": "# Architecture index",
    "docs/architecture/ARCHITECTURE.md": "# Current architecture",
    "docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md": (
        "# Current functional-owner inventory"
    ),
    "docs/architecture/FUTURE_ARCHITECTURE.md": "# Future architecture",
    "docs/architecture/PIPELINE_OVERVIEW.md": "# Current pipeline overview",
    "docs/design/DECISIONS.md": "# Durable decisions",
    "docs/design/PIPELINE_PLAN.md": "# NORAD pipeline plan",
    "docs/design/QUESTIONS.md": "# Open questions",
    "docs/design/REFACTOR_AUDIT.md": "# Refactor audit index and recheck triggers",
    "docs/design/TEST_BASELINE.md": "# Test baseline and contract-risk index",
    "docs/operations/HANDOFF.md": "# Project handoff",
    "docs/operations/RUNBOOK.md": "# Runbook",
    "docs/operations/TROUBLESHOOTING.md": "# Troubleshooting",
    "docs/operations/WORKFLOW.md": "# Workflow kernel",
    "docs/sitemap/DOCUMENTATION_OWNERSHIP.md": "# Documentation ownership",
    "docs/sitemap/README.md": "# Documentation sitemap",
    "docs/sitemap/TOP_LEVEL.md": "# Top-level documentation map",
    "src/norad/contracts/SOURCE_TOPOLOGY.md": (
        "# Source ownership and dependency direction"
    ),
    "src/norad/contracts/STAGE_MAP.md": "# Semantic workflow identity and DAG",
}

RETIRED_DOCUMENTS = (
    "docs/operations/CONCURRENT_WORK.md",
    "docs/operations/TASK_DELIVERY.md",
    "docs/operations/TASK_START.md",
    "src/norad/contracts/MIGRATION_MECHANICS.md",
)

CROSS_CUTTING_OWNER_DOCS = (
    "src/norad/contracts/artifacts/README.md",
    "src/norad/evidence/reference_provenance/README.md",
    "src/norad/evidence/runtime_preflight/README.md",
    "src/norad/evidence/storage_inventory/README.md",
    "src/norad/ingestion/sample_manifest_admission/README.md",
    "src/norad/reporting/README.md",
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
        raise DocumentationError(
            f"repository path is unavailable: {value}: {exc}"
        ) from exc
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


def first_heading(path: Path) -> str:
    """Return the first Markdown H1, or an empty string."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line
    return ""


def validate_canonical_ownership(root: Path, problems: list[str]) -> None:
    """Validate the small canonical kernel and mechanically derived owners."""
    for relative, expected_h1 in CANONICAL_DOCUMENTS.items():
        path = root / relative
        if not path.is_file():
            problems.append(f"missing canonical document: {relative}")
        elif first_heading(path) != expected_h1:
            problems.append(f"canonical document H1 mismatch: {relative}")

    for relative in RETIRED_DOCUMENTS:
        if (root / relative).is_file():
            problems.append(f"retired documentation owner returned: {relative}")

    for relative in CROSS_CUTTING_OWNER_DOCS:
        if not (root / relative).is_file():
            problems.append(f"missing cross-cutting owner documentation: {relative}")

    stage_map = root / "src" / "norad" / "contracts" / "STAGE_MAP.md"
    if not stage_map.is_file():
        return
    identity_pattern = re.compile(
        r"^\| (stage|analysis|evidence) \| [^|]+ \| `([^`]+)` \|",
        flags=re.MULTILINE,
    )
    identities = identity_pattern.findall(stage_map.read_text(encoding="utf-8"))
    if len(identities) != 14 or len({slug for _, slug in identities}) != 14:
        problems.append("STAGE_MAP identity roster must contain 14 unique owners")
        return
    domain_by_kind = {"stage": "stages", "analysis": "analyses", "evidence": "evidence"}
    for kind, slug in identities:
        domain = domain_by_kind[kind]
        owner = root / "src" / "norad" / domain / slug
        tests = root / "tests" / domain / slug
        for basename in ("README.md", "CONTRACT.md"):
            if not (owner / basename).is_file():
                problems.append(
                    f"missing semantic-owner {basename}: "
                    f"{(owner / basename).relative_to(root)}"
                )
        if not tests.is_dir():
            problems.append(f"missing mirrored test owner: {tests.relative_to(root)}")


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
    indices = [
        headings.index(value)
        for value in UNREFINED_SECTIONS
        if headings.count(value) == 1
    ]
    if len(indices) != len(UNREFINED_SECTIONS) or indices != sorted(indices):
        problems.append(f"proposal heading order/count: {relative}")
    if any(heading in CARD_SECTIONS for heading in headings):
        problems.append(f"actionable card heading in proposal: {relative}")
    return proposal_id


def validate_cards(root: Path, problems: list[str]) -> dict[str, TaskCard]:
    """Validate card-local structure without judging cross-card references."""
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
    required_pattern = re.compile(r"^- \[([A-Z0-9-]+)\]\([^)]+\.md\) — Required: .+$")
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
            unblock_lines = [
                line for line in unblocks_text.splitlines() if line.strip()
            ]
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
    return cards


def validate_diagrams(diagrams: list[Path], root: Path, problems: list[str]) -> int:
    """Validate standalone Mermaid syntax without requiring inbound links."""
    for diagram in diagrams:
        meaningful = [
            line.strip()
            for line in diagram.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not meaningful or not re.fullmatch(
            r"flowchart (LR|RL|TB|BT|TD)", meaningful[0]
        ):
            problems.append(f"invalid Mermaid declaration: {diagram.relative_to(root)}")
        if "```" in diagram.read_text(encoding="utf-8"):
            problems.append(
                f"Markdown fence in Mermaid source: {diagram.relative_to(root)}"
            )
    return len(diagrams)


def validate(root: Path) -> tuple[int, int, int]:
    documents = git_paths(root, "*.md")
    diagrams = git_paths(root, "*.mmd")
    problems: list[str] = []
    validate_canonical_ownership(root, problems)
    cards = validate_cards(root, problems)
    diagram_count = validate_diagrams(diagrams, root, problems)
    if problems:
        raise DocumentationError("Documentation gate failures:\n" + "\n".join(problems))
    return len(documents), len(cards), diagram_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate NORAD documentation ownership and local structure."
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
