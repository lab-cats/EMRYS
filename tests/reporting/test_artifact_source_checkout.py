"""Independent checkout-authority tests for artifact indexing."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import norad
import pytest

from norad import __main__ as norad_cli
from norad.reporting._artifact_index import builder as artifact_index_builder
from norad.reporting._artifact_index import source_checkout

if TYPE_CHECKING:
    import argparse

PROJECT_NAME = "norad-rna-workflow"
CLI_USAGE_ERROR = 2
PYTHON_FILES: Mapping[str, bytes] = {
    "__init__.py": b'"""Synthetic NORAD package."""\n',
    "contracts/__init__.py": b'"""Synthetic contracts package."""\n',
    "reporting/__init__.py": b'"""Synthetic reporting package."""\n',
    "reporting/owner.py": b"VALUE = 1\n",
}
RESOURCE_FILES: Mapping[str, bytes] = {
    "contracts/schemas/artifacts/v1/example.json": b'{"schema": true}\n',
    "contracts/schemas/artifacts/v2/report_receipt.schema.json": b'{"schema": true}\n',
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
        ["git", "add", "pyproject.toml", "src/norad"],
        cwd=fixture.root,
        text=True,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=NORAD Fixture",
            "-c",
            "user.email=norad-fixture@example.invalid",
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
        'include = ["norad*"]\n'
        "namespaces = false\n"
        "\n"
        "[tool.setuptools.package-data]\n"
        '"norad.contracts" = ["schemas/artifacts/v1/*.json", "schemas/artifacts/v2/*.json"]\n'
        '"norad.reporting" = ["styles/*.css", "templates/*.html.j2"]\n'
    ).encode()


def _build_fixture(
    tmp_path: Path,
    *,
    git_root: Path | None = None,
) -> CheckoutFixture:
    root = tmp_path / "checkout"
    checkout_package = root / "src" / "norad"
    package_root = tmp_path / "active-package" / "norad"
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


def _admit(fixture: CheckoutFixture) -> source_checkout.SourceCheckout:
    return source_checkout.admit_source_checkout(
        root=fixture.root,
        package_root=fixture.package_root,
    )


def _artifact_index_arguments(source_root: Path) -> list[str]:
    return [
        "build",
        "artifact-index",
        "--source-checkout",
        str(source_root),
        "--run-id",
        "synthetic-run",
        "--run-contract",
        str(source_root / "run-contract.json"),
        "--inventory",
        str(source_root / "inventory.tsv"),
        "--output-root",
        str(source_root / "output"),
    ]


def _assert_rejected(
    *,
    root: Path,
    package_root: Path,
) -> source_checkout.SourceCheckoutError:
    with pytest.raises(source_checkout.SourceCheckoutError) as caught:
        source_checkout.admit_source_checkout(
            root=root,
            package_root=package_root,
        )
    return caught.value


def test_admits_canonical_checkout_with_identical_package(
    tmp_path: Path,
) -> None:
    fixture = _build_fixture(tmp_path)

    admitted = _admit(fixture)

    assert isinstance(admitted, source_checkout.SourceCheckout)
    assert admitted.root == fixture.root


def test_package_identity_matches_clean_checkout_head(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    admitted = _admit(fixture)

    assert source_checkout.package_matches_checkout_head(
        source_checkout=admitted,
        package_root=fixture.package_root,
    )


def test_package_identity_rejects_dirty_tracked_checkout_bytes(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    _commit_package(fixture)
    changed = b"VALUE = 2\n"
    (fixture.checkout_package / "reporting" / "owner.py").write_bytes(changed)
    (fixture.package_root / "reporting" / "owner.py").write_bytes(changed)
    admitted = _admit(fixture)

    assert not source_checkout.package_matches_checkout_head(
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

    assert not source_checkout.package_matches_checkout_head(
        source_checkout=admitted,
        package_root=fixture.package_root,
    )


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

    monkeypatch.setattr(source_checkout.subprocess, "run", fail_decode)

    error = _assert_rejected(
        root=fixture.root,
        package_root=fixture.package_root,
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

    monkeypatch.setattr(source_checkout.subprocess, "run", observe_run)

    admitted = _admit(fixture)

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


def test_grouped_help_precedes_artifact_builder_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        norad_cli,
        "_build_artifact_index_from_args",
        lambda _arguments: pytest.fail("artifact-index builder was dispatched"),
    )

    with pytest.raises(SystemExit) as caught:
        norad_cli.main(["build", "artifact-index", "--help"])

    assert caught.value.code == 0


def test_grouped_cli_threads_explicit_checkout_into_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admitted = source_checkout.SourceCheckout(root=tmp_path)
    context = {"context": "synthetic"}
    events: list[str] = []
    expected_package_root = Path(norad.__file__).resolve().parent

    def admit_checkout(
        *,
        root: Path,
        package_root: Path,
    ) -> source_checkout.SourceCheckout:
        assert root == tmp_path
        assert package_root == expected_package_root
        assert root.is_absolute()
        assert package_root.is_absolute()
        events.append("admit")
        return admitted

    def prepare_context(
        observed_arguments: argparse.Namespace,
        *,
        source_checkout: source_checkout.SourceCheckout,
    ) -> object:
        assert observed_arguments.source_checkout == tmp_path
        assert observed_arguments.run_id == "synthetic-run"
        assert observed_arguments.execute is False
        assert source_checkout == admitted
        events.append("prepare")
        return context

    def print_context(observed_context: object, execute: object) -> None:
        assert observed_context == context
        assert execute is False
        events.append("print")

    monkeypatch.setattr(
        artifact_index_builder,
        "admit_source_checkout",
        admit_checkout,
    )
    monkeypatch.setattr(
        artifact_index_builder,
        "prepare_context",
        prepare_context,
    )
    monkeypatch.setattr(artifact_index_builder, "print_context", print_context)

    assert norad_cli.main(_artifact_index_arguments(tmp_path)) == 0
    assert events == ["admit", "prepare", "print"]


def test_grouped_cli_requires_explicit_source_checkout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        norad_cli,
        "_build_artifact_index_from_args",
        lambda _arguments: pytest.fail("artifact-index builder was dispatched"),
    )
    arguments = [
        "build",
        "artifact-index",
        "--run-id",
        "synthetic-run",
        "--run-contract",
        str(tmp_path / "run-contract.json"),
        "--inventory",
        str(tmp_path / "inventory.tsv"),
        "--output-root",
        str(tmp_path / "output"),
    ]

    with pytest.raises(SystemExit) as caught:
        norad_cli.main(arguments)

    assert caught.value.code == CLI_USAGE_ERROR
    captured = capsys.readouterr()
    assert not captured.out
    assert "--source-checkout" in captured.err


def test_builder_admission_failure_precedes_context_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prepare_context_called = False
    expected_package_root = Path(artifact_index_builder.__file__).resolve().parents[2]

    def reject_checkout(
        *,
        root: Path,
        package_root: Path,
    ) -> source_checkout.SourceCheckout:
        assert root == tmp_path
        assert package_root == expected_package_root
        raise source_checkout.SourceCheckoutError("injected checkout rejection")

    def unexpected_prepare_context(
        _arguments: argparse.Namespace,
        *,
        source_checkout: source_checkout.SourceCheckout,
    ) -> None:
        nonlocal prepare_context_called
        prepare_context_called = True
        pytest.fail(f"context constructed from {source_checkout.root}")

    monkeypatch.setattr(
        artifact_index_builder,
        "admit_source_checkout",
        reject_checkout,
    )
    monkeypatch.setattr(
        artifact_index_builder,
        "prepare_context",
        unexpected_prepare_context,
    )

    assert norad_cli.main(_artifact_index_arguments(tmp_path)) == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert captured.err == "ERROR: injected checkout rejection\n"
    assert not prepare_context_called
