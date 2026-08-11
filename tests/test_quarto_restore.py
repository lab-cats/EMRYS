"""Focused tests for the checksum-pinned repository-local Quarto restore."""

from __future__ import annotations

import hashlib
import io
import json
import stat
import sys
import tarfile
from pathlib import Path

import pytest
from scripts import restore_quarto as RESTORE

REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_bytes(
    bundle: tarfile.TarFile,
    name: str,
    payload: bytes,
    *,
    mode: int = 0o644,
) -> None:
    member = tarfile.TarInfo(name)
    member.size = len(payload)
    member.mode = mode
    bundle.addfile(member, io.BytesIO(payload))


def build_archive(
    path: Path,
    *,
    version: str = RESTORE.QUARTO_VERSION,
    unsafe_member: tarfile.TarInfo | None = None,
) -> Path:
    executable = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'if [[ "${1:-}" == "--version" ]]; then\n'
        f"  printf '%s\\n' '{version}'\n"
        "  exit 0\n"
        "fi\n"
        "exit 2\n"
    ).encode()
    with tarfile.open(path, "w:gz") as bundle:
        add_bytes(bundle, "./bin/quarto", executable, mode=0o755)
        add_bytes(
            bundle,
            "./share/formats/typst/fonts/Font Awesome 6 Free-Solid-900.otf",
            b"synthetic-font",
        )
        add_bytes(
            bundle,
            "./share/extension-subtrees/julia-engine/AGENTS.md",
            b"synthetic-agent-instructions\n",
        )
        link = tarfile.TarInfo("./share/extension-subtrees/julia-engine/CLAUDE.md")
        link.type = tarfile.SYMTYPE
        link.linkname = "AGENTS.md"
        bundle.addfile(link)
        if unsafe_member is not None:
            if unsafe_member.size:
                bundle.addfile(
                    unsafe_member,
                    io.BytesIO(b"x" * unsafe_member.size),
                )
            else:
                bundle.addfile(unsafe_member)
    return path


def restore_fixture(archive: Path, install_root: Path) -> Path:
    return RESTORE.restore_from_archive(
        archive=archive,
        install_root=install_root,
        expected_sha256=sha256_file(archive),
    )


def assert_no_restore_residue(install_root: Path) -> None:
    if not install_root.exists():
        return
    assert not any(
        child.name.startswith(".restore-") for child in install_root.iterdir()
    )


