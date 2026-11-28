"""Week 4, Numerics lane: the cancellation benchmark, with no imports but the package.

Standard library only. Run it in a clean environment:

    python examples/numerics_demo.py

It prints, side by side, the three ways to compute a sample covariance on data
whose magnitude swamps its variation, and it states the accuracy each one
actually delivers. Every "expected" column below is computed from
fractions.Fraction inside this file, so the truth is exact rationals rather
than a number copied out of a library.

It exits non-zero if any claim it prints fails to hold.
"""

import math
import os
import sys
from fractions import Fraction as F

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from stateskol.descriptive import (  # noqa: E402
    BivariateState,
    DimensionMismatchError,
    as_numeric,
    bivariate_online_update,
)
from stateskol.errors import ContractError, DomainError, EmptyDataError  # noqa: E402

NAN = float("nan")
FAILURES = []


def check(label, got, want, bound=None):
    """Print one row and record a breach. bound is an absolute tolerance."""
    if bound is None:
        ok = got == want
    else:
        ok = abs(got - want) <= bound
    if not ok:
        FAILURES.append(label)
    print("  {:<38} {:<22} {} {}".format(
        label, repr(got), "expected" if ok else "FAILED", repr(want)))


def check_bound(label, got, bound):
    """Print one row whose claim is an inequality, so the row cannot be misread."""
    ok = got <= bound
    if not ok:
        FAILURES.append(label)
    print("  {:<38} {:<22} {} {}".format(
        label, repr(got), "within bound" if ok else "FAILED", "<= " + repr(bound)))


def exact_covariance(x, y, ddof=1):
    """The truth, in rationals: no rounding anywhere."""
    n = len(x)
    mean_x = sum(F(v) for v in x) / n
    mean_y = sum(F(v) for v in y) / n
    co = sum((F(a) - mean_x) * (F(b) - mean_y) for a, b in zip(x, y))
    return co / (n - ddof)


def naive_covariance(x, y):
    """(sum(xy) - sum(x)sum(y)/n) / (n - 1): the formula the brief tells us not to ship."""
    n = len(x)
    return (sum(a * b for a, b in zip(x, y)) - sum(x) * sum(y) / n) / (n - 1)


def two_pass_covariance(x, y):
    """Centre once, then accumulate. Two passes over the data."""
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    return math.fsum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / (n - 1)


