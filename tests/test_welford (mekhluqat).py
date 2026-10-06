"""Tests for welford: hand-computed values, boundary cases, stability."""

import importlib.util
import math
from pathlib import Path

import pytest

_path = (
    Path(__file__).resolve().parents[1] / "src" / "stateskol" / "welford (mekhluqat).py"
)
_spec = importlib.util.spec_from_file_location("welford_mekhluqat", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
welford = _module.welford


# --- hand-worked values -----------------------------------------------------
# [2, 4, 6, 8]: n = 4, mean = 20 / 4 = 5
# deviations -3, -1, 1, 3 -> M2 = 9 + 1 + 1 + 9 = 20
# variance = 20 / 3, std = sqrt(20 / 3)
def test_hand_worked_2_4_6_8():
    r = welford([2, 4, 6, 8])
    assert r.count == 4
    assert r.mean == 5.0
    assert r.variance == pytest.approx(20 / 3)
    assert r.std == pytest.approx(math.sqrt(20 / 3))
    assert r.dropped == 0


# [1, 2, 3, 4, 5]: mean = 3, M2 = 4 + 1 + 0 + 1 + 4 = 10, variance = 10 / 4 = 2.5
def test_hand_worked_1_to_5():
    r = welford([1, 2, 3, 4, 5])
    assert r.count == 5
    assert r.mean == 3.0
    assert r.variance == pytest.approx(2.5)
    assert r.std == pytest.approx(math.sqrt(2.5))


# [-1.0, 1.0]: mean = 0, M2 = 1 + 1 = 2, variance = 2 / 1 = 2
def test_negative_and_float_values():
    r = welford([-1.0, 1.0])
    assert r.mean == 0.0
    assert r.variance == pytest.approx(2.0)
    assert r.std == pytest.approx(math.sqrt(2.0))


def test_accepts_generator_and_unpacks_as_five_values():
    count, mean, variance, std, dropped = welford(x for x in [2, 4, 6, 8])
    assert (count, mean, dropped) == (4, 5.0, 0)
    assert variance == pytest.approx(20 / 3)
    assert std == pytest.approx(math.sqrt(20 / 3))


# --- boundary cases ---------------------------------------------------------
def test_empty_input():
    r = welford([])
    assert r.count == 0
    assert math.isnan(r.mean)
    assert math.isnan(r.variance)
    assert math.isnan(r.std)
    assert r.dropped == 0


def test_single_value():
    r = welford([7])
    assert r.count == 1
    assert r.mean == 7.0
    assert math.isnan(r.variance)
    assert math.isnan(r.std)


def test_constant_values():
    r = welford([5, 5, 5, 5])
    assert r.count == 4
    assert r.mean == 5.0
    assert r.variance == 0.0
    assert r.std == 0.0


# --- missing values: dropped and counted ------------------------------------
def test_missing_values_are_dropped_and_counted():
    r = welford([2, 4, None, 6, 8, float("nan")])
    assert r.count == 4
    assert r.mean == 5.0
    assert r.variance == pytest.approx(20 / 3)
    assert r.dropped == 2


def test_all_missing_behaves_like_empty():
    r = welford([None, float("nan")])
    assert r.count == 0
    assert math.isnan(r.mean)
    assert r.dropped == 2


# --- invalid values fail fast -----------------------------------------------
@pytest.mark.parametrize("bad", ["a", True, False, [1], 1 + 2j])
def test_invalid_type_raises_type_error(bad):
    with pytest.raises(TypeError):
        welford([1, 2, bad])


@pytest.mark.parametrize("bad", [float("inf"), float("-inf")])
def test_infinite_value_raises_value_error(bad):
    with pytest.raises(ValueError):
        welford([1, 2, bad])


# --- numerical stability ----------------------------------------------------
# Values sit near 1e9, so the naive formula sum(x*x) - sum(x)**2 / n subtracts
# two huge, nearly equal numbers and loses the answer. By hand the mean is
# 1e9 + 10, deviations are -6, -3, 3, 6, M2 = 36 + 9 + 9 + 36 = 90,
# variance = 90 / 3 = 30.
def test_large_offset_stability():
    data = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    r = welford(data)
    assert r.variance == pytest.approx(30.0, rel=1e-9)


# --- input contract: non-iterables, text and huge integers -------------------
@pytest.mark.parametrize("bad", [123, 4.5, None])
def test_non_iterable_raises_type_error(bad):
    with pytest.raises(TypeError):
        welford(bad)


@pytest.mark.parametrize("bad", ["123", b"12", bytearray(b"12")])
def test_text_and_bytes_raise_type_error(bad):
    # Iterating bytes yields ints, so without this check b"12" would be
    # silently read as the numbers 49 and 50.
    with pytest.raises(TypeError):
        welford(bad)


def test_huge_integer_raises_value_error():
    # math.isinf(10**400) raises OverflowError; the contract says ValueError.
    with pytest.raises(ValueError):
        welford([1, 10**400, 3])
