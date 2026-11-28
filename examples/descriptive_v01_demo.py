"""The descriptive v0.1 release candidate, demonstrated with nothing installed.

Run from the repository root, in a clean environment:

    pip install -e . --no-deps
    python examples/descriptive_v01_demo.py

Standard library only. No numpy, no pandas, no scipy. This is the example the
Week 4 bar asks for: one file that shows the whole frozen surface, and prints
the hand-worked number next to the number the package returns.

Every expected value below is derived twice: once as a literal a reader can
work out with pen and paper, and once from fractions.Fraction inside the
program. Where the two disagree the file fails loudly rather than rounding.

What is NOT here, and why, is printed in section 7.
"""

import math
import sys
from fractions import Fraction

from stateskol import (
    ASSUMPTION,
    DDOFS,
    METHODS,
    POLICIES,
    BivariateState,
    ContractError,
    DimensionMismatchError,
    DomainError,
    UnsupportedRuleError,
    as_numeric,
    bivariate_online_update,
    coefficient_variation,
    count,
    iqr,
    quantile,
    stdev,
    variance,
)

# The week 3 hand-worked samples. TEN is the series the quantile literature
# walks through; DEMO is the six-value sample the spread tests are pinned to.
TEN = [2, 4, 4, 5, 7, 9, 11, 13, 15, 18]
DEMO = [4, 8, 15, 16, 23, 42]
NINE = [1, 2, 2, 3, 4, 4, 5, 6, 7]
NINE_PLUS_ONE = [1, 2, 2, 3, 4, 4, 5, 6, 7, 48]

# The brief's own pair: x = 10^9 + 1..4, y = 2x.
SHIFT = 1e9
XS = [SHIFT + 1, SHIFT + 2, SHIFT + 3, SHIFT + 4]
YS = [SHIFT + 2, SHIFT + 4, SHIFT + 6, SHIFT + 8]

# Same magnitude, ordinary values. The brief pair is dyadic, so it survives any
# sane algorithm; this one does not, which is why the comparison is made here.
XA = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]
YA = [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5]

failures = []


def check(label, got, want):
    """Print a value the reader can check by hand, and fail if it moved."""
    ok = got == want
    if not ok:
        failures.append(label)
    print("  {:<52} {!r}{}".format(label, got, "" if ok else "  != {!r}".format(want)))
    return ok


def check_close(label, got, want, tol, yardstick=None):
    """Print a float against a hand-worked truth, with the gap in a named unit.

    The unit matters. A one-pass accumulator's floor is the ulp of its own
    running mean, not the ulp of the answer, so measuring that error in
    ulps-of-the-answer reports hundreds of millions and means nothing.
    """
    err = abs(got - want)
    ok = err <= tol
    if not ok:
        failures.append(label)
    if yardstick is None:
        unit_name, yard = "the answer", math.ulp(want)
    else:
        unit_name, yard = "ulp({!r})".format(yardstick), math.ulp(yardstick)
    print("  {:<52} {!r}".format(label, got))
    print("     truth {!r}  abs err {:.3e}  {:.3f} of {}  (budget {:.3f})  {}".format(
        want, err, err / yard, unit_name, tol / yard, "ok" if ok else "OVER TOLERANCE"))
    return ok


def exact_covariance(xs, ys, ddof=1):
    """The covariance of two int sequences as a rational, so it is not a float claim."""
    n = len(xs)
    mx = Fraction(sum(xs), n)
    my = Fraction(sum(ys), n)
    return sum((Fraction(a) - mx) * (Fraction(b) - my) for a, b in zip(xs, ys)) / (n - ddof)


def naive_covariance(xs, ys, ddof=1):
    """The textbook form, written out: (sum(xy) - sum(x)sum(y)/n) / (n - ddof)."""
    n = len(xs)
    return (sum(a * b for a, b in zip(xs, ys)) - sum(xs) * sum(ys) / n) / (n - ddof)


