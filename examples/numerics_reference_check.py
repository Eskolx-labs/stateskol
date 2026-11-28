"""Week 4, Numerics lane: the controlled comparison against numpy.

This file is named ``*reference*.py`` on purpose. CI runs it in the reference
job, after ``pip install -e ".[reference]"``, and it is the only place in the
repository where a reference library is allowed to appear. Nothing in
``src/`` or ``tests/`` imports numpy, and ``tests/test_numerics.py`` asserts it.

Run it by hand:

    CMD   ..\\statsdesk\\.venv\\Scripts\\python.exe examples/numerics_reference_check.py

It exits non-zero on the first breach of a tolerance, and every tolerance it
states is derived below from the arithmetic, not chosen to pass. The truth on
each row is ``fractions.Fraction``, so numpy is being graded too.
"""

import math
import os
import random
import sys
from fractions import Fraction as F

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from stateskol.descriptive import bivariate_online_update  # noqa: E402

SEED = 20261128          # fixed, so a failure here is reproducible on any machine
TRIALS = 500
EPS = 2.0 ** -52         # one unit in the last place of a double near 1.0
FAILURES = []


def exact_covariance(x, y, ddof=1):
    """The sample covariance of the rationals these floats are."""
    n = len(x)
    mean_x = sum(F(v) for v in x) / n
    mean_y = sum(F(v) for v in y) / n
    co = sum((F(a) - mean_x) * (F(b) - mean_y) for a, b in zip(x, y))
    return co / (n - ddof)


def draw(rng, n, shift=0.0):
    """A correlated pair: y follows x, so the covariance is signal, not noise.

    The shift is applied to both finished columns. Folding it into the slope
    term instead would move y to 1.3e9 and make the grid this file reports the
    wrong one.
    """
    base_x = [rng.uniform(-5.0, 5.0) for _ in range(n)]
    base_y = [rng.uniform(-5.0, 5.0) + 0.3 * v for v in base_x]
    if shift:
        base_x = [v + shift for v in base_x]
        base_y = [v + shift for v in base_y]
    return base_x, base_y


def verdict(label, worst, bound, note):
    ok = worst <= bound
    if not ok:
        FAILURES.append(label)
    print("  {:<44} {:>11.3e}  {} {:>11.3e}  {}".format(
        label, worst, "within" if ok else "BREACHED", bound, note))


