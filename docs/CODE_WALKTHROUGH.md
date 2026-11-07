# Line-by-line code walkthrough

This document explains the code added for the counting and boundary-case pack.

**How to read it**

- Every executable line is explained.
- Blank lines and long docstring paragraphs are grouped where they are only
  formatting or prose.
- Line numbers match the files in this repository.
- The four files covered are:
  1. `src/stateskol/descriptive.py`
  2. `tests/test_descriptive.py`
  3. `examples/clean_env_demo.py`
  4. `examples/reference_check.py`

---

# 1. `src/stateskol/descriptive.py`

## 1.1 Module docstring (lines 1–71)

| Lines | Code | Explanation |
|---|---|---|
| 1 | `"""Descriptive statistics in pure Python. Stateskol Week 1.` | Opens the module docstring and gives the file its title. |
| 3–7 | `This module is the single home ... # ----- Owner: topic -----` | Explains the one-module rule and shows the marker shape used by the repository. |
| 9–11 | `Welasma's block is the counting ... deliberately explicit.` | States who owns this block and why the rules are written in detail. |
| 13–20 | `Input contract ... handled by the policy argument.` | Lists which values are accepted, which are rejected, and how `None`/`NaN` are treated. |
| 22–29 | `Missing-data policy ... exactly once.` | Documents `"drop"` and `"raise"` and the one-shot-iterator guarantee. |
| 31–70 | `Boundary-case table ... no key is special.` | Gives the one correct answer for empty, single, constant, tied, missing, all-missing, and invalid input. |
| 71 | `"""` | Closes the module docstring. |

## 1.2 Imports (lines 73–81)

| Line | Code | Explanation |
|---|---|---|
| 73 | `from __future__ import annotations` | Makes type hints lazy, so `MissingPolicy \| str` and similar hints are not evaluated at import time. |
| 75 | `import decimal` | Used to accept `decimal.Decimal` input and to detect `Decimal("NaN")` / `Decimal("Infinity")`. |
| 76 | `import math` | Provides `math.isnan` and `math.isinf`. |
| 77 | `import numbers` | Provides `numbers.Real`, the check for ordinary real numbers. |
| 78 | `from collections import Counter` | Counts repeated values inside `frequency_table`. |
| 79 | `from dataclasses import dataclass` | Creates the frozen `BoundaryCase` record. |
| 80 | `from enum import Enum` | Creates the `MissingPolicy` enum. |
| 81 | `from typing import Any, Iterable, Sequence` | Supplies type hints for iterables and sequences. |

## 1.3 Start marker (line 83)

| Line | Code | Explanation |
|---|---|---|
| 83 | `# ----- Welasma: counting and boundary pack -----` | Marks the beginning of this owner's block. Everything below this line belongs to the block. |

## 1.4 `MissingPolicy` (lines 86–95)

| Lines | Code | Explanation |
|---|---|---|
| 86 | `class MissingPolicy(str, Enum):` | Defines an enum whose members are also strings, so callers may pass `"drop"` or `"raise"`. |
| 87–92 | `"""How missing values ... directly."""` | Docstring: explains the two policies and why the string values matter. |
| 94 | `DROP = "drop"` | The default policy: remove `None` and `NaN`. |
| 95 | `RAISE = "raise"` | The strict policy: raise `ValueError` on the first missing value. |

## 1.5 `_coerce_policy` (lines 98–113)

| Lines | Code | Explanation |
|---|---|---|
| 98 | `def _coerce_policy(policy: MissingPolicy \| str) -> MissingPolicy:` | Private helper that turns either an enum member or a string into a `MissingPolicy`. |
| 99–103 | `"""Return a :class:`MissingPolicy` ... raises ``ValueError``."""` | Docstring: says the helper validates before data is touched. |
| 104–105 | `if isinstance(policy, MissingPolicy): return policy` | If the caller already passed the enum, return it unchanged. |
| 106 | `if isinstance(policy, str):` | If the caller passed a string, try to convert it. |
| 107–108 | `try: return MissingPolicy(policy)` | `MissingPolicy("drop")` and `MissingPolicy("raise")` succeed. |
| 109–110 | `except ValueError: pass` | An unknown string falls through to the common error below. |
| 111–113 | `raise ValueError("unknown missing-data policy: ...")` | Rejects any other value before the data iterator is consumed. |

**Why it matters:** every public function calls this first. An invalid policy
therefore cannot consume a one-shot iterator.

## 1.6 `is_missing` (lines 116–123)

| Lines | Code | Explanation |
|---|---|---|
| 116 | `def is_missing(value: object) -> bool:` | Returns whether a value counts as missing. |
| 117–122 | `"""Return ``True`` ... not missing data."""` | Docstring: `None` and float `NaN` are missing; everything else is not. |
| 123 | `return value is None or (isinstance(value, float) and math.isnan(value))` | The actual test. The `isinstance(..., float)` guard prevents calling `math.isnan` on non-floats. |

## 1.7 `to_float_list` (lines 126–207)

| Lines | Code | Explanation |
|---|---|---|
| 126 | `def to_float_list(values: Iterable[object]) -> list[float \| None]:` | Public helper: turn any accepted iterable into a list of floats and `None`. |
| 127–159 | `"""Contract an iterable ... got True` | Docstring: inputs, outputs, errors, and examples. |
| 160–161 | `if isinstance(values, (str, bytes, bytearray)): raise TypeError(...)` | Rejects string-like containers so `"123"` is not read as three values. |
| 162–163 | `try: items = list(values)` | Consumes the input exactly once and stores it in a list. |
| 164–165 | `except TypeError: raise TypeError(...) from None` | A non-iterable input gets a clear `TypeError`. |
| 167 | `contracted: list[float \| None] = []` | Creates the output list. |
| 168 | `for value in items:` | Visits each input value once. |
| 169–171 | `if value is None: contracted.append(None); continue` | `None` is preserved for the missing policy. |
| 172–173 | `if isinstance(value, bool): raise TypeError(...)` | Booleans are rejected even though `bool` is an `int` subclass. |
| 174 | `if isinstance(value, decimal.Decimal):` | Special handling for `Decimal`, which is not `numbers.Real`. |
| 175–176 | `if value.is_nan(): contracted.append(float("nan"))` | `Decimal("NaN")` becomes a normal float `NaN`, which the missing policy can drop. |
| 177–180 | `elif value.is_infinite(): raise ValueError(...)` | `Decimal("Infinity")` is invalid data. |
| 181–188 | `else: try: contracted.append(float(value)) ...` | Converts finite `Decimal` to float and turns overflow into a clear `ValueError`. |
| 189 | `continue` | Skips the generic numeric path after handling `Decimal`. |
| 190–194 | `if not isinstance(value, numbers.Real): raise TypeError(...)` | Rejects strings, complex numbers, objects, and other non-real values. |
| 195–200 | `try: contracted.append(float(value)) ...` | Converts `int`, `float`, `Fraction`, and other real numbers to float, catching overflow. |
| 202–206 | `for value in contracted: if ... math.isinf(value): raise ValueError(...)` | Final guard: any infinity that survived conversion is rejected. |
| 207 | `return contracted` | Returns the validated list. |

## 1.8 `require_nonempty` (lines 210–219)

