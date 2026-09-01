"""Cross-entrypoint characterization of EMRYS's public command surfaces."""

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
DOCUMENTATION_TOOLS_ROOT = SCRIPTS_ROOT / "documentation"
MAKE_EXPANSION_GOLDEN = (
    REPO_ROOT
    / "tests"
    / "fixtures"
    / "public_cli_contracts"
    / "make_target_expansions.json"
)
CLI_USAGE_ERROR = 2

PYTHON_ENTRYPOINT_PATHS: dict[str, Path] = {
    "benchmark_stage_resources.py": Path("scripts/benchmark_stage_resources.py"),
}
PYTHON_ENTRYPOINTS = frozenset(PYTHON_ENTRYPOINT_PATHS)
REPOSITORY_PACKAGE_BOOTSTRAP_ENTRYPOINTS = frozenset()
PRIVATE_PYTHON_MODULES = frozenset()
DIRECT_PYTHON_ENTRYPOINTS = frozenset({"benchmark_stage_resources.py"})
INTERPRETER_ONLY_PYTHON_ENTRYPOINTS = PYTHON_ENTRYPOINTS - DIRECT_PYTHON_ENTRYPOINTS
EMRYS_COMMANDS = (
    (("init", "project"), "usage: emrys init project"),
    (
        ("init", "synthetic"),
        "usage: emrys init synthetic",
    ),
    (("runtime", "discover"), "usage: emrys runtime discover"),
    (("doctor",), "usage: emrys doctor"),
    (("run",), "usage: emrys run"),
    (("resume",), "usage: emrys resume"),
    (("report",), "usage: emrys report"),
    (
        ("validate", "artifact-contracts"),
        "usage: emrys validate artifact-contracts",
    ),
    (("validate", "all-pass"), "usage: emrys validate all-pass"),
    (
        ("validate", "project"),
        "usage: emrys validate project",
    ),
    (
        ("reconcile", "reference-provenance"),
        "usage: emrys reconcile reference-provenance",
    ),
    (
        ("inspect", "run"),
        "usage: emrys inspect run",
    ),
    (
        ("inspect", "runtime-availability"),
        "usage: emrys inspect runtime-availability",
    ),
    (
        ("inspect", "storage-inventory"),
        "usage: emrys inspect storage-inventory",
    ),
    (
        ("inspect", "storage-qualification"),
        "usage: emrys inspect storage-qualification",
    ),
    (("convert", "gtf-to-bed12"), "usage: emrys convert gtf-to-bed12"),
    (("validate", "bed12"), "usage: emrys validate bed12"),
    (("validate", "canonical-bam"), "usage: emrys validate canonical-bam"),
    (
        ("validate", "canonical-bam-qc"),
        "usage: emrys validate canonical-bam-qc",
    ),
    (
        ("validate", "cohort-candidate-preprocessing"),
        "usage: emrys validate cohort-candidate-preprocessing",
    ),
    (
        ("validate", "duplicate-marking"),
        "usage: emrys validate duplicate-marking",
    ),
    (("validate", "fasta-sidecars"), "usage: emrys validate fasta-sidecars"),
    (("validate", "manifest"), "usage: emrys validate manifest"),
    (
        ("validate", "mechanical-orientation"),
        "usage: emrys validate mechanical-orientation",
    ),
    (
        ("validate", "paired-cmh-candidate-ranking"),
        "usage: emrys validate paired-cmh-candidate-ranking",
    ),
    (
        ("validate", "partitioned-cohort-mpileup"),
        "usage: emrys validate partitioned-cohort-mpileup",
    ),
    (
        ("validate", "rseqc-orientation"),
        "usage: emrys validate rseqc-orientation",
    ),
    (
        ("validate", "scientific-context-projection"),
        "usage: emrys validate scientific-context-projection",
    ),
    (("validate", "split-n-cigar"), "usage: emrys validate split-n-cigar"),
    (("validate", "star-alignment"), "usage: emrys validate star-alignment"),
    (("validate", "star-index"), "usage: emrys validate star-index"),
)

