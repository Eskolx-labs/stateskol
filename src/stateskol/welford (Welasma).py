"""
Welford's online variance.

Single-pass computation of count, mean, sample variance, and sample
standard deviation, following Welford (1962).

Missing values (None and NaN) are dropped.
"""

import math


def welford(data):
    """
    Compute count, sample mean, sample variance, and sample standard
    deviation in a single pass.

    Parameters
    ----------
    data : iterable of numbers
        Numeric values. None and NaN are treated as missing and
        dropped before calculation.

    Returns
    -------
    (count, mean, variance, std_dev) : tuple[int, float, float, float]
        variance is the sample variance (denominator n - 1).
        std_dev is sqrt(variance).

    Raises
    ------
    ValueError
        If fewer than two usable values remain after dropping missing
        values.
    TypeError
        If a value is neither a real number nor None.

    Examples
    --------
    >>> welford([5, 7, 4, 10])
    (4, 6.5, 7.0, 2.6457513110645907)
    """
    n = 0
    mean = 0.0
    S = 0.0

    for x in data:
        if x is None:
            continue
        if isinstance(x, float) and math.isnan(x):
            continue
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError(
                f"welford expects real numbers, got {type(x).__name__}"
            )

        n += 1
        delta = x - mean
        mean += delta / n
        S += delta * (x - mean)

    if n < 2:
        raise ValueError(
            f"welford needs at least two usable values; got {n}"
        )

    variance = S / (n - 1)
    return n, mean, variance, math.sqrt(variance)


if __name__ == "__main__":
    print(welford([5, 7, 4, 10]))