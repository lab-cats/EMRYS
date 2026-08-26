#!/usr/bin/env python3
"""Build, time, and independently validate the Step06 count alternatives."""

from __future__ import annotations

import os
import random
import subprocess
import sys
from pathlib import Path
from typing import TextIO


FLAGS = (99, 147, 83, 163)
RECORD_COUNT = 2_000_000
READ_LENGTH = 75
CASES = frozenset({"balanced", "assigned20"})


class BenchmarkFixtureError(RuntimeError):
    """The disposable benchmark fixture or one of its checks is invalid."""


def _samtools() -> Path:
    raw = os.environ.get("EMRYS_STEP06_SAMTOOLS", "")
    if not raw:
        raise BenchmarkFixtureError("EMRYS_STEP06_SAMTOOLS is required")
    path = Path(raw).resolve(strict=True)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise BenchmarkFixtureError(f"samtools is not executable: {path}")
    return path


def _trial_dir(raw: str) -> Path:
    path = Path(raw)
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_dir():
        raise BenchmarkFixtureError(f"trial must be a real directory: {path}")
    return resolved


def _record_count(raw: str) -> int:
    try:
        count = int(raw)
    except ValueError as exc:
        raise BenchmarkFixtureError(f"invalid record count: {raw}") from exc
    if count != RECORD_COUNT:
        raise BenchmarkFixtureError(f"record count must be exactly {RECORD_COUNT}")
    return count


def _case(raw: str) -> str:
    if raw not in CASES:
        raise BenchmarkFixtureError(f"case must be one of {sorted(CASES)}")
    return raw


