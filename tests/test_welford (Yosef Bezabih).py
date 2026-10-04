"""Tests for welford(): hand-computed values and boundary cases."""
import importlib
import math
import statistics

import pytest

mod = importlib.import_module("stateskol.welford (Yosef Bezabih)")
welford = mod.welford

HAND = [2, 4, 4, 4, 5, 5, 7, 9]  # worked by hand: sum of squares S = 32


# --- hand-computed values ---------------------------------------------------
def test_hand_worked_values():
    r = welford(HAND)
    assert r.count == 8
    assert r.mean == 5.0
    assert r.variance == pytest.approx(32 / 7)
    assert r.std == pytest.approx(math.sqrt(32 / 7))
    assert r.dropped == 0


def test_population_variance_ddof_0():
    r = welford(HAND, ddof=0)
    assert r.variance == pytest.approx(4.0)  # 32 / 8
    assert r.std == pytest.approx(2.0)


def test_two_values():
    r = welford([1, 3])  # mean 2, S = 2, variance 2
    assert (r.count, r.mean, r.variance) == (2, 2.0, 2.0)


# --- usual cases ------------------------------------------------------------
def test_matches_stdlib_statistics():
    data = [3.5, -1.2, 8.0, 0.0, 4.4, 4.4, -7.1]
    r = welford(data)
    assert r.mean == pytest.approx(statistics.mean(data))
    assert r.variance == pytest.approx(statistics.variance(data))
    assert r.std == pytest.approx(statistics.stdev(data))


def test_accepts_generator():
    r = welford(x for x in HAND)
    assert r.variance == pytest.approx(32 / 7)


def test_order_does_not_matter():
    assert welford(HAND[::-1]).variance == pytest.approx(welford(HAND).variance)


def test_negative_and_float_values():
    r = welford([-2.5, -1.5, -0.5])
    assert r.mean == pytest.approx(-1.5)
    assert r.variance == pytest.approx(1.0)


# --- boundary cases: empty, single value, constant, invalid ----------------
def test_empty_raises():
    with pytest.raises(ValueError):
        welford([])


def test_single_value_raises_for_sample_variance():
    with pytest.raises(ValueError):
        welford([5])


def test_single_value_ok_for_population_variance():
    r = welford([5], ddof=0)
    assert (r.count, r.mean, r.variance, r.std) == (1, 5.0, 0.0, 0.0)


def test_constant_values_have_zero_variance():
    r = welford([5, 5, 5, 5])
    assert r.variance == 0.0
    assert r.std == 0.0


@pytest.mark.parametrize("bad", ["a", True, [1], 1 + 2j])
def test_invalid_type_raises_typeerror(bad):
    with pytest.raises(TypeError):
        welford([1, 2, bad])


@pytest.mark.parametrize("bad", [float("inf"), float("-inf")])
def test_infinite_raises_valueerror(bad):
    with pytest.raises(ValueError):
        welford([1, 2, bad])


@pytest.mark.parametrize("ddof", [-1, 1.5, "1", True])
def test_bad_ddof_raises(ddof):
    with pytest.raises(ValueError):
        welford(HAND, ddof=ddof)


# --- missing values ---------------------------------------------------------
def test_none_and_nan_are_dropped_and_counted():
    r = welford([2, None, 4, float("nan"), 4, 4, 5, 5, 7, 9])
    assert r.dropped == 2
    assert r.count == 8
    assert r.variance == pytest.approx(32 / 7)


def test_all_missing_raises():
    with pytest.raises(ValueError):
        welford([None, float("nan")])


# --- numerical stability ----------------------------------------------------
def test_large_offset_stays_accurate():
    # true sample variance is exactly 30; the naive formula returns 0.0
    data = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    assert welford(data).variance == pytest.approx(30.0, rel=1e-9)