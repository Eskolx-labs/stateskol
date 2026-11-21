import pytest
from stateskol.descriptive import quantile, iqr
from stateskol.errors import DomainError, EmptyDataError, UnsupportedRuleError

TEN = [2, 4, 4, 5, 7, 9, 11, 13, 15, 18]


def test_quantile_hand_worked():
    assert quantile([1, 2, 3, 4], 0.25) == 1.75
    assert quantile([1, 2, 3, 4, 5], 0.25) == 2.0


def test_quantile_ten_values():
    assert quantile(TEN, 0.75) == 12.5


def test_quantile_ends():
    assert quantile([3, 1, 2], 0) == 1.0
    assert quantile([3, 1, 2], 1) == 3.0


def test_quantile_p_out_of_range():
    with pytest.raises(DomainError):
        quantile([1, 2, 3], 1.5)
    with pytest.raises(DomainError):
        quantile([1, 2, 3], -0.1)


def test_quantile_other_method_refused():
    with pytest.raises(UnsupportedRuleError):
        quantile(TEN, 0.75, method="type6")


def test_quantile_empty():
    with pytest.raises(EmptyDataError):
        quantile([], 0.5)


def test_iqr():
    assert iqr([1, 2, 3, 4]) == 1.5


def test_iqr_constant():
    assert iqr([5, 5, 5, 5]) == 0.0