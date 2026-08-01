"""Focused contract tests for the shared Git-orchestration Python helpers."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON_PATH = REPO_ROOT / "scripts" / "git_orchestration" / "_common.py"
SPEC = importlib.util.spec_from_file_location("git_orchestration_common", COMMON_PATH)
assert SPEC is not None and SPEC.loader is not None
COMMON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMMON)


def run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run fixture Git with deterministic author identity."""
    return subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=NORAD Test",
            "-c",
            "user.email=norad-test@example.invalid",
            *arguments,
        ],
        text=True,
        capture_output=True,
        check=True,
    )


def initialized_repository(path: Path) -> tuple[Path, str]:
    path.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main", str(path)],
        text=True,
        capture_output=True,
        check=True,
    )
    (path / "tracked.txt").write_text("base\n", encoding="utf-8")
    run_git(path, "add", "tracked.txt")
    run_git(path, "commit", "-m", "base")
    return path, run_git(path, "rev-parse", "HEAD").stdout.strip()


def test_require_and_full_sha_contract() -> None:
    full_sha = "a" * 40
    COMMON.require(True, "unused")
    assert COMMON.require_full_sha(full_sha, "candidate") == full_sha

    with pytest.raises(COMMON.OrchestrationError, match="explicit failure"):
        COMMON.require(False, "explicit failure")
    with pytest.raises(COMMON.OrchestrationError, match="full SHA-1"):
        COMMON.require_full_sha("abc123", "candidate")


def test_git_wrapper_success_failure_and_spawn_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _ = initialized_repository(tmp_path / "repo")
    assert COMMON.git_text(repository, "rev-parse", "--show-toplevel") == str(
        repository
    )

    unchecked = COMMON.git(repository, ["not-a-git-command"], check=False)
    assert unchecked.returncode != 0
    with pytest.raises(COMMON.OrchestrationError, match="not-a-git-command.*failed"):
        COMMON.git(repository, ["not-a-git-command"])

    def fail_to_spawn(*_args, **_kwargs):
        raise OSError("synthetic spawn failure")

    monkeypatch.setattr(COMMON.subprocess, "run", fail_to_spawn)
    with pytest.raises(COMMON.OrchestrationError, match="synthetic spawn failure"):
        COMMON.git(repository, ["status"])


def test_repository_and_branch_identity_contracts(tmp_path: Path) -> None:
    repository, _ = initialized_repository(tmp_path / "repo")
    nested = repository / "nested"
    nested.mkdir()

    assert COMMON.verified_repository(repository) == repository
    with pytest.raises(COMMON.OrchestrationError, match="must be absolute"):
        COMMON.verified_repository(Path("relative"))
    with pytest.raises(COMMON.OrchestrationError, match="unavailable"):
        COMMON.verified_repository(tmp_path / "missing")
    with pytest.raises(COMMON.OrchestrationError, match="not the worktree root"):
        COMMON.verified_repository(nested)

    assert COMMON.local_branch_ref("main") == "refs/heads/main"
    for invalid in ("", "refs/heads/main"):
        with pytest.raises(COMMON.OrchestrationError, match="short name"):
            COMMON.local_branch_ref(invalid)


