"""Compare welford() with numpy.

numpy is only used here as an outside reference, never in the package.
Run from the repository root:

    python "examples/welford_reference (Hanna Desalegn).py"

The script exits with status 1 if a tolerance is not met.

How the tolerances were chosen
Normal data: tolerance 1e-10.
    float64 keeps about 16 significant digits, and the measured errors on
    normal data are around 1e-15 to 1e-14. A real bug is much bigger:
    dividing by n instead of n - 1 changes the variance by about 1/n,
    which is 1e-5 even for 100000 values, far above 1e-10.

Hard data (values near 1e9, spread about 1): tolerance 1e-6.
    Near 1e9 a float64 can only store steps of about 1.2e-7
    (math.ulp(1e9)). The running mean sits near 1e9, so every deviation
    d = x - m carries an error of about 1e-7 compared to a spread of 1.
    The measured error is about 3e-8, as expected, and 1e-6
    leaves a safe margin above it. A tolerance like 1e-12 would wrongly
    fail a correct implementation. The mean keeps the 1e-10 tolerance,
    because its relative error stays tiny even here.

numpy's var reads the data twice (mean first, then deviations), so on the
hard data it is closer to the exact answer than a one-pass method can be.
The exact answer is computed with fractions.Fraction, which never rounds.
"""

import random
import sys
from fractions import Fraction
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "stateskol"
    / "welford (Hanna Desalegn).py"
)
SPEC = spec_from_file_location("welford_hanna", MODULE_PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
welford = MODULE.welford

NORMAL_TOL = 1e-10
HARD_TOL = 1e-6


def relative_error(value, reference):
    return abs(value - reference) / abs(reference)


def exact_variance(data):
    # two-pass variance with fractions, no rounding at all
    values = [Fraction(x) for x in data]
    mean = sum(values) / len(values)
    return float(sum((x - mean) ** 2 for x in values) / (len(values) - 1))


def naive_variance(data):
    # textbook shortcut: (sum of squares - (sum)^2 / n) / (n - 1)
    n = len(data)
    return (sum(x * x for x in data) - sum(data) ** 2 / n) / (n - 1)


def check_against_numpy(name, data, var_tol):
    # compare mean, variance and std with numpy, return True if all pass
    result = welford(data)
    values = np.asarray(data, dtype=float)
    np_mean = float(np.mean(values))
    np_var = float(np.var(values, ddof=1))
    np_std = float(np.std(values, ddof=1))

    mean_err = relative_error(result.mean, np_mean)
    var_err = relative_error(result.variance, np_var)
    std_err = relative_error(result.std, np_std)
    passed = mean_err <= NORMAL_TOL and var_err <= var_tol and std_err <= var_tol

    print(f"  {name}")
    print(f"    n={result.count}  welford variance={result.variance!r}  numpy variance={np_var!r}")
    print(
        f"    relative error: mean {mean_err:.1e}, variance {var_err:.1e}, "
        f"std {std_err:.1e}  (tolerance {var_tol:g})  {'pass' if passed else 'FAIL'}"
    )
    return passed


def main():
    rng = random.Random(0)
    all_passed = True

    print(f"1. Normal data, tolerance {NORMAL_TOL:g}")
    normal_cases = [
        ("hand-worked [2, 4, 6, 8]", [2, 4, 6, 8]),
        ("hand-worked [3, 7, 8, 10]", [3, 7, 8, 10]),
        ("1000 values from gauss(0, 1)", [rng.gauss(0, 1) for _ in range(1000)]),
        ("100000 values from gauss(50, 10)", [rng.gauss(50, 10) for _ in range(100_000)]),
        ("5000 values from uniform(-5, 5)", [rng.uniform(-5, 5) for _ in range(5000)]),
        ("5000 values from exponential(1)", [rng.expovariate(1) for _ in range(5000)]),
    ]
    for name, data in normal_cases:
        all_passed &= check_against_numpy(name, data, NORMAL_TOL)

    print("\n2. Large offset: offset + [4, 7, 13, 16], true variance is 30")
    print(f"  {'offset':>8}  {'naive':>20}  {'welford':>20}  {'numpy':>10}")
    for offset in (0.0, 1e4, 1e6, 1e8, 1e9):
        data = [offset + v for v in (4, 7, 13, 16)]
        print(
            f"  {offset:8.0e}  {naive_variance(data):20.15g}  "
            f"{welford(data).variance:20.15g}  "
            f"{float(np.var(data, ddof=1)):10.6g}"
        )
    print("  The naive formula drops to 0.0 at 1e9, welford stays at 30.")

    print(f"\n3. Hard data: 2000 values of 1e9 + gauss(0, 1), tolerance {HARD_TOL:g}")
    hard_rng = random.Random(1)
    data = [1e9 + hard_rng.gauss(0, 1) for _ in range(2000)]
    exact = exact_variance(data)
    print(f"  exact variance (fractions): {exact:.15g}")
    print(f"  naive   error vs exact: {relative_error(naive_variance(data), exact):.2e}")
    print(f"  welford error vs exact: {relative_error(welford(data).variance, exact):.2e}")
    print(f"  numpy   error vs exact: {relative_error(float(np.var(data, ddof=1)), exact):.2e}")
    all_passed &= check_against_numpy("1e9 + gauss(0, 1)", data, HARD_TOL)
    print("  The naive formula is useless here. Welford keeps about 8 digits in")
    print("  one pass. numpy keeps more because it reads the data twice.")

    print("\nResult:", "every check passed" if all_passed else "A TOLERANCE WAS NOT MET")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())