"""Tests for terminal no-op recording and exact-ref publication."""

from __future__ import annotations

import shlex
from pathlib import Path


def write_repo_files(repository: Path, changes: dict[str, str]) -> None:
    """Write a small final-tree fixture without reaching into conftest internals."""
    for relative_path, content in changes.items():
        path = repository / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def install_pre_push_hook(exchange, command: str) -> None:
    """Install one deterministic race at the client-side pre-push boundary."""
    hook = Path(
        exchange.git_text(
            exchange.canonical_repo,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "hooks/pre-push",
        )
    )
    hook.write_text(f"#!/bin/sh\nset -eu\n{command}\n", encoding="utf-8")
    hook.chmod(0o755)


def make_local_final(
    exchange,
    *,
    outcome: str = "no-op",
    source_ref: str | None = None,
    source_sha: str | None = None,
    changes: dict[str, str] | None = None,
) -> str:
    message = exchange.message_file(outcome=outcome, name="publish-message.txt")
    text = message.read_text(encoding="utf-8")
    if source_ref is not None:
        text = text.replace(
            f"Fragment-Source-Ref: refs/heads/{exchange.candidate_branch}",
            f"Fragment-Source-Ref: {source_ref}",
        )
    if source_sha is not None:
        text = text.replace(
            f"Fragment-Source-SHA: {exchange.candidate}",
            f"Fragment-Source-SHA: {source_sha}",
        )
    message.write_text(text, encoding="utf-8")
    if changes:
        write_repo_files(exchange.canonical_repo, changes)
        exchange.git(exchange.canonical_repo, "add", "--all")
    exchange.git(
        exchange.canonical_repo,
        "commit",
        "--allow-empty",
        "-F",
        str(message),
    )
    return exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD")


