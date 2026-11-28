import math
import pytest

from stateskol.welford import WelfordAccumulator


def test_mean_and_variance():
    acc = WelfordAccumulator()
    for value in [2, 4, 6]:
        acc.update(value)

    assert acc.count == 3
    assert acc.mean == pytest.approx(4.0)
    assert acc.variance() == pytest.approx(8 / 3)
    assert acc.variance(ddof=1) == pytest.approx(4.0)


def test_empty_accumulator():
    acc = WelfordAccumulator()
    assert acc.count == 0
    assert acc.mean is None
    with pytest.raises(ValueError):
        acc.variance()


def test_single_observation():
    acc = WelfordAccumulator()
    acc.update(7)
    assert acc.mean == 7.0
    assert acc.variance() == 0.0
    with pytest.raises(ValueError):
        acc.variance(ddof=1)


def test_constant_values():
    acc = WelfordAccumulator()
    for value in [5, 5, 5, 5]:
        acc.update(value)

    assert acc.mean == 5.0
    assert acc.variance() == 0.0


def test_standard_deviation():
    acc = WelfordAccumulator()
    for value in [2, 4, 6]:
        acc.update(value)

    assert acc.standard_deviation() == pytest.approx(math.sqrt(8 / 3))
    assert acc.standard_deviation(ddof=1) == pytest.approx(2.0)


@pytest.mark.parametrize("value", [None, "5", True, False])
def test_invalid_types(value):
    acc = WelfordAccumulator()
    with pytest.raises(TypeError):
        acc.update(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_values(value):
    acc = WelfordAccumulator()
    with pytest.raises(ValueError):
        acc.update(value)


def test_invalid_ddof():
    acc = WelfordAccumulator()
    acc.update(5)
    with pytest.raises(ValueError):
        acc.variance(ddof=2)
    with pytest.raises(TypeError):
        acc.variance(ddof=1.5)
