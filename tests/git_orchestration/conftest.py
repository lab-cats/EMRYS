"""Local-only Git fixtures for the orchestration command tests."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "scripts" / "git_orchestration"
FRAGMENT_ID = "TEST-EXCHANGE"
FRAGMENT_PATH = f"docs/fragments/{FRAGMENT_ID}.md"
REQUEST_ID = "REQ-1"


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
    input_text: str | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a local command with deterministic, noninteractive Git behavior."""
    command_env = os.environ.copy()
    command_env.update(
        {
            "GIT_AUTHOR_NAME": "NORAD Test",
            "GIT_AUTHOR_EMAIL": "norad-test@example.invalid",
            "GIT_COMMITTER_NAME": "NORAD Test",
            "GIT_COMMITTER_EMAIL": "norad-test@example.invalid",
            "GIT_TERMINAL_PROMPT": "0",
            "LC_ALL": "C",
            "NORAD_PYTHON_BIN": sys.executable,
        }
    )
    if env:
        command_env.update(env)
    result = subprocess.run(
        list(command),
        cwd=cwd,
        env=command_env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def git(repository: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run Git against one temporary repository."""
    return run_command(["git", "-C", str(repository), *arguments], cwd=repository, check=check)


def git_text(repository: Path, *arguments: str) -> str:
    return git(repository, *arguments).stdout.strip()


def write_files(repository: Path, files: Mapping[str, str]) -> None:
    for relative, text in files.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def commit_all(repository: Path, message: str) -> str:
    git(repository, "add", "--all")
    git(repository, "commit", "-m", message)
    return git_text(repository, "rev-parse", "HEAD")


def valid_fragment(base: str) -> str:
    return f"""# {FRAGMENT_ID} integration fragment

- Fragment ID: `{FRAGMENT_ID}`
- Owning task: `CONCURRENCY-02`
- Lane ID: `synthetic-sidecar`
- Candidate branch: `sidecar`
- Exact base: `{base}`
- Evidence and scope boundary: `documentation-only synthetic request`

## Request `REQ-1`

- Target owner: `docs/owner.md`
- Target heading or anchor: `# Existing Target`
- Target mode: `existing anchor`
- Requested update: `Add one bounded sentence.`
- Provenance: `Synthetic exchange fixture.`
- Assumptions and coupling: `No executable behavior changes.`
- Candidate disposition: `pending`
"""


@dataclass
class Exchange:
    root: Path
    remote: Path
    candidate_repo: Path
    canonical_repo: Path
    base: str
    candidate: str
    parent: str
    candidate_branch: str = "sidecar"
    canonical_branch: str = "integration"
    fragment: str = FRAGMENT_PATH

    def git(self, repository: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return git(repository, *arguments, check=check)

    def git_text(self, repository: Path, *arguments: str) -> str:
        return git_text(repository, *arguments)

    def candidate_command(
        self,
        *,
        expected: Sequence[tuple[str, str]] | None = None,
        allowed: Sequence[str] | None = None,
    ) -> list[str]:
        rows = expected or (("A", self.fragment),)
        paths = allowed or (self.fragment,)
        command = [
            sys.executable,
            str(TOOLS / "validate_fragment_candidate.py"),
            "--repo",
            str(self.candidate_repo),
            "--branch",
            self.candidate_branch,
            "--base",
            self.base,
            "--candidate",
            self.candidate,
            "--fragment",
            self.fragment,
        ]
        for status, path in rows:
            command.extend(("--expected-change", status, path))
        for path in paths:
            command.extend(("--allowed-path", path))
        return command

    def target_command(
        self,
        *,
        owner: str,
        mode: str,
        heading: str,
        anchor: str,
    ) -> list[str]:
        return [
            sys.executable,
            str(TOOLS / "validate_fragment_target.py"),
            "--repo",
            str(self.canonical_repo),
            "--branch",
            self.canonical_branch,
            "--base",
            self.base,
            "--parent",
            self.parent,
            "--owner",
            owner,
            "--mode",
            mode,
            "--heading",
            heading,
            "--anchor",
            anchor,
        ]

    def apply_command(self, *, execute: bool = False) -> list[str]:
        command = [
            "bash",
            str(TOOLS / "apply_fragment_candidate.sh"),
            "--candidate-repo",
            str(self.candidate_repo),
            "--candidate-branch",
            self.candidate_branch,
            "--candidate",
            self.candidate,
            "--base",
            self.base,
            "--fragment",
            self.fragment,
            "--expected-change",
            "A",
            self.fragment,
            "--allowed-path",
            self.fragment,
            "--canonical-repo",
            str(self.canonical_repo),
            "--canonical-branch",
            self.canonical_branch,
            "--parent",
            self.parent,
        ]
        if execute:
            command.append("--execute")
        return command

    def message_file(self, *, outcome: str, name: str = "message.txt") -> Path:
        path = self.root / name
        path.write_text(
            "\n".join(
                (
                    f"test: record fragment {outcome}",
                    "",
                    f"Fragment-Integration-ID: {FRAGMENT_ID}",
                    f"Fragment-Source-SHA: {self.candidate}",
                    f"Fragment-Source-Ref: refs/heads/{self.candidate_branch}",
                    f"Fragment-Base-SHA: {self.base}",
                    f"Integration-Parent-SHA: {self.parent}",
                    f"Fragment-Package-Outcome: {outcome}",
                    "Fragment-Request-Disposition: REQ-1=accept; "
                    "destination=docs/owner.md#existing-target; "
                    "effect=fixture integration",
                    "",
                )
            ),
            encoding="utf-8",
        )
        return path

    def finalize_command(
        self,
        *,
        applied: str,
        message_file: Path,
        final_paths: Sequence[str] = ("docs/owner.md",),
        execute: bool = False,
    ) -> list[str]:
        command = [
            "bash",
            str(TOOLS / "finalize_fragment_integration.sh"),
            "--repo",
            str(self.canonical_repo),
            "--branch",
            self.canonical_branch,
            "--parent",
            self.parent,
            "--applied",
            applied,
            "--fragment",
            self.fragment,
        ]
        for path in final_paths:
            command.extend(("--final-path", path))
        command.extend(
            (
                "--message-file",
                str(message_file),
                "--integration-id",
                FRAGMENT_ID,
                "--source-repo",
                str(self.candidate_repo),
                "--source-sha",
                self.candidate,
                "--source-ref",
                f"refs/heads/{self.candidate_branch}",
                "--base",
                self.base,
                "--request-id",
                REQUEST_ID,
            )
        )
        if execute:
            command.append("--execute")
        return command

    def noop_command(self, *, message_file: Path, execute: bool = False) -> list[str]:
        command = [
            "bash",
            str(TOOLS / "record_fragment_noop.sh"),
            "--candidate-repo",
            str(self.candidate_repo),
            "--candidate-branch",
            self.candidate_branch,
            "--candidate",
            self.candidate,
            "--base",
            self.base,
            "--fragment",
            self.fragment,
            "--expected-change",
            "A",
            self.fragment,
            "--allowed-path",
            self.fragment,
            "--canonical-repo",
            str(self.canonical_repo),
            "--canonical-branch",
            self.canonical_branch,
            "--parent",
            self.parent,
            "--message-file",
            str(message_file),
            "--integration-id",
            FRAGMENT_ID,
            "--request-id",
            REQUEST_ID,
        ]
        if execute:
            command.append("--execute")
        return command

    def publish_command(
        self,
        *,
        final: str,
        expected_remote: str,
        outcome: str = "no-op",
        final_paths: Sequence[str] = (),
        execute: bool = False,
    ) -> list[str]:
        command = [
            "bash",
            str(TOOLS / "publish_exact_ref.sh"),
            "--repo",
            str(self.canonical_repo),
            "--branch",
            self.canonical_branch,
            "--parent",
            self.parent,
            "--final",
            final,
            "--expected-remote",
            expected_remote,
            "--source-repo",
            str(self.candidate_repo),
            "--source-ref",
            f"refs/heads/{self.candidate_branch}",
            "--source-sha",
            self.candidate,
            "--fragment",
            self.fragment,
            "--integration-id",
            FRAGMENT_ID,
            "--base",
            self.base,
            "--outcome",
            outcome,
            "--request-id",
            REQUEST_ID,
        ]
        for path in final_paths:
            command.extend(("--final-path", path))
        if execute:
            command.append("--execute")
        return command


@pytest.fixture
def run_cli(tmp_path: Path) -> Callable[[Sequence[str]], subprocess.CompletedProcess[str]]:
    outside = tmp_path / "arbitrary-cwd"
    outside.mkdir()

    def invoke(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return run_command(command, cwd=outside)

    return invoke


@pytest.fixture
def exchange_factory(tmp_path: Path) -> Callable[..., Exchange]:
    sequence = 0

    def build(
        *,
        fragment_text: str | None = None,
        candidate_changes: Mapping[str, str] | None = None,
        canonical_changes: Mapping[str, str] | None = None,
    ) -> Exchange:
        nonlocal sequence
        sequence += 1
        root = tmp_path / f"exchange-{sequence}"
        root.mkdir()
        remote = root / "origin.git"
        run_command(["git", "init", "--bare", str(remote)], cwd=root, check=True)

        seed = root / "seed"
        run_command(["git", "init", "-b", "main", str(seed)], cwd=root, check=True)
        write_files(
            seed,
            {
                "README.md": "# Fixture repository\n",
                "docs/fragments/README.md": "# Integration fragments\n",
                "docs/owner.md": "# Existing Target\n\nBase text.\n",
                "docs/unchanged.md": "# Unchanged\n",
            },
        )
        base = commit_all(seed, "seed")
        git(seed, "remote", "add", "origin", str(remote))
        git(seed, "push", "-u", "origin", "main")

        candidate_repo = root / "candidate"
        run_command(
            ["git", "clone", "--branch", "main", str(remote), str(candidate_repo)],
            cwd=root,
            check=True,
        )
        git(candidate_repo, "checkout", "-b", "sidecar")
        candidate_fragment = fragment_text.format(BASE=base) if fragment_text else valid_fragment(base)
        changes = {FRAGMENT_PATH: candidate_fragment}
        changes.update(candidate_changes or {})
        write_files(candidate_repo, changes)
        candidate = commit_all(candidate_repo, "candidate")
        git(candidate_repo, "push", "-u", "origin", "sidecar")

        canonical_repo = root / "canonical"
        run_command(
            ["git", "clone", "--branch", "main", str(remote), str(canonical_repo)],
            cwd=root,
            check=True,
        )
        git(canonical_repo, "checkout", "-b", "integration")
        if canonical_changes:
            write_files(canonical_repo, canonical_changes)
            parent = commit_all(canonical_repo, "canonical parent")
        else:
            parent = base
        git(canonical_repo, "push", "-u", "origin", "integration")

        return Exchange(
            root=root,
            remote=remote,
            candidate_repo=candidate_repo,
            canonical_repo=canonical_repo,
            base=base,
            candidate=candidate,
            parent=parent,
        )

    return build
