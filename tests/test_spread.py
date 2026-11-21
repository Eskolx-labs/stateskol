import pytest
from stateskol.descriptive import quantile, iqr, variance, stdev, coefficient_variation
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


def test_variance_hand_worked():
    assert variance([2, 4, 6]) == 4.0
    assert variance([2, 4, 6], ddof=0) == pytest.approx(8 / 3)


def test_variance_big_numbers():
    x = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
    assert variance(x) == pytest.approx(1.6666667)


def test_variance_constant():
    assert variance([5, 5, 5]) == 0.0


def test_variance_single_value_refused():
    with pytest.raises(DomainError):
        variance([5])
    assert variance([5], ddof=0) == 0.0


def test_variance_bad_ddof():
    with pytest.raises(DomainError):
        variance([1, 2, 3], ddof=2)


def test_variance_empty():
    with pytest.raises(EmptyDataError):
        variance([])


def test_stdev():
    assert stdev([2, 4, 6]) == 2.0


def test_cv():
    assert coefficient_variation([2, 4, 6]) == 0.5


def test_cv_zero_mean_refused():
    with pytest.raises(DomainError):
        coefficient_variation([-1, 1])