"""Read runtime path choices and derive the installed probe policy."""

from __future__ import annotations

import csv
import json
import os
import stat
from dataclasses import replace
from pathlib import Path

from emrys.libraries import validation as report
from emrys.libraries.source_authority import controlled_python_argv

from ._runtime_model import RuntimeCheck, _fail

CHOICE_IDS = (
    "bash",
    "python",
    "star",
    "samtools",
    "java",
    "gatk",
    "picard_jar",
    "bcftools",
    "infer_experiment",
    "gunzip",
    "rscript",
    "renv_library",
)


def load_runtime_policy() -> tuple[RuntimeCheck, ...]:
    """Read the fixed, installed policy; Projects cannot author probe rules."""

    path = Path(__file__).resolve().parents[2] / "resources/runtime/runtime_policy.tsv"
    return tuple(
        RuntimeCheck(
            row["check_id"],
            row["check_type"],
            row["target"],
            tuple(json.loads(row["probe_args"])),
            row["expected"],
        )
        for row in csv.DictReader(
            report.read_bytes(path, "Runtime policy").decode().splitlines(),
            delimiter="\t",
        )
    )


def runtime_profile_checks(data: bytes, source_root: Path) -> tuple[RuntimeCheck, ...]:
    """Expand exactly one selection per tool into the fixed effective checks."""

    try:
        reader = csv.DictReader(
            data.decode("utf-8").splitlines(), delimiter="\t", strict=True
        )
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        _fail(f"Runtime choices are not valid UTF-8 TSV: {exc}")
    if (
        reader.fieldnames != ["check_id", "target"]
        or tuple(row.get("check_id") for row in rows) != CHOICE_IDS
    ):
        _fail(
            "Runtime inventory must contain the exact ordered runtime choices: "
            + ", ".join(CHOICE_IDS)
        )
    if any(
        None in row
        or not row["target"]
        or not Path(row["target"]).is_absolute()
        or any(char in row["target"] for char in "\x00\n\r")
        for row in rows
    ):
        _fail(
            "Runtime choices must be absolute paths without extra columns or unsafe characters"
        )
    selected = {row["check_id"]: row["target"] for row in rows}
    renv_library = Path(selected["renv_library"])
    if os.path.lexists(renv_library):
        state = renv_library.lstat()
        if (
            stat.S_ISLNK(state.st_mode)
            or not stat.S_ISDIR(state.st_mode)
            or renv_library.resolve(strict=True) != renv_library
        ):
            _fail(f"renv library must be a canonical real directory: {renv_library}")
    targets = {
        **selected,
        "snakemake": selected["python"],
        "sha256_python": selected["python"],
        "picard": selected["java"],
        "renv_project": str(source_root),
    }
    arguments = {
        "snakemake": controlled_python_argv(
            selected["python"], "-m", "snakemake", "--version"
        )[1:],
        "picard": ("-jar", selected["picard_jar"], "MarkDuplicates", "--version"),
    }
    return tuple(
        replace(
            check,
            target=check.target
            if check.check_type == "r_namespace"
            else targets[check.check_id],
            probe_args=(selected["rscript"],)
            if check.check_type == "r_namespace"
            else arguments.get(check.check_id, check.probe_args),
        )
        for check in load_runtime_policy()
    )
