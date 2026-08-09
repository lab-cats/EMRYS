#!/usr/bin/env python3
"""Inventory and reconcile one explicit reference bundle without repairing it."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import stat
import sys
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

src_root = str(Path(__file__).resolve().parents[3])
# Direct execution must prefer this checkout over an installed NORAD.
sys.path[:] = [src_root, *(entry for entry in sys.path if entry != src_root)]
from norad.libraries import validation as report

PROFILE_HEADER = (
    "reference_id",
    "artifact_id",
    "role",
    "path",
    "required",
    "expected_sha256",
    "provenance_source",
    "provenance_release",
    "notes",
)
ARTIFACT_HEADER = (
    "reference_id",
    "artifact_id",
    "role",
    "declared_path",
    "resolved_path",
    "required",
    "status",
    "observed_sha256",
    "expected_sha256",
    "size_bytes",
    "provenance_source",
    "provenance_release",
    "detail",
)
CONTIG_HEADER = (
    "reference_id",
    "source_role",
    "ordinal",
    "contig",
    "length",
    "status",
    "detail",
)
SUMMARY_HEADER = (
    "reference_id",
    "profile_sha256",
    "artifact_count",
    "required_missing_count",
    "hash_mismatch_count",
    "invalid_artifact_count",
    "fasta_contig_count",
    "fai_agreement",
    "dict_agreement",
    "gtf_contigs_within_fasta",
    "bed12_contigs_within_fasta",
    "star_agreement",
    "overall_status",
)
OUTPUT_SPECS = (
    ("artifacts", "reference_artifacts.tsv", ARTIFACT_HEADER, None),
    ("contigs", "reference_contigs.tsv", CONTIG_HEADER, None),
    ("summary", "reference_summary.tsv", SUMMARY_HEADER, 1),
)
CONTIG_ROLES = ("fasta", "fai", "dict", "gtf", "bed12", "star")
ROLES = {
    "fasta",
    "fai",
    "dict",
    "gtf",
    "bed12",
    "star_chr_name",
    "star_chr_length",
    "star_index_file",
}
SINGLETON_ROLES = {
    "fasta",
    "fai",
    "dict",
    "gtf",
    "bed12",
    "star_chr_name",
    "star_chr_length",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceError(report.ValidationError):
    pass


from norad.libraries.references import contigs as reference_contigs


@dataclass(frozen=True)
class Item:
    reference_id: str
    artifact_id: str
    role: str
    declared_path: str
    path: Path
    required: bool
    expected_sha256: str
    provenance_source: str
    provenance_release: str
    notes: str


@dataclass
class Observation:
    item: Item
    status: str
    digest: str = "NA"
    size: str = "NA"
    detail: str = ""


def fail(message: str) -> None:
    raise ProvenanceError(message)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument(
        "--base-dir",
        type=Path,
        required=True,
        help="Explicit base for relative inventory paths.",
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args(argv)


def load_inventory(path: Path, base_dir: Path) -> tuple[bytes, list[Item]]:
    raw = report.read_bytes(path, "Reference inventory")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"Reference inventory is not UTF-8: {exc}")
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != PROFILE_HEADER:
        fail("Reference inventory header must be exactly: " + "\t".join(PROFILE_HEADER))
    rows = list(reader)
    if not rows:
        fail("Reference inventory must contain data rows")
    if not base_dir.is_dir() or base_dir.is_symlink():
        fail(f"Reference base directory must be a real directory: {base_dir}")
    base = base_dir.resolve()
    items: list[Item] = []
    ids: set[str] = set()
    paths: set[Path] = set()
    role_counts: dict[str, int] = {}
    reference_id = ""
    for number, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            fail(f"Inventory row {number} has an invalid shape")
        if any(
            "\x00" in value or "\r" in value or "\n" in value for value in row.values()
        ):
            fail(f"Inventory row {number} contains unsafe characters")
        current_id = row["reference_id"]
        if not SAFE_ID.fullmatch(current_id):
            fail(f"Inventory row {number} has invalid reference_id")
        if reference_id and current_id != reference_id:
            fail("Reference inventory must describe exactly one reference_id")
        reference_id = current_id
        artifact_id = row["artifact_id"]
        if not SAFE_ID.fullmatch(artifact_id) or artifact_id in ids:
            fail(f"Inventory row {number} has invalid or duplicate artifact_id")
        ids.add(artifact_id)
        role = row["role"]
        if role not in ROLES:
            fail(f"Inventory row {number} has unsupported role: {role}")
        role_counts[role] = role_counts.get(role, 0) + 1
        required = row["required"]
        if required not in {"true", "false"}:
            fail(f"Inventory row {number} required must be true or false")
        declared = row["path"]
        if not declared or any(token in declared for token in ("*", "?", "[", "]")):
            fail(f"Inventory row {number} path must be explicit")
        declared_path = Path(declared)
        if ".." in declared_path.parts or "." in declared_path.parts:
            fail(f"Inventory row {number} path must not contain traversal components")
        resolved = (
            declared_path if declared_path.is_absolute() else (base / declared_path)
        )
        resolved = resolved.resolve()
        if resolved in paths:
            fail(f"Inventory row {number} resolves to a duplicate path")
        paths.add(resolved)
        expected = row["expected_sha256"]
        if expected != "NA" and not SHA256.fullmatch(expected):
            fail(
                f"Inventory row {number} expected_sha256 must be NA or lowercase SHA-256"
            )
        for field in ("provenance_source", "provenance_release", "notes"):
            if not row[field]:
                fail(f"Inventory row {number} {field} must be nonempty")
        items.append(
            Item(
                reference_id,
                artifact_id,
                role,
                declared,
                resolved,
                required == "true",
                expected,
                row["provenance_source"],
                row["provenance_release"],
                row["notes"],
            )
        )
    for role in SINGLETON_ROLES:
        if role_counts.get(role) != 1:
            fail(f"Reference inventory requires exactly one {role} row")
    if role_counts.get("star_index_file", 0) < 1:
        fail("Reference inventory requires at least one star_index_file row")
    return raw, items


def observe(items: Sequence[Item]) -> list[Observation]:
    observations: list[Observation] = []
    for item in items:
        try:
            metadata = item.path.lstat()
        except OSError as exc:
            status = "missing_required" if item.required else "missing_optional"
            observations.append(Observation(item, status, detail=report.clean(exc)))
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            observations.append(
                Observation(item, "invalid", detail="not a regular non-symlink file")
            )
            continue
        try:
            data = report.read_bytes(item.path, item.artifact_id)
        except (ProvenanceError, report.ValidationError) as exc:
            observations.append(Observation(item, "invalid", detail=report.clean(exc)))
            continue
        digest = hashlib.sha256(data).hexdigest()
        status = (
            "hash_mismatch"
            if item.expected_sha256 != "NA" and digest != item.expected_sha256
            else "present"
        )
        observations.append(
            Observation(item, status, digest, str(len(data)), item.notes)
        )
    return observations


def role_path(observations: Sequence[Observation], role: str) -> Path | None:
    for observation in observations:
        if observation.item.role == role and observation.status in {
            "present",
            "hash_mismatch",
        }:
            return observation.item.path
    return None


def parse_names(path: Path, label: str, column: int = 0) -> list[str]:
    names: list[str] = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) <= column or not fields[column]:
            fail(f"{label} row {number} is malformed")
        if fields[column] not in names:
            names.append(fields[column])
    if not names:
        fail(f"{label} has no contigs")
    return names


def parse_star(observations: Sequence[Observation]) -> list[tuple[str, int]]:
    names_path = role_path(observations, "star_chr_name")
    lengths_path = role_path(observations, "star_chr_length")
    if names_path is None or lengths_path is None:
        fail("STAR chrName/chrLength inputs are unavailable")
    names = [
        line.strip() for line in names_path.read_text().splitlines() if line.strip()
    ]
    lengths_text = [
        line.strip() for line in lengths_path.read_text().splitlines() if line.strip()
    ]
    if len(names) != len(lengths_text) or not names or len(set(names)) != len(names):
        fail("STAR chrName/chrLength rows do not reconcile")
    if any(not value.isdigit() for value in lengths_text):
        fail("STAR chrLength contains a non-integer")
    return list(zip(names, (int(value) for value in lengths_text), strict=True))


def collect_contigs(
    observations: Sequence[Observation],
) -> tuple[dict[str, list[tuple[str, int | None]]], dict[str, str]]:
    parsed: dict[str, list[tuple[str, int | None]]] = {}
    errors: dict[str, str] = {}
    parsers = {
        "fasta": reference_contigs.parse_fasta,
        "fai": reference_contigs.parse_fai,
        "dict": reference_contigs.parse_dict,
        "gtf": lambda p: [(name, None) for name in parse_names(p, "GTF")],
        "bed12": lambda p: [(name, None) for name in parse_names(p, "BED12")],
    }
    for role, parser in parsers.items():
        path = role_path(observations, role)
        if path is None:
            errors[role] = "source unavailable"
            continue
        try:
            parsed[role] = parser(path)
        except (
            OSError,
            UnicodeError,
            ProvenanceError,
            reference_contigs.ReferenceContigError,
        ) as exc:
            errors[role] = report.clean(exc)
    try:
        parsed["star"] = parse_star(observations)
    except (OSError, UnicodeError, ProvenanceError) as exc:
        errors["star"] = report.clean(exc)
    return parsed, errors


def agreement(parsed: dict[str, list[tuple[str, int | None]]], role: str) -> str:
    if "fasta" not in parsed or role not in parsed:
        return "not_checked"
    fasta = parsed["fasta"]
    other = parsed[role]
    if role in {"fai", "dict", "star"}:
        return "pass" if other == fasta else "fail"
    fasta_names = {name for name, _ in fasta}
    return "pass" if {name for name, _ in other} <= fasta_names else "fail"


def tsv(header: Iterable[str], rows: Iterable[Iterable[object]]) -> bytes:
    lines = ["\t".join(header)]
    lines.extend("\t".join(report.clean(value) for value in row) for row in rows)
    return ("\n".join(lines) + "\n").encode()


def render(raw_profile: bytes, observations: Sequence[Observation]) -> dict[str, bytes]:
    parsed, errors = collect_contigs(observations)
    reference_id = observations[0].item.reference_id
    artifact_rows = [
        (
            reference_id,
            o.item.artifact_id,
            o.item.role,
            o.item.declared_path,
            str(o.item.path),
            str(o.item.required).lower(),
            o.status,
            o.digest,
            o.item.expected_sha256,
            o.size,
            o.item.provenance_source,
            o.item.provenance_release,
            o.detail,
        )
        for o in observations
    ]
    contig_rows = []
    fasta_map = dict(parsed.get("fasta", []))
    for role in CONTIG_ROLES:
        for ordinal, (name, length) in enumerate(parsed.get(role, []), 1):
            status = (
                "reference"
                if role == "fasta"
                else (
                    "match"
                    if name in fasta_map
                    and (length is None or fasta_map[name] == length)
                    else "mismatch"
                )
            )
            contig_rows.append(
                (
                    reference_id,
                    role,
                    ordinal,
                    name,
                    "NA" if length is None else length,
                    status,
                    "",
                )
            )
        if role in errors:
            contig_rows.append(
                (reference_id, role, 0, "NA", "NA", "not_checked", errors[role])
            )
    agreements = {
        role: agreement(parsed, role)
        for role in CONTIG_ROLES[1:]
    }
    counts = {
        "required_missing": sum(o.status == "missing_required" for o in observations),
        "hash_mismatch": sum(o.status == "hash_mismatch" for o in observations),
        "invalid": sum(o.status == "invalid" for o in observations),
    }
    overall = "pass"
    if any(counts.values()) or any(value != "pass" for value in agreements.values()):
        overall = "fail"
    summary_row = (
        reference_id,
        hashlib.sha256(raw_profile).hexdigest(),
        len(observations),
        counts["required_missing"],
        counts["hash_mismatch"],
        counts["invalid"],
        len(parsed.get("fasta", [])),
        agreements["fai"],
        agreements["dict"],
        agreements["gtf"],
        agreements["bed12"],
        agreements["star"],
        overall,
    )
    return {
        "artifacts": tsv(ARTIFACT_HEADER, artifact_rows),
        "contigs": tsv(CONTIG_HEADER, contig_rows),
        "summary": tsv(SUMMARY_HEADER, [summary_row]),
    }


def validate_output(
    data: bytes, header: tuple[str, ...], rows: int | None = None
) -> None:
    reader = csv.DictReader(data.decode().splitlines(), delimiter="\t")
    if tuple(reader.fieldnames or ()) != header:
        fail("Generated reference output has invalid header")
    body = list(reader)
    if rows is not None and len(body) != rows:
        fail("Generated reference output has invalid row count")
    if any(None in row or any(value is None for value in row.values()) for row in body):
        fail("Generated reference output has invalid row shape")


def publish(output_root: Path, reference_id: str, outputs: dict[str, bytes]) -> None:
    if not output_root.exists() or output_root.is_symlink() or not output_root.is_dir():
        fail(f"Output root must be an existing real directory: {output_root}")
    destination = output_root / reference_id
    destination.mkdir(mode=0o755, exist_ok=True)
    if destination.is_symlink() or not destination.is_dir():
        fail(f"Reference output directory is unsafe: {destination}")
    finals = {
        key: destination / f"{reference_id}.{filename}"
        for key, filename, _header, _rows in OUTPUT_SPECS
    }
    present = [path.exists() for path in finals.values()]
    if any(present) and not all(present):
        fail("Existing reference provenance outputs are incomplete")
    lock = destination / f".{reference_id}.reference-provenance.lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        fail(f"Reference provenance lock already exists: {lock}")
    token = uuid.uuid4().hex
    staged = {
        key: destination / f".{reference_id}.{filename}.{token}.tmp"
        for key, filename, _header, _rows in OUTPUT_SPECS
    }
    backups = {
        key: destination / f".{reference_id}.{filename}.{token}.previous"
        for key, filename, _header, _rows in OUTPUT_SPECS
    }
    try:
        os.write(descriptor, f"pid={os.getpid()}\nrun_token={token}\n".encode())
        os.fsync(descriptor)
        if all(present):
            for key, _filename, header, expected_rows in OUTPUT_SPECS:
                validate_output(
                    report.read_bytes(finals[key], f"prior {key}"),
                    header,
                    expected_rows,
                )
        for key, _filename, *_rest in OUTPUT_SPECS:
            with staged[key].open("xb") as handle:
                handle.write(outputs[key])
                handle.flush()
                os.fsync(handle.fileno())
        for key, _filename, header, expected_rows in OUTPUT_SPECS:
            validate_output(
                report.read_bytes(staged[key], f"staged {key}"),
                header,
                expected_rows,
            )
        if all(present):
            for key, _filename, *_rest in OUTPUT_SPECS:
                os.replace(finals[key], backups[key])
        published: list[str] = []
        try:
            for key, _filename, *_rest in OUTPUT_SPECS:
                os.replace(staged[key], finals[key])
                published.append(key)
        except BaseException:
            for key in published:
                if finals[key].exists():
                    finals[key].unlink()
            for key in finals:
                if backups[key].exists():
                    os.replace(backups[key], finals[key])
            raise
        for path in backups.values():
            if path.exists():
                path.unlink()
    finally:
        for path in staged.values():
            if path.exists() and not path.is_symlink():
                path.unlink()
        os.close(descriptor)
        if lock.exists() and not lock.is_symlink():
            lock.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        raw, items = load_inventory(args.inventory, args.base_dir)
        observations = observe(items)
        outputs = render(raw, observations)
        for key, _filename, header, rows in OUTPUT_SPECS:
            validate_output(outputs[key], header, rows)
        reference_id = items[0].reference_id
        print(f"Reference inventory: {args.inventory}")
        print(f"Reference base directory: {args.base_dir}")
        print(f"Reference ID: {reference_id}")
        print(f"Output root: {args.output_root}")
        for observation in observations:
            print(f"{observation.item.artifact_id}: {observation.status}")
        print(
            "Evidence boundary: read-only provenance reconciliation; no files are repaired."
        )
        if not args.execute:
            print("Dry-run complete; no output was written.")
            return 0
        if (
            hashlib.sha256(
                report.read_bytes(args.inventory, "Reference inventory")
            ).digest()
            != hashlib.sha256(raw).digest()
        ):
            fail("Reference inventory changed after inspection")
        refreshed = observe(items)
        snapshots = [(item.status, item.digest, item.size) for item in observations]
        refreshed_snapshots = [
            (item.status, item.digest, item.size) for item in refreshed
        ]
        if refreshed_snapshots != snapshots:
            fail("A reference artifact changed after inspection")
        publish(args.output_root, reference_id, outputs)
        print(f"Published reference provenance: {args.output_root / reference_id}")
        return 0
    except ProvenanceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except report.ValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
