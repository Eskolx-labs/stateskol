"""Tests for Welford's online variance (author: Rebika Yihenew).

Stdlib only. The module file name has spaces and parentheses, so a normal
``import`` cannot load it; we load it by path with importlib instead.
"""

import importlib.util
import math
import random
import statistics
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "stateskol"
    / "welford (Rebika Yihenew).py"
)
_spec = importlib.util.spec_from_file_location("welford_rebika", _MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

welford = _module.welford
WelfordResult = _module.WelfordResult


# --------------------------------------------------------------------------
# 1. Hand-computed values (worked on paper first; see the vault note)
# --------------------------------------------------------------------------
def test_hand_worked_three_values():
    # mean 4; squared deviations 4, 0, 4 -> M2 = 8; variance 8/2 = 4; sd 2
    r = welford([2, 4, 6])
    assert r.count == 3
    assert r.mean == 4.0
    assert r.variance == 4.0
    assert r.std == 2.0
    assert r.n_dropped == 0


def test_hand_worked_eight_values():
    # mean 5; squared deviations 9,1,1,1,0,0,4,16 -> M2 = 32; variance 32/7
    r = welford([2, 4, 4, 4, 5, 5, 7, 9])
    assert r.count == 8
    assert r.mean == pytest.approx(5.0)
    assert r.variance == pytest.approx(32 / 7)
    assert r.std == pytest.approx(math.sqrt(32 / 7))


def test_two_values_smallest_valid_input():
    # mean 2; M2 = 1 + 1 = 2; variance 2/1 = 2; sd sqrt(2)
    r = welford([1, 3])
    assert r.count == 2
    assert r.mean == 2.0
    assert r.variance == 2.0
    assert r.std == pytest.approx(math.sqrt(2))


def test_result_is_a_named_tuple_with_expected_fields():
    r = welford([1, 2, 3])
    assert isinstance(r, WelfordResult)
    assert r._fields == ("count", "mean", "variance", "std", "n_dropped")
    count, mean, variance, std, n_dropped = r  # unpackable
    assert (count, mean, n_dropped) == (3, 2.0, 0)


# --------------------------------------------------------------------------
# 2. Usual cases
# --------------------------------------------------------------------------
def test_negative_and_float_values():
    r = welford([-1.5, 0.0, 1.5, 3.0])
    assert r.mean == pytest.approx(0.75)
    assert r.variance == pytest.approx(statistics.variance([-1.5, 0.0, 1.5, 3.0]))


def test_accepts_tuple_and_generator():
    expected = welford([1, 2, 3, 4])
    assert welford((1, 2, 3, 4)) == expected
    assert welford(x for x in [1, 2, 3, 4]) == expected


def test_generator_is_read_exactly_once():
    consumed = []

    def stream():
        for x in [1, 2, 3, 4]:
            consumed.append(x)
            yield x

    welford(stream())
    assert consumed == [1, 2, 3, 4]  # each element produced once, one pass


def test_matches_stdlib_on_random_data():
    rng = random.Random(42)
    data = [rng.gauss(50, 10) for _ in range(5000)]
    r = welford(data)
    assert r.mean == pytest.approx(statistics.fmean(data), rel=1e-12)
    assert r.variance == pytest.approx(statistics.variance(data), rel=1e-9)
    assert r.std == pytest.approx(statistics.stdev(data), rel=1e-9)


def test_shift_invariance():
    data = [3.0, 7.5, 1.25, 9.0, 4.0]
    shifted = [x + 1000.0 for x in data]
    assert welford(shifted).variance == pytest.approx(welford(data).variance, rel=1e-9)


def test_scaling_multiplies_variance_by_square():
    data = [3.0, 7.5, 1.25, 9.0, 4.0]
    scaled = [x * 3 for x in data]
    assert welford(scaled).variance == pytest.approx(
        9 * welford(data).variance, rel=1e-12
    )


# --------------------------------------------------------------------------
# 3. Missing values: dropped, counted, never filled
# --------------------------------------------------------------------------
def test_missing_values_are_dropped_and_counted():
    r = welford([2, None, 4, float("nan"), 6])
    assert r.n_dropped == 2
    assert r.count == 3
    assert r.mean == 4.0
    assert r.variance == 4.0  # same as [2, 4, 6]: nothing was filled in


def test_count_plus_dropped_equals_total_seen():
    data = [1, None, 2, float("nan"), 3, None, 4]
    r = welford(data)
    assert r.count + r.n_dropped == len(data)


def test_no_missing_means_zero_dropped():
    assert welford([1.0, 2.0]).n_dropped == 0


# --------------------------------------------------------------------------
# 4. Boundary cases: empty, single value, constant, invalid
# --------------------------------------------------------------------------
def test_empty_input_raises():
    with pytest.raises(ValueError, match="at least 2"):
        welford([])


def test_all_missing_raises_and_reports_dropped():
    with pytest.raises(ValueError, match="2 missing"):
        welford([None, float("nan")])


@pytest.mark.parametrize("data", [[5], [5.5], (7,)])
def test_single_value_raises(data):
    with pytest.raises(ValueError, match="got 1"):
        welford(data)


def test_single_valid_value_among_missing_raises():
    with pytest.raises(ValueError, match="got 1"):
        welford([None, 3, float("nan")])


@pytest.mark.parametrize("value", [5, 0, -3, 0.1, 1e9 + 0.5])
def test_constant_values_have_exactly_zero_variance(value):
    r = welford([value] * 10)
    assert r.count == 10
    assert r.mean == float(value)
    assert r.variance == 0.0
    assert r.std == 0.0


@pytest.mark.parametrize("bad", ["a", "1", b"x", [2], (1,), {"k": 1}, 1 + 2j])
def test_non_numeric_element_raises_type_error(bad):
    with pytest.raises(TypeError, match="position 1"):
        welford([1, bad, 3])


@pytest.mark.parametrize("flag", [True, False])
def test_bool_is_rejected(flag):
    with pytest.raises(TypeError, match="position 1"):
        welford([1, flag, 3])


@pytest.mark.parametrize("inf", [float("inf"), float("-inf")])
def test_infinity_raises_value_error(inf):
    with pytest.raises(ValueError, match="position 2.*infinite"):
        welford([1, 2, inf, 4])


def test_integer_too_large_for_float_raises_value_error():
    with pytest.raises(ValueError, match="too large"):
        welford([1, 10**400, 3])


@pytest.mark.parametrize("not_iterable", [123, 4.5, object()])
def test_non_iterable_raises_type_error(not_iterable):
    with pytest.raises(TypeError, match="iterable"):
        welford(not_iterable)


@pytest.mark.parametrize("text", ["12345", b"12345"])
def test_string_or_bytes_as_data_raises_type_error(text):
    with pytest.raises(TypeError, match="str/bytes"):
        welford(text)


def test_invalid_value_fails_fast_even_after_missing_values():
    with pytest.raises(TypeError, match="position 2"):
        welford([None, float("nan"), "x"])


# --------------------------------------------------------------------------
# 5. Numerical stability: large offset, small spread
# --------------------------------------------------------------------------
def test_stability_large_offset():
    # deviations from the mean 1e9+10 are -6, -3, 3, 6 -> M2 = 90, var = 30.
    # The naive mean(x**2) - mean(x)**2 formula returns 0.0 on this data.
    r = welford([1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16])
    assert r.mean == pytest.approx(1e9 + 10)
    assert r.variance == pytest.approx(30.0, rel=1e-12)
    assert r.std == pytest.approx(math.sqrt(30.0), rel=1e-12)


def test_stability_large_offset_many_values():
    rng = random.Random(7)
    noise = [rng.gauss(0, 1) for _ in range(2000)]
    big = [1e8 + x for x in noise]
    assert welford(big).variance == pytest.approx(
        statistics.variance(noise), rel=1e-6
    )


# --------------------------------------------------------------------------
# 6. The paper is the specification: Welford (1962), Formula I and identity (1)
# --------------------------------------------------------------------------
def test_matches_welford_1962_formula_I():
    # Formula I:      S_n = S_(n-1) + (n-1)/n * (x_n - m_(n-1))**2
    # identity (1):   m_n = (n-1)/n * m_(n-1) + x_n / n   (as printed)
    rng = random.Random(3)
    data = [rng.gauss(10, 4) for _ in range(500)]
    m, s = 0.0, 0.0
    for n, x in enumerate(data, start=1):
        s += (n - 1) / n * (x - m) ** 2  # uses the OLD mean m_(n-1)
        m = (n - 1) / n * m + x / n
    result = welford(data)
    assert result.variance == pytest.approx(s / (len(data) - 1), rel=1e-12)
    assert result.mean == pytest.approx(m, rel=1e-12)


def test_corrected_sum_of_squares_equals_its_definition():
    # S = sum((x_i - mean)**2) by definition; variance = S / (n - 1)
    data = [3.5, -2.0, 8.25, 0.0, 4.75, 1.5]
    mean = sum(data) / len(data)
    s_definition = sum((x - mean) ** 2 for x in data)
    assert welford(data).variance == pytest.approx(s_definition / (len(data) - 1))


def test_identity_3_holds_for_each_step():
    # identity (3): x_n - m_n = (n-1)/n * (x_n - m_(n-1)),
    # with m_n the plain mean of the first n values (its definition)
    data = [2.0, 9.0, 4.0, 7.0, 1.0]
    for n in range(2, len(data) + 1):
        m_prev = sum(data[: n - 1]) / (n - 1)
        m_now = sum(data[:n]) / n
        assert data[n - 1] - m_now == pytest.approx((n - 1) / n * (data[n - 1] - m_prev))