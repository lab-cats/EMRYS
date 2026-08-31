"""Produce one create-absent Step 06 mechanical-orientation transaction."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import signal
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
from emrys.libraries.validation import sha256_file

SIGNALS = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class ProducerError(RuntimeError):
    """Step 06 admission, execution, or publication failed."""


class Interrupted(ProducerError):
    def __init__(self, signum: int) -> None:
        super().__init__(f"Step 06 interrupted by signal {signum}.")
        self.signum = signum


class ChildError(ProducerError):
    def __init__(self, message: str, status: int) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True, slots=True)
class Context:
    """Immutable inputs and paths for one owner invocation."""

    sample_id: str
    input_bam: Path
    input_bai: Path
    threads: int
    samtools: str
    token: str
    input_hashes: tuple[str, str]
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


def _paths(arguments: argparse.Namespace, token: str) -> dict[str, Path]:
    sample = arguments.sample_id
    output = arguments.output_dir
    qc = arguments.qc_dir
    prefix = output / f".{sample}.step06.{token}"
    return {
        "fwd": output / f"{sample}.{ORIENTATIONS[0]}.bam",
        "fwd_bai": output / f"{sample}.{ORIENTATIONS[0]}.bam.bai",
        "rev": output / f"{sample}.{ORIENTATIONS[1]}.bam",
        "rev_bai": output / f"{sample}.{ORIENTATIONS[1]}.bam.bai",
        "counts": qc / f"{sample}.orientation_counts.tsv",
        "tmp_99": Path(f"{prefix}.99.tmp.bam"),
        "tmp_147": Path(f"{prefix}.147.tmp.bam"),
        "tmp_83": Path(f"{prefix}.83.tmp.bam"),
        "tmp_163": Path(f"{prefix}.163.tmp.bam"),
        "tmp_fwd": Path(f"{prefix}.{ORIENTATIONS[0]}.tmp.bam"),
        "tmp_fwd_bai": Path(f"{prefix}.{ORIENTATIONS[0]}.tmp.bam.bai"),
        "tmp_rev": Path(f"{prefix}.{ORIENTATIONS[1]}.tmp.bam"),
        "tmp_rev_bai": Path(f"{prefix}.{ORIENTATIONS[1]}.tmp.bam.bai"),
        "tmp_counts": qc / f".{sample}.step06.{token}.orientation_counts.tmp.tsv",
        "lock": output / f".{sample}.step06.lock",
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
    token = os.environ.get("EMRYS_RUN_TOKEN", "")
    if SAFE_ID.fullmatch(token) is None:
        fail("Step 06 requires its admitted owner run token.")
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
        input_bai=input_bai,
        threads=int(arguments.threads),
        samtools=str(samtools),
        token=token,
        input_hashes=(sha256_file(input_bam), sha256_file(input_bai)),
        paths=_paths(arguments, token),
    )


class Publication:
    """Owner-local create-absent publication state."""

    finals = ("fwd", "fwd_bai", "rev", "rev_bai", "counts")
    scratch = (
        "tmp_99",
        "tmp_147",
        "tmp_83",
        "tmp_163",
        "tmp_fwd",
        "tmp_fwd_bai",
        "tmp_rev",
        "tmp_rev_bai",
        "tmp_counts",
    )

    def __init__(self, context: Context) -> None:
        self.context = context
        self.p = context.paths
        self.locked = self.committed = False
        self.published: list[str] = []
        self.child: subprocess.Popen[str] | None = None
        self.spawning = False
        self.pending_signal: int | None = None

    @property
    def owner(self) -> Path:
        return self.p["lock"] / "owner"

    def acquire(self) -> None:
        try:
            self.p["lock"].mkdir()
        except FileExistsError as exc:
            raise ProducerError(
                f"Step 06 lock already exists: {self.p['lock']}"
            ) from exc
        self.locked = True
        self.owner.write_text(f"run_token={self.context.token}\n", encoding="utf-8")

    def release(self) -> None:
        if not self.locked:
            return
        try:
            owned = self.owner.read_text(encoding="utf-8") == (
                f"run_token={self.context.token}\n"
            )
            unexpected = tuple(
                path for path in self.p["lock"].iterdir() if path != self.owner
            )
        except OSError as exc:
            raise ProducerError(
                f"Cannot prove Step 06 lock ownership: {self.p['lock']}"
            ) from exc
        if not owned or unexpected:
            fail(f"Step 06 lock ownership changed; preserving lock: {self.p['lock']}")
        self.owner.unlink()
        try:
            self.p["lock"].rmdir()
        except OSError as exc:
            if not os.path.lexists(self.owner) and self.p["lock"].is_dir():
                try:
                    with self.owner.open("x", encoding="utf-8") as stream:
                        stream.write(f"run_token={self.context.token}\n")
                except OSError:
                    pass
            raise ProducerError(
                f"Could not remove Step 06 lock: {self.p['lock']}"
            ) from exc
        self.locked = False

    @staticmethod
    def same(left: Path, right: Path) -> bool:
        try:
            return (
                left.is_file()
                and right.is_file()
                and not left.is_symlink()
                and not right.is_symlink()
                and left.samefile(right)
            )
        except OSError:
            return False

    def publish(self, name: str) -> None:
        staged, final = self.p[f"tmp_{name}"], self.p[name]
        if (
            not staged.is_file()
            or staged.is_symlink()
            or staged.stat().st_size == 0
            or os.path.lexists(final)
        ):
            fail(f"Step 06 {name} cannot be published create-exclusively: {final}")
        self.published.append(name)
        try:
            os.link(staged, final, follow_symlinks=False)
        except OSError as exc:
            if not self.same(staged, final):
                self.published.pop()
            raise ProducerError(
                f"Step 06 {name} final appeared during publication: {final}"
            ) from exc
        if not self.same(staged, final):
            fail(f"Step 06 {name} publication lost staged-inode identity: {final}")

    def command(self, arguments: Sequence[str], *, capture: bool = False) -> str:
        print(f"Step 06 command: {shlex.join(arguments)}", flush=True)
        self.spawning = True
        try:
            process = subprocess.Popen(
                arguments,
                stdout=subprocess.PIPE if capture else None,
                text=capture,
                process_group=0,
            )
        except OSError as exc:
            self.spawning = False
            if self.pending_signal is not None:
                self.interrupted(self.pending_signal, None)
            raise ProducerError(f"Could not execute samtools: {exc}") from exc
        self.child = process
        self.spawning = False
        if self.pending_signal is not None:
            self.interrupted(self.pending_signal, None)
        try:
            output, _ = process.communicate()
        finally:
            self.child = None
        if process.returncode:
            status = (
                process.returncode
                if process.returncode > 0
                else 128 - process.returncode
            )
            raise ChildError(
                f"samtools command failed with status {process.returncode}: {' '.join(arguments[1:])}",
                status,
            )
        return output or ""

    def rollback(self) -> bool:
        success = True
        for name in self.published:
            staged, final = self.p[f"tmp_{name}"], self.p[name]
            if not self.same(staged, final):
                success = False
                continue
            try:
                final.unlink()
                success &= not os.path.lexists(final)
            except OSError:
                success = False
        return success

    def discard_scratch(self) -> bool:
        success = True
        for name in self.scratch:
            try:
                self.p[name].unlink(missing_ok=True)
            except OSError:
                success = False
        return success

    def cleanup(self, failed: bool) -> None:
        rollback_ok = not (
            failed and self.published and not self.committed and not self.rollback()
        )
        scratch_ok = rollback_ok and self.discard_scratch()
        if not rollback_ok or not scratch_ok:
            print(
                f"ERROR: Step 06 cleanup is ambiguous; retaining owned lock and residue: {self.p['lock']}",
                file=sys.stderr,
            )
            return
        if self.locked:
            try:
                self.release()
            except ProducerError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)

    def interrupted(self, signum: int, _frame: object) -> None:
        if self.spawning:
            if self.pending_signal is None:
                self.pending_signal = signum
            return
        for number in SIGNALS:
            signal.signal(number, signal.SIG_IGN)
        child = self.child
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signum)
            except ProcessLookupError:
                pass
            child.wait()
            self.child = None
        raise Interrupted(signum)


def _require_no_residue(context: Context) -> None:
    pattern = f".{context.sample_id}.step06.*"
    for directory in (context.paths["fwd"].parent, context.paths["counts"].parent):
        match = next(directory.glob(pattern), None) if directory.is_dir() else None
        if match is not None:
            fail(f"Step 06 residue requires operator inspection: {match}")


def _count(tx: Publication, *arguments: str) -> int:
    raw = tx.command((tx.context.samtools, "view", "-c", *arguments), capture=True)
    value = raw.removesuffix("\n")
    if re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        fail(f"samtools count is not a non-negative integer: {value!r}")
    return int(value)


def _validate_outputs(tx: Publication, prefix: str) -> None:
    p = tx.p
    for name, label in (("fwd", ORIENTATIONS[0]), ("rev", ORIENTATIONS[1])):
        bam, bai = p[f"{prefix}{name}"], p[f"{prefix}{name}_bai"]
        _nonempty(f"{label} BAM", bam)
        tx.command((tx.context.samtools, "quickcheck", str(bam)))
        _nonempty(f"{label} BAI", bai)
    _nonempty("Orientation counts TSV", p[f"{prefix}counts"])


def _write_counts(tx: Publication) -> None:
    context, p = tx.context, tx.p
    input_records = _count(tx, str(context.input_bam))
    flag_counts = {
        flag: _count(tx, "-f", flag, str(context.input_bam))
        for orientation in ORIENTATIONS
        for flag in MECHANICAL_ORIENTATION_FLAG_GROUPS[orientation]
    }
    fwd_records = _count(tx, str(p["tmp_fwd"]))
    rev_records = _count(tx, str(p["tmp_rev"]))
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
    p["tmp_counts"].write_bytes(
        ("\t".join(COUNTS_HEADER) + "\n" + "\t".join(row) + "\n").encode()
    )


def execute(context: Context) -> None:
    p = context.paths
    _require_no_residue(context)
    p["fwd"].parent.mkdir(parents=True, exist_ok=True)
    p["counts"].parent.mkdir(parents=True, exist_ok=True)
    tx = Publication(context)
    handlers = {number: signal.getsignal(number) for number in SIGNALS}
    failed = True
    try:
        for number in handlers:
            signal.signal(number, tx.interrupted)
        tx.acquire()
        if any(os.path.lexists(p[name]) for name in (*tx.scratch, *tx.finals)):
            fail("Step 06 requires absent scratch and final outputs.")
        tx.command((context.samtools, "--version"))
        for orientation in ORIENTATIONS:
            for flag in MECHANICAL_ORIENTATION_FLAG_GROUPS[orientation]:
                tx.command(
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
            tx.command(
                (
                    context.samtools,
                    "merge",
                    "-@",
                    str(context.threads),
                    "-o",
                    str(p[f"tmp_{name}"]),
                    *(str(p[f"tmp_{flag}"]) for flag in flags),
                )
            )
        for name in ("fwd", "rev"):
            tx.command((context.samtools, "index", str(p[f"tmp_{name}"])))
        _write_counts(tx)
        _validate_outputs(tx, "tmp_")
        if (
            sha256_file(context.input_bam),
            sha256_file(context.input_bai),
        ) != context.input_hashes:
            fail("Input BAM or BAI changed during Step 06.")
        for name in tx.finals:
            tx.publish(name)
        _validate_outputs(tx, "")
        if any(not tx.same(p[f"tmp_{name}"], p[name]) for name in tx.finals):
            fail("A Step 06 final no longer matches its staging anchor.")
        if not tx.discard_scratch():
            fail("Step 06 could not remove owned scratch after publication.")
        tx.committed = True
        tx.release()
        failed = False
    finally:
        for number, handler in handlers.items():
            signal.signal(number, handler)
        tx.cleanup(failed)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--input-bam", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--qc-dir", required=True, type=Path)
    parser.add_argument("--threads", required=True)
    parser.add_argument("--samtools-bin", required=True)
    parser.add_argument("--no-clobber", action="store_true", required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    try:
        execute(build_context(parser.parse_args(argv)))
        print("Step 06 execute complete.")
        return 0
    except Interrupted as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 128 + exc.signum
    except ChildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.status
    except (ProducerError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
