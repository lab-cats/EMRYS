"""Direct contracts for deterministic installed-package tree identity."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from norad.libraries.installed_package_identity import (
    InstalledPackageIdentityError,
    installed_package_tree_identity,
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
