"""Spread of a data set: input contract, quantile, IQR, sample variance and std.

Standard library only. Follows Ross, Introduction to Probability and
Statistics for Engineers and Scientists, 6th ed., sections 2.3.2 and 2.3.3,
and computes the variance with Welford (1962), Formula I.

Input contract (shared by every function here)
    Data is any iterable of real numbers: int, float, fractions.Fraction and
    numpy int/float scalars. Each value is turned into a float.
    Missing values are None and NaN. They are dropped and counted, never
    filled in. ``clean`` returns that count and ``spread`` reports it.
    Anything else fails fast at the first bad value, with its index:
    bool, str, complex, Decimal and other non-real values raise TypeError,
    +inf, -inf and integers too big for a float raise ValueError.
    A str, bytes or mapping passed as the whole data set raises TypeError.
    No valid values left after dropping missing ones raises ValueError.
"""

import math
import numbers
from collections import namedtuple
from collections.abc import Mapping

SpreadResult = namedtuple(
    "SpreadResult",
    ["count", "dropped", "variance", "std", "q1", "median", "q3", "iqr"],
)


def clean(data):
    """Apply the input contract and return ``(values, dropped)``.

    Inputs
        data: iterable of real numbers, read once.
    Outputs
        values: list of floats in the original order, missing values removed.
        dropped: how many None or NaN values were removed.
    Errors
        TypeError for a non-iterable, str, bytes, mapping, or any non-real
        or bool value. ValueError for an infinite or too-large value, or when
        no valid values are left.

    >>> clean([3, None, 1.5, float("nan")])
    ([3.0, 1.5], 2)
    >>> clean([1, True])
    Traceback (most recent call last):
        ...
    TypeError: value at index 1 is not a number: True (bool)
    """
    if isinstance(data, (str, bytes, bytearray)):
        raise TypeError(f"data must be an iterable of numbers, not {type(data).__name__}")
    if isinstance(data, Mapping):
        raise TypeError("data must be an iterable of numbers, not a mapping")
    try:
        items = iter(data)
    except TypeError:
        raise TypeError(f"data must be an iterable of numbers, got {type(data).__name__}") from None

    values = []
    dropped = 0
    for i, v in enumerate(items):
        if v is None:
            dropped += 1
            continue
        # bool is an int in Python, but it is not data
        if isinstance(v, bool) or not isinstance(v, numbers.Real):
            raise TypeError(f"value at index {i} is not a number: {v!r} ({type(v).__name__})")
        try:
            x = float(v)
        except OverflowError:
            raise ValueError(f"value at index {i} is too big to fit in a float") from None
        if math.isnan(x):
            dropped += 1
            continue
        if math.isinf(x):
            raise ValueError(f"value at index {i} is infinite: {v!r}")
        values.append(x)

    if not values:
        raise ValueError(f"no valid values (dropped {dropped} missing)")
    return values, dropped


def sample_variance(data):
    """Sample variance s^2 = sum((x - mean)^2) / (n - 1), Ross 2.3.2.

    Computed in one pass with Welford's Formula I, so data with a large mean
    and a small spread keeps its digits. The naive formula
    sum(x^2) - n*mean^2 gives 0 instead of 30 on 1e9 + [4, 7, 13, 16].

    Inputs
        data: iterable of real numbers, see the module input contract.
    Outputs
        float, the sample variance (divisor n - 1, numpy ddof=1).
    Assumptions
        Values are finite floats. Order only changes the last few bits.
    Errors
        Everything from ``clean``, plus ValueError when fewer than two valid
        values are left, because n - 1 would be 0.

    >>> sample_variance([3, 4, 6, 7, 10])
    7.5
    >>> sample_variance([5, 5, 5])
    0.0
    """
    values, _ = clean(data)
    if len(values) < 2:
        raise ValueError("sample variance needs at least 2 values")

    n = 0
    m = 0.0  # running mean
    s = 0.0  # corrected sum of squares
    for x in values:
        n += 1
        d = x - m  # distance from the mean of the earlier values
        s += (n - 1) / n * d * d  # Welford Formula I
        m += d / n
    return s / (n - 1)