def test_noop_dry_run_preserves_canonical_parent(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()
    message = exchange.message_file(outcome="no-op")

    result = run_cli(exchange.noop_command(message_file=message))

    assert result.returncode == 0, result.stderr
    assert "DRY-RUN:" in result.stdout
    assert "commit --allow-empty" in result.stdout
    assert "no Git state changed" in result.stdout
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == exchange.parent
    assert exchange.git_text(exchange.canonical_repo, "status", "--porcelain=v1") == ""


def test_noop_execute_creates_empty_commit_with_exact_trailers(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    message = exchange.message_file(outcome="no-op")

    result = run_cli(exchange.noop_command(message_file=message, execute=True))

    assert result.returncode == 0, result.stderr
    final = exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD")
    assert f"PASS recorded no-op fragment integration: {final}" in result.stdout
    assert exchange.git_text(
        exchange.canonical_repo, "rev-list", "--parents", "-n", "1", final
    ) == f"{final} {exchange.parent}"
    diff = exchange.git(
        exchange.canonical_repo,
        "diff",
        "--quiet",
        exchange.parent,
        final,
        "--",
        check=False,
    )
    assert diff.returncode == 0
    trailers = exchange.git_text(
        exchange.canonical_repo,
        "show",
        "-s",
        "--format=%(trailers:key=Fragment-Package-Outcome,valueonly)",
        final,
    )
    assert trailers == "no-op"
    assert exchange.git_text(exchange.canonical_repo, "status", "--porcelain=v1") == ""


def test_noop_rejects_fragment_already_in_canonical_tree(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory(
        canonical_changes={"docs/fragments/OTHER-REQUEST.md": "# stale fragment\n"}
    )
    message = exchange.message_file(outcome="no-op")

    result = run_cli(exchange.noop_command(message_file=message))

    assert result.returncode != 0
    assert "fragment already exists" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == exchange.parent


def test_publish_dry_run_does_not_move_remote_ref(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)

    result = run_cli(
        exchange.publish_command(final=final, expected_remote=exchange.parent)
    )

    assert result.returncode == 0, result.stderr
    assert "DRY-RUN:" in result.stdout
    assert "push" in result.stdout
    assert "--force-with-lease=" in result.stdout
    assert f"{final}:refs/heads/{exchange.canonical_branch}" in result.stdout
    assert "no remote state changed" in result.stdout
    assert exchange.git_text(
        exchange.remote, "rev-parse", f"refs/heads/{exchange.canonical_branch}"
    ) == exchange.parent


def test_publish_execute_pushes_exact_reviewed_tip_and_sets_upstream(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            execute=True,
        )
    )

    assert result.returncode == 0, result.stderr
    assert f"PASS published exact canonical ref: {final}" in result.stdout
    assert exchange.git_text(
        exchange.remote, "rev-parse", f"refs/heads/{exchange.canonical_branch}"
    ) == final
    assert exchange.git_text(
        exchange.canonical_repo,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
    ) == f"origin/{exchange.canonical_branch}"
    assert exchange.git_text(
        exchange.canonical_repo, "rev-parse", "@{upstream}"
    ) == final


def test_publish_absent_ref_dry_run_does_not_create_remote_ref(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    canonical_ref = f"refs/heads/{exchange.canonical_branch}"
    exchange.git(exchange.remote, "update-ref", "-d", canonical_ref)

    result = run_cli(exchange.publish_command(final=final, expected_remote="ABSENT"))

    assert result.returncode == 0, result.stderr
    assert f"--force-with-lease={canonical_ref}:" in result.stdout
    absent = exchange.git(
        exchange.remote, "show-ref", "--verify", canonical_ref, check=False
    )
    assert absent.returncode != 0


def test_publish_absent_ref_execute_creates_exact_reviewed_ref(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    canonical_ref = f"refs/heads/{exchange.canonical_branch}"
    exchange.git(exchange.remote, "update-ref", "-d", canonical_ref)

    result = run_cli(
        exchange.publish_command(final=final, expected_remote="ABSENT", execute=True)
    )

    assert result.returncode == 0, result.stderr
    assert exchange.git_text(exchange.remote, "rev-parse", canonical_ref) == final


def test_publish_exact_sha_is_not_retargeted_if_local_branch_moves_in_hook(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    final_tree = exchange.git_text(exchange.canonical_repo, "rev-parse", f"{final}^{{tree}}")
    moved = exchange.git_text(
        exchange.canonical_repo,
        "commit-tree",
        final_tree,
        "-p",
        final,
        "-m",
        "move local branch during push",
    )
    canonical_ref = f"refs/heads/{exchange.canonical_branch}"
    install_pre_push_hook(
        exchange,
        "git -C "
        f"{shlex.quote(str(exchange.canonical_repo))} update-ref "
        f"{shlex.quote(canonical_ref)} {shlex.quote(moved)}",
    )

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            execute=True,
        )
    )

    assert result.returncode != 0
    assert "local ref moved" in result.stderr
    assert exchange.git_text(exchange.remote, "rev-parse", canonical_ref) == final
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", canonical_ref) == moved


def test_publish_rejects_canonical_remote_race_atomically(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    canonical_ref = f"refs/heads/{exchange.canonical_branch}"
    source_ref = f"refs/heads/{exchange.candidate_branch}"
    install_pre_push_hook(
        exchange,
        "git --git-dir="
        f"{shlex.quote(str(exchange.remote))} update-ref "
        f"{shlex.quote(canonical_ref)} {shlex.quote(exchange.candidate)} "
        f"{shlex.quote(exchange.parent)}",
    )

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            execute=True,
        )
    )

    assert result.returncode != 0
    assert exchange.git_text(exchange.remote, "rev-parse", canonical_ref) == exchange.candidate
    assert exchange.git_text(exchange.remote, "rev-parse", source_ref) == exchange.candidate


def test_publish_detects_source_remote_race_as_recovery_incident(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    canonical_ref = f"refs/heads/{exchange.canonical_branch}"
    source_ref = f"refs/heads/{exchange.candidate_branch}"
    install_pre_push_hook(
        exchange,
        "git --git-dir="
        f"{shlex.quote(str(exchange.remote))} update-ref "
        f"{shlex.quote(source_ref)} {shlex.quote(exchange.base)} "
        f"{shlex.quote(exchange.candidate)}",
    )

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            execute=True,
        )
    )

    assert result.returncode != 0
    assert "remote ref moved" in result.stderr
    assert exchange.git_text(exchange.remote, "rev-parse", canonical_ref) == final
    assert exchange.git_text(exchange.remote, "rev-parse", source_ref) == exchange.base


def test_publish_rejects_source_base_mismatch(exchange_factory, run_cli) -> None:
    exchange = exchange_factory(
        canonical_changes={"docs/owner.md": "# Existing Target\n\nNew parent.\n"}
    )
    final = make_local_final(exchange)
    command = exchange.publish_command(final=final, expected_remote=exchange.parent)
    command[command.index("--base") + 1] = exchange.parent

    result = run_cli(command)

    assert result.returncode != 0
    assert "not one non-merge child" in result.stderr


def test_publish_rejects_source_with_two_commits_after_base(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    write_repo_files(exchange.candidate_repo, {"docs/source-note.md": "second commit\n"})
    exchange.git(exchange.candidate_repo, "add", "--all")
    exchange.git(exchange.candidate_repo, "commit", "-m", "second source commit")
    exchange.candidate = exchange.git_text(exchange.candidate_repo, "rev-parse", "HEAD")
    exchange.git(exchange.candidate_repo, "push", "origin", exchange.candidate_branch)
    final = make_local_final(exchange)

    result = run_cli(
        exchange.publish_command(final=final, expected_remote=exchange.parent)
    )

    assert result.returncode != 0
    assert "not one non-merge child" in result.stderr


def test_publish_rejects_declared_request_not_in_source_fragment(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    command = exchange.publish_command(final=final, expected_remote=exchange.parent)
    command[command.index("--request-id") + 1] = "REQ-OTHER"

    result = run_cli(command)

    assert result.returncode != 0
    assert "declared request IDs do not match" in result.stderr


def test_publish_rejects_noop_commit_that_changes_tree(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(
        exchange,
        changes={"docs/owner.md": "# Existing Target\n\nChanged in a no-op.\n"},
    )

    result = run_cli(
        exchange.publish_command(final=final, expected_remote=exchange.parent)
    )

    assert result.returncode != 0
    assert "no-op package changes" in result.stderr


def test_publish_rejects_applied_commit_with_unchanged_tree(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange, outcome="applied")

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            outcome="applied",
            final_paths=("docs/owner.md",),
        )
    )

    assert result.returncode != 0
    assert "applied package must change" in result.stderr


def test_publish_rejects_applied_commit_with_wrong_exact_path_set(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(
        exchange,
        outcome="applied",
        changes={"docs/owner.md": "# Existing Target\n\nIntegrated.\n"},
    )

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            outcome="applied",
            final_paths=("docs/unchanged.md",),
        )
    )

    assert result.returncode != 0
    assert "do not equal the explicit final path set" in result.stderr


def test_publish_rejects_any_fragment_file_in_final_tree(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    extra_fragment = "docs/fragments/OTHER-REQUEST.md"
    final = make_local_final(
        exchange,
        outcome="applied",
        changes={extra_fragment: "# Unconsumed fragment\n"},
    )

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            outcome="applied",
            final_paths=(extra_fragment,),
        )
    )

    assert result.returncode != 0
    assert "candidate fragment survives" in result.stderr


