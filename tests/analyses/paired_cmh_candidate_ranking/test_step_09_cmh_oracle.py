import builtins
import csv
import importlib
import math
import runpy
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
OWNER = ROOT / "tests/analyses/paired_cmh_candidate_ranking"
ORACLE_PATH = OWNER / "step_09_cmh_oracle.py"
CORPUS_PATH = OWNER / "step_09_cmh_oracle.tsv"
ORACLE = importlib.import_module(
    "tests.analyses.paired_cmh_candidate_ranking.step_09_cmh_oracle"
)

CORPUS_HEADER = (
    "case_id",
    "requirement_tags",
    "bh_family",
    "min_sample_dp",
    "control_dp",
    "control_ad",
    "treatment_dp",
    "treatment_ad",
    "expected_status",
    "expected_statistic",
    "expected_p_value",
    "expected_common_odds_ratio",
    "expected_bh",
)


@dataclass(frozen=True)
class Case:
    case_id: str
    requirement_tags: frozenset[str]
    bh_family: str | None
    min_sample_dp: int
    control_dp: tuple[int | None, ...]
    control_ad: tuple[int | None, ...]
    treatment_dp: tuple[int | None, ...]
    treatment_ad: tuple[int | None, ...]
    expected_status: str
    expected_statistic: float | None
    expected_p_value: float | None
    expected_common_odds_ratio: float | None
    expected_bh: float | None


def parse_counts(value: str) -> tuple[int | None, ...]:
    return tuple(None if token == "NA" else int(token) for token in value.split(","))


def parse_number(value: str) -> float | None:
    return None if value == "NA" else float(value)


def load_cases() -> tuple[Case, ...]:
    with CORPUS_PATH.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        assert tuple(reader.fieldnames or ()) == CORPUS_HEADER
        rows = list(reader)
    assert rows
    assert len({row["case_id"] for row in rows}) == len(rows)
    return tuple(
        Case(
            case_id=row["case_id"],
            requirement_tags=frozenset(row["requirement_tags"].split(";")),
            bh_family=None if row["bh_family"] == "NA" else row["bh_family"],
            min_sample_dp=int(row["min_sample_dp"]),
            control_dp=parse_counts(row["control_dp"]),
            control_ad=parse_counts(row["control_ad"]),
            treatment_dp=parse_counts(row["treatment_dp"]),
            treatment_ad=parse_counts(row["treatment_ad"]),
            expected_status=row["expected_status"],
            expected_statistic=parse_number(row["expected_statistic"]),
            expected_p_value=parse_number(row["expected_p_value"]),
            expected_common_odds_ratio=parse_number(row["expected_common_odds_ratio"]),
            expected_bh=parse_number(row["expected_bh"]),
        )
        for row in rows
    )


CASES = load_cases()


def calculate(case: Case):
    return ORACLE.characterize_candidate(
        case.control_dp,
        case.control_ad,
        case.treatment_dp,
        case.treatment_ad,
        min_sample_dp=case.min_sample_dp,
    )


def assert_number(actual: float, expected: float) -> None:
    if math.isinf(actual) or math.isinf(expected):
        assert actual == expected
    else:
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15)


def test_oracle_executes_without_production_imports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def reject_production_imports(name: str, *args, **kwargs):
        if name.startswith(("emrys", "scripts", "step_09", "step09")):
            raise AssertionError(f"independent oracle imported production code: {name}")
        return real_import(name, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "__import__", reject_production_imports)
        namespace = runpy.run_path(
            str(ORACLE_PATH), run_name="independent_oracle_probe"
        )
    assert callable(namespace["characterize_candidate"])


