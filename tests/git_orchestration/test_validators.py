"""Contract tests for candidate and target validation commands."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "scripts" / "git_orchestration"
PUBLIC_COMMANDS = (
    (sys.executable, TOOLS / "validate_documentation.py"),
    (sys.executable, TOOLS / "validate_fragment_candidate.py"),
    (sys.executable, TOOLS / "validate_fragment_target.py"),
    ("bash", TOOLS / "apply_fragment_candidate.sh"),
    ("bash", TOOLS / "finalize_fragment_integration.sh"),
    ("bash", TOOLS / "record_fragment_noop.sh"),
    ("bash", TOOLS / "publish_exact_ref.sh"),
)


def test_documentation_validator_accepts_repository_from_arbitrary_cwd(
    run_cli,
) -> None:
    result = run_cli(
        [
            sys.executable,
            str(TOOLS / "validate_documentation.py"),
            "--repo",
            str(REPO_ROOT),
        ]
    )

    assert result.returncode == 0, result.stderr
    assert "PASS documentation structure" in result.stdout


@pytest.mark.parametrize(("interpreter", "script"), PUBLIC_COMMANDS)
def test_public_commands_expose_help_and_reject_invalid_arguments(
    run_cli, interpreter: str, script: Path
) -> None:
    help_result = run_cli([interpreter, str(script), "--help"])
    assert help_result.returncode == 0
    assert "usage" in help_result.stdout.lower()

    invalid_result = run_cli([interpreter, str(script), "--not-a-real-option"])
    assert invalid_result.returncode != 0
    diagnostic = (invalid_result.stdout + invalid_result.stderr).lower()
    assert "error" in diagnostic
    assert "not-a-real-option" in diagnostic or "required" in diagnostic


def test_candidate_validator_accepts_frozen_candidate_from_arbitrary_cwd(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()

    result = run_cli(exchange.candidate_command())

    assert result.returncode == 0, result.stderr
    assert f"PASS frozen fragment candidate {exchange.candidate}" in result.stdout
    assert exchange.git_text(exchange.candidate_repo, "status", "--porcelain=v1") == ""


def test_candidate_validator_rejects_malformed_fragment(
    exchange_factory, run_cli
) -> None:
    malformed = exchange_factory(
        fragment_text=(
            "# TEST-EXCHANGE integration fragment\n\n"
            "- Fragment ID: `TEST-EXCHANGE`\n"
            "- Owning task: `CONCURRENCY-02`\n"
            "- Lane ID: `sidecar`\n"
            "- Candidate branch: `sidecar`\n"
            "- Exact base: `{BASE}`\n"
            "- Evidence and scope boundary: `test`\n\n"
            "## Request `REQ-1`\n\n"
            "- Target owner: `docs/owner.md`\n"
            "- Target heading or anchor: `# Existing Target`\n"
            "- Target mode: `existing anchor`\n"
            "- Requested update: `test`\n"
            "- Provenance: `test`\n"
            "- Assumptions and coupling: `none`\n"
            "- Candidate disposition: `accept`\n"
        )
    )

    result = run_cli(malformed.candidate_command())

    assert result.returncode != 0
    assert "candidate disposition" in result.stderr
    assert "`pending`" in result.stderr


def test_candidate_validator_requires_fields_within_each_request(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    fragment = exchange.candidate_repo / exchange.fragment
    text = fragment.read_text(encoding="utf-8")
    text = text.replace(
        "- Provenance: `Synthetic exchange fixture.`\n",
        "",
    )
    text += """
## Request `REQ-2`