| Lines | Code | Explanation |
|---|---|---|
| 210 | `def require_nonempty(values: Sequence[Any], name: str = "data") -> Sequence[Any]:` | Helper that refuses an empty sequence. |
| 211–216 | `"""Return ``values`` unchanged ... needed data."""` | Docstring: the sequence is returned unchanged when it has data. |
| 217–218 | `if len(values) == 0: raise ValueError(...)` | Raises `ValueError` with the statistic's name in the message. |
| 219 | `return values` | Returns the same object when it is non-empty. |

## 1.9 `apply_missing` (lines 222–284)

| Lines | Code | Explanation |
|---|---|---|
| 222–225 | `def apply_missing(values: Iterable[float \| None], policy: ... ) -> tuple[list[float], int]:` | Takes contracted values and applies the missing policy. |
| 226–259 | `"""Split contracted values ... policy 'raise'` | Docstring: inputs, outputs, errors, and examples. |
| 260 | `policy = _coerce_policy(policy)` | Validates the policy before the loop. |
| 261 | `clean: list[float] = []` | Holds the values that survive. |
| 262 | `dropped = 0` | Counts how many values were removed. |
| 263 | `for value in values:` | Visits each contracted value once. |
| 264–268 | `if value is None: ... dropped += 1; continue` | Under `"drop"`, `None` is counted and skipped; under `"raise"`, it raises. |
| 269–273 | `if not isinstance(value, float): raise TypeError(...)` | Enforces that the input came from `to_float_list`. |
| 274–278 | `if math.isnan(value): ... dropped += 1; continue` | Same rule for `NaN`. |
| 279–282 | `if math.isinf(value): raise ValueError(...)` | Defensive check; `to_float_list` already rejects infinities. |
| 283 | `clean.append(value)` | Keeps a finite, non-missing float. |
| 284 | `return clean, dropped` | Returns the clean list and the number of removed values. |

## 1.10 `prepare_data` (lines 287–303)

| Lines | Code | Explanation |
|---|---|---|
| 287–290 | `def prepare_data(values: Iterable[object], policy: ...) -> tuple[list[float], int]:` | One-call entry point for the boundary pack. |
| 291–301 | `"""Contract, validate ... ([1.0, 2.0], 2)` | Docstring: consumes once and returns `(clean, dropped)`. |
| 302 | `policy = _coerce_policy(policy)` | Validates before touching the iterable. |
| 303 | `return apply_missing(to_float_list(values), policy)` | Contracts the data, then applies the missing policy. |

## 1.11 `clean_values` (lines 306–317)

| Lines | Code | Explanation |
|---|---|---|
| 306–309 | `def clean_values(values: Iterable[object], policy: ...) -> list[float]:` | Convenience wrapper that returns only the clean list. |
| 310–316 | `"""Return only the clean floats ... [1.0, 2.0]` | Docstring with an example. |
| 317 | `return prepare_data(values, policy)[0]` | Calls `prepare_data` and keeps the first element of the tuple. |

## 1.12 `count_missing` (lines 320–332)

| Lines | Code | Explanation |
|---|---|---|
| 320 | `def count_missing(values: Iterable[object]) -> int:` | Counts `None` and `NaN` without dropping them. |
| 321–330 | `"""Count ``None`` and ``NaN`` ... 2` | Docstring: invalid elements still raise. |
| 331 | `contracted = to_float_list(values)` | Validates and consumes the iterable once. |
| 332 | `return sum(1 for value in contracted if is_missing(value))` | Adds 1 for every missing value. |

## 1.13 `BoundaryCase` (lines 335–347)

| Lines | Code | Explanation |
|---|---|---|
| 335 | `@dataclass(frozen=True, eq=False)` | Makes an immutable record; `eq=False` means cases are compared by identity, which is safe for cases containing `NaN`. |
| 336 | `class BoundaryCase:` | Defines one canonical boundary case. |
| 337–343 | `"""One canonical boundary input ... itself."""` | Docstring: explains `data`, `name`, and the identity rule. |
| 345 | `name: str` | The case name, such as `"empty"`. |
| 346 | `data: tuple[object, ...]` | The input values, stored as an immutable tuple. |
| 347 | `description: str` | A human-readable rule for the case. |

## 1.14 Canonical cases (lines 350–395)

| Lines | Code | Explanation |
|---|---|---|
| 350–354 | `EMPTY_INPUT = BoundaryCase("empty", (), "...")` | The empty case: no values. |
| 355–359 | `SINGLE_VALUE = BoundaryCase("single", (7.0,), "...")` | The single-value case. |
| 360–364 | `CONSTANT_VALUES = BoundaryCase("constant", (4.0, 4.0, 4.0, 4.0), "...")` | The constant case. |
| 365–369 | `TIED_VALUES = BoundaryCase("tied", (1.0, 2.0, 2.0, 3.0, 3.0), "...")` | The tied-values case. |
| 370–374 | `MISSING_VALUES = BoundaryCase("missing", (1.0, None, float("nan"), 4.0), "...")` | The missing-values case. |
| 375–379 | `ALL_MISSING = BoundaryCase("all-missing", (None, float("nan")), "...")` | The all-missing case. |
| 380–384 | `INVALID_VALUES = BoundaryCase("invalid", (1.0, "two", 3.0), "...")` | The invalid-element case. |
| 386–393 | `VALID_BOUNDARY_CASES = (...)` | A tuple of the cases that are valid under the default policy. |
| 394 | `INVALID_BOUNDARY_CASES = (INVALID_VALUES,)` | A tuple of the invalid cases. |
| 395 | `BOUNDARY_CASES = VALID_BOUNDARY_CASES + INVALID_BOUNDARY_CASES` | The full pack, valid cases first. |

## 1.15 `get_boundary_case` (lines 398–412)

| Lines | Code | Explanation |
|---|---|---|
| 398 | `def get_boundary_case(name: str) -> BoundaryCase:` | Looks up a case by name. |
| 399–408 | `"""Return the canonical case ... (7.0,)` | Docstring: unknown names raise `KeyError`. |
| 409 | `for case in BOUNDARY_CASES:` | Scans the small tuple. |
| 410–411 | `if case.name == name: return case` | Returns the matching case. |
| 412 | `raise KeyError(...)` | No match means the name is unknown. |

## 1.16 `boundary_case_names` (lines 415–423)

| Lines | Code | Explanation |
|---|---|---|
| 415 | `def boundary_case_names() -> tuple[str, ...]:` | Returns all case names in pack order. |
| 416–422 | `"""Return the canonical case names ... ('empty', 'single')` | Docstring with an example. |
| 423 | `return tuple(case.name for case in BOUNDARY_CASES)` | Builds the name tuple. |

## 1.17 `count` (lines 426–470)

| Lines | Code | Explanation |
|---|---|---|
| 426–429 | `def count(values: Iterable[object], policy: ...) -> int:` | Public counting function. |
| 430–467 | `"""Count the clean values ... policy 'raise'` | Docstring: inputs, outputs, errors, and examples. |
| 468 | `policy = _coerce_policy(policy)` | Validates the policy first. |
| 469 | `clean, _ = apply_missing(to_float_list(values), policy)` | Contracts the data and applies the missing policy; the dropped count is ignored. |
| 470 | `return len(clean)` | The answer is the length of the clean list. |

## 1.18 `min_` (lines 473–501)

