#!/usr/bin/env python3
"""Disposable baseline/candidate benchmark adapter for FASTQ admission."""

from __future__ import annotations

import gzip
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path


def generate(root: Path, read_count: int, read_length: int) -> None:
    root.mkdir(mode=0o700)
    translation = bytes(b"ACGT"[value % 4] for value in range(256))
    quality = "I" * read_length
    for mate in (1, 2):
        plain = root / f"reads_R{mate}.fastq"
        generator = random.Random(1000 + mate)
        with plain.open("x", encoding="ascii", newline="") as handle:
            for ordinal in range(1, read_count + 1):
                sequence = generator.randbytes(read_length).translate(
                    translation
                ).decode("ascii")
                handle.write(
                    f"@read_{ordinal:07d}/{mate} instrument lane\n"
                    f"{sequence}\n+\n{quality}\n"
                )
        with plain.open("rb") as source, gzip.open(
            root / f"reads_R{mate}.fastq.gz", "xb", compresslevel=6
        ) as destination:
            shutil.copyfileobj(source, destination, length=1024 * 1024)


def prepare(trial: Path, kind: str) -> None:
    fake_bin = trial / "fake-bin"
    fake_bin.mkdir(mode=0o700)
    tool = "gunzip" if kind == "gzip" else "cat"
    wrapper = fake_bin / tool
    wrapper.write_text(
        "#!/bin/sh\n"
        "printf 'stream\\n' >> \"$EMRYS_STREAM_COUNTER\"\n"
        "exec \"$EMRYS_REAL_STREAM\" \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o700)


def paths(kind: str) -> tuple[Path, Path]:
    root = Path(os.environ["EMRYS_FASTQ_FIXTURE_ROOT"])
    suffix = ".fastq.gz" if kind == "gzip" else ".fastq"
    return root / f"reads_R1{suffix}", root / f"reads_R2{suffix}"


def run(variant: int, kind: str, num_reads: int, trial: Path) -> int:
    source_root = Path(
        os.environ[
            "EMRYS_BASELINE_ROOT" if variant == 1 else "EMRYS_CANDIDATE_ROOT"
        ]
    )
    checker = source_root / (
        "src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh"
    )
    tool = "gunzip" if kind == "gzip" else "cat"
    real_tool = shutil.which(tool)
    if real_tool is None:
        raise RuntimeError(f"required benchmark tool is absent: {tool}")
    counter = trial / "stream-count.txt"
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join(
        (str(trial / "fake-bin"), environment["PATH"])
    )
    environment["EMRYS_STREAM_COUNTER"] = str(counter)
    environment["EMRYS_REAL_STREAM"] = real_tool
    r1, r2 = paths(kind)
    completed = subprocess.run(
        [
            str(checker), "--r1-fastq", str(r1), "--r2-fastq", str(r2),
            "--num-reads", str(num_reads),
        ],
        env=environment,
        capture_output=True,
        check=False,
    )
    (trial / "result.bin").write_bytes(
        b"exit\t" + str(completed.returncode).encode("ascii") + b"\nstdout\n"
        + completed.stdout + b"stderr\n" + completed.stderr
    )
    sys.stdout.buffer.write(completed.stdout)
    sys.stderr.buffer.write(completed.stderr)
    return completed.returncode


def validate(variant: int, num_reads: int, trial: Path) -> None:
    expected_streams = 2 * (num_reads + 1) if variant == 1 else 2
    observed_streams = len(
        (trial / "stream-count.txt").read_text(encoding="utf-8").splitlines()
    )
    if observed_streams != expected_streams:
        raise RuntimeError(
            f"expected {expected_streams} streams, observed {observed_streams}"
        )
    result = (trial / "result.bin").read_bytes()
    if not result.startswith(b"exit\t0\n") or b"PASS: FASTQ pair check" not in result:
        raise RuntimeError("FASTQ checker did not produce the expected success result")


def main() -> int:
    arguments = sys.argv[1:]
    mode = arguments[0]
    if mode == "generate":
        generate(Path(arguments[1]), int(arguments[2]), int(arguments[3]))
    elif mode == "prepare":
        prepare(Path(arguments[4]), arguments[2])
    elif mode == "run":
        return run(int(arguments[1]), arguments[2], int(arguments[3]), Path(arguments[4]))
    elif mode == "validate":
        validate(int(arguments[1]), int(arguments[3]), Path(arguments[4]))
    else:
        raise RuntimeError(f"unknown mode: {mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
