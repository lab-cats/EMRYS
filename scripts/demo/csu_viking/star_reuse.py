#!/usr/bin/env python3
"""Demo-only STAR proxy that substitutes one retained compatible index."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
from pathlib import Path
from typing import NoReturn, Optional, Sequence


REQUIRED_INDEX_MEMBERS = (
    "genomeParameters.txt",
    "Genome",
    "SA",
    "SAindex",
    "chrLength.txt",
    "chrName.txt",
    "chrNameLength.txt",
    "chrStart.txt",
    "exonGeTrInfo.tab",
    "exonInfo.tab",
    "geneInfo.tab",
    "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab",
    "sjdbList.out.tab",
    "transcriptInfo.tab",
)


class DemoStarError(RuntimeError):
    """The demo STAR substitution is unsafe or incompatible."""


def _fail(message: str) -> NoReturn:
    raise DemoStarError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _authored_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        _fail(f"path must be absolute: {path}")
    return Path(os.path.abspath(path))


def _real_file(raw: str, label: str, *, executable: bool = False) -> Path:
    path = _authored_path(raw)
    try:
        state = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISREG(state.st_mode)
        or resolved != path
        or (executable and not os.access(path, os.X_OK))
    ):
        _fail(f"{label} must be a canonical real file: {path}")
    return path


def _real_directory(raw: str, label: str) -> Path:
    path = _authored_path(raw)
    try:
        state = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        _fail(f"{label} is unavailable: {path}: {exc}")
    if (
        stat.S_ISLNK(state.st_mode)
        or not stat.S_ISDIR(state.st_mode)
        or resolved != path
    ):
        _fail(f"{label} must be a canonical real directory: {path}")
    return path


def _parse_parameters(path: Path) -> dict[str, tuple[str, ...]]:
    values: dict[str, tuple[str, ...]] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        _fail(f"could not read retained genomeParameters.txt: {exc}")
    for number, raw in enumerate(lines, start=1):
        fields = raw.split()
        if not fields or fields[0] == "###":
            continue
        if len(fields) < 2 or fields[0] in values:
            _fail(f"invalid retained genomeParameters.txt line {number}")
        values[fields[0]] = tuple(fields[1:])
    return values


def _snapshot(path: Path) -> tuple[int, int, int, int, int]:
    state = path.stat(follow_symlinks=False)
    return (
        state.st_dev,
        state.st_ino,
        state.st_mode,
        state.st_size,
        state.st_mtime_ns,
    )


def populate_index(
    *,
    source_index: Path,
    destination: Path,
    source_fasta: Path,
    source_gtf: Path,
    workspace: Path,
) -> None:
    """Hardlink the exact retained index roster into an empty staging directory."""

    source_index = _real_directory(str(source_index), "retained STAR index")
    destination = _real_directory(str(destination), "STAR staging directory")
    workspace = _real_directory(str(workspace), "demo workspace")
    source_fasta = _real_file(str(source_fasta), "retained reference FASTA")
    source_gtf = _real_file(str(source_gtf), "retained reference GTF")

    if destination == source_index or not destination.is_relative_to(workspace):
        _fail("STAR staging directory is outside the selected demo workspace")
    try:
        if any(destination.iterdir()):
            _fail(f"STAR staging directory is not empty: {destination}")
    except OSError as exc:
        _fail(f"could not inspect STAR staging directory: {exc}")

    sources: list[Path] = []
    snapshots: dict[Path, tuple[int, int, int, int, int]] = {}
    destination_device = destination.stat().st_dev
    for name in REQUIRED_INDEX_MEMBERS:
        member = _real_file(str(source_index / name), f"retained index member {name}")
        state = member.stat(follow_symlinks=False)
        if state.st_size < 1:
            _fail(f"retained index member is empty: {member}")
        if state.st_dev != destination_device:
            _fail("retained index and demo workspace are on different filesystems")
        sources.append(member)
        snapshots[member] = _snapshot(member)

    parameters = _parse_parameters(source_index / "genomeParameters.txt")
    if parameters.get("genomeFastaFiles") != (str(source_fasta),):
        _fail("retained STAR index does not bind the selected reference FASTA")
    if parameters.get("sjdbGTFfile") != (str(source_gtf),):
        _fail("retained STAR index does not bind the selected reference GTF")
    if parameters.get("sjdbOverhang") != ("149",):
        _fail("retained STAR index does not use sjdbOverhang 149")
    if parameters.get("genomeSAindexNbases") != ("14",):
        _fail("retained STAR index does not use genomeSAindexNbases 14")

    created: list[Path] = []
    try:
        for source in sources:
            target = destination / source.name
            os.link(source, target, follow_symlinks=False)
            created.append(target)
        for source, target in zip(sources, created):
            if _snapshot(source) != snapshots[source] or not os.path.samefile(
                source, target
            ):
                _fail(f"retained index member changed during import: {source}")
    except BaseException:
        for target in reversed(created):
            try:
                target.unlink()
            except OSError:
                pass
        raise


def _config_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--real-star", required=True)
    parser.add_argument("--real-star-sha256", required=True)
    parser.add_argument("--source-index", required=True)
    parser.add_argument("--source-fasta", required=True)
    parser.add_argument("--source-gtf", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--expected-threads", required=True)
    return parser


def _split_arguments(argv: Sequence[str]) -> tuple[list[str], list[str]]:
    if argv.count("--") != 1:
        _fail("demo STAR launcher requires one argument separator")
    separator = argv.index("--")
    return list(argv[:separator]), list(argv[separator + 1 :])


def _delegate(real_star: Path, arguments: Sequence[str]) -> NoReturn:
    os.execv(real_star, (str(real_star), *arguments))


def main(argv: Optional[Sequence[str]] = None) -> int:
    selected = list(sys.argv[1:] if argv is None else argv)
    try:
        config_arguments, star_arguments = _split_arguments(selected)
        config = _config_parser().parse_args(config_arguments)
        real_star = _real_file(config.real_star, "real STAR", executable=True)
        if _sha256(real_star) != config.real_star_sha256:
            _fail("real STAR content differs from the demo launcher binding")

        expected_generation = [
            "--runThreadN",
            config.expected_threads,
            "--runMode",
            "genomeGenerate",
            "--genomeDir",
            "__DESTINATION__",
            "--genomeFastaFiles",
            config.source_fasta,
            "--sjdbGTFfile",
            config.source_gtf,
            "--sjdbOverhang",
            "149",
            "--genomeSAindexNbases",
            "14",
        ]
        generation_shape = list(star_arguments)
        if len(generation_shape) == len(expected_generation):
            destination = generation_shape[5]
            generation_shape[5] = "__DESTINATION__"
        else:
            destination = ""

        if generation_shape == expected_generation:
            populate_index(
                source_index=Path(config.source_index),
                destination=Path(destination),
                source_fasta=Path(config.source_fasta),
                source_gtf=Path(config.source_gtf),
                workspace=Path(config.workspace),
            )
            print(
                "DEMO_PREBUILT_INDEX_IMPORT=PASS "
                f"members={len(REQUIRED_INDEX_MEMBERS)} "
                f"source={config.source_index} destination={destination}"
            )
            return 0

        if "genomeGenerate" in star_arguments or "--runMode" in star_arguments:
            _fail("unexpected STAR genomeGenerate invocation; refusing delegation")
        _delegate(real_star, star_arguments)
    except (DemoStarError, OSError) as exc:
        print(f"DEMO STAR ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
