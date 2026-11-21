"""Numerics tests: Welford's update, one pass vs two passes, the 1e9 case,
and the 2**53 boundary (owner: yeabsira).

Standard library and pytest only. Every expected number is worked by hand
or computed EXACTLY with fractions.Fraction, never with the code under test.
Errors are checked by built-in parent class AND class name, so the tests pass
before and after errors.py replaces the temporary copy in descriptive.py.
"""

import math
import random
from fractions import Fraction

import pytest

from stateskol.descriptive import (
    _variance_naive,
    _variance_two_pass,
    _variance_welford,
    _welford_moments,
    _welford_update,
)

EPS = 2.0 ** -52


def exact_variance(values, ddof=1):
    """The true variance as an exact fraction, then rounded once to a float."""
    f = [Fraction(v) for v in values]
    n = len(f)
    mean = sum(f) / n
    return float(sum((v - mean) ** 2 for v in f) / (n - ddof))


def error_name(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except Exception as error:
        return type(error).__name__, isinstance(error, ValueError)
    return None, False


# ------------------------------------------------------------- hand-worked
# 2,4,4,4,5,5,7,9: n=8, sum=40, mean=5; deviations -3,-1,-1,-1,0,0,2,4;
# squares 9+1+1+1+0+0+4+16 = 32; sample variance 32/7; population 32/8 = 4.
def test_hand_worked_moments():
    count, mean, m2 = _welford_moments([2, 4, 4, 4, 5, 5, 7, 9])
    assert count == 8
    assert mean == 5.0
    assert m2 == 32.0


def test_hand_worked_variances():
    data = [2, 4, 4, 4, 5, 5, 7, 9]
    assert _variance_welford(data) == pytest.approx(32 / 7, rel=1e-12)
    assert _variance_welford(data, ddof=0) == 4.0
    assert math.sqrt(_variance_welford(data)) == pytest.approx(math.sqrt(32 / 7), rel=1e-12)


# 1,2,3,4: mean 2.5, S = 2.25+0.25+0.25+2.25 = 5, sample variance 5/3
def test_hand_worked_second_set():
    assert _variance_welford([1, 2, 3, 4]) == pytest.approx(5 / 3, rel=1e-12)
    assert _variance_welford([1, 2, 3, 4], ddof=0) == pytest.approx(1.25, rel=1e-12)


def test_running_state_matches_hand_trace():
    # (mean, S) after each value of 2,4,4,4,5,5,7,9, worked by hand
    expected = [(2.0, 0.0), (3.0, 2.0), (10 / 3, 8 / 3), (3.5, 3.0),
                (3.8, 4.8), (4.0, 6.0), (31 / 7, 96 / 7), (5.0, 32.0)]
    count, mean, m2 = 0, 0.0, 0.0
    for x, (m, s) in zip([2, 4, 4, 4, 5, 5, 7, 9], expected):
        count, mean, m2 = _welford_update(count, mean, m2, float(x))
        assert mean == pytest.approx(m, rel=1e-12)
        assert m2 == pytest.approx(s, rel=1e-12, abs=1e-15)


def test_update_first_two_values():
    assert _welford_update(0, 0.0, 0.0, 5.0) == (1, 5.0, 0.0)
    assert _welford_update(1, 5.0, 0.0, 7.0) == (2, 6.0, 2.0)


# the paper's own form, written out: S(n) = S(n-1) + ((n-1)/n) * (x - m(n-1))**2
def test_update_equals_the_paper_formula():
    r = random.Random(3)
    count, mean, m2 = 0, 0.0, 0.0
    for _ in range(200):
        x = r.uniform(-50, 50)
        n = count + 1
        paper_mean = ((n - 1) / n) * mean + x / n
        paper_m2 = m2 + ((n - 1) / n) * (x - mean) ** 2
        count, mean, m2 = _welford_update(count, mean, m2, x)
        assert mean == pytest.approx(paper_mean, rel=1e-12, abs=1e-12)
        assert m2 == pytest.approx(paper_m2, rel=1e-12, abs=1e-12)


# ---------------------------------------------------- THE 1e9 CASE (the brief)
# x = 1e9+1 .. 1e9+4. Deviations from the mean 1e9+2.5 are -1.5,-0.5,0.5,1.5,
# squares 2.25+0.25+0.25+2.25 = 5, sample variance 5/3 = 1.6666...
BIG = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]


def test_big_case_the_three_numbers():
    naive = _variance_naive(BIG)
    two_pass = _variance_two_pass(BIG)
    welford = _variance_welford(BIG)
    assert naive == 0.0                                   # the spread disappears
    assert two_pass == pytest.approx(5 / 3, rel=1e-12)    # two scans
    assert welford == pytest.approx(5 / 3, rel=1e-12)     # one scan


