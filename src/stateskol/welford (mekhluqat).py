"""Welford's online mean and sample variance, on the standard library only."""

import math
from collections import namedtuple

WelfordResult = namedtuple(
    "WelfordResult", ["count", "mean", "variance", "std", "dropped"]
)


# --- begin: Welford (1962) online variance ---
def welford(data):
    """Compute count, mean, sample variance and sample std in one pass.

    Uses Welford's (1962) update, which keeps a running mean and a running
    sum of squared deviations (M2) instead of summing squares and subtracting.

    Inputs
        data: any iterable (list, tuple, generator) of plain ``int`` or
            ``float`` values. It is read exactly once.

    Outputs
        A ``WelfordResult`` named tuple, which also unpacks as five values:
        ``count`` (values used), ``mean``, ``variance`` (sample, divides by
        n - 1), ``std`` (square root of variance) and ``dropped`` (number of
        missing values skipped).

    Parameterization
        The variance is always the sample variance (ddof = 1). There is no
        option for the population variance.

    Assumptions
        Values are finite real numbers. Numpy scalar integers are not
        accepted; convert them with ``int()`` first. Plain ``float`` values
        (including numpy floats, which subclass ``float``) are accepted.

    Missing-value rule
        ``None`` and ``float("nan")`` are dropped, never filled in, and
        counted in ``dropped``. They do not enter count, mean or variance.

    Boundary cases
        No usable values: count 0; mean, variance and std are ``nan``.
        One value: count 1, mean is that value; variance and std are ``nan``,
        because n - 1 is zero.
        Constant values: variance and std are 0.0.

    Errors
        TypeError: ``data`` is not iterable, or is a ``str``, ``bytes`` or
            ``bytearray``; or a value is a ``str``, a ``bool`` or any other
            non-numeric type.
        ValueError: a value is ``inf`` or ``-inf``, or an integer too large
            to convert to a float.

    Examples
        >>> welford([2, 4, 6, 8])
        WelfordResult(count=4, mean=5.0, variance=6.666666666666667, std=2.581988897471611, dropped=0)
        >>> welford([2, 4, None, 6, 8]).dropped
        1
        >>> welford([5, 5, 5]).variance
        0.0
        >>> welford([3]).variance
        nan
        >>> welford([1, "a"])
        Traceback (most recent call last):
            ...
        TypeError: invalid value: 'a'
    """
    if isinstance(data, (str, bytes, bytearray)):
        raise TypeError("data must be an iterable of numbers, not str/bytes")
    try:
        iterator = iter(data)
    except TypeError:
        raise TypeError(
            f"data must be an iterable of numbers, got {type(data).__name__}"
        ) from None

    n = 0
    mean = 0.0
    m2 = 0.0
    dropped = 0

    for x in iterator:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            dropped += 1
            continue
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError(f"invalid value: {x!r}")
        try:
            infinite = math.isinf(x)
        except OverflowError:
            raise ValueError("integer too large to convert to a float") from None
        if infinite:
            raise ValueError(f"infinite value: {x!r}")

        n += 1
        delta = x - mean
        mean += delta / n
        delta2 = x - mean
        m2 += delta * delta2

    nan = float("nan")
    if n == 0:
        return WelfordResult(0, nan, nan, nan, dropped)
    if n == 1:
        return WelfordResult(1, mean, nan, nan, dropped)

    variance = m2 / (n - 1)
    return WelfordResult(n, mean, variance, math.sqrt(variance), dropped)
# --- end: Welford (1962) online variance ---
