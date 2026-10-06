"""Welford's (1962) online mean and sample variance, standard library only.


Reference
    Welford, B. P. (1962). Note on a method for calculating corrected sums
    of squares and products. Technometrics, 4(3), 419-420.
    https://doi.org/10.1080/00401706.1962.10490022

The paper defines, for the first n values,

    m_n = (1/n) * sum_{i=1..n} x_i            (running mean)
    S_n = sum_{i=1..n} (x_i - m_n)**2         (corrected sum of squares)

and proves

    identity (1):  m_n = ((n - 1)/n) * m_(n-1) + x_n / n
    identity (3):  x_n - m_n = ((n - 1)/n) * (x_n - m_(n-1))
    Formula I:     S_n = S_(n-1) + ((n - 1)/n) * (x_n - m_(n-1))**2

The update in :func:`welford` uses Formula I and identity (1).
"""

import math
import numbers
from collections import namedtuple
from collections.abc import Mapping

WelfordResult = namedtuple(
    "WelfordResult",
    ["count", "mean", "variance", "std", "dropped"],
)


def welford(data):
    """Count, mean, sample variance and sample std of ``data`` in one pass.

    Implements Welford (1962): each value updates the running mean m and the
    corrected sum of squares S using only its deviation from the mean of the
    values before it, so nothing is stored and no large, nearly equal sums
    are subtracted.

    Inputs
    ------
    data : iterable of real numbers
        Any iterable (list, tuple, generator, numpy array). It is read
        exactly once. What counts as data: every element that is a
        ``numbers.Real`` -- Python ``int`` and ``float``, ``fractions.Fraction``
        and numpy integer/float scalars. Each is converted with ``float()``.
        ``bool`` is *not* data, even though Python treats it as an ``int``.

    Outputs
    -------
    WelfordResult
        Named tuple ``(count, mean, variance, std, dropped)``, all plain
        Python ``int``/``float``:

        * count    -- number of valid values used
        * mean     -- arithmetic mean m_n of the valid values
        * variance -- sample variance S_n / (count - 1)
        * std      -- sample standard deviation, sqrt(variance)
        * dropped  -- number of missing values skipped

    Parameterization
    ----------------
    Always the *sample* variance (divisor n - 1, numpy ``ddof=1``). There is
    no option for the population variance (divisor n); multiply by
    (count - 1) / count if you need it.

    Assumptions
    -----------
    * Values are finite and fit in a float64.
    * The order of the values does not matter mathematically; in floating
      point it changes only the last few bits.
    * Values far from zero compared to their spread lose digits: near 1e9
      a float64 only stores steps of about 1.2e-7, so with a spread of 1
      expect a relative error near 1e-8 (see
      ``examples/welford_reference (Hanna Desalegn).py``). The naive
      sum-of-squares formula loses every digit on the same data.

    Missing-value rule
    ------------------
    ``None`` and NaN (``float("nan")``, ``numpy.nan``, any float NaN) are
    missing. They are dropped, never filled in, and counted in ``dropped``.
    They do not enter count, mean or variance.

    Boundary cases
    --------------
    * Empty input, or only missing values: count 0, mean/variance/std NaN.
    * One valid value: count 1, mean is that value, variance/std NaN,
      because the sample variance divides by n - 1 = 0.
    * Constant values: variance and std are exactly 0.0.

    NaN (not an exception) is returned for too-few values on purpose: the
    mean is still defined at n = 1 and a stream with a short window should
    not crash. Callers must therefore check ``count`` before trusting
    ``variance``.

    Errors (raised immediately, at the first bad element)
    -----------------------------------------------------
    TypeError
        ``data`` is not iterable, is a ``str``/``bytes``/``bytearray``
        (characters and bytes are not numbers), or is a mapping (iterating
        it would silently use the keys); or an element is a ``bool``, a
        string, a complex number, a ``Decimal`` or any other non-real value.
        The message gives the index of the bad value.
    ValueError
        An element is +inf or -inf, or an integer too large for a float
        (e.g. ``10**400``). The message gives the index of the bad value.

    Examples
    --------
    >>> welford([2, 4, 6, 8])
    WelfordResult(count=4, mean=5.0, variance=6.666666666666667, std=2.581988897471611, dropped=0)
    >>> welford([2, 4, None, 6, 8, float("nan")]).dropped
    2
    >>> welford([5, 5, 5]).variance
    0.0
    >>> welford([3])
    WelfordResult(count=1, mean=3.0, variance=nan, std=nan, dropped=0)
    >>> welford([])
    WelfordResult(count=0, mean=nan, variance=nan, std=nan, dropped=0)
    >>> welford([1, "2"])
    Traceback (most recent call last):
        ...
    TypeError: value at index 1 is not a number: '2' (str)
    """
    if isinstance(data, (str, bytes, bytearray)):
        raise TypeError(
            f"data must be an iterable of numbers, not {type(data).__name__}"
        )
    if isinstance(data, Mapping):
        raise TypeError(
            "data must be an iterable of numbers, not a mapping "
            "(iterating a mapping yields its keys)"
        )
    try:
        observations = iter(data)
    except TypeError:
        raise TypeError(
            f"data must be an iterable of numbers, got {type(data).__name__}"
        ) from None

    n = 0  # number of valid values seen so far
    m = 0.0  # running mean m_n
    s = 0.0  # corrected sum of squares S_n
    dropped = 0

    for index, value in enumerate(observations):
        # skip missing values, stop at the first invalid one
        if value is None:
            dropped += 1
            continue
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise TypeError(
                f"value at index {index} is not a number: "
                f"{value!r} ({type(value).__name__})"
            )
        try:
            x = float(value)
        except OverflowError:
            raise ValueError(
                f"value at index {index} is too big to fit in a float"
            ) from None
        if math.isnan(x):
            dropped += 1
            continue
        if math.isinf(x):
            raise ValueError(
                f"value at index {index} is infinite: {value!r}"
            )

        # Welford update, Formula I from Welford (1962)
        n += 1
        d = x - m  # distance from the mean of the values before x
        s += (n - 1) / n * d * d  # Formula I: S_n = S_(n-1) + (n-1)/n * d**2
        m += d / n  # new mean, same as (n-1)/n * m + x/n in the paper
        # end of Welford update

    nan = float("nan")
    if n == 0:
        return WelfordResult(0, nan, nan, nan, dropped)
    if n == 1:
        return WelfordResult(1, m, nan, nan, dropped)

    variance = s / (n - 1)
    return WelfordResult(n, m, variance, math.sqrt(variance), dropped)