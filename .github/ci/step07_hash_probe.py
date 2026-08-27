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
MODES = (
    "direct-actual",
    "direct-no-read",
    "reuse-actual",
    "reuse-no-read",
)
STEP07_SHA256 = "d9c2b6ea2bfac3f4f0a42a611f5444e17d6e9a0e591964c46649e9b5c702f067"
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
if [[ "$EMRYS_PROBE_HASH_MODE" == *-actual || "$target" == /dev/stdin ]]; then
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


def scientific_input_paths(root: Path) -> tuple[Path, ...]:
    paths = [
        root / "samples.tsv",
        root / "partitions.tsv",
        root / "reference.fa",
        root / "reference.fa.fai",
    ]
    for sample in SAMPLES:
        sample_root = root / "orientation" / sample
        for orientation in ORIENTATIONS:
            bam = sample_root / f"{sample}.{orientation}.bam"
            paths.extend((bam, Path(f"{bam}.bai")))
    return tuple(paths)


def bound_identity(root: Path, *, read_inputs: bool) -> str:
    aggregate = hashlib.sha256(b"emrys.step07-input-identity.v1\0")
    for path in scientific_input_paths(root):
        digest = sha256_file(path) if read_inputs else "0" * 64
        aggregate.update(os.fsencode(f"{path}\0{digest}\0"))
    return aggregate.hexdigest()


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
        "sample_id\tcondition\n" + "".join(f"{sample}\tprobe\n" for sample in SAMPLES),
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
    (root / "bound-actual.sha256").write_text(
        bound_identity(root, read_inputs=True) + "\n", encoding="ascii"
    )
    (root / "bound-no-read.sha256").write_text(
        bound_identity(root, read_inputs=False) + "\n", encoding="ascii"
    )
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
            (
                value
                for value in ORIENTATIONS
                if any(f".{value}.bam" in arg for arg in rest)
            ),
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
    base_environment.pop("EMRYS_STEP07_INPUT_IDENTITY_SHA256", None)
    if mode.startswith("reuse-"):
        identity_kind = "actual" if mode.endswith("-actual") else "no-read"
        base_environment["EMRYS_STEP07_INPUT_IDENTITY_SHA256"] = (
            (root / f"bound-{identity_kind}.sha256").read_text(encoding="ascii").strip()
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


def expected_hashes(root: Path, mode: str) -> dict[str, int]:
    reuse = mode.startswith("reuse-")
    expected = {
        str(root / "samples.tsv"): 6 if reuse else 8,
        str(root / "partitions.tsv"): 6 if reuse else 8,
        str(root / "reference.fa"): 1 if reuse else 3,
        str(root / "reference.fa.fai"): 1 if reuse else 3,
    }
    for sample in SAMPLES:
        for orientation in ORIENTATIONS:
            bam = root / "orientation" / sample / f"{sample}.{orientation}.bam"
            expected[str(bam)] = 1 if reuse else 3
            expected[str(Path(f"{bam}.bai"))] = 1 if reuse else 3
    if reuse:
        expected["/dev/stdin"] = 1
    return expected


def validate_outputs(mode: str, partition_count: int, trial: Path) -> None:
    root = require_root()
    partitions = PARTITIONS[:partition_count]
    hash_rows = read_tsv(trial / "hash.tsv")
    expected = expected_hashes(root, mode)
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
            size = 0 if path == "/dev/stdin" else Path(path).stat().st_size
            matching = [
                row
                for row in hash_rows
                if row["partition_id"] == partition and row["path"] == path
            ]
            if any(
                row["mode"] != mode or int(row["bytes"]) != size for row in matching
            ):
                raise ProbeError(f"hash log metadata mismatch for {partition}: {path}")
            logical_bytes += size * count
            relative = (
                "aggregate-stdin"
                if path == "/dev/stdin"
                else Path(path).relative_to(root)
            )
            roster_lines.append(f"{partition}\t{relative}\t{count}\t{size}\n")
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
    sample_hash = (
        sha256_file(root / "samples.tsv") if mode.endswith("-actual") else "0" * 64
    )
    partition_hash = (
        sha256_file(root / "partitions.tsv") if mode.endswith("-actual") else "0" * 64
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
                raise ProbeError(
                    f"receipt content mismatch for {partition} {orientation}"
                )
            lines = vcf.read_text(encoding="utf-8").splitlines()
            header = next(line for line in lines if line.startswith("#CHROM"))
            if tuple(header.split("\t")[9:]) != SAMPLES:
                raise ProbeError(
                    f"VCF sample order mismatch for {partition} {orientation}"
                )
            if sum(not line.startswith("#") for line in lines) != 1:
                raise ProbeError(
                    f"VCF record count mismatch for {partition} {orientation}"
                )
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
    if len(trials) != 36 or any(row["status"] != "pass" for row in trials):
        raise ProbeError("all 36 benchmark trials must pass")
    output = results / "comparison.tsv"
    with output.open("x", encoding="utf-8", newline="") as handle:
        fields = (
            "partitions",
            "samples",
            "repetitions",
            "direct_hash_invocations",
            "reuse_hash_invocations",
            "direct_logical_hash_bytes",
            "reuse_logical_hash_bytes",
            "logical_hash_bytes_saved",
            "logical_hash_percent_saved",
            "bcftools_invocations",
            "direct_actual_median_wall_seconds",
            "reuse_actual_median_wall_seconds",
            "observed_wall_seconds_saved",
            "observed_wall_percent_saved",
            "direct_no_read_median_wall_seconds",
            "reuse_no_read_median_wall_seconds",
            "direct_isolated_hash_wall_seconds",
            "reuse_isolated_hash_wall_seconds",
            "isolated_hash_wall_seconds_saved",
            "isolated_hash_wall_percent_saved",
            "direct_actual_median_cpu_seconds",
            "reuse_actual_median_cpu_seconds",
            "observed_cpu_seconds_saved",
            "direct_hash_roster_sha256",
            "reuse_hash_roster_sha256",
            "normalized_outputs_sha256",
        )
        writer = csv.DictWriter(handle, fieldnames=fields, dialect="excel-tab")
        writer.writeheader()
        for partition_count in (1, 8, 25):
            metrics: dict[str, list[dict[str, str]]] = {}
            modes = (
                ("direct-actual", "step07_direct_actual"),
                ("direct-no-read", "step07_direct_no_read"),
                ("reuse-actual", "step07_reuse_actual"),
                ("reuse-no-read", "step07_reuse_no_read"),
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
            for variant in ("direct", "reuse"):
                reference = metrics[f"{variant}-actual"][0]
                if any(
                    any(row[field] != reference[field] for field in comparable)
                    for mode in (f"{variant}-actual", f"{variant}-no-read")
                    for row in metrics[mode]
                ):
                    raise ProbeError(
                        f"{variant} actual/control metrics differ for {partition_count}"
                    )
            direct_metrics = metrics["direct-actual"][0]
            reuse_metrics = metrics["reuse-actual"][0]
            if (
                direct_metrics["normalized_outputs_sha256"]
                != reuse_metrics["normalized_outputs_sha256"]
            ):
                raise ProbeError(f"direct/reuse outputs differ for {partition_count}")

            direct_actual = summaries["step07_direct_actual", partition_count]
            direct_control = summaries["step07_direct_no_read", partition_count]
            reuse_actual = summaries["step07_reuse_actual", partition_count]
            reuse_control = summaries["step07_reuse_no_read", partition_count]
            direct_actual_wall = float(direct_actual["median_wall_seconds"])
            direct_control_wall = float(direct_control["median_wall_seconds"])
            reuse_actual_wall = float(reuse_actual["median_wall_seconds"])
            reuse_control_wall = float(reuse_control["median_wall_seconds"])
            direct_hash_wall = direct_actual_wall - direct_control_wall
            reuse_hash_wall = reuse_actual_wall - reuse_control_wall
            observed_wall_saved = direct_actual_wall - reuse_actual_wall
            isolated_hash_wall_saved = direct_hash_wall - reuse_hash_wall
            if min(direct_hash_wall, reuse_hash_wall, observed_wall_saved) <= 0:
                raise ProbeError(
                    f"non-positive Step 07 timing improvement for {partition_count}"
                )
            if isolated_hash_wall_saved <= 0:
                raise ProbeError(
                    f"non-positive isolated hash improvement for {partition_count}"
                )

            direct_bytes = int(direct_metrics["logical_hash_bytes"])
            reuse_bytes = int(reuse_metrics["logical_hash_bytes"])
            bytes_saved = direct_bytes - reuse_bytes
            direct_actual_cpu = float(direct_actual["median_cpu_seconds"])
            reuse_actual_cpu = float(reuse_actual["median_cpu_seconds"])
            writer.writerow(
                {
                    "partitions": partition_count,
                    "samples": direct_metrics["samples"],
                    "repetitions": 3,
                    "direct_hash_invocations": direct_metrics["hash_invocations"],
                    "reuse_hash_invocations": reuse_metrics["hash_invocations"],
                    "direct_logical_hash_bytes": direct_bytes,
                    "reuse_logical_hash_bytes": reuse_bytes,
                    "logical_hash_bytes_saved": bytes_saved,
                    "logical_hash_percent_saved": f"{100 * bytes_saved / direct_bytes:.3f}",
                    "bcftools_invocations": direct_metrics["bcftools_invocations"],
                    "direct_actual_median_wall_seconds": f"{direct_actual_wall:.6f}",
                    "reuse_actual_median_wall_seconds": f"{reuse_actual_wall:.6f}",
                    "observed_wall_seconds_saved": f"{observed_wall_saved:.6f}",
                    "observed_wall_percent_saved": f"{100 * observed_wall_saved / direct_actual_wall:.3f}",
                    "direct_no_read_median_wall_seconds": f"{direct_control_wall:.6f}",
                    "reuse_no_read_median_wall_seconds": f"{reuse_control_wall:.6f}",
                    "direct_isolated_hash_wall_seconds": f"{direct_hash_wall:.6f}",
                    "reuse_isolated_hash_wall_seconds": f"{reuse_hash_wall:.6f}",
                    "isolated_hash_wall_seconds_saved": f"{isolated_hash_wall_saved:.6f}",
                    "isolated_hash_wall_percent_saved": f"{100 * isolated_hash_wall_saved / direct_hash_wall:.3f}",
                    "direct_actual_median_cpu_seconds": f"{direct_actual_cpu:.6f}",
                    "reuse_actual_median_cpu_seconds": f"{reuse_actual_cpu:.6f}",
                    "observed_cpu_seconds_saved": f"{direct_actual_cpu - reuse_actual_cpu:.6f}",
                    "direct_hash_roster_sha256": direct_metrics["hash_roster_sha256"],
                    "reuse_hash_roster_sha256": reuse_metrics["hash_roster_sha256"],
                    "normalized_outputs_sha256": direct_metrics[
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
        command.add_argument("--mode", choices=MODES, required=True)
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
