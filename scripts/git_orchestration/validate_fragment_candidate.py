#!/usr/bin/env python3
"""Validate one frozen integration-fragment candidate without changing Git state."""

from __future__ import annotations

import argparse
import re
from pathlib import Path, PurePosixPath
from typing import Sequence

from _common import (
    OrchestrationError,
    changed_rows,
    cli_main,
    object_text,
    require,
    verified_repository,
    verify_checkout,
    verify_diff_check,
    verify_remote_ref,
    verify_single_child,
)


METADATA_LABELS = (
    "Fragment ID",
    "Owning task",
    "Lane ID",
    "Candidate branch",
    "Exact base",
    "Evidence and scope boundary",
)
REQUEST_LABELS = (
    "Target owner",
    "Target heading or anchor",
    "Target mode",
    "Requested update",
    "Provenance",
    "Assumptions and coupling",
    "Candidate disposition",
)
TARGET_MODES = {
    "`existing anchor`",
    "`authorized-new anchor`",
    "`authorized-new owner`",
}
FRAGMENT_ID = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9-]+$")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--fragment", required=True)
    parser.add_argument("--remote", default="origin")
    parser.add_argument(
        "--expected-change",
        required=True,
        action="append",
        nargs=2,
        metavar=("STATUS", "PATH"),
        help="Repeat for each frozen name-status row.",
    )
    parser.add_argument(
        "--allowed-path",
        required=True,
        action="append",
        help="Repeat for every packet write reservation, including unused paths.",
    )
    return parser.parse_args(argv)


def _relative_path(value: str, label: str) -> str:
    path = PurePosixPath(value)
    require(not path.is_absolute(), f"{label} must be repository-relative")
    require(
        all(part not in {"", ".", ".."} for part in value.split("/")),
        f"invalid {label}: {value}",
    )
    require(
        not value.startswith(":") and "\n" not in value and "\r" not in value,
        f"invalid {label}: {value}",
    )
    return value


def _field_values(text: str, label: str) -> list[str]:
    prefix = f"- {label}:"
    return [line[len(prefix) :].strip() for line in text.splitlines() if line.startswith(prefix)]


def _request_sections(text: str) -> list[tuple[str, str]]:
    """Return exact request IDs and their section-local bodies."""
    heading_lines = re.findall(
        r"^## Request(?:[ \t]|$)[^\r\n]*$",
        text,
        flags=re.MULTILINE,
    )
    matches = list(
        re.finditer(
            r"^## Request `([^`\r\n]*)`[ \t]*$",
            text,
            flags=re.MULTILINE,
        )
    )
    require(
        len(matches) == len(heading_lines),
        "every Request heading must use the exact ## Request `<REQUEST-ID>` form",
    )
    require(bool(matches), "fragment must contain at least one request")

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        request_id = match.group(1)
        require(
            bool(request_id) and request_id == request_id.strip(),
            "fragment request IDs must be nonempty and have no surrounding whitespace",
        )
        require(
            not any(delimiter in request_id for delimiter in ("/", "=", ";")),
            "fragment request IDs must not contain terminal-record delimiters",
        )
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((request_id, text[match.end() : end]))
    return sections


def validate_fragment(
    text: str,
    fragment_path: str,
    candidate_branch: str,
    base_sha: str,
) -> None:
    """Validate the candidate-only Markdown shape defined by the fragment schema."""
    headings = re.findall(r"^# (.+ integration fragment)$", text, flags=re.MULTILINE)
    require(len(headings) == 1, "fragment must have one H1 ending in 'integration fragment'")

    requests = _request_sections(text)
    first_request = re.search(
        r"^## Request `[^`\r\n]*`[ \t]*$",
        text,
        flags=re.MULTILINE,
    )
    require(first_request is not None, "fragment must contain at least one request")
    preamble = text[: first_request.start()]

    for label in METADATA_LABELS:
        values = _field_values(text, label)
        require(len(values) == 1, f"fragment must contain one {label} field")
        require(bool(values[0]), f"fragment {label} field must be nonempty")
        require(
            _field_values(preamble, label) == values,
            f"fragment {label} field must precede all requests",
        )

    for label in REQUEST_LABELS:
        require(
            not _field_values(preamble, label),
            f"request field {label} must appear inside a Request section",
        )

    request_ids = [request_id for request_id, _ in requests]
    require(len(request_ids) == len(set(request_ids)), "fragment request IDs must be unique")

    for request_id, section in requests:
        values_by_label: dict[str, str] = {}
        for label in REQUEST_LABELS:
            values = _field_values(section, label)
            require(
                len(values) == 1,
                f"request {request_id} must contain exactly one {label} field",
            )
            require(bool(values[0]), f"request {request_id} {label} field must be nonempty")
            values_by_label[label] = values[0]
        require(
            values_by_label["Candidate disposition"] == "`pending`",
            f"request {request_id} candidate disposition must be `pending`",
        )
        require(
            values_by_label["Target mode"] in TARGET_MODES,
            f"request {request_id} has an invalid target mode",
        )

    fragment = PurePosixPath(fragment_path)
    require(fragment.suffix == ".md", "fragment path must use the .md suffix")
    filename_id = fragment.stem
    require(bool(FRAGMENT_ID.fullmatch(filename_id)), "fragment filename has an invalid ID")
    declared_ids = _field_values(text, "Fragment ID")
    require(declared_ids == [f"`{filename_id}`"], "fragment ID must match its filename")
    require(
        headings == [f"{filename_id} integration fragment"],
        "fragment H1 must match its filename",
    )
    require(
        _field_values(text, "Candidate branch") == [f"`{candidate_branch}`"],
        "candidate branch metadata does not match the frozen branch",
    )
    require(
        _field_values(text, "Exact base") == [f"`{base_sha}`"],
        "exact-base metadata does not match the frozen base",
    )


def run(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    repository = verified_repository(args.repo)
    fragment_path = _relative_path(args.fragment, "fragment path")
    require(
        PurePosixPath(fragment_path).parent == PurePosixPath("docs/fragments"),
        "fragment must be directly under docs/fragments",
    )

    candidate_ref = verify_checkout(repository, args.branch, args.candidate)
    verify_single_child(repository, args.base, args.candidate)
    verify_diff_check(repository, args.base, args.candidate)

    expected = tuple(
        sorted(
            (status, _relative_path(path, "expected path"))
            for status, path in args.expected_change
        )
    )
    actual = tuple(sorted(changed_rows(repository, args.base, args.candidate)))
    require(actual == expected, "candidate diff does not match the frozen handoff")

    allowed = {_relative_path(path, "allowed path") for path in args.allowed_path}
    unexpected = sorted(path for _, path in actual if path not in allowed)
    require(not unexpected, f"candidate paths exceed packet reservations: {unexpected}")
    require(fragment_path in {path for _, path in actual}, "fragment is absent from candidate diff")

    fragment = object_text(repository, args.candidate, fragment_path)
    require(fragment is not None, "fragment object is unavailable at candidate SHA")
    try:
        validate_fragment(fragment, fragment_path, args.branch, args.base)
    except UnicodeError as exc:
        raise OrchestrationError(f"fragment is not valid UTF-8 text: {exc}") from exc

    verify_remote_ref(repository, args.remote, candidate_ref, args.candidate)
    print(f"PASS frozen fragment candidate {args.candidate}")


if __name__ == "__main__":
    cli_main(run)
