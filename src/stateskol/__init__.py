"""stateskol: statistics in pure Python, one tested function at a time.

The package imports the standard library and nothing else. Reference
libraries belong in tests and in examples/reference_check.py.

Week 2 publishes the data contract. ``as_numeric`` and ``count`` are here;
the summaries arrive with their own lanes.
"""

from stateskol.descriptive import (
    ASSUMPTION,
    DOCSTRING_SHAPE,
    POLICIES,
    as_numeric,
    count,
)
from stateskol.errors import ContractError, EmptyDataError, UnknownPolicyError

__all__ = [
    "ASSUMPTION",
    "DOCSTRING_SHAPE",
    "POLICIES",
    "ContractError",
    "EmptyDataError",
    "UnknownPolicyError",
    "as_numeric",
    "count",
]
