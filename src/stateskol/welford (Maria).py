"""Welford's online variance (Welford, 1962, Technometrics 4(3):419-420)."""
from __future__ import annotations

import math
from typing import Iterable, NamedTuple


class WelfordResult(NamedTuple):
    count: int
    mean: float
    variance: float  # sample variance (n - 1 denominator)
    std: float
    dropped: int  # number of missing values (None / NaN) dropped


def welford(data: Iterable[float]) -> WelfordResult:
    """Single-pass count, mean, sample variance and sample std.

    Inputs
        data: any iterable of real numbers. Missing values (None, float NaN)
        are dropped and counted in ``dropped``; nothing is filled in.
    Outputs
        WelfordResult(count, mean, variance, std, dropped).
    Parameterization
        Sample variance, denominator n - 1 (like numpy ddof=1).
    Assumptions
        Values are finite real numbers; bool and non-numbers are invalid.
    Errors
        ValueError: no valid values (empty / all missing), or an infinite
        value. TypeError: a non-numeric value (e.g. a string, a bool).
        A single value returns variance = std = 0.0 (documented choice:
        no spread observed; the n - 1 estimate is undefined).
    Example
        >>> r = welford([2, 4, 4, 4, 5, 5, 7, 9])
        >>> r.count, r.mean
        (8, 5.0)
        >>> round(r.variance, 6)
        4.571429
    """
    # --- WELFORD BLOCK: recurrences (1)-(3) from the paper ---
    n = 0
    mean = 0.0
    m2 = 0.0  # S_n = sum (x_i - mean_n)^2
    dropped = 0
    for x in data:
        if x is None:
            dropped += 1
            continue
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError(f"invalid value: {x!r}")
        if math.isnan(x):
            dropped += 1
            continue
        if math.isinf(x):
            raise ValueError(f"infinite value: {x!r}")
        n += 1
        delta = x - mean          # x_n - m_(n-1)
        mean += delta / n         # m_n = m_(n-1) + (x_n - m_(n-1)) / n
        m2 += delta * (x - mean)  # S_n = S_(n-1) + (n-1)/n * delta^2
    # --- END WELFORD BLOCK ---
    if n == 0:
        raise ValueError("no valid values")
    var = m2 / (n - 1) if n > 1 else 0.0
    return WelfordResult(n, mean, var, math.sqrt(var), dropped)
