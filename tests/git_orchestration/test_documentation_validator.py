"""Independent behavior locks for the documentation validator."""

from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "git_orchestration" / "validate_documentation.py"
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


def card_text(card_id: str = "TEST-01") -> str:
    sections: list[str] = [f"# {card_id} — Fixture card", ""]
    for heading in CARD_SECTIONS:
        sections.extend((f"## {heading}", ""))
        if heading in {"Blocked by", "Completion unblocks"}:
            sections.extend(("- None.", ""))
        else:
            sections.extend(("Fixture text.", ""))
    return "\n".join(sections)


def write_fixture(root: Path) -> Path:
    repository = root / "repository"
    repository.mkdir()
    initialized = run(["git", "init", "-q", str(repository)], cwd=root)
    assert initialized.returncode == 0, initialized.stderr

    files = {
        "README.md": (
            "# Fixture repository\n\n"
            "[Task card](docs/tasks/TODO/TEST-01-fixture-card.md)\n\n"
            "[Diagram](docs/fixture.mmd)\n"
        ),
        "docs/fixture.mmd": "flowchart LR\n    A --> B\n",
        "docs/tasks/README.md": "# Task registry\n",
        "docs/tasks/TODO/README.md": "# TODO tasks\n",
        "docs/tasks/IN_PROGRESS/README.md": "# Active tasks\n",
        "docs/tasks/COMPLETED/README.md": "# Completed tasks\n",
        "docs/tasks/TODO/TEST-01-fixture-card.md": card_text(),
    }
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


def test_accepts_minimal_repository_and_reports_exact_counts(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "PASS documentation structure "
        "(6 Markdown documents, 1 task cards, 1 Mermaid sources)\n"
    )
    assert result.stderr == ""


def test_rejects_unavailable_root(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    result = validate(missing, cwd=tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith(
        f"ERROR: repository path is unavailable: {missing}:"
    )


def test_rejects_non_git_root(tmp_path: Path) -> None:
    repository = tmp_path / "not-git"
    repository.mkdir()

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith(f"ERROR: not a Git worktree: {repository}:")


def test_rejects_nested_non_root(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    nested = repository / "nested"
    nested.mkdir()

    result = validate(nested, cwd=tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        f"ERROR: repository path is not the worktree root: {nested}\n"
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
    assert result.stdout == ""
    assert result.stderr == (
        "ERROR: could not inventory *.md: inventory exploded\n"
    )


def test_aggregate_cli_diagnostics_are_complete_and_ordered(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "README.md").write_text(
        "# Fixture repository\n\n"
        "[Missing](missing.md)\n\n"
        "[Missing anchor](docs/tasks/README.md#absent)\n\n"
        "[Task card](docs/tasks/TODO/TEST-01-fixture-card.md)\n\n"
        "[Diagram](docs/fixture.mmd)\n",
        encoding="utf-8",
    )
    (repository / "docs/fixture.mmd").write_text(
        "sequenceDiagram\n```\n",
        encoding="utf-8",
    )

    result = validate(repository, cwd=tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "ERROR: Documentation gate failures:\n"
        "missing link: README.md -> missing.md\n"
        "missing anchor: README.md -> docs/tasks/README.md#absent\n"
        "invalid Mermaid declaration: docs/fixture.mmd\n"
        "Markdown fence in Mermaid source: docs/fixture.mmd\n"
    )
