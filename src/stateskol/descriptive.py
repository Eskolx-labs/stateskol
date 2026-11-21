"""descriptive.py: Numerics block only (variance algorithms). Self-contained.
"""

import math


# --- BEGIN NUMERICS BLOCK: variance algorithms (owner: yeabsira) ---

# ---- TEMPORARY: errors, until the Contract lane's errors.py is merged ----
# When errors.py lands: delete this TEMPORARY section and import
#     from stateskol.errors import DomainError, EmptyDataError
# at the top of the file. The tests check the class NAME and the built-in
# parent (ValueError), so they pass before and after the swap.
class EmptyDataError(ValueError):
    """No values, so the summary is undefined."""


class DomainError(ValueError):
    """An argument is outside the range the function is defined for."""
# ---- END TEMPORARY --------------------------------------------------------


def _check_ddof(ddof):
    """ddof must be exactly 0 (divide by n) or 1 (divide by n - 1)."""
    if isinstance(ddof, bool) or ddof not in (0, 1):
        raise DomainError("ddof must be 0 or 1, not " + repr(ddof))


def _welford_update(count, mean, m2, x):
    """One step of Welford's update (1962) for one new value x.

    Inputs
    ------
    count : int, how many values were seen before x.
    mean  : float, the running mean m(n-1) before x.
    m2    : float, the running corrected sum of squares S(n-1) before x.
    x     : float, the new value.

    Outputs
    -------
    (count + 1, new mean m(n), new corrected sum of squares S(n)).

    Method
    ------
    Welford's equation (1) and Formula I, with n = count + 1:
        m(n) = ((n-1)/n) * m(n-1) + x(n)/n
        S(n) = S(n-1) + ((n-1)/n) * (x(n) - m(n-1))**2
    The code uses the equivalent form
        delta = x - m(n-1)
        m(n)  = m(n-1) + delta / n
        S(n)  = S(n-1) + delta * (x - m(n))
    because, by identity (3) of the paper, x(n) - m(n) = ((n-1)/n) * delta,
    so delta * (x - m(n)) = ((n-1)/n) * delta**2. Both increments are never
    negative, so S never goes below zero.

    Examples
    --------
    >>> _welford_update(0, 0.0, 0.0, 5.0)
    (1, 5.0, 0.0)
    >>> _welford_update(1, 5.0, 0.0, 7.0)
    (2, 6.0, 2.0)
    """
    count = count + 1
    delta = x - mean
    mean = mean + delta / count
    m2 = m2 + delta * (x - mean)
    return count, mean, m2


def _welford_moments(values):
    """Run Welford's update over all values in ONE pass.

    Inputs: any iterable of floats (a generator is fine, it is read once).
    Outputs: (count, mean, m2), where m2 is the corrected sum of squares
    S = sum((x - mean)**2). For no values it returns (0, 0.0, 0.0).

    >>> _welford_moments([2, 4, 4, 4, 5, 5, 7, 9])
    (8, 5.0, 32.0)
    """
    count = 0
    mean = 0.0
    m2 = 0.0
    for x in values:
        count, mean, m2 = _welford_update(count, mean, m2, x)
    return count, mean, m2


def _variance_welford(values, ddof=1):
    """Variance by Welford's one-pass update. THIS is what the package uses.

    Inputs
    ------
    values : iterable of finite floats, already cleaned by the contract
             (missing values dropped, bad values refused). Read once.
    ddof   : 1 (default) divides by n - 1, the sample variance.
             0 divides by n, the population variance.

    Outputs
    -------
    float: S / (n - ddof), where S = sum((x - mean)**2).

    Algorithm
    ---------
    Welford (1962): keep the running mean and the running sum of squared
    deviations from it. No large number is ever subtracted from another
    nearly equal large number, so nothing is cancelled. One pass, no copy
    of the data. Constant data gives exactly 0.0.

    Assumptions
    -----------
    Values are real, finite and within abs(x) <= 2**53 (the week 2 rule),
    so each value is exact as a float.

    Errors
    ------
    - EmptyDataError : no values.
    - DomainError    : ddof is not 0 or 1, or n - ddof is not above 0
                       (one value with ddof=1: the sample variance divides
                       by zero and does not exist).

    Examples
    --------
    >>> _variance_welford([2, 4, 4, 4, 5, 5, 7, 9])
    4.571428571428571
    >>> _variance_welford([2, 4, 4, 4, 5, 5, 7, 9], ddof=0)
    4.0
    >>> _variance_welford([1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4])
    1.6666666666666667
    """
    _check_ddof(ddof)
    count, mean, m2 = _welford_moments(values)
    if count == 0:
        raise EmptyDataError("variance: no values")
    if count - ddof <= 0:
        raise DomainError("variance: needs more than ddof=" + str(ddof) + " values")
    return m2 / (count - ddof)


def _variance_two_pass(values, ddof=1):
    """Variance by two passes: the mean first, then the squared deviations.

    Stable, and the numpy method, but it must scan the data twice, so it
    copies an iterable into a list first. Used only to compare in tests.

    >>> _variance_two_pass([1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4])
    1.6666666666666667
    """
    _check_ddof(ddof)
    data = list(values)
    n = len(data)
    if n == 0:
        raise EmptyDataError("variance: no values")
    if n - ddof <= 0:
        raise DomainError("variance: needs more than ddof=" + str(ddof) + " values")
    mean = sum(data) / n
    total = 0.0
    for x in data:
        total = total + (x - mean) ** 2
    return total / (n - ddof)


def _variance_naive(values, ddof=1):
    """The textbook shortcut: mean of squares minus the square of the mean.

    NOT USED by the package. It is here only to show the failure: it
    subtracts two large, nearly equal numbers, and on data around 1e9 the
    answer is lost.

    >>> _variance_naive([1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4])
    0.0
    """
    _check_ddof(ddof)
    data = list(values)
    n = len(data)
    if n == 0:
        raise EmptyDataError("variance: no values")
    if n - ddof <= 0:
        raise DomainError("variance: needs more than ddof=" + str(ddof) + " values")
    mean = sum(data) / n
    sum_of_squares = 0.0
    for x in data:
        sum_of_squares = sum_of_squares + x * x
    return (sum_of_squares - n * mean * mean) / (n - ddof)
# --- END NUMERICS BLOCK ---