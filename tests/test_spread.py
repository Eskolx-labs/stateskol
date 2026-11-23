"""Tests for the week 3 spread summaries.

Every test names the rule it defends. The hand-worked values are computed in
the comments, so a reviewer can check the arithmetic with a pencil instead of
checking it against numpy. Standard library only.

    python -m pytest tests/test_spread.py -q
"""

import doctest
import math
import unittest

import stateskol.descriptive as descriptive
from stateskol.descriptive import (
    ASSUMPTION,
    coefficient_variation,
    iqr,
    quantile,
    stdev,
    variance,
)
from stateskol.errors import (
    ContractError,
    DomainError,
    EmptyDataError,
    UnsupportedRuleError,
)

NAN = float("nan")


class OneShot:
    """An iterable that fails loudly if it is iterated twice.

    Duplicated from test_contract.py on purpose: tests/ has no __init__.py, so
    importing across test modules depends on how pytest was launched, and a
    test that cannot be imported protects nothing.
    """

    def __init__(self, values):
        self._values = tuple(values)
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("the input was consumed more than once")
        return iter(self._values)


# The brief's ten values, already sorted, with mean 88 / 10 = 8.8.
TEN = [2, 4, 4, 5, 7, 9, 11, 13, 15, 18]

# Sum of squared deviations from 8.8, worked by hand:
# 46.24 + 23.04 + 23.04 + 14.44 + 3.24 + 0.04 + 4.84 + 17.64 + 38.44 + 84.64
M2_TEN = 255.6
VARIANCE_TEN = M2_TEN / 9          # 28.4, the sample variance
DDOF0_TEN = M2_TEN / 10            # 25.56, the population variance

# The brief's demonstration sample, used across the week so the numbers line up.
DEMO = [4, 8, 15, 16, 23, 42]


class HandWorked(unittest.TestCase):
    """A relative comparison, because Welford and the two-pass sum differ last-bit."""

    def assertClose(self, got, want, rel=1e-12):
        scale = abs(want) if want else 1.0
        self.assertLessEqual(
            abs(got - want) / scale,
            rel,
            "got {!r}, hand-worked {!r}, relative diff too large".format(got, want),
        )


class TestQuantileIsTypeSeven(HandWorked):
    def test_the_brief_own_p25_of_five_values(self):
        # h = (5 - 1) * 0.25 + 1 = 2, 1-indexed, so the answer is the 2nd value.
        self.assertEqual(quantile([1, 2, 3, 4, 5], 0.25), 2.0)

    def test_the_brief_own_p75_of_ten_values(self):
        # h = (10 - 1) * 0.75 + 1 = 7.75, so 3/4 of the way from the 7th value
        # (11) to the 8th (13): 11 + 0.75 * 2 = 12.5.
        self.assertEqual(quantile(TEN, 0.75), 12.5)

    def test_type_six_would_have_said_13_5_and_this_build_refuses_it(self):
        # The gap the note must show: 13.5 under type 6, 12.5 under type 7.
        # Refusing is the point, so the refusal has to name the rule.
        with self.assertRaises(UnsupportedRuleError) as caught:
            quantile(TEN, 0.75, method="type6")
        self.assertIn("type6", str(caught.exception))
        self.assertIn("type 7", str(caught.exception))

    def test_p_zero_is_the_minimum_and_p_one_the_maximum(self):
        self.assertEqual(quantile(DEMO, 0.0), 4.0)
        self.assertEqual(quantile(DEMO, 1.0), 42.0)

    def test_quartiles_of_the_demo_sample(self):
        # 9.75 = 8 + 0.25 * (15 - 8); 15.5 = (15 + 16) / 2; 21.25 = 16 + 0.25 * (23 - 16).
        self.assertEqual(quantile(DEMO, 0.25), 9.75)
        self.assertEqual(quantile(DEMO, 0.50), 15.5)
        self.assertEqual(quantile(DEMO, 0.75), 21.25)

    def test_median_of_an_even_length_sample_averages_the_middle_pair(self):
        # The brief: type 7 keeps this property, which is one reason it shipped.
        self.assertEqual(quantile([1, 2, 3, 4], 0.5), 2.5)

    def test_median_of_an_odd_length_sample_is_a_real_value(self):
        self.assertEqual(quantile([1, 2, 3], 0.5), 2.0)

    def test_interpolation_between_two_neighbours(self):
        # h = (2 - 1) * 0.25 = 0.25 across a gap of 10, so 2.5.
        self.assertEqual(quantile([0, 10], 0.25), 2.5)

    def test_ties_collapse_to_the_tied_value(self):
        self.assertEqual(quantile([5, 5, 5, 5], 0.3), 5.0)

    def test_a_single_value_is_its_own_quantile_at_every_p(self):
        for p in (0.0, 0.25, 0.5, 0.99, 1.0):
            self.assertEqual(quantile([7], p), 7.0)

    def test_input_order_does_not_matter(self):
        self.assertEqual(quantile([15, 2, 18, 4, 7, 9, 11, 5, 13, 10], 0.75),
                         quantile([10, 13, 11, 9, 7, 5, 4, 2, 18, 15], 0.75))

    def test_the_input_list_is_not_reordered(self):
        data = [3, 1, 2]
        quantile(data, 0.5)
        self.assertEqual(data, [3, 1, 2])


