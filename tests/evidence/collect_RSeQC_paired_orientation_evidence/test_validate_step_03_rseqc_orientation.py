import csv
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
ROSTER_ORACLE = ROOT / "tests" / "contract_integration" / "validation_rosters" / "validation_roster_expectations.py"
ROSTER_SPEC = importlib.util.spec_from_file_location(
    "collect_rseqc_orientation_validation_roster_oracle",
    ROSTER_ORACLE,
)
assert ROSTER_SPEC is not None and ROSTER_SPEC.loader is not None
ROSTER_MODULE = importlib.util.module_from_spec(ROSTER_SPEC)
ROSTER_SPEC.loader.exec_module(ROSTER_MODULE)
assert_exact_check_roster = ROSTER_MODULE.assert_exact_check_roster
SCRIPT = (
    ROOT
    / "src/norad/evidence/collect_RSeQC_paired_orientation_evidence/"
    "validate_step_03_rseqc_orientation.py"
)
TEST_MODULE_NAME = "_norad_test_validate_step_03_rseqc_orientation"


def fixture(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    source = root / "S.infer_experiment.txt"
    source.write_text(
        "Fraction of reads failed to determine: 0.01\n"
        'Fraction of reads explained by "1++,1--,2+-,2-+": 0.97\n'
        'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n'
    )
    out = root / "out"; out.mkdir()
    return source, out / "S.validation.tsv"


def arguments(values, *extra):
    source, output = values
    return [
        "--scope-id", "S",
        "--infer-report", str(source),
        "--output", str(output),
        *extra,
    ]


def run(values, *extra, cwd=ROOT):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments(values, *extra)],
        cwd=cwd, text=True, capture_output=True,
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
    assert_exact_check_roster(rows(values[-1]), "03")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}


def test_invalid_fraction_and_sum_are_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[0].write_text(
        "Fraction of reads failed to determine: 0.01\n"
        'Fraction of reads explained by "1++,1--,2+-,2-+": 1.20\n'
        'Fraction of reads explained by "1+-,1-+,2++,2--": 0.02\n'
    )
    assert run(values, "--execute").returncode == 0
    status = {row["check_id"]: row["status"] for row in rows(values[-1])}
    assert status["paired_orientation_fraction_a"] == "fail"
    assert status["fraction_sum"] == "fail"


def test_nonempty_malformed_producer_output_is_published_failed_evidence(tmp_path):
    values = fixture(tmp_path)
    values[0].write_text(
        "This is PairEnd Data\n"
        "nonempty malformed orientation evidence\n"
    )

    result = run(values, "--execute")

    assert result.returncode == 0, result.stderr
    assert_exact_check_roster(rows(values[-1]), "03")
    assert {row["status"] for row in rows(values[-1])} == {"fail"}


def test_missing_input_and_wrong_output_fail_closed(tmp_path):
    values = fixture(tmp_path)
    values[0].unlink()
    assert run(values, "--execute").returncode == 2
    values = fixture(tmp_path / "second")
    bad = (values[0], values[1].parent / "wrong.tsv")
    assert run(bad, "--execute").returncode == 2


def test_foreign_lock_is_preserved(tmp_path):
    values = fixture(tmp_path)
    lock = values[-1].parent / f".{values[-1].name}.lock"
    lock.write_text("foreign\n")
    assert run(values, "--execute").returncode == 2
    assert lock.read_text() == "foreign\n"


def test_arbitrary_cwd_dry_execute_repeat_is_exact_and_residue_free(tmp_path):
    values = fixture(tmp_path / "fixture")
    invocation_cwd = tmp_path / "invocation"
    invocation_cwd.mkdir()
    input_before = (values[0].read_bytes(), values[0].stat().st_mode)

    dry = run(values, cwd=invocation_cwd)
    assert dry.returncode == 0, dry.stderr
    assert dry.stderr == ""
    assert dry.stdout.endswith("Dry-run complete; no output was written.\n")
    assert not values[-1].exists()

    first = run(values, "--execute", cwd=invocation_cwd)
    assert first.returncode == 0, first.stderr
    assert first.stderr == ""
    first_report = values[-1].read_bytes()
    assert_exact_check_roster(rows(values[-1]), "03")
    assert {row["status"] for row in rows(values[-1])} == {"pass"}

    second = run(values, "--execute", cwd=invocation_cwd)
    assert second.returncode == 0, second.stderr
    assert second.stderr == ""
    assert second.stdout == first.stdout
    assert values[-1].read_bytes() == first_report
    assert (values[0].read_bytes(), values[0].stat().st_mode) == input_before
    assert list(invocation_cwd.iterdir()) == []
    assert list(values[-1].parent.iterdir()) == [values[-1]]


def test_post_build_input_mutation_preserves_valid_predecessor(
    tmp_path, monkeypatch, capsys
):
    values = fixture(tmp_path)
    first = run(values, "--execute")
    assert first.returncode == 0, first.stderr
    predecessor = values[-1].read_bytes()
    validator = load_validator()
    real_build = validator.build

    def mutate_after_build(args):
        built = real_build(args)
        values[0].write_text("changed after validation\n")
        return built

    monkeypatch.setattr(validator, "build", mutate_after_build)
    try:
        status = validator.main(arguments(values, "--execute"))
    finally:
        if sys.modules.get(TEST_MODULE_NAME) is validator:
            sys.modules.pop(TEST_MODULE_NAME, None)

    captured = capsys.readouterr()
    assert status == 2
    assert "Input changed after validation" in captured.err
    assert values[-1].read_bytes() == predecessor
    assert list(values[-1].parent.iterdir()) == [values[-1]]