def test_checkout_contract_checks_cleanliness_and_identity(tmp_path: Path) -> None:
    repository, head = initialized_repository(tmp_path / "repo")
    assert COMMON.verify_checkout(repository, "main", head) == "refs/heads/main"

    (repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(COMMON.OrchestrationError, match="not clean"):
        COMMON.verify_checkout(repository, "main", head)
    assert (
        COMMON.verify_checkout(repository, "main", head, require_clean=False)
        == "refs/heads/main"
    )
    with pytest.raises(COMMON.OrchestrationError, match="unexpected branch"):
        COMMON.verify_checkout(repository, "other", head, require_clean=False)
    with pytest.raises(COMMON.OrchestrationError, match="local ref moved"):
        COMMON.verify_checkout(repository, "main", "b" * 40, require_clean=False)


def test_checkout_detects_head_ref_race(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = "a" * 40

    def fake_git_text(_repository: Path, *arguments: str) -> str:
        values = {
            ("symbolic-ref", "--quiet", "--short", "HEAD"): "main",
            ("show-ref", "--verify", "--hash", "refs/heads/main"): expected,
            ("rev-parse", "HEAD"): "b" * 40,
        }
        return values[arguments]

    monkeypatch.setattr(COMMON, "git_text", fake_git_text)
    with pytest.raises(COMMON.OrchestrationError, match="HEAD moved"):
        COMMON.verify_checkout(Path("/repo"), "main", expected, require_clean=False)


@pytest.mark.parametrize(
    ("expected", "returncode", "stdout", "message"),
    (
        (None, 2, "", None),
        (None, 0, "a" * 40 + "\trefs/heads/main\n", "remote ref exists"),
        ("a" * 40, 1, "", "remote ref is unavailable"),
        ("a" * 40, 0, "b" * 40 + "\trefs/heads/main\n", "remote ref moved"),
    ),
)
def test_remote_ref_contract(
    monkeypatch: pytest.MonkeyPatch,
    expected: str | None,
    returncode: int,
    stdout: str,
    message: str | None,
) -> None:
    completed = subprocess.CompletedProcess(["git"], returncode, stdout, "")
    monkeypatch.setattr(COMMON, "git", lambda *_args, **_kwargs: completed)
    if message is None:
        COMMON.verify_remote_ref(Path("/repo"), "origin", "refs/heads/main", expected)
    else:
        with pytest.raises(COMMON.OrchestrationError, match=message):
            COMMON.verify_remote_ref(
                Path("/repo"), "origin", "refs/heads/main", expected
            )


def test_commit_relationship_diff_and_object_helpers(tmp_path: Path) -> None:
    repository, parent = initialized_repository(tmp_path / "repo")
    (repository / "tracked.txt").write_text("base\nchild\n", encoding="utf-8")
    (repository / "added.txt").write_text("added\n", encoding="utf-8")
    run_git(repository, "add", "--all")
    run_git(repository, "commit", "-m", "child")
    child = run_git(repository, "rev-parse", "HEAD").stdout.strip()

    COMMON.verify_single_child(repository, parent, child)
    COMMON.verify_ancestor(repository, parent, child)
    COMMON.verify_diff_check(repository, parent, child)
    assert set(COMMON.changed_rows(repository, parent, child)) == {
        ("A", "added.txt"),
        ("M", "tracked.txt"),
    }
    assert COMMON.object_text(repository, child, "added.txt") == "added\n"
    assert COMMON.object_text(repository, child, "missing.txt") is None

    with pytest.raises(COMMON.OrchestrationError, match="not one non-merge child"):
        COMMON.verify_single_child(repository, child, parent)
    with pytest.raises(COMMON.OrchestrationError, match="is not an ancestor"):
        COMMON.verify_ancestor(repository, child, parent)

    (repository / "whitespace.txt").write_text("bad trailing space \n", encoding="utf-8")
    run_git(repository, "add", "whitespace.txt")
    run_git(repository, "commit", "-m", "whitespace")
    whitespace = run_git(repository, "rev-parse", "HEAD").stdout.strip()
    with pytest.raises(COMMON.OrchestrationError, match="diff --check"):
        COMMON.verify_diff_check(repository, child, whitespace)


def test_changed_rows_rejects_malformed_git_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = subprocess.CompletedProcess(["git"], 0, "A\0only-status\0orphan", "")
    monkeypatch.setattr(COMMON, "git", lambda *_args, **_kwargs: completed)
    with pytest.raises(COMMON.OrchestrationError, match="unexpected git name-status"):
        COMMON.changed_rows(Path("/repo"), "a" * 40, "b" * 40)


def test_heading_anchor_generation_handles_nonheadings_markup_and_duplicates() -> None:
    text = "\n".join(
        (
            "ordinary prose",
            "## Alpha <em>Beta</em>!",
            "## Alpha Beta",
            "### Different_heading #",
        )
    )
    assert COMMON.heading_anchors(text) == {
        "## Alpha <em>Beta</em>!": {"alpha-beta"},
        "## Alpha Beta": {"alpha-beta-1"},
        "### Different_heading #": {"different_heading"},
    }


def test_cli_main_returns_normally_and_formats_orchestration_errors() -> None:
    calls: list[str] = []
    COMMON.cli_main(lambda: calls.append("called"))
    assert calls == ["called"]

    def fail() -> None:
        raise COMMON.OrchestrationError("synthetic failure")

    with pytest.raises(SystemExit, match="ERROR: synthetic failure"):
        COMMON.cli_main(fail)
