"""Core A tests: count and minimum .

Standard library and pytest only. Every expected number is worked by hand.
Errors are checked by built-in parent class (TypeError / ValueError) and by
class NAME, so these tests pass the same before and after the Contract lane's
errors.py replaces Core A's temporary copy.
"""

import math
from decimal import Decimal
from fractions import Fraction

import pytest

from stateskol.descriptive import count, minimum
BAD_TYPE = TypeError    # bool, str, Decimal, Fraction (InvalidTypeError)
BAD_VALUE = ValueError  # inf, -inf, abs(n) > 2**53 (InvalidValueError)
EMPTY = ValueError      # no present values (EmptyDataError)


def error_name(function, data):
    """Run function(data), return the NAME of the error it raises."""
    try:
        function(data)
    except Exception as error:
        return type(error).__name__
    return None

NAN = float("nan")


# ---------------------------------------------------------------- hand-worked
# 2,4,4,4,5,5,7,9: eight values, the smallest is 2.
def test_hand_worked_basic():
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    assert count(data) == 8
    assert minimum(data) == 2.0


# 4, None, 2.5, NaN, 7: two are missing, so three are present: 4, 2.5, 7.
def test_hand_worked_with_missing():
    data = [4, None, 2.5, NAN, 7]
    assert count(data) == 3
    assert minimum(data) == 2.5


# ------------------------------------------------------------- usual cases
def test_negative_numbers():
    assert minimum([3, -7, 0, -2.5]) == -7.0
    assert count([3, -7, 0, -2.5]) == 4


def test_minimum_first_middle_last():
    assert minimum([1, 5, 9]) == 1.0
    assert minimum([5, 1, 9]) == 1.0
    assert minimum([9, 5, 1]) == 1.0


def test_minimum_returns_float():
    assert isinstance(minimum([3, 4]), float)
    assert isinstance(count([3, 4]), int)


def test_order_does_not_matter():
    assert minimum([9, 2, 5, 4, 7, 4, 5, 4]) == minimum([2, 4, 4, 4, 5, 5, 7, 9])


def test_works_on_tuple_and_set():
    assert minimum((3, 1, 2)) == 1.0
    assert count({3, 1, 2}) == 3


def test_input_is_not_changed():
    data = [3, None, 1]
    count(data)
    minimum(data)
    assert data == [3, None, 1]


def test_mixed_int_and_float():
    assert minimum([2, 1.5, 3]) == 1.5


# ------------------------------------------------------------ boundary pack
def test_empty():
    assert count([]) == 0
    with pytest.raises(EMPTY):
        minimum([])


def test_all_missing():
    assert count([None, NAN, None]) == 0
    with pytest.raises(EMPTY):
        minimum([None, NAN])


def test_single_value():
    assert count([42]) == 1
    assert minimum([42]) == 42.0


def test_constant_values():
    assert count([3.7] * 1000) == 1000
    assert minimum([3.7] * 1000) == 3.7


def test_ties_for_the_minimum():
    assert minimum([5, 2, 2, 9, 2]) == 2.0
    assert count([5, 2, 2, 9, 2]) == 5


@pytest.mark.parametrize("bad", [True, False])
def test_bool_rejected(bad):
    with pytest.raises(BAD_TYPE):
        count([1, bad])
    with pytest.raises(BAD_TYPE):
        minimum([1, bad])


@pytest.mark.parametrize("bad", ["3", "a", ""])
def test_str_rejected(bad):
    with pytest.raises(BAD_TYPE):
        count([1, bad])
    with pytest.raises(BAD_TYPE):
        minimum([1, bad])


@pytest.mark.parametrize("bad", [float("inf"), float("-inf")])
def test_inf_rejected(bad):
    with pytest.raises(BAD_VALUE):
        count([1, bad])
    with pytest.raises(BAD_VALUE):
        minimum([1, bad])


def test_nan_is_missing_not_an_error():
    assert count([1, NAN, 3]) == 2
    assert minimum([NAN, 3, 1]) == 1.0


def test_none_is_missing_not_an_error():
    assert count([None, 1]) == 1
    assert minimum([None, 1]) == 1.0


@pytest.mark.parametrize("bad", [Decimal("1.5"), Fraction(1, 2)])
def test_decimal_and_fraction_rejected(bad):
    with pytest.raises(BAD_TYPE):
        count([1, bad])
    with pytest.raises(BAD_TYPE):
        minimum([1, bad])


# the 2**53 boundary: 2**53 is exactly representable, 2**53 + 1 is not
def test_2_53_is_accepted():
    assert minimum([2 ** 53, 5]) == 5.0
    assert minimum([2 ** 53]) == float(2 ** 53)
    assert minimum([-(2 ** 53), 0]) == -float(2 ** 53)


def test_2_53_plus_1_rejected():
    with pytest.raises(BAD_VALUE):
        count([2 ** 53 + 1])
    with pytest.raises(BAD_VALUE):
        minimum([1, 2 ** 53 + 1])
    with pytest.raises(BAD_VALUE):
        minimum([-(2 ** 53) - 1])


# generators: read once
def test_generator_is_read_once():
    reads = []

    def numbers():
        for x in [5, 3, 8]:
            reads.append(x)
            yield x

    assert minimum(numbers()) == 3.0
    assert reads == [5, 3, 8]        # each value was produced exactly once

    reads.clear()
    assert count(numbers()) == 3
    assert reads == [5, 3, 8]


def test_used_up_generator_counts_zero():
    g = (x for x in [1, 2, 3])
    assert count(g) == 3
    assert count(g) == 0             # already used up: documented, not a bug
    with pytest.raises(EMPTY):
        minimum(g)


def test_invalid_value_deep_in_a_generator_still_rejected():
    g = (x for x in [1, 2, "3", 4])
    with pytest.raises(BAD_TYPE):
        minimum(g)


# ------------------------------------------------------------ large input
def test_large_list():
    data = list(range(100000, 0, -1)) + [None] * 10
    assert count(data) == 100000
    assert minimum(data) == 1.0


# ------------------------------------------------- the exact error classes
def test_exact_error_names():
    assert error_name(minimum, []) == "EmptyDataError"
    assert error_name(minimum, [None]) == "EmptyDataError"
    assert error_name(count, [True]) == "InvalidTypeError"
    assert error_name(minimum, ["3"]) == "InvalidTypeError"
    assert error_name(count, [Decimal("1")]) == "InvalidTypeError"
    assert error_name(count, [float("inf")]) == "InvalidValueError"
    assert error_name(minimum, [2 ** 53 + 1]) == "InvalidValueError"
    assert error_name(minimum, [1, 2, 3]) is None