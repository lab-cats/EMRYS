"""Behavior locks for live documentation and surviving task-card validation."""

from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "git_orchestration" / "validate_documentation.py"
TASK_STATUS = REPO_ROOT / "scripts" / "git_orchestration" / "task_status.py"
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
CANONICAL_H1S = {
    "AGENTS.md": "# NORAD safety guard",
    "README.md": "# NORAD: CSU HPC RNA-seq and RNA-editing workflow",
    "docs/architecture/README.md": "# Architecture index",
    "docs/architecture/ARCHITECTURE.md": "# Current architecture",
    "docs/architecture/FUNCTIONAL_OWNER_INVENTORY.md": "# Current functional-owner inventory",
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
    "src/norad/contracts/SOURCE_TOPOLOGY.md": "# Source ownership and dependency direction",
    "src/norad/contracts/STAGE_MAP.md": "# Semantic workflow identity and DAG",
}
SEMANTIC_OWNERS = (
    ("stage", "STAGE-01"),
    ("stage", "STAGE-02"),
    ("stage", "STAGE-03"),
    ("stage", "STAGE-04"),
    ("stage", "STAGE-05"),
    ("stage", "STAGE-06"),
    ("stage", "STAGE-07"),
    ("stage", "STAGE-08"),
    ("stage", "STAGE-09"),
    ("stage", "STAGE-10"),
    ("analysis", "ANALYSIS-01"),
    ("evidence", "EVIDENCE-01"),
    ("evidence", "EVIDENCE-02"),
    ("evidence", "EVIDENCE-03"),
)
CROSS_CUTTING_DOCS = (
    "src/norad/contracts/artifacts/README.md",
    "src/norad/evidence/reference_provenance/README.md",
    "src/norad/evidence/runtime_preflight/README.md",
    "src/norad/evidence/storage_inventory/README.md",
    "src/norad/ingestion/sample_manifest_admission/README.md",
    "src/norad/reporting/README.md",
)


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    return subprocess.run(
        command,
        cwd=cwd,
        env=command_env,
        text=True,
        capture_output=True,
        check=False,
    )


def card_text(
    card_id: str = "TEST-01",
    *,
    blocked_by: str = "- None.",
    unblocks: str = "- None.",
) -> str:
    lines = [f"# {card_id} — Fixture card", ""]
    for heading in CARD_SECTIONS:
        lines.extend((f"## {heading}", ""))
        if heading == "Blocked by":
            lines.extend((blocked_by, ""))
        elif heading == "Completion unblocks":
            lines.extend((unblocks, ""))
        elif heading == "Completion record":
            lines.extend(("Not complete.", ""))
        else:
            lines.extend(("Fixture text.", ""))
    return "\n".join(lines)


def proposal_text(proposal_id: str = "IDEA-01") -> str:
    lines = [
        f"# {proposal_id} — Fixture proposal",
        "",
        "State: [`UNREFINED` proposal](README.md). Fixture only.",
        "",
    ]
    for heading in UNREFINED_SECTIONS:
        lines.extend((f"## {heading}", "", "Fixture text.", ""))
    return "\n".join(lines)


def write_fixture(root: Path) -> Path:
    repository = root / "repository"
    repository.mkdir()
    initialized = run(["git", "init", "-q", str(repository)], cwd=root)
    assert initialized.returncode == 0, initialized.stderr
    files = {
        "docs/fixture.mmd": "flowchart LR\n    A --> B\n",
        "docs/tasks/README.md": "# Task registry\n",
        "docs/tasks/TODO/README.md": "# TODO\n",
        "docs/tasks/IN_PROGRESS/README.md": "# In progress\n",
        "docs/tasks/INTEGRATION_REVIEW/README.md": "# Review\n",
        "docs/tasks/UNREFINED/README.md": "# UNREFINED\n",
        "docs/tasks/TODO/TEST-01-fixture.md": card_text(),
    }
    files.update({path: f"{h1}\n" for path, h1 in CANONICAL_H1S.items()})
    identity_rows = [
        f"| {kind} | Fixture | `{slug}` | `norad.{kind}.{slug}.v1` | `00` |"
        for kind, slug in SEMANTIC_OWNERS
    ]
    files["src/norad/contracts/STAGE_MAP.md"] = (
        "# Semantic workflow identity and DAG\n\n" + "\n".join(identity_rows) + "\n"
    )
    files.update({path: "# Owner\n" for path in CROSS_CUTTING_DOCS})
    domain_by_kind = {"stage": "stages", "analysis": "analyses", "evidence": "evidence"}
    for kind, slug in SEMANTIC_OWNERS:
        domain = domain_by_kind[kind]
        files[f"src/norad/{domain}/{slug}/README.md"] = "# Owner\n"
        files[f"src/norad/{domain}/{slug}/CONTRACT.md"] = "# Contract\n"
        files[f"tests/{domain}/{slug}/.keep"] = "fixture\n"
    for relative, text in files.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return repository


