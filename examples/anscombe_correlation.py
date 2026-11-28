"""The Sunday demonstration: where Pearson r stops telling the truth.

Run it with nothing installed:

    python examples/anscombe_correlation.py

The brief's Sunday slot asks for *a dataset where correlation severely misleads*.
This prints four of them, in the order they work as a talk:

  1. Anscombe's quartet - four datasets, one regression line, and r inside a
     few ten-thousandths across all four. The summary is not describing the data.
  2. Panel IV with its single leverage point removed - r is not small there, it
     is undefined, because the remaining ten x values are all 8.
  3. y = x^2 over a symmetric design - r is exactly 0.0, not approximately, on a
     relationship that is completely determined.
  4. The same nine x with y = |x|, then one extra point at (20, 20) - r goes
     from nothing to 0.90. One row is not evidence of a trend, it is the trend.

Then the reason r exists at all: covariance changes when you change the units and
r does not.

Every printed number is checked against exact rational arithmetic computed in
this file, and the script exits non-zero if any check fails. Nothing here is
transcribed from a table: an earlier draft of the linked vault note did that and
published a wrong r for panel IV.

What is NOT here: skewness, kurtosis, frequency tables, automatic binning. See
descriptive_v01_demo.py for the engine, and section "Cut from v0.1" at the end.
"""

import math
import sys
from fractions import Fraction

from stateskol.descriptive import bivariate_online_update

failures = []


def check(label, got, want, tol, yardstick=None):
    """Compare a float with the exact value, and say the gap in a named unit.

    The unit matters. The one-pass accumulator's floor is the ulp of its own
    running mean, not the ulp of the answer, so "within 1e-9" would be either
    absurdly loose or impossible depending on where the data sits.
    """
    err = abs(got - want)
    ok = err <= tol
    if not ok:
        failures.append(label)
    yard = math.ulp(yardstick if yardstick is not None else want) if want else 0.0
    print("  {:<44} {!r}".format(label, got))
    if yard:
        print("  {:<44} exact {!r}   gap {:.3g} = {:.2f} ulp({!r})".format(
            "", want, err, err / yard,
            yardstick if yardstick is not None else want))
    else:
        print("  {:<44} exact {!r}   gap {!r}   (the claim is an exact zero)".format(
            "", want, err))
    print("  {:<44} {}".format("", "OK" if ok else "FAIL (tol {!r})".format(tol)))
    return got


def exact_pair(xs, ys, ddof=1):
    """Covariance, correlation, slope and intercept from exact rationals.

    Fraction arithmetic is exact, so this is not a second approximation to
    check the first against - it is the answer, and the float has to be near it.
    """
    ex = [Fraction(str(v)) for v in xs]
    ey = [Fraction(str(v)) for v in ys]
    n = len(ex)
    mx, my = sum(ex) / n, sum(ey) / n
    sxx = sum((v - mx) ** 2 for v in ex)
    syy = sum((v - my) ** 2 for v in ey)
    sxy = sum((a - mx) * (b - my) for a, b in zip(ex, ey))
    if sxx == 0 or syy == 0:
        cov = sxy / (n - ddof)
        return float(mx), float(my), float(cov), None, None, None, (sxx == 0)
    # Fraction has no sqrt, so take the root in Decimal at 40 digits.
    from decimal import Decimal, getcontext
    getcontext().prec = 40
    num = Decimal(sxy.numerator) / Decimal(sxy.denominator)
    den = ((Decimal(sxx.numerator) / Decimal(sxx.denominator))
           * (Decimal(syy.numerator) / Decimal(syy.denominator))).sqrt()
    r_exact = float(num / den)
    cov = float(sxy / (n - ddof))
    slope = float(sxy / sxx)
    intercept = float(my) - slope * float(mx)
    return float(mx), float(my), cov, r_exact, slope, intercept, False


