"""Tests for welford (Yeabsira Tesfaye).

Run with:  pytest
The file name has spaces and brackets, so we load it with its path.
"""

import importlib.util
import math
from pathlib import Path

import pytest


def load_welford():
    folder = Path(__file__).resolve().parent
    name = "welford (Yeabsira Tesfaye).py"
    for path in (folder / name, folder.parent / "src" / "stateskol" / name):
        if path.exists():
            spec = importlib.util.spec_from_file_location("welford_yt", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.welford
    raise FileNotFoundError(name)


welford = load_welford()


# ---------- hand-worked ----------
# Data: 2, 4, 4, 4, 5, 5, 7, 9
# n = 8, sum = 40, mean = 5
# squared distances: 9 + 1 + 1 + 1 + 0 + 0 + 4 + 16 = 32
# variance = 32 / 7, std = square root of that
def test_hand_worked():
    r = welford([2, 4, 4, 4, 5, 5, 7, 9])
    assert r["count"] == 8
    assert r["mean"] == 5.0
    assert r["variance"] == pytest.approx(32 / 7, rel=1e-12)
    assert r["std"] == pytest.approx(math.sqrt(32 / 7), rel=1e-12)
    assert r["dropped"] == 0


# Data: 1, 2, 3, 4  -> mean 2.5, squared distances 2.25+0.25+0.25+2.25 = 5
def test_hand_worked_second():
    r = welford([1, 2, 3, 4])
    assert r["count"] == 4
    assert r["mean"] == 2.5
    assert r["variance"] == pytest.approx(5 / 3, rel=1e-12)


# (mean, m2) after each number, worked by hand
def test_step_by_step():
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    steps = [
        (2.0, 0.0),
        (3.0, 2.0),
        (10 / 3, 8 / 3),
        (3.5, 3.0),
        (3.8, 4.8),
        (4.0, 6.0),
        (31 / 7, 96 / 7),
        (5.0, 32.0),
    ]
    for i in range(len(steps)):
        mean, m2 = steps[i]
        r = welford(data[: i + 1])
        assert r["mean"] == pytest.approx(mean, rel=1e-12)
        if i > 0:
            assert r["variance"] * i == pytest.approx(m2, rel=1e-12)


# ---------- usual cases ----------
def test_negative_and_decimal_numbers():
    r = welford([-1.5, 0.0, 1.5])
    assert r["mean"] == 0.0
    assert r["variance"] == pytest.approx(2.25, rel=1e-12)


def test_tuple_works():
    assert welford((1, 2, 3))["variance"] == pytest.approx(1.0)


def test_order_does_not_matter():
    a = welford([9, 2, 5, 4, 7, 4, 5, 4])
    b = welford([2, 4, 4, 4, 5, 5, 7, 9])
    assert a["variance"] == pytest.approx(b["variance"], rel=1e-12)


# ---------- boundary cases ----------
def test_empty():
    with pytest.raises(ValueError):
        welford([])


def test_all_missing():
    with pytest.raises(ValueError):
        welford([None, float("nan")])


def test_single_value():
    r = welford([42])
    assert r["count"] == 1
    assert r["mean"] == 42.0
    assert math.isnan(r["variance"])
    assert math.isnan(r["std"])


def test_constant_values_short():
    r = welford([3.7] * 5)
    assert r["variance"] == 0.0
    assert r["std"] == 0.0


def test_constant_values_long():
    # the paper's mean formula rounds a little at each step, so the answer
    # is not always exactly 0.0, but it is tiny (about 1e-29 here)
    r = welford([3.7] * 1000)
    assert r["count"] == 1000
    assert r["mean"] == pytest.approx(3.7, rel=1e-12)
    assert abs(r["variance"]) < 1e-20


@pytest.mark.parametrize("bad", ["a", "1", True, False, 1 + 2j, [1]])
def test_invalid_type(bad):
    with pytest.raises(TypeError):
        welford([1.0, bad, 3.0])


@pytest.mark.parametrize("bad", [float("inf"), float("-inf")])
def test_infinity(bad):
    with pytest.raises(ValueError):
        welford([1.0, bad, 3.0])


# ---------- missing values ----------
def test_missing_are_dropped_and_counted():
    r = welford([2, None, 4, float("nan"), 4, 4, 5, 5, 7, 9])
    assert r["dropped"] == 2
    assert r["count"] == 8
    assert r["variance"] == pytest.approx(32 / 7, rel=1e-12)


def test_nothing_dropped():
    assert welford([1, 2])["dropped"] == 0


# ---------- numerical stability ----------
# Distances from the mean are -6, -3, 3, 6, so the true variance is
# (36 + 9 + 9 + 36) / 3 = 30 exactly.
BIG = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]


def test_stability_welford():
    r = welford(BIG)
    assert r["mean"] == 1e9 + 10
    assert r["variance"] == pytest.approx(30.0, rel=1e-12)


def test_stability_naive_formula_fails():
    # the textbook formula: (sum of squares - (sum)^2 / n) / (n - 1)
    n = len(BIG)
    sum_of_squares = sum(x * x for x in BIG)
    total = sum(BIG)
    naive = (sum_of_squares - total * total / n) / (n - 1)
    assert abs(naive - 30.0) > 1e-6

