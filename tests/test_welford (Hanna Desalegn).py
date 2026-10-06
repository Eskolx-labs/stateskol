"""Tests for Welford's online variance.

The module file name has spaces and parentheses, so it is loaded by path.
Ground truth for the larger checks is exact rational arithmetic
(``fractions.Fraction``), which has no rounding at all.
"""

import math
import random
from fractions import Fraction
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "stateskol"
    / "welford (Hanna Desalegn).py"
)
SPEC = spec_from_file_location("welford_hanna", MODULE_PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

welford = MODULE.welford
WelfordResult = MODULE.WelfordResult


def exact_mean_and_variance(data):
    """Two-pass mean and sample variance in exact rational arithmetic."""
    values = [Fraction(x) for x in data]
    n = len(values)
    mean = sum(values) / n
    return float(mean), float(sum((x - mean) ** 2 for x in values) / (n - 1))



# 1. Hand-worked values (worked on paper in the vault note)

def test_hand_worked_2_4_6_8():
    # n=4, mean 20/4 = 5, deviations -3 -1 1 3, S = 9+1+1+9 = 20,
    # variance 20/3, std sqrt(20/3)
    r = welford([2, 4, 6, 8])
    assert r.count == 4
    assert r.mean == 5.0
    assert r.variance == pytest.approx(20 / 3)
    assert r.std == pytest.approx(math.sqrt(20 / 3))
    assert r.dropped == 0


def test_hand_worked_3_7_8_10():
    # Formula I step by step, S_n = S_(n-1) + (n-1)/n * (x_n - m_(n-1))**2
    # x=3:  m=3,    S=0
    # x=7:  d=4,    S=0 + 1/2*16 = 8,      m=5
    # x=8:  d=3,    S=8 + 2/3*9  = 14,     m=6
    # x=10: d=4,    S=14 + 3/4*16 = 26,    m=7
    # variance 26/3, check: deviations -4 0 1 3 -> 16+0+1+9 = 26
    r = welford([3, 7, 8, 10])
    assert r.count == 4
    assert r.mean == 7.0
    assert r.variance == pytest.approx(26 / 3)
    assert r.std == pytest.approx(math.sqrt(26 / 3))


def test_two_values_smallest_defined_variance():
    # mean 2, S = 1 + 1 = 2, variance 2/1 = 2
    r = welford([1, 3])
    assert (r.count, r.mean, r.variance) == (2, 2.0, 2.0)


def test_negative_and_fractional_values():
    # mean 0.75; deviations -2.25 -0.75 0.75 2.25 -> S = 11.25, variance 3.75
    r = welford([-1.5, 0.0, 1.5, 3.0])
    assert r.mean == pytest.approx(0.75)
    assert r.variance == pytest.approx(3.75)



# 2. Checking the code against the paper

def test_code_agrees_with_paper_formulas():
    rng = random.Random(3)
    data = [rng.gauss(10, 4) for _ in range(500)]
    m, s = 0.0, 0.0
    for n, x in enumerate(data, start=1):
        s = s + (n - 1) / n * (x - m) ** 2  # Formula I, uses the old mean
        m = (n - 1) / n * m + x / n  # identity (1) in the paper's form
    r = welford(data)
    assert r.mean == pytest.approx(m, rel=1e-12)
    assert r.variance == pytest.approx(s / (len(data) - 1), rel=1e-12)


def test_delta_times_delta2_equals_formula_I():
    # identity (3): x_n - m_n = (n-1)/n * (x_n - m_(n-1)).
    # So (x_n - m_(n-1)) * (x_n - m_n) = (n-1)/n * (x_n - m_(n-1))**2,
    # i.e. the common "delta * delta2" update is Formula I.
    data = [Fraction(v) for v in (2, 9, 4, 7, 1, 12)]
    for n in range(2, len(data) + 1):
        m_prev = sum(data[: n - 1]) / (n - 1)
        m_now = sum(data[:n]) / n
        x = data[n - 1]
        assert x - m_now == Fraction(n - 1, n) * (x - m_prev)
        assert (x - m_prev) * (x - m_now) == Fraction(n - 1, n) * (x - m_prev) ** 2


def test_matches_exact_two_pass_on_random_data():
    rng = random.Random(42)
    data = [rng.gauss(50, 10) for _ in range(5000)]
    mean, var = exact_mean_and_variance(data)
    r = welford(data)
    assert r.mean == pytest.approx(mean, rel=1e-12)
    assert r.variance == pytest.approx(var, rel=1e-10)


def test_generator_is_consumed_once():
    pulled = []

    def stream():
        for x in [2, 4, 6, 8]:
            pulled.append(x)
            yield x

    assert welford(stream()) == welford([2, 4, 6, 8])
    assert pulled == [2, 4, 6, 8]


def test_returns_plain_python_floats():
    r = welford([2, 4, 6, 8])
    assert isinstance(r, WelfordResult)
    assert type(r.mean) is float and type(r.variance) is float



# 3. Missing values: dropped, counted, never filled

def test_missing_values_are_dropped_and_counted():
    r = welford([2, 4, None, 6, 8, float("nan")])
    assert r.count == 4
    assert r.dropped == 2
    assert r.mean == 5.0  # identical to [2, 4, 6, 8]: nothing was filled
    assert r.variance == pytest.approx(20 / 3)


def test_count_plus_dropped_is_total_length():
    data = [None, 1, float("nan"), 2, None, 3]
    r = welford(data)
    assert r.count + r.dropped == len(data)


# 4. Boundary cases: empty, single value, constant, invalid
def test_empty_input():
    r = welford([])
    assert r.count == 0 and r.dropped == 0
    assert math.isnan(r.mean) and math.isnan(r.variance) and math.isnan(r.std)


def test_all_values_missing():
    r = welford([None, float("nan"), None])
    assert r.count == 0 and r.dropped == 3
    assert math.isnan(r.mean) and math.isnan(r.variance)


def test_single_value():
    r = welford([7])
    assert r.count == 1 and r.mean == 7.0
    assert math.isnan(r.variance) and math.isnan(r.std)


def test_single_value_among_missing():
    r = welford([None, 7, float("nan")])
    assert (r.count, r.mean, r.dropped) == (1, 7.0, 2)
    assert math.isnan(r.variance)


@pytest.mark.parametrize("value", [5, 0, -3, 0.1, 1e9 + 0.5])
def test_constant_data_gives_zero_variance(value):
    r = welford([value] * 10)
    assert r.mean == float(value)
    assert r.variance == 0.0
    assert r.std == 0.0


@pytest.mark.parametrize("bad", ["2", b"2", [2], (2,), {"k": 2}, 1 + 2j, True, False])
def test_non_number_value_is_rejected(bad):
    with pytest.raises(TypeError, match="index 1"):
        welford([1, bad, 3])


def test_decimal_is_rejected():
    from decimal import Decimal

    with pytest.raises(TypeError, match="index 0"):
        welford([Decimal("1"), Decimal("2")])


@pytest.mark.parametrize("inf", [float("inf"), float("-inf")])
def test_infinity_is_rejected(inf):
    with pytest.raises(ValueError, match="index 2.*infinite"):
        welford([1, 2, inf, 4])


def test_huge_integer_is_rejected():
    with pytest.raises(ValueError, match="index 1.*too big"):
        welford([1, 10**400, 3])


def test_stops_at_first_bad_value_after_missing_ones():
    with pytest.raises(TypeError, match="index 2"):
        welford([None, float("nan"), "x", float("inf")])


@pytest.mark.parametrize("text", ["123", b"123", bytearray(b"123")])
def test_str_and_bytes_are_not_data(text):
    with pytest.raises(TypeError, match="iterable of numbers"):
        welford(text)


def test_mapping_is_not_data():
    with pytest.raises(TypeError, match="mapping"):
        welford({1: "a", 3: "b"})


@pytest.mark.parametrize("not_iterable", [123, 4.5, None, object()])
def test_data_that_is_not_iterable_is_rejected(not_iterable):
    with pytest.raises(TypeError, match="iterable"):
        welford(not_iterable)


def test_fraction_is_accepted():
    r = welford([Fraction(1, 2), Fraction(3, 2)])
    assert (r.mean, r.variance) == (1.0, 0.5)


def test_numpy_scalars_and_arrays_are_accepted():
    np = pytest.importorskip("numpy")
    expected = welford([2.0, 4.0, 6.0, 8.0])
    assert welford(np.array([2.0, 4.0, 6.0, 8.0])) == expected
    assert welford([np.int64(2), np.int64(4), np.int64(6), np.int64(8)]) == expected
    assert welford([np.float32(2), np.float32(4), np.float32(6), np.float32(8)]) == expected
    r = welford([np.float32(2), np.float32("nan"), np.nan, 4.0])
    assert (r.count, r.dropped) == (2, 2)


# 5. Numerical stability: large offset, small spread

def naive_variance(data):
    """The textbook shortcut (sum x^2 - (sum x)^2 / n) / (n - 1)."""
    n = len(data)
    return (sum(x * x for x in data) - sum(data) ** 2 / n) / (n - 1)


def test_stability_exact_offset_naive_fails_welford_exact():
    # offset 1e9 + [4, 7, 13, 16]: mean 1e9 + 10, deviations -6 -3 3 6,
    # S = 90, variance exactly 30. The naive formula returns 0.0 here.
    data = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    assert naive_variance(data) != pytest.approx(30.0, rel=0.1)
    r = welford(data)
    assert r.mean == 1e9 + 10
    assert r.variance == 30.0


def test_stability_noisy_large_offset_against_exact():
    # 2000 values 1e9 + N(0, 1). Every value is rounded, so this one really
    # stresses the update. Near 1e9 a float64 stores steps of about 1.2e-7,
    # so errors near 1e-7 are expected; we allow 1e-6 (see note).
    rng = random.Random(1)
    data = [1e9 + rng.gauss(0, 1) for _ in range(2000)]
    _, exact_var = exact_mean_and_variance(data)
    welford_err = abs(welford(data).variance - exact_var) / exact_var
    naive_err = abs(naive_variance(data) - exact_var) / exact_var
    assert welford_err < 1e-6
    assert naive_err > 1.0  # naive is off by more than 100 %