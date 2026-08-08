import csv
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = (
    ROOT
    / "tests"
    / "contract_integration"
    / "validation_rosters"
    / "validation_roster_expectations.py"
)
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "partition_bam_by_mechanical_read_orientation_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src"
    / "norad"
    / "stages"
    / "partition_BAM_by_mechanical_read_orientation"
    / "validate_step_06_orientation_outputs.py"
)
TEST_MODULE_NAME = "_norad_test_validate_step_06_orientation_outputs"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    fwd_bam = root / "S.FWD_like.bam"
    fwd_bam.write_bytes(b"BAM\x01synthetic")
    fwd_bai = root / "S.FWD_like.bam.bai"
    fwd_bai.write_bytes(b"BAI\x01synthetic")
    rev_bam = root / "S.REV_like.bam"
    rev_bam.write_bytes(b"BAM\x01synthetic")
    rev_bai = root / "S.REV_like.bam.bai"
    rev_bai.write_bytes(b"BAI\x01synthetic")
    counts = root / "S.orientation_counts.tsv"
    counts.write_text(
        "sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        "flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        "assigned_records\tunassigned_records\tassigned_fraction\n"
        "S\t10\t3\t2\t2\t1\t5\t3\t8\t2\t0.800000\n"
    )
    out = root / "out"
    out.mkdir()
    return fwd_bam, fwd_bai, rev_bam, rev_bai, counts, out / "S.validation.tsv"


def arguments(values, *extra):
    fwd_bam, fwd_bai, rev_bam, rev_bai, counts, output = values
    return [
        "--scope-id",
        "S",
        "--fwd-bam",
        str(fwd_bam),
        "--fwd-bai",
        str(fwd_bai),
        "--rev-bam",
        str(rev_bam),
        "--rev-bai",
        str(rev_bai),
        "--counts",
        str(counts),
        "--output",
        str(output),
        *extra,
    ]


def run(values, *extra, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments(values, *extra)],
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def load_validator() -> ModuleType:
    sys.modules.pop(TEST_MODULE_NAME, None)
    spec = importlib.util.spec_from_file_location(TEST_MODULE_NAME, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not exact-load validator: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[TEST_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(TEST_MODULE_NAME) is module:
            sys.modules.pop(TEST_MODULE_NAME, None)
        raise
    return module


def test_dry_run_is_side_effect_free(tmp_path):
    values = fixture(tmp_path)
    assert run(values).returncode == 0
    assert not values[-1].exists()


def test_execute_publishes_five_passes(tmp_path):
    values = fixture(tmp_path)
    result = run(values, "--execute")
    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "06")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_count_disagreement_is_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[4].write_text(
        "sample_id\tinput_records\tflag_99_records\tflag_147_records\t"
        "flag_83_records\tflag_163_records\tfwd_like_records\trev_like_records\t"
        "assigned_records\tunassigned_records\tassigned_fraction\n"
        "S\t10\t3\t2\t2\t1\t6\t3\t8\t2\t0.700000\n"
    )
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["fwd_count_arithmetic"] == "fail"
    assert status["assigned_count_arithmetic"] == "fail"


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[0].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (*values[:-1], values[-1].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[-1].parent / f".{values[-1].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"


def test_arbitrary_cwd_dry_run_execute_and_repeat_are_byte_identical(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    input_paths = values[:-1]
    before = {path: (path.read_bytes(), path.stat().st_mode) for path in input_paths}

    dry = run(values, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stderr == ""
    assert dry.stdout.endswith("Dry-run complete; no output was written.\n")
    assert not values[-1].exists()

    first = run(values, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    first_report = values[-1].read_bytes()
    assert dry.stdout.encode().startswith(first_report)
    assert_exact_check_roster(rows(values[-1]), "06")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}

    second = run(values, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert values[-1].read_bytes() == first_report
    assert {
        path: (path.read_bytes(), path.stat().st_mode) for path in input_paths
    } == before
    assert list(invocation_cwd.iterdir()) == []
    assert set(values[-1].parent.iterdir()) == {values[-1]}


@pytest.mark.parametrize(
    "input_index",
    [0, 1, 2, 3],
    ids=["fwd_bam", "fwd_bai", "rev_bam", "rev_bai"],
)
def test_invalid_container_magic_is_published_as_failed_evidence(tmp_path, input_index):
    values = fixture(tmp_path)
    values[input_index].write_bytes(b"INVALID-container-magic")

    result = run(values, "--execute")

    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "06")
    by_check = {row["check_id"]: row for row in rows(values[-1])}
    assert by_check["output_containers"]["status"] == "fail"
    assert {row["status"] for row in rows(values[-1])} == {"pass", "fail"}


@pytest.mark.parametrize(
    "input_index",
    [0, 1, 2, 3, 4],
    ids=["fwd_bam", "fwd_bai", "rev_bam", "rev_bai", "counts"],
)
def test_post_build_input_mutation_preserves_valid_predecessor(
    tmp_path, monkeypatch, capsys, input_index
):
    values = fixture(tmp_path)
    initial = run(values, "--execute")
    assert initial.returncode == 0, initial.stderr
    predecessor = values[-1].read_bytes()
    input_paths = values[:-1]
    before = {path: path.read_bytes() for path in input_paths}
    target = input_paths[input_index]
    validator = load_validator()
    real_build = validator.build

    def mutate_after_build(args):
        built = real_build(args)
        target.write_bytes(before[target] + b"post-build mutation\n")
        return built

    monkeypatch.setattr(validator, "build", mutate_after_build)
    try:
        status = validator.main(arguments(values, "--execute"))
    finally:
        if sys.modules.get(TEST_MODULE_NAME) is validator:
            sys.modules.pop(TEST_MODULE_NAME, None)

    captured = capsys.readouterr()
    assert status == 2
    assert f"Input changed after validation: {target}" in captured.err
    assert values[-1].read_bytes() == predecessor
    assert target.read_bytes() == before[target] + b"post-build mutation\n"
    assert {path: path.read_bytes() for path in input_paths if path != target} == {
        path: data for path, data in before.items() if path != target
    }
    assert set(values[-1].parent.iterdir()) == {values[-1]}
