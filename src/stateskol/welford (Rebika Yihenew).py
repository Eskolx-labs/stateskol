"""Welford's online algorithm for sample mean and variance.

Author: Rebika Yihenew
Reference: Welford, B. P. (1962). Note on a method for calculating corrected
sums of squares and products. Technometrics, 4(3), 419-420.

The recursion implemented here is the paper's own: identity (1) for the running
mean m_n and Formula I for the corrected sum of squares S_n,

    S_n = S_(n-1) + ((n - 1) / n) * (x_n - m_(n-1))**2.

Standard library only: no numpy, no ``statistics``, no library variance.
"""

import math
import numbers
from typing import NamedTuple


class WelfordResult(NamedTuple):
    """Result of :func:`welford`."""

    count: int
    mean: float
    variance: float
    std: float
    n_dropped: int


def welford(data):
    """Online sample statistics of ``data`` in a single pass (Welford, 1962).

    Computes the count, mean, sample variance and sample standard deviation
    without a library variance or standard-deviation routine and without
    storing the data.

    Method
    ------
    Notation follows Welford (1962): ``m`` is the running mean m_n and ``S``
    is the corrected sum of squares S_n = sum((x_i - m_n)**2). For each new
    value x_n, with n values seen so far,

    * Formula I:    S_n = S_(n-1) + ((n - 1) / n) * (x_n - m_(n-1))**2
    * identity (1): m_n = ((n - 1) / n) * m_(n-1) + x_n / n

    Identity (1) is evaluated in its algebraically identical form
    ``m_n = m_(n-1) + (x_n - m_(n-1)) / n``. In floating point this keeps
    constant data exactly constant (variance exactly 0.0), which the form
    ``((n - 1) / n) * m + x / n`` does not. The sample variance is
    S_n / (n - 1); the paper itself defines only S_n.

    Parameters
    ----------
    data : iterable of real numbers
        Any iterable (list, tuple, generator, array). It is read exactly once.
        Accepted values are ``int``, ``float`` and other ``numbers.Real``;
        ``bool`` is rejected. This function has no other parameters; the
        variance is always the *sample* variance (divisor n - 1).

    Returns
    -------
    WelfordResult
        Named tuple ``(count, mean, variance, std, n_dropped)``:

        * count     -- number of valid values used
        * mean      -- arithmetic mean of the valid values
        * variance  -- sample variance, S_n / (count - 1)
        * std       -- sample standard deviation, sqrt(variance)
        * n_dropped -- number of missing values that were dropped

    Missing-value rule
    ------------------
    ``None`` and ``float('nan')`` are missing. They are dropped, never
    filled, and their number is reported in ``n_dropped``.

    Raises
    ------
    TypeError
        If ``data`` is not an iterable (or is a ``str``/``bytes``), or if an
        element is not a real number (e.g. a string or a ``bool``).
    ValueError
        If an element is infinite, or if fewer than two valid values remain
        (empty input, all values missing, or a single value, since the
        sample variance divides by n - 1).

    Assumptions
    -----------
    Values are finite, and the sums involved do not overflow a float.
    Constant data is valid and gives variance 0.0.

    Examples
    --------
    >>> welford([2, 4, 6])
    WelfordResult(count=3, mean=4.0, variance=4.0, std=2.0, n_dropped=0)
    >>> welford([2, None, 4, float("nan"), 6]).n_dropped
    2
    >>> welford([5, 5, 5]).variance
    0.0

    References
    ----------
    Welford, B. P. (1962). Note on a method for calculating corrected sums
    of squares and products. Technometrics, 4(3), 419-420.
    """
    if isinstance(data, (str, bytes)):
        raise TypeError("data must be an iterable of numbers, not str/bytes")
    try:
        iterator = iter(data)
    except TypeError:
        raise TypeError(
            f"data must be an iterable of numbers, got {type(data).__name__}"
        ) from None

    n = 0  # number of valid values seen so far
    m = 0.0  # running mean m_n
    S = 0.0  # corrected sum of squares S_n
    n_dropped = 0

    for position, x in enumerate(iterator):
        # --- 1. validate: drop missing, fail fast on invalid ---------------
        if x is None:
            n_dropped += 1
            continue
        if isinstance(x, bool) or not isinstance(x, numbers.Real):
            raise TypeError(
                f"element at position {position} is not a real number: "
                f"{x!r} ({type(x).__name__})"
            )
        try:
            value = float(x)
        except OverflowError:
            raise ValueError(
                f"element at position {position} is too large for a float"
            ) from None
        if math.isnan(value):
            n_dropped += 1
            continue
        if math.isinf(value):
            raise ValueError(f"element at position {position} is infinite")

        # --- 2. BEGIN WELFORD CORE (Welford 1962: Formula I, identity (1)) --
        n += 1
        dev = value - m  # x_n - m_(n-1), deviation from the mean of the previous values
        S += (n - 1) / n * dev * dev  # Formula I
        m += dev / n  # identity (1): m_n = m_(n-1) + (x_n - m_(n-1)) / n
        # --- END WELFORD CORE ----------------------------------------------

    # --- 3. finish ---------------------------------------------------------
    if n < 2:
        raise ValueError(
            f"need at least 2 valid values for a sample variance, got {n} "
            f"({n_dropped} missing value(s) dropped)"
        )
    variance = S / (n - 1)
    return WelfordResult(n, m, variance, math.sqrt(variance), n_dropped)