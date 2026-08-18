#!/usr/bin/env python3
"""Benchmark explicit NORAD owner commands across resource values.

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

SCHEMA_VERSION = "norad.resource-benchmark.v1"
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


def _load_manifest(path: Path) -> tuple[BenchmarkCase, ...]:
    try:
        document = yaml.safe_load(path.read_bytes())
    except (OSError, yaml.YAMLError) as exc:
        raise BenchmarkError(f"Could not load benchmark manifest {path}: {exc}") from exc
    if not isinstance(document, Mapping) or set(document) != {
        "schema_version",
        "cases",
    }:
        raise BenchmarkError("Benchmark manifest keys must be schema_version and cases")
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


def _expand(argv: Sequence[str], *, value: int, trial_dir: Path) -> tuple[str, ...]:
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
    templates: Sequence[str], *, value: int, trial: Path
) -> str:
    if not templates:
        return ""
    trial_root = trial.resolve(strict=True)
    rows: list[dict[str, Any]] = []
    bundle = hashlib.sha256()
    for ordinal, template in enumerate(templates, start=1):
        expanded = _expand((template,), value=value, trial_dir=trial)[0]
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


def run(manifest: Path, output: Path, *, execute: bool) -> int:
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
