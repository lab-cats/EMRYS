"""Independent checkout-authority tests for artifact indexing."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

from norad.reporting import build_artifact_index as artifact_index_facade
from norad.reporting._artifact_index import (  # ruff: ignore[import-private-name]
    source_checkout,
)

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
    "reporting/styles/example.css": b"body { color: black; }\n",
    "reporting/templates/example.qmd": b"# Synthetic report\n",
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
        '"norad.contracts" = ["schemas/artifacts/v1/*.json"]\n'
        '"norad.reporting" = ["styles/*.css", "templates/*.qmd"]\n'
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


def test_cli_parse_termination_precedes_checkout_admission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def terminate_parse() -> argparse.Namespace:
        raise SystemExit(2)

    def unexpected_admission(
        *,
        root: Path,
        package_root: Path,
    ) -> source_checkout.SourceCheckout:
        pytest.fail(f"admission reached for {root} and {package_root}")

    monkeypatch.setattr(artifact_index_facade, "parse_args", terminate_parse)
    monkeypatch.setattr(
        artifact_index_facade,
        "admit_source_checkout",
        unexpected_admission,
    )

    with pytest.raises(SystemExit) as caught:
        artifact_index_facade.main()

    assert caught.value.code == CLI_USAGE_ERROR


def test_cli_admission_failure_precedes_context_construction(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = argparse.Namespace(execute=False)
    prepare_context_called = False

    def parsed_arguments() -> argparse.Namespace:
        return arguments

    def reject_checkout(
        *,
        root: Path,
        package_root: Path,
    ) -> source_checkout.SourceCheckout:
        assert root.is_absolute()
        assert package_root.is_absolute()
        raise source_checkout.SourceCheckoutError("injected checkout rejection")

    def unexpected_prepare_context(_arguments: argparse.Namespace) -> None:
        nonlocal prepare_context_called
        prepare_context_called = True

    monkeypatch.setattr(artifact_index_facade, "parse_args", parsed_arguments)
    monkeypatch.setattr(
        artifact_index_facade,
        "admit_source_checkout",
        reject_checkout,
    )
    monkeypatch.setattr(
        artifact_index_facade,
        "prepare_context",
        unexpected_prepare_context,
    )

    assert artifact_index_facade.main() == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert captured.err == "ERROR: injected checkout rejection\n"
    assert not prepare_context_called
