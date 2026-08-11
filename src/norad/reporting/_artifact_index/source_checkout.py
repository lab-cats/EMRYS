"""Fail-closed admission for the source checkout used by artifact indexing."""

from __future__ import annotations

import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

PROJECT_NAME = "norad-rna-workflow"
_RESOURCE_PATTERNS = (
    (Path("contracts"), "schemas/artifacts/v1/*.json"),
    (Path("reporting"), "styles/*.css"),
    (Path("reporting"), "templates/*.qmd"),
)


@dataclass(frozen=True, slots=True)
class SourceCheckout:
    """One canonical Git checkout matching the executing NORAD package."""

    root: Path


class SourceCheckoutError(RuntimeError):
    """The claimed checkout cannot own the executing package identity."""


def _canonical_directory(value: Path, label: str) -> Path:
    if not value.is_absolute():
        raise SourceCheckoutError(f"{label} must be absolute: {value}")
    if value.is_symlink():
        raise SourceCheckoutError(f"{label} must not be a symbolic link: {value}")
    try:
        resolved = value.resolve(strict=True)
    except OSError as exc:
        raise SourceCheckoutError(f"{label} is unavailable: {value}") from exc
    if value != resolved:
        raise SourceCheckoutError(
            f"{label} must be canonical: expected {resolved}; received {value}"
        )
    if not resolved.is_dir():
        raise SourceCheckoutError(f"{label} is not a directory: {resolved}")
    return resolved


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


def _git_top_level(root: Path) -> Path:
    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
    }
    try:
        result = subprocess.run(
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


def _python_files(root: Path) -> dict[Path, Path]:
    return {
        path.relative_to(root): path
        for path in root.rglob("*.py")
        if path.is_file() and "__pycache__" not in path.parts
    }


def _declared_resources(source_package: Path) -> dict[Path, Path]:
    resources: dict[Path, Path] = {}
    for package_directory, pattern in _RESOURCE_PATTERNS:
        matches = sorted((source_package / package_directory).glob(pattern))
        if not matches:
            raise SourceCheckoutError(
                f"Source checkout resource pattern matched no files: {pattern!r}"
            )
        resources.update((path.relative_to(source_package), path) for path in matches)
    return resources


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
        for package_path in package_root.rglob("*"):
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
) -> SourceCheckout:
    """Admit one canonical Git checkout matching the executing package bytes."""

    canonical_root = _canonical_directory(root, "Source checkout root")
    canonical_package = _canonical_directory(
        package_root,
        "Executing NORAD package root",
    )
    _validate_project(canonical_root)
    source_package = _canonical_directory(
        canonical_root / "src" / "norad",
        "Source checkout NORAD package root",
    )
    marker = source_package / "__init__.py"
    if not marker.is_file() or marker.is_symlink():
        raise SourceCheckoutError(
            f"Source checkout package marker is unavailable: {marker}"
        )
    observed_top_level = _git_top_level(canonical_root)
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