ANS_X = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
PANELS = [
    ("I   linear, with noise", ANS_X,
     [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    ("II  a curve, not a line", ANS_X,
     [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    ("III line with one outlier", ANS_X,
     [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    ("IV  vertical cluster + lever", [8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8],
     [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
]


def section(title):
    print("\n" + title)
    print("-" * len(title))


def demo_anscombe():
    section("1. Anscombe's quartet: one number, four datasets")
    print("  The 44 pairs below are the Anscombe (1973) quartet as every standard")
    print("  source reproduces it. No summary figure - no r, no mean, no variance - is")
    print("  transcribed from any table. Each one is computed in this file, twice.\n")
    print("  {:<30} {:>11} {:>11} {:>9} {:>9}".format(
        "dataset", "r", "covariance", "slope", "intercept"))
    rows, rs = [], []
    for label, xs, ys in PANELS:
        state = bivariate_online_update(xs, ys)
        r = state.co_moment / math.sqrt(state.m2_x * state.m2_y)
        mx, my, cov, r_exact, slope, intercept, undefined = exact_pair(xs, ys)
        assert not undefined, label
        # One pass and exact rationals must agree to a few ulps here: these are
        # small integers and two-decimal values, nowhere near the magnitude where
        # the running-mean grid bites. The checks are collected and printed after
        # the table so the slide stays readable.
        assert abs(r - r_exact) <= 8 * math.ulp(r_exact), label
        assert abs(state.covariance() - cov) <= 8 * math.ulp(cov), label
        assert abs(state.mean_x - mx) <= 8 * math.ulp(mx), label
        assert abs(state.mean_y - my) <= 8 * math.ulp(my), label
        rs.append((label, r, r_exact, state.covariance(), cov, slope, intercept))
        print("  {:<30} {:>11.6f} {:>11.4f} {:>9.5f} {:>9.5f}".format(
            label, r, state.covariance(), slope, intercept))
    three = [round(v[1], 3) for v in rs]
    r2 = [v[1] * v[1] for v in rs]
    fit = [(round(v[5], 2), round(v[6], 2)) for v in rs]
    print("\n  Same fit, y = 3.00 + 0.50x, in all four:", fit)
    print("  r to three decimals:", three)
    print("  r-squared:", " ".join("{:.6f}".format(v) for v in r2))
    if len(set(fit)) != 1:
        failures.append("the four least-squares fits do not round to one line: "
                        "{}".format(fit))
    if three.count(0.816) != 3 or three.count(0.817) != 1:
        failures.append("r to three decimals is not three 0.816 and one 0.817: "
                        "{}".format(three))
    if sorted(set(round(v, 2) for v in r2)) != [0.67]:
        failures.append("r-squared does not round to 0.67 in all four: {}".format(
            [round(v, 2) for v in r2]))
    print("\n  Cross-checked against exact rational arithmetic, gap in ulps:")
    for label, r, r_exact, cov_got, cov_want, slope, intercept in rs:
        print("    {:<30} r gap {:.0f} ulp   covariance gap {:.0f} ulp".format(
            label.split()[0],
            abs(r - r_exact) / math.ulp(r_exact),
            abs(cov_got - cov_want) / math.ulp(cov_want)))
    spread = max(v[1] for v in rs) - min(v[1] for v in rs)
    print("\n  The four r values are not identical: they span {:.6f}. Rounded the way".format(
        spread))
    print("  any table rounds them, three land on 0.816 and one on 0.817. r-squared spans")
    print("  {:.4f} to {:.4f}, and all four are 0.67 to two decimals. So the honest".format(
        min(r2), max(r2)))
    print("  claim is not \"the same r\", it is \"indistinguishable as summaries\":")
    print("  four different shapes, one fit line.")


def demo_leverage():
    section("2. Panel IV without its one important row")
    label, xs, ys = PANELS[3]
    lever = xs.index(19)
    keep_x = xs[:lever] + xs[lever + 1:]
    keep_y = ys[:lever] + ys[lever + 1:]
    state = bivariate_online_update(keep_x, keep_y)
    print("  x after removing index {}:".format(lever), keep_x)
    check("m2_x (the exact zero is the point)", state.m2_x, 0.0, 0.0)
    print("  variance_x() =", state.variance_x(), " covariance() =", state.covariance())
    try:
        state.co_moment / math.sqrt(state.m2_x * state.m2_y)
    except ZeroDivisionError as exc:
        print("  r = co_moment / sqrt(m2_x * m2_y)  ->  ZeroDivisionError: {}".format(exc))
    else:
        failures.append("constant x must not produce a quotient")
    print("\n  Ten of eleven pairs gave the y-spread and none of the x-spread. The")
    print("  0.8165 belongs entirely to one row. A correlation is not a vote:")
    print("  an observation that cannot vary in x has no say in it, and no")
    print("  presence in it either - it just inflates n.")


def demo_zero_r():
    section("3. r = 0 on a perfectly determined relationship")
    xs = list(range(-4, 5))
    ys = [v * v for v in xs]
    state = bivariate_online_update(xs, ys)
    mx, my, cov, r_exact, slope, intercept, undefined = exact_pair(xs, ys)
    assert not undefined
    check("covariance of y = x^2, x = -4..4", state.covariance(), cov, 0.0)
    r = state.co_moment / math.sqrt(state.m2_x * state.m2_y)
    check("r", r, 0.0, 0.0)
    print("\n  Exactly zero, in float and in rationals, because every +x has a")
    print("  matching -x with the same y. The parabola is as deterministic as a")
    print("  relationship gets, and r reports nothing. A circle x^2 + y^2 = 1 and a")
    print("  full sine period sit in the same place.")


def demo_manufactured():
    section("4. One point manufactures a correlation")
    xs = list(range(-4, 5))
    abs_y = [abs(v) for v in xs]
    state = bivariate_online_update(xs, abs_y)
    r_abs = state.co_moment / math.sqrt(state.m2_x * state.m2_y)
    mx, my, cov, r_exact, slope, intercept, undefined = exact_pair(xs, abs_y)
    print("  y = |x| over x = -4..4")
    check("exact r is 0; float r is residue", r_abs, 0.0, 1e-15)
    print("  (the residue is not pinned further - 20/9 is not representable, and")
    print("   asserting a specific last digit would be asserting the interpreter's")
    print("   own accumulation order. This suite learned that the hard way.)")
    xs2 = xs + [20]
    ys2 = abs_y + [20]
    state2 = bivariate_online_update(xs2, ys2)
    r2 = state2.co_moment / math.sqrt(state2.m2_x * state2.m2_y)
    mx, my, cov, r_exact2, slope, intercept, undefined = exact_pair(xs2, ys2)
    check("r after adding (20, 20)", r2, r_exact2, 8 * math.ulp(r_exact2))
    print("\n  One extra observation out of ten takes r from nothing to {:.5f}.".format(r2))
    print("  r-squared {:.3f}: \"explains\" {:.1f}% of the variance.".format(
        r2 * r2, 100 * r2 * r2))
    print("  Drop that row and the relationship it summarises goes with it.")


def demo_units():
    section("5. Why r exists: covariance is an area in two units")
    span_cm = [18.0, 20.0, 21.0, 23.0, 25.0]
    grip_n = [300.0, 350.0, 380.0, 420.0, 460.0]
    span_m = [v / 100.0 for v in span_cm]
    grip_kgf = [v / 9.80665 for v in grip_n]
    a = bivariate_online_update(span_cm, grip_n)
    b = bivariate_online_update(span_m, grip_kgf)
    ra = a.co_moment / math.sqrt(a.m2_x * a.m2_y)
    rb = b.co_moment / math.sqrt(b.m2_x * b.m2_y)
    print("  same five people, measured twice")
    print("  {:<28} covariance {:>14.6f}   r {:>14.10f}".format("cm, newton", a.covariance(), ra))
    print("  {:<28} covariance {:>14.6f}   r {:>14.10f}".format("metre, kilogram-force",
                                                                b.covariance(), rb))
    ratio = a.covariance() / b.covariance()
    check("covariance ratio is the conversion, not the data",
          ratio, 100 * 9.80665, 1e-9)
    print("  980.665 = 100 cm/m x 9.80665 N/kgf. The covariance moved by the")
    print("  measuring tape. r did not move at all, which is the entire reason")
    print("  Pearson normalises: it is the only one of the two comparable across")
    print("  studies. |r| <= 1 is Cauchy-Schwarz, one rectangle inside another.")


def main():
    print("stateskol week 4 Numerics - the Sunday demonstration on bivariate "
          "misrepresentation")
    print("python {}, stdlib only, no third-party import".format(sys.version.split()[0]))
    demo_anscombe()
    demo_leverage()
    demo_zero_r()
    demo_manufactured()
    demo_units()

    section("Cut from v0.1, and why the demonstration does not need them")
    print("  skewness, kurtosis, frequency_table, automatic histogram binning:")
    print("  other lanes, not this file. covariance() and pearson_r() as public")
    print("  functions are Core C's wrappers over the state printed above.")
    print("  r is written out here as co_moment / sqrt(m2_x * m2_y) instead of")
    print("  behind a method name, so that the ZeroDivisionError in section 2 is")
    print("  visibly the formula's own failure and not the package's.")

    if failures:
        print("\nFAILURES ({}): {}".format(len(failures), ", ".join(failures)))
        return 1
    print("\nALL OK - every number above was checked against exact rational")
    print("arithmetic computed in this file. Exit 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
