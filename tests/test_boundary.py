import pytest
from stateskol.descriptive import (
    mean, median, mode, quantile, iqr, variance, stdev, coefficient_variation,
)
from stateskol.errors import EmptyDataError, InvalidValueError, MissingDataError

BASE = [1, 2, 2, 3, 4, 4, 5, 6, 7]
NAN = float("nan")


@pytest.mark.parametrize("fn", [iqr, variance, stdev, coefficient_variation])
def test_all_missing_refused(fn):
    with pytest.raises(EmptyDataError):
        fn([None, NAN])


def test_quantile_all_missing_refused():
    with pytest.raises(EmptyDataError):
        quantile([None, NAN], 0.5)


def test_single_value_quantile_and_iqr():
    assert quantile([5], 0.5) == 5.0
    assert iqr([5]) == 0.0


def test_constant_data():
    assert variance([4, 4, 4]) == 0.0
    assert stdev([4, 4, 4]) == 0.0
    assert coefficient_variation([4, 4, 4]) == 0.0
    assert iqr([4, 4, 4]) == 0.0


def test_ties():
    assert quantile([1, 2, 2, 2, 3], 0.5) == 2.0
    assert mode([1, 2, 2, 2, 3]) == [2.0]


def test_odd_and_even_length_quantile():
    assert quantile([1, 2, 3, 4, 5], 0.5) == 3.0
    assert quantile([1, 2, 3, 4], 0.5) == 2.5
    assert quantile([1, 2, 3, 4], 0.5) == median([1, 2, 3, 4])


def test_p_zero_and_one_with_missing():
    assert quantile([None, 3, 1, 2], 0) == 1.0
    assert quantile([None, 3, 1, 2], 1) == 3.0


def test_one_outlier_spread():
    with_outlier = BASE + [48]
    assert iqr(with_outlier) - iqr(BASE) < 1
    assert stdev(with_outlier) > 5 * stdev(BASE)


@pytest.mark.parametrize("fn", [quantile])
def test_strict_policy_quantile(fn):
    with pytest.raises(MissingDataError):
        fn([1, None, 3], 0.5, policy="strict")


@pytest.mark.parametrize("fn", [variance, stdev])
def test_strict_policy_spread(fn):
    with pytest.raises(MissingDataError):
        fn([1, None, 3], policy="strict")


def test_float_boundary_refused():
    with pytest.raises(InvalidValueError):
        variance([1, 2**53 + 1])