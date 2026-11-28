"""Online mean and variance using Welford's numerically stable algorithm.

The accumulator accepts finite Python integers and floats. Boolean values
are rejected even though bool is a subclass of int. Missing values are
not skipped: None and other non-numeric inputs raise TypeError.

Population variance uses ddof=0; sample variance uses ddof=1.
At least one observation is required for population variance and at least
two for sample variance.

Raises:
    TypeError: For non-numeric observations, booleans, or non-integer ddof.
    ValueError: For non-finite observations, unsupported ddof, or too few
        observations to calculate the requested variance.

Example:
    >>> acc = WelfordAccumulator()
    >>> for value in [2, 4, 6]:
    ...     acc.update(value)
    >>> acc.mean
    4.0
    >>> acc.variance()
    2.6666666666666665
    >>> acc.variance(ddof=1)
    4.0
"""

from math import isfinite, sqrt


class WelfordAccumulator:
    """Maintain the count, running mean, and corrected sum of squares.

    Attributes:
        count: Number of observations accepted.
        mean: Running arithmetic mean, or None when empty.
    """

    def __init__(self):
        """Create an empty accumulator."""
        self.count = 0
        self.mean = None
        self._m2 = 0.0

    def update(self, value):
        """Add one finite integer or float observation.

        Args:
            value: A finite Python int or float. bool is not accepted.

        Returns:
            None. The accumulator is updated in place.

        Raises:
            TypeError: If value is not an int or float, or is a bool.
            ValueError: If value is NaN or positive/negative infinity.
        """
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("value must be an integer or float, not bool")

        if not isfinite(value):
            raise ValueError("value must be finite")

        self.count += 1

        if self.count == 1:
            self.mean = float(value)
            return

        delta = value - self.mean
        self.mean += delta / self.count
        delta_after_update = value - self.mean
        self._m2 += delta * delta_after_update

    def variance(self, ddof=0):
        """Return the accumulated variance.

        Args:
            ddof: Delta degrees of freedom: 0 for population variance
                (divide by n), or 1 for sample variance (divide by n - 1).

        Returns:
            The requested variance as a float.

        Raises:
            TypeError: If ddof is not an integer or is a bool.
            ValueError: If ddof is not 0 or 1, or there are too few
                observations for the requested variance.
        """
        if isinstance(ddof, bool) or not isinstance(ddof, int):
            raise TypeError("ddof must be an integer")

        if ddof not in (0, 1):
            raise ValueError("ddof must be 0 or 1")

        if self.count <= ddof:
            raise ValueError("not enough observations to calculate variance")

        return self._m2 / (self.count - ddof)

    def standard_deviation(self, ddof=0):
        """Return the square root of variance using the selected ddof.

        Args:
            ddof: 0 for population or 1 for sample standard deviation.

        Returns:
            The standard deviation as a float.

        Raises:
            TypeError: If ddof is not an integer or is a bool.
            ValueError: If ddof is unsupported or too few observations exist.
        """
        return sqrt(self.variance(ddof))
