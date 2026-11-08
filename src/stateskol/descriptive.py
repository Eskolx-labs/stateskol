"""Descriptive statistics in pure Python. Stateskol Week 1.

This module is the single home for Week 1 code. Each owner edits only the
block marked with their name. The marker shape is the one established by the
repository seed::

    # ----- Owner: topic -----

Welasma's block is the counting and boundary-case pack. It is the shared floor
that Kaleb, Philimon, Yoseph, and Yonas import in their own tests, so the
rules below are deliberately explicit.

Input contract
--------------
A data argument is any iterable of real numbers. ``int``, ``float``,
``fractions.Fraction``, and ``decimal.Decimal`` are accepted and converted to
``float``. ``bool`` is rejected even though it is an ``int`` subclass.
``str``, ``bytes``, ``bytearray``, ``complex``, and every other non-numeric
value raise ``TypeError``. ``inf`` and ``-inf`` raise ``ValueError``. ``None``
and ``NaN`` are missing values and are handled by the policy argument.

Missing-data policy
-------------------
``"drop"`` (the default) removes ``None`` and ``NaN`` and reports how many
were removed through :func:`apply_missing` or :func:`prepare_data`.
``"raise"`` stops at the first missing value with ``ValueError``. The policy
is validated before the input iterator is consumed, so an invalid policy
never consumes a one-shot iterator. Every function consumes its input exactly
once.

Boundary-case table
-------------------
The canonical cases live in :data:`BOUNDARY_CASES`. Their one correct
behaviour is:

``empty``
    ``count`` is 0; ``min``/``max``/``range`` raise ``ValueError``;
    ``frequency_table`` is ``{}``.

``single``
    ``count`` is 1; ``min`` and ``max`` are the value; ``range`` is 0.0;
    ``frequency_table`` is ``{value: 1}``.

``constant``
    ``count`` is n; ``min`` and ``max`` are the value; ``range`` is 0.0;
    ``frequency_table`` is ``{value: n}``.

``tied``
    ``count`` is n; ``min`` and ``max`` are the true extremes; ``range`` is
    the true span; ``frequency_table`` keeps every key and its count. A tie
    is simply several keys with the same count; no key is special.

``missing``
    With the default ``"drop"`` policy, ``None`` and ``NaN`` are removed
    first, then the four rules above apply to the clean values.

``all-missing``
    Every value is removed, so this behaves like ``empty``: ``count`` is 0,
    the extremes raise ``ValueError``, and ``frequency_table`` is ``{}``.

``invalid``
    A non-numeric element raises ``TypeError`` from every function. An
    infinite value raises ``ValueError`` from every function.

``range`` is always ``max - min``. It is ``0.0`` for one value and for
constant values, and it raises ``ValueError`` when no value survives the
missing policy.

``frequency_table`` groups equal values. Keys are returned in ascending
order. A tie is simply several keys with the same count; no key is special.
"""

from __future__ import annotations

import decimal
import math
import numbers
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Sequence

# ----- Welasma: counting and boundary pack -----


class MissingPolicy(str, Enum):
    """How missing values (``None`` and ``NaN``) are handled.

    ``DROP`` removes them and reports the count. ``RAISE`` stops at the first
    one with ``ValueError``. The string values are part of the public API
    because callers pass ``"drop"`` or ``"raise"`` directly.
    """

    DROP = "drop"
    RAISE = "raise"


def _coerce_policy(policy: MissingPolicy | str) -> MissingPolicy:
    """Return a :class:`MissingPolicy` without touching the data.

    This is deliberately called before any iterable is consumed. An unknown
    policy raises ``ValueError``.
    """
    if isinstance(policy, MissingPolicy):
        return policy
    if isinstance(policy, str):
        try:
            return MissingPolicy(policy)
        except ValueError:
            pass
    raise ValueError(
        "unknown missing-data policy: %r (use 'drop' or 'raise')" % (policy,)
    )


def is_missing(value: object) -> bool:
    """Return ``True`` for ``None`` and for a float ``NaN``.

    Everything else, including ``0.0``, ``False``, and a string, is not a
    missing value. Validation is a separate step; a string is invalid data,
    not missing data.
    """
    return value is None or (isinstance(value, float) and math.isnan(value))


