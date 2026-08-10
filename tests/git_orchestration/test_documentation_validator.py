"""Behavior locks for documentation ownership and the compact task registry."""

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
JIT_SECTIONS = (
    "Outcome",
    "Touches",
    "Stop",
    "Context",
    "Deliverables",
    "Acceptance evidence",
    "Documentation updates",
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
    "docs/design/LOGGING_CONTRACT.md": "# Application logging contract",
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


def backlog_text(
    entries: tuple[tuple[str, str, str], ...] = (("TEST-01", "actionable", "None"),),
) -> str:
    lines = ["# Backlog", "", "Fixture registry.", ""]
    for card_id, kind, blockers in entries:
        lines.extend(
            (
                f"## {card_id} — Fixture item",
                "",
                f"- **Kind:** {kind}",
                f"- **Blocked by:** {blockers}",
                "- **Intent:** Fixture intent.",
                "- **Boundaries:** Fixture boundary.",
                "",
            )
        )
    return "\n".join(lines)


def jit_text(card_id: str = "TEST-01") -> str:
    lines = [f"# {card_id} — Fixture detail", ""]
    for heading in JIT_SECTIONS:
        lines.extend((f"## {heading}", "", "Fixture detail.", ""))
    return "\n".join(lines)


def write_fixture(root: Path) -> Path:
    repository = root / "repository"
    repository.mkdir()
    initialized = run(["git", "init", "-q", str(repository)], cwd=root)
    assert initialized.returncode == 0, initialized.stderr
    files = {
        "docs/fixture.mmd": "flowchart LR\n    A --> B\n",
        "docs/tasks/README.md": "# Task registry\n",
        "docs/tasks/BACKLOG.md": backlog_text(),
        "docs/tasks/cards/README.md": "# Just-in-time task cards\n",
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


def test_accepts_minimal_repository_and_reports_counts_without_writes(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    before = tuple(
        sorted(path.relative_to(repository) for path in repository.rglob("*"))
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert "1 actionable items, 0 proposals, 1 Mermaid sources" in result.stdout
    assert (
        tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))
        == before
    )


def test_rejects_missing_or_mislabeled_canonical_documents(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/operations/WORKFLOW.md").unlink()
    (repository / "docs/operations/RUNBOOK.md").write_text(
        "No heading.\n", encoding="utf-8"
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "missing canonical document: docs/operations/WORKFLOW.md" in result.stderr
    assert "canonical document H1 mismatch: docs/operations/RUNBOOK.md" in result.stderr


def test_rejects_stage_map_and_owner_failures(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "src/norad/contracts/STAGE_MAP.md").write_text(
        "# Semantic workflow identity and DAG\n\n"
        "| stage | Fixture | `STAGE-01` | `norad.stage.STAGE-01.v1` | `00` |\n",
        encoding="utf-8",
    )
    (repository / "src/norad/stages/STAGE-01/CONTRACT.md").unlink()
    (repository / "src/norad/reporting/README.md").unlink()

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert "STAGE_MAP identity roster must contain 14 unique owners" in result.stderr
    assert "missing cross-cutting owner documentation" in result.stderr


def test_rejects_missing_semantic_owner_after_valid_roster(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "src/norad/stages/STAGE-01/CONTRACT.md").unlink()
    shutil.rmtree(repository / "tests/stages/STAGE-02")

    result = validate(repository, cwd=tmp_path)

    assert "missing semantic-owner CONTRACT.md" in result.stderr
    assert "missing mirrored test owner: tests/stages/STAGE-02" in result.stderr


def test_rejects_returned_retired_docs_and_task_directories(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    retired = repository / "docs/operations/TASK_DELIVERY.md"
    retired.write_text("# Retired\n", encoding="utf-8")
    legacy = repository / "docs/tasks/TODO/OLD-01.md"
    legacy.parent.mkdir()
    legacy.write_text("# Old\n", encoding="utf-8")

    result = validate(repository, cwd=tmp_path)

    assert (
        "retired documentation owner returned: docs/operations/TASK_DELIVERY.md"
        in result.stderr
    )
    assert "retired task directory contains Markdown: docs/tasks/TODO" in result.stderr


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
    assert (
        result.stderr == expected
        if kind == "nested"
        else result.stderr.startswith(expected)
    )


def test_fails_closed_when_git_inventory_fails(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    real_git = shutil.which("git")
    assert real_git is not None
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        'case " $* " in\n'
        "  *\" ls-files \"*) echo 'inventory exploded' >&2; exit 17 ;;\n"
        "esac\n"
        f'exec {shlex.quote(real_git)} "$@"\n',
        encoding="utf-8",
    )
    fake_git.chmod(fake_git.stat().st_mode | stat.S_IXUSR)

    result = validate(
        repository,
        cwd=tmp_path,
        env={"PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}"},
    )

    assert result.stderr == "ERROR: could not inventory *.md: inventory exploded\n"


def test_ignores_general_markdown_links_but_rejects_bad_mermaid(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n[Missing](missing.md)\n[External](https://example.test)\n",
        encoding="utf-8",
    )
    assert validate(repository, cwd=tmp_path).returncode == 0

    (repository / "docs/fixture.mmd").write_text(
        "sequenceDiagram\n```\n", encoding="utf-8"
    )
    result = validate(repository, cwd=tmp_path)
    assert "invalid Mermaid declaration: docs/fixture.mmd" in result.stderr
    assert "Markdown fence in Mermaid source: docs/fixture.mmd" in result.stderr


def test_rejects_missing_registry_docs_and_bad_backlog_fields(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/tasks/cards/README.md").unlink()
    backlog = repository / "docs/tasks/BACKLOG.md"
    backlog.write_text(
        backlog.read_text(encoding="utf-8").replace("- **Intent:**", "- **Wrong:**"),
        encoding="utf-8",
    )

    result = validate(repository, cwd=tmp_path)

    assert "missing task-registry document: docs/tasks/cards/README.md" in result.stderr
    assert "backlog field order/count: TEST-01" in result.stderr


def test_rejects_unknown_proposal_self_and_cyclic_blockers(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/tasks/BACKLOG.md").write_text(
        backlog_text(
            (
                ("TEST-01", "actionable", "`TEST-02`"),
                ("TEST-02", "actionable", "`TEST-01`"),
                ("TEST-03", "actionable", "`MISSING-01`"),
                ("TEST-04", "actionable", "`IDEA-01`"),
                ("TEST-05", "actionable", "`TEST-05`"),
                ("IDEA-01", "proposal", "`TEST-01`"),
            )
        ),
        encoding="utf-8",
    )

    result = validate(repository, cwd=tmp_path)

    for expected in (
        "proposal has blockers: IDEA-01",
        "unknown backlog blocker: TEST-03 -> MISSING-01",
        "proposal used as blocker: TEST-04 -> IDEA-01",
        "self dependency: TEST-05",
        "backlog dependency cycle: TEST-01, TEST-02, TEST-05",
    ):
        assert expected in result.stderr


def test_rejects_duplicate_ids_kind_and_blocker_syntax(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    text = backlog_text((("TEST-01", "invalid", "BAD"),))
    text += "\n" + backlog_text((("TEST-01", "actionable", "None"),)).split("\n", 4)[4]
    (repository / "docs/tasks/BACKLOG.md").write_text(text, encoding="utf-8")

    result = validate(repository, cwd=tmp_path)

    assert "invalid backlog kind: TEST-01" in result.stderr
    assert "invalid backlog blocker list: TEST-01" in result.stderr
    assert "duplicate backlog ID: TEST-01" in result.stderr


def test_accepts_jit_card_and_status_is_read_only(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    card = repository / "docs/tasks/cards/TEST-01-fixture.md"
    card.write_text(jit_text(), encoding="utf-8")
    before = tuple(
        sorted(path.relative_to(repository) for path in repository.rglob("*"))
    )

    validation = validate(repository, cwd=tmp_path)
    status = task_status(repository, cwd=tmp_path)

    assert validation.returncode == 0, validation.stderr
    assert status.returncode == 0, status.stderr
    assert (
        "| TEST-01 | actionable | active | — | — | — | docs/tasks/cards/TEST-01-fixture.md |"
        in status.stdout
    )
    assert (
        tuple(sorted(path.relative_to(repository) for path in repository.rglob("*")))
        == before
    )


def test_rejects_unknown_proposal_and_malformed_jit_cards(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/tasks/BACKLOG.md").write_text(
        backlog_text(
            (("TEST-01", "actionable", "None"), ("IDEA-01", "proposal", "None"))
        ),
        encoding="utf-8",
    )
    cards = repository / "docs/tasks/cards"
    (cards / "MISSING-01-fixture.md").write_text(
        jit_text("MISSING-01"), encoding="utf-8"
    )
    (cards / "IDEA-01-fixture.md").write_text(jit_text("IDEA-01"), encoding="utf-8")
    malformed = jit_text().replace("## Stop\n\nFixture detail.\n\n", "")
    (cards / "WRONG-01-fixture.md").write_text(malformed, encoding="utf-8")

    result = validate(repository, cwd=tmp_path)

    assert "JIT card has unknown backlog ID: MISSING-01" in result.stderr
    assert "proposal has JIT card: IDEA-01" in result.stderr
    assert (
        "JIT card ID/filename mismatch: docs/tasks/cards/WRONG-01-fixture.md"
        in result.stderr
    )
    assert (
        "JIT card heading order/count: docs/tasks/cards/WRONG-01-fixture.md"
        in result.stderr
    )


def test_task_status_derives_readiness_reverse_edges_and_proposals(
    tmp_path: Path,
) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/tasks/BACKLOG.md").write_text(
        backlog_text(
            (
                ("TEST-01", "actionable", "None"),
                ("TEST-02", "actionable", "`TEST-01`"),
                ("IDEA-01", "proposal", "None"),
            )
        ),
        encoding="utf-8",
    )

    result = task_status(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert "| TEST-01 | actionable | planned | yes | — | TEST-02 | — |" in result.stdout
    assert "| TEST-02 | actionable | planned | no | TEST-01 | — | — |" in result.stdout
    assert "| IDEA-01 | proposal | proposal | — | — | — | — |" in result.stdout


def test_task_status_fails_closed_on_bad_registry(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    backlog = repository / "docs/tasks/BACKLOG.md"
    backlog.write_text(
        backlog.read_text(encoding="utf-8").replace(
            "- **Kind:** actionable", "- **Kind:** bad"
        ),
        encoding="utf-8",
    )

    result = task_status(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("ERROR: Task registry failures:\n")
