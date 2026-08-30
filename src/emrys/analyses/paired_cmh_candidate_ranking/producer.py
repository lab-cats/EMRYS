"""Coordinate Step 09 paired-CMH analysis and its six-file transaction."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import signal
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.contracts.scientific_evidence import step08, step09
from emrys.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY as POLICY,
)

SIGNALS = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
OUTPUTS = (
    ("all", "cmh_all_sites.tsv", "all.tmp.tsv"),
    ("significant", "cmh_significant_sites.tsv", "significant.tmp.tsv"),
    ("mutation", "mutation_spectrum.tsv", "mutation.tmp.tsv"),
    ("mutation_pdf", "mutation_spectrum.pdf", "mutation.tmp.pdf"),
    ("depth_pdf", "depth_delta.pdf", "depth.tmp.pdf"),
    ("summary", "cmh_summary.tsv", "summary.tmp.tsv"),
)
DEFAULTS = {
    "control-condition": "EV",
    "treatment-condition": "PUM1",
    "rna-ref": "A",
    "rna-alt": "G",
    "min-sample-dp": "1",
    "mean-dp-threshold": "50",
    "fdr-threshold": "0.05",
    "common-or-threshold": "1.2",
    "absolute-difference-threshold": "0.005",
    "background-condition": "",
    "background-max-fraction": "0.01",
}


class ProducerError(RuntimeError):
    """Step 09 admission, execution, or publication failed."""


class Interrupted(ProducerError):
    def __init__(self, signum: int) -> None:
        super().__init__(f"Step 09 interrupted by signal {signum}.")
        self.signum = signum


@dataclass(frozen=True)
class Context:
    arguments: argparse.Namespace
    samples: tuple[str, ...]
    sample_rows: tuple[Mapping[str, str], ...]
    pairs: tuple[tuple[str, str, str], ...]
    hashes: tuple[str, str, str, str]
    step08_sites: tuple[Mapping[str, str], ...]
    thresholds: tuple[int, float, float, float, float, float]
    token: str
    rscript: str
    paths: dict[str, Path]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    for name in (
        "analysis-id",
        "cohort-id",
        "sample-manifest",
        "partition-manifest",
        "step08-root",
        "output-root",
    ):
        parser.add_argument(f"--{name}", required=True)
    for name, default in DEFAULTS.items():
        parser.add_argument(f"--{name}", default=default)
    parser.add_argument("--rscript-bin")
    parser.add_argument(
        "--r-script",
        default=os.environ.get(
            "STEP09_R_SCRIPT",
            str(Path(__file__).with_name("step_09_cmh_editing_site_calling.R")),
        ),
    )
    parser.add_argument("--no-clobber", action="store_true")
    parser.add_argument("--execute", action="store_true")


def fail(message: str) -> None:
    raise ProducerError(message)


lexists = os.path.lexists
digest = step08.sha256_file


def _thresholds(a: argparse.Namespace) -> tuple[int, float, float, float, float, float]:
    values = (
        step08.parse_nonnegative_int("min_sample_dp", a.min_sample_dp),
        *(
            step08.parse_number(label, getattr(a, label), nonnegative=True)
            for label in (
                "mean_dp_threshold",
                "fdr_threshold",
                "common_or_threshold",
                "absolute_difference_threshold",
                "background_max_fraction",
            )
        ),
    )
    if (
        values[0] < 1
        or values[2] is None
        or not 0 < values[2] <= 1
        or values[3] is None
        or values[3] <= 1
        or values[4] is None
        or values[4] > 1
        or values[5] is None
        or not 0 < values[5] < 1
    ):
        fail("Step 09 thresholds are outside the supported contract.")
    return values  # type: ignore[return-value]


def executable(requested: str | None) -> str:
    value = requested or os.environ.get("RSCRIPT_BIN_OVERRIDE") or "Rscript"
    if "/" not in value:
        resolved = shutil.which(value)
        if resolved is None:
            fail(f"Rscript executable was not found on PATH: {value}")
        return resolved
    if not Path(value).exists():
        fail(f"Rscript does not exist: {value}")
    if not os.access(value, os.X_OK):
        fail(f"Rscript exists but is not executable: {value}")
    return value


def _paths(a: argparse.Namespace, token: str) -> dict[str, Path]:
    root, cohort = Path(a.output_root) / a.analysis_id, a.cohort_id
    upstream = Path(a.step08_root) / cohort
    result = {
        "root": root,
        "step08_sites": upstream / f"{cohort}.step08_sites.tsv",
        "step08_inputs": upstream / f"{cohort}.step08_inputs.tsv",
        "lock": root / f".{a.analysis_id}.step09.lock",
    }
    for name, final_suffix, temporary_suffix in OUTPUTS:
        final = root / f"{a.analysis_id}.{final_suffix}"
        result[name] = final
        result[f"tmp_{name}"] = (
            root / f".{a.analysis_id}.step09.{token}.{temporary_suffix}"
        )
        result[f"backup_{name}"] = root / f".{final.name}.{token}.previous"
    result["lock_owner_tmp"] = result["lock"] / f".owner.{token}.tmp"
    return result


def build_context(a: argparse.Namespace) -> Context:
    for label in (
        "analysis_id",
        "cohort_id",
        "control_condition",
        "treatment_condition",
    ):
        step08.validate_safe_id(label, getattr(a, label))
    if a.control_condition == a.treatment_condition:
        fail("Control and treatment conditions must differ.")
    if a.background_condition:
        step08.validate_safe_id("background_condition", a.background_condition)
        if a.background_condition in (a.control_condition, a.treatment_condition):
            fail("Background condition must differ from control and treatment.")
    step08.validate_enum("rna_ref", a.rna_ref, ("A", "C", "G", "T"))
    step08.validate_enum("rna_alt", a.rna_alt, ("A", "C", "G", "T"))
    if a.rna_ref == a.rna_alt:
        fail("rna_ref and rna_alt must differ.")
    thresholds = _thresholds(a)
    token = (
        os.environ.get("EMRYS_RUN_TOKEN")
        or os.environ.get("SLURM_JOB_ID")
        or str(os.getpid())
    )
    step08.validate_safe_id("run token", token)
    if not Path(a.step08_root).is_dir():
        fail(f"Step 08 root does not exist or is not a directory: {a.step08_root}")
    step08.require_file("Step 09 R script", a.r_script)
    paths = _paths(a, token)
    fixed = (
        Path(a.sample_manifest),
        Path(a.partition_manifest),
        paths["step08_sites"],
        paths["step08_inputs"],
    )
    hashes = tuple(digest(path) for path in fixed)
    _, samples, rows = step08.validate_sample_manifest(fixed[0])
    partitions = step08.validate_partition_manifest(fixed[1])
    replicates, paired = step09.paired_samples(
        rows, a.control_condition, a.treatment_condition
    )
    if a.background_condition and not any(
        row["condition"] == a.background_condition for row in rows
    ):
        fail(f"background condition has no samples: {a.background_condition}")
    inputs = step08.validate_step08_inputs(
        fixed[3], samples, partitions.rows, hashes[0], hashes[1]
    )
    if any(
        row["cohort_id"] != a.cohort_id or row["orientation_policy"] != POLICY
        for row in inputs.rows
    ):
        fail("Step 08 input receipt content/order/counts are invalid.")
    sites = step08.validate_step08_sites(
        fixed[2], samples, partitions.rows, inputs.rows
    )
    context = Context(
        a,
        tuple(samples),
        tuple(map(dict, rows)),
        tuple((replicate, *paired[replicate]) for replicate in replicates),
        (hashes[0], hashes[1], hashes[2], hashes[3]),
        tuple(map(dict, sites.rows)),
        thresholds,
        token,
        executable(a.rscript_bin),
        paths,
    )
    confirm_inputs(context)
    return context


def confirm_inputs(context: Context) -> None:
    a, p = context.arguments, context.paths
    inputs = (
        ("Sample manifest", Path(a.sample_manifest)),
        ("Partition manifest", Path(a.partition_manifest)),
        ("Step 08 sites table", p["step08_sites"]),
        ("Step 08 input receipt", p["step08_inputs"]),
    )
    for (label, path), expected in zip(inputs, context.hashes, strict=True):
        if digest(path) != expected:
            fail(f"{label} changed during Step 09: {path}")


def r_command(context: Context) -> list[str]:
    a, p = context.arguments, context.paths
    command = [context.rscript]
    if os.environ.get("EMRYS_LOCAL_PILOT_R", "0") == "1":
        command += ["--no-environ", "--no-site-file", "--no-restore", "--no-save"]
    values = (
        ("analysis-id", a.analysis_id),
        ("cohort-id", a.cohort_id),
        ("sample-manifest", a.sample_manifest),
        ("partition-manifest", a.partition_manifest),
        ("sample-manifest-sha256", context.hashes[0]),
        ("partition-manifest-sha256", context.hashes[1]),
        ("step08-sites", p["step08_sites"]),
        ("step08-inputs", p["step08_inputs"]),
        ("step08-sites-sha256", context.hashes[2]),
        ("step08-inputs-sha256", context.hashes[3]),
        *(
            (name, getattr(a, name.replace("-", "_")))
            for name in DEFAULTS
            if name != "background-condition"
        ),
        ("all-sites-output", p["tmp_all"]),
        ("significant-sites-output", p["tmp_significant"]),
        ("summary-output", p["tmp_summary"]),
        ("mutation-spectrum-output", p["tmp_mutation"]),
        ("mutation-spectrum-pdf-output", p["tmp_mutation_pdf"]),
        ("depth-delta-pdf-output", p["tmp_depth_pdf"]),
    )
    command += [
        a.r_script,
        *(str(item) for pair in values for item in (f"--{pair[0]}", pair[1])),
    ]
    if a.background_condition:
        command += ["--background-condition", a.background_condition]
    return command


def print_plan(context: Context, command: Sequence[str]) -> None:
    a, p = context.arguments, context.paths
    print("Step 09 paired CMH context:")
    for label, value in (
        ("Mode", "execute" if a.execute else "dry-run"),
        ("Run token", context.token),
        ("Analysis ID", a.analysis_id),
        ("Cohort ID", a.cohort_id),
        ("Samples / paired strata", f"{len(context.samples)} / {len(context.pairs)}"),
    ):
        print(f"  {label}: {value}")
    print("  Manifest-defined pairs:")
    for replicate, control, treatment in context.pairs:
        print(f"    replicate={replicate} control={control} treatment={treatment}")
    print(
        f"  Control / treatment: {a.control_condition} / {a.treatment_condition}\n  RNA change: {a.rna_ref}>{a.rna_alt}"
    )
    print(
        f"  Step 08 sites: {p['step08_sites']}\n  Step 08 inputs: {p['step08_inputs']}\n  Output directory: {p['root']}"
    )
    print(f"  Background condition: {a.background_condition or 'disabled'}")
    print(
        f"  Existing-output policy: {'no-clobber' if a.no_clobber else 'replace-complete-set'}"
    )
    print(
        "  Orientation policy: legacy_provisional_v1 (provisional; not biologically validated)"
    )
    print(f"R command:\n  {shlex.join(command)}")


def validate_outputs(context: Context, prefix: str = "") -> None:
    confirm_inputs(context)
    a, p = context.arguments, context.paths
    path = lambda name: p[f"{prefix}{name}"]  # noqa: E731
    all_sites = step09.validate_step09_results(
        "Step 09 all-sites table",
        path("all"),
        context.samples,
        a.analysis_id,
        context.step08_sites,
    )
    significant = step09.validate_step09_results(
        "Step 09 significant-sites table",
        path("significant"),
        context.samples,
        a.analysis_id,
        context.step08_sites,
    )
    if [row["candidate_id"] for row in all_sites.rows] != [
        row["candidate_id"] for row in context.step08_sites
    ]:
        fail(
            f"Step 09 all-sites rows do not preserve the Step 08 source/analysis contract: {path('all')}"
        )
    step09.validate_significant_subset(all_sites.rows, significant.rows)
    summary = step09.validate_step09_summary(
        path("summary"),
        a.analysis_id,
        a.cohort_id,
        context.samples,
        context.sample_rows,
        all_sites.rows,
        Path(a.sample_manifest),
        Path(a.partition_manifest),
        p["step08_sites"],
        p["step08_inputs"],
        *context.hashes,
        POLICY,
    )
    row = summary.rows[0]
    expected = {
        "control_condition": a.control_condition,
        "treatment_condition": a.treatment_condition,
        "background_condition": a.background_condition or step08.NA_VALUE,
        "target_rna_change": f"{a.rna_ref}>{a.rna_alt}",
    }
    if any(row[key] != value for key, value in expected.items()):
        fail("Step 09 summary provenance/policy fields are invalid.")
    fields = (
        "min_sample_dp",
        "mean_dp_threshold",
        "fdr_threshold",
        "common_or_threshold",
        "absolute_difference_threshold",
        "background_max_fraction",
    )
    if any(
        float(row[key]) != value
        for key, value in zip(fields, context.thresholds, strict=True)
    ):
        fail("Step 09 summary provenance/policy fields are invalid.")
    step09.validate_step09_result_semantics(all_sites.rows, row, context.sample_rows)
    step09.validate_mutation_spectrum(path("mutation"), a.analysis_id, all_sites.rows)
    step09.validate_pdf("Step 09 mutation-spectrum PDF", path("mutation_pdf"))
    step09.validate_pdf("Step 09 depth-delta PDF", path("depth_pdf"))
    confirm_inputs(context)


class Publication:
    names = tuple(item[0] for item in OUTPUTS)

    def __init__(self, context: Context) -> None:
        self.context, self.p = context, context.paths
        self.locked = self.scratch = False
        self.previous = self.started = self.committed = False
        self.child: subprocess.Popen[bytes] | None = None
        self.pending = 0

    @property
    def owner(self) -> Path:
        return self.p["lock"] / "owner"

    def defer(self, signum: int, _frame: object) -> None:
        self.pending = signum

    def honor(self) -> None:
        if self.pending:
            signum, self.pending = self.pending, 0
            self.interrupted(signum, None)

    def acquire(self) -> None:
        try:
            self.p["lock"].mkdir()
        except FileExistsError as exc:
            raise ProducerError(
                f"Step 09 lock already exists: {self.p['lock']}"
            ) from exc
        self.locked = True
        try:
            self.p["lock_owner_tmp"].write_text(
                f"run_token\t{self.context.token}\npid\t{os.getpid()}\n",
                encoding="utf-8",
            )
            self.p["lock_owner_tmp"].replace(self.owner)
        except OSError as exc:
            raise ProducerError(
                f"Could not publish Step 09 lock owner metadata: {self.owner}"
            ) from exc

    def release(self) -> None:
        if not self.locked:
            return
        try:
            owned = (
                f"run_token\t{self.context.token}"
                in self.owner.read_text(encoding="utf-8").splitlines()
            )
            unexpected = [
                path for path in self.p["lock"].iterdir() if path != self.owner
            ]
        except OSError as exc:
            raise ProducerError(
                f"Step 09 cannot prove lock ownership for release: {self.p['lock']}"
            ) from exc
        if not owned or unexpected:
            fail(f"Step 09 lock ownership changed; preserving lock: {self.p['lock']}")
        try:
            self.owner.unlink()
            self.p["lock"].rmdir()
        except OSError as exc:
            if not lexists(self.owner) and self.p["lock"].is_dir():
                try:
                    with self.owner.open("x", encoding="utf-8") as stream:
                        stream.write(
                            f"run_token\t{self.context.token}\npid\t{os.getpid()}\n"
                        )
                except OSError:
                    pass
            raise ProducerError(
                f"Could not remove Step 09 lock directory; preserving residue: {self.p['lock']}"
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
            or not staged.stat().st_size
            or lexists(final)
        ):
            fail(f"Step 09 output cannot be published create-exclusively: {final}")
        try:
            os.link(staged, final)
        except OSError as exc:
            raise ProducerError(
                f"Step 09 output final appeared during publication: {final}"
            ) from exc
        if not self.same(staged, final):
            fail(
                f"Step 09 output publication did not preserve the staged inode: {final}"
            )

    def rollback(self) -> bool:
        success = True
        for name in self.names:
            staged, final, backup = (
                self.p[f"tmp_{name}"],
                self.p[name],
                self.p[f"backup_{name}"],
            )
            try:
                if self.context.arguments.no_clobber:
                    if not self.same(staged, final):
                        success = False
                    else:
                        final.unlink()
                        success &= not lexists(final)
                elif self.previous and lexists(backup):
                    final.unlink(missing_ok=True)
                    backup.replace(final)
                elif self.previous:
                    success &= lexists(final)
                else:
                    final.unlink(missing_ok=True)
            except OSError:
                if self.previous and lexists(backup):
                    print(
                        f"ERROR: Could not restore Step 09 backup during rollback: {backup}",
                        file=sys.stderr,
                    )
                success = False
        return success

    def discard(self, kind: str) -> None:
        for name in self.names:
            try:
                self.p[f"{kind}_{name}"].unlink(missing_ok=True)
            except OSError:
                pass

    def cleanup(self, failed: bool) -> None:
        if self.child is not None and self.child.poll() is None:
            print(
                f"ERROR: Step 09 child remains active; retaining lock and scratch: {self.p['lock']}",
                file=sys.stderr,
            )
            return
        rollback_failed = (
            failed and self.started and not self.committed and not self.rollback()
        )
        if self.scratch and (
            not rollback_failed or not self.context.arguments.no_clobber
        ):
            self.discard("tmp")
        if self.scratch and self.committed:
            self.discard("backup")
        if rollback_failed:
            print(
                f"ERROR: Step 09 rollback was incomplete; retaining the owned lock for operator recovery: {self.p['lock']}",
                file=sys.stderr,
            )
            return
        if not self.locked:
            return
        if not lexists(self.owner):
            try:
                self.p["lock_owner_tmp"].unlink(missing_ok=True)
                self.p["lock"].rmdir()
                self.locked = False
            except OSError:
                pass
            if not self.locked:
                return
        try:
            self.release()
        except ProducerError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)

    @staticmethod
    def signal_child(child: subprocess.Popen[bytes], signum: int) -> None:
        try:
            os.killpg(child.pid, signum)
        except OSError:
            try:
                child.send_signal(signum)
            except ProcessLookupError:
                pass

    def interrupted(self, signum: int, _frame: object) -> None:
        for number in SIGNALS:
            signal.signal(number, signal.SIG_IGN)
        if self.child is not None and self.child.poll() is None:
            self.signal_child(self.child, signum)
            try:
                self.child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.signal_child(self.child, signal.SIGKILL)
                self.child.wait()
            self.child = None
        raise Interrupted(signum)


def require_no_residue(context: Context) -> None:
    root = context.paths["root"]
    if root.is_dir():
        match = next(root.glob(f".{context.arguments.analysis_id}.*"), None)
        if match is not None:
            fail(f"Step 09 residue requires operator inspection: {match}")


def execute(context: Context, command: Sequence[str]) -> None:
    p = context.paths
    p["root"].mkdir(parents=True, exist_ok=True)
    tx, handlers, failed = (
        Publication(context),
        {number: signal.getsignal(number) for number in SIGNALS},
        True,
    )
    try:
        for number in handlers:
            signal.signal(number, tx.defer)
        tx.acquire()
        for number in handlers:
            signal.signal(number, tx.interrupted)
        tx.honor()
        if any(
            lexists(p[f"{kind}_{name}"])
            for kind in ("tmp", "backup")
            for name in tx.names
        ):
            fail("Refusing to reuse an existing Step 09 scratch path.")
        tx.scratch = True
        existing = sum(lexists(p[name]) for name in tx.names)
        if existing not in (0, 6):
            fail(
                f"Existing Step 09 outputs are incomplete; expected all six or none for analysis: {context.arguments.analysis_id}"
            )
        if existing and context.arguments.no_clobber:
            fail(
                f"Refusing to replace an existing complete Step 09 output set under --no-clobber for analysis: {context.arguments.analysis_id}"
            )
        tx.previous = existing == 6
        confirm_inputs(context)
        sys.stdout.flush()
        for number in handlers:
            signal.signal(number, tx.defer)
        try:
            tx.child = subprocess.Popen(command, start_new_session=True)
        except OSError as exc:
            raise ProducerError("Step 09 R CMH analysis failed.") from exc
        for number in handlers:
            signal.signal(number, tx.interrupted)
        tx.honor()
        status = tx.child.wait()
        tx.child = None
        if status:
            fail("Step 09 R CMH analysis failed.")
        validate_outputs(context, "tmp_")
        staged = tuple(digest(p[f"tmp_{name}"]) for name in tx.names)
        tx.started = True
        if tx.previous:
            for name in tx.names:
                p[name].replace(p[f"backup_{name}"])
        for name in tx.names:
            tx.exclusive(name) if context.arguments.no_clobber else p[
                f"tmp_{name}"
            ].replace(p[name])
        validate_outputs(context)
        if tuple(digest(p[name]) for name in tx.names) != staged:
            fail("Published Step 09 output changed during publication.")
        if context.arguments.no_clobber:
            if any(not tx.same(p[f"tmp_{name}"], p[name]) for name in tx.names):
                fail("Step 09 output final no longer matches its owned staging anchor.")
            tx.discard("tmp")
            if any(lexists(p[f"tmp_{name}"]) for name in tx.names):
                fail("Step 09 could not remove an owned publication anchor.")
        tx.committed = True
        tx.discard("backup")
        tx.release()
        failed = False
    finally:
        for number in handlers:
            signal.signal(number, signal.SIG_IGN)
        try:
            tx.cleanup(failed)
        finally:
            for number, handler in handlers.items():
                signal.signal(number, handler)


def run(arguments: argparse.Namespace) -> int:
    context = build_context(arguments)
    command = r_command(context)
    print_plan(context, command)
    if arguments.no_clobber:
        require_no_residue(context)
    if not arguments.execute:
        print("Dry-run only. No R process was invoked and no output path was created.")
        return 0
    execute(context, command)
    print("Step 09 execute complete. Published six-output transaction:")
    for name in Publication.names:
        print(f"  {context.paths[name]}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    try:
        return run(parser.parse_args(argv))
    except Interrupted as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 128 + exc.signum
    except (ProducerError, OSError, UnicodeError, step08.ContractError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
