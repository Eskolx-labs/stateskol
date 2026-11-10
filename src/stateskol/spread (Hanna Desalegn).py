"""Spread statistics: the input contract, quantiles, IQR, sample variance and std.

Pure standard library. The math follows Ross 6th ed., sections 2.3.2 and
2.3.3, and the variance uses Welford's online algorithm (1962), Formula I.

Input contract (shared by every function here):
    * data is any iterable of real numbers - int, float, Fraction, numpy
      scalars; each value is converted to float.
    * Missing values (None, NaN) are dropped and counted, never filled in.
      ``clean`` returns that count; ``spread`` reports it.
    * Anything else fails fast at the offending index: bool, str, complex,
      Decimal and other non-reals raise TypeError; +-inf or an int too big
      for a float raise ValueError. A str/bytes/mapping as the whole data set
      also raises TypeError.
    * If nothing valid remains after dropping, ValueError.
"""

import math
import numbers
from collections import namedtuple
from collections.abc import Mapping
from decimal import ROUND_CEILING, Decimal

SpreadResult = namedtuple(
    "SpreadResult",
    ["count", "dropped", "variance", "std", "q1", "median", "q3", "iqr"],
)


def clean(data):
    """Validate ``data`` and return ``(values, dropped)``.

    Inputs:  data - iterable of real numbers, read once.
    Outputs: values - list of floats, missing values removed, order kept;
             dropped - how many None/NaN were removed.
    Errors:  TypeError for a non-iterable, a str/bytes/mapping, or any
             non-real or bool value. ValueError for an infinite or
             too-large value, or when no valid values remain.

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

    values, dropped = [], 0
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


def _variance_from_values(values):
    # Welford, Formula I: S += (n-1)/n * (x - mean)^2, then mean += (x - mean)/n.
    # Updating s before m is what makes it stable on large-mean data.
    n, mean, s = 0, 0.0, 0.0
    for x in values:
        n += 1
        d = x - mean
        s += (n - 1) / n * d * d
        mean += d / n
    return s / (n - 1)


def sample_variance(data):
    """Sample variance s^2 = sum((x - mean)^2) / (n - 1), Ross 2.3.2.

    One pass with Welford's Formula I, so data with a large mean and a small
    spread keeps its digits. The shortcut sum(x^2) - n*mean^2 returns 0
    instead of 30 on 1e9 + [4, 7, 13, 16].

    Inputs:  data - see the module contract.
    Outputs: float, with divisor n - 1 (numpy ddof=1).
    Assumptions: values are finite floats; order shifts only the last bits.
    Errors:  everything from ``clean``, plus ValueError with fewer than two
             valid values (n - 1 would be 0).

    >>> sample_variance([3, 4, 6, 7, 10])
    7.5
    >>> sample_variance([5, 5, 5])
    0.0
    """
    values, _ = clean(data)
    if len(values) < 2:
        raise ValueError("sample variance needs at least 2 values")
    return _variance_from_values(values)


def sample_std(data):
    """Sample standard deviation s = sqrt(sample_variance(data)), Ross 2.3.2.

    Same inputs and errors as ``sample_variance``; the result is in the same
    units as the data.

    >>> sample_std([2, 4, 4, 4, 5, 5, 7, 9]) == (32 / 7) ** 0.5
    True
    """
    return math.sqrt(sample_variance(data))


def _sorted_quantile(xs, p):
    """Apply Ross 2.3.3 to an already sorted list."""
    n = len(xs)
    k = Decimal(str(p)) * n

    if p == 0:
        return xs[0]
    if p == 1:
        return xs[-1]

    # If n*p is an integer, average the two surrounding values.
    if k == k.to_integral_value():
        r = int(k)
        return (xs[r - 1] + xs[r]) / 2

    # Otherwise, select the value at position ceil(n*p).
    position = int(k.to_integral_value(rounding=ROUND_CEILING))
    return xs[position - 1]


def quantile(data, p):
    """Sample 100p percentile with Ross's rule (section 2.3.3).

    Sort the data. If n*p is not whole, take the value at position ceil(n*p).
    If it is, average the values at positions n*p and n*p + 1 (counting from
    1). p = 0 gives the min, p = 1 the max. n*p is worked out in decimal,
    so 25 * 0.28 counts as exactly 7.

    This is numpy's ``method="averaged_inverted_cdf"`` (Hyndman-Fan type 2),
    not numpy's default linear method, with one difference: numpy works out
    n*p in float, where 25 * 0.28 = 7.000000000000001, so it takes the 8th
    value where Ross averages the 7th and 8th. Here we follow Ross.

    Inputs:  data - see the module contract.
             p - real number in [0, 1].
    Outputs: float, always a data value or the average of two.
    Errors:  everything from ``clean``; TypeError if p is not a real number;
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
    """Interquartile range Q3 - Q1, quartiles from ``quantile`` (Ross 2.3.3).

    The length of the box in a box plot; constant data gives 0.0.
    Same inputs and errors as ``quantile``.

    >>> iqr([1, 2, 3, 4, 5, 6, 7, 8])
    4.0
    """
    xs = sorted(clean(data)[0])
    return _sorted_quantile(xs, 0.75) - _sorted_quantile(xs, 0.25)


def spread(data):
    """Every spread number at once, with the dropped count.

    Cleans the data once and derives the rest from that, so use this when you
    also need to report how many missing values were dropped.

    Outputs: SpreadResult(count, dropped, variance, std, q1, median, q3, iqr).
             With a single valid value, variance and std are NaN (the single
             functions raise instead) and the quartiles equal that value.
    Errors:  everything from ``clean``.

    >>> r = spread([3, 4, None, 6, 7, 10])
    >>> r.count, r.dropped, r.variance, r.median
    (5, 1, 7.5, 6.0)
    """
    values, dropped = clean(data)
    xs = sorted(values)
    if len(values) >= 2:
        var = _variance_from_values(values)
        std = math.sqrt(var)
    else:
        var = std = float("nan")
    q1 = _sorted_quantile(xs, 0.25)
    q3 = _sorted_quantile(xs, 0.75)
    return SpreadResult(len(values), dropped, var, std, q1,
                        _sorted_quantile(xs, 0.5), q3, q3 - q1)