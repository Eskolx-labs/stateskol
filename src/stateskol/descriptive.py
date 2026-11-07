from math import fsum


def mean(data):
    """Calculate the arithmetic mean of numeric observations."""
    return fsum(data) / len(data)


def median(data):
    """Calculate the median of numeric observations."""
    sorted_data = sorted(data)
    n = len(sorted_data)

    middle = n // 2

    if n % 2 == 1:
        return sorted_data[middle]

    return (sorted_data[middle - 1] + sorted_data[middle]) / 2


def mode(data):
    """Return all values with the highest frequency, in ascending order."""
    frequencies = {}

    for value in data:
        frequencies[value] = frequencies.get(value, 0) + 1

    highest_frequency = max(frequencies.values())

    return sorted(
        value
        for value, frequency in frequencies.items()
        if frequency == highest_frequency
    )