def main():
    # ---------------------------------------------------------------- 1
    print("1. the brief's 1e9 pair: three algorithms, one exact answer")
    x = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
    y = [1e9 + 2, 1e9 + 4, 1e9 + 6, 1e9 + 8]
    truth = exact_covariance(x, y)
    print("   x =", x)
    print("   y =", y)
    print("   exact C = 10, so the sample covariance is 10/3 =", F(10, 3))
    check("naive formula, which must be zero", naive_covariance(x, y), 0.0)
    check("two-pass sum", two_pass_covariance(x, y), float(truth), bound=0.0)
    check("one-pass Chan-Golub-LeVeque", bivariate_online_update(x, y).covariance(),
          float(truth), bound=0.0)
    print("   The naive row returning 0.0 is the point of the lane. On this data")
    print("   it is not inaccurate, it is blind: it reports no spread at all for")
    print("   data that has some. The exact answer is 10/3 =", float(truth))

    # ---------------------------------------------------------------- 2
    print("\n2. why the naive formula dies: the accumulator has no room for the answer")
    total = sum(a * b for a, b in zip(x, y))
    print("  {:<38} {:<22}".format("sum(x * y)", repr(total)))
    print("  {:<38} {:<22} {:>6.0f}x the answer".format(
        "one double step at that magnitude", repr(math.ulp(total)),
        math.ulp(total) / float(truth)))
    print("  The covariance is 3.33; the addition it is hiding inside resolves")
    print("  to 512. The digits are gone before the subtraction runs.")

    # ---------------------------------------------------------------- 3
    print("\n3. the hand-worked state, one row per pair")
    print("   k  mean_x              mean_y              m2_x  m2_y   C")
    state = BivariateState()
    table = [(1, 1e9 + 1, 1e9 + 2, 0.0, 0.0, 0.0),
             (2, 1e9 + 1.5, 1e9 + 3.0, 0.5, 2.0, 1.0),
             (3, 1e9 + 2.0, 1e9 + 4.0, 2.0, 8.0, 4.0),
             (4, 1e9 + 2.5, 1e9 + 5.0, 5.0, 20.0, 10.0)]
    for k, mx, my, m2x, m2y, co in table:
        state.add(x[k - 1], y[k - 1])
        ok = (state.mean_x == mx and state.mean_y == my
              and state.m2_x == m2x and state.m2_y == m2y
              and state.co_moment == co)
        if not ok:
            FAILURES.append("step table k={}".format(k))
        print("   {}  {:<18} {:<18} {:<5} {:<6} {}{}".format(
            k, repr(state.mean_x), repr(state.mean_y), repr(state.m2_x),
            repr(state.m2_y), repr(state.co_moment), "" if ok else "  <-- FAILED"))
    print("   Every value is a dyadic rational, so each step is exact. That is")
    print("   why the brief's case passes for any sane algorithm -- and why it")
    print("   proves less than it looks like it does. Section 4 is the harder")
    print("   case: same magnitude, ordinary values, no dyadic luck.")

    # ---------------------------------------------------------------- 4
    print("\n4. the same magnitude with ordinary values: the online update loses ground")
    xs = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]
    ys = [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5]
    shift = 1e9
    sx = [v + shift for v in xs]
    sy = [v + shift for v in ys]
    truth_small = exact_covariance(xs, ys)
    truth_shift = exact_covariance(sx, sy)
    print("   shifting both columns changes nothing about the answer:")
    print("     exact covariance unshifted", float(truth_small))
    print("     exact covariance shifted  ", float(truth_shift))
    st = bivariate_online_update(sx, sy)
    err = abs(st.covariance() - float(truth_shift))
    grid = math.ulp(max(abs(st.mean_x), abs(st.mean_y)))
    scale = math.sqrt(st.variance_x() * st.variance_y())
    def row(label, value, error):
        print("     {:<9} {:<22} absolute error {:>10.3e}".format(label, repr(value), error))

    row("naive", naive_covariance(sx, sy), abs(naive_covariance(sx, sy) - float(truth_shift)))
    row("two-pass", two_pass_covariance(sx, sy),
        abs(two_pass_covariance(sx, sy) - float(truth_shift)))
    row("one-pass", st.covariance(), err)
    print("   The cause is not the co-moment. It is where the mean lives: a double")
    print("   near 1e9 sits on a grid of step {!r}, so the".format(grid))
    print("   increment mean += dx / k is smaller than that grid, it is quantised,")
    print("   and dx inherits the loss. The bound below is stated in that unit, not")
    print("   in ulps of the covariance, which would flatter the algorithm.")
    check_bound("shifted error vs 4 ulps of its own mean", err, 4 * grid)
    check_bound("shifted error vs the product of the spreads", err / scale, 1e-06)
    print("   numpy centres before it accumulates, so it does not pay this. The")
    print("   reference check prints the comparison; this lane states the bound")
    print("   rather than pretending the one-pass update is free.")

    # ---------------------------------------------------------------- 5
    print("\n5. paired missingness: a gap drops the pair, never one column")
    gap_x = [1, None, 3]
    gap_y = [10, 20, 30]
    paired = bivariate_online_update(gap_x, gap_y)
    print("  {:<38} {} complete, {} dropped".format(
        "bivariate_online_update([1, None, 3], [10, 20, 30])",
        paired.n, paired.dropped_pairs))
    check("complete-case covariance", paired.covariance(), 20.0)
    wrong = bivariate_online_update(as_numeric(gap_x), as_numeric(gap_y)[:2])
    check("columns dropped separately would say", wrong.covariance(), 10.0)
    print("   Independent column dropping pairs 3 with 20 instead of 30. It")
    print("   returns a clean number for a sample nobody measured.")

    # ---------------------------------------------------------------- 6
    print("\n6. refusals, one row per rule")
    try:
        bivariate_online_update([1, 2, 3], [1, 2])
        FAILURES.append("length mismatch")
    except DimensionMismatchError as exc:
        print("  {:<38} refused -> len_x={}, len_y={}".format(
            "x longer than y", exc.len_x, exc.len_y))
    try:
        bivariate_online_update([1, 2], ["3", 4])
        FAILURES.append("string in y")
    except ContractError as exc:
        print("  {:<38} refused -> {}".format("a str in y", str(exc)[:58]))
    try:
        BivariateState().add(1.0, None)
        FAILURES.append("missing pair in add")
    except ContractError as exc:
        print("  {:<38} refused -> {}".format("add() given a missing pair",
                                              str(exc)[:58]))
    try:
        bivariate_online_update([1e9 + 4], [1e9 + 6]).covariance()
        FAILURES.append("one pair ddof=1")
    except EmptyDataError as exc:
        print("  {:<38} refused -> {}".format("one pair under ddof=1", str(exc)[:58]))
    try:
        bivariate_online_update(x, y).covariance(ddof=2)
        FAILURES.append("ddof=2")
    except DomainError as exc:
        print("  {:<38} refused -> {}".format("covariance(ddof=2)", str(exc)[:58]))
    empty = bivariate_online_update([], [])
    print("  {:<38} n={} dropped={} -- the count is a finding, so the".format(
        "no pairs at all", empty.n, empty.dropped_pairs))
    print("   state is returned; asking it for a number raises EmptyDataError.")

    # ---------------------------------------------------------------- 7
    print("\n7. one pass per series")
    drained = []

    def series(name, values):
        for v in values:
            drained.append(name)
            yield v

    got = bivariate_online_update(series("x", x), series("y", y))
    counts = (drained.count("x"), drained.count("y"))
    print("  x read {} values, y read {} values, n={}".format(
        counts[0], counts[1], got.n))
    check("each series read once", counts, (len(x), len(y)))

    print()
    if FAILURES:
        print("FAILURES:", ", ".join(FAILURES))
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
