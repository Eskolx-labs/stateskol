"""Online mean and variance by Welford's method (Welford, 1962)."""
from math import isinf, isnan, sqrt
from typing import NamedTuple


class WelfordResult(NamedTuple):
    count: int
    mean: float
    variance: float
    std: float
    dropped: int


def welford(data, ddof=1):
    """Return count, mean, variance and standard deviation in one pass.

    Method: Welford (1962), formula I. For each new value x_n, with
    delta = x_n - m_(n-1):
        m_n = m_(n-1) + delta / n
        S_n = S_(n-1) + ((n - 1) / n) * delta**2
    Variance is S_n / (n - ddof). No value is stored or read twice.

    Parameters
    ----------
    data : iterable of int or float
        Any iterable, including a generator.
    ddof : int, default 1
        Delta degrees of freedom. 1 gives the sample variance, 0 the
        population variance. Same meaning as numpy's ddof.

    Returns
    -------
    WelfordResult
        Named tuple (count, mean, variance, std, dropped).
        count counts the values used, dropped the missing ones.

    Missing values
        None and NaN are dropped and counted in `dropped`. Nothing is
        filled in silently.

    Raises
    ------
    TypeError
        A value is not an int or float (strings, bools, etc.).
    ValueError
        A value is infinite; no valid values remain (empty input);
        count - ddof <= 0 (for example one value with ddof=1); or ddof
        is not a non-negative integer.

    Assumptions
        Values are real numbers, order does not matter, and floats
        follow IEEE 754 double precision.

    Examples
    --------
    >>> r = welford([2, 4, 4, 4, 5, 5, 7, 9])
    >>> r.count, r.mean
    (8, 5.0)
    >>> round(r.variance, 4), round(r.std, 4)
    (4.5714, 2.1381)
    >>> welford([1, None, float("nan"), 3]).dropped
    2
    >>> welford([5, 5, 5]).variance
    0.0
    """
    if isinstance(ddof, bool) or not isinstance(ddof, int) or ddof < 0:
        raise ValueError("ddof must be a non-negative integer")

    count = 0
    dropped = 0
    mean = 0.0
    s = 0.0  # corrected sum of squares, S_n in the paper

    for x in data:
        if x is None:
            dropped += 1
            continue
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError(f"invalid value {x!r}")
        if isnan(x):
            dropped += 1
            continue
        if isinf(x):
            raise ValueError("infinite value")

        # BEGIN WELFORD
        count += 1
        delta = x - mean
        mean += delta / count
        s += (count - 1) / count * delta * delta
        # END WELFORD

    if count == 0:
        raise ValueError("no valid values")
    if count - ddof <= 0:
        raise ValueError("not enough values for this ddof")

    variance = s / (count - ddof)
    return WelfordResult(count, mean, variance, sqrt(variance), dropped)



