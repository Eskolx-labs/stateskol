"""The data contract, in code, and the spread summaries that inherit it.

Week 2, Act I, Descriptive v0.1. Week 3 Core B adds quantile, iqr, variance,
stdev and coefficient_variation in the block at the foot of this file; the
contract above is unchanged.

A function that cannot refuse bad input cannot run unattended. This module is
the first gate in the pipeline: it decides what counts as data, what counts as
missing, and which error each refusal raises. Anything else in the package
that does arithmetic works on the output of ``as_numeric()``.

v0.1 contract
-------------
=====================  ==========================  ==================================
Input                  Behaviour                   Reason
=====================  ==========================  ==================================
``int``, ``float``     accepted                    the only numeric types v0.1 knows
``bool``               ContractError               True is an int, but not a measurement
``str``                ContractError               no coercion; "3" is not a number
``bytes``              ContractError               same reason as ``str``
``Decimal``            ContractError               v0.1 states the boundary
``Fraction``           ContractError               v0.1 states the boundary
``complex``            ContractError               no ordering, so no minimum
``inf``, ``-inf``      ContractError               a data error, not a large number
``abs(n) > 2**53``     ContractError               float(n) would round it silently
``None``, ``nan``      missing, handled by policy  never handled by arithmetic
empty iterable         ``count`` returns 0         an empty file is a finding, not a value
all values missing     summaries raise             the policy ran and left nothing
generator              consumed once               the function never iterates twice
=====================  ==========================  ==================================

Missing-value policy
--------------------
``"drop"`` (default) drops the missing values, continues, and lets the audit
record what was dropped. ``"strict"`` refuses on the first missing value. The
package never fills, imputes, or coerces.

Dropping is not a neutral act. It is unbiased under MCAR, can bias a summary
under MAR, and usually does under MNAR (Rubin 1976). Nothing in this module
can observe the mechanism, so each docstring states the assumption instead of
hiding it.

Lanes
-----
The Contract lane owns this file's rules, ``errors.py``, ``as_numeric`` and
``count``. ``minimum`` is Core A. ``maximum``, ``data_range``,
``missing_report`` and ``audit`` are Core B. They belong in their own pull
requests, not here.

Week 3, Core B
--------------
``quantile``, ``iqr``, ``variance``, ``stdev`` and ``coefficient_variation``
were added on top of the contract, in the block at the foot of this file. They
inherit every rule above: they read the input once, they take their numbers
from ``as_numeric``, they raise ``EmptyDataError`` when nothing is present, and
each docstring states the assumption. Two additions to the contract come with
them, both checked before any data is read:

=========================  ==========================  ========================
Argument                   Behaviour                   Error
=========================  ==========================  ========================
``p`` outside ``[0, 1]``   refused, no clamping        DomainError
``method`` not ``type7``   refused, no substitution    UnsupportedRuleError
``ddof`` outside 0 or 1    refused, no silent n        DomainError
mean of 0 for the CV       refused, not reported       DomainError
=========================  ==========================  ========================
"""

import math

from stateskol.errors import (
    ContractError,
    DomainError,
    EmptyDataError,
    UnknownPolicyError,
    UnsupportedRuleError,
)

DOCSTRING_SHAPE = """Inputs:      what the function takes, including the types it rejects
Outputs:     one value, its type, and what it means
Assumptions: the statistical assumption, or "Unknown. The caller must state the mechanism."
Missing:     how None and nan are treated, per policy
Errors:      every exception, named, with the condition that raises it
Example:     at least one call and its exact result
"""

# Above this, float(n) is not n any more, so an int cannot survive the
# conversion exactly. The bound is about the conversion, not about size:
# a large finite float is accepted because no conversion happens.
_MAX_SAFE_INT = 2**53

POLICIES = ("drop", "strict")

ASSUMPTION = "Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR)."


