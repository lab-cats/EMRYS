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


def card_path(
    repository: Path,
    card_id: str = "TEST-01",
    *,
    status: str = "TODO",
) -> Path:
    return repository / "docs" / "tasks" / status / f"{card_id}-fixture-card.md"


def add_card(
    repository: Path,
    card_id: str,
    *,
    status: str = "TODO",
) -> Path:
    path = card_path(repository, card_id, status=status)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(card_text(card_id), encoding="utf-8")
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + f"\n[{card_id}]({path.relative_to(repository).as_posix()})\n",
        encoding="utf-8",
    )
    return path


def replace_card_section(path: Path, heading: str, lines: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    marker = f"## {heading}\n\n- None."
    replacement = f"## {heading}\n\n" + "\n".join(lines)
    assert marker in text
    path.write_text(text.replace(marker, replacement), encoding="utf-8")


def assert_failures(
    repository: Path,
    *,
    cwd: Path,
    expected: list[str],
) -> None:
    result = validate(repository, cwd=cwd)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        "ERROR: Documentation gate failures:\n" + "\n".join(expected) + "\n"
    )


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


def test_requires_each_task_registry_readme(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/tasks/TODO/README.md").unlink()

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["missing task-registry README: docs/tasks/TODO/README.md"],
    )


def test_rejects_card_outside_current_lifecycle_locations(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    path = repository / "docs/tasks/UNREFINED/TEST-02-fixture-card.md"
    path.parent.mkdir()
    path.write_text(card_text("TEST-02"), encoding="utf-8")
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n[TEST-02](docs/tasks/UNREFINED/TEST-02-fixture-card.md)\n",
        encoding="utf-8",
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "invalid card location: "
            "docs/tasks/UNREFINED/TEST-02-fixture-card.md"
        ],
    )


def test_requires_one_canonical_card_h1(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    path = card_path(repository)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "# TEST-01 — Fixture card", "# TEST-01 Fixture card"
        ),
        encoding="utf-8",
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["invalid card H1: docs/tasks/TODO/TEST-01-fixture-card.md"],
    )


def test_requires_card_id_to_match_filename(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    old_path = card_path(repository)
    new_path = old_path.with_name("WRONG-01-fixture-card.md")
    old_path.rename(new_path)
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(old_path.name, new_path.name),
        encoding="utf-8",
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "card ID/filename mismatch: "
            "docs/tasks/TODO/WRONG-01-fixture-card.md"
        ],
    )


def test_rejects_duplicate_card_ids(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    duplicate = repository / "docs/tasks/TODO/TEST-01-second-card.md"
    duplicate.write_text(card_text(), encoding="utf-8")
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8")
        + "\n[Duplicate](docs/tasks/TODO/TEST-01-second-card.md)\n",
        encoding="utf-8",
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["duplicate card ID: TEST-01"],
    )


def test_requires_exact_card_heading_order(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    path = card_path(repository)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "## Objective", "## Renamed objective"
        ),
        encoding="utf-8",
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "card heading order/count: docs/tasks/TODO/TEST-01-fixture-card.md"
        ],
    )


def test_requires_blocked_by_syntax(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    replace_card_section(card_path(repository), "Blocked by", ["- not canonical"])

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "invalid Blocked by syntax: docs/tasks/TODO/TEST-01-fixture-card.md"
        ],
    )


def test_requires_completion_unblocks_syntax(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    replace_card_section(
        card_path(repository), "Completion unblocks", ["- not canonical"]
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "invalid Completion unblocks syntax: "
            "docs/tasks/TODO/TEST-01-fixture-card.md"
        ],
    )


