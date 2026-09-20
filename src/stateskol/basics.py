"""Basic summaries: count, min, max, range. Owner: Kaleb.

Ross Ch.1 to Ch.2.2. Kaleb implements these in week 1 on top of the input
contract and the missing data policy. Signatures are fixed so Philimon,
Robel, and Yoseph can build beside him without merge fights.
"""

from stateskol._missing import apply_missing
from stateskol._validate import require_nonempty, to_float_list


def count(values, policy: str = "drop") -> int:
    """Number of clean values. Reports data size after missing handling."""
    clean, _ = apply_missing(to_float_list(values), policy)
    return len(clean)


def min_(values, policy: str = "drop") -> float:
    """Smallest clean value. Raises ValueError on empty input."""
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    return min(clean)


def max_(values, policy: str = "drop") -> float:
    """Largest clean value. Raises ValueError on empty input."""
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    return max(clean)


def data_range(values, policy: str = "drop") -> float:
    """max minus min. Zero for a single value, error for no values."""
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    return max(clean) - min(clean)