def test_publish_rejects_outcome_argument_that_disagrees_with_commit(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            outcome="applied",
            final_paths=("docs/owner.md",),
        )
    )

    assert result.returncode != 0
    assert "unexpected committed Fragment-Package-Outcome trailer" in result.stderr


def test_publish_rejects_preexisting_git_operation_without_remote_mutation(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    marker = Path(
        exchange.git_text(
            exchange.canonical_repo,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "CHERRY_PICK_HEAD",
        )
    )
    marker.write_text(exchange.parent + "\n", encoding="utf-8")
    canonical_ref = f"refs/heads/{exchange.canonical_branch}"
    source_ref = f"refs/heads/{exchange.candidate_branch}"

    result = run_cli(
        exchange.publish_command(
            final=final,
            expected_remote=exchange.parent,
            execute=True,
        )
    )

    assert result.returncode != 0
    assert "Git operation state already exists" in result.stderr
    assert exchange.git_text(exchange.remote, "rev-parse", canonical_ref) == exchange.parent
    assert exchange.git_text(exchange.remote, "rev-parse", source_ref) == exchange.candidate


def test_publish_rejects_mismatched_expected_remote(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)

    result = run_cli(
        exchange.publish_command(final=final, expected_remote=exchange.candidate)
    )

    assert result.returncode != 0
    assert "remote ref moved" in result.stderr
    assert exchange.git_text(
        exchange.remote, "rev-parse", f"refs/heads/{exchange.canonical_branch}"
    ) == exchange.parent


def test_publish_rejects_existing_remote_that_is_not_final_ancestor(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    final = make_local_final(exchange)
    exchange.git(
        exchange.remote,
        "update-ref",
        f"refs/heads/{exchange.canonical_branch}",
        exchange.candidate,
    )

    result = run_cli(
        exchange.publish_command(final=final, expected_remote=exchange.candidate)
    )

    assert result.returncode != 0
    assert "is not an ancestor" in result.stderr
    assert exchange.git_text(
        exchange.remote, "rev-parse", f"refs/heads/{exchange.canonical_branch}"
    ) == exchange.candidate


def test_publish_rejects_source_ref_equal_to_canonical_ref(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    canonical_ref = f"refs/heads/{exchange.canonical_branch}"
    final = make_local_final(
        exchange,
        source_ref=canonical_ref,
        source_sha=exchange.parent,
    )
    command = exchange.publish_command(final=final, expected_remote=exchange.parent)
    command[command.index("--source-ref") + 1] = canonical_ref
    command[command.index("--source-sha") + 1] = exchange.parent

    result = run_cli(command)

    assert result.returncode != 0
    assert "source ref and canonical publication ref must differ" in result.stderr
