#!/usr/bin/env python3
"""Benchmark explicit EMRYS owner commands across resource values.

This opt-in operator utility is deliberately outside the normal test suite.  It
does not discover inputs or construct scientific commands: a reviewed manifest
provides exact argv arrays for setup, producer, and validator commands.
Optional trial-local artifacts are hashed and compared byte-for-byte across
resource values; generated benchmark state belongs outside the repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import resource
import shlex
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "emrys.resource-benchmark.v1"
COMPARISON_SCHEMA_VERSION = "emrys.resource-benchmark.v2"
REQUIRED_CASE_FIELDS = {
    "name",
    "values",
    "repetitions",
    "setup_argv",
    "producer_argv",
    "validator_argv",
}
OPTIONAL_CASE_FIELDS = {"artifact_paths"}
RESULT_FIELDS = (
    "case",
    "value",
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
SUMMARY_FIELDS = (
    "case",
    "value",
    "successful_repetitions",
    "median_wall_seconds",
    "median_cpu_seconds",
    "median_max_rss_kib",
    "median_input_blocks",
    "median_output_blocks",
    "recommended",
)
COMPARISON_CASE_FIELDS = (REQUIRED_CASE_FIELDS - {"producer_argv", "setup_argv"}) | {
    "artifact_paths",
    "baseline_variant",
    "variants",
    "warmup_repetitions",
}
COMPARISON_RESULT_FIELDS = (
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


class BenchmarkError(RuntimeError):
    """A benchmark manifest or execution boundary is invalid."""


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """One closed resource sweep over an exact command template."""

    name: str
    values: tuple[int, ...]
    repetitions: int
    setup_argv: tuple[str, ...] | None
    producer_argv: tuple[str, ...]
    validator_argv: tuple[str, ...]
    artifact_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComparisonVariant:
    name: str
    producer_argv: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComparisonCase:
    name: str
    values: tuple[int, ...]
    repetitions: int
    warmup_repetitions: int
    baseline_variant: str
    setup_argv: tuple[str, ...] | None
    variants: tuple[ComparisonVariant, ...]
    validator_argv: tuple[str, ...]
    artifact_paths: tuple[str, ...]


def _argv(value: Any, label: str, *, optional: bool = False) -> tuple[str, ...] | None:
    if value is None and optional:
        return None
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(part, str) or not part for part in value)
    ):
        raise BenchmarkError(f"{label} must be a nonempty argv string array")
    return tuple(value)


def _artifact_paths(value: Any, label: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if (
        not isinstance(value, list)
        or not value
        or any(
            not isinstance(path, str)
            or not path
            or "{trial_dir}" not in path
            for path in value
        )
        or len(value) != len(set(value))
    ):
        raise BenchmarkError(
            f"{label} must be null or distinct paths containing {{trial_dir}}"
        )
    return tuple(value)


def _load_document(path: Path) -> Mapping[str, Any]:
    try:
        document = yaml.safe_load(path.read_bytes())
    except (OSError, yaml.YAMLError) as exc:
        raise BenchmarkError(f"Could not load benchmark manifest {path}: {exc}") from exc
    if not isinstance(document, Mapping) or set(document) != {
        "schema_version",
        "cases",
    }:
        raise BenchmarkError("Benchmark manifest keys must be schema_version and cases")
    return document


def _load_manifest(path: Path) -> tuple[BenchmarkCase, ...]:
    document = _load_document(path)
    if document["schema_version"] != SCHEMA_VERSION:
        raise BenchmarkError(f"schema_version must be {SCHEMA_VERSION}")
    raw_cases = document["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise BenchmarkError("cases must be a nonempty array")
    cases: list[BenchmarkCase] = []
    names: set[str] = set()
    for index, raw in enumerate(raw_cases):
        if (
            not isinstance(raw, Mapping)
            or not REQUIRED_CASE_FIELDS.issubset(raw)
            or not set(raw).issubset(REQUIRED_CASE_FIELDS | OPTIONAL_CASE_FIELDS)
        ):
            allowed = REQUIRED_CASE_FIELDS | OPTIONAL_CASE_FIELDS
            raise BenchmarkError(
                f"cases[{index}] keys must include "
                f"{', '.join(sorted(REQUIRED_CASE_FIELDS))} and may include "
                f"{', '.join(sorted(OPTIONAL_CASE_FIELDS))}; "
                f"allowed keys are {', '.join(sorted(allowed))}"
            )
        name = raw["name"]
        if (
            not isinstance(name, str)
            or not name
            or not all(character.isalnum() or character in "._-" for character in name)
        ):
            raise BenchmarkError(f"cases[{index}].name must be one safe identifier")
        if name in names:
            raise BenchmarkError(f"Duplicate benchmark case name: {name}")
        names.add(name)
        values = raw["values"]
        if (
            not isinstance(values, list)
            or not values
            or any(isinstance(value, bool) or not isinstance(value, int) or value < 1 for value in values)
            or len(values) != len(set(values))
        ):
            raise BenchmarkError(
                f"cases[{index}].values must be distinct positive integers"
            )
        repetitions = raw["repetitions"]
        if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 1:
            raise BenchmarkError(
                f"cases[{index}].repetitions must be a positive integer"
            )
        producer = _argv(raw["producer_argv"], f"cases[{index}].producer_argv")
        validator = _argv(raw["validator_argv"], f"cases[{index}].validator_argv")
        assert producer is not None and validator is not None
        cases.append(
            BenchmarkCase(
                name=name,
                values=tuple(values),
                repetitions=repetitions,
                setup_argv=_argv(
                    raw["setup_argv"], f"cases[{index}].setup_argv", optional=True
                ),
                producer_argv=producer,
                validator_argv=validator,
                artifact_paths=_artifact_paths(
                    raw.get("artifact_paths"), f"cases[{index}].artifact_paths"
                ),
            )
        )
    return tuple(cases)


def _safe_name(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."} or not all(character.isascii() and (character.isalnum() or character in "._-") for character in value):
        raise BenchmarkError(f"{label} must be one safe identifier")
    return value


def _load_comparison_manifest(path: Path) -> tuple[ComparisonCase, ...]:
    document = _load_document(path)
    if document["schema_version"] != COMPARISON_SCHEMA_VERSION:
        raise BenchmarkError(f"schema_version must be {COMPARISON_SCHEMA_VERSION}")
    raw_cases = document["cases"]
    if not isinstance(raw_cases, list) or not raw_cases:
        raise BenchmarkError("cases must be a nonempty array")
    cases: list[ComparisonCase] = []
    names: set[str] = set()
    for index, raw in enumerate(raw_cases):
        if not isinstance(raw, Mapping) or set(raw) not in (COMPARISON_CASE_FIELDS, COMPARISON_CASE_FIELDS | {"setup_argv"}):
            raise BenchmarkError(f"cases[{index}] has invalid comparison keys")
        label = f"cases[{index}]"
        name = _safe_name(raw["name"], f"{label}.name")
        if any(existing.casefold() == name.casefold() for existing in names):
            raise BenchmarkError(f"Duplicate benchmark case name: {name}")
        names.add(name)
        values = raw["values"]
        if (
            not isinstance(values, list)
            or not values
            or any(isinstance(value, bool) or not isinstance(value, int) or value < 1 for value in values)
            or len(values) != len(set(values))
        ):
            raise BenchmarkError(f"{label}.values must be distinct positive integers")
        repetitions, warmups = raw["repetitions"], raw["warmup_repetitions"]
        if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 3:
            raise BenchmarkError(f"{label}.repetitions must be an integer of at least 3")
        if isinstance(warmups, bool) or not isinstance(warmups, int) or warmups < 0:
            raise BenchmarkError(f"{label}.warmup_repetitions must be nonnegative")
        raw_variants = raw["variants"]
        if not isinstance(raw_variants, list) or len(raw_variants) < 2:
            raise BenchmarkError(f"{label}.variants must contain at least two variants")
        variants: list[ComparisonVariant] = []
        variant_names: set[str] = set()
        for variant_index, raw_variant in enumerate(raw_variants):
            variant_label = f"{label}.variants[{variant_index}]"
            if not isinstance(raw_variant, Mapping) or set(raw_variant) != {
                "name",
                "producer_argv",
            }:
                raise BenchmarkError(f"{variant_label} has invalid keys")
            variant_name = _safe_name(raw_variant["name"], f"{variant_label}.name")
            if any(existing.casefold() == variant_name.casefold() for existing in variant_names):
                raise BenchmarkError(f"Duplicate variant name in case {name}: {variant_name}")
            variant_names.add(variant_name)
            producer = _argv(raw_variant["producer_argv"], f"{variant_label}.producer_argv")
            assert producer is not None
            variants.append(ComparisonVariant(variant_name, producer))
        baseline = _safe_name(raw["baseline_variant"], f"{label}.baseline_variant")
        if baseline not in variant_names:
            raise BenchmarkError(f"{label}.baseline_variant must name a variant")
        validator = _argv(raw["validator_argv"], f"{label}.validator_argv")
        assert validator is not None
        artifacts = _artifact_paths(raw["artifact_paths"], f"{label}.artifact_paths")
        if not artifacts:
            raise BenchmarkError(f"{label}.artifact_paths must be nonempty")
        cases.append(
            ComparisonCase(
                name,
                tuple(values),
                repetitions,
                warmups,
                baseline,
                _argv(raw.get("setup_argv"), f"{label}.setup_argv", optional=True),
                tuple(variants),
                validator,
                artifacts,
            )
        )
    return tuple(cases)


def _expand(argv: Sequence[str], *, value: int, trial_dir: Path, variant: str | None = None) -> tuple[str, ...]:
    if variant is not None:
        argv = tuple(part.replace("{variant}", variant) for part in argv)
    replacements = {"{value}": str(value), "{trial_dir}": str(trial_dir)}
    return tuple(
        part.replace("{value}", replacements["{value}"]).replace(
            "{trial_dir}", replacements["{trial_dir}"]
        )
        for part in argv
    )


def _run(argv: Sequence[str], *, stdout: Path, stderr: Path) -> int:
    with stdout.open("xb") as stdout_handle, stderr.open("xb") as stderr_handle:
        completed = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            check=False,
        )
    return completed.returncode


def _run_timed(
    argv: Sequence[str], *, stdout: Path, stderr: Path, usage: Path
) -> tuple[int, float, float, int, int, int]:
    if not hasattr(os, "wait4"):
        raise BenchmarkError("Execution requires os.wait4 child-resource accounting")
    with stdout.open("xb") as stdout_handle, stderr.open("xb") as stderr_handle:
        started = time.monotonic()
        process = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )
        try:
            _, wait_status, child_usage = os.wait4(process.pid, 0)
        except BaseException:
            process.kill()
            process.wait()
            raise
        process.returncode = os.waitstatus_to_exitcode(wait_status)
        wall_seconds = time.monotonic() - started
    cpu_seconds = float(child_usage.ru_utime + child_usage.ru_stime)
    max_rss_kib = int(child_usage.ru_maxrss)
    if sys.platform == "darwin":
        max_rss_kib //= 1024
    input_blocks = int(child_usage.ru_inblock)
    output_blocks = int(child_usage.ru_oublock)
    usage.write_text(
        (
            f"wall_seconds\t{wall_seconds:.6f}\n"
            f"cpu_seconds\t{cpu_seconds:.6f}\n"
            f"max_rss_kib\t{max_rss_kib}\n"
            f"input_blocks\t{input_blocks}\n"
            f"output_blocks\t{output_blocks}\n"
        ),
        encoding="utf-8",
    )
    return (
        process.returncode,
        wall_seconds,
        cpu_seconds,
        max_rss_kib,
        input_blocks,
        output_blocks,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _record_artifacts(
    templates: Sequence[str], *, value: int, trial: Path, variant: str | None = None
) -> str:
    if not templates:
        return ""
    trial_root = trial.resolve(strict=True)
    rows: list[dict[str, Any]] = []
    bundle = hashlib.sha256()
    for ordinal, template in enumerate(templates, start=1):
        expanded = _expand(
            (template,), value=value, trial_dir=trial, variant=variant
        )[0]
        path = Path(expanded)
        resolved = path.resolve(strict=True)
        if (
            path.is_symlink()
            or not resolved.is_file()
            or not resolved.is_relative_to(trial_root)
        ):
            raise BenchmarkError(
                f"Artifact {ordinal} must be a real file inside its trial: {path}"
            )
        size = resolved.stat().st_size
        digest = _sha256(resolved)
        bundle.update(f"{ordinal}\0{size}\0{digest}\n".encode())
        rows.append(
            {
                "ordinal": ordinal,
                "path": str(resolved),
                "bytes": size,
                "sha256": digest,
            }
        )
    with (trial / "producer.artifacts.tsv").open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("ordinal", "path", "bytes", "sha256"),
            dialect="excel-tab",
        )
        writer.writeheader()
        writer.writerows(rows)
    return bundle.hexdigest()


def _write_summary(results: Sequence[dict[str, Any]], path: Path) -> None:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        if row["status"] == "pass":
            grouped[row["case"], int(row["value"])].append(row)
    fastest: dict[str, float] = {}
    medians: dict[tuple[str, int], float] = {}
    for key, rows in grouped.items():
        median = statistics.median(float(row["producer_wall_seconds"]) for row in rows)
        medians[key] = median
        fastest[key[0]] = min(fastest.get(key[0], median), median)
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS, dialect="excel-tab")
        writer.writeheader()
        for case_name, value in sorted(grouped):
            rows = grouped[case_name, value]
            cpu_values = [float(row["producer_cpu_seconds"]) for row in rows]
            rss_values = [
                int(row["producer_max_rss_kib"])
                for row in rows
                if row["producer_max_rss_kib"] != ""
            ]
            input_blocks = [
                int(row["producer_input_blocks"]) for row in rows
            ]
            output_blocks = [
                int(row["producer_output_blocks"]) for row in rows
            ]
            recommended_values = [
                candidate
                for (candidate_case, candidate), median in medians.items()
                if candidate_case == case_name and median <= fastest[case_name] * 1.05
            ]
            writer.writerow(
                {
                    "case": case_name,
                    "value": value,
                    "successful_repetitions": len(rows),
                    "median_wall_seconds": f"{medians[case_name, value]:.6f}",
                    "median_cpu_seconds": f"{statistics.median(cpu_values):.6f}",
                    "median_max_rss_kib": (
                        f"{statistics.median(rss_values):.0f}" if rss_values else ""
                    ),
                    "median_input_blocks": (
                        f"{statistics.median(input_blocks):.0f}"
                    ),
                    "median_output_blocks": (
                        f"{statistics.median(output_blocks):.0f}"
                    ),
                    "recommended": (
                        "yes" if value == min(recommended_values) else "no"
                    ),
                }
            )


def _write_comparison_summary(cases: Sequence[ComparisonCase], results: Sequence[dict[str, Any]], path: Path) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMPARISON_SUMMARY_FIELDS, dialect="excel-tab")
        writer.writeheader()
        for case in cases:
            for value in case.values:
                measured = [row for row in results if row["case"] == case.name and int(row["value"]) == value and row["trial_kind"] == "measured"]
                warmups = [row for row in results if row["case"] == case.name and int(row["value"]) == value and row["trial_kind"] == "warmup"]
                warmups_valid = len(warmups) == case.warmup_repetitions * len(case.variants) and all(row["status"] == "pass" for row in warmups)
                valid = warmups_valid and len(measured) == case.repetitions * len(case.variants) and all(row["status"] == "pass" for row in measured)
                by_key = {(row["variant"], int(row["repetition"])): row for row in measured}
                for variant in case.variants:
                    rows = [row for row in measured if row["variant"] == variant.name and row["status"] == "pass"]
                    walls = [float(row["producer_wall_seconds"]) for row in rows]
                    cpu = [float(row["producer_cpu_seconds"]) for row in rows]
                    rss = [int(row["producer_max_rss_kib"]) for row in rows]
                    input_blocks = [int(row["producer_input_blocks"]) for row in rows]
                    output_blocks = [int(row["producer_output_blocks"]) for row in rows]
                    median_wall = statistics.median(walls) if walls else None
                    mad = statistics.median(abs(observed - median_wall) for observed in walls) if walls else None
                    pairs = (
                        [
                            (
                                float(by_key[case.baseline_variant, repetition]["producer_wall_seconds"]),
                                float(by_key[variant.name, repetition]["producer_wall_seconds"]),
                            )
                            for repetition in range(1, case.repetitions + 1)
                        ]
                        if valid
                        else []
                    )
                    writer.writerow(
                        {
                            "case": case.name,
                            "value": value,
                            "baseline_variant": case.baseline_variant,
                            "variant": variant.name,
                            "required_repetitions": case.repetitions,
                            "successful_repetitions": len(rows),
                            "paired_repetitions": len(pairs),
                            "warmups_valid": "yes" if warmups_valid else "no",
                            "comparison_valid": "yes" if valid else "no",
                            "artifact_parity": "yes" if len(rows) == case.repetitions else "no",
                            "median_wall_seconds": f"{median_wall:.6f}" if median_wall is not None else "",
                            "wall_mad_seconds": f"{mad:.6f}" if mad is not None else "",
                            "wall_range_seconds": f"{max(walls) - min(walls):.6f}" if walls else "",
                            "median_cpu_seconds": f"{statistics.median(cpu):.6f}" if cpu else "",
                            "median_max_rss_kib": f"{statistics.median(rss):.0f}" if rss else "",
                            "median_input_blocks": f"{statistics.median(input_blocks):.0f}" if input_blocks else "",
                            "median_output_blocks": f"{statistics.median(output_blocks):.0f}" if output_blocks else "",
                            "median_paired_speedup_percent": (
                                f"{statistics.median(100 * (base - selected) / base for base, selected in pairs):.6f}" if pairs else ""
                            ),
                            "median_paired_speedup_ratio": (f"{statistics.median(base / selected for base, selected in pairs):.6f}" if pairs else ""),
                        }
                    )


def _run_resource(manifest: Path, output: Path, *, execute: bool) -> int:
    cases = _load_manifest(manifest)
    if output.exists() or output.is_symlink():
        raise BenchmarkError(f"Output directory must be absent: {output}")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise BenchmarkError(f"Output parent must be an existing real directory: {output.parent}")
    for case in cases:
        for value in case.values:
            for repetition in range(1, case.repetitions + 1):
                trial = output / "trials" / case.name / str(value) / f"rep-{repetition:02d}"
                print(f"CASE {case.name} value={value} repetition={repetition}")
                if case.setup_argv is not None:
                    print("  setup: " + shlex.join(_expand(case.setup_argv, value=value, trial_dir=trial)))
                print("  producer: " + shlex.join(_expand(case.producer_argv, value=value, trial_dir=trial)))
                print("  validator: " + shlex.join(_expand(case.validator_argv, value=value, trial_dir=trial)))
    if not execute:
        print("Dry-run complete; no benchmark state was written.")
        return 0

    output.mkdir(mode=0o700)
    results_path = output / "trials.tsv"
    results: list[dict[str, Any]] = []
    artifact_baselines: dict[str, str] = {}
    failed = False
    with results_path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS, dialect="excel-tab")
        writer.writeheader()
        for case in cases:
            for value in case.values:
                for repetition in range(1, case.repetitions + 1):
                    trial = output / "trials" / case.name / str(value) / f"rep-{repetition:02d}"
                    trial.mkdir(mode=0o700, parents=True)
                    setup_code = 0
                    if case.setup_argv is not None:
                        setup_code = _run(
                            _expand(case.setup_argv, value=value, trial_dir=trial),
                            stdout=trial / "setup.stdout.log",
                            stderr=trial / "setup.stderr.log",
                        )
                    producer_code = -1
                    validator_code = -1
                    wall_seconds = 0.0
                    cpu_seconds = 0.0
                    max_rss_kib: int | str = ""
                    input_blocks = 0
                    output_blocks = 0
                    artifact_set_sha256 = ""
                    artifact_match_baseline = ""
                    usage_path = trial / "producer.time.txt"
                    if setup_code == 0:
                        producer = _expand(
                            case.producer_argv, value=value, trial_dir=trial
                        )
                        (
                            producer_code,
                            wall_seconds,
                            cpu_seconds,
                            max_rss_kib,
                            input_blocks,
                            output_blocks,
                        ) = _run_timed(
                            producer,
                            stdout=trial / "producer.stdout.log",
                            stderr=trial / "producer.stderr.log",
                            usage=usage_path,
                        )
                    if producer_code == 0:
                        validator_code = _run(
                            _expand(case.validator_argv, value=value, trial_dir=trial),
                            stdout=trial / "validator.stdout.log",
                            stderr=trial / "validator.stderr.log",
                        )
                    if producer_code == validator_code == 0 and case.artifact_paths:
                        artifact_set_sha256 = _record_artifacts(
                            case.artifact_paths, value=value, trial=trial
                        )
                        baseline = artifact_baselines.setdefault(
                            case.name, artifact_set_sha256
                        )
                        artifact_match_baseline = (
                            "yes" if artifact_set_sha256 == baseline else "no"
                        )
                    status = (
                        "pass"
                        if setup_code == producer_code == validator_code == 0
                        and artifact_match_baseline != "no"
                        else "fail"
                    )
                    failed = failed or status == "fail"
                    row = {
                        "case": case.name,
                        "value": value,
                        "repetition": repetition,
                        "status": status,
                        "setup_exit_code": setup_code,
                        "producer_exit_code": producer_code,
                        "validator_exit_code": validator_code,
                        "producer_wall_seconds": f"{wall_seconds:.6f}",
                        "producer_cpu_seconds": f"{cpu_seconds:.6f}",
                        "producer_max_rss_kib": max_rss_kib,
                        "producer_input_blocks": input_blocks,
                        "producer_output_blocks": output_blocks,
                        "artifact_set_sha256": artifact_set_sha256,
                        "artifact_match_baseline": artifact_match_baseline,
                        "trial_dir": str(trial),
                    }
                    results.append(row)
                    writer.writerow(row)
                    handle.flush()
                    os.fsync(handle.fileno())
                    print(
                        f"RESULT {case.name} value={value} repetition={repetition} "
                        f"status={status} wall={wall_seconds:.3f}s"
                    )
    _write_summary(results, output / "summary.tsv")
    return 1 if failed else 0


def _comparison_order(case: ComparisonCase, repetition: int) -> tuple[ComparisonVariant, ...]:
    baseline = next(variant for variant in case.variants if variant.name == case.baseline_variant)
    variants = (
        baseline,
        *(variant for variant in case.variants if variant != baseline),
    )
    offset = (repetition - 1) % len(variants)
    return variants[offset:] + variants[:offset]


def _comparison_rounds(cases: Sequence[ComparisonCase], output: Path):
    for case in cases:
        for value in case.values:
            counts = (
                ("warmup", case.warmup_repetitions),
                ("measured", case.repetitions),
            )
            for kind, count in counts:
                for repetition in range(1, count + 1):
                    root = "warmups" if kind == "warmup" else "trials"
                    prefix = output / root / case.name / str(value) / f"rep-{repetition:02d}"
                    trials = tuple((variant, prefix / variant.name) for variant in _comparison_order(case, repetition))
                    yield case, value, kind, repetition, trials


def _run_comparison(manifest: Path, output: Path, *, execute: bool) -> int:
    cases = _load_comparison_manifest(manifest)
    if output.exists() or output.is_symlink():
        raise BenchmarkError(f"Output directory must be absent: {output}")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise BenchmarkError(f"Output parent must be an existing real directory: {output.parent}")
    rounds = list(_comparison_rounds(cases, output))
    for case, value, kind, repetition, trials in rounds:
        for variant, trial in trials:
            print(f"CASE {case.name} value={value} kind={kind} repetition={repetition} variant={variant.name}")
            for label, argv in (
                ("setup", case.setup_argv),
                ("producer", variant.producer_argv),
                ("validator", case.validator_argv),
            ):
                if argv is not None:
                    print(f"  {label}: " + shlex.join(_expand(argv, value=value, trial_dir=trial, variant=variant.name)))
    if not execute:
        print("Dry-run complete; no benchmark state was written.")
        return 0

    output.mkdir(mode=0o700)
    results: list[dict[str, Any]] = []
    variant_artifact_references: dict[tuple[str, int, str], str] = {}
    failed = False
    with (output / "trials.tsv").open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COMPARISON_RESULT_FIELDS, dialect="excel-tab")
        writer.writeheader()
        for case, value, trial_kind, repetition, trials in rounds:
            round_rows: list[dict[str, Any]] = []
            for variant, trial in trials:
                trial.mkdir(mode=0o700, parents=True)
                setup_code = 0
                if case.setup_argv is not None:
                    setup_code = _run(
                        _expand(
                            case.setup_argv,
                            value=value,
                            trial_dir=trial,
                            variant=variant.name,
                        ),
                        stdout=trial / "setup.stdout.log",
                        stderr=trial / "setup.stderr.log",
                    )
                producer_code = validator_code = -1
                wall = 0.0
                cpu = 0.0
                rss: int | str = ""
                input_blocks = output_blocks = 0
                artifact_sha256 = ""
                if setup_code == 0:
                    producer_code, wall, cpu, rss, input_blocks, output_blocks = _run_timed(
                        _expand(
                            variant.producer_argv,
                            value=value,
                            trial_dir=trial,
                            variant=variant.name,
                        ),
                        stdout=trial / "producer.stdout.log",
                        stderr=trial / "producer.stderr.log",
                        usage=trial / "producer.time.txt",
                    )
                if producer_code == 0:
                    validator_code = _run(
                        _expand(
                            case.validator_argv,
                            value=value,
                            trial_dir=trial,
                            variant=variant.name,
                        ),
                        stdout=trial / "validator.stdout.log",
                        stderr=trial / "validator.stderr.log",
                    )
                phase_pass = setup_code == producer_code == validator_code == 0
                if phase_pass:
                    artifact_sha256 = _record_artifacts(
                        case.artifact_paths,
                        value=value,
                        trial=trial,
                        variant=variant.name,
                    )
                round_rows.append(
                    {
                        "case": case.name,
                        "value": value,
                        "variant": variant.name,
                        "trial_kind": trial_kind,
                        "repetition": repetition,
                        "status": "pass" if phase_pass else "fail",
                        "setup_exit_code": setup_code,
                        "producer_exit_code": producer_code,
                        "validator_exit_code": validator_code,
                        "producer_wall_seconds": f"{wall:.6f}",
                        "producer_cpu_seconds": f"{cpu:.6f}",
                        "producer_max_rss_kib": rss,
                        "producer_input_blocks": input_blocks,
                        "producer_output_blocks": output_blocks,
                        "artifact_set_sha256": artifact_sha256,
                        "artifact_match_baseline": "",
                        "trial_dir": str(trial),
                    }
                )
            baseline = next(row for row in round_rows if row["variant"] == case.baseline_variant)
            baseline_sha256 = baseline["artifact_set_sha256"] if baseline["status"] == "pass" else ""
            for row in round_rows:
                if row["status"] == "pass" and baseline_sha256:
                    row["artifact_match_baseline"] = "yes" if row["artifact_set_sha256"] == baseline_sha256 else "no"
                    if row["artifact_match_baseline"] == "no":
                        row["status"] = "fail"
                elif row["status"] == "pass":
                    row["status"] = "fail"
                if row["status"] == "pass":
                    artifact_key = (case.name, value, str(row["variant"]))
                    reference = variant_artifact_references.setdefault(
                        artifact_key, str(row["artifact_set_sha256"])
                    )
                    if row["artifact_set_sha256"] != reference:
                        row["status"] = "fail"
                failed = failed or row["status"] == "fail"
                results.append(row)
                writer.writerow(row)
            handle.flush()
            os.fsync(handle.fileno())
    _write_comparison_summary(cases, results, output / "summary.tsv")
    return 1 if failed else 0


def run(manifest: Path, output: Path, *, execute: bool) -> int:
    if _load_document(manifest)["schema_version"] == COMPARISON_SCHEMA_VERSION:
        return _run_comparison(manifest, output, execute=execute)
    return _run_resource(manifest, output, execute=execute)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run every trial. Without this flag, print the exact commands and write nothing.",
    )
    arguments = parser.parse_args(argv)
    try:
        return run(
            arguments.manifest.resolve(strict=True),
            arguments.output.absolute(),
            execute=arguments.execute,
        )
    except (BenchmarkError, OSError) as exc:
        print(f"benchmark-stage-resources: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
