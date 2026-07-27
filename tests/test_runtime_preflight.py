import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "runtime_preflight.py"
EXAMPLE_PROFILE = REPO_ROOT / "configs" / "runtime_preflight.example.tsv"
SPEC = importlib.util.spec_from_file_location("runtime_preflight", SCRIPT)
assert SPEC and SPEC.loader
PREFLIGHT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PREFLIGHT
SPEC.loader.exec_module(PREFLIGHT)


def write_profile(path: Path, rows: list[list[str]]) -> Path:
    lines = ["\t".join(PREFLIGHT.PROFILE_HEADER)]
    lines.extend("\t".join(row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def tool_row(
    check_id: str = "python",
    context: str = "any",
    required: str = "true",
    target: str = sys.executable,
) -> list[str]:
    return [
        check_id,
        "tool_version",
        context,
        required,
        target,
        json.dumps(["--version"]),
        r"^Python 3[.]",
        "Python runtime",
    ]


def run_cli(
    profile: Path,
    output: Path,
    *extra: str,
    context: str = "local",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--profile",
            str(profile),
            "--output",
            str(output),
            "--runtime-context",
            context,
            *extra,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def test_help_and_dry_run_are_side_effect_free(tmp_path: Path) -> None:
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert help_result.returncode == 0
    assert "--runtime-context" in help_result.stdout
    assert "--execute" in help_result.stdout

    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "missing-parent" / "preflight.tsv"
    result = run_cli(profile, output)
    assert result.returncode == 0
    assert "python: pass" in result.stdout
    assert "not runtime validation or cluster proof" in result.stdout
    assert "Dry-run complete" in result.stdout
    assert not output.parent.exists()


def test_tracked_example_profile_is_valid_and_locally_honest() -> None:
    _, checks = PREFLIGHT.load_profile(EXAMPLE_PROFILE)
    results = PREFLIGHT.run_checks(checks, "local")
    statuses = {result.check.check_id: result.status for result in results}
    assert statuses["python_version"] == "pass"
    assert statuses["sha256_python"] == "pass"
    assert statuses["rscript_version"] == "blocked"
    assert statuses["variant_annotation"] == "blocked"
    assert statuses["results_visibility"] == "blocked"


def test_execute_publishes_deterministic_result_and_replaces_valid_prior(
    tmp_path: Path,
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "preflight.tsv"
    first = run_cli(profile, output, "--execute")
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    rows = read_rows(output)
    assert len(rows) == 1
    assert rows[0]["status"] == "pass"
    assert rows[0]["profile_sha256"] == hashlib.sha256(profile.read_bytes()).hexdigest()

    second = run_cli(profile, output, "--execute")
    assert second.returncode == 0, second.stderr
    assert output.read_bytes() == original
    assert not list(tmp_path.glob(".*.lock"))
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.previous"))


def test_context_mismatch_is_blocked_or_not_checked(tmp_path: Path) -> None:
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            tool_row("required_cluster", "cluster_batch", "true"),
            tool_row("optional_cluster", "cluster_batch", "false"),
        ],
    )
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = {row["check_id"]: row for row in read_rows(output)}
    assert rows["required_cluster"]["status"] == "blocked"
    assert rows["optional_cluster"]["status"] == "not_checked"


def test_missing_tool_and_version_mismatch_are_failures(tmp_path: Path) -> None:
    mismatch = tool_row("mismatch")
    mismatch[6] = "^definitely-not-python$"
    profile = write_profile(
        tmp_path / "profile.tsv",
        [tool_row("missing", target="norad-tool-that-does-not-exist"), mismatch],
    )
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = {row["check_id"]: row for row in read_rows(output)}
    assert rows["missing"]["status"] == "fail"
    assert rows["mismatch"]["status"] == "fail"


def test_hash_utility_and_path_visibility(tmp_path: Path) -> None:
    visible = tmp_path / "visible"
    visible.mkdir()
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "sha256",
                "hash_utility",
                "any",
                "true",
                sys.executable,
                json.dumps(["python_hashlib"]),
                "sha256",
                "Python hashlib",
            ],
            [
                "visible",
                "path_visibility",
                "any",
                "true",
                str(visible),
                json.dumps(["directory_readable"]),
                "readable",
                "Visible directory",
            ],
            [
                "missing",
                "path_visibility",
                "any",
                "true",
                str(tmp_path / "missing"),
                json.dumps(["file_readable"]),
                "readable",
                "Missing file",
            ],
        ],
    )
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    rows = {row["check_id"]: row for row in read_rows(output)}
    assert rows["sha256"]["status"] == "pass"
    assert rows["visible"]["status"] == "pass"
    assert rows["missing"]["status"] == "fail"


