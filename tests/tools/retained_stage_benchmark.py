#!/usr/bin/env python3
"""Compare retained performance owners at ``origin/master`` and ``HEAD``.

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
import math
import os
import re
import stat
import subprocess
import sys
import tarfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SUMMARY_SCHEMA = "emrys.retained-stage-benchmark-summary.v3"
E2E_SCHEMA = "emrys.ci-real-synthetic-e2e-summary.v2"
COMPARISON_SCHEMA = "emrys.resource-benchmark.v2"
PHASE_RESOURCE_SCHEMA = "emrys.resource-benchmark-phase.v1"
STEP08_FIXTURE_SCHEMA = "emrys.retained-step08-fixture.v1"
BASELINE_REF = "origin/master"
EXPECTED_READ_PAIRS = 100_000
EXPECTED_CONTIG_LENGTH = 5_000_000
MEASURED_REPETITIONS = 4
WARMUP_REPETITIONS = 1
DEFAULT_SUITE = "cohort-stages"
VARIANTS = ("master", "head")
RETAINED_SAMPLE_ID = "control_pair_01"
STEP01_OWNER = "emrys.stage.align_RNA_reads_with_STAR.v1"
STEP02_OWNER = "emrys.stage.construct_canonical_BAM.v1"
STEP04_OWNER = "emrys.stage.mark_BAM_duplicates_with_Picard.v1"
STEP04_TRIAL_RUN_TOKEN = "retained-step04-benchmark"
STEP05_OWNER = "emrys.stage.split_N_cigar_reads_with_GATK.v1"
STEP05_TRIAL_RUN_TOKEN = "retained-step05-benchmark"
STEP06_OWNER = "emrys.stage.partition_BAM_by_mechanical_read_orientation.v1"
STEP06_TRIAL_RUN_TOKEN = "retained-step06-benchmark"
STEP06_COUNTS_HEADER = (
    "sample_id",
    "input_records",
    "flag_99_records",
    "flag_147_records",
    "flag_83_records",
    "flag_163_records",
    "fwd_like_records",
    "rev_like_records",
    "assigned_records",
    "unassigned_records",
    "assigned_fraction",
)
RUNTIME_PROFILE_HEADER = (
    "check_id",
    "check_type",
    "runtime_context",
    "required",
    "target",
    "probe_args",
    "expected",
    "description",
)
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
COMPARISON_TRIAL_FIELDS = (
    "case",
    "value",
    "variant",
    "trial_kind",
    "repetition",
    "status",
    "setup_exit_code",
    "producer_exit_code",
    "validator_exit_code",
    "producer_wall_seconds",
    "producer_cpu_seconds",
    "producer_max_rss_kib",
    "producer_input_blocks",
    "producer_output_blocks",
    "artifact_set_sha256",
    "artifact_match_baseline",
    "trial_dir",
)
PHASE_RESOURCE_FIELDS = (
    "schema_version",
    "case",
    "value",
    "variant",
    "trial_kind",
    "repetition",
    "phase",
    "state",
    "exit_code",
    "wall_seconds",
    "cpu_seconds",
    "max_rss_kib",
    "input_blocks",
    "output_blocks",
    "trial_dir",
)
PHASES = ("setup", "producer", "validator")
STANDARD_TASK_INPUT_ROLES = ("task_dispatch", "execution_contract", "workflow_profile")
OWNER_ENVIRONMENT_BOOTSTRAP = (
    'export EMRYS_RUN_TOKEN="$1" EMRYS_SHA256_PYTHON="$2" '
    'EMRYS_REQUIRE_BOUND_SHA256=1; shift 2; exec "$@"'
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
    RetainedCase(
        "reference-contig-membership", "identity", 0, (1_000, 4_000, 16_000), 1
    ),
    RetainedCase("step02-canonical-bam", "sample-stages", 2, (100_000,), 2),
    RetainedCase("step04-duplicate-marking", "sample-stages", 4, (100_000,), 1),
    RetainedCase("step05-split-n-cigar", "sample-stages", 5, (100_000,), 1),
    RetainedCase("step06-mechanical-orientation", "sample-stages", 6, (100_000,), 4),
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
    sample_id: str
    retained_step01_bam: RetainedArtifact
    retained_step02_bam: RetainedArtifact
    retained_step02_bai: RetainedArtifact
    retained_step04_bam: RetainedArtifact
    retained_step04_bai: RetainedArtifact
    retained_step04_metrics: RetainedArtifact
    retained_step04_run_token: str
    retained_picard_jar: RetainedArtifact
    retained_reference_fasta: RetainedArtifact
    retained_reference_fai: RetainedArtifact
    retained_reference_dict: RetainedArtifact
    retained_step05_bam: RetainedArtifact
    retained_step05_bai: RetainedArtifact
    retained_step05_run_token: str
    retained_step06_fwd_bam: RetainedArtifact
    retained_step06_fwd_bai: RetainedArtifact
    retained_step06_rev_bam: RetainedArtifact
    retained_step06_rev_bai: RetainedArtifact
    retained_step06_counts: RetainedArtifact
    retained_step06_run_token: str
    retained_step06_threads: int
    runtime_bash: Path
    runtime_gatk: Path
    runtime_java: Path
    runtime_picard_jar: Path
    runtime_samtools: Path
    runtime_sha256_python: Path


@dataclass(frozen=True, slots=True)
class RetainedArtifact:
    path: Path
    size_bytes: int
    sha256: str
    device: int
    inode: int
    mtime_ns: int


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


def _runtime_authorities(
    profile: Path,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    try:
        with profile.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, dialect="excel-tab")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise BenchmarkSetupError(f"retained runtime profile is unreadable: {exc}") from exc
    if tuple(reader.fieldnames or ()) != RUNTIME_PROFILE_HEADER:
        raise BenchmarkSetupError("retained runtime profile header differs")
    selected: dict[str, Path] = {}
    for check_id, check_type, label in (
        ("bash", "tool_version", "retained Bash authority"),
        ("samtools", "tool_version", "retained samtools authority"),
        ("sha256_python", "hash_utility", "retained SHA-256 Python authority"),
        ("gatk", "tool_version", "retained GATK authority"),
        ("java", "tool_version", "retained Java authority"),
        ("picard_jar", "path_visibility", "retained Picard jar authority"),
    ):
        matches = [row for row in rows if row.get("check_id") == check_id]
        if len(matches) != 1:
            raise BenchmarkSetupError(
                f"retained runtime profile omits the exact {check_id} authority"
            )
        if (
            matches[0].get("check_type") != check_type
            or matches[0].get("runtime_context") != "local"
            or matches[0].get("required") != "true"
        ):
            raise BenchmarkSetupError(f"retained {check_id} authority is not required locally")
        target = Path(str(matches[0].get("target")))
        if not target.is_absolute():
            raise BenchmarkSetupError(f"retained {check_id} authority is not absolute")
        selected[check_id] = _real_file(
            target, label, executable=check_id != "picard_jar"
        )
    gatk = [row for row in rows if row.get("check_id") == "gatk"]
    try:
        gatk_probe = json.loads(str(gatk[0].get("probe_args")))
    except (IndexError, json.JSONDecodeError) as exc:
        raise BenchmarkSetupError("retained GATK authority is invalid") from exc
    if len(gatk) != 1 or gatk_probe != ["--version"]:
        raise BenchmarkSetupError("retained GATK authority probe differs")
    picard = [row for row in rows if row.get("check_id") == "picard"]
    expected_probe = [
        "-jar",
        str(selected["picard_jar"]),
        "MarkDuplicates",
        "--version",
    ]
    try:
        probe = json.loads(str(picard[0].get("probe_args")))
    except (IndexError, json.JSONDecodeError) as exc:
        raise BenchmarkSetupError("retained Picard authority is invalid") from exc
    if (
        len(picard) != 1
        or picard[0].get("check_type") != "tool_version_exit_1"
        or picard[0].get("runtime_context") != "local"
        or picard[0].get("required") != "true"
        or picard[0].get("target") != str(selected["java"])
        or probe != expected_probe
    ):
        raise BenchmarkSetupError(
            "retained Picard authority is not coupled to the admitted Java and jar"
        )
    return (
        selected["bash"],
        selected["samtools"],
        selected["sha256_python"],
        selected["gatk"],
        selected["java"],
        selected["picard_jar"],
    )


def _verify_artifact(
    record: Any, label: str, *, executable: bool = False
) -> Path:
    if not isinstance(record, Mapping) or set(record) != {"path", "size_bytes", "sha256"}:
        raise BenchmarkSetupError(f"{label} is not one exact artifact record")
    path = _real_file(Path(str(record["path"])), label, executable=executable)
    if path.stat().st_size != record["size_bytes"] or _sha256_file(path) != record["sha256"]:
        raise BenchmarkSetupError(f"{label} no longer matches its retained identity")
    return path


def _admit_gatk_attestation(
    summary: Mapping[str, Any], *, adapter: Path, java: Path
) -> None:
    attestation = summary.get("gatk_attestation")
    keys = (
        "adapter", "delegate", "java_home", "runtime_java", "runtime_python",
        "runtime_python_launcher", "version_output",
    )
    if not isinstance(attestation, Mapping) or set(attestation) != set(keys):
        raise BenchmarkSetupError("retained GATK attestation differs")
    admitted = {
        key: _verify_artifact(
            attestation[key], f"retained GATK {key} attestation", executable=True
        )
        for key in ("adapter", "delegate", "runtime_java", "runtime_python")
    }
    if admitted["adapter"] != adapter or not os.path.samefile(admitted["adapter"], adapter):
        raise BenchmarkSetupError("retained GATK adapter differs from its runtime attestation")
    if admitted["runtime_java"] != java or not os.path.samefile(admitted["runtime_java"], java):
        raise BenchmarkSetupError("retained GATK Java differs from its runtime attestation")
    java_home = _real_directory(Path(str(attestation["java_home"])), "retained GATK Java home")
    if not os.path.samefile(java, java_home / "bin/java"):
        raise BenchmarkSetupError("retained GATK Java home differs")
    launcher = _real_file(
        Path(str(attestation["runtime_python_launcher"])),
        "retained GATK Python launcher", executable=True,
    )
    if not os.path.samefile(admitted["runtime_python"], launcher):
        raise BenchmarkSetupError("retained GATK Python launcher differs")
    if os.path.samefile(admitted["delegate"], adapter) or attestation["version_output"] != "The Genome Analysis Toolkit (GATK) v4.6.1.0":
        raise BenchmarkSetupError("retained GATK delegate or version differs")


def _admit_bound_artifact(
    record: Any, expected_path: Path, expected_role: str, label: str
) -> RetainedArtifact:
    if not isinstance(record, Mapping) or set(record) != {
        "role",
        "path",
        "size_bytes",
        "sha256",
    }:
        raise BenchmarkSetupError(f"{label} is not one exact bound artifact")
    if record["role"] != expected_role or Path(str(record["path"])) != expected_path:
        raise BenchmarkSetupError(f"{label} binding differs from the retained contract")
    identity = {key: record[key] for key in ("path", "size_bytes", "sha256")}
    _verify_artifact(identity, label)
    path = _real_file(expected_path, label)
    state = path.stat(follow_symlinks=False)
    return RetainedArtifact(
        path,
        int(record["size_bytes"]),
        str(record["sha256"]),
        state.st_dev,
        state.st_ino,
        state.st_mtime_ns,
    )


def _admit_verified_owner(
    summary_records: Sequence[Mapping[str, Any]],
    *,
    machine_key: str,
    scope_id: str,
    expected: Sequence[tuple[str, str, Path]],
    exact_roster: bool = False,
) -> tuple[tuple[RetainedArtifact, ...], Mapping[str, Any]]:
    references = [
        record
        for record in summary_records
        if record.get("machine_key") == machine_key
        and record.get("scope_type") == "sample"
        and record.get("scope_id") == scope_id
    ]
    if len(references) != 1:
        raise BenchmarkSetupError(f"retained summary omits the exact {machine_key} owner")
    verified = _load_json(
        Path(str(references[0]["path"])), f"retained {machine_key} verified task"
    )
    if (
        verified.get("schema_version") != "emrys.verified-task.v1"
        or verified.get("machine_key") != machine_key
        or verified.get("scope")
        != {"scope_type": "sample", "scope_id": scope_id}
        or verified.get("stable_inputs_rechecked") is not True
        or verified.get("all_pass") is not True
    ):
        raise BenchmarkSetupError(f"retained {machine_key} verified-task identity differs")
    outputs = verified.get("outputs")
    if not isinstance(outputs, list):
        raise BenchmarkSetupError(f"retained {machine_key} outputs are absent")
    if exact_roster and len(outputs) != len(expected):
        raise BenchmarkSetupError(
            f"retained {machine_key} outputs differ from the exact expected roster"
        )
    admitted = []
    for label, expected_role, expected_path in expected:
        matches = [
            record
            for record in outputs
            if isinstance(record, Mapping)
            and Path(str(record.get("path"))) == expected_path
        ]
        if len(matches) != 1:
            raise BenchmarkSetupError(
                f"retained {machine_key} verified task omits its exact {label}"
            )
        admitted.append(
            _admit_bound_artifact(
                matches[0], expected_path, expected_role, label
            )
        )
    return tuple(admitted), verified


def _admit_verified_outputs(
    summary_records: Sequence[Mapping[str, Any]],
    *,
    machine_key: str,
    scope_id: str,
    expected: Sequence[tuple[str, str, Path]],
) -> tuple[RetainedArtifact, ...]:
    admitted, _verified = _admit_verified_owner(
        summary_records,
        machine_key=machine_key,
        scope_id=scope_id,
        expected=expected,
    )
    return admitted


def _admit_exact_bindings(
    record: Mapping[str, Any],
    machine_key: str,
    boundary: str,
    expected: Sequence[tuple[str, str, Path]],
) -> tuple[RetainedArtifact, ...]:
    bindings = record.get(boundary)
    required_count = len(STANDARD_TASK_INPUT_ROLES) + len(expected)
    if not isinstance(bindings, list) or len(bindings) != required_count:
        raise BenchmarkSetupError(
            f"retained {machine_key} {boundary} differ from the exact expected roster"
        )
    provenance = bindings[: len(STANDARD_TASK_INPUT_ROLES)]
    if tuple(
        binding.get("role") if isinstance(binding, Mapping) else None
        for binding in provenance
    ) != STANDARD_TASK_INPUT_ROLES:
        raise BenchmarkSetupError(
            f"retained {machine_key} {boundary} omit the exact provenance roster"
        )
    for binding, role in zip(provenance, STANDARD_TASK_INPUT_ROLES, strict=True):
        _admit_bound_artifact(
            binding,
            Path(str(binding.get("path"))) if isinstance(binding, Mapping) else Path(),
            role,
            f"retained {machine_key} {role}",
        )
    return tuple(
        _admit_bound_artifact(binding, path, role, label)
        for binding, (label, role, path) in zip(
            bindings[len(STANDARD_TASK_INPUT_ROLES) :], expected, strict=True
        )
    )


def _admit_owner_run_token(record: Mapping[str, Any], machine_key: str) -> str:
    token = record.get("owner_run_token")
    prefix = "owner-"
    suffix = token.removeprefix(prefix) if isinstance(token, str) else ""
    if (
        not isinstance(token, str)
        or not token.startswith(prefix)
        or len(suffix) != 32
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise BenchmarkSetupError(
            f"retained {machine_key} owner run token differs from the admitted format"
        )
    return token


def _admit_owner_positive_integer_argument(
    record: Mapping[str, Any], machine_key: str, option: str
) -> int:
    commands = record.get("commands")
    producer = commands.get("producer") if isinstance(commands, Mapping) else None
    argv = producer.get("argv") if isinstance(producer, Mapping) else None
    if (
        not isinstance(argv, list)
        or any(not isinstance(value, str) for value in argv)
        or argv.count(option) != 1
    ):
        raise BenchmarkSetupError(
            f"retained {machine_key} producer omits the exact {option} argument"
        )
    index = argv.index(option)
    value = argv[index + 1] if index + 1 < len(argv) else ""
    if not value.isascii() or not value.isdecimal():
        raise BenchmarkSetupError(
            f"retained {machine_key} producer {option} is not a canonical positive integer"
        )
    parsed = int(value)
    if parsed < 1 or str(parsed) != value:
        raise BenchmarkSetupError(
            f"retained {machine_key} producer {option} is not a canonical positive integer"
        )
    return parsed


def _admit_step05_owner_command(
    record: Mapping[str, Any],
    *,
    sample_id: str,
    input_bam: Path,
    reference_fasta: Path,
    output_dir: Path,
    bash: Path,
    gatk: Path,
    samtools: Path,
    java: Path,
    sha256_python: Path,
    owner_run_token: str,
) -> None:
    commands = record.get("commands")
    producer = commands.get("producer") if isinstance(commands, Mapping) else None
    argv = producer.get("argv") if isinstance(producer, Mapping) else None
    expected_tail = (
        "--sample-id", sample_id, "--input-bam", str(input_bam),
        "--reference-fasta", str(reference_fasta), "--output-dir", str(output_dir),
        "--gatk-bin", str(gatk), "--samtools-bin", str(samtools),
        "--java-bin", str(java), "--no-clobber", "--execute",
    )
    expected_prefix = (
        str(bash), "-c", OWNER_ENVIRONMENT_BOOTSTRAP, "emrys-owner",
        owner_run_token, str(sha256_python), str(bash),
    )
    if (
        not isinstance(argv, list)
        or any(not isinstance(value, str) for value in argv)
        or len(argv) != len(expected_prefix) + 1 + len(expected_tail)
        or tuple(argv[: len(expected_prefix)]) != expected_prefix
        or tuple(argv[len(expected_prefix) + 1 :]) != expected_tail
    ):
        raise BenchmarkSetupError("retained Step 05 producer argv differs")
    owner = _real_file(
        Path(argv[len(expected_prefix)]), "retained Step 05 owner"
    )
    if not owner.as_posix().endswith(
        "/src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"
    ):
        raise BenchmarkSetupError("retained Step 05 owner path differs")


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
    (
        runtime_bash,
        runtime_samtools,
        runtime_sha256_python,
        runtime_gatk,
        runtime_java,
        runtime_picard_jar,
    ) = _runtime_authorities(Path(str(runtime_profile["path"])))
    _admit_gatk_attestation(
        summary,
        adapter=runtime_gatk,
        java=runtime_java,
    )

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
    reference_fai = Path(f"{reference_fasta}.fai")
    reference_dict = reference_fasta.with_name(f"{reference_fasta.stem}.dict")
    for selected, label in (
        (sample_manifest, "sample manifest"),
        (partition_manifest, "partition manifest"),
        (reference_fasta, "reference FASTA"),
        (reference_fai, "reference FAI"),
        (reference_dict, "reference DICT"),
        (annotation_gtf, "annotation GTF"),
    ):
        _real_file(selected, label)
    try:
        with sample_manifest.open(encoding="utf-8", newline="") as stream:
            sample_rows = list(csv.DictReader(stream, dialect="excel-tab"))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise BenchmarkSetupError(f"sample manifest is unreadable: {exc}") from exc
    if [row.get("sample_id") for row in sample_rows].count(RETAINED_SAMPLE_ID) != 1:
        raise BenchmarkSetupError(
            f"retained sample manifest must contain {RETAINED_SAMPLE_ID} exactly once"
        )
    expected_step01_bam = (
        run_root
        / "results/star"
        / RETAINED_SAMPLE_ID
        / f"{RETAINED_SAMPLE_ID}.Aligned.sortedByCoord.out.bam"
    )
    expected_step02_bam = (
        run_root
        / "results/bam"
        / RETAINED_SAMPLE_ID
        / f"{RETAINED_SAMPLE_ID}.sorted.bam"
    )
    expected_step02_bai = Path(f"{expected_step02_bam}.bai")
    (retained_step01_bam,) = _admit_verified_outputs(
        records,
        machine_key=STEP01_OWNER,
        scope_id=RETAINED_SAMPLE_ID,
        expected=(("retained Step 01 BAM", "output_001", expected_step01_bam),),
    )
    retained_step02_bam, retained_step02_bai = _admit_verified_outputs(
        records,
        machine_key=STEP02_OWNER,
        scope_id=RETAINED_SAMPLE_ID,
        expected=(
            ("retained Step 02 BAM", "output_001", expected_step02_bam),
            ("retained Step 02 BAI", "output_002", expected_step02_bai),
        ),
    )
    expected_step04_bam = (
        run_root
        / "results/markdup"
        / RETAINED_SAMPLE_ID
        / f"{RETAINED_SAMPLE_ID}.markdup.bam"
    )
    expected_step04_bai = Path(f"{expected_step04_bam}.bai")
    expected_step04_metrics = (
        run_root
        / "results/qc/markdup"
        / f"{RETAINED_SAMPLE_ID}.markdup.metrics.txt"
    )
    step04_artifacts, step04_verified = _admit_verified_owner(
        records,
        machine_key=STEP04_OWNER,
        scope_id=RETAINED_SAMPLE_ID,
        exact_roster=True,
        expected=(
            ("retained Step 04 BAM", "output_001", expected_step04_bam),
            ("retained Step 04 BAI", "output_002", expected_step04_bai),
            ("retained Step 04 metrics", "output_003", expected_step04_metrics),
        ),
    )
    retained_step04_bam, retained_step04_bai, retained_step04_metrics = (
        step04_artifacts
    )
    step04_input_bam, step04_input_bai, retained_picard_jar = _admit_exact_bindings(
        step04_verified,
        STEP04_OWNER,
        "inputs",
        (
            ("retained Step 04 input BAM", "input_001", expected_step02_bam),
            ("retained Step 04 input BAI", "input_002", expected_step02_bai),
            (
                "retained Step 04 Picard jar",
                "input_003",
                runtime_picard_jar,
            ),
        ),
    )
    if (
        step04_input_bam != retained_step02_bam
        or step04_input_bai != retained_step02_bai
        or not os.path.samefile(retained_picard_jar.path, runtime_picard_jar)
    ):
        raise BenchmarkSetupError(
            "retained Step 04 inputs differ from admitted Step 02 and Picard authorities"
        )
    retained_step04_run_token = _admit_owner_run_token(step04_verified, STEP04_OWNER)
    expected_step05_bam = (
        run_root
        / "results/split_ncigar"
        / RETAINED_SAMPLE_ID
        / f"{RETAINED_SAMPLE_ID}.split_ncigar.bam"
    )
    expected_step05_bai = Path(f"{expected_step05_bam}.bai")
    step05_artifacts, step05_verified = _admit_verified_owner(
        records,
        machine_key=STEP05_OWNER,
        scope_id=RETAINED_SAMPLE_ID,
        exact_roster=True,
        expected=(
            ("retained Step 05 BAM", "output_001", expected_step05_bam),
            ("retained Step 05 BAI", "output_002", expected_step05_bai),
        ),
    )
    retained_step05_bam, retained_step05_bai = step05_artifacts
    (
        step05_input_bam,
        step05_input_bai,
        retained_reference_fasta,
        retained_reference_fai,
        retained_reference_dict,
    ) = _admit_exact_bindings(
        step05_verified,
        STEP05_OWNER,
        "inputs",
        (
            ("retained Step 05 input BAM", "input_001", expected_step04_bam),
            ("retained Step 05 input BAI", "input_002", expected_step04_bai),
            ("retained Step 05 reference FASTA", "input_003", reference_fasta),
            ("retained Step 05 reference FAI", "input_004", reference_fai),
            ("retained Step 05 reference DICT", "input_005", reference_dict),
        ),
    )
    if (
        step05_input_bam != retained_step04_bam
        or step05_input_bai != retained_step04_bai
    ):
        raise BenchmarkSetupError(
            "retained Step 05 inputs differ from admitted Step 04 outputs"
        )
    retained_step05_run_token = _admit_owner_run_token(step05_verified, STEP05_OWNER)
    _admit_step05_owner_command(
        step05_verified,
        sample_id=RETAINED_SAMPLE_ID,
        input_bam=expected_step04_bam,
        reference_fasta=reference_fasta,
        output_dir=expected_step05_bam.parent,
        bash=runtime_bash,
        gatk=runtime_gatk,
        samtools=runtime_samtools,
        java=runtime_java,
        sha256_python=runtime_sha256_python,
        owner_run_token=retained_step05_run_token,
    )
    orientation_root = _real_directory(run_root / "results/orientation", "retained orientation root")
    expected_step06_fwd_bam = (
        orientation_root
        / RETAINED_SAMPLE_ID
        / f"{RETAINED_SAMPLE_ID}.FWD_like.bam"
    )
    expected_step06_fwd_bai = Path(f"{expected_step06_fwd_bam}.bai")
    expected_step06_rev_bam = (
        orientation_root
        / RETAINED_SAMPLE_ID
        / f"{RETAINED_SAMPLE_ID}.REV_like.bam"
    )
    expected_step06_rev_bai = Path(f"{expected_step06_rev_bam}.bai")
    expected_step06_counts = (
        run_root
        / "results/qc/orientation"
        / f"{RETAINED_SAMPLE_ID}.orientation_counts.tsv"
    )
    step06_artifacts, step06_verified = _admit_verified_owner(
        records,
        machine_key=STEP06_OWNER,
        scope_id=RETAINED_SAMPLE_ID,
        exact_roster=True,
        expected=(
            ("retained Step 06 FWD BAM", "output_001", expected_step06_fwd_bam),
            ("retained Step 06 FWD BAI", "output_002", expected_step06_fwd_bai),
            ("retained Step 06 REV BAM", "output_003", expected_step06_rev_bam),
            ("retained Step 06 REV BAI", "output_004", expected_step06_rev_bai),
            ("retained Step 06 counts", "output_005", expected_step06_counts),
        ),
    )
    (
        retained_step06_fwd_bam,
        retained_step06_fwd_bai,
        retained_step06_rev_bam,
        retained_step06_rev_bai,
        retained_step06_counts,
    ) = step06_artifacts
    retained_step06_run_token = _admit_owner_run_token(step06_verified, STEP06_OWNER)
    retained_step06_threads = _admit_owner_positive_integer_argument(
        step06_verified,
        STEP06_OWNER,
        "--threads",
    )
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
        RETAINED_SAMPLE_ID,
        retained_step01_bam,
        retained_step02_bam,
        retained_step02_bai,
        retained_step04_bam,
        retained_step04_bai,
        retained_step04_metrics,
        retained_step04_run_token,
        retained_picard_jar,
        retained_reference_fasta,
        retained_reference_fai,
        retained_reference_dict,
        retained_step05_bam,
        retained_step05_bai,
        retained_step05_run_token,
        retained_step06_fwd_bam,
        retained_step06_fwd_bai,
        retained_step06_rev_bam,
        retained_step06_rev_bai,
        retained_step06_counts,
        retained_step06_run_token,
        retained_step06_threads,
        runtime_bash,
        runtime_gatk,
        runtime_java,
        runtime_picard_jar,
        runtime_samtools,
        runtime_sha256_python,
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


def _context_artifact(
    context: Mapping[str, Any], key: str, label: str
) -> RetainedArtifact:
    record = context.get(key)
    required = {"path", "size_bytes", "sha256", "device", "inode", "mtime_ns"}
    if not isinstance(record, Mapping) or set(record) != required:
        raise BenchmarkSetupError(f"benchmark context omits the {label}")
    if (
        any(not isinstance(record[field], int) for field in required - {"path", "sha256"})
        or not isinstance(record["sha256"], str)
        or len(record["sha256"]) != 64
        or any(character not in "0123456789abcdef" for character in record["sha256"])
    ):
        raise BenchmarkSetupError(f"benchmark context has an invalid {label} identity")
    return RetainedArtifact(
        Path(str(record["path"])),
        record["size_bytes"],
        record["sha256"],
        record["device"],
        record["inode"],
        record["mtime_ns"],
    )


def _artifact_context(artifact: RetainedArtifact) -> dict[str, str | int]:
    return {
        "path": str(artifact.path),
        "size_bytes": artifact.size_bytes,
        "sha256": artifact.sha256,
        "device": artifact.device,
        "inode": artifact.inode,
        "mtime_ns": artifact.mtime_ns,
    }


def _retained_step01_bam(context: Mapping[str, Any]) -> Path:
    admitted = _context_artifact(context, "retained_step01_bam", "retained Step 01 BAM")
    path = _real_file(admitted.path, "retained Step 01 BAM")
    state = path.stat(follow_symlinks=False)
    if (
        state.st_size != admitted.size_bytes
        or state.st_dev != admitted.device
        or state.st_ino != admitted.inode
        or state.st_mtime_ns != admitted.mtime_ns
    ):
        raise BenchmarkSetupError("retained Step 01 BAM identity changed")
    return path


def _setup_step02(context: Mapping[str, Any], trial: Path, value: int) -> None:
    if value != EXPECTED_READ_PAIRS:
        raise BenchmarkSetupError("Step 02 benchmark requires the retained 100k profile")
    input_bam = _retained_step01_bam(context)
    if input_bam.stat(follow_symlinks=False).st_dev != trial.stat().st_dev:
        raise BenchmarkSetupError("Step 02 benchmark requires same-filesystem hard links")
    (trial / "qc").mkdir(mode=0o700)


def _produce_step02(context: Mapping[str, Any], trial: Path, source: Path) -> None:
    from emrys.libraries.process_environment import sanitized_subprocess_environment

    input_bam = _retained_step01_bam(context)
    runtime = _real_directory(Path(str(context["runtime_prefix"])), "runtime prefix")
    samtools = _real_file(runtime / "bin/samtools", "samtools", executable=True)
    owner = _real_file(
        source / "src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh",
        "Step 02 owner",
    )
    environment = sanitized_subprocess_environment(os.environ)
    environment.update(
        {
            "EMRYS_RUN_TOKEN": "retained-benchmark",
            "EMRYS_SHA256_PYTHON": str(context["python"]),
            "EMRYS_REQUIRE_BOUND_SHA256": "1",
        }
    )
    _run_checked(
        (
            "bash",
            str(owner),
            "--sample-id",
            str(context["sample_id"]),
            "--input-alignment",
            str(input_bam),
            "--output-dir",
            "output",
            "--threads",
            str(_case_threads("step02-canonical-bam")),
            "--samtools-bin",
            str(samtools),
            "--no-clobber",
            "--execute",
        ),
        cwd=trial,
        environment=environment,
    )


def _validation_report(
    root: Path, scope_id: str, partition_id: str | None = None
) -> Path:
    suffix = f"__{partition_id}" if partition_id is not None else ""
    return root / f"{scope_id}{suffix}.validation.tsv"


def _validate_step02(context: Mapping[str, Any], trial: Path) -> None:
    sample_id = str(context["sample_id"])
    relative_bam = Path("output") / f"{sample_id}.sorted.bam"
    relative_bai = Path(f"{relative_bam}.bai")
    bam = _real_file(trial / relative_bam, "Step 02 benchmark BAM")
    bai = _real_file(trial / relative_bai, "Step 02 benchmark BAI")
    retained_input = _retained_step01_bam(context)
    if not os.path.samefile(bam, retained_input):
        raise BenchmarkSetupError("Step 02 case left the canonical hard-link path")
    runtime = _real_directory(Path(str(context["runtime_prefix"])), "runtime prefix")
    samtools = _real_file(runtime / "bin/samtools", "samtools", executable=True)
    report = _validation_report(Path("qc"), sample_id)
    _run_checked(
        _emrys(
            context,
            "validate",
            "canonical-bam",
            "--scope-id",
            sample_id,
            "--bam",
            str(relative_bam),
            "--bai",
            str(relative_bai),
            "--samtools-bin",
            str(samtools),
            "--output",
            str(report),
            "--execute",
        ),
        cwd=trial,
    )
    _run_checked(
        _emrys(
            context,
            "validate",
            "all-pass",
            "--report",
            str(report),
            "--step-id",
            "02",
            "--scope-id",
            sample_id,
        ),
        cwd=trial,
    )
    idxstats = subprocess.run(
        [str(samtools), "idxstats", str(relative_bam)],
        cwd=trial,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if idxstats.returncode != 0 or not idxstats.stdout:
        raise BenchmarkSetupError("Step 02 benchmark index query failed")
    bam_digest = _sha256_file(bam)
    bai_digest = _sha256_file(bai)
    expected_bam = _context_artifact(
        context, "retained_step02_bam", "retained Step 02 BAM"
    )
    expected_bai = _context_artifact(
        context, "retained_step02_bai", "retained Step 02 BAI"
    )
    if (
        (bam.stat().st_size, bam_digest)
        != (expected_bam.size_bytes, expected_bam.sha256)
        or (bai.stat().st_size, bai_digest)
        != (expected_bai.size_bytes, expected_bai.sha256)
    ):
        raise BenchmarkSetupError("Step 02 outputs differ from retained verified identities")
    _write_bundle(
        trial / "parity.bin",
        (
            ("bam", f"{bam.stat().st_size}\t{bam_digest}\n".encode()),
            ("bai", f"{bai.stat().st_size}\t{bai_digest}\n".encode()),
            ("idxstats", idxstats.stdout),
        ),
    )
    bam.unlink()
    bai.unlink()
    if any((trial / "output").iterdir()):
        raise BenchmarkSetupError("Step 02 benchmark retained publication residue")


def _retained_path(context: Mapping[str, Any], key: str, label: str) -> Path:
    admitted = _context_artifact(context, key, label)
    path = _real_file(admitted.path, label)
    state = path.stat(follow_symlinks=False)
    if (
        state.st_size != admitted.size_bytes
        or state.st_dev != admitted.device
        or state.st_ino != admitted.inode
        or state.st_mtime_ns != admitted.mtime_ns
    ):
        raise BenchmarkSetupError(f"{label} identity changed")
    return path


def _step04_paths(sample_id: str) -> dict[str, Path]:
    output_root = Path("results/markdup") / sample_id
    metrics_root = Path("results/qc/markdup")
    bam = output_root / f"{sample_id}.markdup.bam"
    return {
        "output_root": output_root,
        "metrics_root": metrics_root,
        "scratch": Path("scratch"),
        "bam": bam,
        "bai": Path(f"{bam}.bai"),
        "metrics": metrics_root / f"{sample_id}.markdup.metrics.txt",
        "report": _validation_report(Path("results/qc/validation/04"), sample_id),
    }


def _setup_step04(context: Mapping[str, Any], trial: Path, value: int) -> None:
    if value != EXPECTED_READ_PAIRS or context.get("sample_id") != RETAINED_SAMPLE_ID:
        raise BenchmarkSetupError("Step 04 benchmark requires the retained 100k sample")
    for key, label in (
        ("retained_step02_bam", "retained Step 02 BAM"),
        ("retained_step02_bai", "retained Step 02 BAI"),
        ("retained_step04_bam", "retained Step 04 BAM"),
        ("retained_step04_bai", "retained Step 04 BAI"),
        ("retained_step04_metrics", "retained Step 04 metrics"),
        ("retained_picard_jar", "retained Picard jar"),
    ):
        _retained_path(context, key, label)
    paths = _step04_paths(RETAINED_SAMPLE_ID)
    for key in ("output_root", "metrics_root", "scratch"):
        (trial / paths[key]).mkdir(mode=0o700, parents=True)
    (trial / paths["report"]).parent.mkdir(mode=0o700, parents=True)


def _produce_step04(context: Mapping[str, Any], trial: Path, source: Path) -> None:
    from emrys.libraries.process_environment import sanitized_subprocess_environment

    paths = _step04_paths(RETAINED_SAMPLE_ID)
    input_bam = _retained_path(context, "retained_step02_bam", "retained Step 02 BAM")
    _retained_path(context, "retained_step02_bai", "retained Step 02 BAI")
    picard_jar = _retained_path(
        context, "retained_picard_jar", "retained Picard jar"
    )
    authorities = {
        label: _real_file(Path(str(context[key])), label, executable=executable)
        for key, label, executable in (
            ("runtime_bash", "retained Bash authority", True),
            ("runtime_java", "retained Java authority", True),
            ("runtime_picard_jar", "retained Picard jar authority", False),
            ("runtime_samtools", "retained samtools authority", True),
            ("runtime_sha256_python", "retained SHA-256 Python authority", True),
        )
    }
    if not os.path.samefile(picard_jar, authorities["retained Picard jar authority"]):
        raise BenchmarkSetupError("Step 04 Picard jar differs from runtime authority")
    owner = _real_file(
        source / "src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh",
        "Step 04 owner",
    )
    environment = sanitized_subprocess_environment(os.environ)
    environment.update(
        {
            "EMRYS_RUN_TOKEN": STEP04_TRIAL_RUN_TOKEN,
            "EMRYS_SHA256_PYTHON": str(
                authorities["retained SHA-256 Python authority"]
            ),
            "EMRYS_REQUIRE_BOUND_SHA256": "1",
            "TMPDIR": str((trial / paths["scratch"]).resolve(strict=True)),
        }
    )
    _run_checked(
        (
            str(authorities["retained Bash authority"]),
            str(owner),
            "--sample-id",
            RETAINED_SAMPLE_ID,
            "--input-bam",
            str(input_bam),
            "--output-dir",
            str(paths["output_root"]),
            "--metrics-dir",
            str(paths["metrics_root"]),
            "--picard-jar",
            str(picard_jar),
            "--java-bin",
            str(authorities["retained Java authority"]),
            "--samtools-bin",
            str(authorities["retained samtools authority"]),
            "--no-clobber",
            "--execute",
        ),
        cwd=trial,
        environment=environment,
    )


def _step05_paths(sample_id: str) -> dict[str, Path]:
    output_root = Path("results/split_ncigar") / sample_id
    bam = output_root / f"{sample_id}.split_ncigar.bam"
    return {
        "output_root": output_root,
        "bam": bam,
        "bai": Path(f"{bam}.bai"),
        "report": _validation_report(Path("results/qc/validation/05"), sample_id),
    }


def _step05_references(context: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    fasta = _retained_path(context, "retained_reference_fasta", "retained reference FASTA")
    fai = _retained_path(context, "retained_reference_fai", "retained reference FAI")
    dictionary = _retained_path(context, "retained_reference_dict", "retained reference DICT")
    if fasta != Path(str(context.get("reference_fasta"))):
        raise BenchmarkSetupError("retained reference FASTA path differs from execution")
    return fasta, fai, dictionary


def _step05_authorities(context: Mapping[str, Any]) -> dict[str, Path]:
    return {
        key: _real_file(Path(str(context[f"runtime_{key}"])), f"retained {label} authority", executable=True)
        for key, label in (
            ("bash", "Bash"), ("gatk", "GATK"), ("java", "Java"),
            ("samtools", "samtools"), ("sha256_python", "SHA-256 Python"),
        )
    }


def _setup_step05(context: Mapping[str, Any], trial: Path, value: int) -> None:
    if value != EXPECTED_READ_PAIRS or context.get("sample_id") != RETAINED_SAMPLE_ID:
        raise BenchmarkSetupError("Step 05 benchmark requires the retained 100k sample")
    for key, label in (
        ("retained_step04_bam", "retained Step 04 BAM"),
        ("retained_step04_bai", "retained Step 04 BAI"),
        ("retained_step05_bam", "retained Step 05 BAM"),
        ("retained_step05_bai", "retained Step 05 BAI"),
    ):
        _retained_path(context, key, label)
    _step05_references(context)
    _step05_authorities(context)
    paths = _step05_paths(RETAINED_SAMPLE_ID)
    (trial / paths["output_root"]).mkdir(mode=0o700, parents=True)
    (trial / paths["report"]).parent.mkdir(mode=0o700, parents=True)


def _produce_step05(context: Mapping[str, Any], trial: Path, source: Path) -> None:
    from emrys.libraries.process_environment import gatk_subprocess_environment

    paths = _step05_paths(RETAINED_SAMPLE_ID)
    input_bam = _retained_path(context, "retained_step04_bam", "retained Step 04 BAM")
    _retained_path(context, "retained_step04_bai", "retained Step 04 BAI")
    reference_fasta, _reference_fai, _reference_dict = _step05_references(context)
    authority = _step05_authorities(context)
    owner = _real_file(
        source / "src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh", "Step 05 owner",
    )
    environment = gatk_subprocess_environment(authority["java"], base_environment=os.environ)
    environment.update(
        {
            "EMRYS_RUN_TOKEN": STEP05_TRIAL_RUN_TOKEN,
            "EMRYS_SHA256_PYTHON": str(authority["sha256_python"]),
            "EMRYS_REQUIRE_BOUND_SHA256": "1",
        }
    )
    _run_checked(
        (
            str(authority["bash"]), str(owner), "--sample-id", RETAINED_SAMPLE_ID,
            "--input-bam", str(input_bam), "--reference-fasta", str(reference_fasta),
            "--output-dir", str(paths["output_root"]), "--gatk-bin", str(authority["gatk"]),
            "--samtools-bin", str(authority["samtools"]), "--java-bin", str(authority["java"]),
            "--no-clobber", "--execute",
        ),
        cwd=trial,
        environment=environment,
    )


def _step06_paths(sample_id: str) -> dict[str, Path]:
    orientation = Path("results/orientation") / sample_id
    counts_root = Path("results/qc/orientation")
    return {
        "orientation_root": orientation,
        "counts_root": counts_root,
        "fwd_bam": orientation / f"{sample_id}.FWD_like.bam",
        "fwd_bai": orientation / f"{sample_id}.FWD_like.bam.bai",
        "rev_bam": orientation / f"{sample_id}.REV_like.bam",
        "rev_bai": orientation / f"{sample_id}.REV_like.bam.bai",
        "counts": counts_root / f"{sample_id}.orientation_counts.tsv",
        "report": _validation_report(Path("results/qc/validation/06"), sample_id),
    }


def _setup_step06(context: Mapping[str, Any], trial: Path, value: int) -> None:
    if value != EXPECTED_READ_PAIRS:
        raise BenchmarkSetupError("Step 06 benchmark requires the retained 100k profile")
    _retained_path(context, "retained_step05_bam", "retained Step 05 BAM")
    _retained_path(context, "retained_step05_bai", "retained Step 05 BAI")
    paths = _step06_paths(str(context["sample_id"]))
    for key in ("orientation_root", "counts_root"):
        (trial / paths[key]).mkdir(mode=0o700, parents=True)
    (trial / paths["report"]).parent.mkdir(mode=0o700, parents=True)


def _produce_step06(context: Mapping[str, Any], trial: Path, source: Path) -> None:
    from emrys.libraries.process_environment import sanitized_subprocess_environment

    sample_id = str(context["sample_id"])
    paths = _step06_paths(sample_id)
    input_bam = _retained_path(
        context, "retained_step05_bam", "retained Step 05 BAM"
    )
    _retained_path(context, "retained_step05_bai", "retained Step 05 BAI")
    bash = _real_file(
        Path(str(context["runtime_bash"])), "retained Bash authority", executable=True
    )
    samtools = _real_file(
        Path(str(context["runtime_samtools"])),
        "retained samtools authority",
        executable=True,
    )
    sha256_python = _real_file(
        Path(str(context["runtime_sha256_python"])),
        "retained SHA-256 Python authority",
        executable=True,
    )
    owner = _real_file(
        source
        / "src/emrys/stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh",
        "Step 06 owner",
    )
    environment = sanitized_subprocess_environment(os.environ)
    environment.update(
        {
            "EMRYS_RUN_TOKEN": STEP06_TRIAL_RUN_TOKEN,
            "EMRYS_SHA256_PYTHON": str(sha256_python),
            "EMRYS_REQUIRE_BOUND_SHA256": "1",
        }
    )
    _run_checked(
        (
            str(bash),
            str(owner),
            "--sample-id",
            sample_id,
            "--input-bam",
            str(input_bam),
            "--output-dir",
            str(paths["orientation_root"]),
            "--qc-dir",
            str(paths["counts_root"]),
            "--threads",
            str(_case_threads("step06-mechanical-orientation")),
            "--samtools-bin",
            str(samtools),
            "--no-clobber",
            "--execute",
        ),
        cwd=trial,
        environment=environment,
    )


def _capture_checked(argv: Sequence[str], *, cwd: Path) -> bytes:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise BenchmarkSetupError(
            f"command exited {completed.returncode}: {' '.join(argv)}{suffix}"
        )
    return completed.stdout


def _sam_records(data: bytes, label: str) -> tuple[tuple[bytes, int, bytes], ...]:
    if data and not data.endswith(b"\n"):
        raise BenchmarkSetupError(f"{label} is not newline-terminated SAM")
    records = []
    for index, line in enumerate(data.splitlines(keepends=True), start=1):
        if not line.endswith(b"\n"):
            raise BenchmarkSetupError(f"{label} record {index} is incomplete")
        fields = line[:-1].split(b"\t")
        if len(fields) < 11:
            raise BenchmarkSetupError(f"{label} record {index} is not decoded SAM")
        try:
            flag = int(fields[1])
        except ValueError as exc:
            raise BenchmarkSetupError(
                f"{label} record {index} has an invalid SAM flag"
            ) from exc
        if flag < 0:
            raise BenchmarkSetupError(f"{label} record {index} has a negative SAM flag")
        records.append((line, flag, fields[2]))
    return tuple(records)


def _idxstats_contigs(data: bytes, label: str) -> tuple[tuple[bytes, ...], int]:
    if not data or not data.endswith(b"\n"):
        raise BenchmarkSetupError(f"{label} is empty or incomplete")
    contigs = []
    total_records = 0
    for index, line in enumerate(data.splitlines(), start=1):
        fields = line.split(b"\t")
        if len(fields) != 4:
            raise BenchmarkSetupError(f"{label} row {index} is malformed")
        try:
            length, mapped, unmapped = (int(value) for value in fields[1:])
        except ValueError as exc:
            raise BenchmarkSetupError(
                f"{label} row {index} contains a non-integer count"
            ) from exc
        if min(length, mapped, unmapped) < 0:
            raise BenchmarkSetupError(f"{label} row {index} contains a negative count")
        total_records += mapped + unmapped
        if fields[0] != b"*" and length > 0:
            contigs.append(fields[0])
    if not contigs:
        raise BenchmarkSetupError(f"{label} has no traversable reference contig")
    return tuple(contigs), total_records


def _inspect_indexed_bam(
    samtools: Path, bam: Path, *, cwd: Path, label: str
) -> dict[str, bytes | tuple[tuple[bytes, int, bytes], ...]]:
    quickcheck = _capture_checked(
        (str(samtools), "quickcheck", "-v", str(bam)), cwd=cwd
    )
    if quickcheck:
        raise BenchmarkSetupError(f"{label} emitted quickcheck failure paths")
    header = _capture_checked(
        (str(samtools), "view", "-H", "--no-PG", str(bam)), cwd=cwd
    )
    if not header or not header.endswith(b"\n") or any(
        not line.startswith(b"@") for line in header.splitlines()
    ):
        raise BenchmarkSetupError(f"{label} has an invalid decoded SAM header")
    decoded = _capture_checked((str(samtools), "view", str(bam)), cwd=cwd)
    records = _sam_records(decoded, label)
    idxstats = _capture_checked((str(samtools), "idxstats", str(bam)), cwd=cwd)
    contigs, indexed_record_count = _idxstats_contigs(
        idxstats, f"{label} idxstats"
    )
    if indexed_record_count != len(records):
        raise BenchmarkSetupError(f"{label} idxstats counts do not reconcile")
    indexed = _capture_checked(
        (str(samtools), "view", str(bam), *(item.decode("utf-8") for item in contigs)),
        cwd=cwd,
    )
    expected_indexed = b"".join(
        line for line, _flag, reference in records if reference in set(contigs)
    )
    if indexed != expected_indexed:
        raise BenchmarkSetupError(f"{label} indexed traversal differs from decoded SAM")
    return {
        "header": header,
        "decoded": decoded,
        "records": records,
        "idxstats": idxstats,
        "indexed": indexed,
    }


def _require_indexed_bam_parity(
    observed: Mapping[str, Any],
    reference: Mapping[str, Any],
    *,
    observed_header: bytes,
    reference_header: bytes,
    label: str,
) -> tuple[tuple[str, bytes], ...]:
    if observed_header != reference_header:
        raise BenchmarkSetupError(
            f"{label} header differs beyond admitted roots and run tokens or metadata"
        )
    for key, detail in (
        ("decoded", "decoded SAM records differ in content or order"),
        ("idxstats", "indexed counts differ from retained output"),
        ("indexed", "indexed traversal differs from retained output"),
    ):
        if observed[key] != reference[key]:
            raise BenchmarkSetupError(f"{label} {detail}")
    decoded = bytes(observed["decoded"])
    indexed = bytes(observed["indexed"])
    return (
        ("header", observed_header),
        (
            "records",
            f"{len(decoded)}\t{hashlib.sha256(decoded).hexdigest()}\n".encode(),
        ),
        ("idxstats", bytes(observed["idxstats"])),
        (
            "indexed",
            f"{len(indexed)}\t{hashlib.sha256(indexed).hexdigest()}\n".encode(),
        ),
    )


def _canonicalize_sam_header(
    data: bytes, *, roots: Sequence[Path], run_tokens: Sequence[str]
) -> bytes:
    replacements: list[tuple[bytes, bytes]] = []
    for root in roots:
        encoded = str(root).encode("utf-8")
        if not root.is_absolute() or not encoded:
            raise BenchmarkSetupError("SAM header root must be absolute")
        replacements.append((encoded + b"/", b""))
        replacements.append((encoded, b"<EMRYS_ROOT>"))
    for token in run_tokens:
        if not token or any(
            character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
            for character in token
        ):
            raise BenchmarkSetupError("SAM header run token is invalid")
        replacements.append((token.encode("ascii"), b"<EMRYS_RUN_TOKEN>"))
    normalized = data
    for authored, replacement in sorted(set(replacements), key=lambda item: -len(item[0])):
        normalized = normalized.replace(authored, replacement)
    return normalized


def _sam_header_fields(
    line: bytes, record_type: bytes, label: str
) -> list[tuple[bytes, bytes]]:
    if not line.endswith(b"\n"):
        raise BenchmarkSetupError(f"{label} contains an incomplete {record_type.decode()} line")
    raw_fields = line[:-1].split(b"\t")
    if not raw_fields or raw_fields[0] != record_type:
        raise BenchmarkSetupError(f"{label} contains an invalid {record_type.decode()} line")
    fields: list[tuple[bytes, bytes]] = []
    seen: set[bytes] = set()
    for raw_field in raw_fields[1:]:
        key, separator, value = raw_field.partition(b":")
        if separator != b":" or len(key) != 2 or not value or key in seen:
            raise BenchmarkSetupError(
                f"{label} contains malformed or duplicate {record_type.decode()} metadata"
            )
        fields.append((key, value))
        seen.add(key)
    if b"ID" not in seen:
        raise BenchmarkSetupError(f"{label} contains {record_type.decode()} metadata without ID")
    return fields


def _replace_sam_header_field(
    fields: Sequence[tuple[bytes, bytes]], key: bytes, value: bytes
) -> list[tuple[bytes, bytes]]:
    return [(selected, value if selected == key else current) for selected, current in fields]


def _render_sam_header_fields(
    record_type: bytes, fields: Sequence[tuple[bytes, bytes]]
) -> bytes:
    return b"\t".join(
        (record_type, *(key + b":" + value for key, value in fields))
    ) + b"\n"


def _step06_program_semantics(
    fields: Sequence[tuple[bytes, bytes]],
) -> tuple[tuple[bytes, bytes], ...]:
    return tuple(sorted((key, value) for key, value in fields if key != b"ID"))


def _step06_collision_base(program_id: bytes, known_ids: set[bytes]) -> bytes | None:
    matched = re.fullmatch(rb"(.+)-[0-9A-F]{1,8}", program_id)
    if matched is None or matched.group(1) not in known_ids:
        return None
    return matched.group(1)


def _canonicalize_step06_header(
    data: bytes,
    *,
    roots: Sequence[Path],
    run_tokens: Sequence[str],
    expected_threads: int,
    label: str,
) -> tuple[bytes, dict[bytes, bytes], dict[bytes, bytes]]:
    if type(expected_threads) is not int or expected_threads < 1:
        raise BenchmarkSetupError(f"{label} has no admitted positive thread count")
    normalized = _canonicalize_sam_header(
        data,
        roots=roots,
        run_tokens=run_tokens,
    )
    if not normalized.endswith(b"\n"):
        raise BenchmarkSetupError(f"{label} is not a complete SAM header")
    lines = normalized.splitlines(keepends=True)
    program_fields: dict[int, list[tuple[bytes, bytes]]] = {}
    step06_programs: set[int] = set()
    program_ids: set[bytes] = set()
    thread_pattern = re.compile(rb"(?<!\S)-@ ([1-9][0-9]*)(?= |$)")
    for index, line in enumerate(lines):
        if not line.startswith(b"@PG\t"):
            continue
        fields = _sam_header_fields(line, b"@PG", label)
        values = dict(fields)
        program_id = values[b"ID"]
        if program_id in program_ids:
            raise BenchmarkSetupError(f"{label} contains a duplicate @PG ID")
        program_ids.add(program_id)
        command = values.get(b"CL")
        is_step06 = (
            values.get(b"PN") == b"samtools"
            and command is not None
            and b".step06.<EMRYS_RUN_TOKEN>." in command
        )
        if is_step06:
            matches = tuple(thread_pattern.finditer(command))
            if (
                len(matches) != 1
                or int(matches[0].group(1)) != expected_threads
                or str(expected_threads).encode() != matches[0].group(1)
            ):
                raise BenchmarkSetupError(
                    f"{label} Step 06 command differs from its admitted thread count"
                )
            command = thread_pattern.sub(b"-@ <EMRYS_THREADS>", command, count=1)
            fields = _replace_sam_header_field(fields, b"CL", command)
            step06_programs.add(index)
        program_fields[index] = fields
    if len(step06_programs) != 4:
        raise BenchmarkSetupError(
            f"{label} does not contain the exact four Step 06 samtools programs"
        )

    program_aliases: dict[bytes, bytes] = {}
    semantics_by_id: dict[bytes, tuple[tuple[bytes, bytes], ...]] = {}
    for index, fields in program_fields.items():
        values = dict(fields)
        raw_id = values[b"ID"]
        predecessor = values.get(b"PP")
        if predecessor is not None:
            canonical_predecessor = program_aliases.get(predecessor)
            if canonical_predecessor is None:
                raise BenchmarkSetupError(
                    f"{label} @PG predecessor is absent or appears after its consumer"
                )
            fields = _replace_sam_header_field(
                fields, b"PP", canonical_predecessor
            )
        semantics = _step06_program_semantics(fields)
        base = _step06_collision_base(raw_id, program_ids)
        if base is None:
            canonical_id = raw_id
        else:
            canonical_base = program_aliases.get(base)
            if canonical_base is None:
                raise BenchmarkSetupError(
                    f"{label} collision base is absent or appears after its alias"
                )
            base_semantics = semantics_by_id[canonical_base]
            if semantics == base_semantics:
                canonical_id = canonical_base
            else:
                command = dict(fields).get(b"CL", b"")
                is_step06_view = (
                    index in step06_programs
                    and re.search(
                        rb"(?:^|/)samtools view -@ <EMRYS_THREADS> -b -f "
                        rb"(?:99|147|83|163) -o ",
                        command,
                    )
                    is not None
                )
                if not is_step06_view:
                    raise BenchmarkSetupError(
                        f"{label} collision alias differs beyond admitted Step 06 view metadata"
                    )
                digest_source = b"\0".join(
                    key + b"\0" + value for key, value in semantics
                )
                digest = hashlib.sha256(digest_source).hexdigest()[:16].upper().encode()
                canonical_id = (
                    canonical_base + b"-<EMRYS_COLLISION_" + digest + b">"
                )
        prior_semantics = semantics_by_id.get(canonical_id)
        if prior_semantics is not None and prior_semantics != semantics:
            raise BenchmarkSetupError(f"{label} canonical @PG identities collide")
        semantics_by_id.setdefault(canonical_id, semantics)
        program_aliases[raw_id] = canonical_id
        fields = _replace_sam_header_field(fields, b"ID", canonical_id)
        lines[index] = _render_sam_header_fields(b"@PG", fields)

    read_group_fields: dict[int, list[tuple[bytes, bytes]]] = {}
    read_group_ids: set[bytes] = set()
    for index, line in enumerate(lines):
        if not line.startswith(b"@RG\t"):
            continue
        fields = _sam_header_fields(line, b"@RG", label)
        read_group_id = dict(fields)[b"ID"]
        if read_group_id in read_group_ids:
            raise BenchmarkSetupError(f"{label} contains a duplicate @RG ID")
        read_group_ids.add(read_group_id)
        read_group_fields[index] = fields
    read_group_aliases: dict[bytes, bytes] = {}
    read_group_semantics: dict[bytes, tuple[tuple[bytes, bytes], ...]] = {}
    for index, fields in read_group_fields.items():
        values = dict(fields)
        raw_id = values[b"ID"]
        program = values.get(b"PG")
        if program is not None:
            canonical_program = program_aliases.get(program)
            if canonical_program is None:
                raise BenchmarkSetupError(f"{label} @RG references an unknown @PG ID")
            fields = _replace_sam_header_field(fields, b"PG", canonical_program)
        semantics = _step06_program_semantics(fields)
        base = _step06_collision_base(raw_id, read_group_ids)
        if base is None:
            canonical_id = raw_id
        else:
            canonical_base = read_group_aliases.get(base)
            if canonical_base is None:
                raise BenchmarkSetupError(
                    f"{label} @RG collision base appears after its alias"
                )
            if read_group_semantics[canonical_base] != semantics:
                raise BenchmarkSetupError(
                    f"{label} @RG collision alias differs beyond its generated ID"
                )
            canonical_id = canonical_base
        prior_semantics = read_group_semantics.get(canonical_id)
        if prior_semantics is not None and prior_semantics != semantics:
            raise BenchmarkSetupError(f"{label} canonical @RG identities collide")
        read_group_semantics.setdefault(canonical_id, semantics)
        read_group_aliases[raw_id] = canonical_id
        fields = _replace_sam_header_field(fields, b"ID", canonical_id)
        lines[index] = _render_sam_header_fields(b"@RG", fields)
    return b"".join(lines), read_group_aliases, program_aliases


def _canonicalize_step06_records(
    data: bytes,
    *,
    read_group_aliases: Mapping[bytes, bytes],
    program_aliases: Mapping[bytes, bytes],
    label: str,
) -> bytes:
    records = _sam_records(data, label)
    normalized: list[bytes] = []
    mappings = {b"RG": read_group_aliases, b"PG": program_aliases}
    for index, (line, _flag, _reference) in enumerate(records, start=1):
        fields = line[:-1].split(b"\t")
        _sam_optional_tags(fields, f"{label} record {index}")
        for field_index in range(11, len(fields)):
            tag, value_type, value = fields[field_index].split(b":", 2)
            mapping = mappings.get(tag)
            if mapping is None:
                continue
            if value_type != b"Z" or not value:
                raise BenchmarkSetupError(
                    f"{label} record {index} has a non-text {tag.decode()} tag"
                )
            canonical = mapping.get(value)
            if canonical is None:
                raise BenchmarkSetupError(
                    f"{label} record {index} references an unknown {tag.decode()} ID"
                )
            fields[field_index] = tag + b":Z:" + canonical
        normalized.append(b"\t".join(fields) + b"\n")
    return b"".join(normalized)


def _canonicalize_step05_header(
    data: bytes,
    *,
    roots: Sequence[Path],
    run_tokens: Sequence[str],
    label: str,
) -> bytes:
    lines = data.splitlines(keepends=True)
    selected = [
        index
        for index, line in enumerate(lines)
        if line.startswith(b"@PG\t") and b"SplitNCigarReads" in line
    ]
    if not data.endswith(b"\n") or not selected:
        raise BenchmarkSetupError(
            f"{label} lacks a complete GATK SplitNCigarReads @PG line"
        )
    for line_index in selected:
        fields = lines[line_index][:-1].split(b"\t")
        commands = [
            index for index, field in enumerate(fields) if field.startswith(b"CL:")
        ]
        if len(commands) != 1:
            raise BenchmarkSetupError(
                f"{label} lacks one exact SplitNCigarReads CL field"
            )
        command = _canonicalize_sam_header(
            fields[commands[0]][3:] + b"\n",
            roots=roots,
            run_tokens=run_tokens,
        )
        fields[commands[0]] = b"CL:" + command[:-1]
        lines[line_index] = b"\t".join(fields) + b"\n"
    return b"".join(lines)


def _canonicalize_step04_command(
    data: bytes,
    *,
    roots: Sequence[Path],
    run_tokens: Sequence[str],
    expected_tmp: bytes | None,
    label: str,
) -> tuple[bytes, bytes]:
    tmp_matches = re.findall(rb"TMP_DIR=(?:\[[^\]]+\]|\S+)", data)
    index_matches = tuple(re.finditer(rb"CREATE_INDEX=(?:true|false)", data))
    if len(tmp_matches) != 1 or len(index_matches) != 1:
        raise BenchmarkSetupError(f"{label} omits exact TMP_DIR or CREATE_INDEX metadata")
    index_match = index_matches[0]
    if (
        (index_match.start() > 0 and data[index_match.start() - 1] not in b" \t")
        or (
            index_match.end() < len(data)
            and data[index_match.end()] not in b" \t\n"
        )
    ):
        raise BenchmarkSetupError(f"{label} omits exact TMP_DIR or CREATE_INDEX metadata")
    tmp = tmp_matches[0].removeprefix(b"TMP_DIR=").strip(b"[]")
    if expected_tmp is not None and tmp != expected_tmp:
        raise BenchmarkSetupError(f"{label} TMP_DIR differs from its admitted value")
    removal_start = index_match.start()
    removal_end = index_match.end()
    if removal_start > 0 and data[removal_start - 1 : removal_start] == b" ":
        removal_start -= 1
    elif removal_end < len(data) and data[removal_end : removal_end + 1] == b" ":
        removal_end += 1
    without_index_policy = data[:removal_start] + data[removal_end:]
    normalized = _canonicalize_sam_header(
        without_index_policy.replace(tmp_matches[0], b"TMP_DIR=<EMRYS_TMPDIR>"),
        roots=roots,
        run_tokens=run_tokens,
    )
    return normalized, tmp


def _canonicalize_step04_header(
    data: bytes,
    *,
    roots: Sequence[Path],
    run_tokens: Sequence[str],
    expected_tmp: bytes | None,
    label: str,
) -> tuple[bytes, bytes]:
    lines = data.splitlines(keepends=True)
    selected = [
        index
        for index, line in enumerate(lines)
        if line.startswith(b"@PG\t") and b"\tID:MarkDuplicates\t" in b"\t" + line
    ]
    if not data.endswith(b"\n") or len(selected) != 1:
        raise BenchmarkSetupError(f"{label} lacks one complete MarkDuplicates @PG line")
    lines[selected[0]], tmp = _canonicalize_step04_command(
        lines[selected[0]],
        roots=roots,
        run_tokens=run_tokens,
        expected_tmp=expected_tmp,
        label=label,
    )
    return b"".join(lines), tmp


def _step04_metrics_semantics(
    data: bytes,
    *,
    roots: Sequence[Path],
    run_tokens: Sequence[str],
    expected_tmp: bytes,
    label: str,
) -> tuple[bytes, bytes, dict[str, str]]:
    marker = b"## METRICS CLASS"
    if not data.endswith(b"\n") or data.count(marker) != 1:
        raise BenchmarkSetupError(f"{label} lacks one complete metrics body")
    prefix, body_tail = data.split(marker, 1)
    lines = prefix.splitlines(keepends=True)
    commands = [index for index, line in enumerate(lines) if line.startswith(b"# MarkDuplicates ")]
    started = [index for index, line in enumerate(lines) if line.startswith(b"# Started on: ")]
    if len(commands) != 1 or len(started) != 1:
        raise BenchmarkSetupError(f"{label} metadata roster differs")
    lines[commands[0]], _tmp = _canonicalize_step04_command(
        lines[commands[0]],
        roots=roots,
        run_tokens=run_tokens,
        expected_tmp=expected_tmp,
        label=label,
    )
    lines[started[0]] = b"# Started on: <PICARD_TIMESTAMP>\n"
    body = marker + body_tail
    table = [line for line in body.decode("utf-8").splitlines()[1:] if line]
    if len(table) < 2:
        raise BenchmarkSetupError(f"{label} metrics table is absent")
    header = table[0].split("\t")
    values = table[1].split("\t")
    if len(header) != len(values) or len(set(header)) != len(header):
        raise BenchmarkSetupError(f"{label} metrics row differs from its header")
    return b"".join(lines) + body, body, dict(zip(header, values, strict=True))


def _sam_optional_tags(fields: Sequence[bytes], label: str) -> dict[bytes, bytes]:
    tags: dict[bytes, bytes] = {}
    for field in fields[11:]:
        parts = field.split(b":", 2)
        if len(parts) != 3 or len(parts[0]) != 2 or parts[0] in tags:
            raise BenchmarkSetupError(f"{label} has malformed or duplicate optional tags")
        tags[parts[0]] = b":".join(parts[1:])
    return tags


def _independent_step04_metrics(
    input_records: tuple[tuple[bytes, int, bytes], ...],
    output_records: tuple[tuple[bytes, int, bytes], ...],
    metrics: Mapping[str, str],
    sample_id: str,
) -> dict[str, int | str]:
    if not input_records or len(input_records) != len(output_records):
        raise BenchmarkSetupError("Step 04 input/output record counts differ")
    duplicates = 0
    for index, (source, target) in enumerate(
        zip(input_records, output_records, strict=True), start=1
    ):
        source_fields, target_fields = source[0][:-1].split(b"\t"), target[0][:-1].split(b"\t")
        if source[1] & 0x400:
            raise BenchmarkSetupError("retained Step 02 input already has duplicate flags")
        if (
            source_fields[0] != target_fields[0]
            or source_fields[2:11] != target_fields[2:11]
            or source[1] != target[1] & ~0x400
        ):
            raise BenchmarkSetupError(f"Step 04 record {index} differs beyond the duplicate bit")
        source_tags = _sam_optional_tags(source_fields, f"Step 02 record {index}")
        target_tags = _sam_optional_tags(target_fields, f"Step 04 record {index}")
        if (
            source_tags.pop(b"PG", None) == b"Z:MarkDuplicates"
            or target_tags.pop(b"PG", None) != b"Z:MarkDuplicates"
            or source_tags != target_tags
        ):
            raise BenchmarkSetupError(f"Step 04 record {index} PG/tag transition differs")
        duplicates += bool(target[1] & 0x400)
    integer_fields = (
        "UNPAIRED_READS_EXAMINED",
        "READ_PAIRS_EXAMINED",
        "SECONDARY_OR_SUPPLEMENTARY_RDS",
        "UNMAPPED_READS",
        "UNPAIRED_READ_DUPLICATES",
        "READ_PAIR_DUPLICATES",
    )
    try:
        counts = {field: int(metrics[field]) for field in integer_fields}
        fraction = float(metrics["PERCENT_DUPLICATION"])
    except (KeyError, ValueError) as exc:
        raise BenchmarkSetupError("Step 04 metrics omit exact numeric counts") from exc
    if min(counts.values()) < 0 or metrics.get("LIBRARY") != sample_id:
        raise BenchmarkSetupError("Step 04 metrics library or counts differ")
    primary = counts["UNPAIRED_READS_EXAMINED"] + 2 * counts["READ_PAIRS_EXAMINED"]
    examined = primary + counts["SECONDARY_OR_SUPPLEMENTARY_RDS"] + counts["UNMAPPED_READS"]
    metric_duplicates = counts["UNPAIRED_READ_DUPLICATES"] + 2 * counts["READ_PAIR_DUPLICATES"]
    expected_fraction = metric_duplicates / primary if primary else 0.0
    if (
        examined != len(input_records)
        or metric_duplicates != duplicates
        or not math.isfinite(fraction)
        or not math.isclose(fraction, expected_fraction, abs_tol=5e-7)
    ):
        raise BenchmarkSetupError("Step 04 duplicate flags and Picard metrics do not reconcile")
    return {
        "input_records": len(input_records),
        "output_records": len(output_records),
        "duplicate_records": duplicates,
        "percent_duplication": metrics["PERCENT_DUPLICATION"],
    }


def _validate_step04(context: Mapping[str, Any], trial: Path) -> None:
    paths = _step04_paths(RETAINED_SAMPLE_ID)
    outputs = {
        key: _real_file(trial / paths[key], f"Step 04 benchmark {key}")
        for key in ("bam", "bai", "metrics")
    }
    retained = {
        key: _retained_path(context, f"retained_step04_{key}", f"retained Step 04 {key}")
        for key in ("bam", "bai", "metrics")
    }
    input_bam = _retained_path(context, "retained_step02_bam", "retained Step 02 BAM")
    _retained_path(context, "retained_step02_bai", "retained Step 02 BAI")
    samtools = _real_file(Path(str(context["runtime_samtools"])), "retained samtools authority", executable=True)
    validator_python = _real_file(Path(str(context["runtime_sha256_python"])), "retained SHA-256 Python authority", executable=True)
    if not os.path.samefile(validator_python, Path(str(context["python"]))):
        raise BenchmarkSetupError("validator Python differs from retained SHA-256 authority")
    report = paths["report"]
    _run_checked(
        _emrys(
            context, "validate", "duplicate-marking", "--scope-id", RETAINED_SAMPLE_ID,
            "--bam", str(paths["bam"]), "--bai", str(paths["bai"]),
            "--metrics", str(paths["metrics"]), "--samtools-bin", str(samtools),
            "--output", str(report), "--execute",
        ),
        cwd=trial,
    )
    _run_checked(
        _emrys(context, "validate", "all-pass", "--report", str(report), "--step-id", "04", "--scope-id", RETAINED_SAMPLE_ID),
        cwd=trial,
    )
    input_records = _sam_records(
        _capture_checked((str(samtools), "view", str(input_bam)), cwd=trial),
        "retained Step 02 input",
    )
    observed = _inspect_indexed_bam(samtools, outputs["bam"], cwd=trial, label="Step 04 benchmark BAM")
    reference = _inspect_indexed_bam(samtools, retained["bam"], cwd=trial, label="retained Step 04 BAM")
    run_root = _real_directory(Path(str(context["run_root"])), "retained run root")
    retained_token = context.get("retained_step04_run_token")
    if not isinstance(retained_token, str):
        raise BenchmarkSetupError("benchmark context omits the retained Step 04 run token")
    observed_header, observed_tmp = _canonicalize_step04_header(
        bytes(observed["header"]), roots=(run_root, trial),
        run_tokens=(STEP04_TRIAL_RUN_TOKEN,),
        expected_tmp=str((trial / paths["scratch"]).resolve(strict=True)).encode(),
        label="Step 04 benchmark header",
    )
    reference_header, reference_tmp = _canonicalize_step04_header(
        bytes(reference["header"]), roots=(run_root,), run_tokens=(retained_token,),
        expected_tmp=None, label="retained Step 04 header",
    )
    members = list(
        _require_indexed_bam_parity(
            observed, reference, observed_header=observed_header,
            reference_header=reference_header, label="Step 04 BAM",
        )
    )
    observed_metrics, observed_body, values = _step04_metrics_semantics(
        outputs["metrics"].read_bytes(), roots=(run_root, trial),
        run_tokens=(STEP04_TRIAL_RUN_TOKEN,), expected_tmp=observed_tmp,
        label="Step 04 benchmark metrics",
    )
    reference_metrics, reference_body, _reference_values = _step04_metrics_semantics(
        retained["metrics"].read_bytes(), roots=(run_root,), run_tokens=(retained_token,),
        expected_tmp=reference_tmp, label="retained Step 04 metrics",
    )
    if observed_metrics != reference_metrics or observed_body != reference_body:
        raise BenchmarkSetupError("Step 04 Picard metrics differ beyond admitted metadata")
    output_records = observed["records"]
    if not isinstance(output_records, tuple):
        raise BenchmarkSetupError("Step 04 decoded record boundary is invalid")
    independent = _independent_step04_metrics(
        input_records, output_records, values, RETAINED_SAMPLE_ID
    )
    members.extend(
        (
            ("metrics-body", observed_body),
            ("independent-counts", json.dumps(independent, sort_keys=True, separators=(",", ":")).encode() + b"\n"),
        )
    )
    _write_bundle(trial / "parity.bin", members)
    for output in outputs.values():
        output.unlink()
    for key in ("output_root", "metrics_root", "scratch"):
        if any((trial / paths[key]).iterdir()):
            raise BenchmarkSetupError("Step 04 benchmark retained publication residue")


def _sam_programs(data: bytes, label: str) -> dict[bytes, dict[bytes, bytes]]:
    programs: dict[bytes, dict[bytes, bytes]] = {}
    if not data.endswith(b"\n"):
        raise BenchmarkSetupError(f"{label} is not a complete SAM header")
    for line in data.splitlines():
        if not line.startswith(b"@PG\t"):
            continue
        fields: dict[bytes, bytes] = {}
        for field in line.split(b"\t")[1:]:
            key, separator, value = field.partition(b":")
            if separator != b":" or len(key) != 2 or not value or key in fields:
                raise BenchmarkSetupError(f"{label} contains a malformed @PG field")
            fields[key] = value
        program_id = fields.get(b"ID")
        if program_id is None or program_id in programs:
            raise BenchmarkSetupError(f"{label} contains a missing or duplicate @PG ID")
        programs[program_id] = fields
    if not programs:
        raise BenchmarkSetupError(f"{label} contains no @PG records")
    return programs


def _sam_record_semantics(
    record: tuple[bytes, int, bytes], label: str
) -> tuple[tuple[bytes, int, bytes, bytes, bytes], int, bytes | None]:
    fields = record[0][:-1].split(b"\t")
    tags = _sam_optional_tags(fields, label)
    cigar = fields[5]
    if cigar == b"*":
        n_count = 0
    else:
        operations = re.findall(rb"([1-9][0-9]*)([MIDNSHP=X])", cigar)
        if not operations or b"".join(count + operation for count, operation in operations) != cigar:
            raise BenchmarkSetupError(f"{label} has a malformed CIGAR")
        n_count = sum(operation == b"N" for _count, operation in operations)
    read_group = tags.get(b"RG", b"")
    if read_group and not read_group.startswith(b"Z:"):
        raise BenchmarkSetupError(f"{label} has a non-text RG tag")
    pg = tags.get(b"PG")
    if pg is not None:
        if not pg.startswith(b"Z:") or len(pg) == 2:
            raise BenchmarkSetupError(f"{label} has a malformed PG tag")
        pg = pg[2:]
    stable_flag = record[1] & ~0x800
    return (
        fields[0],
        stable_flag,
        record[2],
        fields[6],
        read_group,
    ), n_count, pg


def _independent_step05_semantics(
    input_inspection: Mapping[str, Any],
    output_inspection: Mapping[str, Any],
) -> dict[str, int]:
    input_records = input_inspection.get("records")
    output_records = output_inspection.get("records")
    if (
        not isinstance(input_records, tuple)
        or not isinstance(output_records, tuple)
        or not input_records
        or not output_records
    ):
        raise BenchmarkSetupError("Step 05 semantic comparison requires decoded records")
    input_programs = _sam_programs(
        bytes(input_inspection["header"]), "retained Step 04 header"
    )
    output_programs = _sam_programs(
        bytes(output_inspection["header"]), "Step 05 benchmark header"
    )
    if any(output_programs.get(key) != value for key, value in input_programs.items()):
        raise BenchmarkSetupError("Step 05 did not preserve predecessor @PG records")
    added = set(output_programs).difference(input_programs)
    if not added:
        raise BenchmarkSetupError("Step 05 adds no program identity")
    for gatk_id in added:
        gatk_program = output_programs[gatk_id]
        if b"SplitNCigarReads" not in b" ".join(gatk_program.values()):
            raise BenchmarkSetupError("Step 05 added program is not SplitNCigarReads")
        predecessor = gatk_program.get(b"PP")
        if predecessor is not None and predecessor not in output_programs:
            raise BenchmarkSetupError("Step 05 @PG predecessor is not an admitted program")

    expected_identities: Counter[tuple[bytes, int, bytes, bytes, bytes]] = Counter()
    source_pg: dict[
        tuple[bytes, int, bytes, bytes, bytes], set[bytes | None]
    ] = {}
    total_n_ops = 0
    input_supplementary = 0
    for index, record in enumerate(input_records, start=1):
        identity, observed_n_count, pg = _sam_record_semantics(
            record, f"retained Step 04 record {index}"
        )
        n_count = 0 if record[1] & 0x100 else observed_n_count
        if pg is not None and pg not in input_programs:
            raise BenchmarkSetupError("Step 04 record references an unknown @PG identity")
        expected_identities[identity] += 1 + n_count
        source_pg.setdefault(identity, set()).add(pg)
        total_n_ops += n_count
        input_supplementary += bool(record[1] & 0x800)

    observed_identities: Counter[tuple[bytes, int, bytes, bytes, bytes]] = Counter()
    output_supplementary = 0
    for index, record in enumerate(output_records, start=1):
        identity, n_count, pg = _sam_record_semantics(
            record, f"Step 05 record {index}"
        )
        if n_count and not record[1] & 0x100:
            raise BenchmarkSetupError(
                "Step 05 non-secondary output retains an N CIGAR operation"
            )
        allowed_pg = source_pg.get(identity, set()) | added
        if identity not in source_pg or pg not in allowed_pg:
            raise BenchmarkSetupError("Step 05 record identity or PG transition differs")
        observed_identities[identity] += 1
        output_supplementary += bool(record[1] & 0x800)

    if total_n_ops == 0:
        raise BenchmarkSetupError("Step 05 retained input exercises no N CIGAR split")
    if observed_identities != expected_identities:
        raise BenchmarkSetupError("Step 05 split record identity multiset differs")
    if len(output_records) != len(input_records) + total_n_ops:
        raise BenchmarkSetupError("Step 05 output count does not reconcile with N operations")
    if output_supplementary != input_supplementary + total_n_ops:
        raise BenchmarkSetupError("Step 05 supplementary count does not reconcile")
    return {
        "input_records": len(input_records),
        "input_n_cigar_operations": total_n_ops,
        "output_records": len(output_records),
        "input_supplementary_records": input_supplementary,
        "output_supplementary_records": output_supplementary,
        "record_identities": len(observed_identities),
    }


def _validate_step05(context: Mapping[str, Any], trial: Path) -> None:
    paths = _step05_paths(RETAINED_SAMPLE_ID)
    outputs = {
        key: _real_file(trial / paths[key], f"Step 05 benchmark {key}")
        for key in ("bam", "bai")
    }
    retained = {
        key: _retained_path(
            context, f"retained_step05_{key}", f"retained Step 05 {key}"
        )
        for key in ("bam", "bai")
    }
    input_bam = _retained_path(context, "retained_step04_bam", "retained Step 04 BAM")
    _retained_path(context, "retained_step04_bai", "retained Step 04 BAI")
    reference_fasta, reference_fai, reference_dict = _step05_references(context)
    authority = _step05_authorities(context)
    samtools = authority["samtools"]
    if not os.path.samefile(authority["sha256_python"], Path(str(context["python"]))):
        raise BenchmarkSetupError("validator Python differs from retained SHA-256 authority")
    report = paths["report"]
    _run_checked(
        _emrys(
            context, "validate", "split-n-cigar", "--scope-id", RETAINED_SAMPLE_ID,
            "--bam", str(paths["bam"]), "--bai", str(paths["bai"]),
            "--reference-fasta", str(reference_fasta), "--reference-fai", str(reference_fai),
            "--reference-dict", str(reference_dict), "--samtools-bin", str(samtools),
            "--output", str(report), "--execute",
        ),
        cwd=trial,
    )
    _run_checked(
        _emrys(
            context, "validate", "all-pass", "--report", str(report),
            "--step-id", "05", "--scope-id", RETAINED_SAMPLE_ID,
        ),
        cwd=trial,
    )
    input_inspection = _inspect_indexed_bam(
        samtools, input_bam, cwd=trial, label="retained Step 04 BAM"
    )
    observed = _inspect_indexed_bam(
        samtools, outputs["bam"], cwd=trial, label="Step 05 benchmark BAM"
    )
    reference = _inspect_indexed_bam(
        samtools, retained["bam"], cwd=trial, label="retained Step 05 BAM"
    )
    run_root = _real_directory(Path(str(context["run_root"])), "retained run root")
    retained_token = context.get("retained_step05_run_token")
    if not isinstance(retained_token, str):
        raise BenchmarkSetupError("benchmark context omits the retained Step 05 run token")
    observed_header = _canonicalize_step05_header(
        bytes(observed["header"]),
        roots=(run_root, trial),
        run_tokens=(STEP05_TRIAL_RUN_TOKEN,),
        label="Step 05 benchmark header",
    )
    reference_header = _canonicalize_step05_header(
        bytes(reference["header"]),
        roots=(run_root,),
        run_tokens=(retained_token,),
        label="retained Step 05 header",
    )
    members = list(
        _require_indexed_bam_parity(
            observed,
            reference,
            observed_header=observed_header,
            reference_header=reference_header,
            label="Step 05 BAM",
        )
    )
    independent = _independent_step05_semantics(input_inspection, observed)
    members.append(
        (
            "independent-counts",
            json.dumps(independent, sort_keys=True, separators=(",", ":")).encode()
            + b"\n",
        )
    )
    _write_bundle(trial / "parity.bin", members)
    for output in outputs.values():
        output.unlink()
    if any((trial / paths["output_root"]).iterdir()):
        raise BenchmarkSetupError("Step 05 benchmark retained publication residue")


def _parse_step06_counts(data: bytes, sample_id: str, label: str) -> dict[str, int | str]:
    try:
        text = data.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text), dialect="excel-tab")
        rows = list(reader)
    except (UnicodeError, csv.Error) as exc:
        raise BenchmarkSetupError(f"{label} is not readable TSV: {exc}") from exc
    if tuple(reader.fieldnames or ()) != STEP06_COUNTS_HEADER:
        raise BenchmarkSetupError(f"{label} header differs from the Step 06 contract")
    if len(rows) != 1 or rows[0].get("sample_id") != sample_id:
        raise BenchmarkSetupError(f"{label} must contain the exact retained sample")
    values: dict[str, int | str] = {"sample_id": sample_id}
    try:
        for field in STEP06_COUNTS_HEADER[1:-1]:
            value = int(rows[0][field])
            if value < 0:
                raise ValueError
            values[field] = value
    except (KeyError, TypeError, ValueError) as exc:
        raise BenchmarkSetupError(f"{label} has invalid integer counts") from exc
    fraction = rows[0].get("assigned_fraction")
    if not isinstance(fraction, str):
        raise BenchmarkSetupError(f"{label} omits assigned_fraction")
    values["assigned_fraction"] = fraction
    return values


def _independent_step06_counts(
    input_records: tuple[tuple[bytes, int, bytes], ...],
    fwd_records: tuple[tuple[bytes, int, bytes], ...],
    rev_records: tuple[tuple[bytes, int, bytes], ...],
) -> dict[str, int | str]:
    def includes(flag: int, required: int) -> bool:
        return flag & required == required

    if not input_records or not fwd_records or not rev_records:
        raise BenchmarkSetupError("Step 06 semantic comparison requires nonempty records")
    if any(
        not (includes(flag, 99) or includes(flag, 147))
        for _line, flag, _reference in fwd_records
    ):
        raise BenchmarkSetupError("Step 06 FWD output contains an unaccepted flag")
    if any(
        not (includes(flag, 83) or includes(flag, 163))
        for _line, flag, _reference in rev_records
    ):
        raise BenchmarkSetupError("Step 06 REV output contains an unaccepted flag")
    expected_fwd = [
        line
        for required in (99, 147)
        for line, flag, _reference in input_records
        if includes(flag, required)
    ]
    expected_rev = [
        line
        for required in (83, 163)
        for line, flag, _reference in input_records
        if includes(flag, required)
    ]
    if Counter(line for line, _flag, _reference in fwd_records) != Counter(expected_fwd):
        raise BenchmarkSetupError("Step 06 FWD record membership differs from Step 05")
    if Counter(line for line, _flag, _reference in rev_records) != Counter(expected_rev):
        raise BenchmarkSetupError("Step 06 REV record membership differs from Step 05")
    counts = {
        "input_records": len(input_records),
        "flag_99_records": sum(includes(flag, 99) for _line, flag, _ref in input_records),
        "flag_147_records": sum(includes(flag, 147) for _line, flag, _ref in input_records),
        "flag_83_records": sum(includes(flag, 83) for _line, flag, _ref in input_records),
        "flag_163_records": sum(includes(flag, 163) for _line, flag, _ref in input_records),
        "fwd_like_records": len(fwd_records),
        "rev_like_records": len(rev_records),
    }
    if counts["fwd_like_records"] != counts["flag_99_records"] + counts["flag_147_records"]:
        raise BenchmarkSetupError("Step 06 FWD component counts do not reconcile")
    if counts["rev_like_records"] != counts["flag_83_records"] + counts["flag_163_records"]:
        raise BenchmarkSetupError("Step 06 REV component counts do not reconcile")
    assigned = counts["fwd_like_records"] + counts["rev_like_records"]
    if assigned > counts["input_records"]:
        raise BenchmarkSetupError("Step 06 assigned count exceeds the input count")
    counts["assigned_records"] = assigned
    counts["unassigned_records"] = counts["input_records"] - assigned
    counts["assigned_fraction"] = f"{assigned / counts['input_records']:.6f}"
    return counts


def _validate_step06(context: Mapping[str, Any], trial: Path) -> None:
    sample_id = str(context["sample_id"])
    paths = _step06_paths(sample_id)
    outputs = {
        key: _real_file(trial / paths[key], f"Step 06 benchmark {key}")
        for key in ("fwd_bam", "fwd_bai", "rev_bam", "rev_bai", "counts")
    }
    retained = {
        key: _retained_path(context, f"retained_step06_{key}", f"retained Step 06 {key}")
        for key in ("fwd_bam", "fwd_bai", "rev_bam", "rev_bai", "counts")
    }
    input_bam = _retained_path(
        context, "retained_step05_bam", "retained Step 05 BAM"
    )
    _retained_path(context, "retained_step05_bai", "retained Step 05 BAI")
    samtools = _real_file(
        Path(str(context["runtime_samtools"])),
        "retained samtools authority",
        executable=True,
    )
    validator_python = _real_file(
        Path(str(context["runtime_sha256_python"])),
        "retained SHA-256 Python authority",
        executable=True,
    )
    if not os.path.samefile(validator_python, Path(str(context["python"]))):
        raise BenchmarkSetupError("validator Python differs from retained SHA-256 authority")
    report = paths["report"]
    _run_checked(
        _emrys(
            context,
            "validate",
            "mechanical-orientation",
            "--scope-id",
            sample_id,
            "--fwd-bam",
            str(paths["fwd_bam"]),
            "--fwd-bai",
            str(paths["fwd_bai"]),
            "--rev-bam",
            str(paths["rev_bam"]),
            "--rev-bai",
            str(paths["rev_bai"]),
            "--counts",
            str(paths["counts"]),
            "--output",
            str(report),
            "--execute",
        ),
        cwd=trial,
    )
    _run_checked(
        _emrys(
            context,
            "validate",
            "all-pass",
            "--report",
            str(report),
            "--step-id",
            "06",
            "--scope-id",
            sample_id,
        ),
        cwd=trial,
    )

    input_decoded = _capture_checked((str(samtools), "view", str(input_bam)), cwd=trial)
    input_records = _sam_records(input_decoded, "retained Step 05 input")
    observed: dict[str, dict[str, bytes | tuple[tuple[bytes, int, bytes], ...]]] = {}
    reference: dict[str, dict[str, bytes | tuple[tuple[bytes, int, bytes], ...]]] = {}
    for orientation in ("fwd", "rev"):
        observed[orientation] = _inspect_indexed_bam(
            samtools,
            outputs[f"{orientation}_bam"],
            cwd=trial,
            label=f"Step 06 benchmark {orientation.upper()} BAM",
        )
        reference[orientation] = _inspect_indexed_bam(
            samtools,
            retained[f"{orientation}_bam"],
            cwd=trial,
            label=f"retained Step 06 {orientation.upper()} BAM",
        )
    run_root = _real_directory(Path(str(context["run_root"])), "retained run root")
    retained_run_token = context.get("retained_step06_run_token")
    if not isinstance(retained_run_token, str):
        raise BenchmarkSetupError("benchmark context omits the retained Step 06 run token")
    retained_threads = context.get("retained_step06_threads")
    observed_roots = (run_root, trial)
    reference_roots = (run_root,)
    observed_tokens = (STEP06_TRIAL_RUN_TOKEN,)
    reference_tokens = (retained_run_token,)
    bam_members: dict[str, tuple[tuple[str, bytes], ...]] = {}
    canonical_observed: dict[str, dict[str, Any]] = {}
    canonical_reference: dict[str, dict[str, Any]] = {}
    for orientation in ("fwd", "rev"):
        observed_header, observed_read_groups, observed_programs = (
            _canonicalize_step06_header(
                bytes(observed[orientation]["header"]),
                roots=observed_roots,
                run_tokens=observed_tokens,
                expected_threads=_case_threads("step06-mechanical-orientation"),
                label=f"Step 06 benchmark {orientation.upper()} header",
            )
        )
        reference_header, reference_read_groups, reference_programs = (
            _canonicalize_step06_header(
                bytes(reference[orientation]["header"]),
                roots=reference_roots,
                run_tokens=reference_tokens,
                expected_threads=retained_threads,
                label=f"retained Step 06 {orientation.upper()} header",
            )
        )
        canonical_observed[orientation] = dict(observed[orientation])
        canonical_reference[orientation] = dict(reference[orientation])
        for selected, inspection, read_groups, programs, selected_label in (
            (
                canonical_observed[orientation],
                observed[orientation],
                observed_read_groups,
                observed_programs,
                f"Step 06 benchmark {orientation.upper()}",
            ),
            (
                canonical_reference[orientation],
                reference[orientation],
                reference_read_groups,
                reference_programs,
                f"retained Step 06 {orientation.upper()}",
            ),
        ):
            decoded = _canonicalize_step06_records(
                bytes(inspection["decoded"]),
                read_group_aliases=read_groups,
                program_aliases=programs,
                label=f"{selected_label} decoded SAM",
            )
            selected["decoded"] = decoded
            selected["records"] = _sam_records(decoded, selected_label)
            selected["indexed"] = _canonicalize_step06_records(
                bytes(inspection["indexed"]),
                read_group_aliases=read_groups,
                program_aliases=programs,
                label=f"{selected_label} indexed SAM",
            )
        bam_members[orientation] = _require_indexed_bam_parity(
            canonical_observed[orientation],
            canonical_reference[orientation],
            observed_header=observed_header,
            reference_header=reference_header,
            label=f"Step 06 {orientation.upper()}",
        )

    counts_data = outputs["counts"].read_bytes()
    retained_counts_data = retained["counts"].read_bytes()
    if counts_data != retained_counts_data:
        raise BenchmarkSetupError("Step 06 counts TSV differs from the retained output")
    observed_counts = _parse_step06_counts(counts_data, sample_id, "Step 06 counts")
    retained_counts = _parse_step06_counts(
        retained_counts_data, sample_id, "retained Step 06 counts"
    )
    fwd_records = canonical_observed["fwd"]["records"]
    rev_records = canonical_observed["rev"]["records"]
    if not isinstance(fwd_records, tuple) or not isinstance(rev_records, tuple):
        raise BenchmarkSetupError("Step 06 decoded record boundary is invalid")
    independent_counts = {
        "sample_id": sample_id,
        **_independent_step06_counts(input_records, fwd_records, rev_records),
    }
    if observed_counts != independent_counts or retained_counts != independent_counts:
        raise BenchmarkSetupError("Step 06 independent flag and aggregate counts differ")

    members: list[tuple[str, bytes]] = [
        ("counts", counts_data),
        (
            "independent-counts",
            json.dumps(independent_counts, sort_keys=True, separators=(",", ":")).encode()
            + b"\n",
        ),
    ]
    for orientation in ("fwd", "rev"):
        members.extend(
            (f"{orientation}/{name}", data)
            for name, data in bam_members[orientation]
        )
    _write_bundle(trial / "parity.bin", members)

    for key in ("fwd_bam", "fwd_bai", "rev_bam", "rev_bai", "counts"):
        outputs[key].unlink()
    for key in ("orientation_root", "counts_root"):
        if any((trial / paths[key]).iterdir()):
            raise BenchmarkSetupError("Step 06 benchmark retained publication residue")


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
        report = _validation_report(root, cohort, partition)
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
    report = _validation_report(trial / "qc", cohort)
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


def _load_variant_module(
    source: Path, module_name: str, relative_path: str, label: str
) -> Any:
    loaded = tuple(
        name for name in sys.modules if name == "emrys" or name.startswith("emrys.")
    )
    if loaded:
        raise BenchmarkSetupError(f"{label} imported EMRYS before source binding")
    source_root = _real_directory(source / "src", "variant Python source root")
    sys.path.insert(0, str(source_root))
    try:
        module = importlib.import_module(module_name)
    finally:
        sys.path.pop(0)
    expected_module = (source_root / relative_path).resolve(strict=True)
    observed_module = Path(str(module.__file__)).resolve(strict=True)
    if observed_module != expected_module:
        raise BenchmarkSetupError(
            f"{label} imported foreign source: {observed_module}"
        )
    return module


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
    module = _load_variant_module(
        source,
        "emrys.libraries.alignments.bam",
        "emrys/libraries/alignments/bam.py",
        "alignment signature producer",
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


def _setup_reference_contig_membership(trial: Path, contig_count: int) -> None:
    retained = RETAINED_CASE_BY_NAME["reference-contig-membership"]
    if contig_count not in retained.values:
        raise BenchmarkSetupError("reference contig count is not registered")
    with (trial / "reference.fa").open(
        "x", encoding="ascii", newline="\n"
    ) as stream:
        for index in range(contig_count):
            stream.write(f">contig-{index:08d}\nA\n")


def _produce_reference_contig_membership(trial: Path, source: Path) -> None:
    module = _load_variant_module(
        source,
        "emrys.libraries.references.contigs",
        "emrys/libraries/references/contigs.py",
        "reference contig producer",
    )
    observed = module.parse_fasta(
        _real_file(trial / "reference.fa", "reference contig fixture")
    )
    if type(observed) is not list or any(
        type(row) is not tuple
        or len(row) != 2
        or type(row[0]) is not str
        or type(row[1]) is not int
        for row in observed
    ):
        raise BenchmarkSetupError("reference contig parser returned an invalid shape")
    with (trial / "observed.tsv").open(
        "x", encoding="utf-8", newline="\n"
    ) as stream:
        for name, length in observed:
            stream.write(f"{name}\t{length}\n")


def _validate_reference_contig_membership(
    trial: Path, contig_count: int
) -> None:
    retained = RETAINED_CASE_BY_NAME["reference-contig-membership"]
    if contig_count not in retained.values:
        raise BenchmarkSetupError("reference contig count is not registered")
    expected = "".join(
        f"contig-{index:08d}\t1\n" for index in range(contig_count)
    ).encode("ascii")
    observed = _real_file(
        trial / "observed.tsv", "reference contig observation"
    ).read_bytes()
    if observed != expected:
        raise BenchmarkSetupError(
            "reference contig order, name, length, or count differs"
        )
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
        if arguments.case == "reference-contig-membership":
            _setup_reference_contig_membership(trial, arguments.value)
        elif retained_case.stage == 0:
            _setup_alignment_signatures(trial, arguments.value)
        elif retained_case.stage == 2:
            _setup_step02(context, trial, arguments.value)
        elif retained_case.stage == 4:
            _setup_step04(context, trial, arguments.value)
        elif retained_case.stage == 5:
            _setup_step05(context, trial, arguments.value)
        elif retained_case.stage == 6:
            _setup_step06(context, trial, arguments.value)
        elif retained_case.stage == 7:
            _setup_step07(context, trial, arguments.value)
        else:
            _setup_step08(context, trial, arguments.case, arguments.value)
    elif arguments.operation == "_produce":
        source = _source(context, arguments.variant)
        if arguments.case == "reference-contig-membership":
            _produce_reference_contig_membership(trial, source)
        elif retained_case.stage == 0:
            _produce_alignment_signatures(trial, source)
        elif retained_case.stage == 2:
            _produce_step02(context, trial, source)
        elif retained_case.stage == 4:
            _produce_step04(context, trial, source)
        elif retained_case.stage == 5:
            _produce_step05(context, trial, source)
        elif retained_case.stage == 6:
            _produce_step06(context, trial, source)
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
    elif arguments.case == "reference-contig-membership":
        _validate_reference_contig_membership(trial, arguments.value)
    elif retained_case.stage == 0:
        _validate_alignment_signatures(trial)
    elif retained_case.stage == 2:
        _validate_step02(context, trial)
    elif retained_case.stage == 4:
        _validate_step04(context, trial)
    elif retained_case.stage == 5:
        _validate_step05(context, trial)
    elif retained_case.stage == 6:
        _validate_step06(context, trial)
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


def _phase_resources_complete(
    phase_path: Path,
    trials_path: Path,
    manifest: Mapping[str, Any],
) -> tuple[bool, str]:
    expected_trials: dict[tuple[str, str, str, str, str], str] = {}
    try:
        for case in manifest["cases"]:
            case_name = str(case["name"])
            variants = tuple(str(variant["name"]) for variant in case["variants"])
            for value in case["values"]:
                for trial_kind, count, directory in (
                    ("warmup", int(case["warmup_repetitions"]), "warmups"),
                    ("measured", int(case["repetitions"]), "trials"),
                ):
                    for repetition in range(1, count + 1):
                        for variant in variants:
                            key = (
                                case_name,
                                str(value),
                                variant,
                                trial_kind,
                                str(repetition),
                            )
                            trial = (
                                phase_path.parent
                                / directory
                                / case_name
                                / str(value)
                                / f"rep-{repetition:02d}"
                                / variant
                            )
                            if key in expected_trials:
                                return False, "comparison manifest repeats a trial identity"
                            expected_trials[key] = str(trial)
    except (KeyError, TypeError, ValueError) as exc:
        return False, f"comparison manifest is invalid: {exc}"

    try:
        with trials_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, dialect="excel-tab")
            if tuple(reader.fieldnames or ()) != COMPARISON_TRIAL_FIELDS:
                return False, "comparison trials header differs"
            trial_rows = list(reader)
        with phase_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream, dialect="excel-tab")
            if tuple(reader.fieldnames or ()) != PHASE_RESOURCE_FIELDS:
                return False, "phase resource header differs"
            phase_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return False, f"phase resource evidence is unreadable: {exc}"
    if any(
        None in row or any(value is None for value in row.values())
        for row in (*trial_rows, *phase_rows)
    ):
        return False, "phase resource evidence contains malformed rows"

    trial_by_key: dict[tuple[str, str, str, str, str], Mapping[str, str]] = {}
    for row in trial_rows:
        key = tuple(row[field] for field in COMPARISON_TRIAL_FIELDS[:5])
        if key in trial_by_key:
            return False, "comparison trials contain a duplicate identity"
        trial_by_key[key] = row
    if set(trial_by_key) != set(expected_trials):
        return False, "comparison trial roster differs from the manifest"

    phase_by_key: dict[
        tuple[str, str, str, str, str, str], Mapping[str, str]
    ] = {}
    for row in phase_rows:
        key = (
            row["case"],
            row["value"],
            row["variant"],
            row["trial_kind"],
            row["repetition"],
            row["phase"],
        )
        if key in phase_by_key:
            return False, "phase resources contain a duplicate identity"
        phase_by_key[key] = row
    expected_phases = {
        (*key, phase) for key in expected_trials for phase in PHASES
    }
    if set(phase_by_key) != expected_phases:
        return False, "phase resource roster differs from the manifest"

    metric_pairs = (
        ("exit_code", "producer_exit_code"),
        ("wall_seconds", "producer_wall_seconds"),
        ("cpu_seconds", "producer_cpu_seconds"),
        ("max_rss_kib", "producer_max_rss_kib"),
        ("input_blocks", "producer_input_blocks"),
        ("output_blocks", "producer_output_blocks"),
    )
    for key, expected_trial in expected_trials.items():
        trial = trial_by_key[key]
        if (
            trial["status"] != "pass"
            or trial["setup_exit_code"] != "0"
            or trial["producer_exit_code"] != "0"
            or trial["validator_exit_code"] != "0"
            or trial["artifact_match_baseline"] != "yes"
            or len(trial["artifact_set_sha256"]) != 64
            or any(
                character not in "0123456789abcdef"
                for character in trial["artifact_set_sha256"]
            )
            or trial["trial_dir"] != expected_trial
        ):
            return False, "comparison trial is not one exact passing trial"
        for phase in PHASES:
            row = phase_by_key[(*key, phase)]
            if (
                row["schema_version"] != PHASE_RESOURCE_SCHEMA
                or row["state"] != "passed"
                or row["exit_code"] != "0"
                or row["trial_dir"] != expected_trial
            ):
                return False, "phase resource row is not one exact passing phase"
            try:
                wall = float(row["wall_seconds"])
                cpu = float(row["cpu_seconds"])
                integers = tuple(
                    int(row[field])
                    for field in ("max_rss_kib", "input_blocks", "output_blocks")
                )
            except (TypeError, ValueError):
                return False, "phase resource row has invalid numeric metrics"
            if (
                not math.isfinite(wall)
                or not math.isfinite(cpu)
                or wall < 0
                or cpu < 0
                or any(value < 0 for value in integers)
            ):
                return False, "phase resource row has invalid numeric metrics"
        producer = phase_by_key[(*key, "producer")]
        if any(producer[phase_field] != trial[trial_field] for phase_field, trial_field in metric_pairs):
            return False, "producer phase metrics differ from comparison trials"
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
    runtime_samtools = _real_file(
        runtime_prefix / "bin/samtools", "selected samtools", executable=True
    )
    if not os.path.samefile(runtime_samtools, e2e.runtime_samtools):
        raise BenchmarkSetupError("selected samtools differs from retained E2E authority")
    if not os.path.samefile(repo.python, e2e.runtime_sha256_python):
        raise BenchmarkSetupError(
            "workflow Python differs from retained E2E SHA-256 authority"
        )
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
        "sample_id": e2e.sample_id,
        "retained_step01_bam": _artifact_context(e2e.retained_step01_bam),
        "retained_step02_bam": _artifact_context(e2e.retained_step02_bam),
        "retained_step02_bai": _artifact_context(e2e.retained_step02_bai),
        "retained_step04_bam": _artifact_context(e2e.retained_step04_bam),
        "retained_step04_bai": _artifact_context(e2e.retained_step04_bai),
        "retained_step04_metrics": _artifact_context(e2e.retained_step04_metrics),
        "retained_step04_run_token": e2e.retained_step04_run_token,
        "retained_picard_jar": _artifact_context(e2e.retained_picard_jar),
        "retained_reference_fasta": _artifact_context(e2e.retained_reference_fasta),
        "retained_reference_fai": _artifact_context(e2e.retained_reference_fai),
        "retained_reference_dict": _artifact_context(e2e.retained_reference_dict),
        "retained_step05_bam": _artifact_context(e2e.retained_step05_bam),
        "retained_step05_bai": _artifact_context(e2e.retained_step05_bai),
        "retained_step05_run_token": e2e.retained_step05_run_token,
        "retained_step06_fwd_bam": _artifact_context(e2e.retained_step06_fwd_bam),
        "retained_step06_fwd_bai": _artifact_context(e2e.retained_step06_fwd_bai),
        "retained_step06_rev_bam": _artifact_context(e2e.retained_step06_rev_bam),
        "retained_step06_rev_bai": _artifact_context(e2e.retained_step06_rev_bai),
        "retained_step06_counts": _artifact_context(e2e.retained_step06_counts),
        "retained_step06_run_token": e2e.retained_step06_run_token,
        "retained_step06_threads": e2e.retained_step06_threads,
        "runtime_bash": str(e2e.runtime_bash),
        "runtime_gatk": str(e2e.runtime_gatk),
        "runtime_java": str(e2e.runtime_java),
        "runtime_picard_jar": str(e2e.runtime_picard_jar),
        "runtime_samtools": str(e2e.runtime_samtools),
        "runtime_sha256_python": str(e2e.runtime_sha256_python),
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
    result_trials = results / "trials.tsv"
    phase_resources = results / "phase-resources.tsv"
    complete, completion_detail = (
        _comparison_summary_complete(result_summary, manifest)
        if result_summary.is_file()
        else (False, "comparison summary was not published")
    )
    phase_complete, phase_completion_detail = (
        _phase_resources_complete(phase_resources, result_trials, manifest)
        if phase_resources.is_file() and result_trials.is_file()
        else (False, "phase resource evidence was not published")
    )
    passed = completed.returncode == 0 and complete and phase_complete
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
            "comparison_trials": (
                _artifact(result_trials) if result_trials.is_file() else None
            ),
            "phase_resources": (
                _artifact(phase_resources) if phase_resources.is_file() else None
            ),
            "comparison_completeness": completion_detail,
            "phase_resource_completeness": phase_completion_detail,
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
    _real_file(runtime / "bin/samtools", "samtools", executable=True)
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
