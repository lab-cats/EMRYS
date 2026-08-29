"""Coordinate Step 08 R preprocessing and its three-file transaction."""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.contracts.scientific_evidence import step08
from emrys.libraries import validation as report
from emrys.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY as POLICY,
    ORIENTATIONS,
)
from emrys.libraries.validation.mpileup import RECEIPT_HEADER, VCF_FIXED_COLUMNS
from emrys.libraries.validation.tsv import read_strict_tsv


class ProducerError(RuntimeError):
    """Step 08 admission, execution, or publication failed."""


class Interrupted(ProducerError):
    def __init__(self, signum: int) -> None:
        super().__init__(f"Step 08 interrupted by signal {signum}.")
        self.signum = signum


@dataclass(frozen=True)
class Step07Input:
    partition: dict[str, str]
    receipt: str
    receipt_hash: str
    vcfs: tuple[str, str]
    vcf_hashes: tuple[str, str]
    counts: tuple[int, int]


@dataclass(frozen=True)
class Context:
    arguments: argparse.Namespace
    samples: tuple[str, ...]
    partitions: tuple[dict[str, str], ...]
    hashes: tuple[str, str, str]
    step07: tuple[Step07Input, ...]
    token: str
    threads: int
    rscript: str
    paths: dict[str, Path]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    for name in (
        "cohort-id",
        "sample-manifest",
        "partition-manifest",
        "step07-root",
        "annotation-gtf",
        "output-root",
        "qc-root",
    ):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--threads", default="1")
    parser.add_argument("--rscript-bin")
    parser.add_argument(
        "--r-script",
        default=os.environ.get(
            "STEP08_R_SCRIPT",
            str(Path(__file__).with_name("step_08_vcf_preprocessing.R")),
        ),
    )
    parser.add_argument("--no-clobber", action="store_true")
    parser.add_argument("--execute", action="store_true")


def fail(message: str) -> None:
    raise ProducerError(message)


def lexists(path: Path) -> bool:
    return os.path.lexists(path)


def digest(path: Path) -> str:
    try:
        return report.sha256_file(path)
    except OSError as exc:
        raise ProducerError(f"Could not hash {path}: {exc}") from exc


def nonempty(label: str, path: Path) -> None:
    try:
        valid = path.is_file() and path.stat().st_size > 0
    except OSError:
        valid = False
    if not valid:
        fail(f"{label} does not exist or is empty: {path}")


def integer(label: str, value: str, *, positive: bool = False) -> int:
    pattern = r"[1-9][0-9]*" if positive else r"0|[1-9][0-9]*"
    if not re.fullmatch(pattern, value):
        qualifier = "positive" if positive else "non-negative"
        fail(f"{label} must be a {qualifier} integer; got: {value}")
    return int(value)


def executable(requested: str | None) -> str:
    value = requested or os.environ.get("RSCRIPT_BIN_OVERRIDE") or "Rscript"
    if "/" in value:
        if not Path(value).exists():
            fail(f"Rscript does not exist: {value}")
        if not os.access(value, os.X_OK):
            fail(f"Rscript exists but is not executable: {value}")
        return value
    resolved = shutil.which(value)
    if resolved is None:
        fail(f"Rscript executable was not found on PATH: {value}")
    return resolved


def inspect_vcf(
    label: str,
    path: Path,
    samples: Sequence[str],
    declared: int,
) -> None:
    definitions = {
        prefix: False
        for prefix in ("##INFO=<ID=AD,", "##FORMAT=<ID=DP,", "##FORMAT=<ID=AD,")
    }
    header_count = observed = 0
    invalid_header = blank_data = False
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            for raw_line in stream:
                line = raw_line.removesuffix("\n")
                for prefix in definitions:
                    definitions[prefix] |= line.startswith(prefix)
                if line.startswith("#CHROM"):
                    header_count += 1
                    fields = line.split("\t")
                    invalid_header |= tuple(fields[:9]) != VCF_FIXED_COLUMNS or fields[
                        9:
                    ] != list(samples)
                elif line.startswith("#"):
                    continue
                elif not line.strip():
                    blank_data = True
                else:
                    observed += 1
    except (OSError, UnicodeError) as exc:
        raise ProducerError(f"Could not read {label} VCF {path}: {exc}") from exc
    if header_count != 1 or invalid_header or not all(definitions.values()):
        fail(f"{label} VCF header or required definitions are invalid: {path}")
    if blank_data or observed != declared:
        fail(f"{label} VCF record count does not match its Step 07 receipt: {path}")