SHELL_ENTRYPOINT_PATHS = {
    "check_fastq_pairs.sh": Path(
        "src/emrys/ingestion/sample_manifest_admission/check_fastq_pairs.sh"
    ),
    "step_00a_build_star_index.sh": Path(
        "src/emrys/stages/star_index/step_00a_build_star_index.sh"
    ),
    "step_00c_prepare_gatk_reference.sh": Path(
        "src/emrys/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh"
    ),
    "step_01_star_align.sh": Path(
        "src/emrys/stages/star_alignment/step_01_star_align.sh"
    ),
    "step_02_sort_index_bam.sh": Path(
        "src/emrys/stages/canonical_bam/step_02_sort_index_bam.sh"
    ),
    "step_02b_bam_qc.sh": Path(
        "src/emrys/evidence/canonical_bam_qc/step_02b_bam_qc.sh"
    ),
    "step_03_infer_strandedness_and_orientation.sh": Path(
        "src/emrys/evidence/rseqc_orientation/"
        "step_03_infer_strandedness_and_orientation.sh"
    ),
    "step_04_mark_duplicates.sh": Path(
        "src/emrys/stages/duplicate_marking/step_04_mark_duplicates.sh"
    ),
    "step_05_split_n_cigar_reads.sh": Path(
        "src/emrys/stages/split_n_cigar/step_05_split_n_cigar_reads.sh"
    ),
    "scientific_context_projection.sh": Path(
        "src/emrys/analyses/paired_cmh_candidate_ranking/"
        "scientific_context_projection/"
        "scientific_context_projection.sh"
    ),
}
SHELL_ENTRYPOINTS = frozenset(SHELL_ENTRYPOINT_PATHS)
INTERPRETER_ONLY_SHELL_DEFECTS = frozenset(
    {
        "step_03_infer_strandedness_and_orientation.sh",
        "step_04_mark_duplicates.sh",
        "step_05_split_n_cigar_reads.sh",
    }
)
DIRECT_SHELL_ENTRYPOINTS = SHELL_ENTRYPOINTS - INTERPRETER_ONLY_SHELL_DEFECTS

R_ENTRYPOINT_PATHS = {
    "check_r_environment.R": Path("scripts/check_r_environment.R"),
    "restore_r_environment.R": Path("scripts/restore_r_environment.R"),
    "step_08_vcf_preprocessing.R": Path(
        "src/emrys/stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.R"
    ),
    "step_09_cmh_editing_site_calling.R": Path(
        "src/emrys/analyses/paired_cmh_candidate_ranking/"
        "step_09_cmh_editing_site_calling.R"
    ),
    "scientific_context_projection.R": Path(
        "src/emrys/analyses/paired_cmh_candidate_ranking/"
        "scientific_context_projection/"
        "scientific_context_projection.R"
    ),
}
R_ENTRYPOINTS = frozenset(R_ENTRYPOINT_PATHS)
DIRECT_R_ENTRYPOINTS = frozenset({"check_r_environment.R", "restore_r_environment.R"})
RSCRIPT_ONLY_ENTRYPOINTS = R_ENTRYPOINTS - DIRECT_R_ENTRYPOINTS

DOCUMENTATION_PYTHON_ENTRYPOINTS = frozenset(
    {
        "validate_structure.py",
    }
)
DOCUMENTATION_SHELL_ENTRYPOINTS = frozenset()
DOCUMENTATION_PRIVATE_FILES = frozenset({"README.md"})

