#!/usr/bin/env python3
"""Validate one fragment request target against the current canonical parent."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
from typing import Sequence

from _common import (
    cli_main,
    git,
    heading_anchors,
    object_text,
    require,
    verified_repository,
    verify_ancestor,
    verify_checkout,
    verify_remote_ref,
)


TARGET_MODES = ("existing anchor", "authorized-new anchor", "authorized-new owner")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--parent", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--mode", required=True, choices=TARGET_MODES)
    parser.add_argument("--heading", required=True)
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--remote", default="origin")
    return parser.parse_args(argv)


def _owner_path(value: str) -> str:
    path = PurePosixPath(value)
    require(not path.is_absolute(), "target owner must be repository-relative")
    require(
        all(part not in {"", ".", ".."} for part in value.split("/")),
        "invalid target owner",
    )
    require(
        not value.startswith(":") and "\n" not in value and "\r" not in value,
        "invalid target owner",
    )
    return value


def _all_anchors(mapping: dict[str, set[str]]) -> set[str]:
    return {anchor for anchors in mapping.values() for anchor in anchors}


def validate_target(
    *,
    base_text: str | None,
    parent_text: str | None,
    mode: str,
    heading: str,
    expected_anchor: str,
) -> None:
    """Bind the declared target mode to the literal heading and its anchor."""
    if mode == "existing anchor":
        require(base_text is not None and parent_text is not None, "target owner is missing")
        require(
            expected_anchor in heading_anchors(base_text).get(heading, set()),
            "base heading does not generate the declared anchor",
        )
        require(
            expected_anchor in heading_anchors(parent_text).get(heading, set()),
            "current heading does not generate the declared anchor",
        )
        return

    if mode == "authorized-new anchor":
        require(base_text is not None and parent_text is not None, "target owner is missing")
        parent_anchors = heading_anchors(parent_text)
        require(heading not in parent_anchors, "authorized-new heading already exists")
        require(
            expected_anchor not in _all_anchors(parent_anchors),
            "authorized-new anchor already exists",
        )
        proposed = heading_anchors(f"{parent_text}\n{heading}\n")
        require(
            expected_anchor in proposed.get(heading, set()),
            "proposed heading does not generate the declared anchor",
        )
        return

    require(mode == "authorized-new owner", f"invalid target mode: {mode}")
    require(base_text is None and parent_text is None, "authorized-new owner already exists")
    proposed = heading_anchors(f"{heading}\n")
    require(
        expected_anchor in proposed.get(heading, set()),
        "initial heading does not generate the declared anchor",
    )


def run(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    repository = verified_repository(args.repo)
    owner = _owner_path(args.owner)
    canonical_ref = verify_checkout(repository, args.branch, args.parent)
    verify_ancestor(repository, args.base, args.parent)
    verify_remote_ref(repository, args.remote, canonical_ref, args.parent)

    validate_target(
        base_text=object_text(repository, args.base, owner),
        parent_text=object_text(repository, args.parent, owner),
        mode=args.mode,
        heading=args.heading,
        expected_anchor=args.anchor,
    )
    literal_owner = f":(top,literal){owner}"
    diff = git(
        repository,
        ["diff", "--name-status", args.base, args.parent, "--", literal_owner],
    ).stdout
    if diff:
        print(diff, end="")
    print(f"PASS fragment target {owner}#{args.anchor}")


if __name__ == "__main__":
    cli_main(run)