def admit_step07(
    arguments: argparse.Namespace,
    partition: dict[str, str],
    samples: Sequence[str],
    sample_hash: str,
    partition_hash: str,
) -> Step07Input:
    partition_id = partition["partition_id"]
    root = f"{arguments.step07_root}/{arguments.cohort_id}/{partition_id}"
    prefix = f"{arguments.cohort_id}.{partition_id}"
    receipt = f"{root}/{prefix}.step07_outputs.tsv"
    vcfs = tuple(
        f"{root}/{prefix}.{orientation}.mpileup.vcf" for orientation in ORIENTATIONS
    )
    nonempty(f"Step 07 receipt for partition {partition_id}", Path(receipt))
    for orientation, path in zip(ORIENTATIONS, vcfs, strict=True):
        nonempty(f"Step 07 {orientation} VCF for partition {partition_id}", Path(path))
    before = (digest(Path(receipt)), *(digest(Path(path)) for path in vcfs))
    _, rows = read_strict_tsv(
        f"Step 07 receipt for partition {partition_id}",
        Path(receipt),
        RECEIPT_HEADER,
        fail,
    )
    if len(rows) != 2:
        fail(
            f"Step 07 receipt must contain the exact header and two 10-field rows: {receipt}"
        )
    counts: list[int] = []
    for row, orientation, vcf in zip(rows, ORIENTATIONS, vcfs, strict=True):
        identity = (
            row["cohort_id"] == arguments.cohort_id
            and row["partition_id"] == partition_id
            and row["selector_type"] == partition["selector_type"]
            and row["selector_value"] == partition["selector_value"]
            and row["orientation"] == orientation
            and row["sample_manifest_sha256"] == sample_hash
            and row["partition_manifest_sha256"] == partition_hash
        )
        try:
            same_vcf = Path(row["vcf_path"]).samefile(Path(vcf))
        except OSError:
            same_vcf = False
        if (
            not identity
            or not same_vcf
            or integer("Step 07 sample count", row["sample_count"]) != len(samples)
        ):
            fail(f"Step 07 receipt provenance mismatch: {receipt}")
        declared = integer(
            f"Step 07 {orientation} record count", row["vcf_record_count"]
        )
        inspect_vcf(f"Step 07 {orientation}", Path(vcf), samples, declared)
        counts.append(declared)
    after = (digest(Path(receipt)), *(digest(Path(path)) for path in vcfs))
    if before != after:
        fail(f"Step 07 partition inputs changed during preflight: {partition_id}")
    return Step07Input(
        dict(partition),
        receipt,
        after[0],
        (vcfs[0], vcfs[1]),
        (after[1], after[2]),
        (counts[0], counts[1]),
    )


def paths(arguments: argparse.Namespace, token: str) -> dict[str, Path]:
    cohort_dir = Path(arguments.output_root) / arguments.cohort_id
    stem, qc = arguments.cohort_id, Path(arguments.qc_root)
    return {
        "sites": cohort_dir / f"{stem}.step08_sites.tsv",
        "summary": qc / f"{stem}.step08_summary.tsv",
        "inputs": cohort_dir / f"{stem}.step08_inputs.tsv",
        "tmp_sites": cohort_dir / f".{stem}.step08.{token}.sites.tmp.tsv",
        "tmp_summary": qc / f".{stem}.step08.{token}.summary.tmp.tsv",
        "tmp_inputs": cohort_dir / f".{stem}.step08.{token}.inputs.tmp.tsv",
        "backup_sites": cohort_dir / f".{stem}.step08.{token}.previous.sites.tsv",
        "backup_summary": qc / f".{stem}.step08.{token}.previous.summary.tsv",
        "backup_inputs": cohort_dir / f".{stem}.step08.{token}.previous.inputs.tsv",
        "lock": cohort_dir / f".{stem}.step08.lock",
    }


