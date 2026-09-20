"""Numeric input contract. Owner: Kaleb.

Every public function in this package takes its data through to_float_list
first, then calls require_nonempty where an empty input has no meaning.
Kaleb finalizes this file in week 1. Others build on it, they do not fork it.
"""

import math
from typing import Iterable


def to_float_list(values: Iterable[object]) -> list:
    """Coerce an iterable of numbers to a plain list of floats.

    Inputs: any iterable of int or float values. None and NaN pass through
    untouched here, the missing data policy in _missing decides their fate.
    Strings, bools, complex numbers, and other types fail fast with TypeError.
    Infinities fail with ValueError, they are not data.

    Outputs: a new list of floats, same order as the input.
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
