
from math import fsum


def mean(data):
    """
    Calculate the arithmetic mean of numeric observations.

    Parameters
    ----------
    data : iterable of numbers
        A non-empty collection of numeric observations.

    Returns
    -------
    float
        The arithmetic mean of the observations.

    Notes
    -----
    Uses math.fsum() for improved floating-point summation accuracy.

    Assumes all observations are valid numeric values.
    Missing-value handling and input validation remain subject
    to the shared Stateskol input contract.

    Raises
    ------
    ZeroDivisionError
        If the dataset is empty.

    Examples
    --------
    >>> mean([2, 4, 6, 8])
    5.0
    """
    return fsum(data) / len(data)


def median(data):
    """
    Calculate the median of numeric observations.

    Parameters
    ----------
    data : iterable of numbers
        A non-empty collection of numeric observations.

    Returns
    -------
    number or float
        The middle observation for odd-sized datasets,
        or the average of the two middle observations
        for even-sized datasets.

    Notes
    -----
    The observations are sorted before the median is calculated.
    The original input collection is not modified.

    Assumes all observations are valid numeric values.
    Missing-value handling and input validation remain subject
    to the shared Stateskol input contract.

    Raises
    ------
    IndexError
        If the dataset is empty.

    Examples
    --------
    >>> median([1, 3, 5])
    3
    >>> median([1, 3, 5, 7])
    4.0
    """
    sorted_data = sorted(data)
    n = len(sorted_data)

    middle = n // 2

    if n % 2 == 1:
        return sorted_data[middle]

    return (sorted_data[middle - 1] + sorted_data[middle]) / 2


def mode(data):
    """
    Return all observations with the highest frequency.

    Parameters
    ----------
    data : iterable of hashable numeric values
        A non-empty collection of numeric observations.

    Returns
    -------
    list
        All observations having the highest frequency,
        sorted in ascending order.

    Notes
    -----
    Multiple modes are returned when observations share
    the highest frequency.

    If every observation occurs once, every distinct
    observation is returned as a mode under this implementation.

    Assumes observations are hashable and mutually sortable.
    Missing-value handling and input validation remain subject
    to the shared Stateskol input contract.

    Raises
    ------
    ValueError
        If the dataset is empty.

    Examples
    --------
    >>> mode([1, 2, 2, 3, 3, 4])
    [2, 3]
    """
    frequencies = {}

    for value in data:
        frequencies[value] = frequencies.get(value, 0) + 1

    highest_frequency = max(frequencies.values())

    return sorted(
        value
        for value, frequency in frequencies.items()
        if frequency == highest_frequency
    )