def build_context(arguments: argparse.Namespace) -> Context:
    threads = integer("--threads", arguments.threads, positive=True)
    token = (
        os.environ.get("EMRYS_RUN_TOKEN")
        or os.environ.get("SLURM_JOB_ID")
        or str(os.getpid())
    )
    try:
        step08.validate_safe_id("--cohort-id", arguments.cohort_id)
        step08.validate_safe_id("run token", token)
        _, samples, _ = step08.validate_sample_manifest(Path(arguments.sample_manifest))
        partition_table = step08.validate_partition_manifest(
            Path(arguments.partition_manifest)
        )
    except step08.ContractError as exc:
        raise ProducerError(str(exc)) from exc
    nonempty("Annotation GTF", Path(arguments.annotation_gtf))
    nonempty("Step 08 R script", Path(arguments.r_script))
    hashes = tuple(
        digest(Path(path))
        for path in (
            arguments.sample_manifest,
            arguments.partition_manifest,
            arguments.annotation_gtf,
        )
    )
    step07 = tuple(
        admit_step07(arguments, row, samples, hashes[0], hashes[1])
        for row in partition_table.rows
    )
    context = Context(
        arguments,
        tuple(samples),
        tuple(map(dict, partition_table.rows)),
        (hashes[0], hashes[1], hashes[2]),
        step07,
        token,
        threads,
        executable(arguments.rscript_bin),
        paths(arguments, token),
    )
    confirm_inputs(context)
    return context


def confirm_inputs(context: Context) -> None:
    arguments = context.arguments
    fixed = zip(
        (
            arguments.sample_manifest,
            arguments.partition_manifest,
            arguments.annotation_gtf,
        ),
        context.hashes,
        strict=True,
    )
    if any(digest(Path(path)) != expected for path, expected in fixed):
        fail("A manifest or annotation input changed during Step 08.")
    for item in context.step07:
        if digest(Path(item.receipt)) != item.receipt_hash or any(
            digest(Path(path)) != expected
            for path, expected in zip(item.vcfs, item.vcf_hashes, strict=True)
        ):
            fail("A Step 07 receipt or VCF changed during Step 08.")


def validate_outputs(context: Context, prefix: str = "") -> None:
    confirm_inputs(context)
    path = lambda name: context.paths[f"{prefix}{name}"]  # noqa: E731
    try:
        inputs = step08.validate_step08_inputs(
            path("inputs"), context.samples, context.partitions, *context.hashes[:2]
        )
        sites = step08.validate_step08_sites(
            path("sites"), context.samples, context.partitions, inputs.rows
        )
        summary = step08.validate_step08_summary(
            path("summary"),
            context.samples,
            context.partitions,
            inputs.rows,
            sites.rows,
            *context.hashes[:2],
        )
    except step08.ContractError as exc:
        raise ProducerError(str(exc)) from exc
    expected = [(item, index) for item in context.step07 for index in range(2)]
    for row, (item, index) in zip(inputs.rows, expected, strict=True):
        values = (
            row["cohort_id"] == context.arguments.cohort_id,
            row["step07_receipt_path"] == str(item.receipt),
            row["step07_receipt_sha256"] == item.receipt_hash,
            row["vcf_path"] == str(item.vcfs[index]),
            row["vcf_sha256"] == item.vcf_hashes[index],
            row["annotation_gtf"] == context.arguments.annotation_gtf,
            row["annotation_gtf_sha256"] == context.hashes[2],
            row["orientation_policy"] == POLICY,
            int(row["declared_vcf_record_count"]) == item.counts[index],
        )
        if not all(values):
            fail("Step 08 input receipt contains invalid admitted provenance.")
    if any(int(row["position"]) < 1 for row in sites.rows):
        fail("Step 08 sites positions must be positive.")
    row = summary.rows[0]
    summary_identity = (
        row["cohort_id"],
        row["annotation_gtf"],
        row["annotation_gtf_sha256"],
        row["orientation_policy"],
    )
    if summary_identity != (
        context.arguments.cohort_id,
        context.arguments.annotation_gtf,
        context.hashes[2],
        POLICY,
    ):
        fail("Step 08 summary contains invalid admitted provenance.")
    confirm_inputs(context)


