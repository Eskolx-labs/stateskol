
"""Basic descriptive statistics for numerical datasets.

This module provides count, minimum, maximum, range, and frequency-table
functions using only the Python standard library.

Input contract:
    - Input must be an iterable of real numbers.
    - Boolean values are not accepted as numbers.
    - None and NaN are treated as missing observations.
    - Missing observations are excluded and reported through a warning.
    - Infinite values are not supported.
    - Input data is not modified.

Empty-data behavior:
    - count([]) returns 0.
    - min([]), max([]), range([]), and frequency_table([])
      raise ValueError.
"""

import math
import warnings
from collections.abc import Iterable
from numbers import Real


def _prepare_data(data: Iterable) -> tuple[list[Real], int]:
    """Validate observations and remove missing values.

    Args:
        data: An iterable containing real numerical observations.

    Returns:
        A tuple containing:
            - A list of valid numerical observations.
            - The number of missing observations removed.

    Raises:
        TypeError: If data is not iterable or contains invalid types.
        ValueError: If data contains positive or negative infinity.

    Notes:
        None and NaN are treated as missing values. Their removal
        is reported using a UserWarning.
    """
    if isinstance(data, (str, bytes)):
        raise TypeError("Data must be an iterable of real numbers.")

    try:
        iterator = iter(data)
    except TypeError:
        raise TypeError(
            "Data must be an iterable of real numbers."
        ) from None

    values = []
    dropped = 0

    for value in iterator:
        if value is None:
            dropped += 1
            continue

        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(
                f"Expected a real number, got {type(value).__name__}."
            )

        # Check floating-point values for NaN and infinity.
        # Integers and other accepted real-number types are finite.
        if isinstance(value, float):
            if math.isnan(value):
                dropped += 1
                continue

            if not math.isfinite(value):
                raise ValueError("Infinite values are not supported.")

        values.append(value)

    if dropped:
        warnings.warn(
            f"Dropped {dropped} missing observation(s).",
            UserWarning,
            stacklevel=2,
        )

    return values, dropped


def count(data: Iterable) -> int:
    """Return the number of valid numerical observations.

    Missing values are excluded and reported through a warning.

    Args:
        data: An iterable of real numbers.

    Returns:
        The number of valid observations. Returns 0 for empty input.
    """
    values, _ = _prepare_data(data)
    return len(values)


def min(data: Iterable) -> Real:
    """Return the smallest valid observation.

    Args:
        data: An iterable of real numbers.

    Returns:
        The smallest numerical observation.

    Raises:
        ValueError: If no valid observations remain.
    """
    values, _ = _prepare_data(data)

    if not values:
        raise ValueError("Cannot calculate minimum of empty data.")

    smallest = values[0]

    for value in values[1:]:
        if value < smallest:
            smallest = value

    return smallest


def max(data: Iterable) -> Real:
    """Return the largest valid observation.

    Args:
        data: An iterable of real numbers.

    Returns:
        The largest numerical observation.

    Raises:
        ValueError: If no valid observations remain.
    """
    values, _ = _prepare_data(data)

    if not values:
        raise ValueError("Cannot calculate maximum of empty data.")

    largest = values[0]

    for value in values[1:]:
        if value > largest:
            largest = value

    return largest


def range(data: Iterable) -> Real:
    """Return the difference between the largest and smallest values.

    Range = maximum - minimum.

    Args:
        data: An iterable of real numbers.

    Returns:
        The difference between the largest and smallest observations.

    Raises:
        ValueError: If no valid observations remain.
    """
    values, _ = _prepare_data(data)

    if not values:
        raise ValueError("Cannot calculate range of empty data.")

    smallest = values[0]
    largest = values[0]

    for value in values[1:]:
        if value < smallest:
            smallest = value

        if value > largest:
            largest = value

    return largest - smallest


def frequency_table(data: Iterable) -> dict[Real, int]:
    """Return a sorted frequency table of valid observations.

    Each unique observation becomes a dictionary key, and its
    frequency becomes the corresponding value.

    Args:
        data: An iterable of real numbers.

    Returns:
        A dictionary mapping each unique observation to its frequency,
        ordered by numerical value.

    Raises:
        ValueError: If no valid observations remain.
    """
    values, _ = _prepare_data(data)

    if not values:
        raise ValueError(
            "Cannot create frequency table from empty data."
        )

    frequencies = {}

    for value in values:
        if value in frequencies:
            frequencies[value] += 1
        else:
            frequencies[value] = 1

    return dict(sorted(frequencies.items()))
