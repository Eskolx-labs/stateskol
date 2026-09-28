"""Numeric input validation, Ross-convention quantiles, and interquartile range."""

import math
from fractions import Fraction
from typing import NamedTuple


class PreparedData(NamedTuple):
    """Validated observations and the number of missing observations removed."""

    values: tuple[int | float, ...]
    dropped_count: int


def prepare_data(data: object, *, min_count: int = 1) -> PreparedData:
    """Validate observations and remove missing values without filling them.

    Args:
        data: A one-dimensional built-in list or tuple of built-in integers,
            finite floats, None, or floating-point NaN. Booleans, numeric
            subclasses, strings, complex numbers, and nested data are rejected.
        min_count: Positive built-in integer specifying the minimum number of
            retained observations. Use 2 for sample variance and standard
            deviation; the default is 1.

    Returns:
        PreparedData containing an immutable tuple of retained values and a
        dropped_count for removed None and NaN observations. Order, duplicates,
        and numeric types are preserved; the input collection is not modified.

    Numeric support:
        Integers are retained exactly, without conversion or a magnitude limit.
        Floats must be finite. Validation performs no statistical arithmetic;
        consuming functions must check their own conversion and overflow limits.
        Data is unweighted; missing-value removal does not imply an unbiased
        sample. Statistics describe only the retained observations.

    Raises:
        TypeError: Unsupported collection, observation, or min_count type.
        ValueError: Infinite observation, nonpositive min_count, or fewer than
            min_count observations remaining after missing-value removal.
        Observation errors identify the original zero-based index. No partial
        result is returned when validation fails.

    Examples:
        >>> prepare_data([2, None, 4, float("nan")])
        PreparedData(values=(2, 4), dropped_count=2)
        >>> prepare_data((0, -3, 4.5), min_count=2)
        PreparedData(values=(0, -3, 4.5), dropped_count=0)
    """
    if type(data) not in (list, tuple):
        raise TypeError("Expected a built-in list or tuple of observations.")
    if type(min_count) is not int:
        raise TypeError("min_count must be a positive built-in integer.")
    if min_count < 1:
        raise ValueError("min_count must be at least 1.")

    values: list[int | float] = []
    dropped_count = 0
    for index, observation in enumerate(data):
        if observation is None:
            dropped_count += 1
            continue
        if type(observation) not in (int, float):
            raise TypeError(
                f"Invalid observation at index {index}: expected a built-in "
                f"integer, float, or None; got {type(observation).__name__}."
            )
        if type(observation) is float:
            if math.isnan(observation):
                dropped_count += 1
                continue
            if not math.isfinite(observation):
                raise ValueError(
                    f"Invalid observation at index {index}: infinity is not supported."
                )
        values.append(observation)

    if len(values) < min_count:
        raise ValueError(
            f"At least {min_count} retained observations required; "
            f"got {len(values)} after dropping {dropped_count}."
        )
    return PreparedData(tuple(values), dropped_count)


class StatisticResult(NamedTuple):
    """A computed statistic and the number of missing observations removed."""

    value: int | float
    dropped_count: int


def _quantile_sorted(values: list[int | float], probability: int | float) -> Fraction:
    """Compute an exact quantile from nonempty, sorted, validated observations."""
    position = len(values) * probability
    if position <= 0:
        return Fraction(values[0])
    if position >= len(values):
        return Fraction(values[-1])
    lower_index = math.floor(position)
    if position == lower_index:
        return (Fraction(values[lower_index - 1]) + Fraction(values[lower_index])) / 2
    return Fraction(values[lower_index])


def _statistic_result(value: Fraction, dropped_count: int) -> StatisticResult:
    """Return an exact integer or a rounded float with the missing-value count."""
    if value.denominator == 1:
        return StatisticResult(value.numerator, dropped_count)
    try:
        return StatisticResult(float(value), dropped_count)
    except OverflowError as error:
        raise OverflowError("Noninteger result exceeds the finite float range.") from error