def r_command(context: Context) -> list[str]:
    arguments, p = context.arguments, context.paths
    command = [context.rscript]
    if os.environ.get("EMRYS_LOCAL_PILOT_R", "0") == "1":
        command += ["--no-environ", "--no-site-file", "--no-restore", "--no-save"]
    command += [
        arguments.r_script,
        "--cohort-id",
        arguments.cohort_id,
        "--sample-manifest",
        arguments.sample_manifest,
        "--partition-manifest",
        arguments.partition_manifest,
        "--step07-root",
        arguments.step07_root,
        "--annotation-gtf",
        arguments.annotation_gtf,
        "--sample-manifest-sha256",
        context.hashes[0],
        "--partition-manifest-sha256",
        context.hashes[1],
        "--annotation-gtf-sha256",
        context.hashes[2],
        "--threads",
        str(context.threads),
        "--sites-output",
        str(p["tmp_sites"]),
        "--inputs-output",
        str(p["tmp_inputs"]),
        "--summary-output",
        str(p["tmp_summary"]),
    ]
    return command


def print_plan(context: Context, command: Sequence[str]) -> None:
    a, p = context.arguments, context.paths
    print("Step 08 VCF preprocessing context:")
    for label, value in (
        ("Mode", "execute" if a.execute else "dry-run"),
        ("Run token", context.token),
        ("Cohort ID", a.cohort_id),
        ("Sample manifest", a.sample_manifest),
        ("Sample manifest SHA-256", context.hashes[0]),
        ("Sample count", len(context.samples)),
        ("Partition manifest", a.partition_manifest),
        ("Partition manifest SHA-256", context.hashes[1]),
        ("Partition count", len(context.partitions)),
        ("Expected Step 07 VCF count", len(context.partitions) * 2),
        ("Step 07 root", a.step07_root),
        ("Annotation GTF", a.annotation_gtf),
        ("Annotation GTF SHA-256", context.hashes[2]),
        ("Threads", context.threads),
        ("Rscript", context.rscript),
        ("R script", a.r_script),
        ("Sites table", p["sites"]),
        ("Input receipt", p["inputs"]),
        ("QC summary", p["summary"]),
        (
            "Existing-output policy",
            "no-clobber" if a.no_clobber else "replace-complete-set",
        ),
    ):
        print(f"  {label}: {value}")
    print("  Samples:\n    " + "\n    ".join(context.samples))
    print(
        "  Orientation policy: legacy_provisional_v1 (provisional; not biologically validated)"
    )
    print("Declared Step 07 input set:")
    for item in context.step07:
        row = item.partition
        print(
            f"  Partition {row['partition_id']} ({row['selector_type']} {row['selector_value']}):"
        )
        print(
            f"    Receipt: {item.receipt}\n    FWD_like VCF: {item.vcfs[0]}\n    REV_like VCF: {item.vcfs[1]}"
        )
    print(f"R command:\n  {shlex.join(command)}")
    print(
        "Planned validation:\n  Recheck sample-manifest, partition-manifest, and annotation-GTF hashes"
    )
    print("  Require exact sites, inputs, and summary TSV headers")
    print(f"  Require exactly {len(context.partitions) * 2} Step 08 input-receipt rows")
    print("  Accept a header-only sites table when counts reconcile")
    print(
        f"Planned publication:\n  Lock: {p['lock']}\n  Temporary sites table: {p['tmp_sites']}"
    )
    print(
        f"  Temporary input receipt: {p['tmp_inputs']}\n  Temporary summary: {p['tmp_summary']}"
    )
    print("  Publish sites, then summary, then the input receipt last as commit marker")
    print("  Restore a previous complete set on failure after backup begins")
    validation = Path(a.qc_root) / f"{a.cohort_id}.step08_validation.tsv"
    prefix = [
        ".venv/bin/python",
        "-X",
        "pycache_prefix=/dev/null",
        "-I",
        "-m",
        "emrys",
        "validate",
    ]
    validator = [
        *prefix,
        "cohort-candidate-preprocessing",
        "--cohort-id",
        a.cohort_id,
        "--sample-manifest",
        a.sample_manifest,
        "--partition-manifest",
        a.partition_manifest,
        "--annotation-gtf",
        a.annotation_gtf,
        "--sites",
        str(p["sites"]),
        "--inputs",
        str(p["inputs"]),
        "--summary",
        str(p["summary"]),
        "--output",
        str(validation),
        "--execute",
    ]
    gate = [
        *prefix,
        "all-pass",
        "--report",
        str(validation),
        "--step-id",
        "08",
        "--scope-id",
        a.cohort_id,
    ]
    print(f"Post-execution validator command:\n  {shlex.join(validator)}")
    print(f"Semantic all-pass gate:\n  {shlex.join(gate)}")


