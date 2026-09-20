"""Stateskol: descriptive statistics in pure Python, rebuilt from scratch.

One module holds week 1: input contract, missing data rule, count, min, max,
range, center, spread, and tables. Each function block names its owner. Edit
only your own blocks. If you need a change in someone else's block, leave a
review comment on their PR instead of touching it.
"""

from stateskol.descriptive import (
    apply_missing,
    count,
    data_range,
    frequency_table,
    histogram_counts,
    iqr,
    max_,
    mean,
    median,
    min_,
    mode,
    quantile,
    require_nonempty,
    std,
    to_float_list,
    variance,
)

__all__ = [
    "apply_missing",
    "count",
    "data_range",
    "frequency_table",
    "histogram_counts",
    "iqr",
    "max_",
    "mean",
    "median",
    "min_",
    "mode",
    "quantile",
    "require_nonempty",
    "std",
    "to_float_list",
    "variance",
]