- Target owner: `docs/owner.md`
- Target heading or anchor: `# Existing Target`
- Target mode: `existing anchor`
- Requested update: `Second bounded update.`
- Provenance: `First provenance value.`
- Provenance: `Second provenance value.`
- Assumptions and coupling: `No executable behavior changes.`
- Candidate disposition: `pending`
"""
    fragment.write_text(text, encoding="utf-8")
    exchange.git(exchange.candidate_repo, "add", "--", exchange.fragment)
    exchange.git(exchange.candidate_repo, "commit", "--amend", "--no-edit")
    exchange.candidate = exchange.git_text(exchange.candidate_repo, "rev-parse", "HEAD")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "request REQ-1 must contain exactly one Provenance field" in result.stderr


def test_candidate_validator_rejects_empty_request_field(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    fragment = exchange.candidate_repo / exchange.fragment
    text = fragment.read_text(encoding="utf-8").replace(
        "- Provenance: `Synthetic exchange fixture.`",
        "- Provenance:",
    )
    fragment.write_text(text, encoding="utf-8")
    exchange.git(exchange.candidate_repo, "add", "--", exchange.fragment)
    exchange.git(exchange.candidate_repo, "commit", "--amend", "--no-edit")
    exchange.candidate = exchange.git_text(exchange.candidate_repo, "rev-parse", "HEAD")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "request REQ-1 Provenance field must be nonempty" in result.stderr


def test_candidate_validator_rejects_duplicate_request_ids(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    fragment = exchange.candidate_repo / exchange.fragment
    text = fragment.read_text(encoding="utf-8")
    request = text[text.index("## Request `REQ-1`") :]
    fragment.write_text(f"{text}\n{request}", encoding="utf-8")
    exchange.git(exchange.candidate_repo, "add", "--", exchange.fragment)
    exchange.git(exchange.candidate_repo, "commit", "--amend", "--no-edit")
    exchange.candidate = exchange.git_text(exchange.candidate_repo, "rev-parse", "HEAD")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "fragment request IDs must be unique" in result.stderr


def test_candidate_validator_rejects_terminal_record_delimiters_in_request_id(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    fragment = exchange.candidate_repo / exchange.fragment
    fragment.write_text(
        fragment.read_text(encoding="utf-8").replace("REQ-1", "REQ/1"),
        encoding="utf-8",
    )
    exchange.git(exchange.candidate_repo, "add", "--", exchange.fragment)
    exchange.git(exchange.candidate_repo, "commit", "--amend", "--no-edit")
    exchange.candidate = exchange.git_text(exchange.candidate_repo, "rev-parse", "HEAD")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "terminal-record delimiters" in result.stderr


def test_candidate_validator_binds_identity_metadata_to_preamble(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory()
    fragment = exchange.candidate_repo / exchange.fragment
    text = fragment.read_text(encoding="utf-8")
    identity = "- Fragment ID: `TEST-EXCHANGE`\n"
    text = text.replace(identity, "").replace(
        "- Candidate disposition: `pending`",
        f"- Candidate disposition: `pending`\n{identity.rstrip()}",
    )
    fragment.write_text(text, encoding="utf-8")
    exchange.git(exchange.candidate_repo, "add", "--", exchange.fragment)
    exchange.git(exchange.candidate_repo, "commit", "--amend", "--no-edit")
    exchange.candidate = exchange.git_text(exchange.candidate_repo, "rev-parse", "HEAD")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "Fragment ID field must precede all requests" in result.stderr


@pytest.mark.parametrize(
    ("original", "replacement", "diagnostic"),
    (
        (
            "# TEST-EXCHANGE integration fragment",
            "# WRONG-ID integration fragment",
            "fragment H1 must match its filename",
        ),
        (
            "- Candidate branch: `sidecar`",
            "- Candidate branch: `wrong-branch`",
            "candidate branch metadata",
        ),
        (
            "- Exact base:",
            "- Exact base: `0000000000000000000000000000000000000000` #",
            "exact-base metadata",
        ),
    ),
)
def test_candidate_validator_binds_fragment_identity_metadata(
    exchange_factory,
    run_cli,
    original: str,
    replacement: str,
    diagnostic: str,
) -> None:
    exchange = exchange_factory()
    fragment = exchange.candidate_repo / exchange.fragment
    text = fragment.read_text(encoding="utf-8")
    if original == "- Exact base:":
        text = "\n".join(
            replacement if line.startswith(original) else line
            for line in text.splitlines()
        ) + "\n"
    else:
        text = text.replace(original, replacement)
    fragment.write_text(text, encoding="utf-8")
    exchange.git(exchange.candidate_repo, "add", "--", exchange.fragment)
    exchange.git(exchange.candidate_repo, "commit", "--amend", "--no-edit")
    exchange.candidate = exchange.git_text(exchange.candidate_repo, "rev-parse", "HEAD")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert diagnostic in result.stderr


def test_candidate_validator_rejects_moved_local_ref(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()
    exchange.git(exchange.candidate_repo, "commit", "--allow-empty", "-m", "move ref")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "local ref moved" in result.stderr


def test_candidate_validator_rejects_moved_remote_ref(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()
    exchange.git(
        exchange.remote,
        "update-ref",
        f"refs/heads/{exchange.candidate_branch}",
        exchange.base,
    )

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "remote ref moved" in result.stderr


def test_candidate_validator_rejects_dirty_worktree(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()
    (exchange.candidate_repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    result = run_cli(exchange.candidate_command())

    assert result.returncode != 0
    assert "worktree is not clean" in result.stderr


def test_candidate_validator_rejects_wrong_parent(exchange_factory, run_cli) -> None:
    exchange = exchange_factory()
    command = exchange.candidate_command()
    command[command.index("--base") + 1] = exchange.candidate

    result = run_cli(command)

    assert result.returncode != 0
    assert "not one non-merge child" in result.stderr


def test_candidate_validator_rejects_unreserved_changed_path(
    exchange_factory, run_cli
) -> None:
    exchange = exchange_factory(candidate_changes={"docs/unreserved.md": "unexpected\n"})
    command = exchange.candidate_command(
        expected=(("A", exchange.fragment), ("A", "docs/unreserved.md")),
        allowed=(exchange.fragment,),
    )

    result = run_cli(command)

    assert result.returncode != 0
    assert "paths exceed packet reservations" in result.stderr
    assert "docs/unreserved.md" in result.stderr


@pytest.mark.parametrize(
    ("owner", "mode", "heading", "anchor"),
    (
        ("docs/owner.md", "existing anchor", "# Existing Target", "existing-target"),
        ("docs/owner.md", "authorized-new anchor", "## Planned Target", "planned-target"),
        ("docs/new-owner.md", "authorized-new owner", "# New Owner", "new-owner"),
    ),
)
def test_target_validator_accepts_each_target_mode(
    exchange_factory,
    run_cli,
    owner: str,
    mode: str,
    heading: str,
    anchor: str,
) -> None:
    exchange = exchange_factory()

    result = run_cli(
        exchange.target_command(
            owner=owner,
            mode=mode,
            heading=heading,
            anchor=anchor,
        )
    )

    assert result.returncode == 0, result.stderr
    assert f"PASS fragment target {owner}#{anchor}" in result.stdout


def test_target_validator_treats_owner_as_literal_git_pathspec(
    exchange_factory, run_cli
) -> None:
    wildcard_match = "docs/literal1.md"
    owner = "docs/literal[1].md"
    exchange = exchange_factory(
        canonical_changes={wildcard_match: "# Different file\n"}
    )

    result = run_cli(
        exchange.target_command(
            owner=owner,
            mode="authorized-new owner",
            heading="# Bracket Owner",
            anchor="bracket-owner",
        )
    )

    assert result.returncode == 0, result.stderr
    assert wildcard_match not in result.stdout
    assert f"PASS fragment target {owner}#bracket-owner" in result.stdout


@pytest.mark.parametrize(
    ("mode", "owner", "heading", "anchor", "diagnostic"),
    (
        (
            "existing anchor",
            "docs/owner.md",
            "# Existing Target",
            "wrong-anchor",
            "base heading does not generate",
        ),
        (
            "authorized-new anchor",
            "docs/owner.md",
            "## Planned Target",
            "wrong-anchor",
            "proposed heading does not generate",
        ),
        (
            "authorized-new owner",
            "docs/new-owner.md",
            "# New Owner",
            "wrong-anchor",
            "initial heading does not generate",
        ),
    ),
)
def test_target_validator_rejects_heading_anchor_mismatch(
    exchange_factory,
    run_cli,
    mode: str,
    owner: str,
    heading: str,
    anchor: str,
    diagnostic: str,
) -> None:
    exchange = exchange_factory()

    result = run_cli(
        exchange.target_command(
            owner=owner,
            mode=mode,
            heading=heading,
            anchor=anchor,
        )
    )

    assert result.returncode != 0
    assert diagnostic in result.stderr