| Lines | Code | Explanation |
|---|---|---|
| 473–476 | `def min_(values: Iterable[object], policy: ...) -> float:` | Returns the smallest clean value. The trailing underscore avoids shadowing the built-in `min`. |
| 477–493 | `"""Return the smallest clean value ... needs at least one value` | Docstring: empty input raises; single/constant input is valid. |
| 494 | `policy = _coerce_policy(policy)` | Validates the policy first. |
| 495 | `clean, _ = apply_missing(to_float_list(values), policy)` | Contracts and cleans the data. |
| 496 | `require_nonempty(clean)` | Raises `ValueError` when nothing survives. |
| 497 | `smallest = clean[0]` | Starts with the first value. |
| 498 | `for value in clean[1:]:` | Visits the rest of the values. |
| 499–500 | `if value < smallest: smallest = value` | Updates the answer when a smaller value is found. |
| 501 | `return smallest` | Returns the minimum. |

## 1.19 `max_` (lines 504–532)

| Lines | Code | Explanation |
|---|---|---|
| 504–507 | `def max_(values: Iterable[object], policy: ...) -> float:` | Returns the largest clean value. |
| 508–524 | `"""Return the largest clean value ... needs at least one value` | Docstring: same rules as `min_`. |
| 525 | `policy = _coerce_policy(policy)` | Validates the policy first. |
| 526 | `clean, _ = apply_missing(to_float_list(values), policy)` | Contracts and cleans the data. |
| 527 | `require_nonempty(clean)` | Raises `ValueError` when nothing survives. |
| 528 | `largest = clean[0]` | Starts with the first value. |
| 529 | `for value in clean[1:]:` | Visits the rest of the values. |
| 530–531 | `if value > largest: largest = value` | Updates the answer when a larger value is found. |
| 532 | `return largest` | Returns the maximum. |

## 1.20 `data_range` (lines 535–563)

| Lines | Code | Explanation |
|---|---|---|
| 535–538 | `def data_range(values: Iterable[object], policy: ...) -> float:` | Returns `max - min`. The name avoids shadowing the built-in `range`. |
| 539–553 | `"""Return ``max - min`` ... 0.0` | Docstring: single and constant input return `0.0`; empty input raises. |
| 554 | `policy = _coerce_policy(policy)` | Validates the policy first. |
| 555 | `clean, _ = apply_missing(to_float_list(values), policy)` | Contracts and cleans the data. |
| 556 | `require_nonempty(clean)` | Raises `ValueError` when nothing survives. |
| 557 | `smallest = largest = clean[0]` | Starts both extremes at the first value. |
| 558 | `for value in clean[1:]:` | Visits the rest of the values. |
| 559–560 | `if value < smallest: smallest = value` | Updates the minimum. |
| 561–562 | `if value > largest: largest = value` | Updates the maximum. |
| 563 | `return largest - smallest` | Returns the span. |

## 1.21 `frequency_table` (lines 566–612)

| Lines | Code | Explanation |
|---|---|---|
| 566–569 | `def frequency_table(values: Iterable[object], policy: ...) -> dict[float, int]:` | Returns a value-to-count mapping. |
| 570–608 | `"""Return a value-to-count mapping ... {1.0: 1, 4.0: 1}` | Docstring: sorted keys, ties, empty input, and examples. |
| 609 | `policy = _coerce_policy(policy)` | Validates the policy first. |
| 610 | `clean, _ = apply_missing(to_float_list(values), policy)` | Contracts and cleans the data. |
| 611 | `counts = Counter(clean)` | Counts how often each value occurs. |
| 612 | `return {value: counts[value] for value in sorted(counts)}` | Builds a new dict with keys in ascending order. |

## 1.22 Aliases (lines 615–617)

| Line | Code | Explanation |
|---|---|---|
| 615 | `minimum = min_` | Descriptive alias for `min_`. |
| 616 | `maximum = max_` | Descriptive alias for `max_`. |
| 617 | `value_range = data_range` | Descriptive alias for `data_range`. |

## 1.23 `__all__` (lines 619–651)

| Lines | Code | Explanation |
|---|---|---|
| 619–651 | `__all__ = (...)` | Declares the public names exported by `from stateskol.descriptive import *`. It includes the boundary pack, the public functions, the aliases, and the short names `min`, `max`, `range`. |

## 1.24 `__getattr__` (lines 654–668)

| Lines | Code | Explanation |
|---|---|---|
| 654 | `def __getattr__(name: str):` | Module-level hook called when an attribute is not found normally. |
| 655–661 | `"""Expose the prompt's short names ... same file."""` | Docstring: explains the built-in-shadowing problem and the solution. |
| 662–663 | `if name == "min": return min_` | `descriptive.min` resolves to `min_`. |
| 664–665 | `if name == "max": return max_` | `descriptive.max` resolves to `max_`. |
| 666–667 | `if name == "range": return data_range` | `descriptive.range` resolves to `data_range`. |
| 668 | `raise AttributeError(...)` | Any other missing attribute raises the normal error. |

**Why not just assign `min = min_`?** Because that would bind `min` in the
module globals and shadow the built-in `min` for every other owner who adds
code to this same file. The hook gives the short name without that side
effect.

## 1.25 `__dir__` (lines 671–672)

| Lines | Code | Explanation |
|---|---|---|
| 671 | `def __dir__():` | Controls what `dir(module)` reports. |
| 672 | `return sorted(set(globals()) \| {"min", "max", "range"})` | Adds the three short names to the normal module names and sorts them. |

## 1.26 End marker (line 675)

| Line | Code | Explanation |
|---|---|---|
| 675 | `# ----- end Welasma: counting and boundary pack -----` | Marks the end of this owner's block. |

---

# 2. `tests/test_descriptive.py`

## 2.1 Module docstring and imports (lines 1–45)

| Lines | Code | Explanation |
|---|---|---|
| 1–11 | `"""Week 1 tests ... magic numbers.` | Docstring: says the suite is standard-library-only, unittest-based, and reuses the shared boundary cases. |
| 13 | `import math` | Used for `math.isnan` and `math.inf`. |
| 14 | `import unittest` | The test framework. |
| 15 | `from decimal import Decimal` | Used to test `Decimal` input and `Decimal("NaN")`. |
| 16 | `from fractions import Fraction` | Used to test exact rational input. |
| 18 | `from stateskol import descriptive` | Imports the module itself for alias and `dir()` checks. |
| 19–45 | `from stateskol.descriptive import (...)` | Imports the boundary cases, helpers, and public functions used by the tests. |

## 2.2 `OneShot` helper (lines 48–59)

| Lines | Code | Explanation |
|---|---|---|
| 48 | `class OneShot:` | A test helper that simulates a one-shot iterator. |
| 49 | `"""Iterable that raises if it is iterated more than once."""` | Docstring. |
| 51 | `def __init__(self, values):` | Stores the values. |
| 52 | `self._values = tuple(values)` | Copies the values into an immutable tuple. |
| 53 | `self.iterations = 0` | Counts how many times `__iter__` was called. |
| 55 | `def __iter__(self):` | Makes the object iterable. |
| 56 | `self.iterations += 1` | Records one iteration attempt. |
| 57–58 | `if self.iterations > 1: raise AssertionError(...)` | A second iteration fails the test immediately. |
| 59 | `return iter(self._values)` | Returns a fresh iterator over the stored values. |