class Publication:
    """Owner-local Step 08 publication state; not a shared operation model."""

    names = ("sites", "summary", "inputs")

    def __init__(self, context: Context) -> None:
        self.context, self.p = context, context.paths
        self.locked = self.owner_written = self.scratch = False
        self.previous = self.started = self.committed = False
        self.child: subprocess.Popen[bytes] | None = None

    @property
    def owner(self) -> Path:
        return self.p["lock"] / "owner"

    def acquire(self) -> None:
        try:
            self.p["lock"].mkdir()
        except FileExistsError as exc:
            raise ProducerError(
                f"Step 08 lock already exists: {self.p['lock']}"
            ) from exc
        self.locked = True
        self.owner.write_text(f"run_token\t{self.context.token}\npid\t{os.getpid()}\n")
        self.owner_written = True

    def release(self) -> None:
        if not self.locked:
            return
        try:
            owned = (
                f"run_token\t{self.context.token}"
                in self.owner.read_text().splitlines()
            )
            unexpected = [
                path for path in self.p["lock"].iterdir() if path != self.owner
            ]
        except OSError as exc:
            raise ProducerError(
                f"Cannot prove Step 08 lock ownership: {self.p['lock']}"
            ) from exc
        if not self.owner_written or not owned or unexpected:
            fail(f"Step 08 lock ownership changed; preserving lock: {self.p['lock']}")
        self.owner.unlink()
        try:
            self.p["lock"].rmdir()
        except OSError as exc:
            try:
                with self.owner.open("x") as stream:
                    stream.write(
                        f"run_token\t{self.context.token}\npid\t{os.getpid()}\n"
                    )
            except OSError:
                pass
            raise ProducerError(
                f"Could not remove Step 08 lock: {self.p['lock']}"
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

    def exclusive(self, name: str) -> None:
        staged, final = self.p[f"tmp_{name}"], self.p[name]
        if (
            not staged.is_file()
            or staged.is_symlink()
            or staged.stat().st_size == 0
            or lexists(final)
        ):
            fail(f"Step 08 {name} cannot be published create-exclusively: {final}")
        try:
            os.link(staged, final)
        except OSError as exc:
            raise ProducerError(
                f"Step 08 {name} final appeared during publication: {final}"
            ) from exc
        if not self.same(staged, final):
            fail(f"Step 08 {name} publication lost staged-inode identity: {final}")

    def rollback(self) -> bool:
        if self.context.arguments.no_clobber:
            results = []
            for name in self.names:
                staged, final = self.p[f"tmp_{name}"], self.p[name]
                if not self.same(staged, final):
                    results.append(False)
                else:
                    try:
                        final.unlink()
                        results.append(not lexists(final))
                    except OSError:
                        results.append(False)
            return all(results)
        if self.previous:
            success = True
            for name in self.names:
                backup, final = self.p[f"backup_{name}"], self.p[name]
                if lexists(backup):
                    try:
                        final.unlink(missing_ok=True)
                        backup.replace(final)
                    except OSError:
                        success = False
                elif not lexists(final):
                    success = False
            return success
        try:
            for name in self.names:
                self.p[name].unlink(missing_ok=True)
            return True
        except OSError:
            return False

    def cleanup(self, failed: bool) -> None:
        if self.child is not None and self.child.poll() is None:
            print(
                f"ERROR: Step 08 child remains active; retaining lock and scratch: {self.p['lock']}",
                file=sys.stderr,
            )
            return
        rollback_failed = (
            failed and self.started and not self.committed and not self.rollback()
        )
        if self.scratch and (
            not rollback_failed or not self.context.arguments.no_clobber
        ):
            for name in self.names:
                try:
                    self.p[f"tmp_{name}"].unlink(missing_ok=True)
                except OSError:
                    pass
            if not rollback_failed and (
                not failed or not self.started or not self.previous or self.committed
            ):
                for name in self.names:
                    try:
                        self.p[f"backup_{name}"].unlink(missing_ok=True)
                    except OSError:
                        pass
        if rollback_failed:
            print(
                f"ERROR: Step 08 rollback incomplete; retaining lock and backups: {self.p['lock']}",
                file=sys.stderr,
            )
        elif self.locked:
            if not self.owner_written:
                try:
                    self.owner.unlink(missing_ok=True)
                    self.p["lock"].rmdir()
                    self.locked = False
                except OSError:
                    pass
            else:
                try:
                    self.release()
                except ProducerError as exc:
                    print(f"ERROR: {exc}", file=sys.stderr)

    def interrupted(self, signum: int, _frame: object) -> None:
        for number in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM):
            signal.signal(number, signal.SIG_IGN)
        child = self.child
        if child is not None and child.poll() is None:
            try:
                child.send_signal(signum)
            except ProcessLookupError:
                pass
            child.wait()
            self.child = None
        raise Interrupted(signum)


