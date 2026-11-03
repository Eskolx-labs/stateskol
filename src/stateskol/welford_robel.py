"""
Welford (1962): online corrected sums.

Implements the three recurrences discussed in the paper:
    Formula I   - corrected sum of squares (one variable)
    Formula II  - corrected sum of products (paired variables)
    Formula III - corrected sums of higher powers (one variable)

The required assignment interface is:
    welford(data)

No NumPy variance, standard-deviation, covariance, or moment
calculation is used in this module.
"""

import math
from numbers import Real


def _is_missing(value):
    """Return True for the two missing-value forms accepted here."""
    if value is None:
        return True
    if isinstance(value, Real) and not isinstance(value, bool):
        return math.isnan(float(value))
    return False


def _validate_observation(value, label="observation"):
    """Validate one non-missing observation and return it as a float."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{label} must be a real number; got {value!r}.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite; got {value!r}.")
    return value


class WelfordAccumulator:
    """
    Running univariate accumulator for Formula I and Formula III.

    moments[r] stores:
        S^(r) = sum((x_i - current_mean) ** r)

    moments[0] is the count, and moments[1] is zero.
    """

    def __init__(self, max_order=4):
        if isinstance(max_order, bool) or not isinstance(max_order, int):
            raise TypeError("max_order must be an integer.")
        if max_order < 2:
            raise ValueError("max_order must be at least 2.")

        self.max_order = max_order
        self.count = 0
        self.mean = 0.0
        self.moments = [0.0] * (max_order + 1)

    def update(self, value):
        """Add one observation using the online recurrences."""
        x = _validate_observation(value)
        old_n = self.count
        old_mean = self.mean
        old_moments = self.moments.copy()

        new_n = old_n + 1
        delta = x - old_mean
        new_mean = old_mean + delta / new_n
        delta_after_update = x - new_mean

        new_moments = [0.0] * (self.max_order + 1)
        new_moments[0] = new_n
        new_moments[1] = 0.0

        # Formula I: corrected sum of squares.
        # This is also Formula III's special case when r = 2.
        new_moments[2] = (
            old_moments[2] + delta * delta_after_update
        )

        # Formula III: corrected sums for powers r >= 3.
        # All terms use old_moments, not partly updated moments.
        for r in range(3, self.max_order + 1):
            previous_contribution = 0.0

            for j in range(r + 1):
                previous_contribution += (
                    math.comb(r, j)
                    * (1.0 / new_n) ** (r - j)
                    * (old_mean - x) ** (r - j)
                    * old_moments[j]
                )

            new_observation_contribution = (
                ((new_n - 1.0) / new_n) ** r
                * (x - old_mean) ** r
            )

            new_moments[r] = (
                previous_contribution + new_observation_contribution
            )

        self.count = new_n
        self.mean = new_mean
        self.moments = new_moments
        return self

    def result(self):
        """Return count, mean, M2, sample variance, and sample SD."""
        n = self.count
        m2 = self.moments[2]
        variance = m2 / (n - 1) if n >= 2 else None
        standard_deviation = (
            math.sqrt(max(0.0, variance)) if variance is not None else None
        )

        return {
            "count": n,
            "mean": self.mean if n else None,
            "M2": m2,
            "sample_variance": variance,
            "sample_std": standard_deviation,
            "dropped_count": 0,
        }

    def higher_order_sums(self):
        """Return the corrected sums M3, M4, ... up to max_order."""
        return {
            f"M{r}": self.moments[r]
            for r in range(3, self.max_order + 1)
        }


def welford(data):
    """
    Required assignment function: online sample variance.

    Contract:
    - data must be an iterable of real numbers.
    - None and NaN are dropped and counted.
    - strings, booleans, and other non-real values raise TypeError.
    - positive and negative infinity raise ValueError.
    - empty data returns None for mean, variance, and standard deviation.
    - fewer than two valid values returns None for sample variance and SD.

    Returns a dictionary with count, mean, sample_variance,
    sample_std, and dropped_count.
    """
    try:
        iterator = iter(data)
    except TypeError as exc:
        raise TypeError("data must be an iterable of real numbers.") from exc

    accumulator = WelfordAccumulator(max_order=2)
    dropped_count = 0

    for value in iterator:
        if _is_missing(value):
            dropped_count += 1
            continue
        accumulator.update(value)

    result = accumulator.result()
    result["dropped_count"] = dropped_count
    return result


def welford_moments(data, max_order=4):
    """
    Apply Formula III to calculate corrected sums of powers.

    Formula I is included as M2. Formula III adds M3, M4, ...
    Missing values None and NaN are dropped and counted.
    """
    try:
        iterator = iter(data)
    except TypeError as exc:
        raise TypeError("data must be an iterable of real numbers.") from exc

    accumulator = WelfordAccumulator(max_order=max_order)
    dropped_count = 0

    for value in iterator:
        if _is_missing(value):
            dropped_count += 1
            continue
        accumulator.update(value)

    result = accumulator.result()
    result["dropped_count"] = dropped_count
    result["higher_order_sums"] = accumulator.higher_order_sums()
    return result


def welford_products(x_data, y_data):
    """
    Apply Formula II to paired observations.

    Returns the corrected sum of products C2 and sample covariance.
    Pairwise deletion is used: if either member of a pair is None or
    NaN, that whole pair is dropped and counted.

    Both inputs must be iterables of equal length.
    """
    try:
        xs = list(x_data)
        ys = list(y_data)
    except TypeError as exc:
        raise TypeError("x_data and y_data must be iterable.") from exc

    if len(xs) != len(ys):
        raise ValueError("x_data and y_data must have equal lengths.")

    n = 0
    mean_x = 0.0
    mean_y = 0.0
    c2 = 0.0
    dropped_pairs = 0

    for x_raw, y_raw in zip(xs, ys):
        missing_x = _is_missing(x_raw)
        missing_y = _is_missing(y_raw)

        if missing_x or missing_y:
            dropped_pairs += 1
            continue

        x = _validate_observation(x_raw, "x observation")
        y = _validate_observation(y_raw, "y observation")

        old_mean_x = mean_x
        old_mean_y = mean_y
        n += 1

        dx = x - old_mean_x
        dy = y - old_mean_y

        mean_x = old_mean_x + dx / n
        mean_y = old_mean_y + dy / n

        # Formula II: corrected sum of products.
        c2 += dx * (y - mean_y)

    covariance = c2 / (n - 1) if n >= 2 else None

    return {
        "paired_count": n,
        "paired_mean_x": mean_x if n else None,
        "mean_y": mean_y if n else None,
        "C2": c2,
        "sample_covariance": covariance,
        "dropped_pairs": dropped_pairs,
    }
