"""stateskol: statistics in pure Python, one tested function at a time.

The package imports the standard library and nothing else. Reference
libraries belong in tests and in examples/reference_check.py.

Week 2 publishes the data contract. Week 3 Core B adds the spread summaries:
``quantile``, ``iqr``, ``variance``, ``stdev`` and ``coefficient_variation``,
plus ``DomainError`` and ``UnsupportedRuleError``. Center (mean, median, mode)
belongs to Core A and is not here.
"""

from stateskol.descriptive import (
    ASSUMPTION,
    DDOFS,
    DOCSTRING_SHAPE,
    METHODS,
    POLICIES,
    as_numeric,
    coefficient_variation,
    count,
    iqr,
    quantile,
    stdev,
    variance,
)
from stateskol.errors import (
    ContractError,
    DomainError,
    EmptyDataError,
    UnknownPolicyError,
    UnsupportedRuleError,
)

__all__ = [
    "ASSUMPTION",
    "DDOFS",
    "DOCSTRING_SHAPE",
    "METHODS",
    "POLICIES",
    "ContractError",
    "DomainError",
    "EmptyDataError",
    "UnknownPolicyError",
    "UnsupportedRuleError",
    "as_numeric",
    "coefficient_variation",
    "count",
    "iqr",
    "quantile",
    "stdev",
    "variance",
]
