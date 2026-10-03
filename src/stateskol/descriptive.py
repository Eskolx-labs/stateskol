import math
from collections.abc import Iterable
from numbers import Real


def welford(data: Iterable[Real]) -> dict:
    """
    Calculate count, mean, sample variance, and sample standard deviation
    using Welford's online algorithm.

    Parameters
    ----------
    data : Iterable[Real]
        An iterable containing numeric values.

        - None and NaN are treated as missing values.
        - Missing values are dropped and counted in ``missing_count``.
        - Valid values must be finite real numbers.
        - Boolean values are not accepted as numeric observations.

    Returns
    -------
    dict
        A dictionary containing:

        - ``count``: number of valid observations.
        - ``mean``: arithmetic mean of valid observations.
        - ``variance``: sample variance using ddof=1, or None when
          fewer than two valid observations are available.
        - ``std_dev``: sample standard deviation, or None when fewer
          than two valid observations are available.
        - ``missing_count``: number of missing values that were dropped.

    Parameterization
    ----------------
    The function calculates sample variance using:

        variance = M2 / (count - 1)

    This corresponds to ddof=1.

    Assumptions
    -----------
    Valid observations are finite real numbers.

    Missing-value rule:
        None and NaN are treated as missing, dropped, and counted.

    Invalid-value rule:
        Non-numeric values, boolean values, and infinite values are
        rejected with ValueError.

    Errors
    ------
    ValueError
        Raised when:

        - data is not iterable.
        - data contains a non-numeric value.
        - data contains a boolean value.
        - data contains an infinite value.
        - no valid observations remain after removing missing values.

    Notes
    -----
    Welford's algorithm updates the mean and the accumulated squared
    deviation M2 incrementally. It avoids calculating the variance by
    subtracting large, potentially close quantities such as E(X^2)
    and E(X)^2, which helps numerical stability.

    Examples
    --------
    >>> welford([2, 4, 6])
    {'count': 3, 'mean': 4.0, 'variance': 4.0, 'std_dev': 2.0, 'missing_count': 0}

    >>> welford([2, 4, None, 6])
    {'count': 3, 'mean': 4.0, 'variance': 4.0, 'std_dev': 2.0, 'missing_count': 1}

    >>> welford([5])
    {'count': 1, 'mean': 5.0, 'variance': None, 'std_dev': None, 'missing_count': 0}
    """

    try:
        iterator = iter(data)
    except TypeError as exc:
        raise ValueError(
            "data must be an iterable of numeric values"
        ) from exc

    count = 0
    mean = 0.0
    m2 = 0.0
    missing_count = 0

    for value in iterator:
        # Missing values are dropped and counted.
        if value is None:
            missing_count += 1
            continue

        if isinstance(value, float) and math.isnan(value):
            missing_count += 1
            continue

        # Reject non-numeric values.
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"invalid value: {value!r}")

        # Infinite values are not valid observations.
        if not math.isfinite(value):
            raise ValueError(f"invalid non-finite value: {value!r}")

        count += 1

        # Welford's online update.
        delta = value - mean
        mean += delta / count
        delta2 = value - mean
        m2 += delta * delta2

    # At least one valid observation is required.
    if count == 0:
        raise ValueError("data contains no valid observations")

    # Sample variance is undefined for a single observation.
    if count == 1:
        variance = None
        std_dev = None
    else:
        variance = m2 / (count - 1)
        std_dev = math.sqrt(variance)

    return {
        "count": count,
        "mean": mean,
        "variance": variance,
        "std_dev": std_dev,
        "missing_count": missing_count,
    }