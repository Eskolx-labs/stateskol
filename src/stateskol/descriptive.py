
import math
from bisect import bisect_right


# --- BEGIN HISTOGRAM BLOCK (owner: Yoseph) ---
def _clean_numbers(data):
    """Return (list of floats, number dropped). Same input rule as the rest
    of the package: None and NaN are dropped and counted, bad values stop
    with an error."""
    values = []
    dropped = 0
    for x in data:
        if x is None:
            dropped = dropped + 1
            continue
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("histogram_counts: this is not a number: " + repr(x))
        if math.isnan(x):
            dropped = dropped + 1
            continue
        if math.isinf(x):
            raise ValueError("histogram_counts: infinity is not allowed")
        values.append(float(x))
    if len(values) == 0:
        raise ValueError("histogram_counts: no usable numbers")
    return values, dropped


def _quantile(sorted_values, p):
    """Quantile p (0 to 1) of an already sorted list, by straight-line
    interpolation between neighbours. This is the numpy default method."""
    position = (len(sorted_values) - 1) * p
    low = int(math.floor(position))
    high = int(math.ceil(position))
    fraction = position - low
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * fraction


def _fd_edges(values):
    """The default bin rule (Freedman-Diaconis, 1981). See histogram_counts."""
    n = len(values)
    low = min(values)
    high = max(values)

    # all values equal: no spread, so make one bin of width 1 around the value
    if low == high:
        return [low - 0.5, low + 0.5]

    ordered = sorted(values)
    iqr = _quantile(ordered, 0.75) - _quantile(ordered, 0.25)
    width = 2 * iqr * n ** (-1 / 3)

    # more than half the values are equal: the rule gives width 0,
    # so we use one bin over the whole range
    if width == 0:
        return [low, high]

    bins = math.ceil((high - low) / width)
    step = (high - low) / bins
    edges = []
    for i in range(bins + 1):
        edges.append(low + i * step)
    edges[-1] = high  # the last edge is exactly the maximum
    return edges


def histogram_counts(data, edges=None):
    """Count how many values fall into each bin (class interval).

    Inputs
    ------
    data  : a list (or tuple, or anything we can loop over) of numbers.
            Integers and floats are fine.
    edges : optional. A list of bin boundaries, smallest first, at least 2.
            If you give edges, they are used exactly as given. If you leave
            it out, the default bin rule below chooses the edges.

    Outputs
    -------
    A dictionary with 3 keys:
        "counts"  : list of ints, one per bin (len(edges) - 1 of them)
        "edges"   : list of floats, the bin boundaries that were used
        "dropped" : how many missing values (None or NaN) we threw away

    Parameterization
    ----------------
    Only `edges`. That is how you use a different rule: work out your own
    edges (for example every 100 starting at 500, as in Ross Table 2.4)
    and pass them in.

    The bin rule (when edges is not given)
    --------------------------------------
    Freedman and Diaconis (1981):
        width  h = 2 * IQR * n ** (-1/3)       IQR = Q3 - Q1, n = values used
        origin   = the smallest value
        bins   k = ceil((max - min) / h)
        The k bins are equal and cover exactly min to max, so the real
        width is (max - min) / k, which is a little less than or equal to h.
    Quantile method for Q1 and Q3: "linear" (straight-line interpolation
    between neighbouring sorted values, position (n - 1) * p, Hyndman-Fan
    type 7). This is the numpy default, method="linear".
    Two special cases, so the rule never divides by zero:
        - all values equal       -> one bin [value - 0.5, value + 0.5]
        - IQR is 0 (more than half the values are equal) but the values
          are not all equal      -> one bin [min, max]. For more detail
          in that case, pass your own edges.

    The edge rule (always, also for edges you give)
    -----------------------------------------------
    A bin holds its left end but not its right end: [left, right). This is
    the "left-end inclusion" convention of Ross, section 2.2.3. The LAST
    bin also holds its right end: [left, right]. That is why the largest
    value is never lost.

    Support
    -------
    - data  : finite real numbers (int or float), any sign, any size, at
              least one usable value.
    - edges : finite real numbers, strictly increasing, at least 2.
    - result: every count is an int >= 0, and sum(counts) + dropped
              equals the number of values given.

    Assumptions
    -----------
    - The numbers are real and finite.
    - Bins are meant to be compared, so they are in order and do not overlap.

    Missing values
    --------------
    None and NaN are dropped and counted in "dropped". Nothing is filled in.

    Errors (we stop early, we do not guess)
    ---------------------------------------
    - TypeError  : a value (in data or in edges) is not a number. True and
                   False are also rejected.
    - ValueError : a value is infinity.
    - ValueError : there are no usable numbers (empty, or all missing).
    - ValueError : edges has fewer than 2 numbers, contains NaN, or is not
                   strictly increasing.
    - ValueError : edges are given and a value is outside the first and last
                   edge. We never drop a value silently.

    Special cases
    -------------
    - one value       -> one bin [value - 0.5, value + 0.5] holding it
    - constant values -> same one bin holding all of them

    Examples
    --------
    >>> r = histogram_counts([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], edges=[0, 2, 4, 6])
    >>> r["counts"]
    [1, 5, 4]
    >>> r = histogram_counts(list(range(1, 17)))
    >>> r["edges"], r["counts"]
    ([1.0, 6.0, 11.0, 16.0], [5, 5, 6])
    >>> histogram_counts([1, None, 2, float("nan"), 3], edges=[0, 2, 4])["dropped"]
    2
    """
    values, dropped = _clean_numbers(data)

    if edges is None:
        used_edges = _fd_edges(values)
    else:
        used_edges = []
        for e in edges:
            if isinstance(e, bool) or not isinstance(e, (int, float)):
                raise TypeError("histogram_counts: an edge is not a number: " + repr(e))
            if math.isnan(e) or math.isinf(e):
                raise ValueError("histogram_counts: an edge must be a finite number")
            used_edges.append(float(e))
        if len(used_edges) < 2:
            raise ValueError("histogram_counts: edges needs at least 2 numbers")
        for i in range(len(used_edges) - 1):
            if used_edges[i] >= used_edges[i + 1]:
                raise ValueError("histogram_counts: edges must be strictly increasing")
        if min(values) < used_edges[0] or max(values) > used_edges[-1]:
            raise ValueError("histogram_counts: some values are outside the edges")

    counts = [0] * (len(used_edges) - 1)
    for x in values:
        # bisect_right finds where x would be inserted among the edges:
        # that is the bin whose left end is <= x and whose right end is > x
        i = bisect_right(used_edges, x) - 1
        if i == len(counts):
            i = i - 1  # x equals the last edge: the last bin includes it
        counts[i] = counts[i] + 1

    return {"counts": counts, "edges": used_edges, "dropped": dropped}
# --- END HISTOGRAM BLOCK ---
