"""
Controlled reference comparison against NumPy.

NumPy is used only here as an independent reference.
The Welford implementation itself does not call NumPy.
"""

import math
import numpy as np

from stateskol.welford_robel import (
    welford,
    welford_products,
    welford_moments,
)

TOLERANCE = 1e-10


def check(label, actual, expected):
    passed = math.isclose(
        actual, float(expected),
        rel_tol=TOLERANCE,
        abs_tol=TOLERANCE,
    )
    print(f"{label}: {'PASS' if passed else 'FAIL'}")
    print(f"  Welford = {actual}")
    print(f"  NumPy   = {expected}")
    return passed


def main():
    data = [1.5, 2.0, 4.5, 5.0, 8.0, 9.5]

    print("FORMULA I - MEAN AND VARIANCE")
    result = welford(data)
    checks = [
        check("Mean", result["mean"], np.mean(data)),
        check("Sample variance", result["sample_variance"],
              np.var(data, ddof=1)),
        check("Sample standard deviation", result["sample_std"],
              np.std(data, ddof=1)),
    ]

    print("\nFORMULA II - COVARIANCE")
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 1.0, 4.0, 3.0, 7.0]
    product_result = welford_products(x, y)
    checks.append(
        check("Corrected sum of products C2", product_result["C2"],
              np.sum((np.array(x) - np.mean(x))
                     * (np.array(y) - np.mean(y))))
    )
    checks.append(
        check("Sample covariance", product_result["sample_covariance"],
              np.cov(x, y, ddof=1)[0, 1])
    )

    print("\nFORMULA III - HIGHER-ORDER CORRECTED SUMS")
    moment_result = welford_moments(data, max_order=4)
    centered = np.array(data) - np.mean(data)
    checks.append(
        check("M3", moment_result["higher_order_sums"]["M3"],
              np.sum(centered ** 3))
    )
    checks.append(
        check("M4", moment_result["higher_order_sums"]["M4"],
              np.sum(centered ** 4))
    )

    print("\nOVERALL:", "ALL CHECKS PASSED" if all(checks)
          else "ONE OR MORE CHECKS FAILED")
    print("Tolerance:", TOLERANCE)


if __name__ == "__main__":
    main()