## 2.3 `TestInputContract` (lines 62–115)

| Lines | Code | Explanation |
|---|---|---|
| 62 | `class TestInputContract(unittest.TestCase):` | Groups tests for `to_float_list`. |
| 63 | `def test_ints_become_floats(self):` | Test: integers become floats. |
| 64 | `self.assertEqual(to_float_list([1, 2, 3]), [1.0, 2.0, 3.0])` | Checks the conversion. |
| 66 | `def test_fraction_and_decimal_are_accepted(self):` | Test: `Fraction` and `Decimal` are valid numeric input. |
| 67–70 | `self.assertEqual(to_float_list([Fraction(1, 2), Decimal("1.5")]), [0.5, 1.5])` | Checks both conversions. |
| 72 | `def test_none_and_nan_pass_through(self):` | Test: missing values survive contraction. |
| 73 | `contracted = to_float_list([None, float("nan")])` | Runs the function. |
| 74 | `self.assertIsNone(contracted[0])` | `None` stays `None`. |
| 75 | `self.assertTrue(math.isnan(contracted[1]))` | `NaN` stays `NaN`. |
| 77 | `def test_decimal_nan_is_missing(self):` | Test: `Decimal("NaN")` becomes a float `NaN`. |
| 78 | `contracted = to_float_list([Decimal("NaN")])` | Runs the function. |
| 79 | `self.assertTrue(math.isnan(contracted[0]))` | Checks the result. |
| 81 | `def test_empty_input_is_allowed(self):` | Test: an empty iterable is valid. |
| 82 | `self.assertEqual(to_float_list([]), [])` | Empty input gives an empty list. |
| 84 | `def test_strings_bytes_and_non_iterables_fail(self):` | Test: string-like containers and non-iterables are rejected. |
| 85 | `for bad in ("123", b"123", bytearray(b"123"), 5, None):` | Tries each bad container. |
| 86 | `with self.subTest(bad=bad):` | Reports which value failed. |
| 87–88 | `with self.assertRaises(TypeError): to_float_list(bad)` | All of them must raise `TypeError`. |
| 90 | `def test_bools_fail(self):` | Test: booleans are not numeric data. |
| 91 | `for bad in (True, False):` | Tries both booleans. |
| 92 | `with self.subTest(bad=bad):` | Labels the failing case. |
| 93–94 | `with self.assertRaises(TypeError): to_float_list([bad])` | Both must raise `TypeError`. |
| 96 | `def test_non_numeric_elements_fail(self):` | Test: strings, complex numbers, and objects are rejected. |
| 97 | `for bad in ("two", 2 + 3j, object()):` | Tries each bad element. |
| 98 | `with self.subTest(bad=bad):` | Labels the failing case. |
| 99–100 | `with self.assertRaises(TypeError): to_float_list([1, bad, 3])` | Each must raise `TypeError`. |
| 102 | `def test_infinities_fail(self):` | Test: infinities are invalid data. |
| 103–108 | `for bad in (math.inf, -math.inf, Decimal("Infinity"), Decimal("-Infinity")):` | Tries float and `Decimal` infinities. |
| 109 | `with self.subTest(bad=bad):` | Labels the failing case. |
| 110–111 | `with self.assertRaises(ValueError): to_float_list([1, bad])` | Each must raise `ValueError`. |
| 113 | `def test_huge_fraction_fails_as_value_error(self):` | Test: a value too large for a float is a `ValueError`. |
| 114–115 | `with self.assertRaises(ValueError): to_float_list([Fraction(10 ** 400, 1)])` | The huge fraction must raise `ValueError`. |

## 2.4 `TestMissingPolicy` (lines 118–167)

| Lines | Code | Explanation |
|---|---|---|
| 118 | `class TestMissingPolicy(unittest.TestCase):` | Groups tests for `apply_missing` and policy validation. |
| 119 | `def test_drop_removes_none_and_nan(self):` | Test: `"drop"` removes both missing kinds. |
| 120 | `clean, dropped = apply_missing(to_float_list([1, None, float("nan"), 4]))` | Runs the pipeline. |
| 121 | `self.assertEqual(clean, [1.0, 4.0])` | Only the real numbers remain. |
| 122 | `self.assertEqual(dropped, 2)` | Two values were removed. |
| 124 | `def test_raise_stops_on_none(self):` | Test: `"raise"` rejects `None`. |
| 125–126 | `with self.assertRaises(ValueError): apply_missing(to_float_list([1, None]), "raise")` | The call must raise. |
| 128 | `def test_raise_stops_on_nan(self):` | Test: `"raise"` rejects `NaN`. |
| 129–130 | `with self.assertRaises(ValueError): apply_missing(to_float_list([1, float("nan")]), MissingPolicy.RAISE)` | The call must raise, using the enum form. |
| 132 | `def test_enum_and_string_policies_agree(self):` | Test: enum and string policies behave the same. |
| 133–136 | `self.assertEqual(count([1, None, 2], MissingPolicy.DROP), count([1, None, 2], "drop"))` | Both forms return the same count. |
| 137–138 | `with self.assertRaises(ValueError): count([1, None, 2], MissingPolicy.RAISE)` | The enum raise policy works. |
| 140 | `def test_unknown_policy_fails_before_iteration(self):` | Test: an invalid policy does not consume the iterator. |
| 141–149 | `for fn in (count, min_, max_, data_range, frequency_table, clean_values, prepare_data):` | Tries every public function and helper. |
| 150 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 151 | `data = OneShot([1, 2, 3])` | Creates a fresh one-shot iterator. |
| 152–153 | `with self.assertRaises(ValueError): fn(data, policy="explode")` | The invalid policy must raise. |
| 154 | `self.assertEqual(data.iterations, 0)` | The iterator was never touched. |
| 156 | `def test_apply_missing_also_validates_before_iteration(self):` | Test: `apply_missing` also validates first. |
| 157 | `data = OneShot([1.0, None])` | Creates a one-shot iterator. |
| 158–159 | `with self.assertRaises(ValueError): apply_missing(data, policy="explode")` | The invalid policy must raise. |
| 160 | `self.assertEqual(data.iterations, 0)` | The iterator was not consumed. |
| 162 | `def test_apply_missing_rejects_uncontracted_values(self):` | Test: `apply_missing` expects `to_float_list` output. |
| 163–164 | `with self.assertRaises(TypeError): apply_missing([1, 2, 3])` | Raw integers are rejected. |
| 166 | `def test_apply_missing_empty(self):` | Test: empty input is valid. |
| 167 | `self.assertEqual(apply_missing([]), ([], 0))` | Empty input gives an empty list and zero dropped. |

## 2.5 `TestBoundaryPack` (lines 170–214)

