"""Produce one receipt-last Step 07 partitioned cohort mpileup transaction."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.libraries.alignments.orientation import ORIENTATIONS
from emrys.libraries.validation import ValidationError, mpileup, sha256_file
from emrys.libraries.validation.tsv import read_strict_tsv

ANNOTATIONS = (
    "FORMAT/DP,FORMAT/AD,FORMAT/ADF,FORMAT/ADR,FORMAT/SP,INFO/AD,INFO/ADF,INFO/ADR"
)
DEFAULT_FILTER = "INFO/AD[1-]>2 & MAX(FORMAT/DP)>20"
DEFAULT_MAX_DEPTH = 10_000_000
INPUT_IDENTITY_ENV = "EMRYS_STEP07_INPUT_IDENTITY_SHA256"
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
SIGNALS = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)


class ProducerError(RuntimeError):
    """Step 07 admission, execution, or publication failed."""


class Interrupted(ProducerError):
    def __init__(self, signum: int) -> None:
        super().__init__(f"Step 07 interrupted by signal {signum}.")
        self.signum = signum


ScientificInput = tuple[str, Path]


@dataclass(frozen=True, slots=True)
class Context:
    arguments: argparse.Namespace
    sample_ids: tuple[str, ...]
    selector_type: str
    selector_value: str
    selector_path: Path | None
    manifest_hashes: tuple[str, str]
    bams: tuple[tuple[Path, ...], tuple[Path, ...]]
    scientific_inputs: tuple[ScientificInput, ...]
    bound_input_identity: str | None
    bcftools: str
    token: str
    paths: dict[str, Path]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    for name in (
        "cohort-id",
        "sample-manifest",
        "partition-manifest",
        "partition-id",
        "orientation-root",
        "reference-fasta",
        "output-root",
    ):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--bcftools-bin")
    parser.add_argument("--max-depth", default=str(DEFAULT_MAX_DEPTH))
    parser.add_argument("--filter-expression", default=DEFAULT_FILTER)
    parser.add_argument("--no-clobber", action="store_true")
    parser.add_argument("--execute", action="store_true")


def fail(message: str) -> None:
    raise ProducerError(message)


def lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _safe_id(label: str, value: str) -> None:
    if not SAFE_ID.fullmatch(value):
        fail(f"{label} must match [A-Za-z0-9][A-Za-z0-9._-]*; got: {value}")


def _positive_integer(label: str, value: str) -> int:
    if not re.fullmatch(r"[1-9][0-9]*", value):
        fail(f"{label} must be a positive integer; got: {value}")
    return int(value)


def _nonempty(label: str, path: Path) -> None:
    try:
        valid = path.is_file() and path.stat().st_size > 0
    except OSError:
        valid = False
    if not valid:
        fail(f"{label} does not exist or is empty: {path}")


def _digest(path: Path) -> str:
    try:
        return sha256_file(path)
    except OSError as exc:
        raise ProducerError(f"Could not hash {path}: {exc}") from exc


def _executable(requested: str | None) -> str:
    value = requested or os.environ.get("BCFTOOLS_BIN_OVERRIDE") or "bcftools"
    if "/" in value:
        if not Path(value).exists():
            fail(f"bcftools does not exist: {value}")
        if not os.access(value, os.X_OK):
            fail(f"bcftools exists but is not executable: {value}")
        return value
    resolved = shutil.which(value)
    if resolved is None:
        fail(f"bcftools executable was not found on PATH: {value}")
    return resolved


def _selector_lines(path: Path) -> Iterable[str]:
    try:
        if path.name.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
                yield from stream
        else:
            with path.open(encoding="utf-8", newline="") as stream:
                yield from stream
    except (OSError, UnicodeError, EOFError) as exc:
        raise ProducerError(f"Could not read regions file {path}: {exc}") from exc


def _validate_regions_file(path: Path, contigs: dict[str, int]) -> None:
    name = path.name.removesuffix(".gz")
    file_type = (
        "bed" if name.endswith(".bed") else "vcf" if name.endswith(".vcf") else "tab"
    )
    row_mode: int | None = None
    data_rows = 0
    for row_number, raw in enumerate(_selector_lines(path), start=1):
        if not raw.strip() or raw.startswith("#"):
            continue
        fields = raw.rstrip("\r\n").split("\t")
        contig = fields[0]
        if contig not in contigs:
            fail(f"regions file contig is absent from FASTA index: {contig}")
        data_rows += 1
        valid = False
        if file_type == "bed" and len(fields) >= 3:
            if re.fullmatch(r"[0-9]+", fields[1]) and re.fullmatch(
                r"[0-9]+", fields[2]
            ):
                start, end = int(fields[1]), int(fields[2])
                valid = 0 <= start < end <= contigs[contig]
        elif file_type == "vcf" and len(fields) >= 2:
            valid = (
                bool(re.fullmatch(r"[1-9][0-9]*", fields[1]))
                and int(fields[1]) <= contigs[contig]
            )
        elif file_type == "tab" and len(fields) >= 2:
            mode = 2 if len(fields) == 2 else 3
            if row_mode is None:
                row_mode = mode
            elif row_mode != mode:
                fail(
                    f"regions file mixes position and interval rows at row {row_number}"
                )
            if re.fullmatch(r"[1-9][0-9]*", fields[1]):
                start = int(fields[1])
                valid = start <= contigs[contig]
                if mode == 3:
                    valid = (
                        valid
                        and bool(re.fullmatch(r"[1-9][0-9]*", fields[2]))
                        and start <= int(fields[2]) <= contigs[contig]
                    )
        if not valid:
            descriptor = (
                "BED interval"
                if file_type == "bed"
                else "VCF position"
                if file_type == "vcf"
                else "regions file row"
            )
            fail(f"invalid {descriptor} on regions file row {row_number}")
    if not data_rows:
        fail(f"regions file contains no selector rows: {path}")


def _selector(
    partition_manifest: Path,
    partition_id: str,
    reference_fai: Path,
) -> tuple[str, str, Path | None]:
    try:
        selector_type, selector_value = mpileup.read_partition(
            partition_manifest, partition_id
        )
        contigs = mpileup.read_fai(reference_fai)
    except (OSError, UnicodeError, ValidationError) as exc:
        fail(str(exc))
    if any(not contig or length < 1 for contig, length in contigs.items()):
        fail(f"Reference FASTA index validation failed: {reference_fai}")
    if selector_type == "region":
        if not mpileup.selector_ok(
            selector_type, selector_value, partition_manifest, contigs
        ):
            fail(
                f"Region selector is invalid or outside FASTA bounds: {selector_value}"
            )
        return selector_type, selector_value, None
    path = Path(selector_value)
    if not path.is_absolute():
        path = (partition_manifest.parent.resolve() / path).resolve()
    _nonempty(f"Regions file for partition {partition_id}", path)
    _validate_regions_file(path, contigs)
    return selector_type, selector_value, path


def _paths(arguments: argparse.Namespace, token: str) -> dict[str, Path]:
    root = Path(arguments.output_root) / arguments.cohort_id / arguments.partition_id
    stem = f"{arguments.cohort_id}.{arguments.partition_id}"
    prefix = root / f".{stem}.step07.{token}"
    return {
        "root": root,
        "fwd": root / f"{stem}.{ORIENTATIONS[0]}.mpileup.vcf",
        "rev": root / f"{stem}.{ORIENTATIONS[1]}.mpileup.vcf",
        "receipt": root / f"{stem}.step07_outputs.tsv",
        "tmp_fwd": Path(f"{prefix}.{ORIENTATIONS[0]}.tmp.vcf"),
        "tmp_rev": Path(f"{prefix}.{ORIENTATIONS[1]}.tmp.vcf"),
        "tmp_receipt": Path(f"{prefix}.outputs.tmp.tsv"),
        "backup_fwd": Path(f"{prefix}.previous.{ORIENTATIONS[0]}.vcf"),
        "backup_rev": Path(f"{prefix}.previous.{ORIENTATIONS[1]}.vcf"),
        "backup_receipt": Path(f"{prefix}.previous.outputs.tsv"),
        "lock": root / f".{stem}.step07.lock",
    }


def _scientific_inputs(
    arguments: argparse.Namespace,
    sample_ids: Sequence[str],
    selector_path: Path | None,
    bams: tuple[tuple[Path, ...], tuple[Path, ...]],
) -> tuple[ScientificInput, ...]:
    paths = [
        ("Sample manifest", Path(arguments.sample_manifest)),
        ("Partition manifest", Path(arguments.partition_manifest)),
        ("Reference FASTA", Path(arguments.reference_fasta)),
        ("Reference FASTA index", Path(f"{arguments.reference_fasta}.fai")),
    ]
    if selector_path is not None:
        paths.append(
            (f"Regions file for partition {arguments.partition_id}", selector_path)
        )
    for index, sample_id in enumerate(sample_ids):
        for orientation_index, orientation in enumerate(ORIENTATIONS):
            bam = bams[orientation_index][index]
            paths.extend(
                (
                    (f"{orientation} BAM for {sample_id}", bam),
                    (f"{orientation} BAI for {sample_id}", Path(f"{bam}.bai")),
                )
            )
    return tuple(paths)


def build_context(arguments: argparse.Namespace) -> Context:
    _safe_id("--cohort-id", arguments.cohort_id)
    _safe_id("--partition-id", arguments.partition_id)
    arguments.max_depth = _positive_integer("--max-depth", arguments.max_depth)
    if not arguments.filter_expression:
        fail("--filter-expression must be non-empty.")
    sample_manifest = Path(arguments.sample_manifest)
    partition_manifest = Path(arguments.partition_manifest)
    reference = Path(arguments.reference_fasta)
    reference_fai = Path(f"{arguments.reference_fasta}.fai")
    for label, path in (
        ("Sample manifest", sample_manifest),
        ("Partition manifest", partition_manifest),
        ("Reference FASTA", reference),
        ("Reference FASTA index", reference_fai),
    ):
        _nonempty(label, path)
    manifest_hashes = (_digest(sample_manifest), _digest(partition_manifest))
    try:
        sample_ids = tuple(mpileup.read_sample_ids(sample_manifest))
    except (OSError, UnicodeError, ValidationError) as exc:
        fail(str(exc))
    for sample_id in sample_ids:
        _safe_id("sample_id", sample_id)
    selector_type, selector_value, selector_path = _selector(
        partition_manifest, arguments.partition_id, reference_fai
    )
    bams = tuple(
        tuple(
            Path(arguments.orientation_root)
            / sample_id
            / f"{sample_id}.{orientation}.bam"
            for sample_id in sample_ids
        )
        for orientation in ORIENTATIONS
    )
    for orientation, members in zip(ORIENTATIONS, bams, strict=True):
        for sample_id, bam in zip(sample_ids, members, strict=True):
            _nonempty(f"{orientation} BAM for {sample_id}", bam)
            _nonempty(f"{orientation} BAI for {sample_id}", Path(f"{bam}.bai"))
    bound = os.environ.pop(INPUT_IDENTITY_ENV, "") or None
    if bound is not None and (
        not arguments.no_clobber
        or os.environ.get("EMRYS_REQUIRE_BOUND_SHA256", "0") != "1"
        or re.fullmatch(r"[0-9a-f]{64}", bound) is None
    ):
        fail("The internal Step 07 input identity is not admitted.")
    token = (
        os.environ.get("EMRYS_RUN_TOKEN")
        or os.environ.get("SLURM_JOB_ID")
        or str(os.getpid())
    )
    _safe_id("Step 07 run token", token)
    context = Context(
        arguments=arguments,
        sample_ids=sample_ids,
        selector_type=selector_type,
        selector_value=selector_value,
        selector_path=selector_path,
        manifest_hashes=manifest_hashes,
        bams=bams,
        scientific_inputs=_scientific_inputs(
            arguments, sample_ids, selector_path, bams
        ),
        bound_input_identity=bound,
        bcftools=_executable(arguments.bcftools_bin),
        token=token,
        paths=_paths(arguments, token),
    )
    _confirm_manifest_hashes(context)
    return context


def _confirm_manifest_hashes(context: Context) -> None:
    for (label, path), expected in zip(
        context.scientific_inputs[:2], context.manifest_hashes, strict=True
    ):
        if _digest(path) != expected:
            fail(f"{label} changed during Step 07: {path}")


def _input_digest(item: ScientificInput) -> str:
    label, path = item
    _nonempty(label, path)
    return _digest(path)


def _snapshot_inputs(context: Context) -> tuple[str, ...]:
    return tuple(map(_input_digest, context.scientific_inputs))


def _confirm_inputs(context: Context, snapshot: tuple[str, ...]) -> None:
    if context.bound_input_identity is not None:
        digest = hashlib.sha256(b"emrys.step07-input-identity.v1\0")
        for item in context.scientific_inputs:
            digest.update(os.fsencode(f"{item[1]}\0{_input_digest(item)}\0"))
        if digest.hexdigest() != context.bound_input_identity:
            fail(
                "Scientific inputs changed after local-pilot admission during "
                "Step 07 --no-clobber execution."
            )
        return
    for item, expected in zip(context.scientific_inputs, snapshot, strict=True):
        if _input_digest(item) != expected:
            fail(f"{item[0]} changed during Step 07 --no-clobber execution: {item[1]}")


def _confirm_stable(context: Context, snapshot: tuple[str, ...]) -> None:
    if context.arguments.no_clobber:
        _confirm_inputs(context, snapshot)
    else:
        _confirm_manifest_hashes(context)


def pipeline_commands(
    context: Context, orientation_index: int
) -> tuple[list[str], list[str]]:
    output = context.paths["tmp_fwd" if orientation_index == 0 else "tmp_rev"]
    selector = (
        ("-r", context.selector_value)
        if context.selector_type == "region"
        else ("-R", str(context.selector_path))
    )
    mpileup_command = [
        context.bcftools,
        "mpileup",
        "-Ou",
        "-f",
        context.arguments.reference_fasta,
        *selector,
        "-d",
        str(context.arguments.max_depth),
        "-I",
        "-a",
        ANNOTATIONS,
        *(str(path) for path in context.bams[orientation_index]),
    ]
    filter_command = [
        context.bcftools,
        "filter",
        "-i",
        context.arguments.filter_expression,
        "-Ov",
        "-o",
        str(output),
        "-",
    ]
    return mpileup_command, filter_command


def _run_pipeline(context: Context, orientation_index: int, tx: Publication) -> None:
    mpileup_command, filter_command = pipeline_commands(context, orientation_index)
    try:
        producer = subprocess.Popen(
            mpileup_command, stdout=subprocess.PIPE, process_group=0
        )
        tx.children = [producer]
        consumer = subprocess.Popen(
            filter_command, stdin=producer.stdout, process_group=0
        )
        tx.children.append(consumer)
        producer.stdout.close()
        filter_status = consumer.wait()
        producer_status = producer.wait()
        tx.children = []
    except OSError as exc:
        tx.stop_children(signal.SIGTERM)
        raise ProducerError(f"Could not execute bcftools pipeline: {exc}") from exc
    if producer_status or filter_status:
        fail(
            f"{ORIENTATIONS[orientation_index]} bcftools mpileup/filter pipeline failed."
        )


def _bcftools(
    context: Context,
    tx: Publication,
    *arguments: str,
    count_lines: bool = False,
) -> str | int:
    try:
        process = subprocess.Popen(
            [context.bcftools, *arguments],
            stdout=subprocess.PIPE,
            text=True,
            process_group=0,
        )
        tx.children = [process]
        output: str | int = (
            sum(1 for _ in process.stdout) if count_lines else process.stdout.read()
        )
        process.stdout.close()
        status = process.wait()
        tx.children = []
    except (OSError, UnicodeError) as exc:
        tx.stop_children(signal.SIGTERM)
        raise ProducerError(f"Could not execute bcftools: {exc}") from exc
    if status:
        fail(f"bcftools {' '.join(arguments[:2])} failed.")
    return output


def _validate_vcf(context: Context, tx: Publication, label: str, path: Path) -> int:
    _nonempty(f"{label} VCF", path)
    _bcftools(context, tx, "view", "-h", str(path))
    sample_output = _bcftools(context, tx, "query", "-l", str(path))
    samples = tuple(sample_output.splitlines())
    if samples != context.sample_ids:
        expected_text = "\n".join(context.sample_ids)
        observed_text = "\n".join(samples)
        fail(
            f"{label} VCF sample order does not match the sample manifest: {path}\n"
            f"Expected samples:\n{expected_text}\n"
            f"Observed samples:\n{observed_text}"
        )
    count = _bcftools(context, tx, "view", "-H", str(path), count_lines=True)
    return count


def _receipt_bytes(context: Context, counts: tuple[int, int]) -> bytes:
    rows = (
        "\t".join(
            (
                context.arguments.cohort_id,
                context.arguments.partition_id,
                context.selector_type,
                context.selector_value,
                orientation,
                str(context.paths[name]),
                *context.manifest_hashes,
                str(len(context.sample_ids)),
                str(counts[index]),
            )
        )
        for index, (orientation, name) in enumerate(
            zip(ORIENTATIONS, ("fwd", "rev"), strict=True)
        )
    )
    return ("\t".join(mpileup.RECEIPT_HEADER) + "\n" + "\n".join(rows) + "\n").encode()


def _validate_receipt(path: Path) -> None:
    _, rows = read_strict_tsv("Step 07 receipt", path, mpileup.RECEIPT_HEADER, fail)
    if len(rows) != 2:
        fail(f"Step 07 receipt must contain exactly two data rows: {path}")


class Publication:
    """Owner-local Step 07 publication state; not a shared operation model."""

    names = ("fwd", "rev", "receipt")

    def __init__(self, context: Context) -> None:
        self.context, self.p = context, context.paths
        self.locked = self.scratch = self.committed = False
        self.prior_set: bool | None = None
        self.children: list[subprocess.Popen[bytes]] = []

    @property
    def owner(self) -> Path:
        return self.p["lock"] / "owner"

    def acquire(self) -> None:
        try:
            self.p["lock"].mkdir()
        except FileExistsError as exc:
            raise ProducerError(
                f"Step 07 lock already exists: {self.p['lock']}"
            ) from exc
        self.locked = True
        try:
            self.owner.write_text(
                f"run_token\t{self.context.token}\npid\t{os.getpid()}\n"
            )
        except OSError:
            try:
                self.owner.unlink(missing_ok=True)
                self.p["lock"].rmdir()
            except OSError:
                pass
            else:
                self.locked = False
            raise

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
                f"Cannot prove Step 07 lock ownership: {self.p['lock']}"
            ) from exc
        if not owned or unexpected:
            fail(f"Step 07 lock ownership changed; preserving lock: {self.p['lock']}")
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
                f"Could not remove Step 07 lock: {self.p['lock']}"
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
            fail(f"Step 07 {name} cannot be published create-exclusively: {final}")
        try:
            os.link(staged, final)
        except OSError as exc:
            raise ProducerError(
                f"Step 07 {name} final appeared during publication: {final}"
            ) from exc
        if not self.same(staged, final):
            fail(f"Step 07 {name} publication lost staged-inode identity: {final}")

    def rollback(self) -> bool:
        success = True
        for name in self.names:
            final = self.p[name]
            try:
                if self.context.arguments.no_clobber:
                    staged = self.p[f"tmp_{name}"]
                    if not self.same(staged, final):
                        success = False
                        continue
                    final.unlink()
                elif self.prior_set:
                    backup = self.p[f"backup_{name}"]
                    if lexists(backup):
                        final.unlink(missing_ok=True)
                        backup.replace(final)
                    elif not lexists(final):
                        success = False
                else:
                    final.unlink(missing_ok=True)
            except OSError:
                success = False
        return success

    def discard(self, prefix: str) -> None:
        for name in self.names:
            try:
                self.p[f"{prefix}_{name}"].unlink(missing_ok=True)
            except OSError:
                pass

    def cleanup(self, failed: bool) -> None:
        if any(process.poll() is None for process in self.children):
            print(
                f"ERROR: Step 07 child remains active; retaining lock and scratch: {self.p['lock']}",
                file=sys.stderr,
            )
            return
        rollback_failed = bool(
            failed
            and self.prior_set is not None
            and not self.committed
            and not self.rollback()
        )
        if self.scratch:
            if not rollback_failed or not self.context.arguments.no_clobber:
                self.discard("tmp")
            if not rollback_failed:
                self.discard("backup")
        if rollback_failed:
            print(
                f"ERROR: Step 07 rollback incomplete; retaining lock and backups: {self.p['lock']}",
                file=sys.stderr,
            )
        elif self.locked:
            try:
                self.release()
            except ProducerError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)

    def interrupted(self, signum: int, _frame: object) -> None:
        for number in SIGNALS:
            signal.signal(number, signal.SIG_IGN)
        self.signal_children(signum)
        raise Interrupted(signum)

    @staticmethod
    def signal(process: subprocess.Popen[bytes], signum: int) -> None:
        try:
            os.killpg(process.pid, signum)
        except OSError:
            try:
                process.send_signal(signum)
            except ProcessLookupError:
                pass

    def signal_children(self, signum: int) -> None:
        for process in reversed(self.children):
            if process.poll() is None:
                self.signal(process, signum)

    def reap_children(self) -> None:
        for process in reversed(self.children):
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.signal(process, signal.SIGKILL)
                process.wait()
        self.children = []

    def stop_children(self, signum: int) -> None:
        self.signal_children(signum)
        self.reap_children()


def _require_no_residue(context: Context) -> None:
    root = context.paths["root"]
    if not root.is_dir():
        return
    prefix = f".{context.arguments.cohort_id}.{context.arguments.partition_id}.step07."
    match = next(
        (path for path in root.iterdir() if path.name.startswith(prefix)), None
    )
    if match is not None:
        fail(f"Step 07 residue requires operator inspection: {match}")


def _print_plan(context: Context) -> None:
    a, p = context.arguments, context.paths
    validation_report = (
        p["root"] / f"{a.cohort_id}.{a.partition_id}.step07_validation.tsv"
    )
    validate_prefix = ("emrys", "validate")
    validator_bindings = (
        ("--cohort-id", a.cohort_id),
        ("--partition-id", a.partition_id),
        ("--sample-manifest", a.sample_manifest),
        ("--partition-manifest", a.partition_manifest),
        ("--reference-fai", f"{a.reference_fasta}.fai"),
        ("--fwd-vcf", p["fwd"]),
        ("--rev-vcf", p["rev"]),
        ("--receipt", p["receipt"]),
        ("--output", validation_report),
    )
    validator_command = (
        *validate_prefix,
        "partitioned-cohort-mpileup",
        *(str(item) for pair in validator_bindings for item in pair),
        "--execute",
    )
    all_pass_command = (
        f"{shlex.join(validate_prefix)} all-pass "
        f"--report {shlex.quote(str(validation_report))} --step-id 07 "
        f"--scope-id {a.cohort_id}__{a.partition_id}"
    )
    print("Step 07 cohort mpileup context:")
    for label, value in (
        ("Mode", "execute" if a.execute else "dry-run"),
        ("Run token", context.token),
        ("Cohort ID", a.cohort_id),
        ("Sample manifest", a.sample_manifest),
        ("Sample manifest SHA-256", context.manifest_hashes[0]),
        ("Sample count", len(context.sample_ids)),
        ("Partition manifest", a.partition_manifest),
        ("Partition manifest SHA-256", context.manifest_hashes[1]),
        ("Partition ID", a.partition_id),
        (
            "Selector declared in manifest",
            f"{context.selector_type} {context.selector_value}",
        ),
        (
            "Selector resolved for execution",
            f"{context.selector_type} {context.selector_path or context.selector_value}",
        ),
        ("Reference FASTA", a.reference_fasta),
        ("Reference FAI", f"{a.reference_fasta}.fai"),
        ("Orientation root", a.orientation_root),
        ("Output directory", p["root"]),
        (f"{ORIENTATIONS[0]} VCF", p["fwd"]),
        (f"{ORIENTATIONS[1]} VCF", p["rev"]),
        ("Receipt", p["receipt"]),
        ("bcftools", context.bcftools),
        ("Maximum depth", a.max_depth),
        ("Filter expression", a.filter_expression),
        (
            "Existing-output policy",
            "no-clobber" if a.no_clobber else "replace-complete-set",
        ),
    ):
        print(f"  {label}: {value}")
    print("  Samples:\n    " + "\n    ".join(context.sample_ids))
    print("  Orientation policy: mechanical FWD_like/REV_like labels only")
    for index, orientation in enumerate(ORIENTATIONS):
        first, second = pipeline_commands(context, index)
        print(
            f"{orientation} pipeline:\n  {shlex.join(first)}\n  | {shlex.join(second)}"
        )
    print(
        "Planned validation:\n  bcftools view/query on both VCFs; manifest sample order; record counts"
    )
    print(
        "Planned publication:\n"
        f"  Lock: {p['lock']}\n"
        f"  Temporary {ORIENTATIONS[0]} VCF: {p['tmp_fwd']}\n"
        f"  Temporary {ORIENTATIONS[1]} VCF: {p['tmp_rev']}\n"
        f"  Temporary receipt: {p['tmp_receipt']}\n"
        f"  Backup {ORIENTATIONS[0]} VCF: {p['backup_fwd']}\n"
        f"  Backup {ORIENTATIONS[1]} VCF: {p['backup_rev']}\n"
        f"  Backup receipt: {p['backup_receipt']}\n"
        "  Publish VCF, VCF, then receipt with rollback protection"
    )
    print(f"Post-execution validator command:\n  {shlex.join(validator_command)}")
    print(f"Semantic all-pass gate:\n  {all_pass_command}")


def execute(context: Context) -> tuple[int, int]:
    p = context.paths
    p["root"].mkdir(parents=True, exist_ok=True)
    tx = Publication(context)
    handlers = {number: signal.getsignal(number) for number in SIGNALS}
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
            fail("Refusing to reuse existing Step 07 scratch or backup residue.")
        tx.scratch = True
        for number in handlers:
            signal.signal(number, tx.interrupted)
        existing = sum(lexists(p[name]) for name in tx.names)
        if existing not in (0, 3):
            fail("Existing Step 07 outputs are incomplete; expected all three or none.")
        if existing and context.arguments.no_clobber:
            fail("Refusing to replace complete Step 07 outputs under --no-clobber.")
        snapshot = (
            _snapshot_inputs(context)
            if context.arguments.no_clobber and context.bound_input_identity is None
            else ()
        )
        _confirm_manifest_hashes(context)
        sys.stdout.flush()
        _run_pipeline(context, 0, tx)
        _run_pipeline(context, 1, tx)
        _confirm_stable(context, snapshot)
        counts = (
            _validate_vcf(
                context, tx, f"Published {ORIENTATIONS[0]} temporary", p["tmp_fwd"]
            ),
            _validate_vcf(
                context, tx, f"Published {ORIENTATIONS[1]} temporary", p["tmp_rev"]
            ),
        )
        p["tmp_receipt"].write_bytes(_receipt_bytes(context, counts))
        _validate_receipt(p["tmp_receipt"])
        _confirm_stable(context, snapshot)
        tx.prior_set = existing == 3
        if tx.prior_set:
            for name in tx.names:
                p[name].replace(p[f"backup_{name}"])
        for name in ("fwd", "rev"):
            tx.exclusive(name) if context.arguments.no_clobber else p[
                f"tmp_{name}"
            ].replace(p[name])
        published = (
            _validate_vcf(context, tx, f"Published {ORIENTATIONS[0]}", p["fwd"]),
            _validate_vcf(context, tx, f"Published {ORIENTATIONS[1]}", p["rev"]),
        )
        if published != counts:
            fail("Published Step 07 VCF record count changed during publication.")
        tx.exclusive("receipt") if context.arguments.no_clobber else p[
            "tmp_receipt"
        ].replace(p["receipt"])
        _validate_receipt(p["receipt"])
        if context.arguments.no_clobber:
            if any(not tx.same(p[f"tmp_{name}"], p[name]) for name in tx.names):
                fail("A Step 07 final no longer matches its staging anchor.")
            for name in tx.names:
                p[f"tmp_{name}"].unlink()
        tx.committed = True
        for name in tx.names:
            p[f"backup_{name}"].unlink(missing_ok=True)
        tx.release()
        failed = False
        return counts
    except Interrupted:
        tx.reap_children()
        raise
    finally:
        for number, handler in handlers.items():
            signal.signal(number, handler)
        tx.cleanup(failed)


def run(arguments: argparse.Namespace) -> int:
    context = build_context(arguments)
    _print_plan(context)
    if arguments.no_clobber:
        _require_no_residue(context)
    if not arguments.execute:
        print("Dry-run complete; no directories or files were created.")
        return 0
    counts = execute(context)
    print("Step 07 execute complete.")
    for index, (orientation, name) in enumerate(
        zip(ORIENTATIONS, ("fwd", "rev"), strict=True)
    ):
        print(
            f"Published {orientation} VCF: {context.paths[name]} ({counts[index]} records)"
        )
    print(f"Published receipt: {context.paths['receipt']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    try:
        return run(parser.parse_args(argv))
    except Interrupted as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 128 + exc.signum
    except (ProducerError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
