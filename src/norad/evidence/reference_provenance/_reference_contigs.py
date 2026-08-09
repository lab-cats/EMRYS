"""Reference artifact observation and contig reconciliation."""

from __future__ import annotations

import hashlib
import stat
from collections.abc import Sequence
from pathlib import Path

from norad.evidence.reference_provenance._reference_model import (
    Item,
    Observation,
    ProvenanceError,
    fail,
)
from norad.libraries import validation as report
from norad.libraries.references import contigs as reference_contigs


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