| Lines | Code | Explanation |
|---|---|---|
| 170 | `class TestBoundaryPack(unittest.TestCase):` | Groups tests for the shared boundary pack. |
| 171 | `def test_required_cases_are_present(self):` | Test: the required case names exist. |
| 172 | `names = boundary_case_names()` | Gets the names. |
| 173 | `for required in ("empty", "single", "constant", "tied", "invalid"):` | The five required cases. |
| 174 | `self.assertIn(required, names)` | Each must be present. |
| 176 | `def test_case_names_are_unique(self):` | Test: no duplicate case names. |
| 177 | `names = boundary_case_names()` | Gets the names. |
| 178 | `self.assertEqual(len(names), len(set(names)))` | The lengths match only when all names are unique. |
| 180 | `def test_pack_is_the_valid_and_invalid_cases(self):` | Test: the full pack is the two sub-packs combined. |
| 181–184 | `self.assertEqual(BOUNDARY_CASES, VALID_BOUNDARY_CASES + INVALID_BOUNDARY_CASES)` | Checks the composition. |
| 185 | `self.assertIn(INVALID_VALUES, INVALID_BOUNDARY_CASES)` | The invalid case is in the invalid pack. |
| 186 | `self.assertNotIn(INVALID_VALUES, VALID_BOUNDARY_CASES)` | It is not in the valid pack. |
| 188 | `def test_get_boundary_case(self):` | Test: every case can be looked up by name. |
| 189–195 | `self.assertIs(get_boundary_case("..."), CASE)` | Each lookup returns the exact canonical object. |
| 197 | `def test_unknown_case_raises_key_error(self):` | Test: an unknown name fails. |
| 198–199 | `with self.assertRaises(KeyError): get_boundary_case("nope")` | The lookup must raise `KeyError`. |
| 201 | `def test_is_missing(self):` | Test: the missing-value predicate. |
| 202 | `self.assertTrue(is_missing(None))` | `None` is missing. |
| 203 | `self.assertTrue(is_missing(float("nan")))` | `NaN` is missing. |
| 204 | `self.assertFalse(is_missing(0.0))` | Zero is not missing. |
| 205 | `self.assertFalse(is_missing(False))` | `False` is not missing. |
| 206 | `self.assertFalse(is_missing("two"))` | A string is invalid, not missing. |
| 208 | `def test_count_missing(self):` | Test: `count_missing`. |
| 209 | `self.assertEqual(count_missing([1, None, float("nan"), 4]), 2)` | Two missing values. |
| 210 | `self.assertEqual(count_missing([]), 0)` | Empty input has zero missing values. |
| 212 | `def test_prepare_data_and_clean_values(self):` | Test: the two convenience helpers. |
| 213 | `self.assertEqual(prepare_data([1, None, 2]), ([1.0, 2.0], 1))` | Returns clean values and the dropped count. |
| 214 | `self.assertEqual(clean_values([1, None, 2]), [1.0, 2.0])` | Returns only the clean values. |

## 2.6 `TestEmptyInput` (lines 217–228)

| Lines | Code | Explanation |
|---|---|---|
| 217 | `class TestEmptyInput(unittest.TestCase):` | Tests the empty boundary case. |
| 218 | `def test_count_is_zero(self):` | Test: count of empty input. |
| 219 | `self.assertEqual(count(EMPTY_INPUT.data), 0)` | Empty input counts as 0. |
| 221 | `def test_frequency_table_is_empty(self):` | Test: frequency table of empty input. |
| 222 | `self.assertEqual(frequency_table(EMPTY_INPUT.data), {})` | Empty input gives an empty dict. |
| 224 | `def test_extremes_raise_value_error(self):` | Test: min, max, and range reject empty input. |
| 225 | `for fn in (min_, max_, data_range):` | Tries the three functions. |
| 226 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 227–228 | `with self.assertRaises(ValueError): fn(EMPTY_INPUT.data)` | Each must raise `ValueError`. |

## 2.7 `TestSingleValue` (lines 231–241)

| Lines | Code | Explanation |
|---|---|---|
| 231 | `class TestSingleValue(unittest.TestCase):` | Tests the single-value case. |
| 232 | `def test_count(self):` | Test: count of one value. |
| 233 | `self.assertEqual(count(SINGLE_VALUE.data), 1)` | One value counts as 1. |
| 235 | `def test_extremes(self):` | Test: min, max, and range of one value. |
| 236 | `self.assertEqual(min_(SINGLE_VALUE.data), 7.0)` | Minimum is the value. |
| 237 | `self.assertEqual(max_(SINGLE_VALUE.data), 7.0)` | Maximum is the value. |
| 238 | `self.assertEqual(data_range(SINGLE_VALUE.data), 0.0)` | Range is zero. |
| 240 | `def test_frequency_table(self):` | Test: frequency table of one value. |
| 241 | `self.assertEqual(frequency_table(SINGLE_VALUE.data), {7.0: 1})` | The value appears once. |

## 2.8 `TestConstantValues` (lines 244–254)

| Lines | Code | Explanation |
|---|---|---|
| 244 | `class TestConstantValues(unittest.TestCase):` | Tests the constant-values case. |
| 245 | `def test_count(self):` | Test: count of constant values. |
| 246 | `self.assertEqual(count(CONSTANT_VALUES.data), 4)` | Four values. |
| 248 | `def test_extremes(self):` | Test: min, max, and range of constant values. |
| 249 | `self.assertEqual(min_(CONSTANT_VALUES.data), 4.0)` | Minimum is the repeated value. |
| 250 | `self.assertEqual(max_(CONSTANT_VALUES.data), 4.0)` | Maximum is the repeated value. |
| 251 | `self.assertEqual(data_range(CONSTANT_VALUES.data), 0.0)` | Range is zero. |
| 253 | `def test_frequency_table(self):` | Test: frequency table of constant values. |
| 254 | `self.assertEqual(frequency_table(CONSTANT_VALUES.data), {4.0: 4})` | The value appears four times. |

## 2.9 `TestTiedValues` (lines 257–269)

| Lines | Code | Explanation |
|---|---|---|
| 257 | `class TestTiedValues(unittest.TestCase):` | Tests the tied-values case. |
| 258 | `def test_count(self):` | Test: count of tied values. |
| 259 | `self.assertEqual(count(TIED_VALUES.data), 5)` | Five values. |
| 261 | `def test_extremes(self):` | Test: min, max, and range with ties. |
| 262 | `self.assertEqual(min_(TIED_VALUES.data), 1.0)` | Minimum is 1. |
| 263 | `self.assertEqual(max_(TIED_VALUES.data), 3.0)` | Maximum is 3. |
| 264 | `self.assertEqual(data_range(TIED_VALUES.data), 2.0)` | Range is 2. |
| 266 | `def test_frequency_table_keeps_every_tie(self):` | Test: every tied key is kept. |
| 267–270 | `self.assertEqual(frequency_table(TIED_VALUES.data), {1.0: 1, 2.0: 2, 3.0: 2})` | The counts are exact. |

## 2.10 `TestMissingValues` (lines 273–288)

| Lines | Code | Explanation |
|---|---|---|
| 273 | `class TestMissingValues(unittest.TestCase):` | Tests the missing-values case. |
| 274 | `def test_default_drop(self):` | Test: the default policy drops missing values. |
| 275 | `self.assertEqual(count(MISSING_VALUES.data), 2)` | Two clean values remain. |
| 276 | `self.assertEqual(min_(MISSING_VALUES.data), 1.0)` | Minimum over the clean values. |
| 277 | `self.assertEqual(max_(MISSING_VALUES.data), 4.0)` | Maximum over the clean values. |
| 278 | `self.assertEqual(data_range(MISSING_VALUES.data), 3.0)` | Range over the clean values. |
| 279–282 | `self.assertEqual(frequency_table(MISSING_VALUES.data), {1.0: 1, 4.0: 1})` | Frequency table over the clean values. |
| 284 | `def test_raise_policy(self):` | Test: `"raise"` rejects the missing values. |
| 285 | `for fn in (count, min_, max_, data_range, frequency_table):` | Tries every public function. |
| 286 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 287–288 | `with self.assertRaises(ValueError): fn(MISSING_VALUES.data, policy="raise")` | Each must raise `ValueError`. |

