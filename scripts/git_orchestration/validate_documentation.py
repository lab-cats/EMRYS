#!/usr/bin/env python3
"""Validate NORAD documentation ownership and the compact task registry."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

JIT_SECTIONS = (
    "Outcome",
    "Touches",
    "Stop",
    "Context",
    "Deliverables",
    "Acceptance evidence",
    "Documentation updates",
)
BACKLOG_FIELDS = ("Kind", "Blocked by", "Intent", "Boundaries")
TASK_H1_PATTERN = re.compile(r"^([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+) — (.+)$")
BACKLOG_ENTRY_PATTERN = re.compile(
    r"^## ([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+) — (.+)$", re.MULTILINE
)
FIELD_PATTERN = re.compile(
    r"^- \*\*(Kind|Blocked by|Intent|Boundaries):\*\* (.+)$", re.MULTILINE
)
BLOCKER_LIST_PATTERN = re.compile(r"`([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)`(?:, |$)")

CANONICAL_DOCUMENTS = {
    "AGENTS.md": "# NORAD safety guard",
    "README.md": "# NORAD: CSU HPC RNA-seq and RNA-editing workflow",
    "docs/architecture/README.md": "# Architecture index",
    "docs/architecture/ARCHITECTURE.md": "# Current architecture",
    "docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md": (
        "# Current functional-owner inventory"
    ),
    "docs/architecture/FUTURE_ARCHITECTURE.md": "# Future architecture",
    "docs/design/DECISIONS.md": "# Durable decisions",
    "docs/design/LOGGING_CONTRACT.md": "# Application logging contract",
    "docs/design/PIPELINE_PLAN.md": "# NORAD pipeline plan",
    "docs/design/QUESTIONS.md": "# Open questions",
    "docs/design/TEST_BASELINE.md": "# Test baseline and contract-risk index",
    "docs/operations/HANDOFF.md": "# Project handoff",
    "docs/operations/RUNBOOK.md": "# Runbook",
    "docs/operations/TROUBLESHOOTING.md": "# Troubleshooting",
    "docs/operations/WORKFLOW.md": "# Workflow kernel",
    "docs/sitemap/README.md": "# Documentation sitemap",
    "src/norad/contracts/SOURCE_TOPOLOGY.md": (
        "# Source ownership and dependency direction"
    ),
    "src/norad/contracts/STAGE_MAP.md": "# Semantic workflow identity and DAG",
}

RETIRED_DOCUMENTS = (
    "docs/design/REFACTOR_AUDIT.md",
    "docs/operations/CONCURRENT_WORK.md",
    "docs/operations/TASK_DELIVERY.md",
    "src/norad/contracts/MIGRATION_MECHANICS.md",
)
RETIRED_TASK_DIRECTORIES = ("TODO", "IN_PROGRESS", "INTEGRATION_REVIEW", "UNREFINED")

CROSS_CUTTING_OWNER_DOCS = (
    "src/norad/contracts/artifacts/README.md",
    "src/norad/evidence/reference_provenance/README.md",
    "src/norad/evidence/runtime_preflight/README.md",
    "src/norad/evidence/storage_inventory/README.md",
    "src/norad/ingestion/sample_manifest_admission/README.md",
    "src/norad/reporting/README.md",
)
SOURCE_OWNER_DIRECTORY_NAMES = {
    ("evidence", "collect_canonical_BAM_QC_evidence"): "canonical_bam_qc",
    ("stage", "align_RNA_reads_with_STAR"): "star_alignment",
    ("stage", "construct_canonical_BAM"): "canonical_bam",
    ("stage", "construct_STAR_index"): "star_index",
    ("stage", "construct_FASTA_sidecars"): "fasta_sidecars",
    ("stage", "convert_GTF_to_BED12"): "gtf_to_bed12",
}


class DocumentationError(RuntimeError):
    """Raised when the documentation gate cannot run or finds failures."""


@dataclass(frozen=True)
class TaskCard:
    card_id: str
    title: str
    path: Path
    state: str
    kind: str
    blockers: frozenset[str]


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
        owner_name = SOURCE_OWNER_DIRECTORY_NAMES.get((kind, slug), slug)
        owner = root / "src" / "norad" / domain / owner_name
        tests = root / "tests" / domain / owner_name
        for basename in ("README.md", "CONTRACT.md"):
            if not (owner / basename).is_file():
                problems.append(
                    f"missing semantic-owner {basename}: "
                    f"{(owner / basename).relative_to(root)}"
                )
        if not tests.is_dir():
            problems.append(f"missing mirrored test owner: {tests.relative_to(root)}")


def parse_blockers(value: str, card_id: str, problems: list[str]) -> frozenset[str]:
    if value == "None":
        return frozenset()
    blockers = BLOCKER_LIST_PATTERN.findall(value)
    if not blockers or ", ".join(f"`{item}`" for item in blockers) != value:
        problems.append(f"invalid backlog blocker list: {card_id}")
        return frozenset()
    if len(blockers) != len(set(blockers)):
        problems.append(f"duplicate backlog blocker: {card_id}")
    return frozenset(blockers)


def cycle_nodes(cards: dict[str, TaskCard]) -> set[str]:
    """Return actionable IDs participating in a dependency cycle."""
    visiting: list[str] = []
    visited: set[str] = set()
    cycles: set[str] = set()

    def visit(card_id: str) -> None:
        if card_id in visiting:
            cycles.update(visiting[visiting.index(card_id) :])
            return
        if card_id in visited:
            return
        visiting.append(card_id)
        for blocker in cards[card_id].blockers:
            if blocker in cards:
                visit(blocker)
        visiting.pop()
        visited.add(card_id)

    for card_id in cards:
        visit(card_id)
    return cycles


def validate_jit_card(
    root: Path,
    path: Path,
    items: dict[str, TaskCard],
    active: dict[str, Path],
    problems: list[str],
) -> None:
    relative = path.relative_to(root)
    text = path.read_text(encoding="utf-8")
    h1s = re.findall(r"^# (.+)$", text, flags=re.MULTILINE)
    match = TASK_H1_PATTERN.fullmatch(h1s[0]) if len(h1s) == 1 else None
    if not match:
        problems.append(f"invalid JIT card H1: {relative}")
        return
    card_id = match.group(1)
    if not path.name.startswith(f"{card_id}-"):
        problems.append(f"JIT card ID/filename mismatch: {relative}")
    if card_id not in items:
        problems.append(f"JIT card has unknown backlog ID: {card_id}")
        return
    if items[card_id].kind != "actionable":
        problems.append(f"proposal has JIT card: {card_id}")
        return
    if card_id in active:
        problems.append(f"duplicate JIT card: {card_id}")
    active[card_id] = path
    headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    if headings != list(JIT_SECTIONS):
        problems.append(f"JIT card heading order/count: {relative}")
    for heading in JIT_SECTIONS:
        marker = f"## {heading}\n"
        if marker in text and not text.split(marker, 1)[1].split("\n## ", 1)[0].strip():
            problems.append(f"empty JIT card section {heading}: {relative}")


def validate_cards(root: Path, problems: list[str]) -> dict[str, TaskCard]:
    """Validate the compact backlog and any selected JIT detail."""
    task_root = root / "docs" / "tasks"
    backlog = task_root / "BACKLOG.md"
    required = (task_root / "README.md", backlog, task_root / "cards" / "README.md")
    for path in required:
        if not path.is_file():
            problems.append(f"missing task-registry document: {path.relative_to(root)}")
    for dirname in RETIRED_TASK_DIRECTORIES:
        if git_paths(root, f"docs/tasks/{dirname}/*.md"):
            problems.append(
                f"retired task directory contains Markdown: docs/tasks/{dirname}"
            )
    if not backlog.is_file():
        return {}
    if first_heading(backlog) != "# Backlog":
        problems.append("backlog H1 mismatch: docs/tasks/BACKLOG.md")

    text = backlog.read_text(encoding="utf-8")
    matches = list(BACKLOG_ENTRY_PATTERN.finditer(text))
    items: dict[str, TaskCard] = {}
    for index, match in enumerate(matches):
        card_id, title = match.groups()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : body_end]
        fields = FIELD_PATTERN.findall(body)
        if [name for name, _ in fields] != list(BACKLOG_FIELDS):
            problems.append(f"backlog field order/count: {card_id}")
            continue
        values = dict(fields)
        kind = values["Kind"]
        if kind not in {"actionable", "proposal"}:
            problems.append(f"invalid backlog kind: {card_id}")
        blockers = parse_blockers(values["Blocked by"], card_id, problems)
        if kind == "proposal" and blockers:
            problems.append(f"proposal has blockers: {card_id}")
        if card_id in items:
            problems.append(f"duplicate backlog ID: {card_id}")
            continue
        items[card_id] = TaskCard(
            card_id=card_id,
            title=title,
            path=backlog,
            state="proposal" if kind == "proposal" else "planned",
            kind=kind,
            blockers=blockers,
        )

    for card_id, item in items.items():
        if card_id in item.blockers:
            problems.append(f"self dependency: {card_id}")
        for blocker in item.blockers:
            target = items.get(blocker)
            if target is None:
                problems.append(f"unknown backlog blocker: {card_id} -> {blocker}")
            elif target.kind != "actionable":
                problems.append(f"proposal used as blocker: {card_id} -> {blocker}")
    cycles = cycle_nodes(
        {key: value for key, value in items.items() if value.kind == "actionable"}
    )
    if cycles:
        problems.append(f"backlog dependency cycle: {', '.join(sorted(cycles))}")

    active: dict[str, Path] = {}
    cards_readme = task_root / "cards" / "README.md"
    for path in sorted(git_paths(root, "docs/tasks/cards/*.md")):
        if path == cards_readme:
            continue
        validate_jit_card(root, path, items, active, problems)
    for card_id, path in active.items():
        items[card_id] = replace(items[card_id], state="active", path=path)
    return items


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


def validate(root: Path) -> tuple[int, int, int, int]:
    documents = git_paths(root, "*.md")
    diagrams = git_paths(root, "*.mmd")
    problems: list[str] = []
    validate_canonical_ownership(root, problems)
    cards = validate_cards(root, problems)
    diagram_count = validate_diagrams(diagrams, root, problems)
    if problems:
        raise DocumentationError("Documentation gate failures:\n" + "\n".join(problems))
    actionable_count = sum(card.kind == "actionable" for card in cards.values())
    proposal_count = sum(card.kind == "proposal" for card in cards.values())
    return len(documents), actionable_count, proposal_count, diagram_count


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
        document_count, actionable_count, proposal_count, diagram_count = validate(root)
    except DocumentationError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(
        f"PASS documentation structure ({document_count} Markdown documents, "
        f"{actionable_count} actionable items, {proposal_count} proposals, "
        f"{diagram_count} Mermaid sources)"
    )


if __name__ == "__main__":
    main()
