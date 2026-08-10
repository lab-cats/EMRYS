from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "src/norad/libraries/executable_resolution.sh"
BASH = Path("/bin/bash")
SOURCE_LINE = (
    'source "$(dirname -- "${BASH_SOURCE[0]}")/'
    '../../libraries/executable_resolution.sh"'
)
CONSUMERS = {
    ROOT / "src/norad/stages/fasta_sidecars/step_00c_prepare_gatk_reference.sh": (
        0o755,
        3,
    ),
    ROOT / "src/norad/stages/split_n_cigar/step_05_split_n_cigar_reads.sh": (0o644, 3),
    ROOT / "src/norad/stages/partition_BAM_by_mechanical_read_orientation/"
    "step_06_split_bam_by_read_orientation.sh": (0o755, 1),
    ROOT / "src/norad/stages/generate_partitioned_cohort_mpileup_VCFs/"
    "step_07_bcftools_mpileup_by_chrom_and_strand.sh": (0o755, 1),
    ROOT / "src/norad/stages/preprocess_and_annotate_cohort_candidates/"
    "step_08_vcf_preprocessing.sh": (0o755, 1),
    ROOT / "src/norad/evidence/assemble_scientific_review_evidence_package/"
    "step_09c_scientific_validation.sh": (0o755, 0),
    ROOT / "src/norad/analyses/rank_cohort_candidates_with_paired_CMH/"
    "step_09_cmh_editing_site_calling.sh": (0o755, 1),
}


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def run_resolver(
    *,
    label: str,
    value: str,
    default_name: str,
    cwd: Path,
    path_value: str,
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
shift
resolve_executable_value "$@"
[[ "$PWD" == "$before_cwd" ]] || exit 91
[[ "$PATH" == "$before_path" ]] || exit 92
"""
    environment = dict(os.environ)
    environment["PATH"] = path_value
    return subprocess.run(
        [
            str(BASH),
            "-c",
            command,
            "executable-resolution-test",
            str(OWNER),
            label,
            value,
            default_name,
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
        label="tool",
        value=value,
        default_name=default_name,
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
        label="tool",
        value="./tool",
        default_name="ignored",
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
        label="tool",
        value="./tool-dir",
        default_name="ignored",
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
        label="tool",
        value=value,
        default_name="unused",
        cwd=tmp_path,
        path_value="",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"ERROR: {expected_error}\n"


def test_owner_is_source_only_and_neutral_when_loaded(tmp_path: Path) -> None:
    source = OWNER.read_text(encoding="utf-8")
    assert mode(OWNER) == 0o644
    assert not source.startswith("#!")
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


def test_one_owner_and_exact_five_consumer_roster() -> None:
    definitions = []
    definition = re.compile(r"^resolve_executable_value\(\) \{", re.MULTILINE)
    for path in (ROOT / "src/norad").rglob("*.sh"):
        if definition.search(path.read_text(encoding="utf-8")):
            definitions.append(path)
    assert len(definitions) == 1
    assert set(definitions) == {OWNER}

    for consumer, (expected_mode, expected_calls) in CONSUMERS.items():
        source = consumer.read_text(encoding="utf-8")
        source_index = source.index(SOURCE_LINE)

        assert source.count(SOURCE_LINE) == 1
        if "die() {" in source:
            die_start = source.index("die() {")
            die_end = source.index("\n}\n", die_start)
            assert die_end < source_index
        else:
            arg_source = 'source "$(dirname -- "${BASH_SOURCE[0]}")/../../libraries/argument_parsing.sh"'
            arg_index = source.index(arg_source)
            assert arg_index > source_index
        calls = source.count('resolve_executable_value "')
        assert calls == expected_calls
        if expected_calls:
            assert source_index < source.index('resolve_executable_value "')
        assert mode(consumer) == expected_mode

    all_sources = [
        path
        for path in (ROOT / "src/norad").rglob("*.sh")
        if SOURCE_LINE in path.read_text(encoding="utf-8")
    ]
    assert set(all_sources) == set(CONSUMERS)


@pytest.mark.parametrize("path", (OWNER, *CONSUMERS), ids=lambda path: path.name)
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