## 2.11 `TestAllMissing` (lines 291–306)

| Lines | Code | Explanation |
|---|---|---|
| 291 | `class TestAllMissing(unittest.TestCase):` | Tests the all-missing case. |
| 292 | `def test_count_is_zero(self):` | Test: count after dropping everything. |
| 293 | `self.assertEqual(count(ALL_MISSING.data), 0)` | Count is 0. |
| 295 | `def test_frequency_table_is_empty(self):` | Test: frequency table after dropping everything. |
| 296 | `self.assertEqual(frequency_table(ALL_MISSING.data), {})` | The table is empty. |
| 298 | `def test_extremes_raise(self):` | Test: extremes reject all-missing input. |
| 299 | `for fn in (min_, max_, data_range):` | Tries the three functions. |
| 300 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 301–302 | `with self.assertRaises(ValueError): fn(ALL_MISSING.data)` | Each must raise `ValueError`. |
| 304 | `def test_raise_policy(self):` | Test: `"raise"` rejects all-missing input immediately. |
| 305–306 | `with self.assertRaises(ValueError): count(ALL_MISSING.data, policy="raise")` | The call must raise. |

## 2.12 `TestInvalidValues` (lines 309–320)

| Lines | Code | Explanation |
|---|---|---|
| 309 | `class TestInvalidValues(unittest.TestCase):` | Tests the invalid-element case. |
| 310 | `def test_every_public_function_raises_type_error(self):` | Test: every public function rejects a string element. |
| 311 | `for fn in (count, min_, max_, data_range, frequency_table):` | Tries every public function. |
| 312 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 313–314 | `with self.assertRaises(TypeError): fn(INVALID_VALUES.data)` | Each must raise `TypeError`. |
| 316 | `def test_helpers_raise_type_error(self):` | Test: the helpers also reject the invalid input. |
| 317 | `for fn in (to_float_list, count_missing, clean_values, prepare_data):` | Tries the helpers. |
| 318 | `with self.subTest(fn=fn.__name__):` | Labels the failing helper. |
| 319–320 | `with self.assertRaises(TypeError): fn(INVALID_VALUES.data)` | Each must raise `TypeError`. |

## 2.13 `TestCount` (lines 323–339)

| Lines | Code | Explanation |
|---|---|---|
| 323 | `class TestCount(unittest.TestCase):` | Focused tests for `count`. |
| 324 | `def test_hand_checked(self):` | Test with a hand-checked dataset. |
| 325 | `self.assertEqual(count([4, 8, 6, 5, 3, 7]), 6)` | Six values. |
| 327 | `def test_empty(self):` | Test empty input. |
| 328 | `self.assertEqual(count([]), 0)` | Zero values. |
| 330 | `def test_missing_drop(self):` | Test the default drop policy. |
| 331 | `self.assertEqual(count([1, None, float("nan"), 4]), 2)` | Two clean values. |
| 333 | `def test_raise(self):` | Test the raise policy. |
| 334–335 | `with self.assertRaises(ValueError): count([1, None], policy="raise")` | The call must raise. |
| 337 | `def test_invalid(self):` | Test invalid data. |
| 338–339 | `with self.assertRaises(TypeError): count([1, "two"])` | The call must raise `TypeError`. |

## 2.14 `TestExtremes` (lines 342–377)

| Lines | Code | Explanation |
|---|---|---|
| 342 | `class TestExtremes(unittest.TestCase):` | Focused tests for `min_`, `max_`, and `data_range`. |
| 343 | `def test_hand_checked(self):` | Test with a hand-checked dataset. |
| 344 | `data = [4, 8, 6, 5, 3, 7]` | The dataset. |
| 345 | `self.assertEqual(min_(data), 3.0)` | Minimum is 3. |
| 346 | `self.assertEqual(max_(data), 8.0)` | Maximum is 8. |
| 347 | `self.assertEqual(data_range(data), 5.0)` | Range is 5. |
| 349 | `def test_negative_values(self):` | Test negative numbers. |
| 350 | `data = [-5, -1, -3]` | The dataset. |
| 351 | `self.assertEqual(min_(data), -5.0)` | Minimum is -5. |
| 352 | `self.assertEqual(max_(data), -1.0)` | Maximum is -1. |
| 353 | `self.assertEqual(data_range(data), 4.0)` | Range is 4. |
| 355 | `def test_float_values(self):` | Test float values. |
| 356 | `data = [1.5, 2.5]` | The dataset. |
| 357 | `self.assertEqual(min_(data), 1.5)` | Minimum is 1.5. |
| 358 | `self.assertEqual(max_(data), 2.5)` | Maximum is 2.5. |
| 359 | `self.assertEqual(data_range(data), 1.0)` | Range is 1.0. |
| 361 | `def test_missing_drop(self):` | Test the default drop policy. |
| 362 | `data = [4, None, 8, float("nan"), 6]` | The dataset with missing values. |
| 363 | `self.assertEqual(min_(data), 4.0)` | Minimum over clean values. |
| 364 | `self.assertEqual(max_(data), 8.0)` | Maximum over clean values. |
| 365 | `self.assertEqual(data_range(data), 4.0)` | Range over clean values. |
| 367 | `def test_raise(self):` | Test the raise policy. |
| 368 | `for fn in (min_, max_, data_range):` | Tries the three functions. |
| 369 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 370–371 | `with self.assertRaises(ValueError): fn([1, None], policy="raise")` | Each must raise. |
| 373 | `def test_invalid(self):` | Test invalid data. |
| 374 | `for fn in (min_, max_, data_range):` | Tries the three functions. |
| 375 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 376–377 | `with self.assertRaises(TypeError): fn([1, "two"])` | Each must raise `TypeError`. |

## 2.15 `TestFrequencyTable` (lines 380–426)