def test_big_case_naive_is_wrong_by_everything():
    assert abs(_variance_naive(BIG) - 5 / 3) > 1.0


def test_big_case_matches_exact_arithmetic():
    assert _variance_welford(BIG) == exact_variance(BIG)


def test_big_case_population_version():
    assert _variance_welford(BIG, ddof=0) == pytest.approx(1.25, rel=1e-12)
    assert _variance_naive(BIG, ddof=0) == 0.0


@pytest.mark.parametrize("offset", [1e3, 1e6, 1e9, 1e12, 1e15])
def test_same_spread_at_every_offset(offset):
    # the spread of 1,2,3,4 does not depend on where the numbers sit
    data = [offset + 1, offset + 2, offset + 3, offset + 4]
    assert _variance_welford(data) == pytest.approx(5 / 3, rel=1e-12)


def test_float_spacing_explains_the_failure():
    # near 1e18 (the size of the squares) neighbouring floats are 128 apart,
    # so a variance of 1.67 cannot survive a subtraction at that size
    assert math.ulp(1e18) == 128.0
    assert (1e9 + 1) ** 2 > 2 ** 53


# ---------------------------------------------------- the 2**53 boundary
# Week 2 refuses abs(x) > 2**53 because above it the integer is not exact.
def test_2_53_plus_1_is_not_a_float():
    assert float(2 ** 53 + 1) == float(2 ** 53)           # it rounds to 2**53
    assert float(2 ** 53 - 1) != float(2 ** 53)           # below, still exact


def test_welford_at_the_2_53_edge():
    top = float(2 ** 53)
    data = [top - 3, top - 2, top - 1, top]               # all exact floats
    assert _variance_welford(data) == pytest.approx(5 / 3, rel=1e-12)
    assert _variance_welford(data) == exact_variance(data)


def test_two_pass_loses_the_answer_at_the_2_53_edge():
    # the sum of the four values is above 2**53, so the mean is not exact
    top = float(2 ** 53)
    data = [top - 3, top - 2, top - 1, top]
    assert abs(_variance_two_pass(data) - 5 / 3) > 0.1


def test_extreme_values_either_side_of_zero():
    top = float(2 ** 53)
    assert _variance_welford([-top, top]) == exact_variance([-top, top])


# ------------------------------------------------------------ usual cases
def test_negative_and_float_values():
    assert _variance_welford([-1.5, 0.0, 1.5]) == pytest.approx(2.25, rel=1e-12)


def test_order_does_not_matter():
    a = _variance_welford([9, 2, 5, 4, 7, 4, 5, 4])
    b = _variance_welford([2, 4, 4, 4, 5, 5, 7, 9])
    assert a == pytest.approx(b, rel=1e-12)


def test_accepts_tuple_and_generator():
    assert _variance_welford((1, 2, 3)) == pytest.approx(1.0)
    assert _variance_welford(x for x in [1, 2, 3]) == pytest.approx(1.0)


def test_welford_reads_each_value_once():
    reads = []

    def numbers():
        for x in [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]:
            reads.append(x)
            yield x

    assert _variance_welford(numbers()) == pytest.approx(32 / 7, rel=1e-12)
    assert len(reads) == 8                                # one pass


def test_input_list_is_not_changed():
    data = [3.0, 1.0, 2.0]
    _variance_welford(data)
    _variance_two_pass(data)
    assert data == [3.0, 1.0, 2.0]


# --------------------------------------------------------- outlier case
# 1 2 2 3 4 4 5 6 7 has mean 34/9 = 3.78; adding 48 moves the mean to 8.20.
def test_outlier_moves_the_mean_and_explodes_the_variance():
    base = [1, 2, 2, 3, 4, 4, 5, 6, 7]
    plus = base + [48]
    c1, m1, _ = _welford_moments(base)
    c2, m2_mean, _ = _welford_moments(plus)
    assert m1 == pytest.approx(34 / 9, rel=1e-12)
    assert m2_mean == pytest.approx(8.2, rel=1e-12)
    assert _variance_welford(plus) > 50 * _variance_welford(base)
    assert _variance_welford(plus) == exact_variance(plus)


# ------------------------------------------------------- boundary pack
def test_constant_values_give_exact_zero():
    assert _variance_welford([3.7] * 1000) == 0.0
    assert _variance_welford([1e9 + 0.1] * 1000) == 0.0
    assert _variance_welford([5, 5]) == 0.0


def test_single_value_population_variance_is_zero():
    assert _variance_welford([42], ddof=0) == 0.0


def test_single_value_sample_variance_does_not_exist():
    assert error_name(_variance_welford, [42]) == ("DomainError", True)


def test_empty():
    assert error_name(_variance_welford, []) == ("EmptyDataError", True)
    assert error_name(_variance_welford, [], ddof=0) == ("EmptyDataError", True)
    assert _welford_moments([]) == (0, 0.0, 0.0)


