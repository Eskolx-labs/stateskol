"""Missing data policy. Owner: Kaleb.

Week 1 decision, single rule for the whole package: drop None and NaN,
report how many values were dropped, and never silently fill anything in.
Kaleb locks this choice in week 1 after the team agrees on Monday.
Fill methods like mean imputation stay out. If a caller wants them, they do
it explicitly before calling us, and they own the bias that adds.
"""

import math


def apply_missing(values: list, policy: str = "drop") -> tuple:
    """Split raw contracted input into clean data plus a dropped count.

    Inputs: a list from to_float_list, plus a policy name. Only "drop" and
    "raise" exist. "drop" removes None and NaN and returns the dropped count.
    "raise" throws ValueError on the first None or NaN instead.

    Outputs: a tuple (clean, dropped) where clean is a list of floats and
    dropped is the number of removed entries.
    """
    if policy not in ("drop", "raise"):
        raise ValueError("unknown missing data policy: %r" % (policy,))
    clean: list = []
    dropped = 0
    for v in values:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            if policy == "raise":
                raise ValueError("missing value found under policy 'raise'")
            dropped += 1
            continue
        clean.append(v)
    return clean, dropped