def _type_refusal(x):
    """Return why x is not a measurement, or None if the contract accepts it.

    bool is tested before int because bool is a subclass of int, and the
    order decides whether ``True`` reaches arithmetic as ``1``.
    """
    if isinstance(x, bool):
        return "bool is not a measurement"
    if isinstance(x, str):
        return "str is not accepted and is never coerced"
    if isinstance(x, (bytes, bytearray)):
        return "bytes is not accepted and is never coerced"
    if isinstance(x, complex):
        return "complex has no ordering, so it cannot enter a summary"
    if not isinstance(x, (int, float)):
        return "unsupported type {}".format(type(x).__name__)
    if isinstance(x, float) and math.isinf(x):
        return "infinite observation"
    if isinstance(x, int) and abs(x) > _MAX_SAFE_INT:
        return "abs(n) > 2**53 would round silently as a float"
    return None


def _validate(x, index=None):
    """Raise ContractError unless x satisfies the v0.1 contract.

    Inputs:  x     one value taken from the input
             index its position in the input, or None
    Outputs: None. The function exists to raise, not to return.
    Assumptions: none. This is a type and range test, not a statistical claim.
    Missing: None and nan are not refused here. They are missing, and the
        policy decides their fate before this function is reached.
    Errors:  ContractError whose message names the rule and the index of the
        offending value.
    Example:
        >>> _validate(3, 0) is None
        True
        >>> _validate(True, 4)
        Traceback (most recent call last):
            ...
        stateskol.errors.ContractError: index 4: bool is not a measurement: True
    """
    reason = _type_refusal(x)
    if reason is not None:
        raise ContractError(
            "index {}: {}: {!r}".format(index, reason, x), index=index, value=x
        )


def _is_missing(x):
    """True if x is None or a float nan.

    Only float nan counts as missing. Decimal("NaN") is not a float, so the
    contract rejects it as an unsupported type rather than quietly dropping a
    value the caller never agreed to treat as missing.

    Inputs:  x any object
    Outputs: bool
    Assumptions: none.
    Missing: this is the v0.1 definition of missing.
    Errors:  never raises.
    Example:
        >>> _is_missing(float("nan"))
        True
        >>> _is_missing(0)
        False
    """
    if x is None:
        return True
    return isinstance(x, float) and math.isnan(x)


def _check_policy(policy):
    """Validate the policy before any input is consumed.

    The order matters for a generator. A caller who passes an unknown policy
    must not have the values swallowed on the way to the error.

    Inputs:  policy one of POLICIES
    Outputs: None
    Assumptions: none.
    Missing: not reached by values at all.
    Errors:  UnknownPolicyError if policy is not documented.
    Example:
        >>> _check_policy("drop") is None
        True
    """
    if policy not in POLICIES:
        raise UnknownPolicyError(
            "unknown policy: {!r}. Expected one of {!r}.".format(policy, POLICIES)
        )


def as_numeric(data, policy="drop"):
    """Turn an arbitrary iterable into the list of floats the package sums over.

    Inputs:  data   any iterable of int or float, which may contain None and
                 nan. bool, str, bytes, Decimal, Fraction, complex, inf and
                 -inf are refused, never coerced.
             policy "drop" (default) discards missing values, "strict"
                 refuses the first one.
    Outputs: list[float] holding the present values in input order. Empty
             input gives [].
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
             Dropping is unbiased only under MCAR; read the module docstring
             before trusting a summary built from a dropped list.
    Missing: under "drop", None and nan are removed and take no part in the
             result. Under "strict", the first one raises ContractError.
    Errors:  ContractError for a value that breaks the v0.1 contract, or for
             a missing value under "strict". UnknownPolicyError if policy is
             not "drop" or "strict", raised before data is iterated.
    Example:
        >>> as_numeric([3, None, 7, float("nan"), 1])
        [3.0, 7.0, 1.0]
        >>> as_numeric([])
        []
    """
    _check_policy(policy)
    values = []
    for index, item in enumerate(data):
        if _is_missing(item):
            if policy == "strict":
                raise ContractError(
                    "index {}: missing value under policy='strict': {!r}".format(
                        index, item
                    ),
                    index=index,
                    value=item,
                )
            continue
        _validate(item, index)
        values.append(float(item))
    return values