def validate(
    repository: Path,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        [sys.executable, str(VALIDATOR), "--repo", str(repository)],
        cwd=cwd,
        env=env,
    )


def task_status(repository: Path, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return run(
        [sys.executable, str(TASK_STATUS), "--repo", str(repository)],
        cwd=cwd,
    )


def add_card(
    repository: Path,
    card_id: str,
    *,
    directory: str = "TODO",
    blocked_by: str = "- None.",
    unblocks: str = "- None.",
) -> Path:
    path = repository / "docs" / "tasks" / directory / f"{card_id}-fixture.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        card_text(card_id, blocked_by=blocked_by, unblocks=unblocks),
        encoding="utf-8",
    )
    return path


def assert_failures(repository: Path, tmp_path: Path, expected: list[str]) -> None:
    result = validate(repository, cwd=tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "ERROR: Documentation gate failures:\n" + "\n".join(expected) + "\n"
    )


def test_accepts_minimal_repository_and_reports_counts_without_writes(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    before = tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "PASS documentation structure "
        "(61 Markdown documents, 1 task cards, 1 Mermaid sources)\n"
    )
    assert result.stderr == ""
    after = tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))
    assert after == before


def test_rejects_missing_or_mislabeled_canonical_documents(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs" / "operations" / "WORKFLOW.md").unlink()
    (repository / "docs" / "operations" / "RUNBOOK.md").write_text(
        "No heading.\n", encoding="utf-8"
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "missing canonical document: docs/operations/WORKFLOW.md" in result.stderr
    assert "canonical document H1 mismatch: docs/operations/RUNBOOK.md" in result.stderr


def test_rejects_missing_stage_map_without_cascading_owner_checks(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    (repository / "src" / "norad" / "contracts" / "STAGE_MAP.md").unlink()

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "missing canonical document: src/norad/contracts/STAGE_MAP.md" in result.stderr
    assert "STAGE_MAP identity roster" not in result.stderr


def test_rejects_incomplete_stage_map_identity_roster(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "src" / "norad" / "contracts" / "STAGE_MAP.md").write_text(
        "# Semantic workflow identity and DAG\n\n"
        "| stage | Fixture | `STAGE-01` | `norad.stage.STAGE-01.v1` | `00` |\n",
        encoding="utf-8",
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "STAGE_MAP identity roster must contain 14 unique owners" in result.stderr


def test_rejects_missing_semantic_and_cross_cutting_owner_docs(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "src" / "norad" / "stages" / "STAGE-01" / "CONTRACT.md").unlink()
    shutil.rmtree(repository / "tests" / "stages" / "STAGE-02")
    (repository / "src" / "norad" / "reporting" / "README.md").unlink()

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "missing semantic-owner CONTRACT.md" in result.stderr
    assert "missing mirrored test owner: tests/stages/STAGE-02" in result.stderr
    assert "missing cross-cutting owner documentation" in result.stderr


def test_rejects_returned_retired_document(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    retired = repository / "docs" / "operations" / "TASK_START.md"
    retired.write_text("# Retired\n", encoding="utf-8")

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "retired documentation owner returned: docs/operations/TASK_START.md" in result.stderr


@pytest.mark.parametrize("kind", ("missing", "non_git", "nested"))
def test_rejects_invalid_repository_roots(tmp_path: Path, kind: str) -> None:
    if kind == "missing":
        root = tmp_path / "missing"
        expected = "ERROR: repository path is unavailable:"
    elif kind == "non_git":
        root = tmp_path / "plain"
        root.mkdir()
        expected = f"ERROR: not a Git worktree: {root}:"
    else:
        repository = write_fixture(tmp_path)
        root = repository / "nested"
        root.mkdir()
        expected = f"ERROR: repository path is not the worktree root: {root}\n"

    result = validate(root, cwd=tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    if kind == "nested":
        assert result.stderr == expected
    else:
        assert result.stderr.startswith(expected)


def test_fails_closed_when_git_inventory_fails(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    real_git = shutil.which("git")
    assert real_git is not None
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        "case \" $* \" in\n"
        "  *\" ls-files \"*) echo 'inventory exploded' >&2; exit 17 ;;\n"
        "esac\n"
        f"exec {shlex.quote(real_git)} \"$@\"\n",
        encoding="utf-8",
    )
    fake_git.chmod(fake_git.stat().st_mode | stat.S_IXUSR)

    result = validate(
        repository,
        cwd=tmp_path,
        env={"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"},
    )

    assert result.returncode == 1
    assert result.stderr == "ERROR: could not inventory *.md: inventory exploded\n"


def test_ignores_missing_links_and_anchors(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n[Missing](missing.md)\n"
        + "[Missing anchor](docs/tasks/README.md#absent)\n",
        encoding="utf-8",
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr


def test_accepts_external_links_encoded_paths_and_duplicate_anchors(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    encoded = repository / "docs" / "encoded file.md"
    encoded.write_text("# Encoded heading\n\n## Repeat\n\n## Repeat\n", encoding="utf-8")
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n[HTTPS](https://example.test)\n"
        + "[Mail](mailto:test@example.test)\n"
        + "[Data](data:text/plain,fixture)\n"
        + "[Encoded](<docs/encoded%20file.md#encoded-heading>)\n"
        + "[Second](<docs/encoded%20file.md#repeat%2D1>)\n",
        encoding="utf-8",
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr


def test_ignores_frozen_history_and_card_link_targets(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    history = repository / "docs" / "history" / "frozen.md"
    history.parent.mkdir()
    history.write_text("# Frozen\n\n[Gone](../missing.md)\n", encoding="utf-8")
    card = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    card.write_text(
        card.read_text(encoding="utf-8").replace(
            "## Required context\n\nFixture text.",
            "## Required context\n\n[Gone](../COMPLETED/GONE-01.md)",
        ),
        encoding="utf-8",
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr


def test_rejects_invalid_mermaid_source(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    diagram = repository / "docs" / "fixture.mmd"
    diagram.write_text("sequenceDiagram\n```\n", encoding="utf-8")

    assert_failures(
        repository,
        tmp_path,
        [
            "invalid Mermaid declaration: docs/fixture.mmd",
            "Markdown fence in Mermaid source: docs/fixture.mmd",
        ],
    )


def test_rejects_missing_registry_readme_and_obsolete_card_location(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs" / "tasks" / "IN_PROGRESS" / "README.md").unlink()
    obsolete = repository / "docs" / "tasks" / "cards" / "OLD-01-fixture.md"
    obsolete.parent.mkdir()
    obsolete.write_text(card_text("OLD-01"), encoding="utf-8")

    assert_failures(
        repository,
        tmp_path,
        [
            "missing task-registry README: docs/tasks/IN_PROGRESS/README.md",
            "invalid card location: docs/tasks/cards/OLD-01-fixture.md",
        ],
    )


def test_rejects_card_identity_structure_and_state_declaration(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    card = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    text = card.read_text(encoding="utf-8")
    text = text.replace("# TEST-01 — Fixture card", "# WRONG-01 — Fixture card")
    text = text.replace("## Why this exists\n\nFixture text.\n\n", "")
    text = text.replace(
        "# WRONG-01 — Fixture card\n\n",
        "# WRONG-01 — Fixture card\n\nState: planned\n\n",
    )
    card.write_text(text, encoding="utf-8")

    assert_failures(
        repository,
        tmp_path,
        [
            "card ID/filename mismatch: docs/tasks/TODO/TEST-01-fixture.md",
            "card heading order/count: docs/tasks/TODO/TEST-01-fixture.md",
            "obsolete card state declaration: docs/tasks/TODO/TEST-01-fixture.md",
        ],
    )


def test_missing_blocker_is_satisfied_and_visible_in_status(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    card = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    card.write_text(
        card_text(
            blocked_by=(
                "- [DONE-01](../COMPLETED/DONE-01-fixture.md) "
                "— Required: Historical prerequisite."
            )
        ),
        encoding="utf-8",
    )

    validation = validate(repository, cwd=tmp_path)
    status = task_status(repository, cwd=tmp_path)

    assert validation.returncode == 0, validation.stderr
    assert status.returncode == 0, status.stderr
    assert "| TEST-01 | planned | yes | DONE-01 | — | " in status.stdout


def test_ignores_cross_card_cycles(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    first = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    first.write_text(
        card_text(
            "TEST-01",
            blocked_by=(
                "- [TEST-02](TEST-02-fixture.md) "
                "— Required: Second card."
            ),
            unblocks=(
                "- [TEST-02](TEST-02-fixture.md) "
                "— Partially: Second card."
            ),
        ),
        encoding="utf-8",
    )
    add_card(
        repository,
        "TEST-02",
        blocked_by=(
            "- [TEST-01](TEST-01-fixture.md) "
            "— Required: First card."
        ),
        unblocks=(
            "- [TEST-01](TEST-01-fixture.md) "
            "— Partially: First card."
        ),
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr


def test_ignores_missing_reciprocal_edge_between_surviving_cards(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    add_card(
        repository,
        "TEST-02",
        blocked_by=(
            "- [TEST-01](TEST-01-fixture.md) "
            "— Required: First card."
        ),
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr


def test_ignores_review_card_references(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    first = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    first.write_text(
        card_text(
            "TEST-01",
            unblocks=(
                "- [TEST-02](../INTEGRATION_REVIEW/TEST-02-fixture.md) "
                "— Partially: Review."
            ),
        ),
        encoding="utf-8",
    )
    add_card(
        repository,
        "TEST-02",
        directory="INTEGRATION_REVIEW",
        blocked_by=(
            "- [TEST-01](../TODO/TEST-01-fixture.md) "
            "— Required: Open prerequisite."
        ),
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr


def test_validates_unrefined_shape_without_counting_it_as_card(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    proposal = repository / "docs" / "tasks" / "UNREFINED" / "IDEA-01-fixture.md"
    proposal.write_text(proposal_text(), encoding="utf-8")

    accepted = validate(repository, cwd=tmp_path)
    assert accepted.returncode == 0, accepted.stderr
    assert "(62 Markdown documents, 1 task cards, 1 Mermaid sources)" in accepted.stdout

    proposal.write_text(
        proposal.read_text(encoding="utf-8")
        + "\n## Blocked by\n\n"
        + "- [TEST-01](../TODO/TEST-01-fixture.md) — Required: Invalid.\n",
        encoding="utf-8",
    )
    rejected = validate(repository, cwd=tmp_path)
    assert rejected.returncode == 1
    assert "actionable card heading in proposal" in rejected.stderr


def test_task_status_derives_open_edges_without_writes(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    first = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    first.write_text(
        card_text(
            "TEST-01",
            unblocks=(
                "- [TEST-02](TEST-02-fixture.md) "
                "— Fully: Only prerequisite."
            ),
        ),
        encoding="utf-8",
    )
    add_card(
        repository,
        "TEST-02",
        blocked_by=(
            "- [TEST-01](TEST-01-fixture.md) "
            "— Required: First card."
        ),
    )
    before = tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))

    result = task_status(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert "| TEST-01 | planned | yes | — | TEST-02 | " in result.stdout
    assert "| TEST-02 | planned | no | TEST-01 | — | " in result.stdout
    after = tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))
    assert after == before


def test_reports_invalid_and_duplicate_proposal_identities(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    proposal_root = repository / "docs" / "tasks" / "UNREFINED"
    (proposal_root / "BAD-01-invalid.md").write_text(
        proposal_text("BAD-01").replace(
            "# BAD-01 — Fixture proposal", "# malformed proposal"
        ),
        encoding="utf-8",
    )
    (proposal_root / "IDEA-01-one.md").write_text(
        proposal_text("IDEA-01"), encoding="utf-8"
    )
    (proposal_root / "IDEA-01-two.md").write_text(
        proposal_text("IDEA-01"), encoding="utf-8"
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "invalid proposal H1: docs/tasks/UNREFINED/BAD-01-invalid.md" in result.stderr
    assert "duplicate proposal ID: IDEA-01" in result.stderr


def test_reports_invalid_proposal_state_and_heading_orders(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    proposal_root = repository / "docs" / "tasks" / "UNREFINED"
    missing = proposal_text("IDEA-01").replace(
        "State: [`UNREFINED` proposal](README.md). Fixture only.",
        "State: invalid.",
    ).replace("## Promotion conditions", "## Extra")
    (proposal_root / "IDEA-01-missing.md").write_text(missing, encoding="utf-8")
    swapped = proposal_text("IDEA-02")
    swapped = swapped.replace("## Proposal", "## HOLD", 1)
    swapped = swapped.replace("## Why preserve it", "## Proposal", 1)
    swapped = swapped.replace("## HOLD", "## Why preserve it", 1)
    (proposal_root / "IDEA-02-swapped.md").write_text(swapped, encoding="utf-8")

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "invalid proposal state declaration" in result.stderr
    assert result.stderr.count("proposal heading order/count") == 2


def test_reports_invalid_duplicate_and_malformed_cards(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    todo = repository / "docs" / "tasks" / "TODO"
    (todo / "BAD-01-invalid.md").write_text(
        card_text("BAD-01").replace("# BAD-01 — Fixture card", "# malformed"),
        encoding="utf-8",
    )
    (todo / "TEST-01-duplicate.md").write_text(
        card_text("TEST-01"), encoding="utf-8"
    )
    malformed = add_card(
        repository,
        "BAD-02",
        blocked_by="- malformed blocker",
        unblocks="- malformed unblock",
    )
    assert malformed.is_file()

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "invalid card H1: docs/tasks/TODO/BAD-01-invalid.md" in result.stderr
    assert "duplicate card ID: TEST-01" in result.stderr
    assert "invalid Blocked by syntax: docs/tasks/TODO/BAD-02-fixture.md" in result.stderr
    assert (
        "invalid Completion unblocks syntax: docs/tasks/TODO/BAD-02-fixture.md"
        in result.stderr
    )


def test_ignores_self_dependency_and_fully_reference_semantics(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    first = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    first.write_text(
        card_text(
            "TEST-01",
            blocked_by=(
                "- [TEST-01](TEST-01-fixture.md) "
                "— Required: Invalid self edge."
            ),
            unblocks=(
                "- [TEST-01](TEST-01-fixture.md) "
                "— Partially: Invalid self edge.\n"
                "- [TEST-02](TEST-02-fixture.md) "
                "— Fully: Claims sole prerequisite."
            ),
        ),
        encoding="utf-8",
    )
    add_card(
        repository,
        "TEST-02",
        blocked_by=(
            "- [TEST-01](TEST-01-fixture.md) — Required: First.\n"
            "- [DONE-01](../COMPLETED/DONE-01.md) — Required: Historical."
        ),
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr


def test_task_status_renders_review_and_fails_closed_on_bad_registry(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    add_card(repository, "TEST-02", directory="INTEGRATION_REVIEW")

    accepted = task_status(repository, cwd=tmp_path)
    assert accepted.returncode == 0, accepted.stderr
    assert "| TEST-02 | review | — | — | — | " in accepted.stdout

    first = repository / "docs" / "tasks" / "TODO" / "TEST-01-fixture.md"
    first.write_text(
        first.read_text(encoding="utf-8").replace(
            "# TEST-01 — Fixture card\n\n",
            "# TEST-01 — Fixture card\n\nState: planned\n\n",
        ),
        encoding="utf-8",
    )
    rejected = task_status(repository, cwd=tmp_path)
    assert rejected.returncode == 1
    assert rejected.stdout == ""
    assert rejected.stderr.startswith("ERROR: Task registry failures:\n")