| Lines | Code | Explanation |
|---|---|---|
| 380 | `class TestFrequencyTable(unittest.TestCase):` | Focused tests for `frequency_table`. |
| 381 | `def test_hand_checked(self):` | Test with a hand-checked dataset. |
| 382–385 | `self.assertEqual(frequency_table([4, 8, 6, 5, 3, 7]), {...})` | Every value appears once. |
| 387 | `def test_empty(self):` | Test empty input. |
| 388 | `self.assertEqual(frequency_table([]), {})` | The table is empty. |
| 390 | `def test_single(self):` | Test one value. |
| 391 | `self.assertEqual(frequency_table([7]), {7.0: 1})` | The value appears once. |
| 393 | `def test_constant(self):` | Test constant values. |
| 394 | `self.assertEqual(frequency_table([4, 4, 4]), {4.0: 3})` | The value appears three times. |
| 396 | `def test_tied(self):` | Test tied values. |
| 397–400 | `self.assertEqual(frequency_table([1, 2, 2, 3, 3]), {1.0: 1, 2.0: 2, 3.0: 2})` | Ties keep every key and count. |
| 402 | `def test_missing_drop(self):` | Test the default drop policy. |
| 403–406 | `self.assertEqual(frequency_table([1, None, 2, float("nan"), 2]), {1.0: 1, 2.0: 2})` | Missing values are removed. |
| 408 | `def test_raise(self):` | Test the raise policy. |
| 409–410 | `with self.assertRaises(ValueError): frequency_table([1, None], policy="raise")` | The call must raise. |
| 412 | `def test_invalid(self):` | Test invalid data. |
| 413–414 | `with self.assertRaises(TypeError): frequency_table([1, "two"])` | The call must raise `TypeError`. |
| 416 | `def test_keys_are_sorted(self):` | Test deterministic key order. |
| 417–420 | `self.assertEqual(list(frequency_table([3, 1, 2, 1])), [1.0, 2.0, 3.0])` | Keys are ascending. |
| 422 | `def test_int_and_float_share_a_key(self):` | Test numeric equality of keys. |
| 423 | `self.assertEqual(frequency_table([1, 1.0]), {1.0: 2})` | `1` and `1.0` share one entry. |
| 425 | `def test_negative_zero_and_zero_share_a_key(self):` | Test signed zero. |
| 426 | `self.assertEqual(frequency_table([0.0, -0.0]), {0.0: 2})` | `0.0` and `-0.0` share one entry. |

## 2.16 `TestOneShotIterators` (lines 429–458)

| Lines | Code | Explanation |
|---|---|---|
| 429 | `class TestOneShotIterators(unittest.TestCase):` | Tests the one-consumption guarantee. |
| 430 | `def test_one_shot_iterator(self):` | Test every reduction with a one-shot iterator. |
| 431–437 | `cases = ((count, 3), (min_, 1.0), (max_, 3.0), (data_range, 2.0), (frequency_table, {...}))` | Pairs each function with its expected result. |
| 438 | `for fn, expected in cases:` | Runs each pair. |
| 439 | `with self.subTest(fn=fn.__name__):` | Labels the failing function. |
| 440 | `data = OneShot([1, 2, 3])` | Creates a fresh one-shot iterator. |
| 441 | `self.assertEqual(fn(data), expected)` | Checks the result. |
| 442 | `self.assertEqual(data.iterations, 1)` | The iterator was consumed exactly once. |
| 444 | `def test_one_shot_iterator_with_missing_values(self):` | Test a one-shot iterator containing missing values. |
| 445 | `data = OneShot([1, None, float("nan"), 4])` | The one-shot input. |
| 446 | `self.assertEqual(count(data), 2)` | The count is correct. |
| 447 | `self.assertEqual(data.iterations, 1)` | Consumed exactly once. |
| 449 | `def test_one_shot_iterator_for_helpers(self):` | Test the helpers with a one-shot iterator. |
| 450–454 | `for fn, expected in ((count_missing, 1), (clean_values, [1.0, 2.0]), (prepare_data, ([1.0, 2.0], 1))):` | Pairs each helper with its expected result. |
| 455 | `with self.subTest(fn=fn.__name__):` | Labels the failing helper. |
| 456 | `data = OneShot([1, None, 2])` | Creates a fresh one-shot iterator. |
| 457 | `self.assertEqual(fn(data), expected)` | Checks the result. |
| 458 | `self.assertEqual(data.iterations, 1)` | Consumed exactly once. |

## 2.17 `TestAliases` (lines 461–485)

| Lines | Code | Explanation |
|---|---|---|
| 461 | `class TestAliases(unittest.TestCase):` | Tests the short and descriptive aliases. |
| 462 | `def test_prompt_names_point_at_the_same_functions(self):` | Test the prompt names. |
| 463 | `self.assertIs(descriptive.min, descriptive.min_)` | `min` is `min_`. |
| 464 | `self.assertIs(descriptive.max, descriptive.max_)` | `max` is `max_`. |
| 465 | `self.assertIs(descriptive.range, descriptive.data_range)` | `range` is `data_range`. |
| 467 | `def test_prompt_names_are_importable(self):` | Test `from ... import min, max, range`. |
| 468 | `from stateskol.descriptive import max as max_fn` | Imports `max` under a safe local name. |
| 469 | `from stateskol.descriptive import min as min_fn` | Imports `min` under a safe local name. |
| 470 | `from stateskol.descriptive import range as range_fn` | Imports `range` under a safe local name. |
| 472 | `self.assertEqual(min_fn([3, 1, 2]), 1.0)` | The imported `min` works. |
| 473 | `self.assertEqual(max_fn([3, 1, 2]), 3.0)` | The imported `max` works. |
| 474 | `self.assertEqual(range_fn([3, 1, 2]), 2.0)` | The imported `range` works. |
| 476 | `def test_short_names_do_not_shadow_builtins_in_module_globals(self):` | Test the no-shadowing design. |
| 477 | `for name in ("min", "max", "range"):` | Checks each short name. |
| 478 | `with self.subTest(name=name):` | Labels the failing name. |
| 479 | `self.assertNotIn(name, descriptive.__dict__)` | The name is not bound in the module globals. |
| 480 | `self.assertIn(name, dir(descriptive))` | But it is visible through `dir()`. |
| 482 | `def test_descriptive_aliases(self):` | Test the descriptive aliases. |
| 483 | `self.assertIs(descriptive.minimum, descriptive.min_)` | `minimum` is `min_`. |
| 484 | `self.assertIs(descriptive.maximum, descriptive.max_)` | `maximum` is `max_`. |
| 485 | `self.assertIs(descriptive.value_range, descriptive.data_range)` | `value_range` is `data_range`. |

## 2.18 `TestDocumentedBoundaryTable` (lines 488–516)

| Lines | Code | Explanation |
|---|---|---|
| 488 | `class TestDocumentedBoundaryTable(unittest.TestCase):` | Checks that the documented table is true. |
| 489 | `def test_every_valid_case_has_one_answer(self):` | One test for every valid case. |
| 490–497 | `expected = {...}` | Maps each case name to `(count, frequency_table, empty_after_policy)`. |
| 498 | `for case in VALID_BOUNDARY_CASES:` | Runs every valid case. |
| 499 | `with self.subTest(case=case.name):` | Labels the failing case. |
| 500–502 | `expected_count, expected_table, empty_after_policy = expected[case.name]` | Unpacks the expected values. |
| 503 | `self.assertEqual(count(case.data), expected_count)` | Checks the count. |
| 504 | `self.assertEqual(frequency_table(case.data), expected_table)` | Checks the table. |
| 505 | `if empty_after_policy:` | Cases that become empty after dropping. |
| 506 | `for fn in (min_, max_, data_range):` | Tries the three extremes. |
| 507–508 | `with self.assertRaises(ValueError): fn(case.data)` | They must raise. |
| 509 | `else:` | Cases with clean data. |
| 510 | `cleaned = clean_values(case.data)` | Gets the clean values. |
| 511 | `self.assertEqual(min_(case.data), min(cleaned))` | `min_` matches the built-in minimum of the clean data. |
| 512 | `self.assertEqual(max_(case.data), max(cleaned))` | `max_` matches the built-in maximum of the clean data. |
| 513–516 | `self.assertEqual(data_range(case.data), max(cleaned) - min(cleaned))` | `data_range` matches the span of the clean data. |

