#!/usr/bin/env python3
"""Validate EMRYS documentation ownership and local structure."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

from markdown_it import MarkdownIt

CANONICAL_DOCUMENTS = {
    "AGENTS.md": "# EMRYS safety guard",
    "README.md": "# EMRYS: Epic Molecular Read Yield System",
    "quickstart.md": "# EMRYS quickstart: synthetic Project to Results",
    "configs/README.md": "# Configuration and input guide",
    "docs/README.md": "# Documentation",
    "docs/architecture/README.md": "# Architecture index",
    "docs/architecture/ARCHITECTURE.md": "# Current architecture",
    "docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md": (
        "# Current functional-owner inventory"
    ),
    "docs/design/DECISIONS.md": "# Durable decisions",
    "docs/design/LOGGING_CONTRACT.md": "# Application logging contract",
    "docs/design/TEST_BASELINE.md": "# Test baseline and contract-risk index",
    "docs/history/validation-evidence.md": "# Dated validation evidence",
    "docs/operations/RUNBOOK.md": "# Runbook",
    "docs/operations/TROUBLESHOOTING.md": "# Troubleshooting",
    "docs/operations/WORKFLOW.md": "# Workflow kernel",
    "docs/tasks/README.md": "# Task planning",
    "docs/tasks/backlog_matrix.md": "# EMRYS backlog matrix",
    "src/emrys/contracts/SOURCE_TOPOLOGY.md": (
        "# Source ownership and dependency direction"
    ),
    "src/emrys/contracts/STAGE_MAP.md": "# Semantic workflow identity and DAG",
}

RETIRED_DOCUMENTS = (
    "docs/architecture/FUTURE_ARCHITECTURE.md",
    "docs/architecture/diagrams/future_modular_pipeline.mmd",
    "docs/architecture/diagrams/future_reporting_layer.mmd",
    "docs/design/PIPELINE_PLAN.md",
    "docs/design/QUESTIONS.md",
    "docs/design/REFACTOR_AUDIT.md",
    "docs/design/ORCHESTRATION_CONTRACT.md",
    "docs/design/ORCHESTRATION_READINESS.md",
    "docs/operations/CONCURRENT_WORK.md",
    "docs/operations/HANDOFF.md",
    "docs/operations/LOCAL_PILOT_LAUNCHER_TEST_PLAN.md",
    "docs/operations/TASK_DELIVERY.md",
    "docs/sitemap/README.md",
    "docs/tasks/architecture_backlog_matrix.md",
    "docs/tasks/architecture_campaign.md",
    "docs/tasks/BACKLOG.md",
    "docs/tasks/cards/README.md",
    "src/emrys/contracts/MIGRATION_MECHANICS.md",
)
RETIRED_TASK_DIRECTORIES = (
    "TODO",
    "IN_PROGRESS",
    "INTEGRATION_REVIEW",
    "UNREFINED",
    "cards",
)

SOURCE_OWNER_DIRECTORY_NAMES = {
    (
        "analysis",
        "rank_cohort_candidates_with_paired_CMH",
    ): "paired_cmh_candidate_ranking",
    (
        "analysis",
        "project_candidate_scientific_context",
    ): "paired_cmh_candidate_ranking/scientific_context_projection",
    ("evidence", "collect_canonical_BAM_QC_evidence"): "canonical_bam_qc",
    ("evidence", "collect_RSeQC_paired_orientation_evidence"): "rseqc_orientation",
    ("stage", "align_RNA_reads_with_STAR"): "star_alignment",
    ("stage", "construct_canonical_BAM"): "canonical_bam",
    ("stage", "construct_STAR_index"): "star_index",
    ("stage", "construct_FASTA_sidecars"): "fasta_sidecars",
    ("stage", "convert_GTF_to_BED12"): "gtf_to_bed12",
    ("stage", "mark_BAM_duplicates_with_Picard"): "duplicate_marking",
    (
        "stage",
        "partition_BAM_by_mechanical_read_orientation",
    ): "mechanical_orientation",
    (
        "stage",
        "generate_partitioned_cohort_mpileup_VCFs",
    ): "partitioned_cohort_mpileup",
    (
        "stage",
        "preprocess_and_annotate_cohort_candidates",
    ): "cohort_candidate_preprocessing",
    ("stage", "split_N_cigar_reads_with_GATK"): "split_n_cigar",
}


class DocumentationError(RuntimeError):
    """Raised when the documentation gate cannot run or finds failures."""


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


def markdown_anchors(path: Path) -> set[str]:
    """Return GitHub-style heading anchors outside fenced code blocks."""
    anchors: set[str] = set()
    occurrences: dict[str, int] = {}
    fenced = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        match = None if fenced else re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if match is None:
            continue
        plain = re.sub(r"<[^>]+>", "", match.group(1)).lower()
        base = re.sub(r"[^\w\- ]", "", plain)
        base = re.sub(r"\s+", "-", base.strip())
        count = occurrences.get(base, 0)
        occurrences[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def markdown_destinations(value: str) -> list[str]:
    """Return CommonMark link and image destinations."""
    destinations: list[str] = []
    for token in MarkdownIt("commonmark").parse(value):
        for child in token.children or ():
            attribute = {"link_open": "href", "image": "src"}.get(child.type)
            if attribute is not None and (target := child.attrGet(attribute)) is not None:
                destinations.append(target)
    return destinations


def validate_local_links(
    documents: list[Path], root: Path, problems: list[str]
) -> None:
    """Reject missing repository-local Markdown destinations and anchors."""
    anchor_cache: dict[Path, set[str]] = {}
    for document in documents:
        relative = document.relative_to(root)
        for raw_target in markdown_destinations(document.read_text(encoding="utf-8")):
            target = raw_target.strip().strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            path_text, _, fragment = target.partition("#")
            path_text = unquote(path_text.split("?", 1)[0])
            destination = document if not path_text else document.parent / path_text
            try:
                destination = destination.resolve()
                destination.relative_to(root)
            except (OSError, ValueError):
                problems.append(f"local link leaves repository: {relative}: {target}")
                continue
            if not destination.exists():
                problems.append(f"missing local link target: {relative}: {target}")
                continue
            if fragment and destination.is_file() and destination.suffix.lower() == ".md":
                anchors = anchor_cache.setdefault(destination, markdown_anchors(destination))
                if unquote(fragment).lower() not in anchors:
                    problems.append(f"missing local link anchor: {relative}: {target}")


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

    stage_map = root / "src" / "emrys" / "contracts" / "STAGE_MAP.md"
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
        owner = root / "src" / "emrys" / domain / owner_name
        tests = root / "tests" / domain / owner_name
        for basename in ("README.md", "CONTRACT.md"):
            if not (owner / basename).is_file():
                problems.append(
                    f"missing semantic-owner {basename}: "
                    f"{(owner / basename).relative_to(root)}"
                )
        if not tests.is_dir():
            problems.append(f"missing mirrored test owner: {tests.relative_to(root)}")


def validate_retired_task_directories(root: Path, problems: list[str]) -> None:
    """Reject Markdown that revives a retired task-detail directory."""
    for dirname in RETIRED_TASK_DIRECTORIES:
        if git_paths(root, f"docs/tasks/{dirname}/*.md"):
            problems.append(
                f"retired task directory contains Markdown: docs/tasks/{dirname}"
            )


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


def validate(root: Path) -> tuple[int, int]:
    documents = git_paths(root, "*.md")
    diagrams = git_paths(root, "*.mmd")
    problems: list[str] = []
    validate_canonical_ownership(root, problems)
    validate_retired_task_directories(root, problems)
    validate_local_links(documents, root, problems)
    diagram_count = validate_diagrams(diagrams, root, problems)
    if problems:
        raise DocumentationError("Documentation gate failures:\n" + "\n".join(problems))
    return len(documents), diagram_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate EMRYS documentation ownership and local structure."
    )
    parser.add_argument("--repo", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        root = repository_root(args.repo)
        document_count, diagram_count = validate(root)
    except DocumentationError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(
        f"PASS documentation structure ({document_count} Markdown documents, "
        f"{diagram_count} Mermaid sources)"
    )


if __name__ == "__main__":
    main()
