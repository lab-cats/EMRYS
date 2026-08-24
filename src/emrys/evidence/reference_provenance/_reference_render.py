"""Deterministic reference-provenance output rendering."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence

from emrys.evidence.reference_provenance._reference_contigs import (
    agreement,
    collect_contigs,
)
from emrys.evidence.reference_provenance._reference_model import (
    ARTIFACT_HEADER,
    CONTIG_HEADER,
    CONTIG_ROLES,
    SUMMARY_HEADER,
    Observation,
)
from emrys.libraries import validation as report


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
    agreements = {role: agreement(parsed, role) for role in CONTIG_ROLES[1:]}
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
