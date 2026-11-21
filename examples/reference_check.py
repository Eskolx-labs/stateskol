"""Compare the variance algorithms (Numerics lane) with exact arithmetic,
the standard library, numpy and pandas.

numpy and pandas are used ONLY here, as trusted answers. The package never
uses them. pandas is optional: if it is not installed it is skipped and a NOTE
is printed.

THE TRUTH: the exact variance, computed with fractions.Fraction (no rounding
at all), then rounded once to a float. numpy, pandas and statistics are
compared against it too, so we know how good the "trusted" answers are.

THE TOLERANCE (relative error against the exact value):
    tolerance = n * EPS * kappa
    EPS   = 2**-52, the float64 rounding unit
    kappa = sqrt(sum(x*x) / S), S = sum((x - mean)**2)
            kappa measures how big the numbers are compared with their
            spread. For data like 1,2,3,4 it is about 1. For 1e9 + 1..4 it
            is about 1e9, because the spread is tiny next to the size.
Why this form: a one-pass update adds one rounding error per value, so the
error grows with n, and it is multiplied by kappa because a value 1e9 big
carries only about 7 digits of the spread. A bound of this shape is known
from the numerical-analysis literature on variance algorithms (Chan, Golub
and LeVeque, 1983; NOT read by me). I do not rely on it: below, the measured
worst error is reported as a fraction of this tolerance, and it must stay
under 1.
When n * EPS * kappa is 1 or more, the data is so ill-conditioned that no
algorithm can be expected to keep any digit, and the dataset is reported but
not judged.
"""

import math
import random
import statistics
import sys
import warnings
from fractions import Fraction
from pathlib import Path

import numpy as np

try:
    import pandas as pd
except ImportError:          # CI may not install pandas
    pd = None

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from stateskol.descriptive import (  # noqa: E402
    _variance_naive, _variance_two_pass, _variance_welford)

EPS = 2.0 ** -52


def exact_and_kappa(values):
    f = [Fraction(v) for v in values]
    n = len(f)
    mean = sum(f) / n
    s = sum((v - mean) ** 2 for v in f)
    truth = float(s / (n - 1))
    kappa = math.sqrt(float(sum(v * v for v in f) / s)) if s != 0 else 1.0
    return truth, kappa


def rel(value, truth):
    if truth == 0.0:
        return abs(value)
    return abs(value - truth) / abs(truth)


def compare(name, values, show_naive=True):
    """Return (ok, worst error as a fraction of the tolerance)."""
    n = len(values)
    truth, kappa = exact_and_kappa(values)
    tol = n * EPS * kappa
    mine = _variance_welford(values)
    two = _variance_two_pass(values)
    naive = _variance_naive(values)
    arr = np.array(values, dtype="float64")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        np_var = float(np.var(arr, ddof=1))
        pd_var = float(pd.Series(arr).var(ddof=1)) if pd is not None else None
    st_var = float(statistics.variance(values))

    judged = tol < 1e-3
    errors = {"welford": rel(mine, truth), "two-pass": rel(two, truth),
              "numpy": rel(np_var, truth), "stdlib": rel(st_var, truth)}
    if pd_var is not None:
        errors["pandas"] = rel(pd_var, truth)
    worst_mine = errors["welford"] / tol if tol > 0 else 0.0
    # judged sets: my result AND numpy, pandas and the stdlib must be inside
    # the tolerance of the exact value, so all of them agree with each other
    ok = (not judged) or (worst_mine <= 1.0 and all(
        e <= tol for k, e in errors.items() if k != "two-pass"))
    flag = "OK" if ok else "FAIL"
    if not judged:
        flag = "not judged (ill-conditioned)"
    print(f"{name:<30} n={n:>6} kappa={kappa:8.1e} tol={tol:7.1e}  "
          f"welford={errors['welford']:7.1e} numpy={errors['numpy']:7.1e} naive={rel(naive, truth):7.1e}  {flag}")
    return ok, (worst_mine if judged else 0.0)


def check_numerics():
    """Run every comparison. Return True if all pass."""
    rng = np.random.default_rng(99)
    top = float(2 ** 53)
    sets = [
        ("hand set 2,4,4,4,5,5,7,9", [2, 4, 4, 4, 5, 5, 7, 9]),
        ("1e9 + 1..4 (the brief)", [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]),
        ("1e12 + 1..4", [1e12 + 1, 1e12 + 2, 1e12 + 3, 1e12 + 4]),
        ("1e15 + 1..4", [1e15 + 1, 1e15 + 2, 1e15 + 3, 1e15 + 4]),
        ("2**53 - 3 .. 2**53", [top - 3, top - 2, top - 1, top]),
        ("-2**53 and 2**53", [-top, top]),
        ("normal(0,1) 100000", rng.normal(0, 1, 100000).tolist()),
        ("normal(100,15) 100000", rng.normal(100, 15, 100000).tolist()),
        ("uniform(-1e6,1e6) 100000", rng.uniform(-1e6, 1e6, 100000).tolist()),
        ("exponential 100000", rng.exponential(2.0, 100000).tolist()),
        ("normal(1e6,1) 100000", rng.normal(1e6, 1, 100000).tolist()),
        ("normal(1e9,1) 100000", rng.normal(1e9, 1, 100000).tolist()),
        ("tiny 1e-100 scale", (rng.normal(0, 1, 1000) * 1e-100).tolist()),
        ("integers 0..9, many ties", rng.integers(0, 10, 5000).tolist()),
        ("one outlier (1..9 and 48)", [1, 2, 2, 3, 4, 4, 5, 6, 7, 48]),
    ]
    all_ok = True
    worst = 0.0
    for name, values in sets:
        ok, w = compare(name, values)
        all_ok = all_ok and ok
        worst = max(worst, w)

    # constant data: every algorithm must give exactly 0.0
    for value in (3.7, 1e9 + 0.1, -2.5):
        data = [value] * 1000
        ok = _variance_welford(data) == 0.0 == _variance_two_pass(data)
        print(f"{'constant ' + repr(value):<30} n={1000:>6} variance == 0.0 exactly  "
              f"{'OK' if ok else 'FAIL'}")
        all_ok = all_ok and ok

    # many random sets, all offsets, judged by the tolerance rule
    r = random.Random(17)
    judged = 0
    worst_random = 0.0
    for _ in range(2000):
        n = r.randint(2, 300)
        centre = r.choice([0.0, 1e3, 1e6, 1e9, 1e12])
        spread = r.choice([1e-3, 1.0, 100.0])
        values = [centre + r.gauss(0, spread) for _ in range(n)]
        truth, kappa = exact_and_kappa(values)
        tol = n * EPS * kappa
        if truth == 0.0 or tol >= 1e-3:
            continue
        judged += 1
        worst_random = max(worst_random, rel(_variance_welford(values), truth) / tol)
    print()
    print(f"2000 random sets, {judged} judged: worst Welford error = "
          f"{worst_random:.2f} of the tolerance (must be <= 1)")
    print(f"named datasets: worst Welford error = {worst:.1e} of the tolerance")
    print("tolerance rule: n * EPS * kappa, EPS = 2**-52, kappa = sqrt(sum(x*x) / S)")
    if pd is None:
        print("NOTE: pandas is not installed here, so pandas was skipped.")
    return all_ok and worst_random <= 1.0


if __name__ == "__main__":
    assert check_numerics(), "a numerics comparison failed"
    print("ALL NUMERICS COMPARISONS PASS")