def count(data, policy="drop"):
    """How many present values the input holds.

    Inputs:  data   any iterable. A generator is consumed once.
             policy "drop" (default) or "strict".
    Outputs: int. 0 when nothing is present, which covers both empty input and
             input whose every value is missing.
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
             A count is only a sample size if the reader knows why the gaps
             are there.
    Missing: missing values are not counted under "drop". Under "strict", the
             first one raises ContractError.
    Errors:  ContractError for a value that breaks the v0.1 contract, or for a
             missing value under "strict". UnknownPolicyError for an unknown
             policy, raised before data is iterated.
    Example:
        >>> count([3, None, 7, float("nan"), 1])
        3
        >>> count([])
        0
    """
    return len(as_numeric(data, policy))


# ---------------------------------------------------------------------------
# Week 3, Core B: spread. quantile, iqr, variance, stdev, coefficient_variation.
# ---------------------------------------------------------------------------

# The one quantile rule this build ships. Hyndman & Fan (1996) collect nine
# defensible definitions; they disagree on real samples, so a caller who asks
# for another one is refused rather than served by a silent substitute.
METHODS = ("type7",)

# ddof states the divisor: n - 0 is the population variance, n - 1 is the
# sample variance. Any other value would be a third definition nobody asked
# for, so the package defines exactly these two.
DDOFS = (0, 1)


def _check_method(method):
    """Raise UnsupportedRuleError unless method is the rule this build ships.

    Runs before any input is read, for the same reason _check_policy does: a
    wrong argument must not consume a generator on the way to the error.
    """
    if method not in METHODS:
        raise UnsupportedRuleError(
            "method={!r} is not implemented. This build ships type 7 only "
            "(h = (n - 1)p + 1, Hyndman & Fan 1996). Asking for another type "
            "asks for another number, so there is no fallback.".format(method),
            rule=method,
            available=METHODS,
        )


def _check_probability(p):
    """Raise DomainError unless p is a usable probability in [0, 1]."""
    if isinstance(p, bool) or not isinstance(p, (int, float)):
        raise DomainError(
            "p must be an int or float between 0 and 1, got {!r} of type {}".format(
                p, type(p).__name__
            )
        )
    if isinstance(p, float) and (math.isnan(p) or math.isinf(p)):
        raise DomainError("p must be a finite probability in [0, 1], got {!r}".format(p))
    if p < 0 or p > 1:
        raise DomainError("p must be between 0 and 1 inclusive, got {!r}".format(p))


def _check_ddof(ddof):
    """Raise DomainError unless ddof is a divisor this package defines."""
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof not in DDOFS:
        raise DomainError(
            "ddof={!r} is not defined. The package divides by n (ddof=0) or "
            "by n - 1 (ddof=1), which is the sample variance.".format(ddof)
        )


def _present(data):
    """The single pass every spread summary makes, then refuses if it found nothing.

    Inputs:  data any iterable the v0.1 contract accepts.
    Outputs: list[float] of the present values, never empty.
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
    Missing: policy "drop", the only one the week 3 table gives these
             summaries. A caller who wants strictness passes the input through
             as_numeric(data, policy="strict") first.
    Errors:  ContractError from the v0.1 contract, EmptyDataError when no
             present value survives.
    """
    values = as_numeric(data, "drop")
    if not values:
        raise EmptyDataError(
            "no present values survived the policy, so this summary is undefined"
        )
    return values


def _quantile_sorted(values, p):
    """Type-7 quantile of values that are already sorted, non-empty, all floats.

    The brief writes the position 1-indexed as h = (n - 1)p + 1; here it is
    the same rule 0-indexed as h = (n - 1)p. Keeping the arithmetic in one
    place is what makes quantile() and iqr() agree on one pass of the input.
    """
    n = len(values)
    if n == 1:
        return float(values[0])
    position = (n - 1) * p
    low = int(position)          # position >= 0, so int() floors it
    fraction = position - low
    if fraction == 0.0:
        return float(values[low])
    upper = values[low + 1]
    return values[low] + fraction * (upper - values[low])


