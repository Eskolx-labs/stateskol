"""Compare Stateskol quantiles and IQR with NumPy reference results.

Run from the repository root with:
    python examples/reference_check.py

The local src directory is located relative to this script, so an absolute
script path also works from other working directories without PYTHONPATH.

Requires NumPy 1.22+ in the evidence environment only. Inputs are restricted to
ordinary float64-compatible datasets; arbitrary-size integers and extreme
float arithmetic remain covered by the standard-library tests, not this check.
Ross's percentile rule is in sec. 2.3.3, printed pp. 26-27 (PDF pp. 41-42);
IQR is defined on printed p. 29 (PDF p. 44). These are original test datasets.
"""

import math
import platform
import random
import sys
from pathlib import Path
from typing import NamedTuple

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stateskol.descriptive import iqr, quantile


METHOD = "averaged_inverted_cdf"
RELATIVE_TOLERANCE = 1e-12
ABSOLUTE_TOLERANCE = 1e-12
SEED = 20260927
PROBABILITIES = (0.0, 0.1, 0.25, 0.5, 0.6, 0.75, 0.9, 1.0)


class ComparisonCase(NamedTuple):
    """Raw input and independently specified retained observations."""

    name: str
    raw: list[int | float | None] | tuple[int | float | None, ...]
    retained: tuple[int | float, ...]


def comparison_cases() -> list[ComparisonCase]:
    """Build fixed and seeded datasets with independent retained observations."""
    cases = [
        ComparisonCase("hand-worked", [2, 4, 6, 8], (2, 4, 6, 8)),
        ComparisonCase("odd-length", [1, 3, 5], (1, 3, 5)),
        ComparisonCase("singleton", [5], (5,)),
        ComparisonCase("constant", [5, 5, 5, 5], (5, 5, 5, 5)),
        ComparisonCase("ties", [3, 1, 3, 1], (3, 1, 3, 1)),
        ComparisonCase("negative-zero-tuple", (-4, 0, 1, 2), (-4, 0, 1, 2)),
        ComparisonCase("fractional", [1.25, 1.75], (1.25, 1.75)),
        ComparisonCase("decimal", [-0.3, 0.1, 0.2, 0.7], (-0.3, 0.1, 0.2, 0.7)),
        ComparisonCase("skewed", [0, 0, 0, 100], (0, 0, 0, 100)),
        ComparisonCase("missing", [8, None, 2, float("nan"), 6, 4], (8, 2, 6, 4)),
        ComparisonCase("missing-singleton", [None, 5, float("nan")], (5,)),
        ComparisonCase(
            "large-offset",
            [10**12 + value for value in (2, 4, 6, 8)],
            tuple(10**12 + value for value in (2, 4, 6, 8)),
        ),
    ]
    generator = random.Random(SEED)
    for size in (1, 2, 3, 4, 5, 8, 16, 31, 64, 127):
        retained = tuple(generator.uniform(-100, 100) for _ in range(size))
        raw: list[int | float | None] = list(retained)
        raw.insert(size // 2, None)
        raw.append(float("nan"))
        cases.append(ComparisonCase(f"seeded-{size}", raw, retained))
    return cases


def compare_value(actual: int | float, expected: float) -> tuple[bool, float]:
    """Use NumPy's asymmetric allclose tolerance formula on finite scalars."""
    observed = float(actual)
    if not math.isfinite(observed) or not math.isfinite(expected):
        return False, math.inf
    error = abs(observed - expected)
    allowed_error = ABSOLUTE_TOLERANCE + RELATIVE_TOLERANCE * abs(expected)
    return error <= allowed_error, error


def main() -> int:
    """Report comparison errors and return zero only when every check passes."""
    cases = comparison_cases()
    failures: list[str] = []
    quantile_checks = 0
    iqr_checks = 0
    largest_quantile_error = 0.0
    largest_iqr_error = 0.0

    print(f"Python {platform.python_version()} | NumPy {np.__version__}")
    print(f"method={METHOD}, dtype=float64, seed={SEED}")
    print(f"rtol={RELATIVE_TOLERANCE:g}, atol={ABSOLUTE_TOLERANCE:g}")
    print("case | retained | dropped | max quantile abs error | IQR abs error | result")

    for case in cases:
        reference_data = np.asarray(case.retained, dtype=np.float64)
        expected_dropped = len(case.raw) - len(case.retained)
        reference_quantiles = np.quantile(reference_data, PROBABILITIES, method=METHOD)
        errors = []
        failures_before = len(failures)

        for probability, expected in zip(PROBABILITIES, reference_quantiles):
            result = quantile(case.raw, probability)
            matches, error = compare_value(result.value, float(expected))
            errors.append(error)
            quantile_checks += 1
            if not matches or result.dropped_count != expected_dropped:
                failures.append(
                    f"{case.name}: quantile({probability}) got {result}; "
                    f"expected value={expected!r}, dropped_count={expected_dropped}"
                )

        reference_quartiles = np.quantile(reference_data, (0.25, 0.75), method=METHOD)
        reference_iqr = float(reference_quartiles[1] - reference_quartiles[0])
        result = iqr(case.raw)
        matches, iqr_error = compare_value(result.value, reference_iqr)
        iqr_checks += 1
        if not matches or result.dropped_count != expected_dropped:
            failures.append(
                f"{case.name}: IQR got {result}; expected value={reference_iqr!r}, "
                f"dropped_count={expected_dropped}"
            )

        largest_quantile_error = max(largest_quantile_error, *errors)
        largest_iqr_error = max(largest_iqr_error, iqr_error)
        outcome = "PASS" if len(failures) == failures_before else "FAIL"
        print(
            f"{case.name} | {len(case.retained)} | {expected_dropped} | "
            f"{max(errors):.6g} | {iqr_error:.6g} | {outcome}"
        )

    print(f"\nDatasets: {len(cases)}")
    print(f"Quantile comparisons: {quantile_checks}; IQR comparisons: {iqr_checks}")
    print(f"Maximum quantile absolute error: {largest_quantile_error:.17g}")
    print(f"Maximum IQR absolute error: {largest_iqr_error:.17g}")
    print(f"Failures: {len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())