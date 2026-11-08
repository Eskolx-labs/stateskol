import math


def _validate(data):
    values = list(data)
    if not values:
        raise ValueError("data is empty")
    for v in values:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TypeError("invalid value: " + repr(v))
        if math.isnan(v) or math.isinf(v):
            raise ValueError("invalid value: " + repr(v))
    return values


def mean(data):
    """Return the average of the numbers.

    Input: a list of numbers.
    Output: the sum divided by how many there are.
    Errors: ValueError if the list is empty or has nan/inf.
            TypeError if an item is not a number.
    Example:
        >>> mean([2, 4, 6])
        4.0
    """
    values = _validate(data)
    return sum(values) / len(values)
def variance(data):
    """Sample variance (divides by n - 1), two-pass method.

    Input: an iterable of numbers, at least 2 values.
    Output: a float >= 0 (0 for constant data).
    Errors: as _validate; ValueError if fewer than 2 values.
    Example:
        >>> variance([2, 4, 6])
        4.0
    """
    values = _validate(data)
    if len(values) < 2:
        raise ValueError("sample variance needs at least 2 values")
    m = mean(values)
    squared = [(v - m) ** 2 for v in values]
    return sum(squared) / (len(values) - 1)


def median(data):
    """Middle value of the sorted data.

    Input: an iterable of numbers.
    Output: the middle value; for an even count, the average of the
            two middle values.
    Errors: as _validate.
    Example:
        >>> median([4, 1, 3, 2])
        2.5
    """
    values = sorted(_validate(data))
    n = len(values)
    mid = n // 2
    if n % 2 == 1:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2


def mode(data):
    """All most-frequent values, in sorted order.

    Input: an iterable of numbers.
    Output: a sorted list; more than one item if there is a tie.
    Errors: as _validate.
    Example:
        >>> mode([1, 1, 2, 2, 3])
        [1, 2]
    """
    values = _validate(data)
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.values())
    return sorted(v for v, c in counts.items() if c == top)

# Quantile: linear interpolation (Type 7, the NumPy default).
# position = q * (n - 1) on sorted data; q must be in [0, 1].
def quantile(data, q):
    """Quantile by linear interpolation (Type 7, the NumPy default).

    Method: sort the data, position = q * (n - 1), then interpolate
            between the two neighbouring values.
    Input: data (numbers), q between 0 and 1.
    Output: a number.
    Errors: as _validate; ValueError if q is outside [0, 1].
    Example:
        >>> quantile([1, 2, 3, 4], 0.25)
        1.75
    """
    values = sorted(_validate(data))
    n = len(values)
    if not 0 <= q <= 1:
        raise ValueError("q must be between 0 and 1")
    pos = q * (n - 1)
    lo = int(pos)
    frac = pos - lo
    if frac == 0:
        return values[lo]
    return values[lo] + frac * (values[lo + 1] - values[lo])


def iqr(data):
    """Interquartile range: quantile 0.75 minus quantile 0.25.

    Input: an iterable of numbers.
    Output: a number >= 0. Uses the quantile method above.
    Errors: as quantile.
    Example:
        >>> iqr([1, 2, 3, 4])
        1.5
    """
    return quantile(data, 0.75) - quantile(data, 0.25)


def drop_missing(data):
    """Remove None and nan, and report how many were removed.

    Input: an iterable that may contain None or nan.
    Output: (kept_list, dropped_count). Nothing is filled in silently.
    Example:
        >>> drop_missing([1, None, 3, float("nan")])
        ([1, 3], 2)
    """
    values = list(data)
    kept = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    return kept, len(values) - len(kept)


def variance_welford(data):
    """Sample variance by Welford's one-pass method (numerically stable).

    Input: an iterable of numbers, at least 2 values.
    Output: a float; equals variance() but streams one value at a time.
    Errors: as variance.
    Example:
        >>> variance_welford([2, 4, 6])
        4.0
    """
    values = _validate(data)
    if len(values) < 2:
        raise ValueError("sample variance needs at least 2 values")
    n = 0
    mean_ = 0.0
    m2 = 0.0
    for x in values:
        n += 1
        delta = x - mean_
        mean_ += delta / n
        m2 += delta * (x - mean_)
    return m2 / (n - 1)


