import pytest
from stateskol.descriptive import mean, median, mode
from stateskol.errors import EmptyDataError, MissingDataError, InvalidTypeError

BASE = [1, 2, 2, 3, 4, 4, 5, 6, 7]


def test_mean():
    assert mean([1, 2, 3, 10]) == 4.0


def test_median_odd_and_even():
    assert median([3, 1, 2]) == 2.0
    assert median([4, 1, 3, 2]) == 2.5


def test_mode_tie():
    assert mode([1, 2, 2, 3]) == [2.0]
    assert mode([1, 1, 2, 2, 3]) == [1.0, 2.0]


def test_single_value():
    assert mean([7]) == 7.0
    assert median([7]) == 7.0
    assert mode([7]) == [7.0]


def test_outlier_demo():
    assert mean(BASE) == pytest.approx(3.78, abs=0.005)
    assert median(BASE) == 4.0
    assert mean(BASE + [48]) == pytest.approx(8.2)
    assert median(BASE + [48]) == 4.0


def test_missing_dropped():
    assert mean([1, None, 3, float("nan")]) == 2.0


def test_strict_raises():
    with pytest.raises(MissingDataError):
        mean([1, None, 3], policy="strict")


def test_empty_raises():
    with pytest.raises(EmptyDataError):
        mean([])
    with pytest.raises(EmptyDataError):
        median([None])
    with pytest.raises(EmptyDataError):
        mode([])


def test_bool_rejected():
    with pytest.raises(InvalidTypeError):
        mean([1, True, 3])