class TestQuantileRefuses(unittest.TestCase):
    def test_p_above_one_is_a_domain_error_not_clamped(self):
        with self.assertRaises(DomainError):
            quantile(TEN, 1.5)

    def test_p_below_zero_is_a_domain_error(self):
        with self.assertRaises(DomainError):
            quantile(TEN, -0.001)

    def test_p_is_never_coerced_from_a_string(self):
        with self.assertRaises(DomainError):
            quantile(TEN, "0.5")

    def test_bool_p_is_refused_before_it_becomes_zero_or_one(self):
        # True would otherwise read as p = 1 and return the maximum silently.
        with self.assertRaises(DomainError):
            quantile(TEN, True)

    def test_nan_and_inf_p_are_domain_errors(self):
        for bad in (NAN, float("inf"), float("-inf")):
            with self.assertRaises(DomainError):
                quantile(TEN, bad)

    def test_any_other_method_is_refused_and_names_itself(self):
        for method in ("type1", "type8", "hazen", "lower", None, 7):
            with self.assertRaises(UnsupportedRuleError) as caught:
                quantile(TEN, 0.5, method=method)
            self.assertIn("not implemented", str(caught.exception))

    def test_the_method_is_checked_before_the_input_is_read(self):
        # A generator cannot be un-consumed. A refused rule must leave it whole.
        source = OneShot(TEN)
        with self.assertRaises(UnsupportedRuleError):
            quantile(source, 0.5, method="type6")
        self.assertEqual(source.iterations, 0)

    def test_p_is_checked_before_the_input_is_read(self):
        source = OneShot(TEN)
        with self.assertRaises(DomainError):
            quantile(source, 2.0)
        self.assertEqual(source.iterations, 0)

    def test_empty_input_raises_rather_than_returning_zero(self):
        with self.assertRaises(EmptyDataError):
            quantile([], 0.5)

    def test_all_missing_input_raises_too(self):
        with self.assertRaises(EmptyDataError):
            quantile([None, NAN, None], 0.5)


