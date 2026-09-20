"""Tables: frequency tables and histogram bin counts. Owner: Yoseph.

Ross Ch.2.1 to Ch.2.3. Yoseph implements these in week 1. The bin rule is
part of the deliverable: Yoseph states it, documents it, and the tests pin
it. Callers who want a different rule pass explicit edges.
"""

from stateskol._missing import apply_missing
from stateskol._validate import require_nonempty, to_float_list


def frequency_table(values, policy: str = "drop") -> dict:
    raise NotImplementedError("Yoseph implements frequency_table in week 1")


def histogram_counts(values, bins=10, policy: str = "drop") -> tuple:
    raise NotImplementedError("Yoseph implements histogram_counts in week 1")
