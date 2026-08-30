"""Independent tests for neutral source and artifact-root authorities."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from emrys.libraries import source_authority

PROJECT_NAME = "emrys-rna-workflow"
PYTHON_FILES: Mapping[str, bytes] = {
    "__init__.py": b'"""Synthetic EMRYS package."""\n',
    "contracts/__init__.py": b'"""Synthetic contracts package."""\n',
    "reporting/__init__.py": b'"""Synthetic reporting package."""\n',
    "reporting/owner.py": b"VALUE = 1\n",
}
RESOURCE_FILES: Mapping[str, bytes] = {
    "contracts/schemas/artifacts/v1/example.json": b'{"schema": true}\n',
    "contracts/schemas/artifacts/v2/artifact_record.schema.json": b'{"schema": true}\n',
    "contracts/schemas/artifacts/v3/report_receipt.schema.json": b'{"schema": 3}\n',
    "contracts/schemas/artifacts/v4/report_receipt.schema.json": b'{"schema": 4}\n',
    "contracts/schemas/orchestration/v1/common.schema.json": b'{"schema": true}\n',
    "contracts/schemas/orchestration/v2/request.schema.json": b'{"schema": true}\n',
    "contracts/schemas/orchestration/v3/execution_profile.schema.json": b'{"schema": 3}\n',
    "orchestration/local_pilot/resources/default_execution.yaml": (
        b"schema_version: emrys.execution-profile.v1\n"
    ),
    "resources/runtime/runtime_policy.tsv": b"check_id\tcheck_type\n",
    "resources/runtime/pixi.toml": b"[workspace]\n",
    "resources/runtime/pixi.lock": b"version: 7\n",
    "reporting/styles/example.css": b"body { color: black; }\n",
    "reporting/templates/example.html.j2": b"<!doctype html>\n",
    "runtime/data.bin": b"synthetic package data\n",
}
GIT_ROUTING_VARIABLES = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_WORK_TREE",
)


@dataclass(frozen=True, slots=True)
class CheckoutFixture:
    """Minimal checkout and independently placed active package."""

    root: Path
    checkout_package: Path
    package_root: Path


def _write_files(root: Path, files: Mapping[str, bytes]) -> None:
    for relative_path, payload in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def _initialize_git(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "init", "--quiet", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)


def _commit_package(fixture: CheckoutFixture) -> str:
    subprocess.run(
        ["git", "add", "pyproject.toml", "src/emrys"],
        cwd=fixture.root,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=EMRYS Fixture",
            "-c",
            "user.email=emrys-fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "fixture package",
        ],
        cwd=fixture.root,
        text=True,
        capture_output=True,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=fixture.root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def _project_configuration(name: str = PROJECT_NAME) -> bytes:
    return (
        f'[project]\nname = "{name}"\n'
        "\n"
        "[tool.setuptools]\n"
        'package-dir = {"" = "src"}\n'
        "include-package-data = false\n"
        "\n"
        "[tool.setuptools.packages.find]\n"
        'where = ["src"]\n'
        'include = ["emrys*"]\n'
        "namespaces = false\n"
        "\n"
        "[tool.setuptools.package-data]\n"
        '"emrys.contracts" = ["schemas/artifacts/v1/*.json", "schemas/artifacts/v2/*.json", "schemas/artifacts/v3/*.json", "schemas/artifacts/v4/*.json", "schemas/orchestration/v1/*.json", "schemas/orchestration/v2/*.json", "schemas/orchestration/v3/*.json"]\n'
        '"emrys.orchestration.local_pilot" = ["resources/*.yaml"]\n'
        '"emrys" = ["resources/runtime/*"]\n'
        '"emrys.reporting" = ["styles/*.css", "templates/*.html.j2"]\n'
    ).encode()


def _build_fixture(
    tmp_path: Path,
    *,
    git_root: Path | None = None,
) -> CheckoutFixture:
    root = tmp_path / "checkout"
    checkout_package = root / "src" / "emrys"
    package_root = tmp_path / "active-package" / "emrys"
    _initialize_git(root if git_root is None else git_root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_bytes(_project_configuration())
    _write_files(checkout_package, PYTHON_FILES)
    _write_files(checkout_package, RESOURCE_FILES)
    _write_files(package_root, PYTHON_FILES)
    _write_files(package_root, RESOURCE_FILES)
    # Runtime caches and bytecode are deliberately outside package identity.
    cache = package_root / "reporting" / "__pycache__" / "owner.pyc"
    cache.parent.mkdir(parents=True)
    cache.write_bytes(b"unrelated bytecode\n")
    return CheckoutFixture(
        root=root,
        checkout_package=checkout_package,
        package_root=package_root,
    )


def _admit(fixture: CheckoutFixture) -> source_authority.SourceCheckout:
    return source_authority.admit_source_checkout(
        root=fixture.root,
        package_root=fixture.package_root,
    )


def _assert_rejected(
    *,
    root: Path,
    package_root: Path,
    ops: source_authority.SourceAuthorityOps = (
        source_authority.DEFAULT_SOURCE_AUTHORITY_OPS
    ),
) -> source_authority.SourceCheckoutError:
    with pytest.raises(source_authority.SourceCheckoutError) as caught:
        source_authority.admit_source_checkout(
            root=root,
            package_root=package_root,
            ops=ops,
        )
    return caught.value


def test_admits_canonical_checkout_with_identical_package(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)

    admitted = _admit(fixture)

    assert isinstance(admitted, source_authority.SourceCheckout)
    assert admitted.root == fixture.root


def test_admits_independent_canonical_artifact_root(tmp_path: Path) -> None:
    artifact_root = tmp_path / "run-root"
    artifact_root.mkdir()

    admitted = source_authority.admit_artifact_source_root(root=artifact_root)

    assert admitted == source_authority.ArtifactSourceRoot(root=artifact_root)


@pytest.mark.parametrize("kind", ("relative", "noncanonical", "symlink", "file"))
def test_rejects_unsafe_artifact_source_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    artifact_root = tmp_path / "run-root"
    artifact_root.mkdir()
    candidate = artifact_root
    if kind == "relative":
        monkeypatch.chdir(tmp_path)
        candidate = Path("run-root")
    elif kind == "noncanonical":
        candidate = artifact_root / ".." / artifact_root.name
    elif kind == "symlink":
        candidate = tmp_path / "run-root-link"
        candidate.symlink_to(artifact_root, target_is_directory=True)
    elif kind == "file":
        candidate = tmp_path / "run-root-file"
        candidate.write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(source_authority.ArtifactSourceRootError):
        source_authority.admit_artifact_source_root(root=candidate)


def test_package_identity_matches_clean_checkout_head(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    admitted = _admit(fixture)

    assert source_authority.package_matches_checkout_head(
        source_checkout=admitted,
        package_root=fixture.package_root,
    )


def test_matching_checkout_head_commit_rejects_head_aba(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    commit = _commit_package(fixture)
    admitted = _admit(fixture)
    head_calls = 0

    def move_head(
        command: Sequence[str],
        **options: object,
    ) -> subprocess.CompletedProcess[object]:
        nonlocal head_calls
        if tuple(command) == ("git", "rev-parse", "--verify", "HEAD"):
            head_calls += 1
            value = commit if head_calls == 1 else "e" * 40
            return subprocess.CompletedProcess(command, 0, value + "\n", "")
        return subprocess.run(command, **options)  # type: ignore[arg-type]

    with pytest.raises(source_authority.SourceCheckoutError, match="HEAD changed"):
        source_authority.matching_checkout_head_commit(
            source_checkout=admitted,
            package_root=fixture.package_root,
            ops=source_authority.SourceAuthorityOps(run_git=move_head),
        )


def test_matching_checkout_head_commit_returns_none_for_dirty_package(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    changed = b"VALUE = 2\n"
    (fixture.checkout_package / "reporting" / "owner.py").write_bytes(changed)
    (fixture.package_root / "reporting" / "owner.py").write_bytes(changed)
    admitted = _admit(fixture)

    assert (
        source_authority.matching_checkout_head_commit(
            source_checkout=admitted,
            package_root=fixture.package_root,
        )
        is None
    )


def test_matching_clean_checkout_head_commit_rejects_dirty_external_producer(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    producer = fixture.root / "src" / "emrys" / "stages" / "owner" / "step.sh"
    producer.parent.mkdir(parents=True)
    producer.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", str(producer.relative_to(fixture.root))],
        cwd=fixture.root,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=EMRYS Fixture",
            "-c",
            "user.email=emrys-fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "fixture producer",
        ],
        cwd=fixture.root,
        check=True,
    )
    admitted = _admit(fixture)
    producer.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")

    assert (
        source_authority.matching_clean_checkout_head_commit(
            source_checkout=admitted,
            package_root=fixture.package_root,
        )
        is None
    )


def test_controlled_python_ignores_timestamp_valid_adjacent_bytecode(
    tmp_path: Path,
) -> None:
    source = tmp_path / "payload.py"
    malicious = b"VALUE = 'evil'\n"
    safe = b"VALUE = 'safe'\n"
    assert len(malicious) == len(safe)
    source.write_bytes(malicious)
    source_state = source.stat()
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(source)],
        check=True,
    )
    source.write_bytes(safe)
    source.touch()
    source.chmod(source_state.st_mode)
    # Timestamp pyc headers use whole seconds plus source size.
    os.utime(source, ns=(source_state.st_atime_ns, source_state.st_mtime_ns))
    program = (
        f"import sys; sys.path.insert(0, {str(tmp_path)!r}); "
        "import payload; print(payload.VALUE)"
    )
    uncontrolled = subprocess.run(
        [sys.executable, "-I", "-c", program],
        check=True,
        capture_output=True,
        text=True,
    )
    controlled = subprocess.run(
        source_authority.controlled_python_argv(sys.executable, "-c", program),
        check=True,
        capture_output=True,
        text=True,
    )

    assert uncontrolled.stdout.strip() == "evil"
    assert controlled.stdout.strip() == "safe"


def test_uncontrolled_python_runtime_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(source_authority.sys, "pycache_prefix", None)

    with pytest.raises(source_authority.SourceCheckoutError, match="pycache_prefix"):
        source_authority.require_controlled_python_runtime()


def test_package_identity_rejects_dirty_tracked_checkout_bytes(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    changed = b"VALUE = 2\n"
    (fixture.checkout_package / "reporting" / "owner.py").write_bytes(changed)
    (fixture.package_root / "reporting" / "owner.py").write_bytes(changed)
    admitted = _admit(fixture)

    assert not source_authority.package_matches_checkout_head(
        source_checkout=admitted,
        package_root=fixture.package_root,
    )


@pytest.mark.parametrize(
    "relative",
    (
        Path("contracts/schemas/artifacts/v3/report_receipt.schema.json"),
        Path("contracts/schemas/artifacts/v4/report_receipt.schema.json"),
        Path("contracts/schemas/orchestration/v1/common.schema.json"),
        Path("contracts/schemas/orchestration/v3/execution_profile.schema.json"),
        Path("orchestration/local_pilot/resources/default_execution.yaml"),
        Path("resources/runtime/runtime_policy.tsv"),
    ),
)
def test_package_identity_includes_declared_resource_bytes(
    tmp_path: Path,
    relative: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    changed = b'{"schema": "changed"}\n'
    (fixture.checkout_package / relative).write_bytes(changed)
    (fixture.package_root / relative).write_bytes(changed)
    admitted = _admit(fixture)

    assert not source_authority.package_matches_checkout_head(
        source_checkout=admitted,
        package_root=fixture.package_root,
    )


def test_package_identity_rejects_untracked_package_file(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    relative_path = Path("reporting/untracked_owner.py")
    _write_files(fixture.checkout_package, {str(relative_path): b"VALUE = 2\n"})
    _write_files(fixture.package_root, {str(relative_path): b"VALUE = 2\n"})
    admitted = _admit(fixture)

    assert not source_authority.package_matches_checkout_head(
        source_checkout=admitted,
        package_root=fixture.package_root,
    )


@pytest.mark.parametrize(
    "relative",
    [
        Path("reporting/nested_python"),
        Path("reporting/templates/nested_resources"),
    ],
)
@pytest.mark.parametrize("which_tree", ["checkout", "executing"])
def test_package_identity_rejects_nested_directory_symlinks(
    tmp_path: Path,
    relative: Path,
    which_tree: str,
) -> None:
    fixture = _build_fixture(tmp_path)
    outside = tmp_path / f"outside-{which_tree}-{relative.name}"
    outside.mkdir()
    suffix = ".py" if relative.name == "nested_python" else ".html.j2"
    (outside / f"payload{suffix}").write_text("foreign\n", encoding="utf-8")
    target_root = (
        fixture.checkout_package if which_tree == "checkout" else fixture.package_root
    )
    link = target_root / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(
        source_authority.SourceCheckoutError, match="contains a symbolic link"
    ):
        _admit(fixture)


def test_rejects_relative_checkout_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)

    error = _assert_rejected(
        root=Path(fixture.root.name),
        package_root=fixture.package_root,
    )

    assert "absolute" in str(error).lower()


def test_rejects_noncanonical_checkout_root(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    noncanonical = fixture.root / ".." / fixture.root.name

    error = _assert_rejected(
        root=noncanonical,
        package_root=fixture.package_root,
    )

    assert "canonical" in str(error).lower()


def test_rejects_symbolic_link_checkout_root(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    linked_root = tmp_path / "linked-checkout"
    linked_root.symlink_to(fixture.root, target_is_directory=True)

    error = _assert_rejected(
        root=linked_root,
        package_root=fixture.package_root,
    )

    assert "symbolic link" in str(error).lower()


def test_rejects_wrong_project_identity(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    (fixture.root / "pyproject.toml").write_bytes(
        _project_configuration("another-project")
    )

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert PROJECT_NAME in str(error)


def test_rejects_non_table_project_metadata(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    (fixture.root / "pyproject.toml").write_bytes(b"project = []\n")

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert "project" in str(error).lower()


def test_rejects_missing_package_marker(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    (fixture.checkout_package / "__init__.py").unlink()

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert "package marker" in str(error).lower()


def test_rejects_checkout_below_git_top_level(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path, git_root=tmp_path)

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert "top level" in str(error).lower()


@pytest.mark.parametrize("missing_from", ("checkout", "package"))
def test_rejects_python_roster_drift(
    tmp_path: Path,
    missing_from: str,
) -> None:
    fixture = _build_fixture(tmp_path)
    owner = (
        fixture.checkout_package if missing_from == "checkout" else fixture.package_root
    )
    (owner / "reporting" / "owner.py").unlink()

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert "python" in str(error).lower()
    assert "roster" in str(error).lower()


def test_rejects_python_byte_drift(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    (fixture.checkout_package / "reporting" / "owner.py").write_bytes(b"VALUE = 2\n")

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert "python" in str(error).lower()
    assert "bytes" in str(error).lower()


@pytest.mark.parametrize("mutation", ("missing", "changed"))
def test_rejects_installed_resource_drift(
    tmp_path: Path,
    mutation: str,
) -> None:
    fixture = _build_fixture(tmp_path)
    resource = fixture.checkout_package / "runtime" / "data.bin"
    if mutation == "missing":
        resource.unlink()
    else:
        resource.write_bytes(b"changed package data\n")

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert "resource" in str(error).lower()


def test_git_probe_ignores_ambient_routing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_fixture(tmp_path)
    for variable in GIT_ROUTING_VARIABLES:
        monkeypatch.setenv(variable, str(tmp_path / "hostile" / variable))

    admitted = _admit(fixture)

    assert admitted.root == fixture.root


def test_git_probe_translates_output_decoding_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_fixture(tmp_path)

    def fail_decode(
        *_arguments: object,
        **_options: object,
    ) -> subprocess.CompletedProcess[str]:
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
        ops=source_authority.SourceAuthorityOps(run_git=fail_decode),
    )

    assert "git top level" in str(error).lower()


def test_git_probe_requests_only_the_checkout_top_level(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _build_fixture(tmp_path)
    calls: list[tuple[tuple[str, ...], Mapping[str, object]]] = []

    def observe_run(
        command: Sequence[str],
        **options: object,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((tuple(command), options))
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=f"{fixture.root}\n",
            stderr="",
        )

    admitted = source_authority.admit_source_checkout(
        root=fixture.root,
        package_root=fixture.package_root,
        ops=source_authority.SourceAuthorityOps(run_git=observe_run),
    )

    assert admitted.root == fixture.root
    assert len(calls) == 1
    command, options = calls[0]
    assert command == ("git", "rev-parse", "--show-toplevel")
    assert Path(str(options["cwd"])) == fixture.root
    environment = options["env"]
    assert isinstance(environment, dict)
    assert set(environment).isdisjoint(GIT_ROUTING_VARIABLES)
    assert "HEAD" not in command
    assert "--verify" not in command


def test_inspect_source_checkout_reports_sanitized_head_and_clean_state(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    commit = _commit_package(fixture)

    identity = source_authority.inspect_source_checkout(
        root=fixture.root,
        package_root=fixture.package_root,
    )

    assert identity == source_authority.SourceCheckoutIdentity(
        root=fixture.root,
        commit=commit,
        clean=True,
    )


def test_inspect_source_checkout_rejects_tracked_or_untracked_dirt(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    commit = _commit_package(fixture)
    (fixture.root / "untracked.txt").write_text("dirt\n", encoding="utf-8")

    with pytest.raises(source_authority.SourceCheckoutError, match="must be clean"):
        source_authority.inspect_source_checkout(
            root=fixture.root,
            package_root=fixture.package_root,
        )

    identity = source_authority.inspect_source_checkout(
        root=fixture.root,
        package_root=fixture.package_root,
        require_clean=False,
    )
    assert identity.commit == commit
    assert identity.clean is False


def test_inspect_source_checkout_uses_explicit_git_dependency(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    commit = _commit_package(fixture)
    calls: list[tuple[str, ...]] = []

    def run_git(
        command: Sequence[str],
        **options: object,
    ) -> subprocess.CompletedProcess[object]:
        calls.append(tuple(command))
        assert Path(str(options["cwd"])) == fixture.root
        environment = options["env"]
        assert isinstance(environment, dict)
        assert set(environment).isdisjoint(GIT_ROUTING_VARIABLES)
        return subprocess.run(command, **options)  # type: ignore[arg-type]

    identity = source_authority.inspect_source_checkout(
        root=fixture.root,
        package_root=fixture.package_root,
        ops=source_authority.SourceAuthorityOps(run_git=run_git),
    )

    assert identity.commit == commit
    assert identity.clean
    assert calls == [
        ("git", "rev-parse", "--show-toplevel"),
        ("git", "rev-parse", "--verify", "HEAD"),
        ("git", "rev-parse", "--show-object-format"),
        ("git", "ls-tree", "-r", "-z", commit, "--", "src/emrys"),
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
        ("git", "rev-parse", "--verify", "HEAD"),
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
    ]


def test_inspection_rejects_ignored_package_identity_outside_head(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    info_exclude = fixture.root / ".git" / "info" / "exclude"
    info_exclude.write_text(
        "src/emrys/reporting/ignored_owner.py\n",
        encoding="utf-8",
    )
    relative = Path("reporting/ignored_owner.py")
    _write_files(fixture.checkout_package, {str(relative): b"VALUE = 2\n"})
    _write_files(fixture.package_root, {str(relative): b"VALUE = 2\n"})

    with pytest.raises(
        source_authority.SourceCheckoutError,
        match="does not exactly match.*HEAD",
    ):
        source_authority.inspect_source_checkout(
            root=fixture.root,
            package_root=fixture.package_root,
        )


def test_child_attestation_rejects_unchanged_head_dirty_working_package(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    commit = _commit_package(fixture)
    relative = Path("reporting/owner.py")
    changed = b"VALUE = 2\n"
    _write_files(fixture.checkout_package, {str(relative): changed})
    _write_files(fixture.package_root, {str(relative): changed})

    with pytest.raises(
        source_authority.SourceCheckoutError,
        match="does not exactly match.*attempt commit",
    ):
        source_authority.attest_source_checkout(
            root=fixture.root,
            package_root=fixture.package_root,
            expected_commit=commit,
        )


def test_child_attestation_rejects_wrong_declared_commit(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)

    with pytest.raises(source_authority.SourceCheckoutError, match="differs"):
        source_authority.attest_source_checkout(
            root=fixture.root,
            package_root=fixture.package_root,
            expected_commit="f" * 40,
        )


def test_child_attestation_rejects_executing_package_byte_drift(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    commit = _commit_package(fixture)
    (fixture.package_root / "reporting" / "owner.py").write_bytes(b"VALUE = 3\n")

    with pytest.raises(source_authority.SourceCheckoutError, match="bytes differ"):
        source_authority.attest_source_checkout(
            root=fixture.root,
            package_root=fixture.package_root,
            expected_commit=commit,
        )


def test_child_attestation_detects_head_change_between_observations(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)
    commit = _commit_package(fixture)
    head_calls = 0

    def move_head(
        command: Sequence[str],
        **options: object,
    ) -> subprocess.CompletedProcess[object]:
        nonlocal head_calls
        if tuple(command) == ("git", "rev-parse", "--verify", "HEAD"):
            head_calls += 1
            if head_calls == 2:
                return subprocess.CompletedProcess(command, 0, "e" * 40 + "\n", "")
        return subprocess.run(command, **options)  # type: ignore[arg-type]

    with pytest.raises(source_authority.SourceCheckoutError, match="changed"):
        source_authority.attest_source_checkout(
            root=fixture.root,
            package_root=fixture.package_root,
            expected_commit=commit,
            ops=source_authority.SourceAuthorityOps(run_git=move_head),
        )
