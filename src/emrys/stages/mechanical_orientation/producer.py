"""Compute mechanical-orientation BAMs and counts in runner-owned working paths."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.libraries.alignments.orientation import (
    COUNTS_HEADER,
    MECHANICAL_ORIENTATION_FLAG_GROUPS,
    ORIENTATIONS,
)

SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class ProducerError(RuntimeError):
    """Step 06 scientific preparation or computation failed."""


class ChildError(ProducerError):
    def __init__(self, message: str, status: int) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True, slots=True)
class Context:
    """Immutable inputs and paths for one owner invocation."""

    sample_id: str
    input_bam: Path
    threads: int
    samtools: str
    paths: dict[str, Path]


def fail(message: str) -> None:
    raise ProducerError(message)


def _nonempty(label: str, path: Path) -> None:
    try:
        valid = path.is_file() and path.stat().st_size > 0
    except OSError:
        valid = False
    if not valid:
        fail(f"{label} does not exist or is empty: {path}")


def _paths(arguments: argparse.Namespace) -> dict[str, Path]:
    sample = arguments.sample_id
    try:
        work = Path(os.environ["EMRYS_TASK_WORK_DIR"])
    except KeyError:
        fail("Step 06 requires the task runner's working directory.")
    output, qc = arguments.output_dir, arguments.qc_dir
    return {
        "fwd": output / f"{sample}.{ORIENTATIONS[0]}.bam",
        "fwd_bai": output / f"{sample}.{ORIENTATIONS[0]}.bam.bai",
        "rev": output / f"{sample}.{ORIENTATIONS[1]}.bam",
        "rev_bai": output / f"{sample}.{ORIENTATIONS[1]}.bam.bai",
        "counts": qc / f"{sample}.orientation_counts.tsv",
        **{
            f"tmp_{flag}": work / f"{sample}.{flag}.bam"
            for flag in ("99", "147", "83", "163")
        },
    }


def build_context(arguments: argparse.Namespace) -> Context:
    if SAFE_ID.fullmatch(arguments.sample_id) is None:
        fail(f"Invalid Step 06 sample ID: {arguments.sample_id}")
    if re.fullmatch(r"[1-9][0-9]*", arguments.threads) is None:
        fail(f"--threads must be a positive integer: {arguments.threads}")
    input_bam = arguments.input_bam
    input_bai = Path(f"{input_bam}.bai")
    _nonempty("Input BAM", input_bam)
    _nonempty("Input BAI", input_bai)
    samtools = Path(arguments.samtools_bin)
    if (
        not samtools.is_absolute()
        or not samtools.exists()
        or not os.access(samtools, os.X_OK)
    ):
        fail(f"samtools must be an absolute executable path: {samtools}")
    return Context(
        sample_id=arguments.sample_id,
        input_bam=input_bam,
        threads=int(arguments.threads),
        samtools=str(samtools),
        paths=_paths(arguments),
    )


def _command(arguments: Sequence[str], *, capture: bool = False) -> str:
    process = subprocess.run(
        arguments,
        stdout=subprocess.PIPE if capture else None,
        text=capture,
    )
    if process.returncode:
        status = (
            process.returncode if process.returncode > 0 else 128 - process.returncode
        )
        raise ChildError(
            f"samtools command failed with status {process.returncode}: {' '.join(arguments[1:])}",
            status,
        )
    return process.stdout or ""


def _count(context: Context, *arguments: str) -> int:
    raw = _command((context.samtools, "view", "-c", *arguments), capture=True)
    value = raw.removesuffix("\n")
    if re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        fail(f"samtools count is not a non-negative integer: {value!r}")
    return int(value)


def _validate_outputs(context: Context) -> None:
    p = context.paths
    for name, label in (("fwd", ORIENTATIONS[0]), ("rev", ORIENTATIONS[1])):
        bam, bai = p[name], p[f"{name}_bai"]
        _nonempty(f"{label} BAM", bam)
        _command((context.samtools, "quickcheck", str(bam)))
        _nonempty(f"{label} BAI", bai)
    _nonempty("Orientation counts TSV", p["counts"])


def _write_counts(context: Context) -> None:
    p = context.paths
    input_records = _count(context, str(context.input_bam))
    flag_counts = {
        flag: _count(context, "-f", flag, str(context.input_bam))
        for orientation in ORIENTATIONS
        for flag in MECHANICAL_ORIENTATION_FLAG_GROUPS[orientation]
    }
    fwd_records = _count(context, str(p["fwd"]))
    rev_records = _count(context, str(p["rev"]))
    if input_records == 0:
        fail("input_records is zero; refusing to publish empty Step 06 outputs")
    if fwd_records == 0 or rev_records == 0:
        fail("both mechanical-orientation groups must be nonempty")
    assigned = fwd_records + rev_records
    if assigned > input_records:
        fail(f"assigned_records exceeds input_records: {assigned} > {input_records}")
    row = (
        context.sample_id,
        str(input_records),
        *(str(flag_counts[flag]) for flag in ("99", "147", "83", "163")),
        str(fwd_records),
        str(rev_records),
        str(assigned),
        str(input_records - assigned),
        f"{assigned / input_records:.6f}",
    )
    p["counts"].write_bytes(
        ("\t".join(COUNTS_HEADER) + "\n" + "\t".join(row) + "\n").encode()
    )


def execute(context: Context) -> None:
    p = context.paths
    _command((context.samtools, "--version"))
    for orientation in ORIENTATIONS:
        for flag in MECHANICAL_ORIENTATION_FLAG_GROUPS[orientation]:
            _command(
                (
                    context.samtools,
                    "view",
                    "-@",
                    str(context.threads),
                    "-b",
                    "-f",
                    flag,
                    str(context.input_bam),
                    "-o",
                    str(p[f"tmp_{flag}"]),
                )
            )
    for name, flags in (("fwd", ("99", "147")), ("rev", ("83", "163"))):
        _command(
            (
                context.samtools,
                "merge",
                "-@",
                str(context.threads),
                "-o",
                str(p[name]),
                *(str(p[f"tmp_{flag}"]) for flag in flags),
            )
        )
    for name in ("fwd", "rev"):
        _command((context.samtools, "index", str(p[name])))
    _write_counts(context)
    _validate_outputs(context)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--input-bam", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--qc-dir", required=True, type=Path)
    parser.add_argument("--threads", required=True)
    parser.add_argument("--samtools-bin", required=True)
    try:
        execute(build_context(parser.parse_args(argv)))
        return 0
    except ChildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.status
    except (ProducerError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
