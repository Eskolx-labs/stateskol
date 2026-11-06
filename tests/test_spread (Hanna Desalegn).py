"""Tests for the spread block: contract, quantile, IQR, sample variance and std.

Standard library only. Hand-worked values come from Ross 6th ed. 2.3.2 and
2.3.3 and are worked on paper in the vault note. The module file name has
spaces, so it is loaded by path.
"""

import math
import random
from fractions import Fraction
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "stateskol" / "spread (Hanna Desalegn).py"
SPEC = spec_from_file_location("spread_hanna", MODULE_PATH)
sp = module_from_spec(SPEC)
SPEC.loader.exec_module(sp)

NOISE = [82, 89, 94, 110, 74, 122, 112, 95, 100, 78, 65, 60, 90, 83, 87, 75, 114, 85,
         69, 94, 124, 115, 107, 88, 97, 74, 72, 68, 83, 91, 90, 102, 77, 125, 108, 65]


def exact_variance(data):
    # two-pass in exact fractions, no rounding at all
    xs = [Fraction(x) for x in data]
    mean = sum(xs) / len(xs)
    return float(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))


# hand-worked values from Ross

def test_ross_2_3_f_variance():
    # A: mean 6, deviations -3 -2 0 1 4, S = 9+4+0+1+16 = 30, s^2 = 30/4
    assert sp.sample_variance([3, 4, 6, 7, 10]) == 7.5
    # B: mean 6, S = 676+1+81+324 = 1082, s^2 = 1082/3
    assert sp.sample_variance([-20, 5, 15, 24]) == pytest.approx(1082 / 3)


def test_ross_2_3_g_airline_accidents():
    # Ross shifts by 18: sum y^2 = 314, ybar = -2, s^2 = (314 - 9*4)/8
    assert sp.sample_variance([25, 20, 21, 18, 13, 13, 7, 9, 18]) == pytest.approx(34.75)


def test_hand_worked_welford_table():
    # n m S: 1 2 0 | 2 3 2 | 3 3.33 2.67 | ... | 8 5 32, s^2 = 32/7
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    assert sp.sample_variance(data) == pytest.approx(32 / 7)
    assert sp.sample_std(data) == pytest.approx(math.sqrt(32 / 7))


def test_ross_2_3_h_rule():
    # n = 25: p = .1 -> np = 2.5 -> 3rd value, p = .8 -> np = 20 -> avg of 20th and 21st
    data = list(range(1, 26))
    assert sp.quantile(data, 0.10) == 3
    assert sp.quantile(data, 0.80) == 20.5


def test_ross_2_3_i_noise_quartiles():
    # n = 36, np = 9, 18, 27 are whole, so average neighbours
    # sorted 9th and 10th are 75 and 77, so Q1 = 76 (the book prints 74.5)
    assert sp.quantile(NOISE, 0.25) == 76
    assert sp.quantile(NOISE, 0.50) == 89.5
    assert sp.quantile(NOISE, 0.75) == 104.5
    assert sp.iqr(NOISE) == 28.5


def test_small_quantiles_by_hand():
    data = [7, 1, 3, 9, 5]  # sorted 1 3 5 7 9
    assert sp.quantile(data, 0.5) == 5  # np = 2.5 -> 3rd
    assert sp.quantile(data, 0.2) == 2  # np = 1 -> avg of 1st and 2nd
    assert sp.quantile(data, 0.25) == 3  # np = 1.25 -> 2nd
    assert sp.quantile(data, 0) == 1
    assert sp.quantile(data, 1) == 9
    assert sp.iqr(data) == 7 - 3


# boundary pack: empty, single, constant, ties, invalid

def test_empty_raises():
    for f in (sp.sample_variance, sp.sample_std, sp.iqr, sp.spread, sp.clean):
        with pytest.raises(ValueError, match="no valid values"):
            f([])
    with pytest.raises(ValueError):
        sp.quantile([], 0.5)


def test_only_missing_raises():
    with pytest.raises(ValueError, match="dropped 3 missing"):
        sp.clean([None, float("nan"), None])


def test_single_value():
    with pytest.raises(ValueError, match="at least 2"):
        sp.sample_variance([4])
    with pytest.raises(ValueError):
        sp.sample_std([4])
    assert sp.quantile([4], 0.3) == 4
    assert sp.iqr([4]) == 0
    r = sp.spread([4])
    assert r.count == 1 and math.isnan(r.variance) and r.median == 4


