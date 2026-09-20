"""Spread: quantiles, IQR, sample variance, sample std. Owner: Robel.

Ross Ch.2.2 to Ch.2.4. Robel implements these in week 1. Variance uses the
sample denominator n minus 1. Quantiles use the linear interpolation method
and the method name goes in the docstring once Robel picks it, so the
reference comparison can match the same method exactly.
"""

from stateskol._missing import apply_missing
from stateskol._validate import require_nonempty, to_float_list


def quantile(values, q: float, policy: str = "drop") -> float:
    raise NotImplementedError("Robel implements quantile in week 1")


def iqr(values, policy: str = "drop") -> float:
    raise NotImplementedError("Robel implements iqr in week 1")


def variance(values, policy: str = "drop") -> float:
    raise NotImplementedError("Robel implements sample variance in week 1")


def std(values, policy: str = "drop") -> float:
    raise NotImplementedError("Robel implements sample std in week 1")
