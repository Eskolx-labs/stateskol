
"""Descriptive statistics and data-quality utilities.

This module provides basic descriptive statistics and missing-data
reporting using only the Python standard library.

Input contract:
    - Input must be an iterable of real numerical observations.
    - Integers and floats are accepted.
    - Boolean values and strings are rejected.
    - Decimal and Fraction values are rejected.
    - None and NaN are treated as missing observations.
    - Positive and negative infinity are rejected.
    - Integers with absolute values greater than 2**53 are rejected.
    - Input data is not modified.
    - Generators are consumed only once.

Missingness policies:
    - "drop": exclude missing observations and issue a warning.
    - "strict": raise ValueError when missing observations are found.

Empty-data behavior:
    - count([]) returns 0.
    - min([]), max([]), range([]), and frequency_table([])
      raise EmptyDataError.
"""

import math
import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from numbers import Real


MAX_EXACT_INTEGER = 2**53
VALID_POLICIES = ("drop", "strict")
VALID_MISSINGNESS_MECHANISMS = ("unknown", "MCAR", "MAR", "MNAR")

class EmptyDataError(ValueError):
    """Raised when a statistical calculation requires nonempty data."""


@dataclass(frozen=True)
class MissingReport:
    """Summary of missing observations in a dataset."""

    n_total: int
    n_present: int
    n_missing: int
    missing_positions: tuple[int, ...]


@dataclass(frozen=True)
class DataAudit:
    """Structured audit report for a numerical dataset.

    Records observation counts, missing positions, the missing-data
    policy and its assumption, numerical summaries, observed input
    types, and a concise summary for reviewers.
    """

    n_total: int
    n_present: int
    n_missing: int
    missing_positions: tuple[int, ...]
    policy: str
    missingness_mechanism: str
    assumption: str
    minimum: Real | None
    maximum: Real | None
    data_range: Real | None
    input_types: tuple[str, ...]
    summary: str

def _is_missing(value: object) -> bool:
    """Return whether a value is None or a floating-point NaN."""
    return value is None or (
        isinstance(value, float) and math.isnan(value)
    )


def _validate_observation(value: object) -> Real:
    """Validate one non-missing numerical observation.

    Args:
        value: The observation to validate.

    Returns:
        The validated numerical observation.

    Raises:
        TypeError: If the value is not an accepted real number.
        ValueError: If the value is infinite or an integer exceeds
            the supported exact-integer limit.
    """
    if isinstance(value, bool) or type(value) not in (int, float):
        raise TypeError(
            f"Expected a real number, got {type(value).__name__}."
        )

    if isinstance(value, int) and abs(value) > MAX_EXACT_INTEGER:
        raise ValueError(
            "Integer values with absolute magnitude greater than "
            "2**53 are not supported."
        )

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Infinite values are not supported.")

    return value


def _get_iterator(data: Iterable):
    """Validate the input container and return its iterator."""
    if isinstance(data, (str, bytes)):
        raise TypeError("Data must be an iterable of real numbers.")

    try:
        return iter(data)
    except TypeError:
        raise TypeError(
            "Data must be an iterable of real numbers."
        ) from None


def _prepare_data(
    data: Iterable,
    policy: str = "drop",
) -> tuple[list[Real], int]:
    """Validate observations and handle missing values.

    Args:
        data: An iterable of real numerical observations.
        policy: "drop" excludes missing observations; "strict"
            raises an error if missing observations are encountered.

    Returns:
        A tuple containing the valid observations and the number
        of missing observations encountered.

    Raises:
        TypeError: If the input is not iterable or contains invalid types.
        ValueError: If the policy is invalid, infinity is encountered,
            an unsupported integer is encountered, or strict policy
            encounters a missing observation.
    """
    if policy not in VALID_POLICIES:
        raise ValueError(
            "Policy must be either 'drop' or 'strict'."
        )

    iterator = _get_iterator(data)

    values = []
    dropped = 0

    for value in iterator:
        if _is_missing(value):
            if policy == "strict":
                raise ValueError(
                    "Missing observations are not allowed."
                )

            dropped += 1
            continue

        values.append(_validate_observation(value))

    if dropped:
        warnings.warn(
            f"Dropped {dropped} missing observation(s).",
            UserWarning,
            stacklevel=2,
        )

    return values, dropped