def to_float_list(values: Iterable[object]) -> list[float | None]:
    """Contract an iterable of numbers into a list of floats.

    Parameters
    ----------
    values:
        Any iterable of real numbers. A string, bytes object, or bytearray is
        rejected as a container so ``"123"`` is not read as three values.

    Returns
    -------
    list[float | None]
        One entry per input value, in input order. ``int``,
        ``fractions.Fraction``, and ``decimal.Decimal`` values become
        ``float``. ``None`` and ``NaN`` are preserved for the missing policy.
        ``inf`` and ``-inf`` are rejected.

    Raises
    ------
    TypeError
        If ``values`` is not iterable, or if an element is a ``bool``,
        ``str``, ``bytes``, ``complex``, or another non-real value.
    ValueError
        If an element is infinite or too large to represent as a float.

    Examples
    --------
    >>> to_float_list([1, 2.5, None])
    [1.0, 2.5, None]
    >>> to_float_list([1, True])
    Traceback (most recent call last):
        ...
    TypeError: bools are not numeric data, got True
    """
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError("data must be an iterable of numbers, not a string")
    try:
        items = list(values)
    except TypeError:
        raise TypeError("data must be an iterable of numbers") from None

    contracted: list[float | None] = []
    for value in items:
        if value is None:
            contracted.append(None)
            continue
        if isinstance(value, bool):
            raise TypeError("bools are not numeric data, got %r" % (value,))
        if isinstance(value, decimal.Decimal):
            if value.is_nan():
                contracted.append(float("nan"))
            elif value.is_infinite():
                raise ValueError(
                    "infinite values are not accepted as data: %r" % (value,)
                )
            else:
                try:
                    contracted.append(float(value))
                except (OverflowError, ValueError):
                    raise ValueError(
                        "numeric value cannot be represented as a float: %r"
                        % (value,)
                    ) from None
            continue
        if not isinstance(value, numbers.Real):
            raise TypeError(
                "non-numeric value in data: %r (%s)"
                % (value, type(value).__name__)
            )
        try:
            contracted.append(float(value))
        except (OverflowError, ValueError):
            raise ValueError(
                "numeric value cannot be represented as a float: %r" % (value,)
            ) from None

    for value in contracted:
        if isinstance(value, float) and math.isinf(value):
            raise ValueError(
                "infinite values are not accepted as data: %r" % (value,)
            )
    return contracted


def require_nonempty(values: Sequence[Any], name: str = "data") -> Sequence[Any]:
    """Return ``values`` unchanged, or raise ``ValueError`` when it is empty.

    This helper expects a sized sequence, which is what the public functions
    pass after contracting the input. The ``name`` is used in the error
    message so callers can say which statistic needed data.
    """
    if len(values) == 0:
        raise ValueError("empty input: %s needs at least one value" % (name,))
    return values


def apply_missing(
    values: Iterable[float | None],
    policy: MissingPolicy | str = "drop",
) -> tuple[list[float], int]:
    """Split contracted values into clean data and a dropped count.

    Parameters
    ----------
    values:
        Output of :func:`to_float_list`: floats and ``None`` only. A non-float
        that is not ``None`` is a programming error and raises ``TypeError``.
    policy:
        ``"drop"`` or ``"raise"``. The policy is validated before iteration.

    Returns
    -------
    (clean, dropped):
        ``clean`` is a new list of finite floats. ``dropped`` is the number of
        ``None`` and ``NaN`` values removed. Under ``"raise"`` the function
        never returns a dropped count; it raises on the first missing value.

    Raises
    ------
    ValueError
        For an unknown policy, or for the first missing value under
        ``"raise"``.
    TypeError
        If ``values`` contains a value that is neither a float nor ``None``.

    Examples
    --------
    >>> apply_missing([1.0, None, float("nan"), 4.0])
    ([1.0, 4.0], 2)
    >>> apply_missing([1.0, None], "raise")
    Traceback (most recent call last):
        ...
    ValueError: missing value found under policy 'raise'
    """
    policy = _coerce_policy(policy)
    clean: list[float] = []
    dropped = 0
    for value in values:
        if value is None:
            if policy is MissingPolicy.RAISE:
                raise ValueError("missing value found under policy 'raise'")
            dropped += 1
            continue
        if not isinstance(value, float):
            raise TypeError(
                "apply_missing expects to_float_list output; got %r (%s)"
                % (value, type(value).__name__)
            )
        if math.isnan(value):
            if policy is MissingPolicy.RAISE:
                raise ValueError("missing value found under policy 'raise'")
            dropped += 1
            continue
        if math.isinf(value):
            raise ValueError(
                "infinite values are not accepted as data: %r" % (value,)
            )
        clean.append(value)
    return clean, dropped


def prepare_data(
    values: Iterable[object],
    policy: MissingPolicy | str = "drop",
) -> tuple[list[float], int]:
    """Contract, validate, and apply the missing policy in one call.

    This is the boundary pack's main entry point for other owners. It consumes
    the input exactly once and returns ``(clean, dropped)``. The policy is
    validated before the iterable is touched.

    Examples
    --------
    >>> prepare_data([1, None, 2, float("nan")])
    ([1.0, 2.0], 2)
    """
    policy = _coerce_policy(policy)
    return apply_missing(to_float_list(values), policy)


