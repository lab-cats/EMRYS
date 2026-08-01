"""Shared fail-closed Git checks for repository orchestration commands."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Sequence


FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


class OrchestrationError(RuntimeError):
    """Raised when an orchestration precondition cannot be proved."""


def require(condition: bool, message: str) -> None:
    """Raise a stable operator-facing error when a condition is false."""
    if not condition:
        raise OrchestrationError(message)


def require_full_sha(value: str, label: str) -> str:
    """Reject abbreviated or otherwise ambiguous commit identities."""
    require(bool(FULL_SHA.fullmatch(value)), f"{label} must be a full SHA-1")
    return value


def git(
    repository: Path,
    arguments: Sequence[str],
    *,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run Git without a shell and return captured, normalized text output."""
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(repository), *arguments],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )
    except (OSError, UnicodeError) as exc:
        raise OrchestrationError(
            f"could not run git {' '.join(arguments)} in {repository}: {exc}"
        ) from exc
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic"
        raise OrchestrationError(
            f"git {' '.join(arguments)} failed in {repository}: {detail}"
        )
    return result


def git_text(repository: Path, *arguments: str) -> str:
    """Return stripped stdout from a successful Git command."""
    return git(repository, arguments).stdout.strip()


def verified_repository(value: Path) -> Path:
    """Require an explicit absolute path to the exact Git worktree root."""
    require(value.is_absolute(), f"repository path must be absolute: {value}")
    try:
        resolved = value.resolve(strict=True)
    except OSError as exc:
        raise OrchestrationError(f"repository path is unavailable: {value}: {exc}") from exc
    top = Path(git_text(resolved, "rev-parse", "--show-toplevel")).resolve()
    require(top == resolved, f"repository is not the worktree root: {value}")
    return resolved


def local_branch_ref(branch: str) -> str:
    """Return a full local branch ref after rejecting ambiguous input."""
    require(branch and not branch.startswith("refs/"), "branch must be a short name")
    return f"refs/heads/{branch}"


def verify_checkout(
    repository: Path,
    branch: str,
    expected_head: str,
    *,
    require_clean: bool = True,
) -> str:
    """Bind a worktree, branch ref, and HEAD to one full commit identity."""
    require_full_sha(expected_head, "expected HEAD")
    ref = local_branch_ref(branch)
    current_branch = git_text(repository, "symbolic-ref", "--quiet", "--short", "HEAD")
    require(current_branch == branch, f"unexpected branch: {current_branch}")
    ref_sha = git_text(repository, "show-ref", "--verify", "--hash", ref)
    require(ref_sha == expected_head, f"local ref moved: {ref}")
    require(git_text(repository, "rev-parse", "HEAD") == expected_head, "HEAD moved")
    if require_clean:
        status = git_text(
            repository,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        require(not status, "worktree is not clean")
    return ref


def verify_remote_ref(
    repository: Path,
    remote: str,
    ref: str,
    expected: str | None,
) -> None:
    """Require a remote ref to be absent or equal one exact full SHA."""
    result = git(repository, ["ls-remote", "--exit-code", "--heads", remote, ref], check=False)
    if expected is None:
        require(result.returncode == 2 and not result.stdout, f"remote ref exists: {ref}")
        return
    require_full_sha(expected, "expected remote SHA")
    require(result.returncode == 0, f"remote ref is unavailable: {ref}")
    require(result.stdout.strip() == f"{expected}\t{ref}", f"remote ref moved: {ref}")


def verify_single_child(repository: Path, parent: str, child: str) -> None:
    """Require child to be exactly one non-merge commit after parent."""
    require_full_sha(parent, "parent SHA")
    require_full_sha(child, "child SHA")
    parents = git_text(repository, "rev-list", "--parents", "-n", "1", child)
    require(parents == f"{child} {parent}", "commit is not one non-merge child of parent")
    count = git_text(repository, "rev-list", "--count", f"{parent}..{child}")
    require(count == "1", "commit range does not contain exactly one commit")


def verify_ancestor(repository: Path, ancestor: str, descendant: str) -> None:
    """Require one full commit to be an ancestor of another."""
    require_full_sha(ancestor, "ancestor SHA")
    require_full_sha(descendant, "descendant SHA")
    result = git(repository, ["merge-base", "--is-ancestor", ancestor, descendant], check=False)
    require(result.returncode == 0, f"{ancestor} is not an ancestor of {descendant}")


def verify_diff_check(repository: Path, parent: str, child: str) -> None:
    """Require Git's whitespace/error check to pass for one range."""
    git(repository, ["diff", "--check", parent, child, "--"])


def changed_rows(repository: Path, parent: str, child: str) -> tuple[tuple[str, str], ...]:
    """Return exact no-rename name-status rows for a commit range."""
    output = git(
        repository,
        ["diff", "--name-status", "--no-renames", "-z", parent, child, "--"],
    ).stdout
    fields = output.split("\0")
    if fields and fields[-1] == "":
        fields.pop()
    require(len(fields) % 2 == 0, "unexpected git name-status output")
    return tuple((fields[index], fields[index + 1]) for index in range(0, len(fields), 2))


def object_text(repository: Path, commit: str, path: str) -> str | None:
    """Return a UTF-8 text object, or None when the path does not exist."""
    probe = git(repository, ["cat-file", "-e", f"{commit}:{path}"], check=False)
    if probe.returncode != 0:
        return None
    result = git(repository, ["show", f"{commit}:{path}"])
    return result.stdout


def heading_anchors(text: str) -> dict[str, set[str]]:
    """Map literal Markdown headings to the anchors used by the doc gate."""
    counts: dict[str, int] = {}
    result: dict[str, set[str]] = {}
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        value = re.sub(r"<[^>]*>", "", match.group(1)).lower()
        value = re.sub(r"[^\w\- ]", "", value).replace(" ", "-")
        number = counts.get(value, 0)
        counts[value] = number + 1
        anchor = value if number == 0 else f"{value}-{number}"
        result.setdefault(line, set()).add(anchor)
    return result


def cli_main(run) -> None:
    """Provide consistent concise failure handling for command entry points."""
    try:
        run()
    except OrchestrationError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