def test_pinned_public_contract_matches_makefile_and_hardened_download(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    makefile = (REPO_ROOT / "scripts" / "make_reporting.mk").read_text(encoding="utf-8")
    assert RESTORE.QUARTO_VERSION == "1.9.38"
    assert RESTORE.QUARTO_SHA256 == (
        "47089a5020cfb41981ba0d4b46e110edfa608722aea45ef248e14efba6d6b18a"
    )
    assert RESTORE.QUARTO_URL.startswith("https://github.com/")
    assert f"QUARTO_VERSION := {RESTORE.QUARTO_VERSION}" in makefile
    assert f"QUARTO_SHA256 := {RESTORE.QUARTO_SHA256}" in makefile
    assert "quarto-restore:" in makefile

    observed: list[list[str]] = []

    def run_curl(arguments: list[str], **_kwargs: object):
        observed.append(arguments)
        return RESTORE.subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(RESTORE.shutil, "which", lambda _name: "/usr/bin/curl")
    monkeypatch.setattr(RESTORE.subprocess, "run", run_curl)
    destination = tmp_path / "quarto.tar.gz"
    RESTORE._download_archive(destination)

    assert len(observed) == 1
    arguments = observed[0]
    assert arguments[0] == "/usr/bin/curl"
    assert arguments[-2:] == [str(destination), RESTORE.QUARTO_URL]
    for hardening_flag in (
        "--disable",
        "--proto",
        "=https",
        "--tlsv1.2",
        "--proto-redir",
        "--connect-timeout",
        "--max-time",
        "--max-filesize",
    ):
        assert hardening_flag in arguments
    assert "--expected-sha256" not in arguments


def test_restore_accepts_official_shape_spaces_and_contained_symlink(
    tmp_path: Path,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "tools" / "quarto"

    executable = restore_fixture(archive, install_root)
    target = install_root / RESTORE.QUARTO_VERSION
    target_inode = target.stat().st_ino

    assert executable == target / "bin" / "quarto"
    assert executable.is_file()
    assert executable.stat().st_mode & stat.S_IXUSR
    receipt = target / RESTORE.INSTALL_RECEIPT_NAME
    receipt_document = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_document == {
        "archive_sha256": sha256_file(archive),
        "archive_url": RESTORE.QUARTO_URL,
        "producer": "restore_quarto",
        "quarto_version": RESTORE.QUARTO_VERSION,
        "schema_version": RESTORE.INSTALL_RECEIPT_SCHEMA_VERSION,
        "tree_sha256": RESTORE._tree_sha256(target),
    }
    assert (
        target
        / "share"
        / "formats"
        / "typst"
        / "fonts"
        / "Font Awesome 6 Free-Solid-900.otf"
    ).is_file()
    link = target / "share" / "extension-subtrees" / "julia-engine" / "CLAUDE.md"
    assert link.is_symlink()
    assert link.readlink() == Path("AGENTS.md")
    assert_no_restore_residue(install_root)

    second = restore_fixture(archive, install_root)
    assert second == executable
    assert target.stat().st_ino == target_inode
    assert_no_restore_residue(install_root)


def test_same_version_tree_without_verified_receipt_is_rejected(
    tmp_path: Path,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "quarto"
    target = install_root / RESTORE.QUARTO_VERSION
    (target / "bin").mkdir(parents=True)
    fake = f"#!/usr/bin/env bash\nprintf '%s\\n' '{RESTORE.QUARTO_VERSION}'\n"
    executable = target / "bin" / "quarto"
    executable.write_text(fake, encoding="utf-8")
    executable.chmod(0o755)

    with pytest.raises(
        RESTORE.QuartoRestoreError,
        match="install receipt",
    ):
        restore_fixture(archive, install_root)

    assert executable.read_text(encoding="utf-8") == fake
    assert_no_restore_residue(install_root)


def test_mutated_verified_installation_is_rejected_on_reuse(
    tmp_path: Path,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "quarto"
    executable = restore_fixture(archive, install_root)
    executable.write_text(
        executable.read_text(encoding="utf-8") + "# mutation\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RESTORE.QuartoRestoreError,
        match="does not match the verified restore contract",
    ):
        restore_fixture(archive, install_root)

    assert executable.read_text(encoding="utf-8").endswith("# mutation\n")
    assert_no_restore_residue(install_root)


def test_restore_extracts_only_the_owned_bound_archive_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    expected_sha256 = sha256_file(archive)
    install_root = tmp_path / "quarto"
    original_extract = RESTORE._extract_archive
    observed_extract_paths: list[Path] = []

    def mutate_source_then_extract(bound_archive: Path, destination: Path) -> None:
        observed_extract_paths.append(bound_archive)
        archive.write_bytes(b"replaced source path after the owned copy")
        original_extract(bound_archive, destination)

    monkeypatch.setattr(RESTORE, "_extract_archive", mutate_source_then_extract)
    executable = RESTORE.restore_from_archive(
        archive=archive,
        install_root=install_root,
        expected_sha256=expected_sha256,
    )

    assert executable.is_file()
    assert observed_extract_paths
    assert observed_extract_paths[0] != archive
    assert observed_extract_paths[0].parent.name.startswith(".restore-")
    assert_no_restore_residue(install_root)


def test_safe_tar_filter_failure_never_retries_unfiltered(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "quarto"
    calls = 0

    def unsupported_filter(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        raise TypeError("synthetic filter incompatibility")

    monkeypatch.setattr(tarfile.TarFile, "extractall", unsupported_filter)
    with pytest.raises(
        RESTORE.QuartoRestoreError,
        match="refusing an unfiltered Quarto restore",
    ):
        restore_fixture(archive, install_root)

    assert calls == 1
    assert not (install_root / RESTORE.QUARTO_VERSION).exists()
    assert_no_restore_residue(install_root)


def test_quarto_version_checks_ignore_hostile_shell_and_tool_overrides(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "quarto"
    sentinel = tmp_path / "hostile-shell-environment-ran"
    bash_environment = tmp_path / "hostile-bash-env.sh"
    bash_environment.write_text(
        f"#!/bin/sh\nprintf unsafe > {sentinel}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("BASH_ENV", str(bash_environment))
    monkeypatch.setenv("ENV", str(bash_environment))
    monkeypatch.setenv("QUARTO_DENO", "/tmp/undeclared-deno")
    monkeypatch.setenv("QUARTO_PANDOC", "/tmp/undeclared-pandoc")
    monkeypatch.setenv("QUARTO_PROFILE", "undeclared-profile")

    executable = restore_fixture(archive, install_root)

    assert executable.is_file()
    assert not sentinel.exists()
    assert_no_restore_residue(install_root)


def test_wrong_hash_fails_closed_and_cleans_owned_paths(tmp_path: Path) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "tools" / "quarto"

    with pytest.raises(RESTORE.QuartoRestoreError, match="SHA-256 mismatch"):
        RESTORE.restore_from_archive(
            archive=archive,
            install_root=install_root,
            expected_sha256="0" * 64,
        )

    assert not (install_root / RESTORE.QUARTO_VERSION).exists()
    assert_no_restore_residue(install_root)


@pytest.mark.parametrize(
    ("member", "message"),
    [
        (tarfile.TarInfo("../escape"), "unsafe member path"),
        (tarfile.TarInfo("/absolute"), "unsafe member path"),
        (tarfile.TarInfo("bad\nname"), "control byte"),
    ],
)
def test_unsafe_archive_member_paths_are_rejected(
    tmp_path: Path,
    member: tarfile.TarInfo,
    message: str,
) -> None:
    member.size = 1
    archive = build_archive(
        tmp_path / "unsafe.tar.gz",
        unsafe_member=member,
    )
    install_root = tmp_path / "quarto"

    with pytest.raises(RESTORE.QuartoRestoreError, match=message):
        restore_fixture(archive, install_root)

    assert not (install_root / RESTORE.QUARTO_VERSION).exists()
    assert_no_restore_residue(install_root)


def test_escaping_archive_symlink_is_rejected(tmp_path: Path) -> None:
    link = tarfile.TarInfo("./share/escape")
    link.type = tarfile.SYMTYPE
    link.linkname = "../../outside"
    archive = build_archive(
        tmp_path / "unsafe-link.tar.gz",
        unsafe_member=link,
    )
    install_root = tmp_path / "quarto"

    with pytest.raises(RESTORE.QuartoRestoreError, match="escapes extraction"):
        restore_fixture(archive, install_root)

    assert not (install_root / RESTORE.QUARTO_VERSION).exists()
    assert_no_restore_residue(install_root)


def test_wrong_executable_version_rolls_back_first_install(
    tmp_path: Path,
) -> None:
    archive = build_archive(tmp_path / "wrong-version.tar.gz", version="1.9.37")
    install_root = tmp_path / "quarto"

    with pytest.raises(RESTORE.QuartoRestoreError, match="expected exactly"):
        restore_fixture(archive, install_root)

    assert not (install_root / RESTORE.QUARTO_VERSION).exists()
    assert_no_restore_residue(install_root)


def test_invalid_existing_target_and_foreign_lock_are_preserved(
    tmp_path: Path,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "quarto"
    install_root.mkdir()
    target = install_root / RESTORE.QUARTO_VERSION
    target.write_text("foreign-invalid-target\n", encoding="utf-8")

    with pytest.raises(
        RESTORE.QuartoRestoreError,
        match="non-symlink directory",
    ):
        restore_fixture(archive, install_root)
    assert target.read_text(encoding="utf-8") == "foreign-invalid-target\n"

    target.unlink()
    lock = install_root / f".restore-{RESTORE.QUARTO_VERSION}.lock"
    lock.write_text("foreign-lock\n", encoding="utf-8")
    with pytest.raises(RESTORE.QuartoRestoreError, match="lock already exists"):
        restore_fixture(archive, install_root)
    assert lock.read_text(encoding="utf-8") == "foreign-lock\n"
    assert not target.exists()


def test_post_publish_validation_failure_removes_only_new_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = build_archive(tmp_path / "quarto.tar.gz")
    install_root = tmp_path / "quarto"
    original = RESTORE.validate_installation

    def fail_after_publish(
        target: Path,
        *,
        expected_sha256: str = RESTORE.QUARTO_SHA256,
    ) -> Path:
        if target.exists():
            raise RESTORE.QuartoRestoreError("synthetic post-publish failure")
        return original(target, expected_sha256=expected_sha256)

    monkeypatch.setattr(RESTORE, "validate_installation", fail_after_publish)
    with pytest.raises(
        RESTORE.QuartoRestoreError,
        match="synthetic post-publish failure",
    ):
        restore_fixture(archive, install_root)

    assert not (install_root / RESTORE.QUARTO_VERSION).exists()
    assert_no_restore_residue(install_root)