def test_rejects_unknown_blocker(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/unknown.md").write_text("# Unknown\n", encoding="utf-8")
    replace_card_section(
        card_path(repository),
        "Blocked by",
        ["- [UNKNOWN-01](../../unknown.md) — Required: fixture."],
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["unknown blocker: TEST-01 <- UNKNOWN-01"],
    )


def test_rejects_unknown_unblock_target(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    (repository / "docs/unknown.md").write_text("# Unknown\n", encoding="utf-8")
    replace_card_section(
        card_path(repository),
        "Completion unblocks",
        ["- [UNKNOWN-01](../../unknown.md) — Partially: fixture."],
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["unknown unblock target: TEST-01 -> UNKNOWN-01"],
    )


def test_requires_reciprocal_unblock(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    dependent = add_card(repository, "TEST-02")
    replace_card_section(
        dependent,
        "Blocked by",
        ["- [TEST-01](TEST-01-fixture-card.md) — Required: fixture."],
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["missing reciprocal unblock: TEST-01 -> TEST-02"],
    )


def test_reports_self_dependency_and_resulting_cycle(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    path = card_path(repository)
    replace_card_section(
        path,
        "Blocked by",
        ["- [TEST-01](TEST-01-fixture-card.md) — Required: fixture."],
    )
    replace_card_section(
        path,
        "Completion unblocks",
        ["- [TEST-01](TEST-01-fixture-card.md) — Fully: fixture."],
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "self dependency: TEST-01",
            "dependency cycle: TEST-01 -> TEST-01",
        ],
    )


def test_reports_multi_card_dependency_cycle(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    first = card_path(repository)
    second = add_card(repository, "TEST-02")
    replace_card_section(
        first,
        "Blocked by",
        ["- [TEST-02](TEST-02-fixture-card.md) — Required: fixture."],
    )
    replace_card_section(
        first,
        "Completion unblocks",
        ["- [TEST-02](TEST-02-fixture-card.md) — Partially: fixture."],
    )
    replace_card_section(
        second,
        "Blocked by",
        ["- [TEST-01](TEST-01-fixture-card.md) — Required: fixture."],
    )
    replace_card_section(
        second,
        "Completion unblocks",
        ["- [TEST-01](TEST-01-fixture-card.md) — Partially: fixture."],
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["dependency cycle: TEST-01 -> TEST-02 -> TEST-01"],
    )


def test_fully_unblock_must_be_the_only_direct_blocker(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    first = card_path(repository)
    second = add_card(repository, "TEST-02")
    third = add_card(repository, "TEST-03")
    replace_card_section(
        first,
        "Completion unblocks",
        ["- [TEST-02](TEST-02-fixture-card.md) — Fully: fixture."],
    )
    replace_card_section(
        second,
        "Blocked by",
        [
            "- [TEST-01](TEST-01-fixture-card.md) — Required: fixture.",
            "- [TEST-03](TEST-03-fixture-card.md) — Required: fixture.",
        ],
    )
    replace_card_section(
        third,
        "Completion unblocks",
        ["- [TEST-02](TEST-02-fixture-card.md) — Partially: fixture."],
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["invalid Fully relationship: TEST-01 -> TEST-02"],
    )


def test_rejects_card_link_label_target_mismatch(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    path = card_path(repository)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "Fixture text.",
            "Fixture text. [TEST-02](TEST-01-fixture-card.md)",
            1,
        ),
        encoding="utf-8",
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "card-link label/target mismatch: "
            "docs/tasks/TODO/TEST-01-fixture-card.md "
            "TEST-02 -> TEST-01-fixture-card.md"
        ],
    )


def test_requires_external_inbound_reference_for_card(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    readme = repository / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "\n[Task card](docs/tasks/TODO/TEST-01-fixture-card.md)\n", "\n"
        ),
        encoding="utf-8",
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=["orphan task card: docs/tasks/TODO/TEST-01-fixture-card.md"],
    )


def test_active_card_requires_completed_blockers(tmp_path: Path) -> None:
    repository = write_fixture(tmp_path)
    blocker = card_path(repository)
    active = add_card(repository, "TEST-02", status="IN_PROGRESS")
    replace_card_section(
        blocker,
        "Completion unblocks",
        [
            "- [TEST-02](../IN_PROGRESS/TEST-02-fixture-card.md) "
            "— Fully: fixture."
        ],
    )
    replace_card_section(
        active,
        "Blocked by",
        [
            "- [TEST-01](../TODO/TEST-01-fixture-card.md) "
            "— Required: fixture."
        ],
    )

    assert_failures(
        repository,
        cwd=tmp_path,
        expected=[
            "active/completed card has incomplete blocker: TEST-02 <- TEST-01"
        ],
    )