def require_no_residue(context: Context) -> None:
    pattern = f".{context.arguments.cohort_id}.step08.*"
    for directory in (context.paths["sites"].parent, Path(context.arguments.qc_root)):
        if directory.is_dir():
            match = next(
                (
                    path
                    for path in directory.iterdir()
                    if fnmatch.fnmatchcase(path.name, pattern)
                ),
                None,
            )
            if match is not None:
                fail(f"Step 08 residue requires operator inspection: {match}")


def execute(context: Context, command: Sequence[str]) -> None:
    p = context.paths
    p["sites"].parent.mkdir(parents=True, exist_ok=True)
    p["summary"].parent.mkdir(parents=True, exist_ok=True)
    tx = Publication(context)
    handlers = {
        number: signal.getsignal(number)
        for number in (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
    }
    failed = True
    try:
        for number in handlers:
            signal.signal(number, signal.SIG_IGN)
        tx.acquire()
        if any(
            lexists(p[f"{kind}_{name}"])
            for kind in ("tmp", "backup")
            for name in tx.names
        ):
            fail("Refusing to reuse existing Step 08 scratch or backup residue.")
        tx.scratch = True
        for number in handlers:
            signal.signal(number, tx.interrupted)
        existing = sum(lexists(p[name]) for name in tx.names)
        if existing not in (0, 3):
            fail("Existing Step 08 outputs are incomplete; expected all three or none.")
        if existing and context.arguments.no_clobber:
            fail("Refusing to replace complete Step 08 outputs under --no-clobber.")
        confirm_inputs(context)
        sys.stdout.flush()
        tx.child = subprocess.Popen(command)
        status = tx.child.wait()
        tx.child = None
        if status:
            fail("Step 08 R VCF preprocessing failed.")
        validate_outputs(context, "tmp_")
        staged_hashes = tuple(digest(p[f"tmp_{name}"]) for name in tx.names)
        tx.previous, tx.started = existing == 3, True
        if tx.previous:
            for name in tx.names:
                p[name].replace(p[f"backup_{name}"])
        for name in tx.names:
            tx.exclusive(name) if context.arguments.no_clobber else p[
                f"tmp_{name}"
            ].replace(p[name])
        validate_outputs(context)
        if tuple(digest(p[name]) for name in tx.names) != staged_hashes:
            fail("Published Step 08 outputs changed during publication.")
        if context.arguments.no_clobber:
            if any(not tx.same(p[f"tmp_{name}"], p[name]) for name in tx.names):
                fail("A Step 08 final no longer matches its staging anchor.")
            for name in tx.names:
                p[f"tmp_{name}"].unlink()
        tx.committed = True
        for name in tx.names:
            p[f"backup_{name}"].unlink(missing_ok=True)
        tx.release()
        failed = False
    finally:
        for number, handler in handlers.items():
            signal.signal(number, handler)
        tx.cleanup(failed)


def run(arguments: argparse.Namespace) -> int:
    context = build_context(arguments)
    command = r_command(context)
    print_plan(context, command)
    if arguments.no_clobber:
        require_no_residue(context)
    if not arguments.execute:
        print(
            "Dry-run complete; no directories or files were created and R was not invoked."
        )
        return 0
    execute(context, command)
    print("Step 08 execute complete.")
    print(f"Published sites table: {context.paths['sites']}")
    print(f"Published input receipt: {context.paths['inputs']}")
    print(f"Published QC summary: {context.paths['summary']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    try:
        return run(parser.parse_args(argv))
    except Interrupted as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 128 + exc.signum
    except (ProducerError, OSError, report.ValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