def clean_values(
    values: Iterable[object],
    policy: MissingPolicy | str = "drop",
) -> list[float]:
    """Return only the clean floats after the input contract and policy.

    Examples
    --------
    >>> clean_values([1, None, 2])
    [1.0, 2.0]
    """
    return prepare_data(values, policy)[0]


def count_missing(values: Iterable[object]) -> int:
    """Count ``None`` and ``NaN`` values in a valid numeric iterable.

    The iterable is consumed once. Invalid elements raise the same errors as
    :func:`to_float_list`; this function does not silently skip them.

    Examples
    --------
    >>> count_missing([1, None, float("nan"), 4])
    2
    """
    contracted = to_float_list(values)
    return sum(1 for value in contracted if is_missing(value))


@dataclass(frozen=True, eq=False)
class BoundaryCase:
    """One canonical boundary input and the rule it pins down.

    ``data`` is a tuple so a case can be reused by many tests without one test
    mutating another test's input. Cases are identified by ``name``; equality
    is identity because a case may contain ``NaN``, which is not equal to
    itself.
    """

    name: str
    data: tuple[object, ...]
    description: str


EMPTY_INPUT = BoundaryCase(
    "empty",
    (),
    "No values: count is 0; min/max/range raise ValueError; frequency_table is {}.",
)
SINGLE_VALUE = BoundaryCase(
    "single",
    (7.0,),
    "One value: min=max=value; range=0.0; frequency_table={value: 1}.",
)
CONSTANT_VALUES = BoundaryCase(
    "constant",
    (4.0, 4.0, 4.0, 4.0),
    "All values equal: min=max=value; range=0.0; frequency_table={value: n}.",
)
TIED_VALUES = BoundaryCase(
    "tied",
    (1.0, 2.0, 2.0, 3.0, 3.0),
    "Repeated values: frequency_table keeps every key and count; min/max use the values.",
)
MISSING_VALUES = BoundaryCase(
    "missing",
    (1.0, None, float("nan"), 4.0),
    "None/NaN: default 'drop' removes them; 'raise' raises ValueError.",
)
ALL_MISSING = BoundaryCase(
    "all-missing",
    (None, float("nan")),
    "Every value is missing: after dropping, count is 0 and min/max/range raise ValueError.",
)
INVALID_VALUES = BoundaryCase(
    "invalid",
    (1.0, "two", 3.0),
    "Non-numeric element: every function raises TypeError.",
)

VALID_BOUNDARY_CASES = (
    EMPTY_INPUT,
    SINGLE_VALUE,
    CONSTANT_VALUES,
    TIED_VALUES,
    MISSING_VALUES,
    ALL_MISSING,
)
INVALID_BOUNDARY_CASES = (INVALID_VALUES,)
BOUNDARY_CASES = VALID_BOUNDARY_CASES + INVALID_BOUNDARY_CASES


def get_boundary_case(name: str) -> BoundaryCase:
    """Return the canonical case called ``name``.

    Raises ``KeyError`` for an unknown name. The lookup is linear because the
    pack is small and a module-level index would be mutable global state.

    Examples
    --------
    >>> get_boundary_case("single").data
    (7.0,)
    """
    for case in BOUNDARY_CASES:
        if case.name == name:
            return case
    raise KeyError("unknown boundary case: %r" % (name,))


def boundary_case_names() -> tuple[str, ...]:
    """Return the canonical case names in pack order.

    Examples
    --------
    >>> boundary_case_names()[:2]
    ('empty', 'single')
    """
    return tuple(case.name for case in BOUNDARY_CASES)


def count(
    values: Iterable[object],
    policy: MissingPolicy | str = "drop",
) -> int:
    """Count the clean values after the input contract and missing policy.

    Parameters
    ----------
    values:
        Iterable of real numbers. See the module docstring for the full input
        contract.
    policy:
        ``"drop"`` (default) removes ``None`` and ``NaN``; ``"raise"`` raises
        ``ValueError`` on the first missing value.

    Returns
    -------
    int
        The number of values that survive the policy. Empty input and
        all-missing input both return ``0``.

    Raises
    ------
    TypeError
        For a non-iterable container or an invalid element.
    ValueError
        For an unknown policy, an infinite value, or a missing value under
        ``"raise"``.

    Examples
    --------
    >>> count([4, 8, 6, 5, 3, 7])
    6
    >>> count([])
    0
    >>> count([1, None, float("nan"), 4])
    2
    >>> count([1, None], "raise")
    Traceback (most recent call last):
        ...
    ValueError: missing value found under policy 'raise'
    """
    policy = _coerce_policy(policy)
    clean, _ = apply_missing(to_float_list(values), policy)
    return len(clean)