def _expected_counts(case: str, record_count: int) -> dict[int, int]:
    divisor = 4 if case == "balanced" else 20
    if record_count % divisor:
        raise BenchmarkFixtureError(
            f"record count must be divisible by {divisor} for {case}"
        )
    return {flag: record_count // divisor for flag in FLAGS}


def _flag_for_record(case: str, ordinal: int) -> int:
    if case == "balanced":
        return FLAGS[ordinal % len(FLAGS)]
    position = ordinal % 20
    return FLAGS[position] if position < len(FLAGS) else 0


def _write_sam_records(
    handle: TextIO, *, case: str, record_count: int
) -> None:
    rng = random.Random(20260826)
    alphabet = "ACGT"
    sequences = tuple(
        "".join(rng.choice(alphabet) for _ in range(READ_LENGTH))
        for _ in range(64)
    )
    quality = "I" * READ_LENGTH
    handle.write("@HD\tVN:1.6\tSO:unsorted\n@SQ\tSN:chr1\tLN:50000000\n")
    batch: list[str] = []
    for ordinal in range(record_count):
        flag = _flag_for_record(case, ordinal)
        position = ordinal % 2_000_000 + 1
        if flag in FLAGS:
            mate_reference = "="
            mate_position = position + 100
            template_length = 175 if flag in (99, 83) else -175
        else:
            mate_reference = "*"
            mate_position = 0
            template_length = 0
        batch.append(
            f"read_{ordinal:08d}\t{flag}\tchr1\t{position}\t60\t"
            f"{READ_LENGTH}M\t{mate_reference}\t{mate_position}\t"
            f"{template_length}\t{sequences[ordinal % len(sequences)]}\t"
            f"{quality}\n"
        )
        if len(batch) == 8192:
            handle.writelines(batch)
            batch.clear()
    handle.writelines(batch)


def _run_checked(argv: list[str]) -> None:
    completed = subprocess.run(argv, stdin=subprocess.DEVNULL, check=False)
    if completed.returncode:
        raise BenchmarkFixtureError(
            f"command exited {completed.returncode}: {' '.join(argv)}"
        )


def _build_input_bam(
    samtools: Path, *, case: str, record_count: int, destination: Path
) -> None:
    process = subprocess.Popen(
        [str(samtools), "view", "-@", "1", "-b", "-o", str(destination), "-"],
        stdin=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    assert process.stdin is not None
    write_error: BaseException | None = None
    try:
        _write_sam_records(process.stdin, case=case, record_count=record_count)
    except BaseException as exc:
        write_error = exc
    finally:
        try:
            process.stdin.close()
        except BrokenPipeError:
            pass
    return_code = process.wait()
    if write_error is not None:
        raise write_error
    if return_code:
        raise BenchmarkFixtureError(f"samtools view exited {return_code}")


def setup(case: str, record_count: int, trial: Path) -> None:
    samtools = _samtools()
    input_bam = trial / "input.bam"
    _build_input_bam(
        samtools, case=case, record_count=record_count, destination=input_bam
    )
    for flag in FLAGS:
        _run_checked(
            [
                str(samtools),
                "view",
                "-@",
                "1",
                "-b",
                "-f",
                str(flag),
                "-o",
                str(trial / f"flag_{flag}.bam"),
                str(input_bam),
            ]
        )


def _count(argv: list[str]) -> int:
    completed = subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode:
        raise BenchmarkFixtureError(
            f"command exited {completed.returncode}: {' '.join(argv)}: "
            f"{completed.stderr.strip()}"
        )
    output = completed.stdout.strip()
    if not output.isascii() or not output.isdecimal():
        raise BenchmarkFixtureError(f"invalid samtools count output: {output!r}")
    return int(output)


def _write_counts(path: Path, counts: dict[int, int]) -> None:
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write("flag\tcount\n")
        for flag in FLAGS:
            handle.write(f"{flag}\t{counts[flag]}\n")


def run(variant: int, case: str, record_count: int, trial: Path) -> None:
    samtools = _samtools()
    input_bam = trial / "input.bam"
    counts: dict[int, int] = {}
    for flag in FLAGS:
        if variant == 1:
            argv = [
                str(samtools),
                "view",
                "-c",
                "-f",
                str(flag),
                str(input_bam),
            ]
        elif variant == 2:
            argv = [str(samtools), "view", "-c", str(trial / f"flag_{flag}.bam")]
        else:
            raise BenchmarkFixtureError("variant must be 1 or 2")
        counts[flag] = _count(argv)
    _write_counts(trial / "counts.tsv", counts)

    filtered_bytes = sum((trial / f"flag_{flag}.bam").stat().st_size for flag in FLAGS)
    input_bytes = input_bam.stat().st_size
    assigned_records = sum(_expected_counts(case, record_count).values())
    logical_scan_bytes = input_bytes * len(FLAGS) if variant == 1 else filtered_bytes
    logical_scan_records = record_count * len(FLAGS) if variant == 1 else assigned_records
    with (trial / "scan_observation.tsv").open(
        "x", encoding="utf-8", newline=""
    ) as handle:
        handle.write(
            "variant\tinput_bam_bytes\tfiltered_bam_bytes\t"
            "logical_scan_bytes\tlogical_scan_records\n"
        )
        handle.write(
            f"{variant}\t{input_bytes}\t{filtered_bytes}\t"
            f"{logical_scan_bytes}\t{logical_scan_records}\n"
        )


def _read_counts(path: Path) -> dict[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "flag\tcount" or len(lines) != len(FLAGS) + 1:
        raise BenchmarkFixtureError(f"invalid counts table structure: {path}")
    counts: dict[int, int] = {}
    for expected_flag, line in zip(FLAGS, lines[1:], strict=True):
        parts = line.split("\t")
        if len(parts) != 2 or parts[0] != str(expected_flag) or not parts[1].isdecimal():
            raise BenchmarkFixtureError(f"invalid counts row: {line!r}")
        counts[expected_flag] = int(parts[1])
    return counts


def validate(
    variant: int, case: str, record_count: int, trial: Path
) -> None:
    samtools = _samtools()
    input_bam = trial / "input.bam"
    filtered_bams = tuple(trial / f"flag_{flag}.bam" for flag in FLAGS)
    _run_checked(
        [str(samtools), "quickcheck", str(input_bam), *(str(path) for path in filtered_bams)]
    )

    recorded = _read_counts(trial / "counts.tsv")
    expected = _expected_counts(case, record_count)
    for flag, filtered_bam in zip(FLAGS, filtered_bams, strict=True):
        full_input_count = _count(
            [
                str(samtools),
                "view",
                "-c",
                "-f",
                str(flag),
                str(input_bam),
            ]
        )
        filtered_count = _count([str(samtools), "view", "-c", str(filtered_bam)])
        if not recorded[flag] == full_input_count == filtered_count == expected[flag]:
            raise BenchmarkFixtureError(
                f"count mismatch for flag {flag}: recorded={recorded[flag]}, "
                f"input={full_input_count}, filtered={filtered_count}, "
                f"expected={expected[flag]}"
            )

    observation = (trial / "scan_observation.tsv").read_text(
        encoding="utf-8"
    ).splitlines()
    if len(observation) != 2 or not observation[1].startswith(f"{variant}\t"):
        raise BenchmarkFixtureError("invalid scan observation")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        raise BenchmarkFixtureError("a setup, run, or validate mode is required")
    mode = argv[1]
    if mode == "setup":
        if len(argv) != 5:
            raise BenchmarkFixtureError("setup requires CASE COUNT TRIAL")
        case = _case(argv[2])
        record_count = _record_count(argv[3])
        setup(case, record_count, _trial_dir(argv[4]))
        return 0

    if len(argv) != 6:
        raise BenchmarkFixtureError(
            "run and validate require MODE VARIANT CASE COUNT TRIAL"
        )
    try:
        variant = int(argv[2])
    except ValueError as exc:
        raise BenchmarkFixtureError(f"invalid variant: {argv[2]}") from exc
    case = _case(argv[3])
    record_count = _record_count(argv[4])
    trial = _trial_dir(argv[5])
    if mode == "run":
        run(variant, case, record_count, trial)
    elif mode == "validate":
        validate(variant, case, record_count, trial)
    else:
        raise BenchmarkFixtureError(f"unknown mode: {mode}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except (BenchmarkFixtureError, OSError) as exc:
        print(f"benchmark-step06-counts: error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
