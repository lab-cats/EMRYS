#!/usr/bin/env python3
"""Disposable CI probe for Step 07 hashing amplification."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


SAMPLES = tuple(f"sample_{index:02d}" for index in range(1, 7))
ORIENTATIONS = ("FWD_like", "REV_like")
PARTITIONS = tuple(f"p{index:02d}" for index in range(1, 26))
COHORT = "probe"
STEP07_SHA256 = "52c79a455049f59fe79b692fa02b289b01108186fc7068c8fb669e05b8f49ba1"
FILE_CHECKS_SHA256 = "6e066085d7cdc8e142acd9c4171b7a25cb977d7d82a8bfddede7ee5bb07bafd9"
BENCHMARK_SHA256 = "0144d04c9b2a97242aaf84e6452a0a0e9b2226a58842ba8ff704015764bbc283"
RECEIPT_HEADER = (
    "cohort_id",
    "partition_id",
    "selector_type",
    "selector_value",
    "orientation",
    "vcf_path",
    "sample_manifest_sha256",
    "partition_manifest_sha256",
    "sample_count",
    "vcf_record_count",
)
HASH_WRAPPER = r"""#!/usr/bin/env bash
set -euo pipefail
target="${!#}"
size="$(stat --format=%s -- "$target")"
printf '%s\t%s\t%s\t%s\n' \
  "$EMRYS_PROBE_PARTITION" "$EMRYS_PROBE_HASH_MODE" "$size" "$target" \
  >> "$EMRYS_PROBE_HASH_LOG"
if [[ "$EMRYS_PROBE_HASH_MODE" == actual ]]; then
  exec "$EMRYS_PROBE_REAL_PYTHON" "$@"
fi
printf '%064d\n' 0
"""
BCFTOOLS_WRAPPER = r"""#!/usr/bin/env bash
set -euo pipefail
exec "$EMRYS_PROBE_PYTHON" "$EMRYS_PROBE_SCRIPT" bcftools "$@"
"""


class ProbeError(RuntimeError):
    """The disposable measurement is invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_root() -> Path:
    raw = os.environ.get("EMRYS_STEP07_HASH_FIXTURE", "")
    if not raw:
        raise ProbeError("EMRYS_STEP07_HASH_FIXTURE is required")
    root = Path(raw)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ProbeError(f"fixture root must be one real absolute directory: {root}")
    return root


def write_payload(path: Path, size: int, prefix: bytes = b"") -> None:
    remaining = size
    with path.open("xb") as handle:
        if prefix:
            handle.write(prefix)
            remaining -= len(prefix)
        block = b"A" * (1024 * 1024)
        while remaining:
            chunk = block[: min(remaining, len(block))]
            handle.write(chunk)
            remaining -= len(chunk)


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o700)


def assert_fixed_baseline(repo: Path) -> None:
    expected = {
        repo
        / (
            "src/emrys/stages/partitioned_cohort_mpileup/"
            "step_07_bcftools_mpileup_by_chrom_and_strand.sh"
        ): STEP07_SHA256,
        repo / "src/emrys/libraries/file_checks.sh": FILE_CHECKS_SHA256,
        repo / "scripts/benchmark_stage_resources.py": BENCHMARK_SHA256,
    }
    for path, digest in expected.items():
        if sha256_file(path) != digest:
            raise ProbeError(f"fixed-baseline file changed: {path}")


