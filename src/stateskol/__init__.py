"""stateskol: descriptive statistics in pure Python (Week 1)."""

from __future__ import annotations

__version__ = "0.1.0"

from .descriptive import (
    MissingPolicy,
    is_missing,
    to_float_list,
    require_nonempty,
    apply_missing,
    prepare_data,
    clean_values,
    BoundaryCase,
    get_boundary_case,
    boundary_case_names,
    BOUNDARY_CASES,
    count,
    count_missing,
    min_,
    max_,
    data_range,
    frequency_table,
)

min = min_
max = max_
range = data_range

__all__ = [
    "__version__",
    "MissingPolicy",
    "is_missing",
    "to_float_list",
    "require_nonempty",
    "apply_missing",
    "prepare_data",
    "clean_values",
    "BoundaryCase",
    "get_boundary_case",
    "boundary_case_names",
    "BOUNDARY_CASES",
    "count",
    "count_missing",
    "min_",
    "max_",
    "data_range",
    "frequency_table",
    "min",
    "max",
    "range",
]