def test_hash_utility_digest_mismatch_is_reported_without_aborting(
    tmp_path: Path,
) -> None:
    fake_hash = tmp_path / "sha256sum"
    fake_hash.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "cat >/dev/null\n"
        "printf '%064d  -\\n' 0\n",
        encoding="utf-8",
    )
    fake_hash.chmod(0o755)
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "bad_digest",
                "hash_utility",
                "any",
                "true",
                str(fake_hash),
                json.dumps(["sha256sum"]),
                "sha256",
                "Synthetic mismatching hash utility",
            ]
        ],
    )
    output = tmp_path / "preflight.tsv"

    result = run_cli(profile, output, "--execute")

    assert result.returncode == 0, result.stderr
    row = read_rows(output)[0]
    assert row["status"] == "fail"
    assert row["observed"] == "0" * 64
    assert row["detail"] == "SHA-256 digest mismatch"


def test_probe_timeout_is_recorded_as_a_failed_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    check = PREFLIGHT.Check(
        check_id="timeout",
        check_type="tool_version",
        runtime_context="any",
        required=True,
        target=sys.executable,
        probe_args=("--version",),
        expected=r"^Python",
        description="Synthetic timeout",
    )

    def time_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=kwargs["timeout"],
        )

    monkeypatch.setattr(PREFLIGHT.subprocess, "run", time_out)
    result = PREFLIGHT._probe_tool(check)

    assert result.status == "fail"
    assert result.detail == "Version probe failed"
    assert "timed out" in result.observed


def test_executable_visibility_uses_absolute_target_and_matching_expectation(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "tool"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "executable",
                "path_visibility",
                "any",
                "true",
                str(executable),
                json.dumps(["executable"]),
                "executable",
                "Executable path",
            ]
        ],
    )
    output = tmp_path / "preflight.tsv"
    assert run_cli(profile, output, "--execute").returncode == 0
    assert read_rows(output)[0]["status"] == "pass"

    relative = write_profile(
        tmp_path / "relative.tsv",
        [
            [
                "relative",
                "path_visibility",
                "any",
                "true",
                "relative/path",
                json.dumps(["file_readable"]),
                "readable",
                "Relative path",
            ]
        ],
    )
    rejected = run_cli(relative, tmp_path / "relative-output.tsv", "--execute")
    assert rejected.returncode == 2
    assert "must be absolute" in rejected.stderr


def test_r_namespace_with_fake_rscript(tmp_path: Path) -> None:
    fake = tmp_path / "Rscript"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "if [[ \"${*: -1}\" == \"GoodPackage\" ]]; then printf '1.2.3'; exit 0; fi\n"
        "exit 42\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    rows = []
    for check_id, package in (("good", "GoodPackage"), ("missing", "MissingPackage")):
        rows.append(
            [
                check_id,
                "r_namespace",
                "any",
                "true",
                package,
                json.dumps([str(fake)]),
                r"^[0-9]+[.][0-9]+[.][0-9]+$",
                "R namespace",
            ]
        )
    profile = write_profile(tmp_path / "profile.tsv", rows)
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 0, result.stderr
    observed = {row["check_id"]: row["status"] for row in read_rows(output)}
    assert observed == {"good": "pass", "missing": "fail"}