def _welford(values):
    """One scan of values, returning (n, mean, m2) with m2 = sum of squared deviations.

    Welford (1962). Each new value updates the running mean first, then weighs
    the deviation against the OLD mean and the NEW one, so no large number is
    ever subtracted from another large number. The shortcut
    sum(x * x) / n - mean **2 does exactly that subtraction and returns 0.0
    for [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4].
    """
    n = 0
    mean = 0.0
    m2 = 0.0
    for x in values:
        n += 1
        delta = x - mean
        mean += delta / n
        m2 += delta * (x - mean)
    return n, mean, m2


def _variance_of(values, ddof):
    """Welford variance of a non-empty list of floats."""
    n, _mean, m2 = _welford(values)
    if n - ddof <= 0:
        raise EmptyDataError(
            "variance needs more present values than the divisor takes: "
            "n={}, ddof={}".format(n, ddof)
        )
    return m2 / (n - ddof)


def quantile(data, p, method="type7"):
    """The p-th quantile of the present values, by one named rule.

    Inputs:  data   any iterable the v0.1 contract accepts. A generator is
                 consumed once.
             p      an int or float between 0 and 1 inclusive.
             method the quantile rule. Only "type7" is shipped; anything else
                 raises UnsupportedRuleError that names the rule it refused.
    Outputs: float. The value at position h = (n - 1)p + 1 of the sorted
             present values, 1-indexed, interpolated linearly between the two
             values h falls between. The rule is type 7. Hyndman & Fan (1996)
             collect the nine defensible definitions; this is the one R, numpy,
             pandas and Excel PERCENTILE.INC default to.
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
             Type 7 is a choice, not a fact: on 2 4 4 5 7 9 11 13 15 18 the
             75th percentile is 12.5 here and 13.5 under type 6.
    Missing: missing values are dropped before the sort, under policy "drop".
    Errors:  DomainError if p is outside [0, 1] or is not a finite number;
             UnsupportedRuleError if method is not "type7"; EmptyDataError if
             nothing is present; ContractError for input the contract refuses.
             The rule is checked before data is read, so a bad method or p
             never drains a generator.
    Example:
        >>> quantile([2, 4, 4, 5, 7, 9, 11, 13, 15, 18], 0.75)
        12.5
        >>> quantile([1, 2, 3, 4, 5], 0.25)
        2.0
        >>> quantile([1, 2, 3], 0)
        1.0
    """
    _check_method(method)
    _check_probability(p)
    values = sorted(_present(data))
    return _quantile_sorted(values, p)


def iqr(data, method="type7"):
    """Interquartile range: the type-7 Q3 minus the type-7 Q1.

    Inputs:  data   any iterable the v0.1 contract accepts, consumed once.
             method as in quantile(); only "type7".
    Outputs: float, the spread of the middle half of the present values: the
             type 7 quantile at 0.75 minus the type 7 quantile at 0.25, per
             Hyndman & Fan (1996). Both quartiles come from one sorted list, so
             they cannot disagree about which sample they describe.
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
    Missing: missing values are dropped before the sort, under policy "drop".
    Errors:  UnsupportedRuleError if method is not "type7"; EmptyDataError if
             nothing is present; ContractError for input the contract refuses.
    Example:
        >>> iqr([2, 4, 4, 5, 7, 9, 11, 13, 15, 18])
        8.25
        >>> iqr([4, 8, 15, 16, 23, 42])
        11.5
    """
    _check_method(method)
    values = sorted(_present(data))
    return _quantile_sorted(values, 0.75) - _quantile_sorted(values, 0.25)