def seed(root: Path) -> None:
    repo = Path(__file__).resolve().parents[2]
    assert_fixed_baseline(repo)
    root.mkdir(mode=0o700)
    orientation_root = root / "orientation"
    orientation_root.mkdir()
    sample_manifest = root / "samples.tsv"
    sample_manifest.write_text(
        "sample_id\tcondition\n"
        + "".join(f"{sample}\tprobe\n" for sample in SAMPLES),
        encoding="utf-8",
    )
    partition_manifest = root / "partitions.tsv"
    partition_manifest.write_text(
        "partition_id\tselector_type\tselector_value\n"
        + "".join(
            f"{partition}\tregion\tchrProbe:{index}\n"
            for index, partition in enumerate(PARTITIONS, start=1)
        ),
        encoding="utf-8",
    )
    reference = root / "reference.fa"
    write_payload(reference, 256 * 1024 * 1024, b">chrProbe\n")
    (root / "reference.fa.fai").write_text(
        "chrProbe\t268435446\t10\t268435446\t268435447\n", encoding="utf-8"
    )
    bam_seed = root / "bam.payload"
    bai_seed = root / "bai.payload"
    write_payload(bam_seed, 64 * 1024 * 1024)
    write_payload(bai_seed, 1024 * 1024)
    for sample in SAMPLES:
        sample_root = orientation_root / sample
        sample_root.mkdir()
        for orientation in ORIENTATIONS:
            bam = sample_root / f"{sample}.{orientation}.bam"
            os.link(bam_seed, bam)
            os.link(bai_seed, Path(f"{bam}.bai"))
    write_executable(root / "hash-python", HASH_WRAPPER)
    write_executable(root / "fake-bcftools", BCFTOOLS_WRAPPER)
    with (root / "seed.tsv").open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, dialect="excel-tab")
        writer.writerow(("path", "bytes", "sha256"))
        for path in (reference, root / "reference.fa.fai", bam_seed, bai_seed):
            writer.writerow((path.name, path.stat().st_size, sha256_file(path)))


def append_atomic(path: Path, fields: Iterable[str]) -> None:
    data = ("\t".join(fields) + "\n").encode()
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND)
    try:
        if os.write(descriptor, data) != len(data):
            raise ProbeError(f"short append: {path}")
    finally:
        os.close(descriptor)


def fake_bcftools(arguments: list[str]) -> int:
    if not arguments:
        raise ProbeError("fake bcftools requires a subcommand")
    command, *rest = arguments
    partition = os.environ["EMRYS_PROBE_PARTITION"]
    log = Path(os.environ["EMRYS_PROBE_BCFTOOLS_LOG"])
    samples = os.environ["EMRYS_PROBE_SAMPLES"].split(",")
    detail = ""
    if command == "mpileup":
        orientation = next(
            (value for value in ORIENTATIONS if any(f".{value}.bam" in arg for arg in rest)),
            "",
        )
        if not orientation:
            raise ProbeError("fake mpileup could not identify orientation")
        detail = orientation
        print(orientation)
    elif command == "filter":
        try:
            output = Path(rest[rest.index("-o") + 1])
        except (ValueError, IndexError) as exc:
            raise ProbeError("fake filter requires -o") from exc
        detail = sys.stdin.read().strip()
        if detail not in ORIENTATIONS:
            raise ProbeError("fake filter received an invalid orientation")
        with output.open("x", encoding="utf-8") as handle:
            handle.write("##fileformat=VCFv4.2\n")
            handle.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT")
            handle.write("".join(f"\t{sample}" for sample in samples) + "\n")
            handle.write("chrProbe\t1\t.\tA\tG\t60\tPASS\tAD=20,4\tDP:AD")
            handle.write("\t12:10,2" * len(samples) + "\n")
    elif command == "view":
        if len(rest) != 2 or rest[0] not in ("-h", "-H"):
            raise ProbeError("fake view requires -h or -H and one path")
        detail = rest[0]
        want_header = rest[0] == "-h"
        with Path(rest[1]).open(encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("#") == want_header:
                    sys.stdout.write(line)
    elif command == "query":
        if len(rest) != 2 or rest[0] != "-l":
            raise ProbeError("fake query requires -l and one path")
        detail = "-l"
        with Path(rest[1]).open(encoding="utf-8") as handle:
            header = next(line for line in handle if line.startswith("#CHROM"))
        print("\n".join(header.rstrip("\n").split("\t")[9:]))
    else:
        raise ProbeError(f"unsupported fake bcftools subcommand: {command}")
    append_atomic(log, (partition, command, detail))
    return 0


def run_producer(mode: str, partition_count: int, trial: Path) -> None:
    root = require_root()
    repo = Path(__file__).resolve().parents[2]
    assert_fixed_baseline(repo)
    script = repo / (
        "src/emrys/stages/partitioned_cohort_mpileup/"
        "step_07_bcftools_mpileup_by_chrom_and_strand.sh"
    )
    hash_log = trial / "hash.tsv"
    bcftools_log = trial / "bcftools.tsv"
    hash_log.write_text("partition_id\tmode\tbytes\tpath\n", encoding="utf-8")
    bcftools_log.write_text("partition_id\tcommand\tdetail\n", encoding="utf-8")
    base_environment = os.environ.copy()
    base_environment.update(
        {
            "EMRYS_PROBE_HASH_MODE": mode,
            "EMRYS_PROBE_HASH_LOG": str(hash_log),
            "EMRYS_PROBE_BCFTOOLS_LOG": str(bcftools_log),
            "EMRYS_PROBE_REAL_PYTHON": sys.executable,
            "EMRYS_PROBE_PYTHON": sys.executable,
            "EMRYS_PROBE_SCRIPT": str(Path(__file__).resolve()),
            "EMRYS_PROBE_SAMPLES": ",".join(SAMPLES),
            "EMRYS_SHA256_PYTHON": str(root / "hash-python"),
            "EMRYS_REQUIRE_BOUND_SHA256": "1",
        }
    )
    for partition in PARTITIONS[:partition_count]:
        environment = base_environment | {
            "EMRYS_PROBE_PARTITION": partition,
            "EMRYS_RUN_TOKEN": f"{mode}-{partition}",
        }
        command = (
            "bash",
            str(script),
            "--cohort-id",
            COHORT,
            "--sample-manifest",
            str(root / "samples.tsv"),
            "--partition-manifest",
            str(root / "partitions.tsv"),
            "--partition-id",
            partition,
            "--orientation-root",
            str(root / "orientation"),
            "--reference-fasta",
            str(root / "reference.fa"),
            "--output-root",
            str(trial / "output"),
            "--bcftools-bin",
            str(root / "fake-bcftools"),
            "--no-clobber",
            "--execute",
        )
        completed = subprocess.run(command, env=environment, check=False)
        if completed.returncode:
            raise ProbeError(f"Step 07 failed for {mode} {partition}")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, dialect="excel-tab"))