MAKE_TARGET_DECISIONS = {
    "test": "local_gate",
    "documentation-check": "local_gate",
    "shell-test": "local_gate",
    "validation-shell-contracts": "local_gate",
    "validation-wheel-smoke": "internal_lane",
    "real-r-test": "local_gate",
    "r-restore": "operator_mutation",
    "r-check": "local_gate",
    "local-real-r-test": "local_gate",
    "report-test": "local_gate",
    "dashboard": "operator_observation",
    "python-coverage-shard": "internal_lane",
    "python-coverage-finalize": "internal_lane",
    "python-coverage-enforce": "internal_lane",
    "python-coverage-measure": "explicit_output",
    "python-coverage-check": "local_gate",
    "python-coverage-baseline-update": "operator_mutation",
    "validation-guarded-r": "internal_lane",
    "validation-static": "internal_lane",
    "validate": "local_gate",
    "smoke": "local_gate",
    "lint": "local_gate",
    "all-checks": "local_gate",
}
MAKE_OPERATION_CONTEXT_VARIABLES = frozenset(
    {
        "DASHBOARD_PYTHON_BIN",
        "DASHBOARD_REFRESH",
        "JOB_ID",
        "LOG_DIR",
    }
)
MAKE_CONTEXT_VARIABLES = frozenset(
    {
        "PYTHON_BIN",
        "PYTHON_COVERAGE_BASELINE",
        "PYTHON_COVERAGE_CURRENT",
        "PYTHON_COVERAGE_DATA",
        "PYTHON_COVERAGE_RAW",
        "PYTHON_COVERAGE_ROOT",
        "PYTHON_COVERAGE_WORKERS",
        "PYTHON_TEST_DURATION_BASELINE",
        "PYTHON_TEST_SHARD_COUNT",
        "PYTHON_TEST_SHARD_INDEX",
        "PYTHON_TEST_SHARD_RECEIPT",
        "REPORT_PYTHON_BIN",
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


def python_entrypoint_path(entrypoint: str) -> Path:
    return REPO_ROOT / PYTHON_ENTRYPOINT_PATHS[entrypoint]


def shell_entrypoint_path(entrypoint: str) -> Path:
    return REPO_ROOT / SHELL_ENTRYPOINT_PATHS[entrypoint]


def r_entrypoint_path(entrypoint: str) -> Path:
    return REPO_ROOT / R_ENTRYPOINT_PATHS[entrypoint]


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
    return {target: tuple(lines) for target, lines in document.items()}


def accepted_make_expansion_renderings(
    expected: tuple[str, ...],
) -> frozenset[tuple[str, ...]]:
    """Allow the two exact GNU Make dry-run recipe-prefix renderings."""

    without_recipe_prefix = tuple(
        line[1:] if line.startswith("\t") else line for line in expected
    )
    return frozenset((expected, without_recipe_prefix))


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


def test_make_expansion_accepts_only_complete_portable_indent_renderings() -> None:
    literal = (
        "command \\",
        "\t\tcontinued \\",
        "\t\t\tdeeper",
    )
    without_recipe_prefix = (
        "command \\",
        "\tcontinued \\",
        "\t\tdeeper",
    )
    mixed = (
        "command \\",
        "\tcontinued \\",
        "\t\t\tdeeper",
    )
    over_normalized = (
        "command \\",
        "continued \\",
        "\tdeeper",
    )

    accepted = accepted_make_expansion_renderings(literal)

    assert accepted == frozenset((literal, without_recipe_prefix))
    assert mixed not in accepted
    assert over_normalized not in accepted


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
    assert normalized_make_expansion(
        result.stdout
    ) in accepted_make_expansion_renderings(expected_make_expansions()["test"])


def test_inventory_classifies_every_live_public_script() -> None:
    live_python = {path.name for path in SCRIPTS_ROOT.glob("*.py")}
    live_shell = {path.name for path in SCRIPTS_ROOT.glob("*.sh")}
    live_r = {path.name for path in SCRIPTS_ROOT.glob("*.R")}

    flat_python_entrypoints = {
        path.name
        for path in PYTHON_ENTRYPOINT_PATHS.values()
        if path.parent == Path("scripts")
    }
    flat_shell_entrypoints = {
        path.name
        for path in SHELL_ENTRYPOINT_PATHS.values()
        if path.parent == Path("scripts")
    }
    assert live_python == flat_python_entrypoints | PRIVATE_PYTHON_MODULES
    assert all(python_entrypoint_path(name).is_file() for name in PYTHON_ENTRYPOINTS)
    assert len(set(PYTHON_ENTRYPOINT_PATHS.values())) == len(PYTHON_ENTRYPOINTS)
    assert live_shell == flat_shell_entrypoints
    assert all(shell_entrypoint_path(name).is_file() for name in SHELL_ENTRYPOINTS)
    assert len(set(SHELL_ENTRYPOINT_PATHS.values())) == len(SHELL_ENTRYPOINTS)
    flat_r_entrypoints = {
        path.name
        for path in R_ENTRYPOINT_PATHS.values()
        if path.parent == Path("scripts")
    }
    assert live_r == flat_r_entrypoints
    assert all(r_entrypoint_path(name).is_file() for name in R_ENTRYPOINTS)
    assert len(set(R_ENTRYPOINT_PATHS.values())) == len(R_ENTRYPOINTS)
    assert DIRECT_PYTHON_ENTRYPOINTS | INTERPRETER_ONLY_PYTHON_ENTRYPOINTS == (
        PYTHON_ENTRYPOINTS
    )
    assert DIRECT_SHELL_ENTRYPOINTS | INTERPRETER_ONLY_SHELL_DEFECTS == (
        SHELL_ENTRYPOINTS
    )
    assert DIRECT_R_ENTRYPOINTS | RSCRIPT_ONLY_ENTRYPOINTS == R_ENTRYPOINTS


def test_documentation_tool_inventory_is_explicit() -> None:
    live_files = {
        item.name for item in DOCUMENTATION_TOOLS_ROOT.iterdir() if item.is_file()
    }
    assert live_files == (
        DOCUMENTATION_PYTHON_ENTRYPOINTS
        | DOCUMENTATION_SHELL_ENTRYPOINTS
        | DOCUMENTATION_PRIVATE_FILES
    )


@pytest.mark.parametrize(
    "entrypoint",
    sorted(DOCUMENTATION_PYTHON_ENTRYPOINTS),
)
def test_documentation_python_help_is_cwd_independent(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = DOCUMENTATION_TOOLS_ROOT / entrypoint
    before = relative_snapshot(tmp_path)
    result = run_command([sys.executable, str(script), "--help"], cwd=tmp_path)

    assert mode_is_executable(script)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "entrypoint",
    sorted(DOCUMENTATION_SHELL_ENTRYPOINTS),
)
def test_documentation_shell_help_is_cwd_independent(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = DOCUMENTATION_TOOLS_ROOT / entrypoint
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
    script = python_entrypoint_path(entrypoint)
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


@pytest.mark.parametrize(("command", "expected_usage"), EMRYS_COMMANDS)
def test_installed_emrys_commands_are_isolated_and_cwd_independent(
    command: tuple[str, ...],
    expected_usage: str,
    tmp_path: Path,
) -> None:
    foreign_root = tmp_path / "foreign"
    foreign_package = foreign_root / "emrys"
    foreign_package.mkdir(parents=True)
    (foreign_package / "__init__.py").write_text(
        "raise RuntimeError('foreign emrys package imported')\n",
        encoding="utf-8",
    )
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(foreign_root)
    before = relative_snapshot(tmp_path)

    help_result = run_command(
        [sys.executable, "-I", "-m", "emrys", *command, "--help"],
        cwd=invocation_cwd,
        env=environment,
    )
    parse_failure = run_command(
        [
            sys.executable,
            "-I",
            "-m",
            "emrys",
            *command,
            "--definitely-not-a-public-option",
        ],
        cwd=invocation_cwd,
        env=environment,
    )

    assert help_result.returncode == 0, help_result.stderr
    assert expected_usage in help_result.stdout
    assert parse_failure.returncode != 0
    assert expected_usage in parse_failure.stderr
    assert "foreign emrys package imported" not in help_result.stderr
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize(
    "command",
    (
        ("runtime", "discover"),
        ("validate", "project"),
        ("doctor",),
        ("run",),
    ),
)
def test_project_is_the_only_active_intake_spelling(
    command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result = run_command(
        [sys.executable, "-I", "-m", "emrys", *command, "--help"],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert "--project" in result.stdout
    assert "--request" not in result.stdout
    assert "--workspace" not in result.stdout


@pytest.mark.parametrize(
    ("command", "selects_analysis"),
    (
        (("doctor",), True),
        (("run",), True),
        (("runtime", "discover"), False),
        (("validate", "project"), False),
        (("resume",), False),
        (("inspect", "run"), False),
        (("report",), False),
    ),
)
def test_analysis_selection_exists_only_where_readiness_or_run_is_selected(
    command: tuple[str, ...],
    selects_analysis: bool,
    tmp_path: Path,
) -> None:
    result = run_command(
        [sys.executable, "-I", "-m", "emrys", *command, "--help"],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert ("--analysis" in result.stdout) is selects_analysis


@pytest.mark.parametrize(
    "command",
    (("doctor",), ("run",), ("resume",)),
)
def test_runtime_profile_is_project_owned_not_public_path_glue(
    command: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result = run_command(
        [sys.executable, "-I", "-m", "emrys", *command, "--help"],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert "--runtime-profile" not in result.stdout


@pytest.mark.parametrize(
    ("configuration", "expected_status"),
    (
        ("[project\n", 0),
        ('[project]\nname = "another-project"\n', 0),
        ('[project]\nname = "emrys-rna-workflow"\n', CLI_USAGE_ERROR),
    ),
)
def test_checkout_authority_ignores_nonowners_and_rejects_another_owner(
    tmp_path: Path,
    configuration: str,
    expected_status: int,
) -> None:
    checkout = tmp_path / "checkout"
    invocation_cwd = checkout / "nested"
    package = checkout / "src" / "emrys"
    invocation_cwd.mkdir(parents=True)
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (checkout / "pyproject.toml").write_text(configuration, encoding="utf-8")
    before = relative_snapshot(tmp_path)

    result = run_command(
        [sys.executable, "-I", "-m", "emrys", "--help"],
        cwd=invocation_cwd,
    )

    assert result.returncode == expected_status
    if expected_status == 0:
        assert "usage: emrys" in result.stdout
    else:
        assert "not the current checkout" in result.stderr
    assert relative_snapshot(tmp_path) == before


def test_retired_build_group_is_rejected_without_side_effects(
    tmp_path: Path,
) -> None:
    """Parser termination preserves public exits without filesystem effects."""
    program = """
import json

from emrys import __main__ as cli

try:
    cli.main(["build", "run-summary"])
except SystemExit as error:
    status = error.code
print(json.dumps({
    "status": status,
}))
"""
    result = run_command(
        [sys.executable, "-I", "-c", program],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    observed = json.loads(result.stdout.splitlines()[-1])
    assert observed == {"status": CLI_USAGE_ERROR}
    assert relative_snapshot(tmp_path) == ()


@pytest.mark.parametrize(
    "arguments",
    (
        ("--help",),
        ("init", "--help"),
        ("runtime", "--help"),
        ("report", "--help"),
        ("convert", "--help"),
        ("validate", "--help"),
    ),
)
def test_installed_emrys_command_routing_help(
    arguments: tuple[str, ...],
    tmp_path: Path,
) -> None:
    result = run_command(
        [sys.executable, "-I", "-m", "emrys", *arguments],
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
    assert "usage: emrys" in result.stdout
    assert relative_snapshot(tmp_path) == ()


@pytest.mark.parametrize(
    "entrypoint",
    sorted(REPOSITORY_PACKAGE_BOOTSTRAP_ENTRYPOINTS),
)
def test_repository_package_bootstrap_precedes_ambient_pythonpath(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    foreign_root = tmp_path / "foreign"
    foreign_package = foreign_root / "emrys"
    foreign_package.mkdir(parents=True)
    (foreign_package / "__init__.py").write_text(
        "raise RuntimeError('foreign emrys package imported')\n",
        encoding="utf-8",
    )
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(foreign_root), str(REPO_ROOT / "src"))
    )
    before = relative_snapshot(tmp_path)

    result = run_command(
        [sys.executable, str(python_entrypoint_path(entrypoint)), "--help"],
        cwd=invocation_cwd,
        env=environment,
    )

    assert result.returncode == 0, result.stderr
    assert "foreign emrys package imported" not in result.stderr
    assert relative_snapshot(tmp_path) == before


@pytest.mark.parametrize("entrypoint", sorted(DIRECT_PYTHON_ENTRYPOINTS))
def test_executable_python_help_uses_a_prepared_path_from_arbitrary_cwd(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = python_entrypoint_path(entrypoint)
    shim_dir = tmp_path / "prepared-path"
    shim_dir.mkdir()
    python_shim = shim_dir / "python3"
    python_shim.write_text(
        f'#!/bin/sh\nexec {str(Path(sys.executable))!r} "$@"\n',
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
    assert not mode_is_executable(python_entrypoint_path(entrypoint))


@pytest.mark.parametrize("entrypoint", sorted(SHELL_ENTRYPOINTS))
def test_shell_help_and_missing_arguments_are_cwd_independent_and_side_effect_free(
    entrypoint: str,
    tmp_path: Path,
) -> None:
    script = shell_entrypoint_path(entrypoint)
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
    script = shell_entrypoint_path(entrypoint)

    result = run_command([str(script), "--help"], cwd=tmp_path)

    assert mode_is_executable(script)
    assert result.returncode == 0, result.stderr
    assert "usage" in result.stdout.lower()


@pytest.mark.parametrize("entrypoint", sorted(INTERPRETER_ONLY_SHELL_DEFECTS))
def test_nonexecutable_public_shell_modes_are_characterized_defects(
    entrypoint: str,
) -> None:
    assert not mode_is_executable(shell_entrypoint_path(entrypoint))


@pytest.mark.parametrize("entrypoint", sorted(DIRECT_R_ENTRYPOINTS))
def test_direct_r_entrypoint_modes_are_explicit(entrypoint: str) -> None:
    assert mode_is_executable(r_entrypoint_path(entrypoint))


@pytest.mark.parametrize("entrypoint", sorted(RSCRIPT_ONLY_ENTRYPOINTS))
def test_rscript_only_entrypoint_modes_are_explicit(entrypoint: str) -> None:
    assert not mode_is_executable(r_entrypoint_path(entrypoint))


def test_make_target_inventory_and_applicability_decisions_are_complete() -> None:
    makefile_lines = (REPO_ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
    operations_makefile_lines = (
        (REPO_ROOT / "scripts" / "make_operations.mk")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    phony_line = next(line for line in makefile_lines if line.startswith(".PHONY:"))
    live_targets = set(phony_line.partition(":")[2].split())
    configurable_variables = {
        match.group(1)
        for line in makefile_lines
        if (match := re.match(r"^([A-Z][A-Z0-9_]*)\s*\?=", line))
    }
    operation_configurable_variables = {
        match.group(1)
        for line in operations_makefile_lines
        if (match := re.match(r"^([A-Z][A-Z0-9_]*)\s*\?=", line))
    }
    include_lines = [line for line in makefile_lines if line.startswith("include ")]

    assert live_targets == set(MAKE_TARGET_DECISIONS)
    assert configurable_variables == MAKE_CONTEXT_VARIABLES
    assert operation_configurable_variables == MAKE_OPERATION_CONTEXT_VARIABLES
    assert ".PHONY: dashboard" in operations_makefile_lines
    assert (
        "EMRYS_MAKE_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))"
        in makefile_lines
    )
    assert include_lines == [
        "include $(EMRYS_MAKE_ROOT)/scripts/make_quality.mk",
        "include $(EMRYS_MAKE_ROOT)/scripts/make_operations.mk",
    ]
    assert set(MAKE_TARGET_DECISIONS.values()) == {
        "explicit_output",
        "internal_lane",
        "local_gate",
        "operator_mutation",
        "operator_observation",
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
    assert normalized_make_expansion(
        result.stdout
    ) in accepted_make_expansion_renderings(expected_make_expansions()[target])
    assert relative_snapshot(tmp_path) == before


def test_make_validation_targets_honor_report_python_bin(
    tmp_path: Path,
) -> None:
    result = run_command(
        [
            "make",
            "-n",
            "--no-print-directory",
            "-C",
            str(REPO_ROOT),
            "REPORT_PYTHON_BIN=/sentinel/python",
            "test",
            "validate",
            "lint",
        ],
        cwd=tmp_path,
        env=canonical_make_environment(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    lines = result.stdout.splitlines()
    assert sum("/sentinel/python" in line for line in lines) == 4
    assert not any(".venv/bin/python" in line for line in lines)


def test_make_expansion_oracle_rejects_recipe_mutation(
    tmp_path: Path,
) -> None:
    source = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    original = 'test:\n\t"$(REPORT_PYTHON_BIN)" -m pytest\n'
    mutated = 'test:\n\t"$(REPORT_PYTHON_BIN)" -m pytest -q\n'
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
            f"EMRYS_MAKE_ROOT={REPO_ROOT}",
            "test",
        ],
        cwd=tmp_path,
        env=canonical_make_environment(),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert normalized_make_expansion(
        result.stdout
    ) not in accepted_make_expansion_renderings(expected_make_expansions()["test"])
