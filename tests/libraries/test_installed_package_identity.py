"""Direct contracts for deterministic installed-package tree identity."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

import pytest

import emrys.libraries.installed_package_identity as package_identity
from emrys.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    admit_installed_provider,
    installed_package_tree_identity,
    installed_python_package_identity,
)


def _package(root: Path, *, reverse: bool = False) -> Path:
    root.mkdir()
    directories = [root / "R", root / "libs", root / "data"]
    for directory in reversed(directories) if reverse else directories:
        directory.mkdir()
    files = [
        (root / "DESCRIPTION", b"Package: Fixture\nVersion: 1.0.0\n"),
        (root / "R" / "Fixture.rdb", b"database-bytes\n"),
        (root / "R" / "Fixture.rdx", b"index-bytes\n"),
        (root / "libs" / "Fixture.so", b"shared-object-bytes\n"),
    ]
    for path, data in reversed(files) if reverse else files:
        path.write_bytes(data)
    return root


def _mutate_after_directory_scan(
    monkeypatch: pytest.MonkeyPatch,
    *,
    target: Path,
    mutation: Callable[[], None],
) -> None:
    real_scandir = package_identity.os.scandir

    @contextmanager
    def scan_then_mutate(directory: Path):
        with real_scandir(directory) as scanned:
            entries = list(scanned)
        if directory == target:
            mutation()
        yield iter(entries)

    monkeypatch.setattr(package_identity.os, "scandir", scan_then_mutate)


def test_tree_identity_is_order_stable_and_ignores_timestamps(tmp_path: Path) -> None:
    first = _package(tmp_path / "first")
    second = _package(tmp_path / "second", reverse=True)
    for index, path in enumerate([second, *second.rglob("*")], start=1):
        os.utime(path, ns=(index * 1_000_000_000, index * 1_000_000_000))

    first_identity = installed_package_tree_identity(first)
    second_identity = installed_package_tree_identity(second)

    assert first_identity.root == first
    assert second_identity.root == second
    assert first_identity.sha256 == second_identity.sha256


def test_python_package_identity_ignores_interpreter_cache(tmp_path: Path) -> None:
    package = _package(tmp_path / "package")
    before = installed_python_package_identity(package).sha256
    cache = package / "__pycache__"
    cache.mkdir()
    (cache / "module.cpython-314.pyc").write_bytes(b"interpreter-cache")

    assert installed_python_package_identity(package).sha256 == before


def test_python_package_identity_binds_sourceless_bytecode(tmp_path: Path) -> None:
    package = _package(tmp_path / "package")
    module = package / "module.pyc"
    module.write_bytes(b"first-bytecode")
    before = installed_python_package_identity(package).sha256

    module.write_bytes(b"second-bytecode")

    assert installed_python_package_identity(package).sha256 != before


def test_provider_admission_rejects_missing_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(package_identity.importlib.metadata, "entry_points", lambda **_: ())

    with pytest.raises(InstalledPackageIdentityError, match="not installed"):
        admit_installed_provider("emrys.analysis_modules", "missing", label="Module")


@pytest.mark.parametrize(
    "mutation",
    ["add_database", "remove_database", "mutate_database", "mutate_shared_object"],
)
def test_tree_identity_changes_for_package_roster_and_byte_mutations(
    tmp_path: Path,
    mutation: str,
) -> None:
    package = _package(tmp_path / "package")
    before = installed_package_tree_identity(package).sha256

    if mutation == "add_database":
        (package / "R" / "Added.rdb").write_bytes(b"added-database\n")
    elif mutation == "remove_database":
        (package / "R" / "Fixture.rdb").unlink()
    elif mutation == "mutate_database":
        (package / "R" / "Fixture.rdb").write_bytes(b"DATABASE-BYTES\n")
    else:
        (package / "libs" / "Fixture.so").write_bytes(b"SHARED-OBJECT-BYTES\n")

    assert installed_package_tree_identity(package).sha256 != before


def test_tree_identity_includes_normalized_permission_mode(tmp_path: Path) -> None:
    package = _package(tmp_path / "package")
    library = package / "libs" / "Fixture.so"
    library.chmod(0o644)
    before = installed_package_tree_identity(package).sha256

    library.chmod(0o600)

    assert installed_package_tree_identity(package).sha256 != before


@pytest.mark.parametrize("entry_kind", ["symlink", "fifo"])
def test_tree_identity_rejects_symlinks_and_special_entries(
    tmp_path: Path,
    entry_kind: str,
) -> None:
    package = _package(tmp_path / "package")
    entry = package / "foreign"
    if entry_kind == "symlink":
        entry.symlink_to(package / "DESCRIPTION")
        expected = "symbolic link"
    else:
        os.mkfifo(entry)
        expected = "special entry"

    with pytest.raises(InstalledPackageIdentityError, match=expected):
        installed_package_tree_identity(package)


def test_tree_identity_rejects_noncanonical_package_root(tmp_path: Path) -> None:
    package = _package(tmp_path / "package")
    linked = tmp_path / "linked"
    linked.symlink_to(package, target_is_directory=True)

    with pytest.raises(InstalledPackageIdentityError, match="canonical real directory"):
        installed_package_tree_identity(linked)


def test_tree_identity_rejects_relative_package_root() -> None:
    with pytest.raises(InstalledPackageIdentityError, match="root must be absolute"):
        installed_package_tree_identity(Path("relative-package"))


def test_tree_identity_rejects_lexically_noncanonical_absolute_root(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path / "package")
    detour = tmp_path / "detour"
    detour.mkdir()
    noncanonical = detour / ".." / package.name

    with pytest.raises(InstalledPackageIdentityError, match="canonical real directory"):
        installed_package_tree_identity(noncanonical)


def test_tree_identity_reports_an_unavailable_package_root(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(
        InstalledPackageIdentityError,
        match="Could not inspect installed package root",
    ) as caught:
        installed_package_tree_identity(missing)

    assert isinstance(caught.value.__cause__, FileNotFoundError)


def test_tree_identity_requires_no_follow_file_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    monkeypatch.delattr(package_identity.os, "O_NOFOLLOW")

    with pytest.raises(
        InstalledPackageIdentityError,
        match="lacks required no-follow package-tree admission",
    ):
        installed_package_tree_identity(package)


def test_tree_identity_rejects_file_replaced_by_directory_before_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "DESCRIPTION"
    real_open = package_identity.os.open

    def replace_before_open(path: Path, flags: int) -> int:
        if path == target:
            target.unlink()
            target.mkdir()
        return real_open(path, flags)

    monkeypatch.setattr(package_identity.os, "open", replace_before_open)

    with pytest.raises(
        InstalledPackageIdentityError,
        match="entry is not a regular file",
    ):
        installed_package_tree_identity(package)


@pytest.mark.parametrize("failure_point", ["open", "read"])
def test_tree_identity_wraps_file_read_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "DESCRIPTION"

    if failure_point == "open":
        real_open = package_identity.os.open

        def deny_open(path: Path, flags: int) -> int:
            if path == target:
                raise PermissionError("synthetic open denial")
            return real_open(path, flags)

        monkeypatch.setattr(package_identity.os, "open", deny_open)
    else:

        def deny_read(descriptor: int, count: int) -> bytes:
            raise OSError("synthetic read failure")

        monkeypatch.setattr(package_identity.os, "read", deny_read)

    with pytest.raises(
        InstalledPackageIdentityError,
        match="Could not read installed package file",
    ) as caught:
        installed_package_tree_identity(package)

    assert isinstance(caught.value.__cause__, OSError)


def test_tree_identity_rejects_file_removed_before_read_re_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "DESCRIPTION"
    real_read = package_identity.os.read
    removed = False

    def read_then_remove(descriptor: int, count: int) -> bytes:
        nonlocal removed
        data = real_read(descriptor, count)
        if data and not removed:
            target.unlink()
            removed = True
        return data

    monkeypatch.setattr(package_identity.os, "read", read_then_remove)

    with pytest.raises(
        InstalledPackageIdentityError,
        match="Could not re-admit installed package file",
    ):
        installed_package_tree_identity(package)


def test_tree_identity_rejects_file_mutated_while_reading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "DESCRIPTION"
    real_read = package_identity.os.read
    mutated = False

    def read_then_mutate(descriptor: int, count: int) -> bytes:
        nonlocal mutated
        data = real_read(descriptor, count)
        if data and not mutated:
            target.write_bytes(b"Package: Mutated\nVersion: 100.0.0\n")
            mutated = True
        return data

    monkeypatch.setattr(package_identity.os, "read", read_then_mutate)

    with pytest.raises(
        InstalledPackageIdentityError,
        match="file changed while it was read",
    ):
        installed_package_tree_identity(package)


def test_tree_identity_wraps_directory_scan_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "data"
    real_scandir = package_identity.os.scandir

    def deny_scan(directory: Path):
        if directory == target:
            raise PermissionError("synthetic scan denial")
        return real_scandir(directory)

    monkeypatch.setattr(package_identity.os, "scandir", deny_scan)

    with pytest.raises(
        InstalledPackageIdentityError,
        match="Could not inspect installed package directory",
    ) as caught:
        installed_package_tree_identity(package)

    assert isinstance(caught.value.__cause__, PermissionError)


def test_tree_identity_rejects_entry_removed_after_directory_scan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "DESCRIPTION"
    _mutate_after_directory_scan(
        monkeypatch,
        target=package,
        mutation=target.unlink,
    )

    with pytest.raises(
        InstalledPackageIdentityError,
        match="Could not inspect installed package entry",
    ):
        installed_package_tree_identity(package)


def test_tree_identity_rejects_directory_removed_before_re_admission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "data"
    _mutate_after_directory_scan(
        monkeypatch,
        target=target,
        mutation=target.rmdir,
    )

    with pytest.raises(
        InstalledPackageIdentityError,
        match="Could not re-admit installed package directory",
    ):
        installed_package_tree_identity(package)


def test_tree_identity_rejects_directory_mutated_while_scanning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = _package(tmp_path / "package")
    target = package / "data"
    target.chmod(0o755)
    _mutate_after_directory_scan(
        monkeypatch,
        target=target,
        mutation=lambda: target.chmod(0o700),
    )

    with pytest.raises(
        InstalledPackageIdentityError,
        match="directory changed while it was read",
    ):
        installed_package_tree_identity(package)
