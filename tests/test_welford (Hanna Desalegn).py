"""Tests for Welford implementation."""

import math
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "stateskol"
    / "welford (Hanna Desalegn).py"
)

SPEC = spec_from_file_location("welford_hanna", MODULE_PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

welford = MODULE.welford


def test_hand_worked_example():
    """Check the hand-worked Welford example [2, 4, 6, 8]."""
    result = welford([2, 4, 6, 8])

    assert result.count == 4
    assert result.mean == 5.0
    assert result.variance == pytest.approx(20 / 3)
    assert result.std == pytest.approx(math.sqrt(20 / 3))
    assert result.dropped == 0


def test_missing_values_are_dropped_and_counted():
    """None and NaN are dropped instead of being imputed."""
    result = welford([2, 4, None, 6, 8, float("nan")])

    assert result.count == 4
    assert result.mean == 5.0
    assert result.variance == pytest.approx(20 / 3)
    assert result.dropped == 2


def test_empty_input():
    """An empty input has no defined sample statistics."""
    result = welford([])

    assert result.count == 0
    assert math.isnan(result.mean)
    assert math.isnan(result.variance)
    assert math.isnan(result.std)
    assert result.dropped == 0


def test_all_values_missing():
    """All missing observations produce no usable sample."""
    result = welford([None, float("nan"), None])

    assert result.count == 0
    assert math.isnan(result.mean)
    assert math.isnan(result.variance)
    assert math.isnan(result.std)
    assert result.dropped == 3


def test_single_value():
    """One observation has a defined mean but undefined sample variance."""
    result = welford([7])

    assert result.count == 1
    assert result.mean == 7.0
    assert math.isnan(result.variance)
    assert math.isnan(result.std)
    assert result.dropped == 0


def test_constant_values():
    """A constant sample has zero sample variance and standard deviation."""
    result = welford([5, 5, 5, 5])

    assert result.count == 4
    assert result.mean == 5.0
    assert result.variance == 0.0
    assert result.std == 0.0
    assert result.dropped == 0


def test_generator_is_consumed_once():
    """The implementation works with a one-pass iterable."""
    result = welford(x for x in [2, 4, 6, 8])

    assert result.count == 4
    assert result.mean == 5.0
    assert result.variance == pytest.approx(20 / 3)


def test_string_is_invalid():
    """Non-numeric observations raise TypeError."""
    with pytest.raises(TypeError):
        welford([1, "2", 3])


def test_boolean_is_invalid():
    """Boolean values are not treated as numeric observations."""
    with pytest.raises(TypeError):
        welford([1, True, 3])


def test_infinity_is_invalid():
    """Positive and negative infinity are rejected."""
    with pytest.raises(ValueError):
        welford([1, float("inf"), 3])

    with pytest.raises(ValueError):
        welford([1, float("-inf"), 3])


def test_numerical_stability_case():
    """Welford remains accurate for values with a large common offset."""
    data = [
        1_000_000_001,
        1_000_000_002,
        1_000_000_003,
        1_000_000_004,
        1_000_000_005,
    ]

    result = welford(data)

    assert result.count == 5
    assert result.mean == 1_000_000_003
    assert result.variance == pytest.approx(2.5)
    assert result.std == pytest.approx(math.sqrt(2.5))