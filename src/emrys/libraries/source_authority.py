"""Fail-closed filesystem authorities shared by EMRYS functional owners.

``SourceCheckout`` binds executing package and producer identity to one Git
checkout. ``ArtifactSourceRoot`` independently binds the root used to resolve
contract-relative scientific artifacts. Keeping these values distinct avoids
making an operator's run workspace a child of the source checkout.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import sys
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_NAME = "emrys-rna-workflow"
CONTROLLED_PYTHON_CACHE_PREFIX = "/dev/null"
CONTROLLED_PYTHON_OPTIONS = (
    "-X",
    f"pycache_prefix={CONTROLLED_PYTHON_CACHE_PREFIX}",
    "-I",
)
_RESOURCE_PATTERNS = (
    (Path("contracts"), "schemas/artifacts/v1/*.json"),
    (Path("contracts"), "schemas/artifacts/v2/*.json"),
    (Path("contracts"), "schemas/artifacts/v3/*.json"),
    (Path("contracts"), "schemas/artifacts/v4/*.json"),
    (Path("contracts"), "schemas/orchestration/v1/*.json"),
    (Path("contracts"), "schemas/orchestration/v2/*.json"),
    (Path("contracts"), "schemas/orchestration/v3/*.json"),
    (Path("orchestration/local_pilot"), "resources/*.yaml"),
    (Path("resources"), "runtime/*"),
    (Path("reporting"), "styles/*.css"),
    (Path("reporting"), "templates/*.html.j2"),
)


@dataclass(frozen=True, slots=True)
class SourceCheckout:
    """One canonical Git checkout matching the executing EMRYS package."""

    root: Path


@dataclass(frozen=True, slots=True)
class ArtifactSourceRoot:
    """One canonical directory resolving contract-relative artifact paths."""

    root: Path


class SourceCheckoutError(RuntimeError):
    """The claimed checkout cannot own the executing package identity."""


class ArtifactSourceRootError(RuntimeError):
    """The claimed artifact source root is not an admissible directory."""


@dataclass(frozen=True, slots=True)
class SourceAuthorityOps:
    """Explicit process dependency for source-authority Git observations."""

    run_git: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run


DEFAULT_SOURCE_AUTHORITY_OPS = SourceAuthorityOps()


@dataclass(frozen=True, slots=True)
class SourceCheckoutIdentity:
    """Admitted checkout identity observed from sanitized Git state."""

    root: Path
    commit: str
    clean: bool


@dataclass(frozen=True, slots=True)
class SourceCheckoutAttestation:
    """Child observation binding executing bytes to one declared checkout HEAD."""

    root: Path
    commit: str


def controlled_python_argv(
    python_executable: str | Path,
    *arguments: str,
) -> tuple[str, ...]:
    """Build the one Python launch prefix used by controlled EMRYS children."""

    return (str(python_executable), *CONTROLLED_PYTHON_OPTIONS, *arguments)


def is_controlled_python_argv(
    argv: Sequence[str],
    *,
    python_executable: str | Path,
) -> bool:
    """Return whether ``argv`` begins with the exact controlled Python prefix."""

    expected = controlled_python_argv(python_executable)
    return tuple(argv[: len(expected)]) == expected


def require_controlled_python_runtime() -> None:
    """Reject a Python child that could load adjacent package bytecode caches."""

    if sys.pycache_prefix != CONTROLLED_PYTHON_CACHE_PREFIX:
        raise SourceCheckoutError(
            "Controlled EMRYS Python children require "
            "-X pycache_prefix=/dev/null before -I"
        )


def _canonical_directory(
    value: Path,
    label: str,
    error_type: type[RuntimeError] = SourceCheckoutError,
) -> Path:
    if not value.is_absolute():
        raise error_type(f"{label} must be absolute: {value}")
    if value.is_symlink():
        raise error_type(f"{label} must not be a symbolic link: {value}")
    try:
        resolved = value.resolve(strict=True)
    except OSError as exc:
        raise error_type(f"{label} is unavailable: {value}") from exc
    if value != resolved:
        raise error_type(
            f"{label} must be canonical: expected {resolved}; received {value}"
        )
    if not resolved.is_dir():
        raise error_type(f"{label} is not a directory: {resolved}")
    return resolved


def admit_artifact_source_root(*, root: Path) -> ArtifactSourceRoot:
    """Admit an explicit canonical directory for contract-relative artifacts."""

    canonical_root = _canonical_directory(
        root,
        "Artifact source root",
        ArtifactSourceRootError,
    )
    return ArtifactSourceRoot(root=canonical_root)


def _validate_project(root: Path) -> None:
    path = root / "pyproject.toml"
    if not path.is_file() or path.is_symlink():
        raise SourceCheckoutError(
            f"Source checkout project metadata is unavailable: {path}"
        )
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise SourceCheckoutError(
            f"Source checkout project metadata is invalid: {path}"
        ) from exc
    project = document.get("project")
    if not isinstance(project, dict) or project.get("name") != PROJECT_NAME:
        raise SourceCheckoutError(f"Source checkout project must be {PROJECT_NAME!r}")


def _git_top_level(root: Path, *, ops: SourceAuthorityOps) -> Path:
    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    try:
        result = ops.run_git(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        raise SourceCheckoutError(
            f"Could not resolve source checkout Git top level: {root}"
        ) from exc
    observed_text = result.stdout.strip()
    observed = Path(observed_text)
    if not observed.is_absolute():
        raise SourceCheckoutError(
            f"Source checkout Git top level is invalid: {observed_text!r}"
        )
    try:
        return observed.resolve(strict=True)
    except OSError as exc:
        raise SourceCheckoutError(
            f"Source checkout Git top level is unavailable: {observed}"
        ) from exc


def _real_tree_entries(root: Path) -> tuple[Path, ...]:
    """Walk a package without following or silently omitting any symlink."""

    entries: list[Path] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            children = tuple(sorted(directory.iterdir()))
        except OSError as exc:
            raise SourceCheckoutError(
                f"Could not inspect source package directory: {directory}"
            ) from exc
        for path in children:
            try:
                state = path.lstat()
            except OSError as exc:
                raise SourceCheckoutError(
                    f"Could not inspect source package entry: {path}"
                ) from exc
            if stat.S_ISLNK(state.st_mode):
                raise SourceCheckoutError(
                    f"Source package tree contains a symbolic link: {path}"
                )
            entries.append(path)
            if stat.S_ISDIR(state.st_mode):
                if path.name != "__pycache__":
                    pending.append(path)
            elif not stat.S_ISREG(state.st_mode):
                raise SourceCheckoutError(
                    f"Source package tree contains a non-regular entry: {path}"
                )
    return tuple(entries)


def _python_files(root: Path) -> dict[Path, Path]:
    return {
        path.relative_to(root): path
        for path in _real_tree_entries(root)
        if path.suffix == ".py" and "__pycache__" not in path.parts
    }


def _declared_resources(source_package: Path) -> dict[Path, Path]:
    entries = _real_tree_entries(source_package)
    resources: dict[Path, Path] = {}
    for package_directory, pattern in _RESOURCE_PATTERNS:
        matches = sorted(
            path
            for path in entries
            if path.is_file()
            and path.relative_to(source_package).match(str(package_directory / pattern))
        )
        if not matches:
            raise SourceCheckoutError(
                f"Source checkout resource pattern matched no files: {pattern!r}"
            )
        resources.update((path.relative_to(source_package), path) for path in matches)
    return resources


def _is_package_identity_path(relative_path: Path) -> bool:
    if relative_path.suffix == ".py" and "__pycache__" not in relative_path.parts:
        return True
    return any(
        relative_path.match(str(package_directory / pattern))
        for package_directory, pattern in _RESOURCE_PATTERNS
    )


def _git_environment() -> dict[str, str]:
    return {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }


def _package_matches_checkout_revision(
    *,
    source_checkout: SourceCheckout,
    package_root: Path,
    revision: str,
    ops: SourceAuthorityOps = DEFAULT_SOURCE_AUTHORITY_OPS,
) -> bool:
    canonical_package = _canonical_directory(
        package_root,
        "Executing EMRYS package root",
    )
    package_files = _python_files(canonical_package)
    package_files.update(_declared_resources(canonical_package))
    environment = _git_environment()
    try:
        object_format = ops.run_git(
            ["git", "rev-parse", "--show-object-format"],
            cwd=source_checkout.root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        tree = ops.run_git(
            ["git", "ls-tree", "-r", "-z", revision, "--", "src/emrys"],
            cwd=source_checkout.root,
            env=environment,
            check=True,
            capture_output=True,
        ).stdout
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        raise SourceCheckoutError(
            f"Could not compare the executing package with source checkout HEAD: {exc}"
        ) from exc
    if object_format not in hashlib.algorithms_available:
        raise SourceCheckoutError(
            f"Unsupported Git object format for package identity: {object_format!r}"
        )
    head_objects: dict[Path, str] = {}
    prefix = Path("src/emrys")
    try:
        entries = (entry for entry in tree.split(b"\0") if entry)
        for entry in entries:
            metadata, raw_path = entry.split(b"\t", 1)
            _mode, object_type, object_id = metadata.decode("ascii").split()
            relative_path = Path(os.fsdecode(raw_path)).relative_to(prefix)
            if object_type == "blob" and _is_package_identity_path(relative_path):
                head_objects[relative_path] = object_id
    except (UnicodeError, ValueError) as exc:
        raise SourceCheckoutError(
            "Source checkout Git tree contains an invalid package identity"
        ) from exc
    if package_files.keys() != head_objects.keys():
        return False
    for relative_path, path in package_files.items():
        payload = _read_identity_file(path, "package identity file")
        header = f"blob {len(payload)}\0".encode("ascii")
        digest = hashlib.new(object_format, header + payload).hexdigest()
        if digest != head_objects[relative_path]:
            return False
    return True


def package_matches_checkout_head(
    *,
    source_checkout: SourceCheckout,
    package_root: Path,
    ops: SourceAuthorityOps = DEFAULT_SOURCE_AUTHORITY_OPS,
) -> bool:
    """Return whether the executing package identity is exactly at checkout HEAD."""

    return _package_matches_checkout_revision(
        source_checkout=source_checkout,
        package_root=package_root,
        revision="HEAD",
        ops=ops,
    )


def matching_checkout_head_commit(
    *,
    source_checkout: SourceCheckout,
    package_root: Path,
    ops: SourceAuthorityOps = DEFAULT_SOURCE_AUTHORITY_OPS,
) -> str | None:
    """Return one stable HEAD only when it exactly owns executing package bytes."""

    environment = _git_environment()

    def observe_head() -> str:
        try:
            commit = ops.run_git(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=source_checkout.root,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
            raise SourceCheckoutError(
                f"Could not inspect source checkout HEAD: {source_checkout.root}"
            ) from exc
        if re.fullmatch(r"[0-9a-f]{40,64}", commit) is None:
            raise SourceCheckoutError(
                f"Source checkout HEAD commit is invalid: {commit!r}"
            )
        return commit

    before = observe_head()
    matches = _package_matches_checkout_revision(
        source_checkout=source_checkout,
        package_root=package_root,
        revision=before,
        ops=ops,
    )
    after = observe_head()
    if after != before:
        raise SourceCheckoutError(
            "Source checkout HEAD changed during exact package attribution"
        )
    return before if matches else None


def matching_clean_checkout_head_commit(
    *,
    source_checkout: SourceCheckout,
    package_root: Path,
    ops: SourceAuthorityOps = DEFAULT_SOURCE_AUTHORITY_OPS,
) -> str | None:
    """Return one stable HEAD only for an exactly matching clean checkout."""

    identity = inspect_source_checkout(
        root=source_checkout.root,
        package_root=package_root,
        require_clean=False,
        ops=ops,
    )
    return identity.commit if identity.clean else None


def _read_identity_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise SourceCheckoutError(f"Source checkout {label} is unavailable: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SourceCheckoutError(
            f"Source checkout {label} cannot be read: {path}"
        ) from exc


def _compare_package_identity(
    *,
    source_package: Path,
    package_root: Path,
) -> None:
    source_python = _python_files(source_package)
    package_python = _python_files(package_root)
    if source_python.keys() != package_python.keys():
        raise SourceCheckoutError(
            "Source checkout Python roster differs from the executing package"
        )
    for relative_path, source_path in source_python.items():
        if _read_identity_file(source_path, "Python file") != _read_identity_file(
            package_python[relative_path], "Python file"
        ):
            raise SourceCheckoutError(
                f"Source checkout Python bytes differ: {relative_path}"
            )

    declared_resources = _declared_resources(source_package)
    for relative_path, source_path in declared_resources.items():
        if _read_identity_file(source_path, "resource") != _read_identity_file(
            package_root / relative_path, "resource"
        ):
            raise SourceCheckoutError(
                f"Source checkout resource bytes differ: {relative_path}"
            )

    if package_root != source_package:
        for package_path in _real_tree_entries(package_root):
            relative_path = package_path.relative_to(package_root)
            if (
                not package_path.is_file()
                or package_path.suffix in {".py", ".pyc", ".pyo"}
                or "__pycache__" in relative_path.parts
            ):
                continue
            source_path = source_package / relative_path
            if _read_identity_file(source_path, "resource") != _read_identity_file(
                package_path, "resource"
            ):
                raise SourceCheckoutError(
                    f"Source checkout resource bytes differ: {relative_path}"
                )


def admit_source_checkout(
    *,
    root: Path,
    package_root: Path,
    ops: SourceAuthorityOps = DEFAULT_SOURCE_AUTHORITY_OPS,
) -> SourceCheckout:
    """Admit one canonical Git checkout matching the executing package bytes."""

    canonical_root = _canonical_directory(root, "Source checkout root")
    canonical_package = _canonical_directory(
        package_root,
        "Executing EMRYS package root",
    )
    _validate_project(canonical_root)
    source_package = _canonical_directory(
        canonical_root / "src" / "emrys",
        "Source checkout EMRYS package root",
    )
    marker = source_package / "__init__.py"
    if not marker.is_file() or marker.is_symlink():
        raise SourceCheckoutError(
            f"Source checkout package marker is unavailable: {marker}"
        )
    observed_top_level = _git_top_level(canonical_root, ops=ops)
    if observed_top_level != canonical_root:
        raise SourceCheckoutError(
            "Source checkout Git top level differs: "
            f"expected {canonical_root}; observed {observed_top_level}"
        )
    _compare_package_identity(
        source_package=source_package,
        package_root=canonical_package,
    )
    return SourceCheckout(root=canonical_root)


def attest_source_checkout(
    *,
    root: Path,
    package_root: Path,
    expected_commit: str,
    ops: SourceAuthorityOps = DEFAULT_SOURCE_AUTHORITY_OPS,
) -> SourceCheckoutAttestation:
    """Bind child package bytes to a checkout whose HEAD is the declared commit.

    The child independently proves that the executing package roster and bytes
    equal the declared commit between stable HEAD observations. Checkout-wide
    cleanliness remains the parent lifecycle's pre/post execution authority.
    """

    if re.fullmatch(r"[0-9a-f]{40,64}", expected_commit) is None:
        raise SourceCheckoutError(
            f"Expected source checkout commit is invalid: {expected_commit!r}"
        )
    checkout = admit_source_checkout(root=root, package_root=package_root, ops=ops)
    environment = _git_environment()

    def observe_head() -> str:
        try:
            value = ops.run_git(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=checkout.root,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
            raise SourceCheckoutError(
                f"Could not attest source checkout HEAD: {checkout.root}"
            ) from exc
        if re.fullmatch(r"[0-9a-f]{40,64}", value) is None:
            raise SourceCheckoutError(
                f"Source checkout HEAD commit is invalid: {value!r}"
            )
        return value

    before = observe_head()
    if before != expected_commit:
        raise SourceCheckoutError(
            "Source checkout HEAD differs from the workflow attempt commit"
        )
    if not _package_matches_checkout_revision(
        source_checkout=checkout,
        package_root=package_root,
        revision=expected_commit,
        ops=ops,
    ):
        raise SourceCheckoutError(
            "Executing package identity does not exactly match the workflow "
            "attempt commit"
        )
    # Repeat working-tree admission between HEAD observations so neither a
    # package swap nor a revision move can be paired with the other snapshot.
    admitted_again = admit_source_checkout(
        root=root, package_root=package_root, ops=ops
    )
    after = observe_head()
    if admitted_again != checkout or after != expected_commit:
        raise SourceCheckoutError(
            "Source checkout identity changed during child attestation"
        )
    return SourceCheckoutAttestation(root=checkout.root, commit=expected_commit)


def inspect_source_checkout(
    *,
    root: Path,
    package_root: Path,
    require_clean: bool = True,
    ops: SourceAuthorityOps = DEFAULT_SOURCE_AUTHORITY_OPS,
) -> SourceCheckoutIdentity:
    """Admit package identity and return exact sanitized Git HEAD/cleanliness."""

    checkout = admit_source_checkout(
        root=root,
        package_root=package_root,
        ops=ops,
    )
    environment = _git_environment()
    try:
        commit = ops.run_git(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=checkout.root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if not _package_matches_checkout_revision(
            source_checkout=checkout,
            package_root=package_root,
            revision=commit,
            ops=ops,
        ):
            raise SourceCheckoutError(
                "Executing package identity does not exactly match source checkout HEAD"
            )
        status = ops.run_git(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=checkout.root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        confirmed_commit = ops.run_git(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=checkout.root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        confirmed_status = ops.run_git(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=checkout.root,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, UnicodeError, subprocess.CalledProcessError) as exc:
        raise SourceCheckoutError(
            f"Could not inspect source checkout Git identity: {checkout.root}"
        ) from exc
    if not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        raise SourceCheckoutError(f"Source checkout HEAD commit is invalid: {commit!r}")
    if confirmed_commit != commit:
        raise SourceCheckoutError(
            "Source checkout HEAD changed while identity was inspected"
        )
    if confirmed_status != status:
        raise SourceCheckoutError(
            "Source checkout status changed while identity was inspected"
        )
    clean = status == ""
    if require_clean and not clean:
        raise SourceCheckoutError(
            "Source checkout must be clean, including untracked files"
        )
    return SourceCheckoutIdentity(root=checkout.root, commit=commit, clean=clean)


__all__ = (
    "ArtifactSourceRoot",
    "ArtifactSourceRootError",
    "CONTROLLED_PYTHON_CACHE_PREFIX",
    "CONTROLLED_PYTHON_OPTIONS",
    "DEFAULT_SOURCE_AUTHORITY_OPS",
    "SourceAuthorityOps",
    "SourceCheckout",
    "SourceCheckoutAttestation",
    "SourceCheckoutError",
    "SourceCheckoutIdentity",
    "admit_artifact_source_root",
    "admit_source_checkout",
    "attest_source_checkout",
    "controlled_python_argv",
    "inspect_source_checkout",
    "is_controlled_python_argv",
    "matching_checkout_head_commit",
    "matching_clean_checkout_head_commit",
    "package_matches_checkout_head",
    "require_controlled_python_runtime",
)
