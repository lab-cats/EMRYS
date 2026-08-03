"""Independent, test-only Step 09 CMH characterization oracle.

This module intentionally does not import NORAD production code.  It derives
the two-sided, continuity-corrected 2 x 2 x K Mantel-Haenszel result directly
from paired DP/AD counts so tests can detect coordinated corruption in
producer-shaped result fields.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence


MISSING_COUNTS = "missing_counts"
LOW_COVERAGE = "low_coverage"
DEGENERATE_TABLE = "degenerate_table"
TESTED = "tested"


class OracleError(ValueError):
    """Raised when an oracle input violates the characterization contract."""


class OracleMismatch(AssertionError):
    """Raised when reported statistics disagree with count-derived results."""


@dataclass(frozen=True)
class CmhResult:
    """A finite CMH statistic/p-value and a non-negative odds ratio."""

    statistic: float
    p_value: float
    common_odds_ratio: float


@dataclass(frozen=True)
class CandidateResult:
    """Count-derived pretest status and optional estimable CMH result."""

    test_status: str
    cmh: CmhResult | None


def _validate_count_vector(
    label: str, values: Sequence[int | None]
) -> tuple[int | None, ...]:
    result: list[int | None] = []
    for index, value in enumerate(values, start=1):
        if value is None:
            result.append(None)
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise OracleError(
                f"{label}[{index}] must be a non-negative integer or None"
            )
        result.append(value)
    return tuple(result)


def _validated_counts(
    control_dp: Sequence[int | None],
    control_ad: Sequence[int | None],
    treatment_dp: Sequence[int | None],
    treatment_ad: Sequence[int | None],
) -> tuple[tuple[int | None, ...], ...]:
    vectors = (
        _validate_count_vector("control_dp", control_dp),
        _validate_count_vector("control_ad", control_ad),
        _validate_count_vector("treatment_dp", treatment_dp),
        _validate_count_vector("treatment_ad", treatment_ad),
    )
    lengths = {len(vector) for vector in vectors}
    if len(lengths) != 1 or next(iter(lengths), 0) < 2:
        raise OracleError(
            "Paired control/treatment DP/AD vectors must have one shared "
            "length of at least two strata"
        )
    for condition, dp_values, ad_values in (
        ("control", vectors[0], vectors[1]),
        ("treatment", vectors[2], vectors[3]),
    ):
        for index, (dp, ad) in enumerate(
            zip(dp_values, ad_values, strict=True), start=1
        ):
            if (dp is None) != (ad is None):
                raise OracleError(
                    f"{condition} stratum {index} has partial DP/AD missingness"
                )
            if dp is not None and ad is not None and ad > dp:
                raise OracleError(
                    f"{condition} stratum {index} has AD greater than DP"
                )
    return vectors


def _complete_cmh(
    control_dp: Sequence[int],
    control_ad: Sequence[int],
    treatment_dp: Sequence[int],
    treatment_ad: Sequence[int],
) -> CmhResult | None:
    delta = Fraction(0)
    variance = Fraction(0)
    diagonal = Fraction(0)
    off_diagonal = Fraction(0)
    for control_depth, control_alt, treatment_depth, treatment_alt in zip(
        control_dp,
        control_ad,
        treatment_dp,
        treatment_ad,
        strict=True,
    ):
        a = treatment_alt
        b = treatment_depth - treatment_alt
        c = control_alt
        d = control_depth - control_alt
        total = a + b + c + d
        if total <= 1:
            return None
        treatment_total = a + b
        control_total = c + d
        edited_total = a + c
        unedited_total = b + d
        delta += Fraction(
            a * total - treatment_total * edited_total,
            total,
        )
        variance += Fraction(
            treatment_total
            * control_total
            * edited_total
            * unedited_total,
            total * total * (total - 1),
        )
        diagonal += Fraction(a * d, total)
        off_diagonal += Fraction(b * c, total)

    if variance <= 0 or (diagonal == 0 and off_diagonal == 0):
        return None
    correction = Fraction(1, 2) if abs(delta) >= Fraction(1, 2) else Fraction(0)
    statistic = float((abs(delta) - correction) ** 2 / variance)
    p_value = math.erfc(math.sqrt(statistic / 2))
    if off_diagonal == 0:
        odds_ratio = math.inf
    else:
        odds_ratio = float(diagonal / off_diagonal)
    if (
        not math.isfinite(statistic)
        or statistic < 0
        or not math.isfinite(p_value)
        or not 0 <= p_value <= 1
        or math.isnan(odds_ratio)
        or odds_ratio < 0
    ):
        return None
    return CmhResult(
        statistic=statistic,
        p_value=p_value,
        common_odds_ratio=odds_ratio,
    )


def characterize_candidate(
    control_dp: Sequence[int | None],
    control_ad: Sequence[int | None],
    treatment_dp: Sequence[int | None],
    treatment_ad: Sequence[int | None],
    *,
    min_sample_dp: int,
) -> CandidateResult:
    """Derive Step 09 pretest status and CMH values from paired counts."""

    if (
        isinstance(min_sample_dp, bool)
        or not isinstance(min_sample_dp, int)
        or min_sample_dp < 1
    ):
        raise OracleError("min_sample_dp must be a positive integer")
    validated = _validated_counts(
        control_dp,
        control_ad,
        treatment_dp,
        treatment_ad,
    )
    if any(value is None for vector in validated for value in vector):
        return CandidateResult(MISSING_COUNTS, None)
    complete = tuple(
        tuple(value for value in vector if value is not None)
        for vector in validated
    )
    (
        complete_control_dp,
        complete_control_ad,
        complete_treatment_dp,
        complete_treatment_ad,
    ) = complete
    if any(
        depth < min_sample_dp
        for depth in complete_control_dp + complete_treatment_dp
    ):
        return CandidateResult(LOW_COVERAGE, None)
    cmh = _complete_cmh(
        complete_control_dp,
        complete_control_ad,
        complete_treatment_dp,
        complete_treatment_ad,
    )
    if cmh is None:
        return CandidateResult(DEGENERATE_TABLE, None)
    return CandidateResult(TESTED, cmh)


def benjamini_hochberg(p_values: Sequence[float]) -> tuple[float, ...]:
    """Apply one global Benjamini-Hochberg family in input order."""

    values = tuple(float(value) for value in p_values)
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values):
        raise OracleError("BH p-values must be finite values in [0, 1]")
    count = len(values)
    if count == 0:
        return ()
    descending = sorted(
        range(count), key=lambda index: values[index], reverse=True
    )
    adjusted = [0.0] * count
    running = 1.0
    for rank, index in zip(
        range(count, 0, -1), descending, strict=True
    ):
        running = min(running, count * values[index] / rank)
        adjusted[index] = min(1.0, running)
    return tuple(adjusted)


def _numbers_match(expected: float, observed: float) -> bool:
    if math.isinf(expected) or math.isinf(observed):
        return expected == observed
    return math.isclose(
        expected,
        observed,
        rel_tol=1e-12,
        abs_tol=1e-15,
    )


def require_reported_match(
    expected: CandidateResult,
    *,
    test_status: str,
    statistic: float | None,
    p_value: float | None,
    common_odds_ratio: float | None,
) -> None:
    """Fail when producer-shaped fields disagree with the independent oracle."""

    if test_status != expected.test_status:
        raise OracleMismatch(
            f"test_status mismatch: expected {expected.test_status}, "
            f"observed {test_status}"
        )
    observed_values = (statistic, p_value, common_odds_ratio)
    if expected.cmh is None:
        if any(value is not None for value in observed_values):
            raise OracleMismatch(
                f"{test_status} result must not report CMH values"
            )
        return
    expected_values = (
        expected.cmh.statistic,
        expected.cmh.p_value,
        expected.cmh.common_odds_ratio,
    )
    labels = ("statistic", "p_value", "common_odds_ratio")
    for label, expected_value, observed_value in zip(
        labels, expected_values, observed_values, strict=True
    ):
        if observed_value is None or not _numbers_match(
            expected_value, observed_value
        ):
            raise OracleMismatch(
                f"{label} mismatch: expected {expected_value}, "
                f"observed {observed_value}"
            )


def require_bh_match(
    p_values: Sequence[float],
    reported_adjusted: Sequence[float],
) -> None:
    """Fail when a reported BH family differs from independent adjustment."""

    expected = benjamini_hochberg(p_values)
    observed = tuple(float(value) for value in reported_adjusted)
    if len(observed) != len(expected):
        raise OracleMismatch(
            f"BH family length mismatch: expected {len(expected)}, "
            f"observed {len(observed)}"
        )
    for index, (expected_value, observed_value) in enumerate(
        zip(expected, observed, strict=True), start=1
    ):
        if not _numbers_match(expected_value, observed_value):
            raise OracleMismatch(
                f"BH value {index} mismatch: expected {expected_value}, "
                f"observed {observed_value}"
            )
