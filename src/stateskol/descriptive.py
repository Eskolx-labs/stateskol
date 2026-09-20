"""Descriptive statistics in pure Python. Ross Ch.1 to Ch.2.4.

One module for the whole week. Ownership is by function block:

- Kaleb: contract, missing policy, quantile, iqr, variance, std
- Philimon: mean, median, mode, plus the Ross exercise solutions
- Robel: count, min, max, range, frequency_table, boundary pack
- Yoseph: histogram_counts and the bin rule
- Yonas: reference checks and the demo script, plus release notes

Blocks are marked below. Stay inside yours.
"""

import math
from typing import Iterable

# ----- Kaleb: input contract -----


def to_float_list(values: Iterable[object]) -> list:
    """Coerce an iterable of numbers to a plain list of floats.

    Strings, bools, complex numbers, and other non numeric types fail fast
    with TypeError. Infinities fail with ValueError. None and NaN pass
    through untouched here, the missing data policy below decides their fate.
    """
    if isinstance(values, (str, bytes)):
        raise TypeError("data must be an iterable of numbers, not a string")
    try:
        items = list(values)
    except TypeError:
        raise TypeError("data must be an iterable of numbers") from None
    out: list = []
    for v in items:
        if v is None:
            out.append(v)
            continue
        if isinstance(v, bool):
            raise TypeError("bools are not numeric data, got True/False")
        if isinstance(v, int):
            out.append(float(v))
        elif isinstance(v, float):
            out.append(v)
        else:
            raise TypeError("non numeric value in data: %r" % (v,))
    for v in out:
        if isinstance(v, float) and math.isinf(v):
            raise ValueError("infinite values are not accepted as data")
    return out


def require_nonempty(values: list, name: str = "data") -> list:
    """Raise ValueError when a function needs data and got none."""
    if len(values) == 0:
        raise ValueError("empty input: %s needs at least one value" % name)
    return values


# ----- Kaleb: missing data policy -----
# Team rule, locked Monday: drop None and NaN, report the dropped count,
# never silently fill anything in.


def apply_missing(values: list, policy: str = "drop") -> tuple:
    """Split contracted input into clean data plus a dropped count.

    Only "drop" and "raise" exist. "drop" removes None and NaN and returns
    how many went. "raise" throws ValueError on the first one instead.
    """
    if policy not in ("drop", "raise"):
        raise ValueError("unknown missing data policy: %r" % (policy,))
    clean: list = []
    dropped = 0
    for v in values:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            if policy == "raise":
                raise ValueError("missing value found under policy 'raise'")
            dropped += 1
            continue
        clean.append(v)
    return clean, dropped


# ----- Robel: basic summaries and frequencies -----


def count(values, policy: str = "drop") -> int:
    """Number of clean values after missing handling. Owner: Robel."""
    clean, _ = apply_missing(to_float_list(values), policy)
    return len(clean)


def min_(values, policy: str = "drop") -> float:
    """Smallest clean value. Raises ValueError on empty input. Owner: Robel."""
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    return min(clean)


def max_(values, policy: str = "drop") -> float:
    """Largest clean value. Raises ValueError on empty input. Owner: Robel."""
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    return max(clean)


def data_range(values, policy: str = "drop") -> float:
    """Max minus min. Zero for a single value, error for none. Owner: Robel."""
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    return max(clean) - min(clean)


def frequency_table(values, policy: str = "drop") -> dict:
    """Value to count mapping. Owner: Robel."""
    raise NotImplementedError("Robel implements frequency_table in week 1")


# ----- Philimon: center -----
# Philimon also solves every Ross Ch.2 exercise with these functions. The
# solutions live in his vault note, linked from his PR.


def mean(values, policy: str = "drop") -> float:
    """Arithmetic average. Owner: Philimon."""
    raise NotImplementedError("Philimon implements mean in week 1")


def median(values, policy: str = "drop") -> float:
    """Middle value, averaged pair for even counts. Owner: Philimon."""
    raise NotImplementedError("Philimon implements median in week 1")


def mode(values, policy: str = "drop") -> list:
    """All tied winners in sorted order. Owner: Philimon."""
    raise NotImplementedError("Philimon implements mode in week 1")


# ----- Kaleb: spread -----
# Variance uses the sample denominator n minus 1. The quantile method goes
# in the docstring once Kaleb picks it, so the reference check can match it.
# Kaleb also shows naive versus stable variance on real data (Welford).


def quantile(values, q: float, policy: str = "drop") -> float:
    """q-th quantile by linear interpolation. Owner: Kaleb."""
    raise NotImplementedError("Kaleb implements quantile in week 1")


def iqr(values, policy: str = "drop") -> float:
    """Interquartile range. Owner: Kaleb."""
    raise NotImplementedError("Kaleb implements iqr in week 1")


def variance(values, policy: str = "drop") -> float:
    """Sample variance, denominator n minus 1. Owner: Kaleb."""
    raise NotImplementedError("Kaleb implements sample variance in week 1")


def std(values, policy: str = "drop") -> float:
    """Sample standard deviation. Owner: Kaleb."""
    raise NotImplementedError("Kaleb implements sample std in week 1")


# ----- Yoseph: histograms -----
# The bin rule is the deliverable: Yoseph states it, documents it, and pins
# it with tests. Callers who want another rule pass explicit edges.


def histogram_counts(values, bins=10, policy: str = "drop") -> tuple:
    """Bin counts over the data range. Owner: Yoseph."""
    raise NotImplementedError("Yoseph implements histogram_counts in week 1")
