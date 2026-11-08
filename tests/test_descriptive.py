
"""Tests for Robel's descriptive statistics functions."""

import pytest

from stateskol.descriptive import (
    count,
    frequency_table,
    max as data_max,
    min as data_min,
    range as data_range,
)


# Shared boundary cases for the Week 1 team.
BOUNDARY_CASES = [
    ("single value", [8], 1, 8, 8, 0),
    ("constant values", [5, 5, 5, 5], 4, 5, 5, 0),
    ("tied values", [2, 4, 2, 4, 2], 5, 2, 4, 2),
]


@pytest.mark.parametrize(
    "name,data,expected_count,expected_min,expected_max,expected_range",
    BOUNDARY_CASES,
)
def test_boundary_cases(
    name, data, expected_count, expected_min, expected_max, expected_range
):
    assert count(data) == expected_count
    assert data_min(data) == expected_min
    assert data_max(data) == expected_max
    assert data_range(data) == expected_range


def test_count_normal_data():
    assert count([10, 20, 30, 40]) == 4


def test_min_normal_data():
    assert data_min([10, 20, 30, 40]) == 10


def test_max_normal_data():
    assert data_max([10, 20, 30, 40]) == 40


def test_range_normal_data():
    assert data_range([10, 20, 30, 40]) == 30


def test_frequency_table_normal_data():
    assert frequency_table([4, 2, 7, 2, 5, 4, 2]) == {
        2: 3,
        4: 2,
        5: 1,
        7: 1,
    }


def test_frequency_table_is_sorted():
    result = frequency_table([7, 2, 5, 2, 4])
    assert list(result.keys()) == [2, 4, 5, 7]


# Empty input boundary cases.
def test_count_empty_data():
    assert count([]) == 0


@pytest.mark.parametrize(
    "function",
    [data_min, data_max, data_range, frequency_table],
)
def test_other_functions_reject_empty_data(function):
    with pytest.raises(ValueError):
        function([])


# Invalid input boundary cases.
@pytest.mark.parametrize(
    "invalid_value",
    ["hello", True, complex(2, 3)],
)
def test_invalid_values_raise_type_error(invalid_value):
    functions = [count, data_min, data_max, data_range, frequency_table]

    for function in functions:
        with pytest.raises(TypeError):
            function([1, invalid_value, 3])


# Infinite values are not accepted.
@pytest.mark.parametrize(
    "infinite_value",
    [float("inf"), float("-inf")],
)
def test_infinite_values_raise_value_error(infinite_value):
    functions = [count, data_min, data_max, data_range, frequency_table]

    for function in functions:
        with pytest.raises(ValueError):
            function([1, infinite_value, 3])


# Missing values are dropped and reported with a warning.
def test_count_drops_none_and_nan():
    with pytest.warns(UserWarning, match="Dropped 2"):
        assert count([1, None, 2, float("nan")]) == 2


def test_frequency_table_drops_missing_values():
    with pytest.warns(UserWarning):
        result = frequency_table([2, None, 2, float("nan"), 3])

    assert result == {2: 2, 3: 1}


def test_all_missing_data_raises_for_minimum():
    with pytest.warns(UserWarning):
        with pytest.raises(ValueError):
            data_min([None, float("nan")])


def test_count_all_missing_data():
    with pytest.warns(UserWarning):
        assert count([None, float("nan")]) == 0


# Large integers must remain valid real-number inputs.
def test_large_integer_is_accepted():
    large_number = 10**1000

    assert count([large_number]) == 1
    assert data_min([large_number]) == large_number
    assert data_max([large_number]) == large_number
    assert data_range([large_number]) == 0


# The functions must not modify the original input.
def test_functions_do_not_modify_original_data():
    original = [4, 2, 7, 2, 5]
    original_copy = original.copy()

    count(original)
    data_min(original)
    data_max(original)
    data_range(original)
    frequency_table(original)

    assert original == original_copy