def min_(
    values: Iterable[object],
    policy: MissingPolicy | str = "drop",
) -> float:
    """Return the smallest clean value.

    Empty input, and input where every value is missing, raises
    ``ValueError``. A single value or a constant input is valid and returns
    that value. Ties do not change the answer.

    Examples
    --------
    >>> min_([4, 8, 6, 5, 3, 7])
    3.0
    >>> min_([7])
    7.0
    >>> min_([])
    Traceback (most recent call last):
        ...
    ValueError: empty input: data needs at least one value
    """
    policy = _coerce_policy(policy)
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    smallest = clean[0]
    for value in clean[1:]:
        if value < smallest:
            smallest = value
    return smallest


def max_(
    values: Iterable[object],
    policy: MissingPolicy | str = "drop",
) -> float:
    """Return the largest clean value.

    Empty input, and input where every value is missing, raises
    ``ValueError``. A single value or a constant input is valid and returns
    that value. Ties do not change the answer.

    Examples
    --------
    >>> max_([4, 8, 6, 5, 3, 7])
    8.0
    >>> max_([7])
    7.0
    >>> max_([])
    Traceback (most recent call last):
        ...
    ValueError: empty input: data needs at least one value
    """
    policy = _coerce_policy(policy)
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    largest = clean[0]
    for value in clean[1:]:
        if value > largest:
            largest = value
    return largest


def data_range(
    values: Iterable[object],
    policy: MissingPolicy | str = "drop",
) -> float:
    """Return ``max - min`` over the clean values.

    A single value and a constant input both return ``0.0``. Empty input, and
    input where every value is missing, raises ``ValueError``. Ties do not
    change the answer.

    Examples
    --------
    >>> data_range([4, 8, 6, 5, 3, 7])
    5.0
    >>> data_range([7])
    0.0
    >>> data_range([4, 4, 4])
    0.0
    """
    policy = _coerce_policy(policy)
    clean, _ = apply_missing(to_float_list(values), policy)
    require_nonempty(clean)
    smallest = largest = clean[0]
    for value in clean[1:]:
        if value < smallest:
            smallest = value
        if value > largest:
            largest = value
    return largest - smallest


def frequency_table(
    values: Iterable[object],
    policy: MissingPolicy | str = "drop",
) -> dict[float, int]:
    """Return a value-to-count mapping over the clean values.

    The table is a plain ``dict``. Keys are the clean float values in
    ascending order, so the result is deterministic for a given input.
    Equal values share one entry; a tie is several keys with the same count.
    Empty input and all-missing input return ``{}``.

    Parameters
    ----------
    values:
        Iterable of real numbers.
    policy:
        ``"drop"`` (default) removes ``None`` and ``NaN``; ``"raise"`` raises
        ``ValueError`` on the first missing value.

    Returns
    -------
    dict[float, int]
        Each surviving value mapped to how many times it occurred.

    Raises
    ------
    TypeError
        For a non-iterable container or an invalid element.
    ValueError
        For an unknown policy, an infinite value, or a missing value under
        ``"raise"``.

    Examples
    --------
    >>> frequency_table([3, 1, 2, 1])
    {1.0: 2, 2.0: 1, 3.0: 1}
    >>> frequency_table([4, 4, 4])
    {4.0: 3}
    >>> frequency_table([])
    {}
    >>> frequency_table([1, None, float("nan"), 4])
    {1.0: 1, 4.0: 1}
    """
    policy = _coerce_policy(policy)
    clean, _ = apply_missing(to_float_list(values), policy)
    counts = Counter(clean)
    return {value: counts[value] for value in sorted(counts)}


minimum = min_
maximum = max_
value_range = data_range

__all__ = (
    "ALL_MISSING",
    "BOUNDARY_CASES",
    "BoundaryCase",
    "CONSTANT_VALUES",
    "EMPTY_INPUT",
    "INVALID_BOUNDARY_CASES",
    "INVALID_VALUES",
    "MISSING_VALUES",
    "MissingPolicy",
    "SINGLE_VALUE",
    "TIED_VALUES",
    "VALID_BOUNDARY_CASES",
    "apply_missing",
    "boundary_case_names",
    "clean_values",
    "count",
    "count_missing",
    "data_range",
    "frequency_table",
    "get_boundary_case",
    "is_missing",
    "max",
    "max_",
    "min",
    "min_",
    "minimum",
    "prepare_data",
    "range",
    "require_nonempty",
    "to_float_list",
    "value_range",
)


def __getattr__(name: str):
    """Expose the prompt's short names without shadowing built-ins.

    ``min``, ``max``, and ``range`` are available as module attributes and
    through ``from stateskol.descriptive import min``, but they are not bound
    in the module globals. Other owners can therefore keep using the built-in
    ``min``, ``max``, and ``range`` inside their own blocks in this same file.
    """
    if name == "min":
        return min_
    if name == "max":
        return max_
    if name == "range":
        return data_range
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(set(globals()) | {"min", "max", "range"})


# ----- end Welasma: counting and boundary pack -----
