"""The data contract, in code.

Week 2, Act I, Descriptive v0.1.

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
"""

import math

from stateskol.errors import ContractError, UnknownPolicyError

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


# --------------------------------------------------------------------------
# Numerics lane (Hanna Desalegn). Week 2.
#
# The contract above decides which values are data. This block covers what
# happens to accepted values once arithmetic touches them. Three facts drive it:
#
# 1. Above 2**53 a float cannot hold every integer. float(2**53 + 1) is
#    2**53, so two different measurements become equal. That is why the
#    contract refuses ints with abs(n) > 2**53. The rule is about converting
#    an int, not about size: a float such as 1e16 or 1e308 needs no
#    conversion and is accepted. The bound is also conservative. 2**60 is
#    exactly representable but is still refused, because one simple bound is
#    easier to state and test than an exactness check.
# 2. nan breaks ordering. Python's min([nan, 3, 1]) is nan but
#    min([3, nan, 1]) is 1, so the answer depends on input order. Missing
#    values must leave before min and max run, which as_numeric guarantees.
# 3. Two finite floats can have an infinite difference.
#    1e308 - (-1e308) is inf, so data_range must check its own result.
#
# Types: v0.1 accepts int and float, including float subclasses such as
# numpy.float64, because they convert to float exactly. numpy.int64 and
# numpy.float32 are not int or float and are refused by the contract.
# --------------------------------------------------------------------------

def checked_difference(hi, lo):
    """hi - lo as a float, refusing a result the inputs cannot justify.

    Inputs:      hi, lo  finite floats, already accepted by as_numeric.
    Outputs:     float, hi - lo. For hi >= lo this is the data range.
    Assumptions: none. This is an arithmetic guard, not a statistical claim.
    Missing:     not reached. Callers pass values that already left the policy.
    Errors:      ContractError when hi or lo breaks the v0.1 contract (bool, str,
                 inf, abs(n) > 2**53 and the other refused types), the same rule
                 as_numeric applies. ValueError when hi or lo is nan, since a
                 missing value should have left through the policy first.
                 OverflowError when hi and lo are finite but hi - lo is not,
                 e.g. 1e308 - (-1e308).
    Example:
        >>> checked_difference(9.0, 2.0)
        7.0
        >>> checked_difference(1e308, -1e308)
        Traceback (most recent call last):
            ...
        OverflowError: range of 1e+308 and -1e+308 overflows a float
    """
    # same accepted types as the contract, so a helper cannot take what as_numeric refuses
    for v in (hi, lo):
        _validate(v)
    hi = float(hi)
    lo = float(lo)
    if math.isnan(hi) or math.isnan(lo):
        raise ValueError("checked_difference needs present values, got {!r} and {!r}".format(hi, lo))
    diff = hi - lo
    # finite in, infinite out: the float ran out of room
    if math.isinf(diff):
        raise OverflowError("range of {!r} and {!r} overflows a float".format(hi, lo))
    return diff


def float_spacing(x):
    """The gap between x and the next larger float, in the units of x.

    Shows how fine the measurement grid is at a given size. Below 2**53 the
    gap is at most 1, so every integer fits. At 2**53 it becomes 2.

    Inputs:      x  an int or float the v0.1 contract accepts.
    Outputs:     float, math.ulp(abs(x)).
    Assumptions: IEEE 754 double precision, which is what Python float is.
    Missing:     not handled. Pass a present value.
    Errors:      ContractError if x breaks the v0.1 contract (bool, str, inf,
                 abs(n) > 2**53 and the other refused types). ValueError if x is nan.
    Example:
        >>> float_spacing(1.0)
        2.220446049250313e-16
        >>> float_spacing(2**53)
        2.0
    """
    _validate(x)
    x = float(x)
    if math.isnan(x):
        raise ValueError("float_spacing needs a present value, got nan")
    return math.ulp(abs(x))