def test_corpus_covers_every_required_characterization_boundary() -> None:
    observed = set().union(*(case.requirement_tags for case in CASES))
    assert {
        "valid",
        "zero_cell",
        "all_zero",
        "missing",
        "low_coverage",
        "continuity_correction",
        "infinite_odds",
        "rounding",
        "multi_stratum",
        "global_bh",
        "coordinated_corruption",
    } <= observed
    assert {case.expected_status for case in CASES} == {
        ORACLE.TESTED,
        ORACLE.DEGENERATE_TABLE,
        ORACLE.MISSING_COUNTS,
        ORACLE.LOW_COVERAGE,
    }


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_count_derived_oracle_matches_independent_golden(case: Case) -> None:
    observed = calculate(case)
    assert observed.test_status == case.expected_status
    if observed.cmh is None:
        assert case.expected_statistic is None
        assert case.expected_p_value is None
        assert case.expected_common_odds_ratio is None
        return
    assert case.expected_statistic is not None
    assert case.expected_p_value is not None
    assert case.expected_common_odds_ratio is not None
    assert_number(observed.cmh.statistic, case.expected_statistic)
    assert_number(observed.cmh.p_value, case.expected_p_value)
    assert_number(
        observed.cmh.common_odds_ratio,
        case.expected_common_odds_ratio,
    )


def test_global_bh_family_matches_independent_golden() -> None:
    family = [case for case in CASES if case.bh_family == "primary"]
    observed_results = [calculate(case) for case in family]
    assert all(result.cmh is not None for result in observed_results)
    adjusted = ORACLE.benjamini_hochberg(
        [result.cmh.p_value for result in observed_results if result.cmh]
    )
    for case, observed in zip(family, adjusted, strict=True):
        assert case.expected_bh is not None
        assert_number(observed, case.expected_bh)


def test_coordinated_false_cmh_family_is_rejected() -> None:
    valid = next(case for case in CASES if case.case_id == "valid_multi")
    expected = calculate(valid)
    assert expected.cmh is not None
    ORACLE.require_reported_match(
        expected,
        test_status=ORACLE.TESTED,
        statistic=expected.cmh.statistic,
        p_value=expected.cmh.p_value,
        common_odds_ratio=expected.cmh.common_odds_ratio,
    )
    with pytest.raises(ORACLE.OracleMismatch, match="statistic mismatch"):
        ORACLE.require_reported_match(
            expected,
            test_status=ORACLE.TESTED,
            statistic=12.0,
            p_value=0.0005,
            common_odds_ratio=3.5,
        )
    all_zero = next(case for case in CASES if case.case_id == "all_zero_edited")
    with pytest.raises(ORACLE.OracleMismatch, match="test_status mismatch"):
        ORACLE.require_reported_match(
            calculate(all_zero),
            test_status=ORACLE.TESTED,
            statistic=1.0,
            p_value=0.5,
            common_odds_ratio=2.0,
        )
    family = [case for case in CASES if case.bh_family == "primary"]
    family_results = [calculate(case) for case in family]
    assert all(result.cmh is not None for result in family_results)
    p_values = [result.cmh.p_value for result in family_results if result.cmh]
    golden_adjusted = tuple(
        case.expected_bh for case in family if case.expected_bh is not None
    )
    ORACLE.require_bh_match(p_values, golden_adjusted)
    coordinated_false_bh = (0.0015, 0.0015, 1.0, 0.003)
    with pytest.raises(ORACLE.OracleMismatch, match="BH value"):
        ORACLE.require_bh_match(p_values, coordinated_false_bh)


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            ((100, 100), (1,), (100, 100), (2, 2)),
            "shared length",
        ),
        (
            ((100, 100), (None, 1), (100, 100), (2, 2)),
            "partial DP/AD",
        ),
        (
            ((100, 100), (101, 1), (100, 100), (2, 2)),
            "AD greater than DP",
        ),
    ],
)
def test_invalid_count_contracts_fail_closed(arguments, message) -> None:
    with pytest.raises(ORACLE.OracleError, match=message):
        ORACLE.characterize_candidate(*arguments, min_sample_dp=1)


def test_invalid_bh_family_fails_closed() -> None:
    with pytest.raises(ORACLE.OracleError, match="finite"):
        ORACLE.benjamini_hochberg((0.1, math.nan))