def expected_hashes(root: Path) -> dict[str, int]:
    expected = {
        str(root / "samples.tsv"): 8,
        str(root / "partitions.tsv"): 8,
        str(root / "reference.fa"): 3,
        str(root / "reference.fa.fai"): 3,
    }
    for sample in SAMPLES:
        for orientation in ORIENTATIONS:
            bam = root / "orientation" / sample / f"{sample}.{orientation}.bam"
            expected[str(bam)] = 3
            expected[str(Path(f"{bam}.bai"))] = 3
    return expected


def validate_outputs(mode: str, partition_count: int, trial: Path) -> None:
    root = require_root()
    partitions = PARTITIONS[:partition_count]
    hash_rows = read_tsv(trial / "hash.tsv")
    expected = expected_hashes(root)
    expected_total = sum(expected.values()) * partition_count
    if len(hash_rows) != expected_total:
        raise ProbeError(f"expected {expected_total} hashes, got {len(hash_rows)}")
    logical_bytes = 0
    roster_lines: list[str] = []
    for partition in partitions:
        observed = Counter(
            row["path"] for row in hash_rows if row["partition_id"] == partition
        )
        if observed != Counter(expected):
            raise ProbeError(f"hash roster mismatch for {partition}")
        for path, count in sorted(expected.items()):
            size = Path(path).stat().st_size
            matching = [
                row
                for row in hash_rows
                if row["partition_id"] == partition and row["path"] == path
            ]
            if any(row["mode"] != mode or int(row["bytes"]) != size for row in matching):
                raise ProbeError(f"hash log metadata mismatch for {partition}: {path}")
            logical_bytes += size * count
            roster_lines.append(
                f"{partition}\t{Path(path).relative_to(root)}\t{count}\t{size}\n"
            )
    calls = read_tsv(trial / "bcftools.tsv")
    expected_calls = Counter(
        {
            ("mpileup", "FWD_like"): 1,
            ("mpileup", "REV_like"): 1,
            ("filter", "FWD_like"): 1,
            ("filter", "REV_like"): 1,
            ("view", "-h"): 4,
            ("view", "-H"): 4,
            ("query", "-l"): 4,
        }
    )
    for partition in partitions:
        observed = Counter(
            (row["command"], row["detail"])
            for row in calls
            if row["partition_id"] == partition
        )
        if observed != expected_calls:
            raise ProbeError(f"fake bcftools call roster mismatch for {partition}")
    if len(calls) != 16 * partition_count:
        raise ProbeError("fake bcftools call count is invalid")
    sample_hash = sha256_file(root / "samples.tsv") if mode == "actual" else "0" * 64
    partition_hash = (
        sha256_file(root / "partitions.tsv") if mode == "actual" else "0" * 64
    )
    normalized: list[str] = []
    for index, partition in enumerate(partitions, start=1):
        output = trial / "output" / COHORT / partition
        receipt = output / f"{COHORT}.{partition}.step07_outputs.tsv"
        rows = read_tsv(receipt)
        if tuple(rows[0]) != RECEIPT_HEADER or len(rows) != 2:
            raise ProbeError(f"receipt structure mismatch for {partition}")
        for row, orientation in zip(rows, ORIENTATIONS, strict=True):
            vcf = output / f"{COHORT}.{partition}.{orientation}.mpileup.vcf"
            if row != {
                "cohort_id": COHORT,
                "partition_id": partition,
                "selector_type": "region",
                "selector_value": f"chrProbe:{index}",
                "orientation": orientation,
                "vcf_path": str(vcf),
                "sample_manifest_sha256": sample_hash,
                "partition_manifest_sha256": partition_hash,
                "sample_count": str(len(SAMPLES)),
                "vcf_record_count": "1",
            }:
                raise ProbeError(f"receipt content mismatch for {partition} {orientation}")
            lines = vcf.read_text(encoding="utf-8").splitlines()
            header = next(line for line in lines if line.startswith("#CHROM"))
            if tuple(header.split("\t")[9:]) != SAMPLES:
                raise ProbeError(f"VCF sample order mismatch for {partition} {orientation}")
            if sum(not line.startswith("#") for line in lines) != 1:
                raise ProbeError(f"VCF record count mismatch for {partition} {orientation}")
            normalized.append(
                f"{partition}\tchrProbe:{index}\t{orientation}\t{len(SAMPLES)}\t1\t"
                f"{sha256_file(vcf)}\n"
            )
        if any(output.glob(f".{COHORT}.{partition}.step07.*")):
            raise ProbeError(f"Step 07 residue remains for {partition}")
    metrics = trial / "metrics.tsv"
    with metrics.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, dialect="excel-tab")
        writer.writerow(
            (
                "mode",
                "partitions",
                "samples",
                "hash_invocations",
                "logical_hash_bytes",
                "bcftools_invocations",
                "hash_roster_sha256",
                "normalized_outputs_sha256",
            )
        )
        writer.writerow(
            (
                mode,
                partition_count,
                len(SAMPLES),
                len(hash_rows),
                logical_bytes,
                len(calls),
                hashlib.sha256("".join(roster_lines).encode()).hexdigest(),
                hashlib.sha256("".join(normalized).encode()).hexdigest(),
            )
        )


