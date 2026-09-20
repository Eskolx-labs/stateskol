"""Center: mean, median, mode. Owner: Philimon.

Ross Ch.2.1 to Ch.2.4. Philimon implements these in week 1. Mean is the
plain arithmetic average. Median is the middle value, averaged pair for even
counts. Mode returns all tied winners in sorted order, empty list when every
value appears once and the data has more than one distinct value.
"""

from stateskol._missing import apply_missing
from stateskol._validate import require_nonempty, to_float_list


def mean(values, policy: str = "drop") -> float:
    raise NotImplementedError("Philimon implements mean in week 1")


def median(values, policy: str = "drop") -> float:
    raise NotImplementedError("Philimon implements median in week 1")


def mode(values, policy: str = "drop") -> list:
    raise NotImplementedError("Philimon implements mode in week 1")