def test_constant_values_zero_spread():
    data = [2.5] * 7
    assert sp.sample_variance(data) == 0.0
    assert sp.sample_std(data) == 0.0
    assert sp.iqr(data) == 0.0


def test_ties():
    data = [1, 2, 2, 2, 3]
    assert sp.quantile(data, 0.25) == 2
    assert sp.quantile(data, 0.75) == 2
    assert sp.iqr(data) == 0
    assert sp.sample_variance(data) == pytest.approx(0.5)  # S = 1+0+0+0+1 = 2, /4


@pytest.mark.parametrize("bad", ["3", True, False, 1 + 2j, [1], object()])
def test_invalid_value_type_fails_fast(bad):
    with pytest.raises(TypeError, match="index 1"):
        sp.sample_variance([1, bad, 3])


@pytest.mark.parametrize("bad", [float("inf"), float("-inf"), 10 ** 400])
def test_invalid_value_range_fails_fast(bad):
    with pytest.raises(ValueError, match="index 2"):
        sp.quantile([1, 2, bad], 0.5)


@pytest.mark.parametrize("bad", ["123", b"12", {1: 2}, 5, None])
def test_invalid_container(bad):
    with pytest.raises(TypeError):
        sp.clean(bad)


@pytest.mark.parametrize("p", [-0.1, 1.5, float("nan")])
def test_p_out_of_range(p):
    with pytest.raises(ValueError):
        sp.quantile([1, 2, 3], p)


def test_p_wrong_type():
    with pytest.raises(TypeError):
        sp.quantile([1, 2, 3], "0.5")
    with pytest.raises(TypeError):
        sp.quantile([1, 2, 3], True)


# missing-value rule: drop and report, never fill

def test_missing_dropped_and_counted():
    values, dropped = sp.clean([3, None, 4, float("nan"), 6, 7, 10])
    assert values == [3, 4, 6, 7, 10]
    assert dropped == 2
    r = sp.spread([3, None, 4, float("nan"), 6, 7, 10])
    assert (r.count, r.dropped, r.variance) == (5, 2, 7.5)


def test_missing_does_not_change_results():
    with_missing = [None, 3, 4, float("nan"), 6, 7, 10, None]
    assert sp.sample_variance(with_missing) == sp.sample_variance([3, 4, 6, 7, 10])
    assert sp.quantile(with_missing, 0.5) == 6


# other inputs and properties

def test_accepts_any_iterable_and_number_type():
    gen = (x for x in [3, 4, 6, 7, 10])
    assert sp.sample_variance(gen) == 7.5
    assert sp.sample_variance([Fraction(1, 2), 1, 1.5]) == 0.25


def test_order_does_not_matter():
    data = [3.1, 8.2, 1.7, 9.9, 4.4, 4.4, 0.3]
    rev = data[::-1]
    assert sp.quantile(data, 0.3) == sp.quantile(rev, 0.3)
    assert sp.sample_variance(data) == pytest.approx(sp.sample_variance(rev), rel=1e-14)


def test_shift_and_scale_ross_identity():
    # Ross 2.3.2: y = a + b*x gives s_y^2 = b^2 * s_x^2
    x = [3, 4, 6, 7, 10]
    y = [100 + 3 * v for v in x]
    assert sp.sample_variance(y) == pytest.approx(9 * 7.5)
    assert sp.iqr(y) == pytest.approx(3 * sp.iqr(x))


def test_spread_matches_single_functions():
    r = sp.spread(NOISE)
    assert r.count == 36 and r.dropped == 0
    assert r.variance == sp.sample_variance(NOISE)
    assert r.std == sp.sample_std(NOISE)
    assert (r.q1, r.median, r.q3, r.iqr) == (76, 89.5, 104.5, 28.5)


def test_against_exact_arithmetic():
    rng = random.Random(7)
    for _ in range(200):
        data = [rng.uniform(-50, 50) for _ in range(rng.randint(2, 60))]
        assert sp.sample_variance(data) == pytest.approx(exact_variance(data), rel=1e-12)


# numerical stability, Welford (1962)

def naive_variance(data):
    n = len(data)
    return (sum(x * x for x in data) - sum(data) ** 2 / n) / (n - 1)


def test_large_mean_is_stable():
    data = [1e9 + v for v in [4, 7, 13, 16]]
    assert naive_variance(data) != pytest.approx(30)  # naive loses every digit here
    assert sp.sample_variance(data) == 30.0
    assert sp.iqr(data) == sp.iqr([4, 7, 13, 16])
