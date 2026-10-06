"""Welford's online variance.

Source: B. P. Welford (1962), "Note on a Method for Calculating Corrected
Sums of Squares and Products", Technometrics 4(3), 419-420.

Author: Yeabsira Tesfaye
"""

import math


# --- BEGIN WELFORD BLOCK (Yeabsira Tesfaye) ---
def welford(data):
    """Find count, mean, sample variance and standard deviation of data.

    The data is read ONE value at a time, only once (this is the "online"
    idea). We never keep the list and never subtract two huge numbers.

    Inputs
    ------
    data : a list (or tuple, or anything we can loop over) of numbers.
           Integers and floats are fine.

    Outputs
    -------
    A dictionary with 5 keys:
        "count"    : how many numbers we really used
        "mean"     : the average
        "variance" : sample variance (divide by n - 1)
        "std"      : standard deviation = square root of the variance
        "dropped"  : how many missing values we threw away

    Parameterization
    ----------------
    None. The divisor is always n - 1 (sample variance, like numpy ddof=1).

    How it works (Welford 1962)
    ---------------------------
    These are the formulas written in the paper. For each new number x,
    where n counts x too, m is the mean and S the corrected sum of squares:
        S_n = S_(n-1) + ((n - 1) / n) * (x_n - m_(n-1))**2     Formula I
        m_n = ((n - 1) / n) * m_(n-1) + x_n / n                equation (1)
    Formula I needs the OLD mean m_(n-1), so S is updated BEFORE the mean.
    S is the "corrected sum of squares" (sum of (x - mean)**2).
    At the end: variance = S / (n - 1).

    Assumptions
    -----------
    - The numbers are a sample, not the whole population.
    - The numbers are real and finite.

    Missing values
    --------------
    None and NaN are missing. We DROP them and report how many in "dropped".
    We never fill them in.

    Errors (we stop early, we do not guess)
    ---------------------------------------
    - TypeError  if a value is not a number (for example a string).
                 True and False are also rejected, they are probably a bug.
    - ValueError if a value is infinity (inf or -inf).
    - ValueError if there are no usable numbers (empty, or all missing).

    Special cases
    -------------
    - empty input     -> ValueError
    - one value       -> count 1, mean = that value, variance and std = nan
                         (we would divide by n - 1 = 0)
    - constant values -> variance is 0.0, or extremely close to it. For short
                         lists it is exactly 0.0. For long lists the mean
                         from equation (1) is rounded a little at every
                         step, so the variance can be a tiny leftover such
                         as 1e-29 (1000 copies of 3.7 gave 1.9e-29).
    - invalid values  -> TypeError or ValueError, see above

    Examples
    --------
    >>> r = welford([2, 4, 4, 4, 5, 5, 7, 9])
    >>> r["count"], r["mean"]
    (8, 5.0)
    >>> round(r["variance"], 6), round(r["std"], 6)
    (4.571429, 2.13809)
    >>> welford([1, None, float("nan"), 3])["dropped"]
    2
    """
    n = 0  # how many good numbers so far
    m = 0.0  # running mean, m_n in the paper
    S = 0.0  # running corrected sum of squares, S_n in the paper
    dropped = 0  # how many missing values we skipped

    for x in data:
        # 1. Missing value: skip it and count it
        if x is None:
            dropped = dropped + 1
            continue

        # 2. Not a number: stop with an error
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("welford: this is not a number: " + repr(x))

        # 3. NaN is also missing
        if math.isnan(x):
            dropped = dropped + 1
            continue

        # 4. Infinity: stop with an error
        if math.isinf(x):
            raise ValueError("welford: infinity is not allowed")

        # 5. The update, exactly as in the paper
        n = n + 1
        S = S + ((n - 1) / n) * (x - m) ** 2  # Formula I (uses OLD mean)
        m = ((n - 1) / n) * m + x / n  # equation (1)

    if n == 0:
        raise ValueError("welford: no usable numbers")

    if n == 1:
        variance = math.nan
        std = math.nan
    else:
        variance = S / (n - 1)
        std = math.sqrt(variance)

    return {
        "count": n,
        "mean": m,
        "variance": variance,
        "std": std,
        "dropped": dropped,
    }
# --- END WELFORD BLOCK ---

