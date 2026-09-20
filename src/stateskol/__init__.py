"""Stateskol: descriptive statistics in pure Python.

Week 1 covers the Ross Ch.1 to Ch.2.4 slice: input contract, missing data
policy, count, min, max, range, center, spread, and tables. Each module names
its owner in the week 1 brief. Import from the module, not from the top level,
so ownership stays clear.
"""

from stateskol._missing import apply_missing
from stateskol._validate import require_nonempty, to_float_list

__all__ = ["apply_missing", "require_nonempty", "to_float_list"]
