"""descriptive.py: Core A only (count, minimum). Self-contained.

"""

import math


# --- BEGIN CORE A BLOCK: count, minimum (owner: yeabsira) ---

# ---- TEMPORARY: Core A's own copy of the contract rules ----------------
# The Contract lane's errors.py and as_numeric are not merged yet, so Core A
# carries a private version of the same rules and the same error names. When
# they land: delete this TEMPORARY section, add
#     from stateskol.errors import EmptyDataError
# at the top of the file, and in count and minimum replace _present_numbers(...)
# with as_numeric(...). The tests do not change (see tests/test_descriptive.py).
class EmptyDataError(ValueError):
    """No present values remain, so the summary is undefined."""


class InvalidTypeError(TypeError):
    """An input is not an int or float (bool, str, Decimal, ... rejected)."""


class InvalidValueError(ValueError):
    """Right type, unacceptable value (inf, abs(n) > 2**53)."""


_LIMIT = 2 ** 53


def _present_numbers(data):
    """Return the present values as a list of floats. None and NaN are
    dropped. Bad values raise. Reads the data exactly once."""
    values = []
    for x in data:
        if x is None:
            continue
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise InvalidTypeError("not an int or float: " + repr(x))
        if isinstance(x, float) and math.isnan(x):
            continue
        if isinstance(x, float) and math.isinf(x):
            raise InvalidValueError("infinite value is not allowed")
        if abs(x) > _LIMIT:
            raise InvalidValueError("abs(value) is above 2**53: " + repr(x))
        values.append(float(x))
    return values
# ---- END TEMPORARY -----------------------------------------------------

def count(data):
    """Count how many present (non-missing) values there are.

    Inputs
    ------
    data : any iterable (list, tuple, set, generator, ...) of numbers.
           int and float are accepted. A generator is read once.

    Outputs
    -------
    int. The number of present values. 0 for empty input.

    Parameterization
    ----------------
    None. The missing-value policy is "drop" (see below).

    Support
    -------
    Any iterable. The result is an int from 0 up to the length of the data.

    Missing-value rule
    ------------------
    None and NaN are missing. They are dropped and not counted. Nothing is
    filled in. Assumption made by dropping: the values are missing
    completely at random (MCAR). If you do not know that, the count of
    present values may not describe the whole sample. Unknown: the caller
    must state the mechanism. To see how many were dropped, use
    missing_report or audit.

    Errors
    ------
    The contract's errors:
    - InvalidTypeError  : a value is not an int or float (bool, str, Decimal,
      Fraction, ...).
    - InvalidValueError : right type, bad value (inf, -inf, abs(value) > 2**53).

    Examples
    --------
    >>> count([4, None, 2.5, float("nan"), 7])
    3
    >>> count([])
    0
    """
    values = _present_numbers(data)  # drops missing, rejects bad values
    return len(values)


def minimum(data):
    """Return the smallest present (non-missing) value.

    Inputs
    ------
    data : any iterable of numbers (int or float). A generator is read once.

    Outputs
    -------
    float. The smallest present value. An int is returned as a float,
    because the contract converts every accepted number to float.

    Parameterization
    ----------------
    None. The missing-value policy is "drop".

    Support
    -------
    Finite numbers with abs(value) <= 2**53, so the float conversion is exact.

    Method
    ------
    One pass. Keep the smallest value seen so far; replace it whenever a
    smaller value comes. No sorting, no arithmetic, so the result is always
    one of the input values, exactly.

    Missing-value rule
    ------------------
    None and NaN are dropped first, never filled in. Assumption made by
    dropping: MCAR (missing completely at random). If the values are not
    missing at random, the minimum of the present values can be wrong about
    the whole sample. Unknown: the caller must state the mechanism.

    Errors
    ------
    - EmptyDataError : no present values (empty input, or everything
      missing). This is a finding, not a number, so we do not invent one.
    - InvalidTypeError  : bool, str, Decimal, Fraction, ... in the data.
    - InvalidValueError : inf, -inf, or abs(value) > 2**53 in the data.

    Examples
    --------
    >>> minimum([4, None, 2.5, float("nan"), 7])
    2.5
    >>> minimum([2, 4, 4, 4, 5, 5, 7, 9])
    2.0
    """
    values = _present_numbers(data)
    if len(values) == 0:
        raise EmptyDataError("minimum: no present values (empty or all missing)")

    smallest = values[0]
    for x in values:
        if x < smallest:
            smallest = x
    return smallest
# --- END CORE A BLOCK ---