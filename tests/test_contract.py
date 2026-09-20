"""Contract tests. Owner: Yonas assembles, Kaleb owns the behavior."""

import math

import pytest

from stateskol._missing import apply_missing
from stateskol._validate import require_nonempty, to_float_list
from stateskol.basics import count, data_range, max_, min_


def test_ints_become_floats():
    assert to_float_list([1, 2, 3]) == [1.0, 2.0, 3.0]


def test_strings_and_bools_fail():
    with pytest.raises(TypeError):
        to_float_list("123")
    with pytest.raises(TypeError):
        to_float_list([1, True, 3])
    with pytest.raises(TypeError):
        to_float_list([1, "two", 3])


def test_infinities_fail():
    with pytest.raises(ValueError):
        to_float_list([1.0, math.inf])


def test_empty_needs_data():
    with pytest.raises(ValueError):
        require_nonempty([])


def test_missing_drop_counts():
    clean, dropped = apply_missing(to_float_list([1, None, float("nan"), 4]))
    assert clean == [1.0, 4.0]
    assert dropped == 2


def test_missing_raise():
    with pytest.raises(ValueError):
        apply_missing(to_float_list([1, None]), "raise")


def test_basics_hand_checked():
    data = [4, 8, 6, 5, 3, 7]
    assert count(data) == 6
    assert min_(data) == 3.0
    assert max_(data) == 8.0
    assert data_range(data) == 5.0


def test_basics_empty_fails():
    with pytest.raises(ValueError):
        min_([])
