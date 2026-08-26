#!/usr/bin/env python3
"""Compare retained Step 07/08 owners at ``origin/master`` and ``HEAD``.

This CI-only helper consumes a successful retained 100,000-read-pair E2E.  It
creates deterministic external fixtures, materializes the two committed source
trees with ``git archive``, and delegates paired timing to
``scripts/benchmark_stage_resources.py``.  Planning is the default and writes
nothing; ``--execute`` is required for every mutation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import io
import json
import os
import stat
import subprocess
import sys
import tarfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SUMMARY_SCHEMA = "emrys.retained-stage-benchmark-summary.v2"
E2E_SCHEMA = "emrys.ci-real-synthetic-e2e-summary.v2"
COMPARISON_SCHEMA = "emrys.resource-benchmark.v2"
STEP08_FIXTURE_SCHEMA = "emrys.retained-step08-fixture.v1"
BASELINE_REF = "origin/master"
EXPECTED_READ_PAIRS = 100_000
EXPECTED_CONTIG_LENGTH = 5_000_000
MEASURED_REPETITIONS = 4
WARMUP_REPETITIONS = 1
DEFAULT_SUITE = "cohort-stages"
VARIANTS = ("master", "head")
BCFTOOLS_METADATA_PREFIXES = (
    b"##bcftoolsVersion=",
    b"##bcftoolsCommand=",
    b"##bcftools_filterVersion=",
    b"##bcftools_filterCommand=",
)
COMPARISON_SUMMARY_FIELDS = (
    "case",
    "value",
    "baseline_variant",
    "variant",
    "required_repetitions",
    "successful_repetitions",
    "paired_repetitions",
    "warmups_valid",
    "comparison_valid",
    "artifact_parity",
    "median_wall_seconds",
    "wall_mad_seconds",
    "wall_range_seconds",
    "median_cpu_seconds",
    "median_max_rss_kib",
    "median_input_blocks",
    "median_output_blocks",
    "median_paired_speedup_percent",
    "median_paired_speedup_ratio",
)


class BenchmarkSetupError(RuntimeError):
    """The retained evidence or benchmark boundary is not admissible."""


@dataclass(frozen=True, slots=True)
class RetainedCase:
    name: str
    suite: str
    stage: int
    values: tuple[int, ...]
    threads: int


RETAINED_CASES = (
    RetainedCase("alignment-signatures-mib", "identity", 0, (10, 100, 1024), 1),
    RetainedCase("step07-partitions", "cohort-stages", 7, (1, 5, 25), 2),
    RetainedCase("step08-reread", "cohort-stages", 8, (10_000, 100_000), 1),
    RetainedCase("step08-skew", "cohort-stages", 8, (100_000,), 2),
    RetainedCase("step08-uniform", "cohort-stages", 8, (100_000,), 2),
)
RETAINED_CASE_BY_NAME = {case.name: case for case in RETAINED_CASES}
RETAINED_CASE_NAMES = tuple(case.name for case in RETAINED_CASES)
RETAINED_SUITES = tuple(dict.fromkeys(case.suite for case in RETAINED_CASES))


@dataclass(frozen=True, slots=True)
class AdmittedE2E:
    summary_path: Path
    summary_sha256: str
    run_root: Path
    cohort_id: str
    sample_manifest: Path
    reference_fasta: Path
    annotation_gtf: Path
    orientation_root: Path
    retained_primary_vcf: Path


@dataclass(frozen=True, slots=True)
class RepositoryState:
    root: Path
    python: Path
    baseline_commit: str
    head_commit: str


def _sha256_file(path: Path) -> str:
    before = path.stat(follow_symlinks=False)
    if path.is_symlink() or not stat.S_ISREG(before.st_mode):
        raise BenchmarkSetupError(f"required artifact must be one real file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = path.stat(follow_symlinks=False)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise BenchmarkSetupError(f"artifact changed while hashing: {path}")
    return digest.hexdigest()


def _real_directory(path: Path, label: str) -> Path:
    authored = Path(os.path.abspath(path))
    try:
        state = authored.lstat()
        resolved = authored.resolve(strict=True)
    except OSError as exc:
        raise BenchmarkSetupError(f"{label} is unavailable: {authored}: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode) or resolved != authored:
        raise BenchmarkSetupError(f"{label} must be one canonical real directory: {authored}")
    return authored


def _real_file(path: Path, label: str, *, executable: bool = False) -> Path:
    authored = Path(os.path.abspath(path))
    try:
        state = authored.lstat()
        resolved = authored.resolve(strict=True)
        target = resolved.stat()
    except OSError as exc:
        raise BenchmarkSetupError(f"{label} is unavailable: {authored}: {exc}") from exc
    if stat.S_ISLNK(state.st_mode) and not executable:
        raise BenchmarkSetupError(f"{label} must be one real file, not a symlink: {path}")
    if not stat.S_ISREG(target.st_mode) or (executable and not os.access(resolved, os.X_OK)):
        requirement = "an executable real file" if executable else "one real file"
        raise BenchmarkSetupError(f"{label} must resolve to {requirement}: {path}")
    return authored


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    admitted = _real_file(path, label)
    try:
        value = json.loads(admitted.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BenchmarkSetupError(f"{label} is not readable JSON: {exc}") from exc
    if not isinstance(value, Mapping):
        raise BenchmarkSetupError(f"{label} must contain one JSON object")
    return value


def _verify_artifact(record: Any, label: str) -> None:
    if not isinstance(record, Mapping) or set(record) != {"path", "size_bytes", "sha256"}:
        raise BenchmarkSetupError(f"{label} is not one exact artifact record")
    path = _real_file(Path(str(record["path"])), label)
    if path.stat().st_size != record["size_bytes"] or _sha256_file(path) != record["sha256"]:
        raise BenchmarkSetupError(f"{label} no longer matches its retained identity")


def _admit_e2e(summary_path: Path) -> AdmittedE2E:
    path = _real_file(summary_path, "retained 100k E2E summary")
    summary = _load_json(path, "retained 100k E2E summary")
    if (
        summary.get("schema_version") != E2E_SCHEMA
        or summary.get("status") != "passed"
        or str(summary.get("profile")) != "100000"
        or summary.get("dataset_profile") != "production-like-v1"
        or summary.get("fixture_id") != "deterministic-production-like-v1"
        or summary.get("read_pairs_per_library") != EXPECTED_READ_PAIRS
        or summary.get("biological_interpretation_claimed") is not False
    ):
        raise BenchmarkSetupError("summary is not the exact passed retained 100k profile")
    operator_root = _real_directory(Path(str(summary.get("operator_root"))), "retained operator root")
    if path != operator_root / "e2e-summary.json":
        raise BenchmarkSetupError("summary path is not the retained operator-root summary")
    completion = summary.get("completion")
    if (
        not isinstance(completion, Mapping)
        or completion.get("state") != "local_pipeline_complete"
        or completion.get("verified_owner_jobs") != 35
        or completion.get("step10_verified") is not True
    ):
        raise BenchmarkSetupError("retained completion boundary is incomplete")
    run_root = _real_directory(Path(str(completion.get("run_root"))), "retained run root")
    expected_runs = operator_root / "workspace" / "runs"
    if run_root.parent != expected_runs or run_root.name != completion.get("run_id"):
        raise BenchmarkSetupError("retained run root does not match its summary identity")
    records = completion.get("verified_owner_records")
    if not isinstance(records, list) or len(records) != 35:
        raise BenchmarkSetupError("retained summary does not contain 35 owner records")
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise BenchmarkSetupError(f"owner record {index} is invalid")
        _verify_artifact(
            {key: record.get(key) for key in ("path", "size_bytes", "sha256")},
            f"retained owner record {index + 1}",
        )
    artifacts = completion.get("artifacts")
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise BenchmarkSetupError("retained completion artifacts are absent")
    for name, record in artifacts.items():
        _verify_artifact(record, f"retained completion artifact {name}")
    runtime_profile = summary.get("runtime_profile")
    _verify_artifact(runtime_profile, "retained runtime profile")
    if not isinstance(runtime_profile, Mapping) or Path(str(runtime_profile["path"])) != operator_root / "runtime.selected.tsv":
        raise BenchmarkSetupError("retained runtime profile path differs")

    execution = _load_json(run_root / "contract/normalized.json", "normalized execution")
    try:
        cohort_id = str(execution["analysis"]["cohort_id"])
        sample_manifest = Path(str(execution["samples"]["manifest"]["path"]))
        partition_manifest = Path(str(execution["partitions"]["manifest"]["path"]))
        partitions = execution["partitions"]["rows"]
        reference_fasta = Path(str(execution["reference"]["fasta"]["path"]))
        annotation_gtf = Path(str(execution["reference"]["gtf"]["path"]))
    except (KeyError, TypeError) as exc:
        raise BenchmarkSetupError("normalized execution omits required Step 07/08 inputs") from exc
    synthetic_inputs = operator_root / "synthetic-inputs"
    if (
        sample_manifest != synthetic_inputs / "samples.tsv"
        or partition_manifest != synthetic_inputs / "partitions.tsv"
        or reference_fasta != synthetic_inputs / "inputs/reference/reference.fa"
        or annotation_gtf != synthetic_inputs / "inputs/reference/genes.gtf"
        or not isinstance(partitions, list)
        or len(partitions) != 1
        or not isinstance(partitions[0], Mapping)
        or partitions[0].get("partition_id") != "primary"
    ):
        raise BenchmarkSetupError("normalized execution differs from exact synthetic 100k inputs")
    for selected, label in (
        (sample_manifest, "sample manifest"),
        (partition_manifest, "partition manifest"),
        (reference_fasta, "reference FASTA"),
        (reference_fasta.with_name(reference_fasta.name + ".fai"), "reference FAI"),
        (annotation_gtf, "annotation GTF"),
    ):
        _real_file(selected, label)
    orientation_root = _real_directory(run_root / "results/orientation", "retained orientation root")
    retained_step07_root = _real_directory(run_root / "results/mpileup", "retained Step 07 root")
    retained_primary_vcf = _real_file(
        retained_step07_root
        / cohort_id
        / "primary"
        / f"{cohort_id}.primary.FWD_like.mpileup.vcf",
        "retained primary FWD_like VCF",
    )
    return AdmittedE2E(
        path,
        _sha256_file(path),
        run_root,
        cohort_id,
        sample_manifest,
        reference_fasta,
        annotation_gtf,
        orientation_root,
        retained_primary_vcf,
    )


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _commit(value: bytes, label: str) -> str:
    text = value.decode("ascii").strip()
    if len(text) != 40 or any(character not in "0123456789abcdef" for character in text):
        raise BenchmarkSetupError(f"{label} is not one full commit identity")
    return text


def _admit_repository(repo_root: Path) -> RepositoryState:
    root = _real_directory(repo_root, "repository root")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise BenchmarkSetupError("repository must be completely clean for benchmarking")
    baseline = _commit(_git(root, "rev-parse", f"{BASELINE_REF}^{{commit}}").stdout, BASELINE_REF)
    head = _commit(_git(root, "rev-parse", "HEAD^{commit}").stdout, "HEAD")
    ancestor = _git(root, "merge-base", "--is-ancestor", baseline, head, check=False)
    if ancestor.returncode != 0:
        raise BenchmarkSetupError(f"{BASELINE_REF} is not an ancestor of HEAD")
    for lockfile in (
        "uv.lock",
        "renv.lock",
        ".github/ci/real-tools.conda-lock.yml",
    ):
        baseline_lock = _git(root, "show", f"{baseline}:{lockfile}").stdout
        head_lock = _git(root, "show", f"{head}:{lockfile}").stdout
        if not baseline_lock or baseline_lock != head_lock:
            raise BenchmarkSetupError(
                f"origin/master and HEAD must have the same nonempty {lockfile}"
            )
    python = _real_file(root / ".venv/bin/python", "locked workflow Python", executable=True)
    return RepositoryState(root, python, baseline, head)


def _partition_rows(count: int, contig: str, length: int) -> list[tuple[str, str, str]]:
    if count < 1 or length != EXPECTED_CONTIG_LENGTH or count > length:
        raise BenchmarkSetupError("partition fixture requires 1..5,000,000 pieces over 5Mb")
    rows = []
    for index in range(count):
        start = index * length // count + 1
        end = (index + 1) * length // count
        rows.append((f"p{index + 1:02d}", "region", f"{contig}:{start}-{end}"))
    return rows


def _step08_counts(case: str, total: int) -> tuple[int, ...]:
    if total not in {10_000, 100_000}:
        raise BenchmarkSetupError("Step 08 fixtures support only 10k or 100k rows")
    if case == "step08-reread":
        return (total // 2, total - total // 2)
    if total != 100_000:
        raise BenchmarkSetupError("Step 08 scheduling fixtures require 100k rows")
    if case == "step08-uniform":
        return (6_250,) * 16
    if case == "step08-skew":
        return tuple(12_000 if index % 2 == 0 else 500 for index in range(16))
    raise BenchmarkSetupError(f"unknown Step 08 case: {case}")


def _write_tsv(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _fasta(path: Path) -> tuple[str, str]:
    contig = ""
    sequence: list[str] = []
    for line in path.read_text(encoding="ascii").splitlines():
        if line.startswith(">"):
            if contig:
                raise BenchmarkSetupError("benchmark reference must contain one contig")
            contig = line[1:].split()[0]
        elif line:
            sequence.append(line.strip().upper())
    joined = "".join(sequence)
    if not contig or len(joined) != EXPECTED_CONTIG_LENGTH or set(joined) - set("ACGT"):
        raise BenchmarkSetupError("retained 100k reference is not the expected 5Mb contig")
    return contig, joined


def _vcf_template(path: Path) -> tuple[list[bytes], list[bytes]]:
    header: list[bytes] = []
    for line in _real_file(path, "retained primary VCF").read_bytes().splitlines(keepends=True):
        if line.startswith(b"#"):
            header.append(line)
            continue
        fields = line.rstrip(b"\n").split(b"\t")
        alternates = fields[4].split(b",") if len(fields) >= 5 else []
        if (
            len(fields) >= 10
            and len(fields[3]) == 1
            and fields[3] in b"ACGT"
            and len(alternates) == 2
            and len(alternates[0]) == 1
            and alternates[0] in b"ACGT"
            and alternates[0] != fields[3]
            and alternates[1] == b"<*>"
        ):
            return header, fields
    raise BenchmarkSetupError(
        "retained primary VCF contains no concrete-SNV plus <*> template"
    )


def _write_vcf(
    path: Path,
    header: Sequence[bytes],
    template: Sequence[bytes],
    contig: str,
    sequence: str,
    count: int,
    start: int,
) -> None:
    alternatives = {"A": "G", "C": "T", "G": "A", "T": "C"}
    if count < 0 or start < 1 or start + count - 1 > len(sequence):
        raise BenchmarkSetupError("synthetic VCF records exceed the declared contig")
    with path.open("xb") as stream:
        stream.writelines(header)
        for position in range(start, start + count):
            fields = list(template)
            reference = sequence[position - 1]
            fields[0] = contig.encode("ascii")
            fields[1] = str(position).encode("ascii")
            fields[2] = b"."
            fields[3] = reference.encode("ascii")
            fields[4] = alternatives[reference].encode("ascii") + b",<*>"
            stream.write(b"\t".join(fields) + b"\n")


def _step08_fixture_path(trial: Path, case: str, value: int) -> Path:
    """Derive one case/value fixture shared by every warmup and repetition."""

    selected = _real_directory(trial, "benchmark trial")
    variant = selected.name
    repetition = _real_directory(selected.parent, "benchmark repetition")
    value_root = _real_directory(repetition.parent, "benchmark value root")
    case_root = _real_directory(value_root.parent, "benchmark case root")
    kind_root = _real_directory(case_root.parent, "benchmark trial-kind root")
    results_root = _real_directory(kind_root.parent, "benchmark results root")
    if (
        variant not in VARIANTS
        or len(repetition.name) != 6
        or not repetition.name.startswith("rep-")
        or not repetition.name[4:].isdigit()
        or int(repetition.name[4:]) < 1
        or value_root.name != str(value)
        or case_root.name != case
        or kind_root.name not in {"warmups", "trials"}
    ):
        raise BenchmarkSetupError("Step 08 trial path does not match benchmark anatomy")
    return results_root / "fixtures" / case / str(value)


def _mkdir_real(path: Path, label: str) -> Path:
    if path.exists() or path.is_symlink():
        return _real_directory(path, label)
    try:
        path.mkdir(mode=0o700)
    except OSError as exc:
        raise BenchmarkSetupError(f"could not create {label}: {path}: {exc}") from exc
    return _real_directory(path, label)


def _step08_member_roster(cohort: str, counts: Sequence[int]) -> tuple[str, ...]:
    members = ["partitions.tsv"]
    for index in range(len(counts) // 2):
        partition = f"p{index + 1:02d}"
        root = f"step07/{cohort}/{partition}"
        members.extend(
            (
                f"{root}/{cohort}.{partition}.FWD_like.mpileup.vcf",
                f"{root}/{cohort}.{partition}.REV_like.mpileup.vcf",
                f"{root}/{cohort}.{partition}.step07_outputs.tsv",
            )
        )
    return tuple(members)


def _step08_fixture_identity(
    context: Mapping[str, Any], case: str, total: int, counts: Sequence[int]
) -> dict[str, Any]:
    return {
        "schema_version": STEP08_FIXTURE_SCHEMA,
        "case": case,
        "value": total,
        "cohort_id": str(context["cohort_id"]),
        "counts": list(counts),
        "sample_manifest_sha256": _sha256_file(Path(str(context["sample_manifest"]))),
        "reference_fasta_sha256": _sha256_file(Path(str(context["reference_fasta"]))),
        "retained_primary_vcf_sha256": _sha256_file(
            Path(str(context["retained_primary_vcf"]))
        ),
        "expected_vcf_record_count": total,
        "expected_supported_candidate_count": total,
        "expected_symbolic_alt_count": total,
    }


def _expected_step08_directories(members: Iterable[str]) -> set[str]:
    expected: set[str] = set()
    for member in members:
        parent = PurePosixPath(member).parent
        while parent != PurePosixPath("."):
            expected.add(parent.as_posix())
            parent = parent.parent
    return expected


def _admit_step08_fixture(
    context: Mapping[str, Any], fixture: Path, case: str, total: int
) -> Path:
    admitted = _real_directory(fixture, "shared Step 08 fixture")
    counts = _step08_counts(case, total)
    identity = _step08_fixture_identity(context, case, total, counts)
    document = _load_json(admitted / "fixture.json", "shared Step 08 fixture marker")
    if set(document) != {*identity, "members"} or any(
        document.get(key) != value for key, value in identity.items()
    ):
        raise BenchmarkSetupError("shared Step 08 fixture identity differs")
    members = document.get("members")
    roster = set(_step08_member_roster(str(context["cohort_id"]), counts))
    if not isinstance(members, Mapping) or set(members) != roster:
        raise BenchmarkSetupError("shared Step 08 fixture member roster differs")

    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for current, directories, files in os.walk(admitted, followlinks=False):
        root = Path(current)
        for name in directories:
            child = root / name
            state = child.lstat()
            if stat.S_ISLNK(state.st_mode) or not stat.S_ISDIR(state.st_mode):
                raise BenchmarkSetupError(f"shared Step 08 fixture has unsafe directory: {child}")
            actual_directories.add(child.relative_to(admitted).as_posix())
        for name in files:
            child = root / name
            state = child.lstat()
            if stat.S_ISLNK(state.st_mode) or not stat.S_ISREG(state.st_mode):
                raise BenchmarkSetupError(f"shared Step 08 fixture has unsafe file: {child}")
            actual_files.add(child.relative_to(admitted).as_posix())
    if actual_files != roster | {"fixture.json"} or actual_directories != _expected_step08_directories(roster):
        raise BenchmarkSetupError("shared Step 08 fixture filesystem roster differs")

    for relative in sorted(roster):
        record = members[relative]
        selected = admitted / relative
        if (
            not isinstance(record, Mapping)
            or set(record) != {"size_bytes", "sha256"}
            or isinstance(record["size_bytes"], bool)
            or not isinstance(record["size_bytes"], int)
            or record["size_bytes"] < 0
            or not isinstance(record["sha256"], str)
            or len(record["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in record["sha256"])
            or selected.stat().st_size != record["size_bytes"]
            or _sha256_file(selected) != record["sha256"]
        ):
            raise BenchmarkSetupError(f"shared Step 08 fixture member differs: {relative}")
    return admitted


def _setup_step07(context: Mapping[str, Any], trial: Path, partitions: int) -> None:
    fixture = trial / "fixture"
    fixture.mkdir(mode=0o700)
    contig, _sequence = _fasta(Path(str(context["reference_fasta"])))
    rows = _partition_rows(partitions, contig, EXPECTED_CONTIG_LENGTH)
    _write_tsv(
        fixture / "partitions.tsv",
        ("partition_id", "selector_type", "selector_value"),
        rows,
    )


def _setup_step08(context: Mapping[str, Any], trial: Path, case: str, total: int) -> None:
    fixture = _step08_fixture_path(trial, case, total)
    counts = _step08_counts(case, total)
    if fixture.exists() or fixture.is_symlink():
        _admit_step08_fixture(context, fixture, case, total)
        return
    fixtures = _mkdir_real(fixture.parent.parent, "Step 08 fixture collection")
    _mkdir_real(fixtures / case, "Step 08 case fixture collection")
    fixture.mkdir(mode=0o700)
    contig, sequence = _fasta(Path(str(context["reference_fasta"])))
    header, template = _vcf_template(Path(str(context["retained_primary_vcf"])))
    partition_count = len(counts) // 2
    rows = _partition_rows(partition_count, contig, EXPECTED_CONTIG_LENGTH)
    manifest = fixture / "partitions.tsv"
    _write_tsv(manifest, ("partition_id", "selector_type", "selector_value"), rows)
    cohort = str(context["cohort_id"])
    sample_manifest = Path(str(context["sample_manifest"]))
    sample_hash = _sha256_file(sample_manifest)
    partition_hash = _sha256_file(manifest)
    step07_root = fixture / "step07"
    receipt_header = (
        "cohort_id", "partition_id", "selector_type", "selector_value",
        "orientation", "vcf_path", "sample_manifest_sha256",
        "partition_manifest_sha256", "sample_count", "vcf_record_count",
    )
    sample_count = len(sample_manifest.read_text(encoding="utf-8").splitlines()) - 1
    for partition_index, row in enumerate(rows):
        partition_id, selector_type, selector_value = row
        interval = selector_value.split(":", 1)[1]
        start = int(interval.split("-", 1)[0])
        root = step07_root / cohort / partition_id
        root.mkdir(mode=0o700, parents=True)
        receipt_rows = []
        for orientation_index, orientation in enumerate(("FWD_like", "REV_like")):
            count = counts[partition_index * 2 + orientation_index]
            vcf = root / f"{cohort}.{partition_id}.{orientation}.mpileup.vcf"
            _write_vcf(vcf, header, template, contig, sequence, count, start)
            receipt_rows.append(
                (
                    cohort, partition_id, selector_type, selector_value, orientation,
                    vcf.relative_to(fixture).as_posix(),
                    sample_hash,
                    partition_hash,
                    sample_count,
                    count,
                )
            )
        _write_tsv(root / f"{cohort}.{partition_id}.step07_outputs.tsv", receipt_header, receipt_rows)
    roster = _step08_member_roster(cohort, counts)
    members = {
        relative: {
            "size_bytes": (fixture / relative).stat().st_size,
            "sha256": _sha256_file(fixture / relative),
        }
        for relative in roster
    }
    _write_json(
        fixture / "fixture.json",
        {**_step08_fixture_identity(context, case, total, counts), "members": members},
    )
    _admit_step08_fixture(context, fixture, case, total)


def _load_context(path: Path) -> Mapping[str, Any]:
    return _load_json(path, "retained benchmark context")


def _source(context: Mapping[str, Any], variant: str) -> Path:
    if variant not in VARIANTS:
        raise BenchmarkSetupError(f"unknown benchmark variant: {variant}")
    sources = context.get("sources")
    if not isinstance(sources, Mapping):
        raise BenchmarkSetupError("benchmark context omits source roots")
    return _real_directory(Path(str(sources[variant])), f"{variant} source archive")


def _run_checked(
    argv: Sequence[str], *, cwd: Path, environment: Mapping[str, str] | None = None
) -> None:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=None if environment is None else dict(environment),
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        raise BenchmarkSetupError(f"command exited {completed.returncode}: {' '.join(argv)}")


def _produce_step07(context: Mapping[str, Any], trial: Path, source: Path) -> None:
    from emrys.libraries.process_environment import sanitized_subprocess_environment

    repo = _real_directory(Path(str(context["repo_root"])), "repository root")
    fixture = _real_directory(trial / "fixture", "Step 07 fixture")
    with (fixture / "partitions.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, dialect="excel-tab"))
    output = trial / "output"
    runtime = _real_directory(Path(str(context["runtime_prefix"])), "runtime prefix")
    environment = sanitized_subprocess_environment(os.environ)
    environment.update(
        {
            "EMRYS_SHA256_PYTHON": str(context["python"]),
            "EMRYS_REQUIRE_BOUND_SHA256": "1",
        }
    )
    for row in rows:
        _run_checked(
            (
                "bash",
                str(source / "src/emrys/stages/partitioned_cohort_mpileup/step_07_bcftools_mpileup_by_chrom_and_strand.sh"),
                "--cohort-id", str(context["cohort_id"]),
                "--sample-manifest", str(context["sample_manifest"]),
                "--partition-manifest", str(fixture / "partitions.tsv"),
                "--partition-id", row["partition_id"],
                "--orientation-root", str(context["orientation_root"]),
                "--reference-fasta", str(context["reference_fasta"]),
                "--output-root", str(output),
                "--bcftools-bin", str(runtime / "bin/bcftools"),
                "--no-clobber", "--execute",
            ),
            cwd=repo,
            environment=environment,
        )


def _produce_step08(
    context: Mapping[str, Any], trial: Path, source: Path, case: str, total: int, threads: int
) -> None:
    from emrys.libraries.process_environment import guarded_r_environment

    fixture = _real_directory(
        _step08_fixture_path(trial, case, total), "shared Step 08 fixture"
    )
    environment = guarded_r_environment(
        source,
        Path(str(context["renv_library"])),
        base_environment=os.environ,
    )
    environment.update(
        {
            "EMRYS_SHA256_PYTHON": str(context["python"]),
            "EMRYS_REQUIRE_BOUND_SHA256": "1",
        }
    )
    _run_checked(
        (
            "bash",
            str(source / "src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.sh"),
            "--cohort-id", str(context["cohort_id"]),
            "--sample-manifest", str(context["sample_manifest"]),
            "--partition-manifest", str(fixture / "partitions.tsv"),
            "--step07-root", "step07",
            "--annotation-gtf", str(context["annotation_gtf"]),
            "--output-root", str(trial / "output"),
            "--qc-root", str(trial / "qc"),
            "--threads", str(threads),
            "--rscript-bin", str(context["rscript"]),
            "--r-script", str(source / "src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R"),
            "--no-clobber", "--execute",
        ),
        cwd=fixture,
        environment=environment,
    )


def _emrys(context: Mapping[str, Any], *arguments: str) -> tuple[str, ...]:
    return (
        str(context["python"]), "-X", "pycache_prefix=/dev/null", "-I", "-m", "emrys", *arguments,
    )


def _write_bundle(path: Path, members: Iterable[tuple[str, bytes]]) -> None:
    with path.open("xb") as stream:
        for name, data in members:
            encoded = name.encode("utf-8")
            stream.write(len(encoded).to_bytes(4, "big") + encoded)
            stream.write(len(data).to_bytes(8, "big") + data)


def _normalize_step07(data: bytes, trial: Path) -> bytes:
    root = str(trial).encode()
    return b"".join(
        line.replace(root, b"<TRIAL_ROOT>")
        for line in data.splitlines(keepends=True)
        if not line.startswith(BCFTOOLS_METADATA_PREFIXES)
    )


def _validate_step07(context: Mapping[str, Any], trial: Path) -> None:
    repo = _real_directory(Path(str(context["repo_root"])), "repository root")
    cohort = str(context["cohort_id"])
    fixture = trial / "fixture"
    output = trial / "output"
    reference_fai = f"{context['reference_fasta']}.fai"
    members: list[tuple[str, bytes]] = []
    with (fixture / "partitions.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, dialect="excel-tab"))
    for row in rows:
        partition = row["partition_id"]
        root = output / cohort / partition
        fwd = root / f"{cohort}.{partition}.FWD_like.mpileup.vcf"
        rev = root / f"{cohort}.{partition}.REV_like.mpileup.vcf"
        receipt = root / f"{cohort}.{partition}.step07_outputs.tsv"
        report = root / f"{cohort}.{partition}.step07_validation.tsv"
        owner = _emrys(
            context, "validate", "partitioned-cohort-mpileup",
            "--cohort-id", cohort, "--partition-id", partition,
            "--sample-manifest", str(context["sample_manifest"]),
            "--partition-manifest", str(fixture / "partitions.tsv"),
            "--reference-fai", reference_fai, "--fwd-vcf", str(fwd),
            "--rev-vcf", str(rev), "--receipt", str(receipt), "--output", str(report),
            "--execute",
        )
        _run_checked(owner, cwd=repo)
        _run_checked(_emrys(context, "validate", "all-pass", "--report", str(report), "--step-id", "07", "--scope-id", f"{cohort}__{partition}"), cwd=repo)
        for label, selected in (("fwd", fwd), ("rev", rev), ("receipt", receipt)):
            members.append((f"{partition}/{label}", _normalize_step07(selected.read_bytes(), trial)))
    _write_bundle(trial / "parity.bin", members)


def _validate_step08(
    context: Mapping[str, Any], trial: Path, case: str, total: int
) -> None:
    fixture = _admit_step08_fixture(
        context, _step08_fixture_path(trial, case, total), case, total
    )
    cohort = str(context["cohort_id"])
    sites = trial / "output" / cohort / f"{cohort}.step08_sites.tsv"
    inputs = trial / "output" / cohort / f"{cohort}.step08_inputs.tsv"
    summary = trial / "qc" / f"{cohort}.step08_summary.tsv"
    report = trial / "qc" / f"{cohort}.step08_validation.tsv"
    owner = _emrys(
        context, "validate", "cohort-candidate-preprocessing",
        "--cohort-id", cohort, "--sample-manifest", str(context["sample_manifest"]),
        "--partition-manifest", str(fixture / "partitions.tsv"),
        "--annotation-gtf", str(context["annotation_gtf"]),
        "--sites", str(sites), "--inputs", str(inputs), "--summary", str(summary),
        "--output", str(report), "--execute",
    )
    _run_checked(owner, cwd=fixture)
    _run_checked(_emrys(context, "validate", "all-pass", "--report", str(report), "--step-id", "08", "--scope-id", cohort), cwd=fixture)
    _write_bundle(
        trial / "parity.bin",
        (("sites", sites.read_bytes()), ("inputs", inputs.read_bytes()), ("summary", summary.read_bytes())),
    )


def _case_threads(case: str) -> int:
    return RETAINED_CASE_BY_NAME[case].threads


def _setup_alignment_signatures(trial: Path, size_mib: int) -> None:
    retained = RETAINED_CASE_BY_NAME["alignment-signatures-mib"]
    if size_mib not in retained.values:
        raise BenchmarkSetupError("alignment signature size is not registered")
    size_bytes = size_mib * 1024 * 1024
    for name, magic in (
        ("input.bam", b"\x1f\x8b\x08\x04"),
        ("input.bam.bai", b"BAI\x01"),
    ):
        with (trial / name).open("xb") as stream:
            stream.write(magic)
            stream.truncate(size_bytes)


def _produce_alignment_signatures(trial: Path, source: Path) -> None:
    loaded = tuple(
        name for name in sys.modules if name == "emrys" or name.startswith("emrys.")
    )
    if loaded:
        raise BenchmarkSetupError(
            "alignment signature producer imported EMRYS before source binding"
        )
    source_root = _real_directory(source / "src", "variant Python source root")
    sys.path.insert(0, str(source_root))
    try:
        module = importlib.import_module("emrys.libraries.alignments.bam")
    finally:
        sys.path.pop(0)
    expected_module = (
        source_root / "emrys/libraries/alignments/bam.py"
    ).resolve(strict=True)
    observed_module = Path(str(module.__file__)).resolve(strict=True)
    if observed_module != expected_module:
        raise BenchmarkSetupError(
            f"alignment signature producer imported foreign source: {observed_module}"
        )
    valid, bam_magic, bai_magic = module.validate_bam_bai_pair(
        trial / "input.bam", trial / "input.bam.bai"
    )
    if not valid:
        raise BenchmarkSetupError("alignment signature fixture failed validation")
    with (trial / "observed.bin").open("xb") as stream:
        stream.write(bam_magic + bai_magic)


def _validate_alignment_signatures(trial: Path) -> None:
    expected = b"\x1f\x8b\x08\x04BAI\x01"
    observed = _real_file(
        trial / "observed.bin", "alignment signature observation"
    ).read_bytes()
    if observed != expected:
        raise BenchmarkSetupError("alignment signature observation differs")
    with (trial / "parity.bin").open("xb") as stream:
        stream.write(expected)


def _select_cases(
    *, suite: str | None, names: Sequence[str] | None
) -> tuple[RetainedCase, ...]:
    requested = tuple(names or ())
    if suite is not None and requested:
        raise BenchmarkSetupError("--suite and --case are mutually exclusive")
    if len(requested) != len(set(requested)):
        raise BenchmarkSetupError("each retained benchmark case may be selected once")
    if requested:
        unknown = set(requested).difference(RETAINED_CASE_BY_NAME)
        if unknown:
            raise BenchmarkSetupError(
                "unknown retained benchmark case: " + ", ".join(sorted(unknown))
            )
        selected = tuple(case for case in RETAINED_CASES if case.name in requested)
    else:
        selected_suite = suite or DEFAULT_SUITE
        if selected_suite == "all":
            selected = RETAINED_CASES
        elif selected_suite in RETAINED_SUITES:
            selected = tuple(
                case for case in RETAINED_CASES if case.suite == selected_suite
            )
        else:
            raise BenchmarkSetupError(
                f"unknown retained benchmark suite: {selected_suite}"
            )
    if not selected:
        raise BenchmarkSetupError("retained benchmark selection is empty")
    return selected


def _internal(arguments: argparse.Namespace) -> int:
    context = _load_context(arguments.context)
    trial = Path(os.path.abspath(arguments.trial_dir))
    retained_case = RETAINED_CASE_BY_NAME[arguments.case]
    if arguments.operation == "_setup":
        if retained_case.stage == 0:
            _setup_alignment_signatures(trial, arguments.value)
        elif retained_case.stage == 7:
            _setup_step07(context, trial, arguments.value)
        else:
            _setup_step08(context, trial, arguments.case, arguments.value)
    elif arguments.operation == "_produce":
        source = _source(context, arguments.variant)
        if retained_case.stage == 0:
            _produce_alignment_signatures(trial, source)
        elif retained_case.stage == 7:
            _produce_step07(context, trial, source)
        else:
            _produce_step08(
                context,
                trial,
                source,
                arguments.case,
                arguments.value,
                _case_threads(arguments.case),
            )
    elif retained_case.stage == 0:
        _validate_alignment_signatures(trial)
    elif retained_case.stage == 7:
        _validate_step07(context, trial)
    else:
        _validate_step08(context, trial, arguments.case, arguments.value)
    return 0


def _manifest(
    python: Path,
    script: Path,
    context: Path,
    selected_cases: Sequence[RetainedCase] | None = None,
) -> dict[str, Any]:
    prefix = [
        str(python),
        "-X",
        "pycache_prefix=/dev/null",
        str(script),
    ]
    common = ["--context", str(context), "--case"]
    cases = []
    retained_cases = tuple(
        selected_cases
        if selected_cases is not None
        else _select_cases(suite=DEFAULT_SUITE, names=None)
    )
    for retained_case in retained_cases:
        name = retained_case.name
        values = list(retained_case.values)
        setup = [*prefix, "_setup", *common, name, "--value", "{value}", "--trial-dir", "{trial_dir}"]
        variants = [
            {
                "name": variant,
                "producer_argv": [
                    *prefix, "_produce", *common, name,
                    "--value", "{value}", "--variant", variant,
                    "--trial-dir", "{trial_dir}",
                ],
            }
            for variant in VARIANTS
        ]
        validator = [*prefix, "_validate", *common, name, "--value", "{value}", "--trial-dir", "{trial_dir}"]
        cases.append(
            {
                "name": name,
                "values": values,
                "repetitions": MEASURED_REPETITIONS,
                "warmup_repetitions": WARMUP_REPETITIONS,
                "baseline_variant": "master",
                "setup_argv": setup,
                "variants": variants,
                "validator_argv": validator,
                "artifact_paths": ["{trial_dir}/parity.bin"],
            }
        )
    return {"schema_version": COMPARISON_SCHEMA, "cases": cases}


def _safe_extract_archive(data: bytes, destination: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if (
                name.is_absolute()
                or ".." in name.parts
                or not (member.isdir() or member.isreg())
            ):
                raise BenchmarkSetupError(f"git archive contains an unsafe member: {member.name}")
        destination.mkdir(mode=0o700, parents=True)
        archive.extractall(destination)  # noqa: S202 - members were admitted above


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def _require_external_output(output: Path, repo_root: Path) -> None:
    if output == repo_root or output.is_relative_to(repo_root):
        raise BenchmarkSetupError("benchmark output root must be outside the repository")


def _comparison_summary_complete(
    path: Path, manifest: Mapping[str, Any]
) -> tuple[bool, str]:
    try:
        expected = {
            (str(case["name"]), str(value), str(variant["name"])): (
                str(case["baseline_variant"]),
                str(case["repetitions"]),
            )
            for case in manifest["cases"]
            for value in case["values"]
            for variant in case["variants"]
        }
    except (KeyError, TypeError, ValueError) as exc:
        return False, f"comparison manifest is invalid: {exc}"
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, dialect="excel-tab")
            if tuple(reader.fieldnames or ()) != COMPARISON_SUMMARY_FIELDS:
                return False, "comparison summary header differs"
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return False, f"comparison summary is unreadable: {exc}"
    roster = {(row["case"], row["value"], row["variant"]) for row in rows}
    if len(rows) != len(expected) or roster != set(expected):
        return False, "comparison summary row roster is incomplete or duplicated"
    required_metrics = COMPARISON_SUMMARY_FIELDS[10:]
    for row in rows:
        baseline, repetitions = expected[
            (row["case"], row["value"], row["variant"])
        ]
        if (
            row["baseline_variant"] != baseline
            or row["required_repetitions"] != repetitions
            or row["successful_repetitions"] != repetitions
            or row["paired_repetitions"] != repetitions
            or row["warmups_valid"] != "yes"
            or row["comparison_valid"] != "yes"
            or row["artifact_parity"] != "yes"
            or any(not row[field] for field in required_metrics)
        ):
            return False, "comparison summary contains an incomplete result row"
    return True, "complete"


def _execute(
    repo: RepositoryState,
    e2e: AdmittedE2E,
    output: Path,
    runtime_prefix: Path,
    rscript: Path,
    renv_library: Path,
    selected_cases: Sequence[RetainedCase],
    selected_suite: str | None,
) -> int:
    _require_external_output(output, repo.root)
    if output.exists() or output.is_symlink():
        raise BenchmarkSetupError(f"output root must be absent: {output}")
    parent = _real_directory(output.parent, "benchmark output parent")
    output = parent / output.name
    output.mkdir(mode=0o700)
    sources = output / "sources"
    baseline_root = sources / "origin-master"
    head_root = sources / "head"
    _safe_extract_archive(_git(repo.root, "archive", "--format=tar", repo.baseline_commit).stdout, baseline_root)
    _safe_extract_archive(_git(repo.root, "archive", "--format=tar", repo.head_commit).stdout, head_root)
    context_path = output / "benchmark-context.json"
    context = {
        "repo_root": str(repo.root),
        "python": str(repo.root / ".venv/bin/python"),
        "baseline_commit": repo.baseline_commit,
        "head_commit": repo.head_commit,
        "e2e_summary": str(e2e.summary_path),
        "e2e_summary_sha256": e2e.summary_sha256,
        "run_root": str(e2e.run_root),
        "cohort_id": e2e.cohort_id,
        "sample_manifest": str(e2e.sample_manifest),
        "reference_fasta": str(e2e.reference_fasta),
        "annotation_gtf": str(e2e.annotation_gtf),
        "orientation_root": str(e2e.orientation_root),
        "retained_primary_vcf": str(e2e.retained_primary_vcf),
        "runtime_prefix": str(runtime_prefix),
        "rscript": str(rscript),
        "renv_library": str(renv_library),
        "sources": {"master": str(baseline_root), "head": str(head_root)},
    }
    _write_json(context_path, context)
    manifest = _manifest(
        repo.python,
        repo.root / "tests/tools/retained_stage_benchmark.py",
        context_path,
        selected_cases,
    )
    manifest_path = output / "benchmark-manifest.yaml"
    with manifest_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(manifest, indent=2) + "\n")
    results = output / "benchmark-results"
    completed = subprocess.run(
        [
            str(repo.python),
            str(repo.root / "scripts/benchmark_stage_resources.py"),
            "--manifest", str(manifest_path), "--output", str(results), "--execute",
        ],
        cwd=repo.root,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    summary_path = output / "retained-stage-benchmark-summary.json"
    result_summary = results / "summary.tsv"
    complete, completion_detail = (
        _comparison_summary_complete(result_summary, manifest)
        if result_summary.is_file()
        else (False, "comparison summary was not published")
    )
    passed = completed.returncode == 0 and complete
    _write_json(
        summary_path,
        {
            "schema_version": SUMMARY_SCHEMA,
            "status": "passed" if passed else "failed",
            "baseline_ref": BASELINE_REF,
            "baseline_commit": repo.baseline_commit,
            "head_commit": repo.head_commit,
            "read_pairs_per_library": EXPECTED_READ_PAIRS,
            "selection": {
                "suite": selected_suite,
                "cases": {
                    case.name: list(case.values) for case in selected_cases
                },
            },
            "e2e_summary": _artifact(e2e.summary_path),
            "run_root": str(e2e.run_root),
            "manifest": _artifact(manifest_path),
            "comparison_summary": _artifact(result_summary) if result_summary.is_file() else None,
            "comparison_completeness": completion_detail,
            "benchmark_exit_code": completed.returncode,
            "evidence_boundary": (
                "paired hosted single-node synthetic stage timing only; not cluster, "
                "production-data, scientific-review, or biological evidence"
            ),
        },
    )
    print(f"Retained stage benchmark summary: {summary_path}")
    return 0 if passed else 1


def _orchestrate(arguments: argparse.Namespace) -> int:
    repo = _admit_repository(arguments.repo_root)
    e2e = _admit_e2e(arguments.e2e_summary)
    runtime = _real_directory(arguments.runtime_prefix, "runtime prefix")
    _real_file(runtime / "bin/bcftools", "bcftools", executable=True)
    rscript = _real_file(arguments.rscript, "Rscript", executable=True)
    renv = _real_directory(arguments.renv_library, "renv library")
    output = Path(os.path.abspath(arguments.output_root))
    _require_external_output(output, repo.root)
    case_names = getattr(arguments, "case_names", None)
    suite = getattr(arguments, "suite", None)
    selected_cases = _select_cases(suite=suite, names=case_names)
    selected_suite = None if case_names else suite or DEFAULT_SUITE
    manifest = _manifest(
        repo.python,
        repo.root / "tests/tools/retained_stage_benchmark.py",
        output / "benchmark-context.json",
        selected_cases,
    )
    plan = {
        "operation": "execute" if arguments.execute else "plan",
        "output_root": str(output),
        "baseline_commit": repo.baseline_commit,
        "head_commit": repo.head_commit,
        "selection": {
            "suite": selected_suite,
            "cases": {
                case["name"]: case["values"] for case in manifest["cases"]
            },
        },
        "paired_repetitions": MEASURED_REPETITIONS,
        "warmup_repetitions": WARMUP_REPETITIONS,
    }
    print(json.dumps(plan, indent=2, sort_keys=True))
    if not arguments.execute:
        print("Dry-run complete; no benchmark state was written.")
        return 0
    return _execute(
        repo,
        e2e,
        output,
        runtime,
        rscript,
        renv,
        selected_cases,
        selected_suite,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--e2e-summary", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--rscript", required=True, type=Path)
    parser.add_argument("--renv-library", required=True, type=Path)
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument(
        "--suite", choices=("all", *RETAINED_SUITES), default=None
    )
    selector.add_argument(
        "--case",
        choices=RETAINED_CASE_NAMES,
        action="append",
        dest="case_names",
    )
    parser.add_argument("--execute", action="store_true")
    return parser


def _internal_parser(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("operation", choices=("_setup", "_produce", "_validate"))
    parser.add_argument("--context", required=True, type=Path)
    parser.add_argument(
        "--case",
        required=True,
        choices=RETAINED_CASE_NAMES,
    )
    parser.add_argument("--value", required=True, type=int)
    parser.add_argument("--variant", choices=VARIANTS)
    parser.add_argument("--trial-dir", required=True, type=Path)
    selected = parser.parse_args(argv)
    if selected.operation == "_produce" and selected.variant is None:
        parser.error("_produce requires --variant")
    if selected.operation != "_produce" and selected.variant is not None:
        parser.error("--variant is valid only for _produce")
    if selected.value not in RETAINED_CASE_BY_NAME[selected.case].values:
        parser.error("--value is not registered for the selected case")
    return selected


def main(argv: Sequence[str] | None = None) -> int:
    selected = list(sys.argv[1:] if argv is None else argv)
    try:
        if selected and selected[0].startswith("_"):
            return _internal(_internal_parser(selected))
        return _orchestrate(_parser().parse_args(selected))
    except (BenchmarkSetupError, OSError, subprocess.SubprocessError) as exc:
        print(f"retained-stage-benchmark: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