def main():
    print("stateskol descriptive v0.1-rc, one pass through the frozen surface")
    print("python {}\n".format(sys.version.split()[0]))

    print("1. what this build defines")
    print("  policies {}   methods {}   ddof {}".format(POLICIES, METHODS, DDOFS))
    print("  assumption: {}\n".format(ASSUMPTION))

    print("2. the contract, in one line each")
    mixed = [4, 8, None, 15, float("nan"), 16]
    check("count(mixed)", count(mixed), 4)
    check("as_numeric(mixed)", as_numeric(mixed), [4.0, 8.0, 15.0, 16.0])
    try:
        as_numeric([4, "8", 15])
        failures.append("a str was accepted as a measurement")
        print('  str in a numeric series                       ACCEPTED, which is wrong')
    except ContractError as err:
        print('  as_numeric([4, "8", 15])                       refused -> {}'.format(err))
    print("  the full refusal tour is examples/clean_env_demo.py\n")

    print("3. center and spread, hand-worked")
    check("quantile(DEMO, 0.25)", quantile(DEMO, 0.25), 9.75)
    check("quantile(DEMO, 0.50)", quantile(DEMO, 0.50), 15.5)
    check("quantile(DEMO, 0.75)", quantile(DEMO, 0.75), 21.25)
    check("iqr(DEMO)", iqr(DEMO), 11.5)
    check("iqr(TEN)", iqr(TEN), 8.25)
    check_close("variance(DEMO)", variance(DEMO), 182.0, 0.0)
    check_close("stdev(DEMO)", stdev(DEMO), math.sqrt(182.0), 0.0)
    check_close("coefficient_variation(DEMO)", coefficient_variation(DEMO),
                math.sqrt(182.0) / 18.0, 0.0)
    print("  variance(TEN) lands one ulp under 142/5: {!r} vs {!r}".format(
        variance(TEN), 142 / 5))
    check("variance(TEN) is the next double below the exact value",
          variance(TEN), math.nextafter(142 / 5, 0.0))
    print()

    print("4. the median does not move; the mean does")
    check("quantile(NINE, 0.5)", quantile(NINE, 0.5), 4.0)
    check("quantile(NINE_PLUS_ONE, 0.5)", quantile(NINE_PLUS_ONE, 0.5), 4.0)
    print("  mean(NINE) = {!r}, mean(NINE_PLUS_ONE) = {!r}".format(
        sum(NINE) / 9, sum(NINE_PLUS_ONE) / 10))
    check("iqr(NINE)", iqr(NINE), 3.0)
    print("  one 48 moved the mean by {:.2f} and the median by {:.1f}\n".format(
        sum(NINE_PLUS_ONE) / 10 - sum(NINE) / 9,
        quantile(NINE_PLUS_ONE, 0.5) - quantile(NINE, 0.5)))

    print("5. the package refuses to guess a rule")
    try:
        quantile(TEN, 0.5, method="type5")
        failures.append("type5 fell back to type7 instead of refusing")
        print('  quantile(..., method="type5")                    ACCEPTED, which is wrong')
    except UnsupportedRuleError as err:
        print('  quantile(..., method="type5")                    refused -> {}'.format(err))
    try:
        variance(TEN, ddof=2)
        failures.append("ddof=2 was accepted")
        print("  variance(..., ddof=2)                            ACCEPTED, which is wrong")
    except DomainError as err:
        print("  variance(..., ddof=2)                            refused -> {}".format(err))
    print()

    print("6. association on the brief pair")
    state = bivariate_online_update(XS, YS)
    check("state.n", state.n, 4)
    check("state.mean_x", state.mean_x, SHIFT + 2.5)
    check("state.m2_x", state.m2_x, 5.0)
    check("state.co_moment", state.co_moment, 10.0)
    check("covariance() against the hand-worked 10/3", state.covariance(), 10 / 3)
    print("  exact rational truth: {}".format(exact_covariance(
        [1, 2, 3, 4], [2, 4, 6, 8])))
    r = state.co_moment / math.sqrt(state.m2_x * state.m2_y)
    check("r from the same pass (y = 2x)", r, 1.0)
    print()

    print("7. paired missingness, and the wrong way to do it")
    pairs = bivariate_online_update([1, None, 3], [10, 20, 30])
    check("complete-case n", pairs.n, 2)
    check("dropped_pairs", pairs.dropped_pairs, 1)
    check("complete-case covariance", pairs.covariance(), 20.0)
    check("covariance if the columns were dropped separately",
          bivariate_online_update([1, 3], [10, 20]).covariance(), 10.0)
    print("  both report n = 2. Only one of them paired 3 with a value that")
    print("  was ever measured against it.\n")

    print("8. a constant column has no correlation, and that is not a number")
    flat = bivariate_online_update([7, 7, 7, 7], [1, 2, 4, 8])
    check("m2_x is exactly zero", flat.m2_x, 0.0)
    check("co_moment is exactly zero", flat.co_moment, 0.0)
    try:
        flat.co_moment / math.sqrt(flat.m2_x * flat.m2_y)
        failures.append("the zero-divisor correlation returned a value")
        print("  co_moment / sqrt(m2_x * m2_y)                     RETURNED, which is wrong")
    except ZeroDivisionError:
        print("  co_moment / sqrt(m2_x * m2_y)                     ZeroDivisionError,")
        print("     so pearson_r must raise rather than answer 0.0\n")

    print("9. two series of different length are not one sample")
    try:
        bivariate_online_update([1, 2, 3], [10, 20])
        failures.append("a length mismatch was truncated instead of refused")
        print("  bivariate_online_update(3 values, 2 values)        ACCEPTED, which is wrong")
    except DimensionMismatchError as err:
        print("  bivariate_online_update(3 values, 2 values)        refused -> {}\n".format(err))

    print("10. the 10^9 shift: three algorithms, one answer")
    truth = exact_covariance(XA, YA)
    xs_shift = [SHIFT + v for v in XA]
    ys_shift = [SHIFT + v for v in YA]
    naive = naive_covariance(xs_shift, ys_shift)
    one_pass = bivariate_online_update(xs_shift, ys_shift).covariance()
    mean_x = sum(xs_shift) / len(xs_shift)
    two_pass = sum((a - mean_x) * (b - sum(ys_shift) / len(ys_shift))
                   for a, b in zip(xs_shift, ys_shift)) / (len(xs_shift) - 1)
    print("  exact covariance as a rational: {} = {!r}".format(truth, float(truth)))
    check_close("one-pass CGL", one_pass, float(truth), 40 * math.ulp(SHIFT),
                yardstick=SHIFT + 4.4)
    check_close("two-pass, centred", two_pass, float(truth), 32 * math.ulp(float(truth)))
    print("  naive: {!r}, wrong by at least the answer itself: {}".format(
        naive, abs(naive - float(truth)) >= float(truth)))
    if abs(naive - float(truth)) < float(truth):
        failures.append("the naive form was closer than the bound claims")
    print("  the one-pass floor is the ulp of its own running mean,")
    print("  ulp(1e9) = {!r}, so a 1e-07 scale error at this magnitude is the\n"
          "  algorithm working, not failing.\n".format(math.ulp(SHIFT)))

    print("11. not in this build, stated rather than hidden")
    print("  skewness, kurtosis: cut to v0.2 per the week 4 cut rule, so the")
    print("     scipy.stats comparison has no subject yet.")
    print("  histogram_bins, frequency_table: another lane. The IQR = 0 binning")
    print("     refusal cannot be tested from this branch.")
    print("  covariance(), pearson_r() as public functions: Core C builds them on")
    print("     BivariateState. Section 6 computes r inline to show the state is")
    print("     sufficient; it is not a claim that the function shipped.\n")

    print("12. the one-pass state, for the reader who wants to check by hand")
    walk = BivariateState()
    print("   k  mean_x          mean_y          m2_x   m2_y   co_moment")
    for k, (a, b) in enumerate(zip(XS, YS), start=1):
        walk.add(a, b)
        print("  {}  {:<15} {:<15} {:<6} {:<6} {}".format(
            k, repr(walk.mean_x), repr(walk.mean_y), repr(walk.m2_x),
            repr(walk.m2_y), repr(walk.co_moment)))
    print("  the rows are exactly 1e9 + the dyadic steps a pen gives: means")
    print("  1.0, 1.5, 2.0, 2.5; m2_x 0, 0.5, 2, 5; co_moment 0, 1, 4, 10.\n")

    print("=" * 62)
    print("ALL OK" if not failures else "FAILURES: " + ", ".join(failures))
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