def count(
    data: Iterable,
    *,
    policy: str = "drop",
) -> int:
    """Return the number of valid numerical observations.

    Args:
        data: An iterable of real numerical observations.
        policy: Missingness policy, either "drop" or "strict".

    Returns:
        The number of valid observations. Returns 0 for empty input.

    Raises:
        TypeError: If an observation has an invalid type.
        ValueError: If the policy or an observation is invalid.
    """
    values, _ = _prepare_data(data, policy=policy)
    return len(values)


def min(
    data: Iterable,
    *,
    policy: str = "drop",
) -> Real:
    """Return the smallest valid observation.

    Args:
        data: An iterable of real numerical observations.
        policy: Missingness policy, either "drop" or "strict".

    Returns:
        The smallest numerical observation.

    Raises:
        EmptyDataError: If no valid observations remain.
        TypeError: If an observation has an invalid type.
        ValueError: If the policy or an observation is invalid.
    """
    values, _ = _prepare_data(data, policy=policy)

    if not values:
        raise EmptyDataError(
            "Cannot calculate minimum of empty data."
        )

    smallest = values[0]

    for value in values[1:]:
        if value < smallest:
            smallest = value

    return smallest


def max(
    data: Iterable,
    *,
    policy: str = "drop",
) -> Real:
    """Return the largest valid observation.

    Args:
        data: An iterable of real numerical observations.
        policy: Missingness policy, either "drop" or "strict".

    Returns:
        The largest numerical observation.

    Raises:
        EmptyDataError: If no valid observations remain.
        TypeError: If an observation has an invalid type.
        ValueError: If the policy or an observation is invalid.
    """
    values, _ = _prepare_data(data, policy=policy)

    if not values:
        raise EmptyDataError(
            "Cannot calculate maximum of empty data."
        )

    largest = values[0]

    for value in values[1:]:
        if value > largest:
            largest = value

    return largest


def range(
    data: Iterable,
    *,
    policy: str = "drop",
) -> Real:
    """Return the difference between the largest and smallest values.

    Args:
        data: An iterable of real numerical observations.
        policy: Missingness policy, either "drop" or "strict".

    Returns:
        The numerical range: maximum minus minimum.

    Raises:
        EmptyDataError: If no valid observations remain.
        TypeError: If an observation has an invalid type.
        ValueError: If the policy or an observation is invalid.
    """
    values, _ = _prepare_data(data, policy=policy)

    if not values:
        raise EmptyDataError(
            "Cannot calculate range of empty data."
        )

    smallest = values[0]
    largest = values[0]

    for value in values[1:]:
        if value < smallest:
            smallest = value

        if value > largest:
            largest = value

    return largest - smallest


def frequency_table(
    data: Iterable,
    *,
    policy: str = "drop",
) -> dict[Real, int]:
    """Return a sorted frequency table of valid observations.

    Args:
        data: An iterable of real numerical observations.
        policy: Missingness policy, either "drop" or "strict".

    Returns:
        A dictionary mapping each unique observation to its frequency,
        ordered by numerical value.

    Raises:
        EmptyDataError: If no valid observations remain.
        TypeError: If an observation has an invalid type.
        ValueError: If the policy or an observation is invalid.
    """
    values, _ = _prepare_data(data, policy=policy)

    if not values:
        raise EmptyDataError(
            "Cannot create frequency table from empty data."
        )

    frequencies = {}

    for value in values:
        frequencies[value] = frequencies.get(value, 0) + 1

    return dict(sorted(frequencies.items()))


def maximum(
    data: Iterable,
    *,
    policy: str = "drop",
) -> Real:
    """Return the largest valid observation.

    This is the Core B public function for maximum.
    """
    return max(data, policy=policy)


def data_range(
    data: Iterable,
    *,
    policy: str = "drop",
) -> Real:
    """Return the difference between the largest and smallest values.

    This is the Core B public function for range.
    """
    return range(data, policy=policy)


