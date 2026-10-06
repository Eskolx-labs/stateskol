"""Compare welford (Yeabsira Tesfaye) with numpy.

numpy is used ONLY in this file, as the trusted answer to compare with.
The welford function itself never uses numpy's var or std.

TOLERANCE (relative):   tol = max(1e-12, EPS * |mean| / std)
    EPS = 2.2e-16 is the float64 machine epsilon.

Why 1e-12 as the minimum:
    A float64 number is rounded by about 1e-16 on every operation.
    For normal data we measured errors around 1e-14 or smaller, so 1e-12
    leaves a safety margin of about 100 times. It is still strict: using
    n instead of n - 1 gives an error of about 1e-5 for n = 100,000.

Why the tolerance grows when the mean is big compared with the spread:
    Welford computes x - mean. If the mean is huge and the spread is small,
    that subtraction loses digits, and the mean of equation (1) is rounded
    at every step. We measured this: for normal(1e6, 1) with 100,000
    values, welford is off by 4.6e-11 from the EXACT variance (computed
    with Python fractions), while numpy is exact because it uses two
    passes. So a flat 1e-12 is too strict there, and the rule gives
    2.2e-10, about 5 times more than the error we saw.
    This rule is a rule of thumb from measurement, not a proven bound.
"""

import importlib.util
from pathlib import Path

import numpy as np

MIN_TOL = 1e-12
EPS = 2.2e-16


def load_welford():
    folder = Path(__file__).resolve().parent
    name = "welford (Yeabsira Tesfaye).py"
    for path in (folder / name, folder.parent / "src" / "stateskol" / name):
        if path.exists():
            spec = importlib.util.spec_from_file_location("welford_yt", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.welford
    raise FileNotFoundError(name)


welford = load_welford()


def compare(name, x):
    """Compare welford and numpy on the numpy array x. Return True if close."""
    mine = welford(x.tolist())
    numpy_var = np.var(x, ddof=1)
    numpy_mean = np.mean(x)

    error_var = abs(mine["variance"] - numpy_var) / numpy_var
    error_mean = abs(mine["mean"] - numpy_mean) / abs(numpy_mean)

    tol = max(MIN_TOL, EPS * abs(numpy_mean) / np.sqrt(numpy_var))
    ok = error_var <= tol

    if ok:
        word = "OK"
    else:
        word = "FAIL"
    print(f"{name:<28} n={len(x):>6}  var error={error_var:.2e}  "
          f"mean error={error_mean:.2e}  tol={tol:.1e}  {word}")
    return ok


rng = np.random.default_rng(12345)  # fixed seed, so results repeat

datasets = [
    ("hand-worked 2,4,4,4,5,5,7,9", np.array([2, 4, 4, 4, 5, 5, 7, 9], float)),
    ("normal(0, 1)", rng.normal(0, 1, 100000)),
    ("normal(100, 15)", rng.normal(100, 15, 100000)),
    ("uniform(-1000, 1000)", rng.uniform(-1000, 1000, 100000)),
    ("normal(1e6, 1) big mean", rng.normal(1e6, 1, 100000)),
    ("stability 1e9+4,7,13,16", np.array([1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16])),
]

all_ok = True
for name, x in datasets:
    if not compare(name, x):
        all_ok = False

# 2000 small random datasets: what is the worst error?
worst = 0.0
for i in range(2000):
    n = int(rng.integers(2, 500))
    x = rng.normal(rng.uniform(-100, 100), rng.uniform(0.1, 10), n)
    mine = welford(x.tolist())["variance"]
    error = abs(mine - np.var(x, ddof=1)) / np.var(x, ddof=1)
    if error > worst:
        worst = error

print()
print(f"worst error in 2000 random datasets: {worst:.2e}")
print(f"minimum tolerance: {MIN_TOL:.0e}")

assert all_ok, "one comparison failed"
assert worst < MIN_TOL, "random datasets above tolerance"
print("ALL COMPARISONS WITHIN TOLERANCE")

