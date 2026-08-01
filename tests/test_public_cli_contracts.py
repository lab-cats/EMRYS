"""Cross-entrypoint characterization of NORAD's public command surfaces."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
GIT_ORCHESTRATION_ROOT = SCRIPTS_ROOT / "git_orchestration"
MAKE_EXPANSION_GOLDEN = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "public_cli_contracts"
    / "make_target_expansions.json"
)

PYTHON_ENTRYPOINTS = frozenset(
    {
        "build_artifact_index.py",
        "build_run_summary.py",
        "gtf_to_bed12.py",
        "reference_provenance.py",
        "render_run_report.py",
        "render_run_report_bundle.py",
        "restore_quarto.py",
        "runtime_preflight.py",
        "step_09c_scientific_validation.py",
        "storage_inventory.py",
        "validate_artifact_contracts.py",
        "validate_manifest.py",
        "validate_step_00a_star_index.py",
        "validate_step_00b_bed12.py",
        "validate_step_00c_reference_sidecars.py",
        "validate_step_01_star_alignment.py",
        "validate_step_02_canonical_bam.py",
        "validate_step_02b_bam_qc.py",
        "validate_step_03_rseqc_orientation.py",
        "validate_step_04_mark_duplicates.py",
        "validate_step_05_split_ncigar.py",
        "validate_step_06_orientation_outputs.py",
        "validate_step_07_mpileup_outputs.py",
        "validate_step_08_preprocessing_outputs.py",
        "validate_step_09_cmh_outputs.py",
    }
)
PRIVATE_PYTHON_MODULES = frozenset({"_run_summary_science.py"})
DIRECT_PYTHON_ENTRYPOINTS = frozenset(
    {
        "build_run_summary.py",
        "gtf_to_bed12.py",
        "reference_provenance.py",
        "render_run_report.py",
        "restore_quarto.py",
        "runtime_preflight.py",
        "validate_artifact_contracts.py",
        "validate_manifest.py",
    }
)
INTERPRETER_ONLY_PYTHON_ENTRYPOINTS = PYTHON_ENTRYPOINTS - DIRECT_PYTHON_ENTRYPOINTS

SHELL_ENTRYPOINTS = frozenset(
    {
        "render_run_report.sh",
        "step_00c_prepare_gatk_reference.sh",
        "step_01_star_align.sh",
        "step_02_sort_index_bam.sh",
        "step_02b_bam_qc.sh",
        "step_03_infer_strandedness_and_orientation.sh",
        "step_04_mark_duplicates.sh",
        "step_05_split_n_cigar_reads.sh",
        "step_06_split_bam_by_read_orientation.sh",
        "step_07_bcftools_mpileup_by_chrom_and_strand.sh",
        "step_08_vcf_preprocessing.sh",
        "step_09_cmh_editing_site_calling.sh",
        "step_09c_scientific_validation.sh",
    }
)
INTERPRETER_ONLY_SHELL_DEFECTS = frozenset(
    {
        "step_03_infer_strandedness_and_orientation.sh",
        "step_04_mark_duplicates.sh",
        "step_05_split_n_cigar_reads.sh",
    }
)
DIRECT_SHELL_ENTRYPOINTS = SHELL_ENTRYPOINTS - INTERPRETER_ONLY_SHELL_DEFECTS

R_ENTRYPOINTS = frozenset(
    {
        "check_r_environment.R",
        "restore_r_environment.R",
        "step_08_vcf_preprocessing.R",
        "step_09_cmh_editing_site_calling.R",
    }
)
DIRECT_R_ENTRYPOINTS = frozenset(
    {"check_r_environment.R", "restore_r_environment.R"}
)
RSCRIPT_ONLY_ENTRYPOINTS = R_ENTRYPOINTS - DIRECT_R_ENTRYPOINTS

GIT_ORCHESTRATION_PYTHON_ENTRYPOINTS = frozenset(
    {
        "validate_documentation.py",
        "validate_fragment_candidate.py",
        "validate_fragment_target.py",
    }
)
GIT_ORCHESTRATION_SHELL_ENTRYPOINTS = frozenset(
    {
        "apply_fragment_candidate.sh",
        "finalize_fragment_integration.sh",
        "publish_exact_ref.sh",
        "record_fragment_noop.sh",
    }
)
GIT_ORCHESTRATION_PRIVATE_FILES = frozenset(
    {"README.md", "_common.py", "_common.sh"}
)

MAKE_TARGET_DECISIONS = {
    "test": "local_gate",
    "shell-test": "local_gate",
    "validation-shell-contracts": "local_gate",
    "real-r-test": "local_gate",
    "r-restore": "operator_mutation",
    "r-check": "local_gate",
    "local-real-r-test": "local_gate",
    "quarto-restore": "operator_mutation",
    "report-test": "local_gate",
    "validation-report-runtime": "explicit_output",
    "demo-report": "explicit_output",
    "python-coverage-measure": "explicit_output",
    "python-coverage-check": "local_gate",
    "python-coverage-baseline-update": "operator_mutation",
    "validation-python-coverage": "internal_lane",
    "validation-guarded-r": "internal_lane",
    "validation-static": "internal_lane",
    "validate": "local_gate",
    "smoke": "local_gate",
    "lint": "local_gate",
    "all-checks": "local_gate",
    "demo-step03-dry-run": "cluster_deferred",
    "demo-step03": "cluster_deferred",
}
MAKE_CONTEXT_VARIABLES = frozenset(
    {
        "DEMO_REPORT_FORMATS",
        "DEMO_REPORT_ROOT",
        "DEMO_SAMPLE",
        "PYTHON_BIN",
        "PYTHON_COVERAGE_BASELINE",
        "PYTHON_COVERAGE_CURRENT",
        "PYTHON_COVERAGE_DATA",
        "PYTHON_COVERAGE_PYTEST_ARGS",
        "PYTHON_COVERAGE_RAW",
        "PYTHON_COVERAGE_ROOT",
        "QUARTO_BIN",
        "QUARTO_TOOLS_ROOT",
        "REPORT_PYTHON_BIN",
        "REPORT_TEST_RESULT",
        "RSCRIPT_BIN",
        "VALIDATION_ARGS",
        "VALIDATION_JOBS",
        "VALIDATION_PYTHON_WORKERS",
    }
)
MAKE_ENVIRONMENT_PASSTHROUGH = frozenset(
    {"COMSPEC", "PATH", "PATHEXT", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR"}
)


def mode_is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def relative_snapshot(root: Path) -> tuple[str, ...]:
    return tuple(sorted(str(path.relative_to(root)) for path in root.rglob("*")))


def run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def normalized_make_expansion(output: str) -> tuple[str, ...]:
    """Normalize checkout and recursive-Make executable identities."""

    normalized = output.replace(str(REPO_ROOT), "<REPO_ROOT>")
    normalized = re.sub(
        r"(?m)^([ \t]*)(?:\S*/)?g?make(?=\s)",
        r"\1<MAKE>",
        normalized,
    )
    return tuple(normalized.splitlines())


def expected_make_expansions() -> dict[str, tuple[str, ...]]:
    """Load the independently reviewed literal Make expansion oracle."""

    document = json.loads(MAKE_EXPANSION_GOLDEN.read_text(encoding="utf-8"))
    return {
        target: tuple(lines)
        for target, lines in document.items()
    }


def canonical_make_environment() -> dict[str, str]:
    """Build a bounded environment so the golden describes declared defaults."""

    environment = {
        variable: os.environ[variable]
        for variable in MAKE_ENVIRONMENT_PASSTHROUGH
        if variable in os.environ
    }
    environment["LC_ALL"] = "C"
    return environment


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("make real-r-test\n", ("<MAKE> real-r-test",)),
        ("gmake -s r-check\n", ("<MAKE> -s r-check",)),
        (
            "\t\t/usr/bin/make real-r-test\n",
            ("\t\t<MAKE> real-r-test",),
        ),
        (
            "\t\t/opt/homebrew/bin/gmake real-r-test\n",
            ("\t\t<MAKE> real-r-test",),
        ),
    ],
)
def test_make_normalization_accepts_portable_recursive_identities(
    output: str,
    expected: tuple[str, ...],
) -> None:
    assert normalized_make_expansion(output) == expected


def test_make_expansion_ignores_ambient_make_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ambient_makefile = tmp_path / "ambient.mk"
    ambient_makefile.write_text(
        "test:\n\t@printf 'contaminated\\n'\n",
        encoding="utf-8",
    )
    ambient_make_state = {
        "GNUMAKEFLAGS": "--warn-undefined-variables",
        "MAKE": "make",
        "MAKEFILES": str(ambient_makefile),
        "MAKEFLAGS": "--warn-undefined-variables",
        "MAKELEVEL": "9",
        "MAKEOVERRIDES": "RSCRIPT_BIN",
        "MFLAGS": "-s",
    }
    for variable, value in ambient_make_state.items():
        monkeypatch.setenv(variable, value)

    environment = canonical_make_environment()
    assert set(environment).isdisjoint(ambient_make_state)

    result = run_command(
        ["make", "-n", "--no-print-directory", "-C", str(REPO_ROOT), "test"],
        cwd=tmp_path,
        env=environment,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert normalized_make_expansion(result.stdout) == (
        expected_make_expansions()["test"]
    )


def test_inventory_classifies_every_live_public_script() -> None:
    live_python = {path.name for path in SCRIPTS_ROOT.glob("*.py")}
    live_shell = {path.name for path in SCRIPTS_ROOT.glob("*.sh")}
    live_r = {path.name for path in SCRIPTS_ROOT.glob("*.R")}

    assert live_python == PYTHON_ENTRYPOINTS | PRIVATE_PYTHON_MODULES
    assert live_shell == SHELL_ENTRYPOINTS
    assert live_r == R_ENTRYPOINTS
    assert DIRECT_PYTHON_ENTRYPOINTS | INTERPRETER_ONLY_PYTHON_ENTRYPOINTS == (
        PYTHON_ENTRYPOINTS
    )
    assert DIRECT_SHELL_ENTRYPOINTS | INTERPRETER_ONLY_SHELL_DEFECTS == (
        SHELL_ENTRYPOINTS
    )
    assert DIRECT_R_ENTRYPOINTS | RSCRIPT_ONLY_ENTRYPOINTS == R_ENTRYPOINTS


def test_git_orchestration_inventory_is_explicit() -> None:
    live_files = {
        item.name for item in GIT_ORCHESTRATION_ROOT.iterdir() if item.is_file()
    }
    assert live_files == (
        GIT_ORCHESTRATION_PYTHON_ENTRYPOINTS
        | GIT_ORCHESTRATION_SHELL_ENTRYPOINTS
        | GIT_ORCHESTRATION_PRIVATE_FILES
    )


@pytest.mark.parametrize(
    "entrypoint",
    sorted(GIT_ORCHESTRATION_PYTHON_ENTRYPOINTS),
)
def test_git_orchestration_python_help_is_cwd_independent(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = GIT_ORCHESTRATION_ROOT / entrypoint
    before = relative_snapshot(tmp_path)
    result = run_command([sys.executable, str(script), "--help"], cwd=tmp_path)

    assert mode_is_executable(script)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "entrypoint",
    sorted(GIT_ORCHESTRATION_SHELL_ENTRYPOINTS),
)
def test_git_orchestration_shell_help_is_cwd_independent(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = GIT_ORCHESTRATION_ROOT / entrypoint
    before = relative_snapshot(tmp_path)
    result = run_command([str(script), "--help"], cwd=tmp_path)

    assert mode_is_executable(script)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize("entrypoint", sorted(PYTHON_ENTRYPOINTS))
def test_python_help_and_parse_failure_are_cwd_independent_and_side_effect_free(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = SCRIPTS_ROOT / entrypoint
    before = relative_snapshot(tmp_path)

    help_result = run_command(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
    )
    parse_failure = run_command(
        [sys.executable, str(script), "--definitely-not-a-public-option"],
        cwd=tmp_path,
    )

    assert help_result.returncode == 0, help_result.stderr
    assert "usage:" in help_result.stdout.lower()
    assert parse_failure.returncode != 0
    assert "usage:" in parse_failure.stderr.lower()
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize("entrypoint", sorted(DIRECT_PYTHON_ENTRYPOINTS))
def test_executable_python_help_uses_a_prepared_path_from_arbitrary_cwd(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = SCRIPTS_ROOT / entrypoint
    shim_dir = tmp_path / "prepared-path"
    shim_dir.mkdir()
    python_shim = shim_dir / "python3"
    python_shim.write_text(
        f"#!/bin/sh\nexec {str(Path(sys.executable))!r} \"$@\"\n",
        encoding="utf-8",
    )
    python_shim.chmod(0o755)
    environment = os.environ.copy()
    environment["PATH"] = os.pathsep.join((str(shim_dir), "/usr/bin", "/bin"))
    before = relative_snapshot(tmp_path)

    result = run_command([str(script), "--help"], cwd=tmp_path, env=environment)

    assert mode_is_executable(script)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "entrypoint",
    sorted(INTERPRETER_ONLY_PYTHON_ENTRYPOINTS),
)
def test_interpreter_only_python_file_modes_are_characterized(
    entrypoint: str,
) -> None:
    assert not mode_is_executable(SCRIPTS_ROOT / entrypoint)


@pytest.mark.parametrize("entrypoint", sorted(SHELL_ENTRYPOINTS))
def test_shell_help_and_missing_arguments_are_cwd_independent_and_side_effect_free(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = SCRIPTS_ROOT / entrypoint
    before = relative_snapshot(tmp_path)

    help_result = run_command(["/bin/bash", str(script), "--help"], cwd=tmp_path)
    missing = run_command(["/bin/bash", str(script)], cwd=tmp_path)

    assert help_result.returncode == 0, help_result.stderr
    assert "usage" in help_result.stdout.lower()
    assert missing.returncode != 0
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize("entrypoint", sorted(DIRECT_SHELL_ENTRYPOINTS))
def test_executable_shell_help_runs_directly_from_arbitrary_cwd(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = SCRIPTS_ROOT / entrypoint

    result = run_command([str(script), "--help"], cwd=tmp_path)

    assert mode_is_executable(script)
    assert result.returncode == 0, result.stderr
    assert "usage" in result.stdout.lower()


@pytest.mark.parametrize("entrypoint", sorted(INTERPRETER_ONLY_SHELL_DEFECTS))
def test_nonexecutable_public_shell_modes_are_characterized_defects(
    entrypoint: str,
) -> None:
    assert not mode_is_executable(SCRIPTS_ROOT / entrypoint)


@pytest.mark.parametrize("entrypoint", sorted(DIRECT_R_ENTRYPOINTS))
def test_direct_r_entrypoint_modes_are_explicit(entrypoint: str) -> None:
    assert mode_is_executable(SCRIPTS_ROOT / entrypoint)


@pytest.mark.parametrize("entrypoint", sorted(RSCRIPT_ONLY_ENTRYPOINTS))
def test_rscript_only_entrypoint_modes_are_explicit(entrypoint: str) -> None:
    assert not mode_is_executable(SCRIPTS_ROOT / entrypoint)


def test_make_target_inventory_and_applicability_decisions_are_complete() -> None:
    makefile_lines = (REPO_ROOT / "Makefile").read_text(
        encoding="utf-8"
    ).splitlines()
    phony_line = next(
        line
        for line in makefile_lines
        if line.startswith(".PHONY:")
    )
    live_targets = set(phony_line.partition(":")[2].split())
    configurable_variables = {
        match.group(1)
        for line in makefile_lines
        if (match := re.match(r"^([A-Z][A-Z0-9_]*)\s*\?=", line))
    }

    assert live_targets == set(MAKE_TARGET_DECISIONS)
    assert configurable_variables == MAKE_CONTEXT_VARIABLES
    assert set(MAKE_TARGET_DECISIONS.values()) == {
        "cluster_deferred",
        "explicit_output",
        "internal_lane",
        "local_gate",
        "operator_mutation",
    }
    assert set(expected_make_expansions()) == set(MAKE_TARGET_DECISIONS)


@pytest.mark.parametrize("target", sorted(MAKE_TARGET_DECISIONS))
def test_make_targets_have_side_effect_free_command_expansion(
    target: str,
    tmp_path: Path,
) -> None:
    before = relative_snapshot(tmp_path)

    result = run_command(
        ["make", "-n", "--no-print-directory", "-C", str(REPO_ROOT), target],
        cwd=tmp_path,
        env=canonical_make_environment(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert normalized_make_expansion(result.stdout) == (
        expected_make_expansions()[target]
    )
    assert relative_snapshot(tmp_path) == before


def test_make_expansion_oracle_rejects_recipe_mutation(
    tmp_path: Path,
) -> None:
    source = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    original = "test:\n\tpython -m pytest\n"
    mutated = "test:\n\tpython -m pytest -q\n"
    assert original in source
    mutated_makefile = tmp_path / "Makefile"
    mutated_makefile.write_text(
        source.replace(original, mutated, 1),
        encoding="utf-8",
    )

    result = run_command(
        [
            "make",
            "-n",
            "--no-print-directory",
            "-C",
            str(REPO_ROOT),
            "-f",
            str(mutated_makefile),
            "test",
        ],
        cwd=tmp_path,
        env=canonical_make_environment(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert normalized_make_expansion(result.stdout) != (
        expected_make_expansions()["test"]
    )