def variance(data, ddof=1):
    """Sample variance of the present values, by Welford's one-pass update.

    Inputs:  data  any iterable the v0.1 contract accepts, consumed once.
             ddof  the divisor is n - ddof. Default 1, the sample variance;
                 0 gives the population variance. Any other value raises.
    Outputs: float. The average squared deviation from the mean, divided by
             n - ddof. 0.0 exactly when every present value is equal.
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
             ddof=1 claims an unbiased estimate for a sample drawn from a
             wider population; ddof=0 claims only a description of these
             values. The default follows the book's sample convention.
    Missing: missing values are dropped before the arithmetic, under policy
             "drop", and the count that survives is what n means here.
    Errors:  DomainError if ddof is not 0 or 1; EmptyDataError if nothing is
             present, or if n - ddof would not be positive (a single value
             under ddof=1); ContractError for input the contract refuses.
    Example:
        >>> round(variance([2, 4, 4, 5, 7, 9, 11, 13, 15, 18]), 10)
        28.4
        >>> variance([5, 5, 5])
        0.0
    """
    _check_ddof(ddof)
    return _variance_of(_present(data), ddof)


def stdev(data, ddof=1):
    """Sample standard deviation: the square root of variance(data, ddof).

    Inputs:  data  any iterable the v0.1 contract accepts, consumed once.
             ddof  passed straight to variance(); default 1.
    Outputs: float in the units of the data, which is the whole reason it
             exists next to variance. Always non-negative. The algorithm is
             variance's Welford (1962) one-pass update followed by
             ``math.sqrt``, which the standard library rounds correctly; no
             hand-rolled iteration is introduced here, so there is no stopping
             rule for a reviewer to re-derive.
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
    Missing: dropped exactly as variance() drops them, because the variance is
             computed from the same single pass, not from a second read of
             the input.
    Errors:  DomainError if ddof is not 0 or 1; EmptyDataError when variance
             raises it; ContractError for input the contract refuses.
    Example:
        >>> round(stdev([2, 4, 4, 5, 7, 9, 11, 13, 15, 18]), 10)
        5.3291650378
        >>> stdev([3, 3, 3])
        0.0
    """
    _check_ddof(ddof)
    return math.sqrt(_variance_of(_present(data), ddof))


def coefficient_variation(data):
    """Spread measured in units of the mean: stdev / mean, with ddof=1.

    Inputs:  data any iterable the v0.1 contract accepts, consumed once.
    Outputs: float, a ratio and not a percentage. Multiply by 100 to read it
             as one. Comparable across samples on different scales; the
             standard deviation is not. The algorithm is one Welford (1962)
             pass that returns the count, the mean and m2 together, so the
             numerator and the denominator cannot come from different samples.
    Assumptions: Unknown. The caller must state the missingness mechanism (MCAR, MAR, MNAR).
             The ratio also assumes the mean is on a scale where zero is
             meaningful, so it is not a statement about a temperature in
             Celsius or any other interval scale with an arbitrary origin.
    Missing: dropped before both the mean and the spread are computed, under
             policy "drop", so the ratio describes one sample, not two.
    Errors:  DomainError when the mean is 0, because the ratio is undefined
             rather than large; EmptyDataError when nothing is present, or
             when only one value is present so ddof=1 has no divisor;
             ContractError for input the contract refuses.
    Example:
        >>> round(coefficient_variation([4, 8, 15, 16, 23, 42]), 10)
        0.7494854202
        >>> round(coefficient_variation([2, 4, 4, 5, 7, 9, 11, 13, 15, 18]), 10)
        0.6055869361
    """
    values = _present(data)
    n, mean, m2 = _welford(values)
    if mean == 0.0:
        raise DomainError(
            "coefficient of variation is undefined when the mean is 0: the "
            "ratio would divide by zero. n={}".format(n)
        )
    if n - 1 <= 0:
        raise EmptyDataError(
            "variance needs more present values than the divisor takes: "
            "n={}, ddof=1".format(n)
        )
    return math.sqrt(m2 / (n - 1)) / mean

