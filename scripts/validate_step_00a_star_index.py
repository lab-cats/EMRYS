#!/usr/bin/env python3
"""Validate one explicit Step 00a STAR index without modifying it."""

from __future__ import annotations

import argparse
import csv
import os
import stat
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


HEADER = ("step_id", "scope_id", "check_id", "status", "observed", "expected", "detail")
REQUIRED_MEMBERS = (
    "genomeParameters.txt", "Genome", "SA", "SAindex", "chrLength.txt",
    "chrName.txt", "chrNameLength.txt", "chrStart.txt", "exonGeTrInfo.tab",
    "exonInfo.tab", "geneInfo.tab", "sjdbInfo.txt",
    "sjdbList.fromGTF.out.tab", "sjdbList.out.tab", "transcriptInfo.tab",
)


class ValidationError(RuntimeError):
    """Raised when the validator contract or publication state is unsafe."""


@dataclass(frozen=True)
class Snapshot:
    device: int
    inode: int
    size: int
    mtime_ns: int


def fail(message: str) -> None:
    raise ValidationError(message)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-id", required=True)
    parser.add_argument("--index-dir", required=True, type=Path)
    parser.add_argument("--reference-fasta", required=True, type=Path)
    parser.add_argument("--reference-gtf", required=True, type=Path)
    parser.add_argument(
        "--parameter-path-base",
        required=True,
        type=Path,
        help="Explicit base for relative paths recorded in genomeParameters.txt.",
    )
    parser.add_argument("--expected-sjdb-overhang", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def clean(value: object) -> str:
    return " ".join(str(value).replace("\x00", "").split())


def regular_snapshot(path: Path, label: str, *, nonempty: bool = True) -> Snapshot:
    try:
        value = path.lstat()
    except OSError as exc:
        fail(f"{label} is unavailable: {path}: {exc}")
    if stat.S_ISLNK(value.st_mode) or not stat.S_ISREG(value.st_mode):
        fail(f"{label} must be a regular non-symlink file: {path}")
    if nonempty and value.st_size == 0:
        fail(f"{label} must be nonempty: {path}")
    return Snapshot(value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)


def stable_text(path: Path, label: str) -> tuple[str, Snapshot]:
    before = regular_snapshot(path, label)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(f"{label} cannot be read as UTF-8: {path}: {exc}")
    after = regular_snapshot(path, label)
    if before != after:
        fail(f"{label} changed while read: {path}")
    return text, after


def parse_parameters(path: Path) -> tuple[dict[str, list[str]], Snapshot]:
    text, snapshot = stable_text(path, "STAR genomeParameters")
    parsed: dict[str, list[str]] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        fields = raw.split()
        if not fields:
            continue
        if len(fields) < 2:
            fail(f"STAR genomeParameters line {number} has no value")
        if fields[0] in parsed:
            fail(f"STAR genomeParameters repeats {fields[0]!r}")
        parsed[fields[0]] = fields[1:]
    return parsed, snapshot


def fasta_contigs(path: Path) -> tuple[list[tuple[str, int]], Snapshot]:
    before = regular_snapshot(path, "Reference FASTA")
    contigs: list[tuple[str, int]] = []
    name: str | None = None
    length = 0
    seen: set[str] = set()
    try:
        with path.open(encoding="utf-8") as stream:
            for number, raw in enumerate(stream, 1):
                line = raw.rstrip("\n")
                if line.startswith(">"):
                    if name is not None:
                        contigs.append((name, length))
                    name = line[1:].split()[0]
                    if not name or name in seen:
                        fail(f"Reference FASTA line {number} has invalid or duplicate contig")
                    seen.add(name)
                    length = 0
                else:
                    if name is None or not line:
                        fail(f"Reference FASTA line {number} is invalid")
                    length += len(line)
    except (OSError, UnicodeError) as exc:
        fail(f"Reference FASTA cannot be read: {exc}")
    if name is not None:
        contigs.append((name, length))
    if not contigs or any(length <= 0 for _, length in contigs):
        fail("Reference FASTA must contain nonempty contigs")
    after = regular_snapshot(path, "Reference FASTA")
    if before != after:
        fail("Reference FASTA changed while read")
    return contigs, after


def index_contigs(index_dir: Path) -> tuple[list[tuple[str, int]], tuple[Snapshot, Snapshot]]:
    names_text, names_snapshot = stable_text(index_dir / "chrName.txt", "STAR chrName")
    lengths_text, lengths_snapshot = stable_text(index_dir / "chrLength.txt", "STAR chrLength")
    names = names_text.splitlines()
    lengths = lengths_text.splitlines()
    if not names or len(names) != len(lengths) or len(names) != len(set(names)):
        fail("STAR chrName/chrLength rows are empty, duplicate, or misaligned")
    try:
        parsed = [(name, int(length)) for name, length in zip(names, lengths, strict=True)]
    except ValueError as exc:
        fail(f"STAR chrLength contains a non-integer: {exc}")
    if any(not name or length <= 0 for name, length in parsed):
        fail("STAR contig names and lengths must be nonempty and positive")
    return parsed, (names_snapshot, lengths_snapshot)


def normalized_declared_path(value: str, path_base: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = path_base / path
    return path.resolve(strict=False)


def row(scope_id: str, check_id: str, passed: bool, observed: object, expected: object, detail: str) -> tuple[str, ...]:
    return (
        "00a", scope_id, check_id, "pass" if passed else "fail",
        clean(observed), clean(expected), clean(detail),
    )


def render(rows: Sequence[Sequence[str]]) -> bytes:
    lines = ["\t".join(HEADER)]
    lines.extend("\t".join(clean(value) for value in values) for values in rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_report(data: bytes, scope_id: str) -> None:
    try:
        reader = csv.DictReader(data.decode("utf-8").splitlines(), delimiter="\t")
    except UnicodeError as exc:
        fail(f"Validation report is not UTF-8: {exc}")
    if tuple(reader.fieldnames or ()) != HEADER:
        fail("Validation report header is invalid")
    rows = list(reader)
    if len(rows) != 5:
        fail("Step 00a validation report must contain exactly five checks")
    if any(None in item or any(value is None for value in item.values()) for item in rows):
        fail("Validation report contains an invalid row")
    expected_ids = {
        "index_members", "fasta_identity", "gtf_identity",
        "contig_names_lengths", "sjdb_overhang",
    }
    if {item["check_id"] for item in rows} != expected_ids:
        fail("Validation report check IDs are invalid")
    if any(item["step_id"] != "00a" or item["scope_id"] != scope_id for item in rows):
        fail("Validation report scope identity is invalid")
    if any(item["status"] not in {"pass", "fail"} for item in rows):
        fail("Validation report status is invalid")


def build_report(args: argparse.Namespace) -> tuple[bytes, dict[Path, Snapshot]]:
    if not args.scope_id or any(char.isspace() for char in args.scope_id):
        fail("scope-id must be nonempty and contain no whitespace")
    if args.expected_sjdb_overhang < 0:
        fail("expected-sjdb-overhang must be nonnegative")
    index_dir = args.index_dir.resolve(strict=False)
    if not index_dir.is_dir() or index_dir.is_symlink():
        fail(f"STAR index directory must be an existing real directory: {index_dir}")
    path_base = args.parameter_path_base.resolve(strict=False)
    if not path_base.is_dir() or path_base.is_symlink():
        fail(f"Parameter path base must be an existing real directory: {path_base}")
    snapshots: dict[Path, Snapshot] = {}
    missing: list[str] = []
    for name in REQUIRED_MEMBERS:
        path = index_dir / name
        try:
            snapshots[path] = regular_snapshot(path, f"STAR index member {name}")
        except ValidationError:
            missing.append(name)
    members_pass = not missing
    parameters, parameter_snapshot = parse_parameters(index_dir / "genomeParameters.txt")
    snapshots[index_dir / "genomeParameters.txt"] = parameter_snapshot
    fasta = args.reference_fasta.resolve(strict=False)
    gtf = args.reference_gtf.resolve(strict=False)
    fasta_records, fasta_snapshot = fasta_contigs(fasta)
    snapshots[fasta] = fasta_snapshot
    _, gtf_snapshot = stable_text(gtf, "Reference GTF")
    snapshots[gtf] = gtf_snapshot
    star_records, star_snapshots = index_contigs(index_dir)
    snapshots[index_dir / "chrName.txt"] = star_snapshots[0]
    snapshots[index_dir / "chrLength.txt"] = star_snapshots[1]
    fasta_values = parameters.get("genomeFastaFiles", [])
    gtf_values = parameters.get("sjdbGTFfile", [])
    overhang_values = parameters.get("sjdbOverhang", [])
    fasta_match = len(fasta_values) == 1 and normalized_declared_path(
        fasta_values[0], path_base
    ) == fasta
    gtf_match = len(gtf_values) == 1 and normalized_declared_path(
        gtf_values[0], path_base
    ) == gtf
    try:
        observed_overhang = int(overhang_values[0]) if len(overhang_values) == 1 else None
    except ValueError:
        observed_overhang = None
    rows = (
        row(args.scope_id, "index_members", members_pass,
            len(REQUIRED_MEMBERS) - len(missing), len(REQUIRED_MEMBERS),
            "all required members present" if members_pass else "missing: " + ",".join(missing)),
        row(args.scope_id, "fasta_identity", fasta_match,
            fasta_values[0] if len(fasta_values) == 1 else "invalid", str(fasta),
            "genomeFastaFiles resolves to the explicit FASTA"),
        row(args.scope_id, "gtf_identity", gtf_match,
            gtf_values[0] if len(gtf_values) == 1 else "invalid", str(gtf),
            "sjdbGTFfile resolves to the explicit GTF"),
        row(args.scope_id, "contig_names_lengths", star_records == fasta_records,
            f"{len(star_records)} STAR contigs", f"{len(fasta_records)} FASTA contigs",
            "ordered contig names and lengths agree" if star_records == fasta_records else "ordered contig names or lengths differ"),
        row(args.scope_id, "sjdb_overhang", observed_overhang == args.expected_sjdb_overhang,
            observed_overhang if observed_overhang is not None else "invalid",
            args.expected_sjdb_overhang, "configured STAR splice-junction overhang"),
    )
    data = render(rows)
    validate_report(data, args.scope_id)
    return data, snapshots


def publish(path: Path, data: bytes, scope_id: str) -> None:
    parent = path.parent
    if not parent.exists() or parent.is_symlink() or not parent.is_dir():
        fail(f"Output parent must be an existing real directory: {parent}")
    if path.name != f"{scope_id}.validation.tsv":
        fail(f"Output basename must be {scope_id}.validation.tsv")
    lock = parent / f".{path.name}.lock"
    token = uuid.uuid4().hex
    staged = parent / f".{path.name}.{token}.tmp"
    previous = parent / f".{path.name}.{token}.previous"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        fail(f"Validation report lock already exists: {lock}")
    replaced = False
    try:
        os.write(descriptor, f"pid={os.getpid()}\nrun_token={token}\n".encode())
        with staged.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        validate_report(staged.read_bytes(), scope_id)
        if path.exists() or path.is_symlink():
            if path.is_symlink() or not path.is_file():
                fail(f"Existing validation report is unsafe: {path}")
            validate_report(path.read_bytes(), scope_id)
            os.replace(path, previous)
            replaced = True
        try:
            os.replace(staged, path)
            validate_report(path.read_bytes(), scope_id)
        except BaseException:
            if path.exists() and not path.is_symlink():
                path.unlink()
            if replaced and previous.exists():
                os.replace(previous, path)
            raise
        if previous.exists():
            previous.unlink()
    finally:
        if staged.exists() and not staged.is_symlink():
            staged.unlink()
        os.close(descriptor)
        if lock.exists() and not lock.is_symlink():
            lock.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data, snapshots = build_report(args)
        print(f"Step: 00a")
        print(f"Scope: {args.scope_id}")
        print(f"STAR index: {args.index_dir}")
        print(f"Parameter path base: {args.parameter_path_base}")
        print(f"Output: {args.output}")
        print(data.decode("utf-8"), end="")
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        for path, expected in snapshots.items():
            if regular_snapshot(path, f"Input {path.name}") != expected:
                fail(f"Input changed after validation: {path}")
        publish(args.output, data, args.scope_id)
        print(f"Published Step 00a validation report: {args.output}")
        return 0
    except ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