def std(data):
    """Sample standard deviation: square root of the sample variance.

    Input: an iterable of numbers, at least 2 values.
    Output: a float >= 0, in the same units as the data.
    Errors: as variance.
    Example:
        >>> std([2, 4, 6])
        2.0
    """
    return math.sqrt(variance(data))


def frequency_table(data):
    """Each distinct value with its count and relative frequency.

    Input: an iterable of numbers.
    Output: a list of (value, count, relative) sorted by value.
    Errors: as _validate.
    Example:
        >>> frequency_table([1, 2, 2, 2])
        [(1, 1, 0.25), (2, 3, 0.75)]
    """
    values = _validate(data)
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    n = len(values)
    return [(v, counts[v], counts[v] / n) for v in sorted(counts)]



def count(data):
    """Number of values.

    Input: an iterable of numbers.
    Output: int.
    Errors: as _validate (empty, invalid values).
    Example:
        >>> count([3, 1, 2])
        3
    """
    return len(_validate(data))


def minimum(data):
    """Smallest value.

    Input: an iterable of numbers.
    Output: the minimum value.
    Errors: as _validate.
    Example:
        >>> minimum([3, 1, 2])
        1
    """
    return min(_validate(data))


def maximum(data):
    """Largest value.

    Input: an iterable of numbers.
    Output: the maximum value.
    Errors: as _validate.
    Example:
        >>> maximum([3, 1, 2])
        3
    """
    return max(_validate(data))


def data_range(data):
    """Range: maximum minus minimum.

    Input: an iterable of numbers.
    Output: a number >= 0 (0 for one value or constant data).
    Errors: as _validate.
    Example:
        >>> data_range([3, 1, 2])
        2
    """
    values = _validate(data)
    return max(values) - min(values)

def frequency_table(data):
    """Each distinct value with its count and relative frequency.

    Input: an iterable of numbers.
    Output: a list of (value, count, relative) sorted by value.
    Errors: as _validate.
    Example:
        >>> frequency_table([1, 2, 2, 2])
        [(1, 1, 0.25), (2, 3, 0.75)]
    """
    values = _validate(data)
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    n = len(values)
    return [(v, counts[v], counts[v] / n) for v in sorted(counts)]

# Default bins: Freedman-Diaconis width = 2 * IQR * n(-1/3), origin at the minimum.
def _default_edges(values):
    lo = min(values)
    hi = max(values)
    if lo == hi:
        return [lo, lo + 1]
    width = 2 * iqr(values) * len(values) ** (-1 / 3)
    if width == 0:
        return [lo, hi]
    k = math.ceil((hi - lo) / width)
    edges = [lo + i * width for i in range(k + 1)]
    edges[-1] = max(edges[-1], hi)
    return edges


# Bins are [a, b) except the last, which is [a, b]. Returns (edges, counts).
def histogram_counts(data, edges=None):
    """Count values per bin.

    Bin rule: bins are [a, b) except the last, which is [a, b], so the
    maximum is never lost. Default edges use Freedman-Diaconis width,
    origin at the minimum; pass edges to use any other rule.
    Input: data (numbers), optional strictly increasing edges.
    Output: (edges, counts).
    Errors: as _validate; ValueError for fewer than 2 edges, edges not
            strictly increasing, or a value outside the edges.
    Example:
        >>> histogram_counts([1, 2, 2, 3, 4, 5], [0, 2, 4, 6])
        ([0, 2, 4, 6], [1, 3, 2])
    """
    values = _validate(data)
    if edges is None:
        edges = _default_edges(values)
    edges = list(edges)
    if len(edges) < 2:
        raise ValueError("need at least 2 edges")
    for i in range(len(edges) - 1):
        if edges[i] >= edges[i + 1]:
            raise ValueError("edges must be strictly increasing")
    nbins = len(edges) - 1
    counts = [0] * nbins
    for v in values:
        if v < edges[0] or v > edges[-1]:
            raise ValueError("value outside edges: " + repr(v))
        for i in range(nbins):
            last = (i == nbins - 1)
            if edges[i] <= v < edges[i + 1] or (last and v == edges[i + 1]):
                counts[i] += 1
                break
    return edges, counts