class TestIqr(HandWorked):
    def test_hand_worked_iqr_of_the_brief_sample(self):
        # Q3 12.5 minus Q1 4.25 (4 + 0.25 * (5 - 4)) = 8.25.
        self.assertEqual(iqr(TEN), 8.25)

    def test_hand_worked_iqr_of_the_demo_sample(self):
        self.assertEqual(iqr(DEMO), 11.5)

    def test_iqr_is_the_difference_of_its_own_quartiles(self):
        self.assertEqual(iqr(TEN), quantile(TEN, 0.75) - quantile(TEN, 0.25))

    def test_a_constant_sample_has_no_spread(self):
        self.assertEqual(iqr([5, 5, 5, 5]), 0.0)

    def test_one_value_has_no_spread(self):
        self.assertEqual(iqr([9]), 0.0)

    def test_iqr_refuses_another_rule_before_reading_the_data(self):
        source = OneShot(TEN)
        with self.assertRaises(UnsupportedRuleError):
            iqr(source, method="type8")
        self.assertEqual(source.iterations, 0)

    def test_iqr_of_empty_input_raises(self):
        with self.assertRaises(EmptyDataError):
            iqr([])


class TestVarianceAndStdev(HandWorked):
    def test_sample_variance_matches_the_hand_sum(self):
        self.assertClose(variance(TEN), VARIANCE_TEN)

    def test_ddof_zero_gives_the_population_divisor(self):
        self.assertClose(variance(TEN, ddof=0), DDOF0_TEN)

    def test_the_default_is_the_sample_variance(self):
        self.assertEqual(variance(TEN), variance(TEN, ddof=1))

    def test_the_1e9_case_the_brief_requires(self):
        data = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
        # Deviations from 1e9 + 2.5 are -1.5, -0.5, 0.5, 1.5, so m2 = 5 and
        # the sample variance is 5 / 3 = 1.6666666666666667.
        self.assertAlmostEqual(variance(data), 5 / 3, places=12)

    def test_the_naive_formula_loses_the_spread_entirely(self):
        # The reason Welford shipped: sum(x*x)/n - mean**2 cancles 18 digits
        # of scale away and reports no spread at all for data that has some.
        data = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
        mean = sum(data) / len(data)
        naive = sum(x * x for x in data) / len(data) - mean * mean
        self.assertEqual(naive, 0.0)

    def test_a_constant_sample_has_zero_variance_exactly(self):
        self.assertEqual(variance([5, 5, 5]), 0.0)
        self.assertEqual(stdev([5, 5, 5]), 0.0)

    def test_one_value_cannot_support_ddof_one(self):
        # n - ddof would be 0. This is an empty sample for this statistic, not
        # a division the package is willing to fake.
        with self.assertRaises(EmptyDataError):
            variance([7])
        with self.assertRaises(EmptyDataError):
            stdev([7])

    def test_one_value_under_ddof_zero_is_zero_spread(self):
        self.assertEqual(variance([7], ddof=0), 0.0)

    def test_ddof_outside_the_defined_pair_is_a_domain_error(self):
        for bad in (2, -1, 0.5, "1", True):
            with self.assertRaises(DomainError):
                variance(TEN, ddof=bad)

    def test_ddof_is_checked_before_the_input_is_read(self):
        source = OneShot(TEN)
        with self.assertRaises(DomainError):
            variance(source, ddof=2)
        self.assertEqual(source.iterations, 0)

    def test_stdev_is_the_sqrt_of_variance(self):
        self.assertEqual(stdev(TEN), math.sqrt(variance(TEN)))

    def test_stdev_of_the_demo_sample(self):
        # sqrt(182.0), the hand-worked sample variance of the demo data.
        self.assertClose(stdev(DEMO), math.sqrt(182.0))

    def test_spread_scales_linearly_when_the_data_does(self):
        self.assertClose(stdev([2 * x for x in TEN]), 2 * stdev(TEN))

    def test_shifting_every_value_leaves_the_spread_alone(self):
        self.assertClose(stdev([x + 1000 for x in TEN]), stdev(TEN))

    def test_variance_and_stdev_raise_on_empty_and_all_missing(self):
        for fn in (variance, stdev):
            with self.assertRaises(EmptyDataError):
                fn([])
            with self.assertRaises(EmptyDataError):
                fn([None, NAN])

    def test_the_contract_still_refuses_bad_measurements(self):
        with self.assertRaises(ContractError):
            variance([4, "8", 15])