def sample_std(data):
    """Sample standard deviation s = sqrt(sample_variance(data)), Ross 2.3.2.

    Same inputs, assumptions and errors as ``sample_variance``. The result is
    in the same units as the data.

    >>> sample_std([2, 4, 4, 4, 5, 5, 7, 9]) == (32 / 7) ** 0.5
    True
    """
    return math.sqrt(sample_variance(data))


def _sorted_quantile(xs, p):
    # xs is already sorted and non-empty
    n = len(xs)
    k = n * p
    r = round(k)
    if abs(k - r) < 1e-9:
        # np is a whole number: average positions np and np + 1
        if r == 0:
            return xs[0]
        if r >= n:
            return xs[-1]
        return (xs[r - 1] + xs[r]) / 2
    # np is not whole: the value at position ceil(np)
    return xs[math.ceil(k) - 1]


def quantile(data, p):
    """Sample 100p percentile, using Ross's rule from section 2.3.3.

    Method: sort the data. If n*p is not a whole number, return the value at
    position ceil(n*p). If it is, return the average of the values at
    positions n*p and n*p + 1 (positions start at 1). p = 0 gives the
    minimum and p = 1 the maximum. This is numpy's
    ``method="averaged_inverted_cdf"`` (Hyndman and Fan type 2), not numpy's
    default linear method.

    Inputs
        data: iterable of real numbers, see the module input contract.
        p: real number with 0 <= p <= 1.
    Outputs
        float, always one of the data values or the average of two of them.
    Errors
        Everything from ``clean``, TypeError if p is not a real number,
        ValueError if p is outside [0, 1] or NaN.

    >>> quantile([1, 2, 3, 4, 5], 0.5)
    3.0
    >>> quantile([1, 2, 3, 4], 0.5)
    2.5
    >>> quantile([10, 20, 30, 40, 50], 0.1)
    10.0
    """
    if isinstance(p, bool) or not isinstance(p, numbers.Real):
        raise TypeError(f"p must be a number, got {type(p).__name__}")
    p = float(p)
    if not 0 <= p <= 1:
        raise ValueError(f"p must be between 0 and 1, got {p}")
    values, _ = clean(data)
    return _sorted_quantile(sorted(values), p)


def iqr(data):
    """Interquartile range Q3 - Q1, with quartiles from ``quantile``.

    Ross 2.3.3: the length of the box in a box plot. Constant data gives 0.0.
    Same inputs and errors as ``quantile``.

    >>> iqr([1, 2, 3, 4, 5, 6, 7, 8])
    4.0
    """
    xs = sorted(clean(data)[0])
    return _sorted_quantile(xs, 0.75) - _sorted_quantile(xs, 0.25)


def spread(data):
    """All spread numbers at once, with the dropped count.

    Reads and cleans the data once. Use this when you need to report how many
    missing values were dropped.

    Outputs
        SpreadResult(count, dropped, variance, std, q1, median, q3, iqr).
        With a single valid value, variance and std are NaN while the
        quartiles are that value. The single functions raise instead.
    Errors
        Everything from ``clean``.

    >>> r = spread([3, 4, None, 6, 7, 10])
    >>> r.count, r.dropped, r.variance, r.median
    (5, 1, 7.5, 6.0)
    """
    values, dropped = clean(data)
    xs = sorted(values)
    if len(values) >= 2:
        var = sample_variance(values)
        std = math.sqrt(var)
    else:
        var = std = float("nan")
    q1 = _sorted_quantile(xs, 0.25)
    q3 = _sorted_quantile(xs, 0.75)
    return SpreadResult(len(values), dropped, var, std, q1, _sorted_quantile(xs, 0.5), q3, q3 - q1)