def quantile(data: object, probability: object) -> StatisticResult:
    """Return a quantile using Ross's averaged-inverted-CDF percentile rule.

    Args:
        data: Built-in list or tuple accepted by prepare_data. None and float
            NaN observations are removed; at least one observation must remain.
        probability: Built-in integer or finite float in [0, 1], excluding
            booleans. Probabilities are fractions, not percentages.

    Returns:
        StatisticResult(value, dropped_count). For sorted data of size n and
        0 < probability < 1, average one-based positions n*p and n*p+1 when
        n*p is integral; otherwise select position ceil(n*p). At 0 return the
        minimum; at 1 return the maximum. This matches the convention named
        method="averaged_inverted_cdf" by NumPy, not its default linear method.

    Support and assumptions:
        Data is unweighted and describes retained observations only. The input
        is not modified. Ranking uses ordinary Python multiplication n*p with
        no tolerance near integer positions. Midpoints use exact rational
        arithmetic on the supplied numeric values. Integral results are exact
        Python integers; nonintegral results are floats, with normal rounding
        and possible underflow. Numeric types need not match the input types.

    Raises:
        TypeError: Unsupported data or probability type.
        ValueError: Empty retained data, infinite observation, or probability
            outside [0, 1], including NaN and infinity.
        OverflowError: A nonintegral result cannot be represented as a finite
            float. No fixed magnitude limit is imposed on integral results.

    Reference:
        Ross, 6th ed., sec. 2.3.3, printed pp. 26-27 (PDF pp. 41-42).
        Missing-data, endpoint, and exception policies follow the project contract.

    Examples:
        >>> quantile([8, None, 2, 6, 4], 0.25)
        StatisticResult(value=3, dropped_count=1)
        >>> quantile([2, 4, 6, 8], 0.6)
        StatisticResult(value=6, dropped_count=0)
        >>> quantile([1, 2], 0.5)
        StatisticResult(value=1.5, dropped_count=0)
    """
    prepared = prepare_data(data)
    if type(probability) not in (int, float):
        raise TypeError("probability must be a built-in integer or float, not a boolean.")
    if not 0 <= probability <= 1:
        raise ValueError("probability must be finite and between 0 and 1 inclusive.")
    value = _quantile_sorted(sorted(prepared.values), probability)
    return _statistic_result(value, prepared.dropped_count)


def iqr(data: object) -> StatisticResult:
    """Return the interquartile range using Ross's percentile rule.

    Args:
        data: Built-in list or tuple accepted by prepare_data. None and float
            NaN observations are removed; at least one observation must remain.

    Returns:
        StatisticResult(value, dropped_count), with value equal to Q(0.75)
        minus Q(0.25), using the same averaged-inverted-CDF rule as quantile.
        Missing observations are counted once, not once per quartile. Single
        values and constant data return zero IQR.

    Support and assumptions:
        Data is unweighted and describes retained observations only. Cleaning
        and sorting occur once without modifying the input. Quartiles and their
        difference use exact rational arithmetic internally; integral results
        are exact integers and nonintegral results are floats with normal
        rounding and possible underflow. Units match the observations.

    Raises:
        TypeError: Unsupported collection or observation type.
        ValueError: Empty retained data or infinite observation.
        OverflowError: A nonintegral result exceeds the finite float range.
            Integral results have no fixed magnitude limit.

    Reference:
        Ross, 6th ed., sec. 2.3.3, printed p. 29 (PDF p. 44), defines IQR.
        Percentile selection is on printed pp. 26-27 (PDF pp. 41-42).
        Missing-data and exception policies follow the project contract.

    Examples:
        >>> iqr([2, None, 4, 6, 8, float("nan")])
        StatisticResult(value=4, dropped_count=2)
        >>> iqr([5])
        StatisticResult(value=0, dropped_count=0)
    """
    prepared = prepare_data(data)
    values = sorted(prepared.values)
    spread = _quantile_sorted(values, 0.75) - _quantile_sorted(values, 0.25)
    return _statistic_result(spread, prepared.dropped_count)