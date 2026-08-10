import subprocess
import sys
from pathlib import Path

import pytest

from tests.stage_validator_test_support import (
    load_exact_module,
    load_roster_oracle,
)
from tests.stage_validator_test_support import read_tsv as rows

ROOT = Path(__file__).resolve().parents[3]
assert_exact_check_roster = load_roster_oracle(ROOT).assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src"
    / "norad"
    / "stages"
    / "construct_FASTA_sidecars"
    / "validate_step_00c_reference_sidecars.py"
)
TEST_MODULE_NAME = "_norad_test_validate_step_00c_reference_sidecars"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    fasta = root / "genome.fa"
    fasta.write_text(">1\nACGT\n>MT\nAA\n")
    fai = root / "genome.fa.fai"
    fai.write_text("1\t4\t3\t4\t5\nMT\t2\t12\t2\t3\n")
    dictionary = root / "genome.dict"
    dictionary.write_text("@HD\tVN:1.6\n@SQ\tSN:1\tLN:4\n@SQ\tSN:MT\tLN:2\n")
    outdir = root / "out"
    outdir.mkdir()
    return fasta, fai, dictionary, outdir / "novogene_ref.validation.tsv"


def run(values, *extra, cwd=ROOT):
    fasta, fai, dictionary, output = values
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--scope-id",
            "novogene_ref",
            "--reference-fasta",
            str(fasta),
            "--reference-fai",
            str(fai),
            "--reference-dict",
            str(dictionary),
            "--output",
            str(output),
            *extra,
        ],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


@pytest.fixture
def validator_module():
    module = load_exact_module(SCRIPT, TEST_MODULE_NAME)
    try:
        yield module
    finally:
        if sys.modules.get(TEST_MODULE_NAME) is module:
            sys.modules.pop(TEST_MODULE_NAME, None)


def assert_loader_fault_is_residue_free(
    *, before_sys_path, invocation_cwd, report_path
):
    assert sys.path == before_sys_path
    assert not report_path.exists()
    assert not any(invocation_cwd.iterdir())


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[3].exists()


def test_execute_publishes_five_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[3]), "00c")
    assert {item["status"] for item in rows(values[3])} == {"pass"}


def test_sidecar_mismatch_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[1].write_text("1\t4\t3\t4\t5\nMT\t3\t12\t3\t4\n")
    assert run(values, "--execute").returncode == 0
    status = {item["check_id"]: item["status"] for item in rows(values[3])}
    assert status["fai_contig_agreement"] == "fail"


def test_malformed_sidecar_is_role_local_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[1].write_text("malformed\n")
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    by_check = {item["check_id"]: item for item in rows(values[3])}
    assert by_check["fasta_structure"]["status"] == "pass"
    assert by_check["fai_structure"]["status"] == "fail"
    assert by_check["fai_structure"]["observed"] == "FAI row 1 is malformed"
    assert by_check["dict_structure"]["status"] == "pass"
    assert by_check["fai_contig_agreement"]["status"] == "fail"
    assert by_check["dict_contig_agreement"]["status"] == "pass"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[1].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (*values[:3], values[3].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[3].parent / f".{values[3].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"


def test_non_repository_cwd_dry_execute_repeat_is_deterministic(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    input_before = tuple(path.read_bytes() for path in values[:3])

    dry = run(values, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stderr == ""
    assert not values[3].exists()

    first = run(values, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    first_bytes = values[3].read_bytes()
    first_rows = rows(values[3])

    second = run(values, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert values[3].read_bytes() == first_bytes
    assert second.stdout == first.stdout
    assert [item["check_id"] for item in first_rows] == [
        "fasta_structure",
        "fai_structure",
        "dict_structure",
        "fai_contig_agreement",
        "dict_contig_agreement",
    ]
    assert {item["status"] for item in first_rows} == {"pass"}
    assert tuple(path.read_bytes() for path in values[:3]) == input_before
    assert not any(invocation_cwd.iterdir())
    assert list(values[3].parent.iterdir()) == [values[3]]