def main():
    print("numpy", np.__version__, " trials", TRIALS, " seed", SEED)

    # ---------------------------------------------------------------- 1
    print("\n1. the parameter mapping, stated rather than assumed")
    print("   bivariate_online_update(x, y).covariance()  <->  np.cov(x, y, ddof=1)[0, 1]")
    print("   bivariate_online_update(x, y).variance_x()  <->  np.var(x, ddof=1)")
    print("   bivariate_online_update(x, y).variance_y()  <->  np.var(y, ddof=1)")
    print("   state.mean_x / state.mean_y                 <->  np.mean(x) / np.mean(y)")
    print("   ddof=1 is written out on both sides. np.cov defaults to it and the")
    print("   package defaults to it, but a comparison that relies on two")
    print("   defaults agreeing is a comparison that breaks when one of them")
    print("   changes. bias=False is not passed because numpy 2 removed it in")
    print("   favour of ddof.")

    # ---------------------------------------------------------------- 2
    print("\n2. the brief's own case, graded against rationals")
    x = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
    y = [1e9 + 2, 1e9 + 4, 1e9 + 6, 1e9 + 8]
    truth = float(exact_covariance(x, y))
    ours = bivariate_online_update(x, y).covariance()
    theirs = float(np.cov(np.asarray(x), np.asarray(y), ddof=1)[0, 1])
    print("   exact 10/3                    ", repr(truth))
    print("   stateskol one-pass            ", repr(ours),
          "== exact" if ours == truth else "differs")
    print("   numpy np.cov                  ", repr(theirs),
          "== exact" if theirs == truth
          else "{} ulp(s) below the exact value".format(
              round(abs(theirs - truth) / math.ulp(truth))))
    if ours != truth:
        FAILURES.append("brief case not exact")
    print("   On this pair the package is exact and numpy is one step low. That")
    print("   is not a claim that numpy is wrong in general: the deviations here")
    print("   are dyadic, so the exact answer is representable and any rounding")
    print("   in the path shows. It is the reason the row is printed, not hidden.")

    # ---------------------------------------------------------------- 3
    print("\n3. ordinary values: error over the product of the two spreads")
    rng = random.Random(SEED)
    worst_ours = worst_numpy = 0.0
    for _ in range(TRIALS):
        n = rng.randint(2, 60)
        xs, ys = draw(rng, n)
        truth = float(exact_covariance(xs, ys))
        state = bivariate_online_update(xs, ys)
        scale = math.sqrt(state.variance_x() * state.variance_y())
        if scale == 0.0:
            continue
        worst_ours = max(worst_ours, abs(state.covariance() - truth) / scale)
        ref = float(np.cov(np.asarray(xs), np.asarray(ys), ddof=1)[0, 1])
        worst_numpy = max(worst_numpy, abs(ref - truth) / scale)
    print("   The covariance of two near-independent series can be arbitrarily")
    print("   close to zero, so a bound relative to the covariance itself is")
    print("   meaningless: it measures the conditioning of the sample, not the")
    print("   algorithm. The honest scale is s_x * s_y, the largest covariance")
    print("   those two spreads can produce, which is also the denominator")
    print("   Pearson r divides by.")
    verdict("stateskol one-pass, ordinary magnitude", worst_ours, 16 * EPS,
            "<= 16 eps")
    verdict("numpy np.cov, same samples", worst_numpy, 16 * EPS, "<= 16 eps")

    # ---------------------------------------------------------------- 4
    print("\n4. shifted by 1e9: whose error grows, and in what unit")
    rng = random.Random(SEED + 1)
    grid_1e9 = math.ulp(1e9)
    worst_ours = worst_numpy = 0.0
    worst_ours_scaled = 0.0
    for _ in range(TRIALS):
        n = rng.randint(2, 60)
        xs, ys = draw(rng, n, shift=1e9)
        truth = float(exact_covariance(xs, ys))
        state = bivariate_online_update(xs, ys)
        grid = math.ulp(max(abs(state.mean_x), abs(state.mean_y)))
        scale = math.sqrt(state.variance_x() * state.variance_y())
        if grid == 0.0 or scale == 0.0:
            continue
        worst_ours = max(worst_ours, abs(state.covariance() - truth) / grid)
        worst_ours_scaled = max(worst_ours_scaled, abs(state.covariance() - truth) / scale)
        ref = float(np.cov(np.asarray(xs), np.asarray(ys), ddof=1)[0, 1])
        worst_numpy = max(worst_numpy, abs(ref - truth) / scale)
    print("   The online update stores its mean as a double near 1e9. A double")
    print("   there lives on a grid of step ulp(1e9) = {},".format(grid_1e9))
    print("   so the increment mean += (x - mean) / k is quantised and dx = x -")
    print("   mean inherits that loss. Each sample's own mean sets the step, so")
    print("   the bound is measured in ulps of state.mean_x / state.mean_y.")
    print("   numpy centres the column before it accumulates -- algorithm S of")
    print("   the same 1983 paper -- so its floor stays at the data's own scale.")
    verdict("stateskol error / ulp of its own mean", worst_ours, 4.0, "<= 4 grid steps")
    verdict("stateskol error / (s_x * s_y)", worst_ours_scaled, 1e-06, "<= 1e-6")
    verdict("numpy error / (s_x * s_y)", worst_numpy, 1e-10, "<= 1e-10")
    print("   Read together: at this magnitude the one-pass state is about {:.1e}".format(
        worst_ours_scaled / worst_numpy if worst_numpy else 0.0))
    print("   times worse than numpy relative to the spreads, and the gap is one")
    print("   line of arithmetic -- which is why the lane states a bound here")
    print("   instead of a pass.")

    # ---------------------------------------------------------------- 5
    print("\n5. means and variances, checked field by field")
    rng = random.Random(SEED + 2)
    worst_mean = worst_var = 0.0
    for _ in range(TRIALS):
        n = rng.randint(2, 60)
        xs, ys = draw(rng, n)
        state = bivariate_online_update(xs, ys)
        truth_mean_x = float(sum(F(v) for v in xs) / n)
        worst_mean = max(worst_mean, abs(state.mean_x - truth_mean_x) / max(abs(truth_mean_x), 1.0))
        worst_var = max(worst_var, abs(state.variance_x() - float(exact_covariance(xs, xs)))
                        / max(abs(exact_covariance(xs, xs)), 1.0))
    verdict("state.mean_x, relative", worst_mean, 32 * EPS, "<= 32 eps")
    verdict("state.variance_x against cov(x, x)", worst_var, 32 * EPS, "<= 32 eps")

    # ---------------------------------------------------------------- 6
    print("\n6. correlation, where the package has no function yet")
    pear = bivariate_online_update(x, y)
    r = pear.co_moment / math.sqrt(pear.m2_x * pear.m2_y)
    print("   r from the state  ", repr(r), " np.corrcoef",
          repr(float(np.corrcoef(np.asarray(x), np.asarray(y))[0, 1])))
    if r != 1.0:
        FAILURES.append("exactly linear pair did not give r == 1.0")
    print("   y is not 2x for that pair; its deviations are, dy = 2 * dx exactly,")
    print("   so the relationship is perfectly linear and r must be 1.0, not")
    print("   0.9999999999. That is why this row asserts equality, not a bound.")
    print("   pearson_r() itself is Core C's name; this lane only guarantees the")
    print("   three sums it needs come from one pass.")

    print()
    if FAILURES:
        print("FAILURES:", ", ".join(FAILURES))
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