def missing_report(
    data: Iterable,
    *,
    policy: str = "drop",
) -> MissingReport:
    """Report the number and positions of missing observations.

    Missing positions use zero-based indexing. This function validates
    all present observations but does not issue a drop warning because
    its purpose is to report missingness rather than calculate a
    statistic.

    Args:
        data: An iterable of numerical observations.
        policy: "drop" reports missing values; "strict" rejects them.

    Returns:
        A MissingReport containing total, present, and missing counts
        and the zero-based positions of missing observations.

    Raises:
        TypeError: If data is not iterable or contains invalid types.
        ValueError: If policy is invalid or strict policy encounters
            missing observations.
    """
    if policy not in VALID_POLICIES:
        raise ValueError(
            "Policy must be either 'drop' or 'strict'."
        )

    iterator = _get_iterator(data)

    n_total = 0
    n_present = 0
    missing_positions = []

    for position, value in enumerate(iterator):
        n_total += 1

        if _is_missing(value):
            if policy == "strict":
                raise ValueError(
                    "Missing observations are not allowed."
                )

            missing_positions.append(position)
        else:
            _validate_observation(value)
            n_present += 1

    return MissingReport(
        n_total=n_total,
        n_present=n_present,
        n_missing=len(missing_positions),
        missing_positions=tuple(missing_positions),
    )



def audit(
    data: Iterable,
    *,
    policy: str = "drop",
    missingness_mechanism: str = "unknown",
) -> DataAudit:
    """Audit a numerical dataset and report its quality.

    Args:
        data: An iterable of numerical observations.
        policy: "drop" reports and excludes missing values;
            "strict" raises an error when missing values occur.

    Returns:
        A DataAudit containing observation counts, missing positions,
        policy, missingness assumption, numerical summaries,
        encountered input types, and a reviewer-ready summary.

    Raises:
        TypeError: If data is not iterable or contains invalid types.
        ValueError: If the policy is invalid, an unsupported integer
            or infinity is encountered, or strict policy encounters
            missing observations.

    Notes:
        The missingness mechanism is recorded as unknown. Dropping
        missing observations does not establish that the remaining
        observations are unbiased.
    """
    if policy not in VALID_POLICIES:
        raise ValueError(
            "Policy must be either 'drop' or 'strict'."
        )

    if missingness_mechanism not in VALID_MISSINGNESS_MECHANISMS:
        raise ValueError(
            "Missingness mechanism must be one of "
            "'unknown', 'MCAR', 'MAR', or 'MNAR'."
        )
    iterator = _get_iterator(data)
    values = []
    missing_positions = []
    input_types = []

    for position, value in enumerate(iterator):
        type_name = type(value).__name__

        if type_name not in input_types:
            input_types.append(type_name)

        if _is_missing(value):
            if policy == "strict":
                raise ValueError(
                    "Missing observations are not allowed."
                )

            missing_positions.append(position)
            continue

        values.append(_validate_observation(value))

    n_total = len(values) + len(missing_positions)
    n_present = len(values)
    n_missing = len(missing_positions)

    if values:
        minimum_value = values[0]
        maximum_value = values[0]

        for value in values[1:]:
            if value < minimum_value:
                minimum_value = value

            if value > maximum_value:
                maximum_value = value

        data_range_value = maximum_value - minimum_value
    else:
        minimum_value = None
        maximum_value = None
        data_range_value = None

    if n_missing:
        assumption = "Unknown"
    else:
        assumption = "No missing observations; mechanism not assessed"

    summary = (
        f"Audited {n_total} observations: "
        f"{n_present} present, {n_missing} missing; "
        f"policy={policy}; "
f"mechanism={missingness_mechanism}; "
f"assumption={assumption}."
    )

    return DataAudit(
        n_total=n_total,
        n_present=n_present,
        n_missing=n_missing,
        missing_positions=tuple(missing_positions),
        policy=policy,
missingness_mechanism=missingness_mechanism,
assumption=assumption,
        minimum=minimum_value,
        maximum=maximum_value,
        data_range=data_range_value,
        input_types=tuple(input_types),
        summary=summary,
    )
