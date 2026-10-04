"""Reference check of welford() against numpy (author: Rebika Yihenew).

Needs numpy (``pip install numpy``); numpy is used ONLY here, never in
``src/`` or ``tests/``. Run from the repository root:

    python "examples/welford_reference (Rebika Yihenew).py"

The script exits with a non-zero status if a stated tolerance is violated.

Tolerances (relative error |welford - numpy| / numpy), chosen from error theory
and confirmed by measurement:

* ORDINARY data (mean not much larger than the spread): 1e-10.
  Rounding error of a sum of n terms is bounded by about n * eps, where eps =
  2.2e-16 is the float64 machine epsilon. For n up to 1e5 that is 2.2e-11, so
  1e-10 covers the worst-case bound with margin. Measured: below 1e-15.
* STRESS data (mean 1e9, spread 1): 1e-6.
  The error of a one-pass update grows with the condition number
  kappa = |mean| / std = 1e9, i.e. about eps * kappa = 2.2e-7. 1e-6 allows
  that with margin. Measured: about 4e-8.
"""

import importlib.util
import random
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "stateskol"
    / "welford (Rebika Yihenew).py"
)
_spec = importlib.util.spec_from_file_location("welford_rebika", _MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
welford = _module.welford

RTOL_ORDINARY = 1e-10
RTOL_STRESS = 1e-6


def exact_variance(data):
    """Exact sample variance using rational arithmetic (the ground truth)."""
    fractions = [Fraction(x) for x in data]
    n = len(fractions)
    mu = sum(fractions) / n
    return float(sum((x - mu) ** 2 for x in fractions) / (n - 1))


def naive_variance(data):
    """The textbook shortcut mean(x^2) - mean(x)^2 (numerically unsafe)."""
    n = len(data)
    mean_of_squares = sum(x * x for x in data) / n
    square_of_mean = (sum(data) / n) ** 2
    return (mean_of_squares - square_of_mean) * n / (n - 1)


def rel_err(value, truth):
    return abs(value - truth) / abs(truth)


def check_ordinary():
    print(f"A. Ordinary data vs numpy.var(ddof=1), tolerance {RTOL_ORDINARY:g}")
    rng = random.Random(0)
    cases = {
        "hand example": [2, 4, 4, 4, 5, 5, 7, 9],
        "gauss(0,1), n=1000": [rng.gauss(0, 1) for _ in range(1000)],
        "gauss(50,10), n=100000": [rng.gauss(50, 10) for _ in range(100_000)],
        "uniform(-5,5), n=5000": [rng.uniform(-5, 5) for _ in range(5000)],
    }
    ok = True
    for name, data in cases.items():
        w = welford(data).variance
        ref = float(np.var(np.array(data, dtype=float), ddof=1))
        err = rel_err(w, ref)
        passed = err <= RTOL_ORDINARY
        ok &= passed
        print(f"   {name:26s} welford={w:<22.15g} numpy={ref:<22.15g} "
              f"rel.err={err:.2e} {'OK' if passed else 'FAIL'}")
    return ok


def check_stability():
    print("\nB. Numerical stability: large offset, small spread")
    print("   Data = offset + [4, 7, 13, 16]; true variance is exactly 30.")
    print(f"   {'offset':>8}  {'naive':>22}  {'welford':>22}  {'numpy':>10}")
    for offset in (0.0, 1e4, 1e6, 1e8, 1e9):
        data = [offset + x for x in (4, 7, 13, 16)]
        print(f"   {offset:8.0e}  {naive_variance(data):22.15g}  "
              f"{welford(data).variance:22.15g}  "
              f"{float(np.var(np.array(data), ddof=1)):10.6g}")
    print("   -> the naive formula loses all accuracy; Welford does not.")

    print(f"\n   Harder case: 2000 values = 1e9 + gauss(0,1), tolerance {RTOL_STRESS:g}")
    rng = random.Random(1)
    data = [1e9 + rng.gauss(0, 1) for _ in range(2000)]
    truth = exact_variance(data)
    w = welford(data).variance
    ref = float(np.var(np.array(data), ddof=1))
    naive = naive_variance(data)
    print(f"   exact (Fractions) = {truth:.15g}")
    print(f"   naive   error vs exact = {rel_err(naive, truth):.2e}")
    print(f"   welford error vs exact = {rel_err(w, truth):.2e}")
    print(f"   numpy   error vs exact = {rel_err(ref, truth):.2e}")
    err = rel_err(w, ref)
    passed = err <= RTOL_STRESS
    print(f"   welford vs numpy rel.err = {err:.2e} {'OK' if passed else 'FAIL'}")
    print("   -> Welford is far better than naive, but with mean >> spread the")
    print("      two-pass method (numpy) is still more accurate. Welford's")
    print("      advantage is that it needs ONE pass and no stored data.")
    return passed


def main():
    ok = check_ordinary()
    ok &= check_stability()
    print("\nRESULT:", "all comparisons within tolerance" if ok else "TOLERANCE VIOLATED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())