def test_r_namespace_requires_package_name(tmp_path: Path) -> None:
    profile = write_profile(
        tmp_path / "profile.tsv",
        [
            [
                "bad_namespace",
                "r_namespace",
                "any",
                "true",
                "bad namespace",
                json.dumps(["Rscript"]),
                r"^[0-9]+[.]",
                "Invalid package name",
            ]
        ],
    )
    result = run_cli(profile, tmp_path / "preflight.tsv", "--execute")
    assert result.returncode == 2
    assert "must be an R package name" in result.stderr


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda rows: [], "at least one check"),
        (lambda rows: [rows[0], rows[0]], "duplicate check_id"),
        (
            lambda rows: [rows[0][:-1] + [""]],
            "description must be nonempty",
        ),
        (
            lambda rows: [rows[0][:5] + ["not-json"] + rows[0][6:]],
            "not valid JSON",
        ),
    ],
)
def test_malformed_profiles_fail_without_output(
    tmp_path: Path,
    mutator,
    message: str,
) -> None:
    rows = mutator([tool_row()])
    profile = write_profile(tmp_path / "profile.tsv", rows)
    output = tmp_path / "preflight.tsv"
    result = run_cli(profile, output, "--execute")
    assert result.returncode == 2
    assert message in result.stderr
    assert not output.exists()


def test_profile_symlink_and_changed_profile_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    link = tmp_path / "profile-link.tsv"
    link.symlink_to(profile)
    output = tmp_path / "preflight.tsv"
    linked = run_cli(link, output, "--execute")
    assert linked.returncode == 2
    assert "symbolic link" in linked.stderr

    original_run_checks = PREFLIGHT.run_checks

    def mutate(checks, runtime_context):
        results = original_run_checks(checks, runtime_context)
        profile.write_text(profile.read_text() + "\n", encoding="utf-8")
        return results

    monkeypatch.setattr(PREFLIGHT, "run_checks", mutate)
    assert PREFLIGHT.main(
        [
            "--profile",
            str(profile),
            "--output",
            str(output),
            "--runtime-context",
            "local",
            "--execute",
        ]
    ) == 2
    assert not output.exists()