def summarize(results: Path) -> None:
    summaries = {
        (row["case"], int(row["value"])): row
        for row in read_tsv(results / "summary.tsv")
    }
    trials = read_tsv(results / "trials.tsv")
    if len(trials) != 18 or any(row["status"] != "pass" for row in trials):
        raise ProbeError("all 18 benchmark trials must pass")
    output = results / "comparison.tsv"
    with output.open("x", encoding="utf-8", newline="") as handle:
        fields = (
            "partitions",
            "samples",
            "repetitions",
            "hash_invocations",
            "logical_hash_bytes",
            "bcftools_invocations",
            "actual_median_wall_seconds",
            "no_read_median_wall_seconds",
            "isolated_hash_wall_seconds",
            "actual_median_cpu_seconds",
            "no_read_median_cpu_seconds",
            "isolated_hash_cpu_seconds",
            "effective_hash_mib_per_second",
            "hash_roster_sha256",
            "normalized_outputs_sha256",
        )
        writer = csv.DictWriter(handle, fieldnames=fields, dialect="excel-tab")
        writer.writeheader()
        for partition_count in (1, 8, 25):
            metrics: dict[str, list[dict[str, str]]] = {}
            modes = (
                ("actual", "step07_hash_actual"),
                ("no-read", "step07_hash_no_read"),
            )
            for mode, case in modes:
                metrics[mode] = [
                    read_tsv(path)[0]
                    for path in sorted(
                        (results / "trials" / case / str(partition_count)).glob(
                            "rep-*/metrics.tsv"
                        )
                    )
                ]
                if len(metrics[mode]) != 3:
                    raise ProbeError(f"missing metrics for {mode} {partition_count}")
            comparable = (
                "partitions",
                "samples",
                "hash_invocations",
                "logical_hash_bytes",
                "bcftools_invocations",
                "hash_roster_sha256",
                "normalized_outputs_sha256",
            )
            reference = metrics["actual"][0]
            if any(
                any(row[field] != reference[field] for field in comparable)
                for rows in metrics.values()
                for row in rows
            ):
                raise ProbeError(f"actual/control metrics differ for {partition_count}")
            actual = summaries["step07_hash_actual", partition_count]
            control = summaries["step07_hash_no_read", partition_count]
            actual_wall = float(actual["median_wall_seconds"])
            control_wall = float(control["median_wall_seconds"])
            wall_delta = actual_wall - control_wall
            if wall_delta <= 0:
                raise ProbeError(f"non-positive isolated hash time for {partition_count}")
            actual_cpu = float(actual["median_cpu_seconds"])
            control_cpu = float(control["median_cpu_seconds"])
            cpu_delta = actual_cpu - control_cpu
            logical_bytes = int(reference["logical_hash_bytes"])
            writer.writerow(
                {
                    "partitions": partition_count,
                    "samples": reference["samples"],
                    "repetitions": 3,
                    "hash_invocations": reference["hash_invocations"],
                    "logical_hash_bytes": logical_bytes,
                    "bcftools_invocations": reference["bcftools_invocations"],
                    "actual_median_wall_seconds": f"{actual_wall:.6f}",
                    "no_read_median_wall_seconds": f"{control_wall:.6f}",
                    "isolated_hash_wall_seconds": f"{wall_delta:.6f}",
                    "actual_median_cpu_seconds": f"{actual_cpu:.6f}",
                    "no_read_median_cpu_seconds": f"{control_cpu:.6f}",
                    "isolated_hash_cpu_seconds": f"{cpu_delta:.6f}",
                    "effective_hash_mib_per_second": f"{logical_bytes / 1048576 / wall_delta:.3f}",
                    "hash_roster_sha256": reference["hash_roster_sha256"],
                    "normalized_outputs_sha256": reference[
                        "normalized_outputs_sha256"
                    ],
                }
            )


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed not in (1, 8, 25):
        raise argparse.ArgumentTypeError("must be 1, 8, or 25")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    seed_parser = commands.add_parser("seed")
    seed_parser.add_argument("--root", type=Path, required=True)
    for name in ("produce", "validate"):
        command = commands.add_parser(name)
        command.add_argument("--mode", choices=("actual", "no-read"), required=True)
        command.add_argument("--partitions", type=positive_int, required=True)
        command.add_argument("--trial-dir", type=Path, required=True)
    summary_parser = commands.add_parser("summarize")
    summary_parser.add_argument("--results", type=Path, required=True)
    return parser


def main(arguments: list[str] | None = None) -> int:
    selected = sys.argv[1:] if arguments is None else arguments
    try:
        if selected and selected[0] == "bcftools":
            return fake_bcftools(selected[1:])
        parsed = build_parser().parse_args(selected)
        if parsed.command == "seed":
            seed(parsed.root)
        elif parsed.command == "produce":
            run_producer(parsed.mode, parsed.partitions, parsed.trial_dir)
        elif parsed.command == "validate":
            validate_outputs(parsed.mode, parsed.partitions, parsed.trial_dir)
        else:
            summarize(parsed.results)
    except (
        csv.Error,
        IndexError,
        KeyError,
        OSError,
        ProbeError,
        StopIteration,
        ValueError,
    ) as exc:
        print(f"step07-hash-probe: error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
