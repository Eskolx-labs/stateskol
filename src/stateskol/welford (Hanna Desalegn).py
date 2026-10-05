"""Calculate sample variance online using Welford's algorithm."""

import math
from collections import namedtuple


WelfordResult = namedtuple(
    "WelfordResult",
    ["count", "mean", "variance", "std", "dropped"],
)


def welford(data):
    """Calculate sample statistics using Welford's online algorithm.

    Parameters
    ----------
    data : iterable
        An iterable of Python integers and floats. The iterable is
        consumed once. None and NaN values are treated as missing.

    Returns
    -------
    WelfordResult
        A result containing:
        - count: number of valid observations
        - mean: arithmetic mean of valid observations
        - variance: sample variance using denominator (count - 1)
        - std: sample standard deviation
        - dropped: number of missing observations skipped

    Parameterization
    ----------------
    Calculates sample statistics with ddof=1.

    Assumptions
    -----------
    Observations are Python int or float values. Boolean values are
    excluded, and valid observations must be finite.

    Missing values
    --------------
    None and NaN are skipped and counted in `dropped`.

    Boundary cases
    --------------
    Empty input or input containing only missing values returns count 0
    and NaN for mean, variance, and std.

    One valid observation returns its mean and NaN for variance and std.
    Constant observations have zero variance and standard deviation.

    Errors
    ------
    TypeError
        Raised for observations that are not int or float, or are bool.

    ValueError
        Raised for positive or negative infinity.

    Examples
    --------
    >>> welford([2, 4, 6, 8])
    WelfordResult(count=4, mean=5.0, variance=6.666666666666667, std=2.581988897471611, dropped=0)

    >>> welford([2, 4, None, 6, 8]).dropped
    1

    >>> welford([2, 4, float("nan"), 6, 8]).count
    4

    >>> welford([5, 5, 5]).variance
    0.0

    >>> welford([3]).variance
    nan

    >>> welford([])
    WelfordResult(count=0, mean=nan, variance=nan, std=nan, dropped=0)

    >>> welford([1, "invalid"])
    Traceback (most recent call last):
        ...
    TypeError: invalid observation: 'invalid'
    """
    count = 0
    mean = 0.0
    m2 = 0.0
    dropped = 0

    for value in data:
        if value is None:
            dropped += 1
            continue

        if isinstance(value, float) and math.isnan(value):
            dropped += 1
            continue

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"invalid observation: {value!r}")

        if isinstance(value, float) and math.isinf(value):
            raise ValueError(f"infinite observation: {value!r}")

        count += 1

        delta = value - mean
        mean += delta / count

        delta2 = value - mean
        m2 += delta * delta2

    nan = float("nan")

    if count == 0:
        return WelfordResult(0, nan, nan, nan, dropped)

    if count == 1:
        return WelfordResult(1, mean, nan, nan, dropped)

    variance = m2 / (count - 1)
    std = math.sqrt(variance)

    return WelfordResult(count, mean, variance, std, dropped)