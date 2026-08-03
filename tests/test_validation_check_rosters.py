"""Independent characterization of every live validation check roster."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from validation_roster_expectations import (
    EXPECTED_CHECK_ROSTERS,
    assert_exact_check_roster,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
REPORT_LIBRARY = REPO_ROOT / "src" / "norad" / "libraries" / "validation_report.py"
VALIDATOR_PATHS = {
    "00a": Path(
        "src/norad/stages/construct_STAR_index/validate_step_00a_star_index.py"
    ),
    "00b": Path("scripts/validate_step_00b_bed12.py"),
    "00c": Path("scripts/validate_step_00c_reference_sidecars.py"),
    "01": Path("scripts/validate_step_01_star_alignment.py"),
    "02": Path("scripts/validate_step_02_canonical_bam.py"),
    "02b": Path("scripts/validate_step_02b_bam_qc.py"),
    "03": Path("scripts/validate_step_03_rseqc_orientation.py"),
    "04": Path("scripts/validate_step_04_mark_duplicates.py"),
    "05": Path("scripts/validate_step_05_split_ncigar.py"),
    "06": Path("scripts/validate_step_06_orientation_outputs.py"),
    "07": Path("scripts/validate_step_07_mpileup_outputs.py"),
    "08": Path("scripts/validate_step_08_preprocessing_outputs.py"),
    "09": Path("scripts/validate_step_09_cmh_outputs.py"),
}
VALIDATION_HEADER = (
    "step_id",
    "scope_id",
    "check_id",
    "status",
    "observed",
    "expected",
    "detail",
)


def load_shared_report_validator() -> ModuleType:
    path = REPORT_LIBRARY
    spec = importlib.util.spec_from_file_location("shared_report_validator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load shared report validator: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SHARED_REPORT_VALIDATOR = load_shared_report_validator()


def validation_report_bytes(step_id: str, check_ids: tuple[str, ...]) -> bytes:
    lines = ["\t".join(VALIDATION_HEADER)]
    lines.extend(
        "\t".join(
            (
                step_id,
                "scope",
                check_id,
                "pass",
                "observed",
                "expected",
                "detail",
            )
        )
        for check_id in check_ids
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def mutate_roster(expected: tuple[str, ...], mutation: str) -> tuple[str, ...]:
    if mutation == "missing":
        return expected[:-1]
    if mutation == "extra":
        return (*expected, "unexpected_check")
    if mutation == "duplicate":
        return (*expected[:-1], expected[0])
    if mutation == "reordered":
        return tuple(reversed(expected))
    raise AssertionError(f"Unknown test mutation: {mutation}")


def test_expectations_cover_exactly_the_live_validator_inventory() -> None:
    live_flat = {
        Path("scripts") / path.name
        for path in SCRIPTS_ROOT.glob("validate_step_*.py")
    }
    expected_flat = {
        path for path in VALIDATOR_PATHS.values() if path.parent == Path("scripts")
    }

    assert set(EXPECTED_CHECK_ROSTERS) == set(VALIDATOR_PATHS)
    assert live_flat == expected_flat
    assert all((REPO_ROOT / path).is_file() for path in VALIDATOR_PATHS.values())
    assert len(set(VALIDATOR_PATHS.values())) == len(VALIDATOR_PATHS)


@pytest.mark.parametrize("step_id", sorted(EXPECTED_CHECK_ROSTERS))
@pytest.mark.parametrize(
    "mutation",
    ("missing", "extra", "duplicate", "reordered"),
)
def test_independent_exact_roster_oracle_rejects_each_mutation(
    step_id: str,
    mutation: str,
) -> None:
    actual = mutate_roster(EXPECTED_CHECK_ROSTERS[step_id], mutation)
    rows = [{"check_id": check_id} for check_id in actual]

    with pytest.raises(AssertionError, match=f"Step {step_id}"):
        assert_exact_check_roster(rows, step_id)


@pytest.mark.parametrize("step_id", sorted(EXPECTED_CHECK_ROSTERS))
@pytest.mark.parametrize("mutation", ("missing", "extra", "duplicate"))
def test_shared_report_validator_rejects_set_membership_mutations(
    step_id: str,
    mutation: str,
) -> None:
    expected = EXPECTED_CHECK_ROSTERS[step_id]
    data = validation_report_bytes(step_id, mutate_roster(expected, mutation))

    with pytest.raises(SHARED_REPORT_VALIDATOR.ValidationError):
        SHARED_REPORT_VALIDATOR.validate_report(
            data,
            "scope",
            step_id=step_id,
            check_ids=set(expected),
        )


@pytest.mark.parametrize("step_id", sorted(EXPECTED_CHECK_ROSTERS))
def test_shared_report_validator_accepts_reordering_as_characterized_defect(
    step_id: str,
) -> None:
    expected = EXPECTED_CHECK_ROSTERS[step_id]
    reordered = mutate_roster(expected, "reordered")

    SHARED_REPORT_VALIDATOR.validate_report(
        validation_report_bytes(step_id, reordered),
        "scope",
        step_id=step_id,
        check_ids=set(expected),
    )
