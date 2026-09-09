"""Compute paired-CMH scientific outputs in runner-owned working paths."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from emrys.contracts.scientific_evidence import step08, step09
from emrys.libraries.alignments.orientation import (
    LEGACY_PROVISIONAL_ORIENTATION_POLICY as POLICY,
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


@dataclass(frozen=True)
class Context:
    arguments: argparse.Namespace
    samples: tuple[str, ...]
    sample_rows: tuple[Mapping[str, str], ...]
    pairs: tuple[tuple[str, str, str], ...]
    hashes: tuple[str, str, str, str]
    step08_sites: tuple[Mapping[str, str], ...]
    thresholds: tuple[int, float, float, float, float, float]
    rscript: str
    paths: dict[str, Path]


def configure_parser(parser: argparse.ArgumentParser) -> None:
    for name in (
        "analysis-id",
        "cohort-id",
        "sample-manifest",
        "partition-manifest",
        "step08-root",
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
    for name in (
        "all-sites-output",
        "significant-sites-output",
        "summary-output",
        "mutation-output",
        "mutation-pdf-output",
        "depth-pdf-output",
    ):
        parser.add_argument(f"--{name}", required=True, type=Path)


def fail(message: str) -> None:
    raise ProducerError(message)


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
    if not Path(a.step08_root).is_dir():
        fail(f"Step 08 root does not exist or is not a directory: {a.step08_root}")
    step08.require_file("Step 09 R script", a.r_script)
    upstream = Path(a.step08_root) / a.cohort_id
    paths = {
        "step08_sites": upstream / f"{a.cohort_id}.step08_sites.tsv",
        "step08_inputs": upstream / f"{a.cohort_id}.step08_inputs.tsv",
        "all": a.all_sites_output,
        "significant": a.significant_sites_output,
        "summary": a.summary_output,
        "mutation": a.mutation_output,
        "mutation_pdf": a.mutation_pdf_output,
        "depth_pdf": a.depth_pdf_output,
    }
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
        executable(a.rscript_bin),
        paths,
    )
    return context


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
        ("all-sites-output", p["all"]),
        ("significant-sites-output", p["significant"]),
        ("summary-output", p["summary"]),
        ("mutation-spectrum-output", p["mutation"]),
        ("mutation-spectrum-pdf-output", p["mutation_pdf"]),
        ("depth-delta-pdf-output", p["depth_pdf"]),
    )
    command += [
        a.r_script,
        *(str(item) for pair in values for item in (f"--{pair[0]}", pair[1])),
    ]
    if a.background_condition:
        command += ["--background-condition", a.background_condition]
    return command


def validate_outputs(context: Context) -> None:
    a, p = context.arguments, context.paths
    all_sites = step09.validate_step09_results(
        "Step 09 all-sites table",
        p["all"],
        context.samples,
        a.analysis_id,
        context.step08_sites,
    )
    significant = step09.validate_step09_results(
        "Step 09 significant-sites table",
        p["significant"],
        context.samples,
        a.analysis_id,
        context.step08_sites,
    )
    if [row["candidate_id"] for row in all_sites.rows] != [
        row["candidate_id"] for row in context.step08_sites
    ]:
        fail(
            f"Step 09 all-sites rows do not preserve the Step 08 source/analysis contract: {p['all']}"
        )
    step09.validate_significant_subset(all_sites.rows, significant.rows)
    summary = step09.validate_step09_summary(
        p["summary"],
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
    step09.validate_mutation_spectrum(p["mutation"], a.analysis_id, all_sites.rows)
    step09.validate_pdf("Step 09 mutation-spectrum PDF", p["mutation_pdf"])
    step09.validate_pdf("Step 09 depth-delta PDF", p["depth_pdf"])


def execute(context: Context) -> None:
    if subprocess.run(r_command(context)).returncode:
        fail("Step 09 R CMH analysis failed.")
    validate_outputs(context)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    configure_parser(parser)
    try:
        execute(build_context(parser.parse_args(argv)))
        return 0
    except (ProducerError, OSError, UnicodeError, step08.ContractError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
