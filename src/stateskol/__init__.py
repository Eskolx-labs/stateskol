"""stateskol: statistics in pure Python, one tested function at a time.

The package imports the standard library and nothing else. Reference libraries
belong in ``examples/*reference*.py``, which CI runs only after installing
them; no test in ``tests/`` imports one either.

Week 2 publishes the data contract. Week 3 Core B adds the spread summaries:
``quantile``, ``iqr``, ``variance``, ``stdev`` and ``coefficient_variation``,
plus ``DomainError`` and ``UnsupportedRuleError``. Center (mean, median, mode)
belongs to Core A and is not here.

Week 4 Numerics adds ``bivariate_online_update`` and ``BivariateState``, the
Chan, Golub & LeVeque (1983) one-pass pair state, plus
``DimensionMismatchError``. ``covariance`` and ``pearson_r`` belong to Core C;
the state here is what they should be built on.
"""

from stateskol.descriptive import (
    ASSUMPTION,
    DDOFS,
    DOCSTRING_SHAPE,
    METHODS,
    POLICIES,
    BivariateState,
    as_numeric,
    bivariate_online_update,
    coefficient_variation,
    count,
    iqr,
    quantile,
    stdev,
    variance,
)
from stateskol.errors import (
    ContractError,
    DimensionMismatchError,
    DomainError,
    EmptyDataError,
    UnknownPolicyError,
    UnsupportedRuleError,
)

__all__ = [
    "ASSUMPTION",
    "BivariateState",
    "DDOFS",
    "DOCSTRING_SHAPE",
    "METHODS",
    "POLICIES",
    "ContractError",
    "DimensionMismatchError",
    "DomainError",
    "EmptyDataError",
    "UnknownPolicyError",
    "UnsupportedRuleError",
    "as_numeric",
    "bivariate_online_update",
    "coefficient_variation",
    "count",
    "iqr",
    "quantile",
    "stdev",
    "variance",
]
