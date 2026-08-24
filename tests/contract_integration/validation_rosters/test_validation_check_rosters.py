"""Independent characterization of every live validation check roster."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from validation_roster_expectations import (
    EXPECTED_CHECK_ROSTERS,
    assert_exact_check_roster,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
REPORT_LIBRARY = REPO_ROOT / "src" / "emrys" / "libraries" / "validation/report.py"
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from emrys.libraries import validation as SHARED_REPORT_VALIDATOR

VALIDATOR_PATHS = {
    "00a": Path("src/emrys/stages/star_index/validator.py"),
    "00b": Path("src/emrys/stages/gtf_to_bed12/validator.py"),
    "00c": Path("src/emrys/stages/fasta_sidecars/validator.py"),
    "01": Path("src/emrys/stages/star_alignment/validator.py"),
    "02": Path("src/emrys/stages/canonical_bam/validator.py"),
    "02b": Path("src/emrys/evidence/canonical_bam_qc/validator.py"),
    "03": Path("src/emrys/evidence/rseqc_orientation/validator.py"),
    "04": Path("src/emrys/stages/duplicate_marking/validator.py"),
    "05": Path("src/emrys/stages/split_n_cigar/validator.py"),
    "06": Path("src/emrys/stages/mechanical_orientation/validator.py"),
    "07": Path("src/emrys/stages/partitioned_cohort_mpileup/validator.py"),
    "08": Path("src/emrys/stages/cohort_candidate_preprocessing/validator.py"),
    "09": Path("src/emrys/analyses/paired_cmh_candidate_ranking/validator.py"),
    "10": Path("src/emrys/analyses/scientific_context_projection/validator.py"),
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
        return (*expected, expected[0])
    if mutation == "reordered":
        return tuple(reversed(expected))
    raise AssertionError(f"Unknown test mutation: {mutation}")


def test_expectations_cover_exactly_the_live_validator_inventory() -> None:
    live_flat = {
        Path("scripts") / path.name for path in SCRIPTS_ROOT.glob("validate_step_*.py")
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
    expected = EXPECTED_CHECK_ROSTERS[step_id]
    if mutation == "reordered" and len(expected) < 2:
        pytest.skip("A one-check roster has no distinct reordered form")
    actual = mutate_roster(expected, mutation)
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