class TestCoefficientOfVariation(HandWorked):
    def test_hand_worked_value_on_the_demo_sample(self):
        self.assertClose(coefficient_variation(DEMO), math.sqrt(182.0) / 18.0)

    def test_a_constant_sample_has_no_relative_spread(self):
        self.assertEqual(coefficient_variation([5, 5, 5]), 0.0)

    def test_a_zero_mean_is_refused_not_reported_as_infinite(self):
        with self.assertRaises(DomainError) as caught:
            coefficient_variation([1, -1])
        self.assertIn("mean is 0", str(caught.exception))

    def test_a_negative_mean_is_allowed_and_the_ratio_goes_negative(self):
        # Documented limitation, not a bug: CV means nothing on a scale whose
        # zero is arbitrary. The refusal is only for a mean of exactly 0.
        self.assertLess(coefficient_variation([-2.0, -4.0]), 0.0)

    def test_one_value_leaves_no_divisor(self):
        with self.assertRaises(EmptyDataError):
            coefficient_variation([7])

    def test_it_drops_missing_values_before_both_halves(self):
        # The mean and the spread must be computed from one sample, so the
        # dropped rows cannot inflate the ratio by affecting only one of them.
        self.assertEqual(
            coefficient_variation([4, None, 8, 15, NAN, 16, 23, 42]),
            coefficient_variation(DEMO),
        )

    def test_a_generator_is_consumed_once(self):
        coefficient_variation(OneShot(DEMO))


class TestOnePassPerSummary(unittest.TestCase):
    def test_each_summary_reads_its_input_exactly_once(self):
        for fn in (quantile, iqr, variance, stdev, coefficient_variation):
            source = OneShot(DEMO)
            if fn is quantile:
                fn(source, 0.5)
            else:
                fn(source)
            self.assertEqual(source.iterations, 1, fn.__name__)


class TestDocstringShape(unittest.TestCase):
    """Week 3 point 1: the rule, the divisor, the algorithm and the assumption."""

    SPREAD = (quantile, iqr, variance, stdev, coefficient_variation)

    def test_every_summary_states_the_missingness_assumption(self):
        for fn in self.SPREAD:
            self.assertIsNotNone(fn.__doc__, fn.__name__)
            self.assertIn(ASSUMPTION, fn.__doc__, fn.__name__)

    def test_the_quantile_functions_name_the_type_by_number(self):
        for fn in (quantile, iqr):
            self.assertIn("type 7", fn.__doc__)
            self.assertIn("Hyndman & Fan (1996)", fn.__doc__)

    def test_variance_and_stdev_state_the_divisor_and_the_algorithm(self):
        for fn in (variance, stdev):
            self.assertIn("ddof", fn.__doc__)
            self.assertIn("Welford", fn.__doc__)

    def test_every_summary_lists_the_errors_it_raises(self):
        for fn in self.SPREAD:
            self.assertIn("Errors:", fn.__doc__, fn.__name__)
            self.assertIn("Example:", fn.__doc__, fn.__name__)

    def test_the_docstring_shape_constant_is_importable(self):
        self.assertIn("Assumptions:", descriptive.DOCSTRING_SHAPE)


class TestThePackageStillImportsNothingExtra(unittest.TestCase):
    def test_no_reference_library_in_the_package_or_these_tests(self):
        # The bar is a clean environment: numpy and pandas are the reference,
        # never the method.
        import sys

        loaded = [name for name in ("numpy", "pandas") if name in sys.modules]
        self.assertEqual(loaded, [])

    def test_the_docstrings_run(self):
        results = doctest.testmod(descriptive)
        self.assertEqual(results.failed, 0)


if __name__ == "__main__":
    unittest.main()
