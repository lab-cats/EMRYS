"""Lifecycle tests for applying and finalizing fragment candidates."""

from __future__ import annotations

from pathlib import Path

import pytest


def apply_candidate(exchange, run_cli) -> str:
    result = run_cli(exchange.apply_command(execute=True))
    assert result.returncode == 0, result.stderr
    applied = exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD")
    assert f"PASS applied fragment candidate: {applied}" in result.stdout
    return applied


def test_apply_dry_run_proves_preconditions_without_mutation(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()

    result = run_cli(exchange.apply_command())

    assert result.returncode == 0, result.stderr
    assert "DRY-RUN:" in result.stdout
    assert "cherry-pick" in result.stdout
    assert "no Git state changed" in result.stdout
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == exchange.parent
    assert not (exchange.canonical_repo / exchange.fragment).exists()


def test_apply_execute_creates_one_clean_child(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()

    applied = apply_candidate(exchange, run_cli)

    parents = exchange.git_text(
        exchange.canonical_repo, "rev-list", "--parents", "-n", "1", applied
    )
    assert parents == f"{applied} {exchange.parent}"
    assert (exchange.canonical_repo / exchange.fragment).is_file()
    assert exchange.git_text(exchange.canonical_repo, "status", "--porcelain=v1") == ""


def test_apply_conflict_aborts_and_restores_exact_clean_parent(
    exchange_factory, run_cli
) -> None:
    canonical_fragment = "# Canonical competing fragment\n"
    exchange = exchange_factory(
        canonical_changes={"docs/fragments/TEST-EXCHANGE.md": canonical_fragment}
    )

    result = run_cli(exchange.apply_command(execute=True))

    assert result.returncode != 0
    assert "abort restored the exact clean parent" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == exchange.parent
    assert exchange.git_text(exchange.canonical_repo, "status", "--porcelain=v1") == ""
    assert (
        exchange.canonical_repo / exchange.fragment
    ).read_text(encoding="utf-8") == canonical_fragment
    git_state = Path(
        exchange.git_text(exchange.canonical_repo, "rev-parse", "--git-path", "CHERRY_PICK_HEAD")
    )
    if not git_state.is_absolute():
        git_state = exchange.canonical_repo / git_state
    assert not git_state.exists()


def test_finalize_dry_run_preserves_applied_and_dirty_state(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    owner = exchange.canonical_repo / "docs/owner.md"
    owner.write_text("# Existing Target\n\nIntegrated text.\n", encoding="utf-8")
    message = exchange.message_file(outcome="applied")
    status_before = exchange.git_text(
        exchange.canonical_repo, "status", "--porcelain=v1", "--untracked-files=all"
    )
    objects_before = exchange.git_text(exchange.canonical_repo, "count-objects", "-v")

    result = run_cli(
        exchange.finalize_command(applied=applied, message_file=message)
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("DRY-RUN:") == 3
    assert "no Git state changed" in result.stdout
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied
    assert exchange.git_text(
        exchange.canonical_repo, "status", "--porcelain=v1", "--untracked-files=all"
    ) == status_before
    assert exchange.git_text(exchange.canonical_repo, "diff", "--cached", "--name-only") == ""
    assert (exchange.canonical_repo / exchange.fragment).is_file()
    assert exchange.git_text(exchange.canonical_repo, "count-objects", "-v") == objects_before


def test_finalize_execute_removes_fragment_and_records_exact_trailers(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    owner = exchange.canonical_repo / "docs/owner.md"
    owner.write_text("# Existing Target\n\nIntegrated text.\n", encoding="utf-8")
    message = exchange.message_file(outcome="applied")

    result = run_cli(
        exchange.finalize_command(
            applied=applied,
            message_file=message,
            execute=True,
        )
    )

    assert result.returncode == 0, result.stderr
    final = exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD")
    assert f"PASS finalized fragment integration: {final}" in result.stdout
    assert exchange.git_text(
        exchange.canonical_repo, "rev-list", "--parents", "-n", "1", final
    ) == f"{final} {exchange.parent}"
    assert exchange.git_text(
        exchange.canonical_repo,
        "diff",
        "--name-only",
        "--no-renames",
        exchange.parent,
        final,
        "--",
    ) == "docs/owner.md"
    assert not (exchange.canonical_repo / exchange.fragment).exists()
    assert (exchange.canonical_repo / "docs/fragments/README.md").is_file()
    trailers = exchange.git_text(
        exchange.canonical_repo,
        "show",
        "-s",
        "--format=%(trailers:key=Fragment-Package-Outcome,valueonly)",
        final,
    )
    assert trailers == "applied"
    assert exchange.git_text(exchange.canonical_repo, "status", "--porcelain=v1") == ""


def test_finalize_rejects_missing_required_request_trailer(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated text.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")
    message.write_text(
        "\n".join(
            line
            for line in message.read_text(encoding="utf-8").splitlines()
            if not line.startswith("Fragment-Request-Disposition:")
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_cli(
        exchange.finalize_command(
            applied=applied,
            message_file=message,
            execute=True,
        )
    )

    assert result.returncode != 0
    assert "request-disposition trailer count" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied
    assert (exchange.canonical_repo / exchange.fragment).is_file()


def test_finalize_rejects_final_path_set_that_is_not_exact(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated text.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")

    result = run_cli(
        exchange.finalize_command(
            applied=applied,
            message_file=message,
            final_paths=("docs/owner.md", "docs/unchanged.md"),
            execute=True,
        )
    )

    assert result.returncode != 0
    assert "explicit final path set" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied


def test_finalize_accepts_complete_partial_disposition_records(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated subset.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")
    message.write_text(
        message.read_text(encoding="utf-8").replace(
            "Fragment-Request-Disposition: REQ-1=accept; "
            "destination=docs/owner.md#existing-target; "
            "effect=fixture integration",
            "Fragment-Request-Disposition: REQ-1=partial; "
            "destination=docs/owner.md#existing-target; "
            "effect=integrated subset\n"
            "Fragment-Accepted-Subset: REQ-1/A; "
            "destination=docs/owner.md#existing-target\n"
            "Fragment-Residual-Disposition: REQ-1/B=reject; "
            "destination=none; reason=not authorized",
        ),
        encoding="utf-8",
    )

    result = run_cli(
        exchange.finalize_command(
            applied=applied,
            message_file=message,
            execute=True,
        )
    )

    assert result.returncode == 0, result.stderr
    assert "PASS finalized fragment integration" in result.stdout


def test_finalize_rejects_partial_without_residual_record(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated subset.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")
    message.write_text(
        message.read_text(encoding="utf-8").replace(
            "Fragment-Request-Disposition: REQ-1=accept; "
            "destination=docs/owner.md#existing-target; "
            "effect=fixture integration",
            "Fragment-Request-Disposition: REQ-1=partial; "
            "destination=docs/owner.md#existing-target; "
            "effect=integrated subset\n"
            "Fragment-Accepted-Subset: REQ-1/A; "
            "destination=docs/owner.md#existing-target",
        ),
        encoding="utf-8",
    )

    result = run_cli(
        exchange.finalize_command(applied=applied, message_file=message)
    )

    assert result.returncode != 0
    assert "needs accepted and residual subset records" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied


def test_apply_rejects_preexisting_git_operation_without_mutation(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    exchange.git(
        exchange.canonical_repo,
        "update-ref",
        "CHERRY_PICK_HEAD",
        exchange.parent,
    )

    result = run_cli(exchange.apply_command(execute=True))

    assert result.returncode != 0
    assert "Git operation state already exists: CHERRY_PICK_HEAD" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == exchange.parent
    assert exchange.git_text(exchange.canonical_repo, "diff", "--cached", "--name-only") == ""
    assert not (exchange.canonical_repo / exchange.fragment).exists()


def test_finalize_rejects_applied_delta_that_is_not_the_frozen_source(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    extra = exchange.canonical_repo / "docs/unreviewed.md"
    extra.write_text("# Unreviewed\n", encoding="utf-8")
    exchange.git(exchange.canonical_repo, "add", "--", "docs/unreviewed.md")
    exchange.git(exchange.canonical_repo, "commit", "--amend", "--no-edit")
    applied = exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD")
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated text.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")
    status_before = exchange.git_text(
        exchange.canonical_repo, "status", "--porcelain=v1", "--untracked-files=all"
    )

    result = run_cli(exchange.finalize_command(applied=applied, message_file=message))

    assert result.returncode != 0
    assert "patch does not match the frozen source candidate" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied
    assert exchange.git_text(
        exchange.canonical_repo, "status", "--porcelain=v1", "--untracked-files=all"
    ) == status_before
    assert exchange.git_text(exchange.canonical_repo, "diff", "--cached", "--name-only") == ""


def test_finalize_rejects_git_pathspec_magic_without_mutation(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated text.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")
    status_before = exchange.git_text(
        exchange.canonical_repo, "status", "--porcelain=v1", "--untracked-files=all"
    )

    result = run_cli(
        exchange.finalize_command(
            applied=applied,
            message_file=message,
            final_paths=(":(glob)docs/*.md",),
            execute=True,
        )
    )

    assert result.returncode != 0
    assert "must not use Git pathspec magic" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied
    assert exchange.git_text(
        exchange.canonical_repo, "status", "--porcelain=v1", "--untracked-files=all"
    ) == status_before
    assert exchange.git_text(exchange.canonical_repo, "diff", "--cached", "--name-only") == ""


def test_finalize_treats_wildcard_filename_as_a_literal_path(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    literal_path = "docs/literal*.md"
    (exchange.canonical_repo / literal_path).write_text(
        "# Literal wildcard filename\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")

    result = run_cli(
        exchange.finalize_command(
            applied=applied,
            message_file=message,
            final_paths=(literal_path,),
            execute=True,
        )
    )

    assert result.returncode == 0, result.stderr
    final = exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD")
    assert exchange.git_text(
        exchange.canonical_repo,
        "diff",
        "--name-only",
        "--no-renames",
        exchange.parent,
        final,
        "--",
    ) == literal_path
    assert exchange.git_text(
        exchange.canonical_repo, "show", f"{final}:docs/owner.md"
    ) == "# Existing Target\n\nBase text."


@pytest.mark.parametrize(
    ("replacement", "diagnostic"),
    (
        (
            "Fragment-Request-Disposition: REQ-1=accept; "
            "destination=docs/owner.md#existing-target; effect=",
            "nonempty destination and effect",
        ),
        (
            "Fragment-Request-Disposition: REQ-1=stale; "
            "destination=none; reason=unspecified",
            "nonempty drift",
        ),
    ),
)
def test_finalize_rejects_incomplete_terminal_detail_records(
    exchange_factory,
    run_cli,
    replacement: str,
    diagnostic: str,
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated text.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")
    message.write_text(
        message.read_text(encoding="utf-8").replace(
            "Fragment-Request-Disposition: REQ-1=accept; "
            "destination=docs/owner.md#existing-target; "
            "effect=fixture integration",
            replacement,
        ),
        encoding="utf-8",
    )

    result = run_cli(exchange.finalize_command(applied=applied, message_file=message))

    assert result.returncode != 0
    assert diagnostic in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied
    assert exchange.git_text(exchange.canonical_repo, "diff", "--cached", "--name-only") == ""


def test_finalize_rejects_subset_label_used_as_accepted_and_residual(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    applied = apply_candidate(exchange, run_cli)
    (exchange.canonical_repo / "docs/owner.md").write_text(
        "# Existing Target\n\nIntegrated subset.\n", encoding="utf-8"
    )
    message = exchange.message_file(outcome="applied")
    message.write_text(
        message.read_text(encoding="utf-8").replace(
            "Fragment-Request-Disposition: REQ-1=accept; "
            "destination=docs/owner.md#existing-target; "
            "effect=fixture integration",
            "Fragment-Request-Disposition: REQ-1=partial; "
            "destination=docs/owner.md#existing-target; effect=integrated A\n"
            "Fragment-Accepted-Subset: REQ-1/A; "
            "destination=docs/owner.md#existing-target\n"
            "Fragment-Residual-Disposition: REQ-1/A=reject; "
            "destination=none; reason=not authorized",
        ),
        encoding="utf-8",
    )

    result = run_cli(exchange.finalize_command(applied=applied, message_file=message))

    assert result.returncode != 0
    assert "duplicate subset trailer" in result.stderr
    assert exchange.git_text(exchange.canonical_repo, "rev-parse", "HEAD") == applied