def test_foreign_lock_and_invalid_prior_are_preserved(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "preflight.tsv"
    lock = tmp_path / ".preflight.tsv.lock"
    lock.write_text("foreign\n")
    locked = run_cli(profile, output, "--execute")
    assert locked.returncode == 2
    assert "lock already exists" in locked.stderr
    assert lock.read_text() == "foreign\n"
    lock.unlink()

    output.write_text("foreign\n")
    invalid = run_cli(profile, output, "--execute")
    assert invalid.returncode == 2
    assert "invalid header" in invalid.stderr
    assert output.read_text() == "foreign\n"


def test_prior_report_rows_must_reconcile_to_profile(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    output = tmp_path / "preflight.tsv"
    assert run_cli(profile, output, "--execute").returncode == 0
    original = output.read_text(encoding="utf-8")
    output.write_text(original.replace("\tpython\ttool_version\t", "\ttampered\ttool_version\t"))

    result = run_cli(profile, output, "--execute")
    assert result.returncode == 2
    assert "check_id does not match the profile" in result.stderr
    assert "\ttampered\ttool_version\t" in output.read_text(encoding="utf-8")


def test_execute_requires_existing_real_parent_and_tsv_suffix(tmp_path: Path) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    missing_parent = run_cli(
        profile,
        tmp_path / "missing" / "preflight.tsv",
        "--execute",
    )
    assert missing_parent.returncode == 2
    assert "Output parent must already exist" in missing_parent.stderr

    wrong_suffix = run_cli(profile, tmp_path / "preflight.txt", "--execute")
    assert wrong_suffix.returncode == 2
    assert "must use the .tsv suffix" in wrong_suffix.stderr

    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(tmp_path, target_is_directory=True)
    linked_parent = run_cli(
        profile,
        parent_link / "preflight.tsv",
        "--execute",
    )
    assert linked_parent.returncode == 2
    assert "real directory" in linked_parent.stderr


def test_publish_failure_rolls_back_valid_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    profile_data, checks = PREFLIGHT.load_profile(profile)
    digest = hashlib.sha256(profile_data).hexdigest()
    results = PREFLIGHT.run_checks(checks, "local")
    previous = PREFLIGHT.result_bytes(digest, "local", results)
    output = tmp_path / "preflight.tsv"
    output.write_bytes(previous)

    real_validate = PREFLIGHT.validate_result_bytes
    calls = 0

    def fail_after_publish(data, profile_sha256, runtime_context, expected_checks):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise PREFLIGHT.PreflightError("injected validation failure")
        return real_validate(data, profile_sha256, runtime_context, expected_checks)

    monkeypatch.setattr(PREFLIGHT, "validate_result_bytes", fail_after_publish)
    with pytest.raises(PREFLIGHT.PreflightError, match="injected"):
        PREFLIGHT.publish(output, previous, digest, "local", checks)
    assert output.read_bytes() == previous
    assert not list(tmp_path.glob(".*.lock"))
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.previous"))


def test_first_publication_validation_failure_cleans_owned_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    profile_data, checks = PREFLIGHT.load_profile(profile)
    digest = hashlib.sha256(profile_data).hexdigest()
    rendered = PREFLIGHT.result_bytes(
        digest,
        "local",
        PREFLIGHT.run_checks(checks, "local"),
    )
    output = tmp_path / "preflight.tsv"
    real_validate = PREFLIGHT.validate_result_bytes
    calls = 0

    def fail_published(data, profile_sha256, runtime_context, expected_checks):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise PREFLIGHT.PreflightError("injected published validation failure")
        return real_validate(data, profile_sha256, runtime_context, expected_checks)

    monkeypatch.setattr(PREFLIGHT, "validate_result_bytes", fail_published)
    with pytest.raises(PREFLIGHT.PreflightError, match="injected published"):
        PREFLIGHT.publish(output, rendered, digest, "local", checks)

    assert not output.exists()
    assert not list(tmp_path.glob(".*.lock"))
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.previous"))


def test_rollback_failure_retains_lock_and_previous_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    profile_data, checks = PREFLIGHT.load_profile(profile)
    digest = hashlib.sha256(profile_data).hexdigest()
    rendered = PREFLIGHT.result_bytes(
        digest,
        "local",
        PREFLIGHT.run_checks(checks, "local"),
    )
    output = tmp_path / "preflight.tsv"
    output.write_bytes(rendered)
    real_validate = PREFLIGHT.validate_result_bytes
    real_replace = os.replace
    calls = 0

    def fail_published(data, profile_sha256, runtime_context, expected_checks):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise PREFLIGHT.PreflightError("injected published validation failure")
        return real_validate(data, profile_sha256, runtime_context, expected_checks)

    def fail_restore(source, destination):
        source_path = Path(source)
        if ".previous" in source_path.name and Path(destination) == output:
            raise OSError("injected restore failure")
        return real_replace(source, destination)

    monkeypatch.setattr(PREFLIGHT, "validate_result_bytes", fail_published)
    monkeypatch.setattr(PREFLIGHT.os, "replace", fail_restore)
    with pytest.raises(
        PREFLIGHT.PreflightError,
        match="rollback was incomplete",
    ):
        PREFLIGHT.publish(output, rendered, digest, "local", checks)

    lock = tmp_path / ".preflight.tsv.lock"
    previous = list(tmp_path.glob(".*.previous"))
    assert lock.is_file()
    assert len(previous) == 1
    assert previous[0].read_bytes() == rendered
    assert not output.exists()


def test_previous_report_cleanup_failure_retains_lock_and_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = write_profile(tmp_path / "profile.tsv", [tool_row()])
    profile_data, checks = PREFLIGHT.load_profile(profile)
    digest = hashlib.sha256(profile_data).hexdigest()
    rendered = PREFLIGHT.result_bytes(
        digest,
        "local",
        PREFLIGHT.run_checks(checks, "local"),
    )
    output = tmp_path / "preflight.tsv"
    output.write_bytes(rendered)
    real_unlink = Path.unlink

    def fail_backup_cleanup(path: Path, *args, **kwargs):
        if ".previous" in path.name:
            raise OSError("injected backup cleanup failure")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(PREFLIGHT.Path, "unlink", fail_backup_cleanup)
    with pytest.raises(
        PREFLIGHT.PreflightError,
        match="cleanup was incomplete",
    ):
        PREFLIGHT.publish(output, rendered, digest, "local", checks)

    lock = tmp_path / ".preflight.tsv.lock"
    previous = list(tmp_path.glob(".*.previous"))
    assert output.read_bytes() == rendered
    assert lock.is_file()
    assert len(previous) == 1
    assert previous[0].read_bytes() == rendered
