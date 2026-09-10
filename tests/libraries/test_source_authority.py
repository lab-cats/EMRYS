"""Installed-code admission and independent artifact-root boundaries."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from emrys.libraries import source_authority


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

    with pytest.raises(source_authority.InstalledPackageError, match="pycache_prefix"):
        source_authority.require_controlled_python_runtime()


def test_console_entry_restarts_with_the_controlled_python_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[str, tuple[str, ...]]] = []

    def stop_after_exec(executable: str, arguments: tuple[str, ...]) -> None:
        observed.append((executable, arguments))
        raise RuntimeError("exec observed")

    monkeypatch.setattr(source_authority.os, "execv", stop_after_exec)
    monkeypatch.setattr(source_authority.sys, "argv", ["emrys", "run", "--execute"])

    with pytest.raises(RuntimeError, match="exec observed"):
        source_authority.controlled_console_main()

    assert observed == [
        (
            sys.executable,
            source_authority.controlled_python_argv(
                sys.executable, "-m", "emrys", "run", "--execute"
            ),
        )
    ]


def test_installed_identity_binds_code_and_build_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "emrys"
    package.mkdir()
    module = package / "__init__.py"
    module.write_text("VALUE = 1\n")
    monkeypatch.setattr(source_authority, "PACKAGE_ROOT", package)
    first = source_authority.admit_installed_package(root=package)
    module.write_text("VALUE = 2\n")
    changed = source_authority.admit_installed_package(root=package)
    assert changed.content_sha256 != first.content_sha256
    assert changed.version == first.version
    assert changed.python_lock_sha256 == first.python_lock_sha256
    module.unlink()
    module.symlink_to(tmp_path / "external.py")
    with pytest.raises(source_authority.InstalledPackageError, match="symbolic link"):
        source_authority.admit_installed_package(root=package)


def test_installed_admission_rejects_different_root_and_missing_build_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(
        source_authority.InstalledPackageError, match="executing package"
    ):
        source_authority.admit_installed_package(root=tmp_path)
    distribution = source_authority.importlib.metadata.distribution(
        source_authority.PROJECT_NAME
    )
    monkeypatch.setattr(distribution, "read_text", lambda _name: None)
    monkeypatch.setattr(
        source_authority.importlib.metadata, "distribution", lambda _name: distribution
    )
    with pytest.raises(
        source_authority.InstalledPackageError, match="build provenance"
    ):
        source_authority.admit_installed_package()
