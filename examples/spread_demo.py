"""Spread, demonstrated with nothing installed but the package.

Run from the repository root, in a clean environment:

    pip install -e . --no-deps
    python examples/spread_demo.py

Standard library only. No numpy, no pandas -- the numbers below are hand-worked
in the comments so a reader can check them with a pencil. This is the week 3
bar's "one documentation example that runs with nothing installed but the
package", scoped to Core B: quantile, iqr, variance, stdev, coefficient of
variation. Center (mean, median, mode) is Core A and is not shown here.
"""

import math
import sys

from stateskol import (
    ContractError,
    DomainError,
    EmptyDataError,
    UnsupportedRuleError,
    as_numeric,
    coefficient_variation,
    count,
    iqr,
    quantile,
    stdev,
    variance,
)

# The brief's ten values. Sorted already, sum 88, so the mean is 8.8.
TEN = [2, 4, 4, 5, 7, 9, 11, 13, 15, 18]

# The demonstration sample used across the week.
DEMO = [4, 8, 15, 16, 23, 42]

# The numerics case: visible spread, and the naive formula reports none of it.
SHIFTED = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]


def show(label, got, want, ok, rel=1e-12):
    """Print one line and fail loudly if the value is not the hand-worked one."""
    scale = abs(want) if want else 1.0
    good = abs(got - want) / scale <= rel
    print("  {:<34} {:<22} expected {}".format(label, repr(got), want))
    if not good:
        print("  {:<34} ^^^ MISMATCH".format(""))
    return ok and good


def show_refusal(label, call, error, ok):
    """Print one refusal, and fail if the package answered instead of refusing."""
    try:
        value = call()
    except error as err:
        print("  {:<34} refused -> {}".format(label, err))
        return ok
    except Exception as err:  # the wrong type of refusal is still a finding
        print("  {:<34} raised {}, expected {}".format(label, type(err).__name__, error.__name__))
        return False
    print("  {:<34} ANSWERED {}, expected a refusal".format(label, repr(value)))
    return False


def main():
    ok = True
    print("stateskol spread summaries, v0.1")
    print("python {}\n".format(sys.version.split()[0]))

    print("1. the five summaries on one dataset")
    print("  data:", TEN, "\n")
    # h = (10 - 1) * 0.25 + 1 = 3.25, so a quarter of the way from the 3rd
    # value (4) to the 4th (5): 4.25.
    ok = show("quantile(p=0.25)", quantile(TEN, 0.25), 4.25, ok)
    # h = 5.5, the midpoint of the two middle values 7 and 9. Type 7 keeps the
    # book's rule that an even-length median averages the middle pair.
    ok = show("quantile(p=0.50)  = median", quantile(TEN, 0.5), 8.0, ok)
    # h = 7.75, three quarters from 11 to 13: 12.5, the brief's own number.
    ok = show("quantile(p=0.75)", quantile(TEN, 0.75), 12.5, ok)
    ok = show("iqr = Q3 - Q1", iqr(TEN), 8.25, ok)
    # Sum of squared deviations: 46.24 + 23.04 + 23.04 + 14.44 + 3.24 + 0.04
    # + 4.84 + 17.64 + 38.44 + 84.64 = 255.6. Divided by n - 1 = 9 it is 28.4.
    ok = show("variance(ddof=1)", variance(TEN), 255.6 / 9, ok)
    # Divided by n = 10 instead it is 25.56. Same data, different claim.
    ok = show("variance(ddof=0)", variance(TEN, ddof=0), 255.6 / 10, ok)
    ok = show("stdev(ddof=1)", stdev(TEN), math.sqrt(255.6 / 9), ok)
    ok = show("coefficient_variation", coefficient_variation(TEN),
              math.sqrt(255.6 / 9) / 8.8, ok)
    print()

    print("2. the rule is named, and the alternative is refused")
    print("  quantile(TEN, 0.75)          ->", quantile(TEN, 0.75), "(type 7)")
    print("  type 6 would have said 13.5. That is a modelling choice, not a")
    print("  rounding error, so the package refuses to guess which one you meant:")
    ok = show_refusal('method="type6"', lambda: quantile(TEN, 0.75, method="type6"),
                      UnsupportedRuleError, ok)
    ok = show_refusal('method="type8"', lambda: iqr(TEN, method="type8"),
                      UnsupportedRuleError, ok)
    print()

    print("3. variance has one definition and many algorithms")
    print("  data:", ["1e9+1", "1e9+2", "1e9+3", "1e9+4"])
    mean = sum(SHIFTED) / len(SHIFTED)
    naive = sum(x * x for x in SHIFTED) / len(SHIFTED) - mean * mean
    print("  naive sum(x*x)/n - mean**2   ->", naive, "  <- the spread vanished")
    ok = show("welford variance(ddof=1)", variance(SHIFTED), 5 / 3, ok, rel=1e-9)
    print("  The deviations from 1e9 + 2.5 are -1.5, -0.5, 0.5, 1.5, so m2 = 5")
    print("  and the sample variance is 5/3. Nothing large is ever subtracted.\n")

    print("4. a constant sample has no spread, and the answer is exact")
    ok = show("variance([5, 5, 5, 5])", variance([5, 5, 5, 5]), 0.0, ok)
    ok = show("stdev([5, 5, 5, 5])", stdev([5, 5, 5, 5]), 0.0, ok)
    ok = show("iqr([5, 5, 5, 5])", iqr([5, 5, 5, 5]), 0.0, ok)
    print()

    print("5. missing values are dropped, and the drop is visible")
    holey = [2, None, 4, float("nan"), 4, 5, 7, 9, 11, 13, 15, 18]
    print("  data:", holey)
    print("  n_total", len(holey), "n_present", count(holey), "-> as_numeric",
          as_numeric(holey))
    # The same summary as on the complete sample: dropping happened first, and
    # the count that survived is what n means in the divisor.
    ok = show("quantile(p=0.75) after drop", quantile(holey, 0.75), 12.5, ok)
    print("  The week 2 audit object records positions and the assumption. It")
    print("  lives in week 2 Core B, which has not merged, so the drop is shown")
    print("  here through as_numeric instead of being hidden.\n")

    print("6. refusals, one row per rule")
    ok = show_refusal("quantile p=1.5", lambda: quantile(TEN, 1.5), DomainError, ok)
    ok = show_refusal("quantile p='0.5'", lambda: quantile(TEN, "0.5"), DomainError, ok)
    ok = show_refusal("variance ddof=2", lambda: variance(TEN, ddof=2), DomainError, ok)
    ok = show_refusal("variance([])", lambda: variance([]), EmptyDataError, ok)
    ok = show_refusal("variance([None, nan])", lambda: variance([None, float("nan")]),
                      EmptyDataError, ok)
    ok = show_refusal("variance([7])  n-1 is 0", lambda: variance([7]), EmptyDataError, ok)
    ok = show_refusal("coefficient_variation([1, -1])",
                      lambda: coefficient_variation([1, -1]), DomainError, ok)
    ok = show_refusal("quantile([4, '8'], 0.5)", lambda: quantile([4, "8"], 0.5),
                      ContractError, ok)
    print()

    print("7. a generator is consumed once, even though iqr needs two quartiles")
    drained = []

    def source():
        for value in TEN:
            drained.append(value)
            yield value

    print("  iqr(generator) ->", iqr(source()))
    print("  values the generator produced:", len(drained), "(ten means one pass)")
    ok = ok and len(drained) == len(TEN)
    print()

    print("ALL OK" if ok else "FAILURES PRESENT")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
