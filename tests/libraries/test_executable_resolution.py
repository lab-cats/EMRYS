from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "src/norad"
OWNER = SOURCE_ROOT / "libraries/executable_resolution.sh"
BASH = Path("/bin/bash")
SOURCE_STATEMENT = re.compile(
    r'^\s*source\s+.+executable_resolution\.sh["\']?\s*$', re.MULTILINE
)
ARGUMENT_SOURCE_STATEMENT = re.compile(
    r'^\s*source\s+.+argument_parsing\.sh["\']?\s*$', re.MULTILINE
)
DIRECT_RESOLVER_CALL = re.compile(r"\bresolve_executable_value\s")
OVERRIDABLE_RESOLVER_CALL = re.compile(r"\bresolve_overridable_executable\s")
CONSUMERS = {
    "stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh": (0o755, 3, 0, 1),
    "stages/canonical_bam/step_02_sort_index_bam.sh": (0o755, 1, 0, 1),
    "evidence/canonical_bam_qc/step_02b_bam_qc.sh": (0o755, 1, 0, 1),
    "evidence/rseqc_orientation/step_03_infer_strandedness_and_orientation.sh": (
        0o644,
        1,
        0,
        1,
    ),
    "stages/duplicate_marking/step_04_mark_duplicates.sh": (0o644, 2, 0, 1),
    "stages/split_n_cigar/step_05_split_n_cigar_reads.sh": (0o644, 0, 3, 1),
    "stages/mechanical_orientation/step_06_split_bam_by_read_orientation.sh": (
        0o755,
        0,
        1,
        1,
    ),
    "stages/partitioned_cohort_mpileup/"
    "step_07_bcftools_mpileup_by_chrom_and_strand.sh": (0o755, 0, 1, 1),
    "stages/cohort_candidate_preprocessing/step_08_vcf_preprocessing.sh": (
        0o755,
        0,
        1,
        1,
    ),
    "analyses/rank_cohort_candidates_with_paired_CMH/"
    "step_09_cmh_editing_site_calling.sh": (0o755, 1, 0, 2),
    "evidence/assemble_scientific_review_evidence_package/"
    "step_09c_scientific_validation.sh": (0o755, 0, 0, 1),
    "reporting/render_run_report.sh": (0o755, 1, 0, 1),
}


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def run_resolver(
    *,
    arguments: tuple[str, ...],
    cwd: Path,
    path_value: str,
    resolver: str = "resolve_executable_value",
    environment_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = r"""
set -u
die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}
before_cwd="$PWD"
before_path="$PATH"
source "$1"
resolver="$2"
shift 2
"$resolver" "$@"
[[ "$PWD" == "$before_cwd" ]] || exit 91
[[ "$PATH" == "$before_path" ]] || exit 92
"""
    environment = dict(os.environ)
    environment["PATH"] = path_value
    environment.pop("JAVA_HOME", None)
    environment.pop("TEST_TOOL_OVERRIDE", None)
    if environment_overrides:
        environment.update(environment_overrides)
    return subprocess.run(
        [
            str(BASH),
            "-c",
            command,
            "executable-resolution-test",
            str(OWNER),
            resolver,
            *arguments,
        ],
        cwd=cwd,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def make_executable(path: Path) -> None:
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


@pytest.mark.parametrize(
    ("value", "default_name", "executable_name"),
    [
        ("", "default-tool", "default-tool"),
        ("selected-tool", "unused-default", "selected-tool"),
    ],
)
def test_empty_value_uses_default_and_basename_uses_path_verbatim(
    value: str,
    default_name: str,
    executable_name: str,
    tmp_path: Path,
) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    executable = bin_dir / executable_name
    make_executable(executable)

    result = run_resolver(
        arguments=("tool", value, default_name),
        cwd=tmp_path,
        path_value=str(bin_dir),
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{executable}\n"
    assert result.stderr == ""


def test_slash_path_is_returned_without_canonicalization(tmp_path: Path) -> None:
    executable = tmp_path / "tool"
    make_executable(executable)

    result = run_resolver(
        arguments=("tool", "./tool", "ignored"),
        cwd=tmp_path,
        path_value="",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "./tool\n"
    assert result.stderr == ""


def test_slash_path_preserves_executable_directory_acceptance(
    tmp_path: Path,
) -> None:
    executable_directory = tmp_path / "tool-dir"
    executable_directory.mkdir(mode=0o755)

    result = run_resolver(
        arguments=("tool", "./tool-dir", "ignored"),
        cwd=tmp_path,
        path_value="",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "./tool-dir\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("value", "expected_error"),
    [
        ("./missing", "tool does not exist: ./missing"),
        (
            "./not-executable",
            "tool exists but is not executable: ./not-executable",
        ),
        (
            "not-on-path",
            "tool executable was not found on PATH: not-on-path",
        ),
    ],
    ids=("missing-path", "nonexecutable-path", "missing-basename"),
)
def test_failures_keep_exact_exit_and_diagnostic(
    value: str,
    expected_error: str,
    tmp_path: Path,
) -> None:
    nonexecutable = tmp_path / "not-executable"
    nonexecutable.write_text("not executable\n", encoding="utf-8")
    nonexecutable.chmod(0o644)

    result = run_resolver(
        arguments=("tool", value, "unused"),
        cwd=tmp_path,
        path_value="",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"ERROR: {expected_error}\n"


def test_overridable_precedence_and_failure_boundaries(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    default_executable = bin_dir / "default-tool"
    explicit_executable = tmp_path / "explicit-tool"
    override_executable = tmp_path / "override-tool"
    java_home = tmp_path / "java-home"
    java_executable = java_home / "bin/java"
    for executable in (
        default_executable,
        explicit_executable,
        override_executable,
        java_executable,
    ):
        executable.parent.mkdir(parents=True, exist_ok=True)
        make_executable(executable)

    def resolve(
        value: str,
        override_value: str,
        java_home_value: str,
    ) -> subprocess.CompletedProcess[str]:
        return run_resolver(
            arguments=(
                "tool",
                value,
                "TEST_TOOL_OVERRIDE",
                "default-tool",
                "/bin/java",
            ),
            cwd=tmp_path,
            path_value=str(bin_dir),
            resolver="resolve_overridable_executable",
            environment_overrides={
                "TEST_TOOL_OVERRIDE": override_value,
                "JAVA_HOME": java_home_value,
            },
        )

    precedence_cases = (
        (
            "./explicit-tool",
            str(override_executable),
            str(java_home),
            "./explicit-tool",
        ),
        ("", str(override_executable), str(java_home), str(override_executable)),
        ("", "", str(java_home), str(java_executable)),
        ("", "", str(tmp_path / "missing-home"), str(default_executable)),
    )
    for value, override_value, java_home_value, expected in precedence_cases:
        result = resolve(value, override_value, java_home_value)

        assert result.returncode == 0, result.stderr
        assert result.stdout == f"{expected}\n"
        assert result.stderr == ""

    failure_cases = (
        ("./missing-explicit", str(override_executable), "./missing-explicit"),
        ("", "./missing-override", "./missing-override"),
    )
    for value, override_value, missing_path in failure_cases:
        result = resolve(value, override_value, str(java_home))

        assert result.returncode == 1
        assert result.stdout == ""
        assert result.stderr == f"ERROR: tool does not exist: {missing_path}\n"


def test_owner_is_source_only_and_neutral_when_loaded(tmp_path: Path) -> None:
    source = OWNER.read_text(encoding="utf-8")
    assert mode(OWNER) == 0o644
    assert not source.startswith("#!")
    assert source.count("resolve_overridable_executable() {") == 1
    assert source.count("resolve_executable_value() {") == 1
    assert "die() {" not in source
    assert "set -" not in source
    assert "trap " not in source
    assert "PATH=" not in source
    assert "cd " not in source

    command = r"""
set -u
die() { exit 1; }
before_flags="$-"
before_cwd="$PWD"
before_path="$PATH"
source "$1"
[[ "$-" == "$before_flags" ]] || exit 91
[[ "$PWD" == "$before_cwd" ]] || exit 92
[[ "$PATH" == "$before_path" ]] || exit 93
declare -F resolve_executable_value >/dev/null || exit 94
declare -F resolve_overridable_executable >/dev/null || exit 95
"""
    result = subprocess.run(
        [str(BASH), "-c", command, "owner-load-test", str(OWNER)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def test_one_owner_and_exact_consumer_roster() -> None:
    for function_name in (
        "resolve_executable_value",
        "resolve_overridable_executable",
    ):
        definition = re.compile(rf"^{function_name}\(\) \{{", re.MULTILINE)
        definitions = [
            path
            for path in (ROOT / "src/norad").rglob("*.sh")
            if definition.search(path.read_text(encoding="utf-8"))
        ]
        assert definitions == [OWNER]

    for relative_path, (
        expected_mode,
        expected_direct_calls,
        expected_overridable_calls,
        expected_source_statements,
    ) in CONSUMERS.items():
        consumer = SOURCE_ROOT / relative_path
        source = consumer.read_text(encoding="utf-8")
        source_statements = list(SOURCE_STATEMENT.finditer(source))
        argument_sources = list(ARGUMENT_SOURCE_STATEMENT.finditer(source))

        assert len(source_statements) == expected_source_statements
        assert len(argument_sources) == expected_source_statements
        direct_calls = list(DIRECT_RESOLVER_CALL.finditer(source))
        overridable_calls = list(OVERRIDABLE_RESOLVER_CALL.finditer(source))
        assert len(direct_calls) == expected_direct_calls
        assert len(overridable_calls) == expected_overridable_calls
        calls = sorted(
            (*direct_calls, *overridable_calls), key=lambda match: match.start()
        )
        if calls:
            assert (
                max(source_statements[-1].end(), argument_sources[-1].end())
                < calls[0].start()
            )
        assert mode(consumer) == expected_mode

    all_sources = [
        path
        for path in SOURCE_ROOT.rglob("*.sh")
        if SOURCE_STATEMENT.search(path.read_text(encoding="utf-8"))
    ]
    assert set(all_sources) == {SOURCE_ROOT / path for path in CONSUMERS}


@pytest.mark.parametrize(
    "path",
    (OWNER, *(SOURCE_ROOT / path for path in CONSUMERS)),
    ids=lambda path: path.name,
)
def test_owner_and_consumers_have_valid_bash_syntax(path: Path) -> None:
    result = subprocess.run(
        [str(BASH), "-n", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