## 2.19 `TestRequireNonempty` (lines 519–530)

| Lines | Code | Explanation |
|---|---|---|
| 519 | `class TestRequireNonempty(unittest.TestCase):` | Tests `require_nonempty`. |
| 520 | `def test_nonempty_is_returned(self):` | Test that a non-empty sequence is returned unchanged. |
| 521 | `values = [1, 2, 3]` | A non-empty list. |
| 522 | `self.assertIs(require_nonempty(values), values)` | The exact same object is returned. |
| 524 | `def test_empty_raises_value_error(self):` | Test empty input. |
| 525–526 | `with self.assertRaises(ValueError): require_nonempty([])` | The call must raise. |
| 528 | `def test_name_appears_in_message(self):` | Test the custom name in the error. |
| 529–530 | `with self.assertRaisesRegex(ValueError, "sample"): require_nonempty([], name="sample")` | The message contains `"sample"`. |

## 2.20 Main guard (lines 533–534)

| Lines | Code | Explanation |
|---|---|---|
| 533 | `if __name__ == "__main__":` | Runs only when the file is executed directly. |
| 534 | `unittest.main()` | Starts the unittest runner. |

---

# 3. `examples/clean_env_demo.py`

| Lines | Code | Explanation |
|---|---|---|
| 1–7 | `"""Clean-environment demo ... clean_env_demo.py` | Docstring: says the demo uses only the standard library and shows how to run it. |
| 9–16 | `from stateskol.descriptive import (...)` | Imports the boundary pack and the five public functions used in the demo. |
| 19 | `def main() -> None:` | Defines the demo entry point. |
| 20 | `raw = [4, 8, 6, 5, 3, 7, None, float("nan")]` | A small dataset with two missing values. |
| 21 | `print("raw:", raw)` | Shows the raw input. |
| 22 | `print("count:", count(raw))` | Shows the count after dropping missing values. |
| 23 | `print("min:", min_(raw))` | Shows the minimum. |
| 24 | `print("max:", max_(raw))` | Shows the maximum. |
| 25 | `print("range:", data_range(raw))` | Shows the range. |
| 26 | `print("frequency_table:", frequency_table(raw))` | Shows the frequency table. |
| 27 | `print()` | Prints a blank line. |
| 28 | `print("Canonical boundary cases:")` | Prints a heading. |
| 29 | `for case in BOUNDARY_CASES:` | Visits every canonical case. |
| 30 | `print("-", case.name, ":", case.description)` | Prints the case name and its rule. |
| 33 | `if __name__ == "__main__":` | Runs the demo only when executed directly. |
| 34 | `main()` | Calls the entry point. |

---

# 4. `examples/reference_check.py`

| Lines | Code | Explanation |
|---|---|---|
| 1–9 | `"""Reference evidence ... reference_check.py` | Docstring: says this is the only place a third-party library may appear. |
| 11 | `try:` | Starts an optional import. |
| 12 | `import numpy` | Imports NumPy for the comparison. |
| 13–14 | `except ImportError: numpy = None` | If NumPy is missing, the script prints a message instead of crashing. |
| 16 | `from stateskol.descriptive import count, data_range, frequency_table, max_, min_` | Imports the functions being checked. |
| 19 | `def check(name, ours, theirs, tol=0.0):` | Helper that compares one result and prints one line. |
| 20 | `"""Compare one result and print a single evidence line."""` | Docstring. |
| 21 | `if isinstance(ours, dict):` | A frequency table needs equality, not subtraction. |
| 22 | `ok = ours == theirs` | Dicts are compared directly. |
| 23 | `diff = 0.0 if ok else float("nan")` | A readable difference value for the printout. |
| 24 | `else:` | Numeric results use subtraction. |
| 25 | `diff = abs(ours - theirs)` | Absolute difference. |
| 26 | `ok = diff <= tol` | The result is acceptable when the difference is within tolerance. |
| 27–30 | `print("%-28s ours=%r theirs=%r diff=%r %s" % (...))` | Prints one evidence line with `ok` or `MISMATCH`. |
| 31 | `return ok` | Returns the comparison result. |
| 34 | `def main() -> None:` | Defines the reference-check entry point. |
| 35 | `if numpy is None:` | Checks whether NumPy is available. |
| 36 | `print("numpy not installed; ...")` | Explains how to fix the missing dependency. |
| 37 | `return` | Stops without failing. |
| 39 | `data = [4.0, 8.0, 6.0, 5.0, 3.0, 7.0, 3.0]` | The shared dataset. |
| 40 | `ok = True` | Starts with a passing result. |
| 41 | `ok &= check("count", count(data), int(numpy.size(data)), 0)` | Compares the count. |
| 42 | `ok &= check("min", min_(data), float(numpy.min(data)), 0.0)` | Compares the minimum. |
| 43 | `ok &= check("max", max_(data), float(numpy.max(data)), 0.0)` | Compares the maximum. |
| 44 | `ok &= check("range", data_range(data), float(numpy.ptp(data)), 0.0)` | Compares the range with NumPy's peak-to-peak. |
| 46 | `values, counts = numpy.unique(data, return_counts=True)` | Gets NumPy's unique values and their counts. |
| 47 | `expected = {float(value): int(freq) for value, freq in zip(values, counts)}` | Converts them into a plain dict. |
| 48 | `ok &= check("frequency_table", frequency_table(data), expected, 0)` | Compares the frequency table. |
| 50 | `if not ok:` | Checks whether any comparison failed. |
| 51 | `raise SystemExit("reference mismatch, ...")` | Fails the script with a clear message. |
| 52 | `print("all reference checks match")` | Reports success. |
| 55 | `if __name__ == "__main__":` | Runs the script only when executed directly. |
| 56 | `main()` | Calls the entry point. |

---

# 5. How to run everything

From the repository root:

```bash
# Unit tests
python -m unittest discover -s tests -v

# Doctests
python -m doctest src/stateskol/descriptive.py

# Standard-library-only demo
python examples/clean_env_demo.py

# Reference comparison (needs numpy)
python examples/reference_check.py
```

If the package is not installed, add `src` to `PYTHONPATH`:

```powershell
$env:PYTHONPATH="src"
```

On this machine, the global pytest install auto-loads a broken `web3`
plugin. If `python -m pytest` fails before collecting tests, run:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest -q
```

---

# 6. Design decisions in one place

1. **One module, marked block.** All implementation code is inside
   `src/stateskol/descriptive.py`, between the two `# ----- Welasma: ... -----`
   markers.
2. **Float contract.** Accepted numeric inputs are converted to `float` once,
   in `to_float_list`. Every other function works on that clean, validated
   list.
3. **Missing policy first.** Every public function validates the policy before
   consuming the input, so a bad policy cannot consume a one-shot iterator.
4. **One pass.** `to_float_list` consumes the original iterable once; the
   remaining work happens on a list.
5. **Boundary cases are data.** The canonical cases are reusable
   `BoundaryCase` objects in `BOUNDARY_CASES`, so the rest of the team can
   import them instead of copying magic numbers.
6. **Short names without shadowing.** `min`, `max`, and `range` are exposed
   through module `__getattr__`. They are importable, but they are not bound
   in the module globals, so other owners can still use the built-ins.
7. **Deterministic frequency tables.** Keys are sorted ascending, and equal
   values share one entry.