@pytest.mark.parametrize("bad", [2, -1, 0.5, True, False, "1", None])
def test_ddof_must_be_zero_or_one(bad):
    assert error_name(_variance_welford, [1, 2, 3], ddof=bad) == ("DomainError", True)


def test_two_values_is_the_smallest_sample_variance():
    assert _variance_welford([1, 3]) == 2.0               # S = 2, n - 1 = 1


def test_two_pass_and_naive_reject_the_same_inputs():
    for function in (_variance_two_pass, _variance_naive):
        assert error_name(function, []) == ("EmptyDataError", True)
        assert error_name(function, [1.0]) == ("DomainError", True)
        assert error_name(function, [1, 2], ddof=2) == ("DomainError", True)


# --------------------------------------------------- properties, random data
def test_m2_is_never_negative_and_matches_exact_variance():
    r = random.Random(11)
    for _ in range(200):
        n = r.randint(2, 200)
        centre = r.choice([0.0, 1e3, 1e6, 1e9])
        data = [centre + r.gauss(0, r.choice([1e-3, 1, 100])) for _ in range(n)]
        _, _, m2 = _welford_moments(data)
        assert m2 >= 0.0
        # the tolerance rule from the note: relative error <= n * EPS * kappa,
        # kappa = sqrt(sum(x*x) / S), computed with exact fractions
        f = [Fraction(v) for v in data]
        true_s = sum((v - sum(f) / n) ** 2 for v in f)
        if true_s == 0:
            continue
        kappa = math.sqrt(float(sum(v * v for v in f) / true_s))
        bound = n * EPS * kappa
        if bound >= 1e-3:                                 # data too ill-conditioned
            continue
        true_var = float(true_s / (n - 1))
        assert abs(_variance_welford(data) - true_var) <= bound * true_var


def test_welford_and_two_pass_agree_when_the_data_is_well_behaved():
    r = random.Random(21)
    for _ in range(300):
        data = [r.gauss(5, 2) for _ in range(r.randint(2, 300))]
        assert _variance_welford(data) == pytest.approx(_variance_two_pass(data), rel=1e-11)


# ------------------------------------------------ Ross, section 2.3.2 and Problem 18
# Ross: adding a constant to every value does not change the sample variance;
# multiplying every value by b multiplies it by b**2.
def test_ross_shift_does_not_change_the_variance():
    # In exact arithmetic the shift changes nothing. In floats the digits
    # that survive shrink as the shift grows past the spread, by the rule
    # relative error <= n * EPS * kappa from the note (kappa = sqrt(sum(x*x)/S)).
    base = [3, 4, 7, 2, 9, 6]
    for shift in (1, 1e3, 1e6, 1e9, 1e12):
        shifted = [v + shift for v in base]
        f = [Fraction(v) for v in shifted]
        mean = sum(f) / len(f)
        s_exact = sum((v - mean) ** 2 for v in f)
        kappa = math.sqrt(float(sum(v * v for v in f) / s_exact))
        bound = max(1e-12, len(base) * EPS * kappa)
        assert _variance_welford(shifted) == pytest.approx(
            _variance_welford(base), rel=bound)


def test_ross_scale_multiplies_the_variance_by_b_squared():
    base = [3, 4, 7, 2, 9, 6]
    assert _variance_welford([5 * v for v in base]) == pytest.approx(
        25 * _variance_welford(base), rel=1e-12)
    assert _variance_welford([-2 * v for v in base]) == pytest.approx(
        4 * _variance_welford(base), rel=1e-12)


# Ross Chapter 2, Problem 18: data 3, 4, 7, 2, 9, 6, with the book's recursion
#   mean(j+1) = mean(j) + (x(j+1) - mean(j)) / (j + 1)
#   s2(j+1)   = (1 - 1/j) * s2(j) + (j + 1) * (mean(j+1) - mean(j))**2,  s2(1) = 0
# By hand: sum 31, sum of squares 195, S = 195 - 31**2/6 = 34.8333, s2 = S/5.
def test_ross_problem_18_recursion_agrees_with_welford():
    data = [3, 4, 7, 2, 9, 6]
    mean, s2 = float(data[0]), 0.0
    for j in range(1, len(data)):                    # j values seen so far
        new_mean = mean + (data[j] - mean) / (j + 1)
        s2 = (1 - 1 / j) * s2 + (j + 1) * (new_mean - mean) ** 2
        mean = new_mean
    assert mean == pytest.approx(31 / 6, rel=1e-12)
    assert s2 == pytest.approx(209 / 30, rel=1e-12)          # 34.8333/5 = 6.9667
    assert _variance_welford(data) == pytest.approx(s2, rel=1e-12)
    count, wmean, _ = _welford_moments(data)
    assert wmean == pytest.approx(mean, rel=1e-12)