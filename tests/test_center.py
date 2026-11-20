"""Tests for mean, median and mode (Core A, week 3).

Every hand-worked number is worked out in the docstring of its test first.
"""

import math
import statistics
import unittest

from stateskol.descriptive import mean, median, mode
from stateskol.errors import ContractError, EmptyDataError, UnknownPolicyError

NAN = float("nan")
SAMPLE = [1, 2, 2, 3, 4, 4, 5, 6, 7]
WITH_OUTLIER = SAMPLE + [48]


class HandWorked(unittest.TestCase):
    def test_small_sample(self):
        """2 4 4 4 5 5 7 9: sum 40, n 8, mean 5. Sorted middle pair 4 and 5, median 4.5. 4 occurs three times."""
        data = [2, 4, 4, 4, 5, 5, 7, 9]
        self.assertEqual(mean(data), 5.0)
        self.assertEqual(median(data), 4.5)
        self.assertEqual(mode(data), [4.0])

    def test_sunday_sample(self):
        """1 2 2 3 4 4 5 6 7: sum 34, n 9, mean 34/9 = 3.777... Middle (5th) value 4. 2 and 4 tie at two each."""
        self.assertEqual(mean(SAMPLE), 34 / 9)
        self.assertEqual(median(SAMPLE), 4.0)
        self.assertEqual(mode(SAMPLE), [2.0, 4.0])

    def test_one_outlier_moves_the_mean_not_the_median(self):
        """Add 48: sum 82, n 10, mean 8.2. Sorted 5th and 6th values are both 4, so the median stays 4.0."""
        self.assertAlmostEqual(mean(SAMPLE), 3.78, places=2)
        self.assertEqual(mean(WITH_OUTLIER), 8.2)
        self.assertEqual(median(WITH_OUTLIER), 4.0)
        self.assertEqual(median(WITH_OUTLIER), median(SAMPLE))


class EvenAndOdd(unittest.TestCase):
    def test_odd_length_takes_the_middle_value(self):
        self.assertEqual(median([9, 1, 5]), 5.0)

    def test_even_length_averages_the_two_middle_values(self):
        # type 7 at p = 0.5: h = (4 - 1) * 0.5 + 1 = 2.5, halfway between the 2nd and 3rd
        self.assertEqual(median([4, 1, 3, 2]), 2.5)

    def test_input_order_does_not_matter(self):
        self.assertEqual(median([3, 1, 2, 5, 4]), median([1, 2, 3, 4, 5]))

    def test_median_does_not_sort_the_callers_list(self):
        data = [3, 1, 2]
        median(data)
        self.assertEqual(data, [3, 1, 2])


class Ties(unittest.TestCase):
    def test_every_tied_mode_is_returned_in_order(self):
        self.assertEqual(mode([5, 1, 5, 1, 3]), [1.0, 5.0])

    def test_all_unique_means_every_value_is_a_mode(self):
        self.assertEqual(mode([3, 1, 2]), [1.0, 2.0, 3.0])

    def test_int_and_float_of_the_same_value_count_together(self):
        self.assertEqual(mode([2, 2.0, 3]), [2.0])

    def test_negative_zero_counts_as_zero(self):
        self.assertEqual(mode([0.0, -0.0, 1]), [0.0])

    def test_tied_middle_values_for_median(self):
        self.assertEqual(median([1, 2, 2, 2, 3]), 2.0)


class Boundaries(unittest.TestCase):
    def test_empty_input_raises(self):
        for f in (mean, median, mode):
            with self.subTest(f=f.__name__), self.assertRaises(EmptyDataError):
                f([])

    def test_all_missing_raises(self):
        # the policy ran and left nothing, so there is no summary to report
        for f in (mean, median, mode):
            with self.subTest(f=f.__name__), self.assertRaises(EmptyDataError):
                f([None, NAN])

    def test_single_value(self):
        self.assertEqual(mean([7]), 7.0)
        self.assertEqual(median([7]), 7.0)
        self.assertEqual(mode([7]), [7.0])

    def test_constant_values(self):
        data = [3.5] * 6
        self.assertEqual(mean(data), 3.5)
        self.assertEqual(median(data), 3.5)
        self.assertEqual(mode(data), [3.5])

    def test_negative_values(self):
        self.assertEqual(mean([-3, -1, 1]), -1.0)
        self.assertEqual(median([-3, -1, 1, 7]), 0.0)


class InheritsTheContract(unittest.TestCase):
    def test_missing_values_are_dropped_in_any_position(self):
        for data in ([NAN, 1, 2, 3], [1, None, 2, 3], [1, 2, 3, NAN]):
            with self.subTest(data=data):
                self.assertEqual(mean(data), 2.0)
                self.assertEqual(median(data), 2.0)

    def test_nan_is_never_a_mode(self):
        self.assertEqual(mode([NAN, NAN, NAN, 1]), [1.0])

    def test_strict_refuses_missing(self):
        for f in (mean, median, mode):
            with self.subTest(f=f.__name__), self.assertRaises(ContractError):
                f([1, None, 3], policy="strict")

    def test_refused_values_raise_before_any_summary(self):
        for bad in (True, "3", float("inf"), 2**53 + 1):
            with self.subTest(bad=bad), self.assertRaises(ContractError):
                mean([1, bad, 3])

    def test_unknown_policy(self):
        with self.assertRaises(UnknownPolicyError):
            median([1, 2], policy="impute")

    def test_generator_is_read_once(self):
        self.assertEqual(mean(x for x in [1, 2, 3]), 2.0)
        self.assertEqual(mode(x for x in [1, 1, 2]), [1.0])


class Numerics(unittest.TestCase):
    def test_mean_of_large_values_does_not_overflow(self):
        # 1e308 + 1e308 is inf, but the mean of two equal values is that value
        self.assertEqual(mean([1e308, 1e308]), 1e308)
        self.assertTrue(math.isinf(1e308 + 1e308))

    def test_median_of_large_values_does_not_overflow(self):
        self.assertEqual(median([1e308, 1.5e308]), 1.25e308)

    def test_fsum_keeps_small_values_next_to_large_ones(self):
        # a plain running total loses the 1.0: 1e16 + 1.0 rounds back to 1e16
        data = [1e16, 1.0, -1e16]
        total = 0.0
        for v in data:
            total += v
        self.assertEqual(total, 0.0)
        self.assertEqual(mean(data), 1 / 3)


class AgainstReferences(unittest.TestCase):
    def test_statistics_module(self):
        for data in (SAMPLE, WITH_OUTLIER, [2, 4, 4, 4, 5, 5, 7, 9], [0.1, 0.2, 0.3]):
            with self.subTest(data=data):
                self.assertAlmostEqual(mean(data), statistics.fmean(data), places=12)
                self.assertEqual(median(data), statistics.median(data))
                self.assertEqual(mode(data), sorted(float(v) for v in statistics.multimode(data)))

    def test_numpy_if_installed(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("numpy not installed, the package itself does not need it")
        for data in (SAMPLE, WITH_OUTLIER, [4, 1, 3, 2], [-3.5, 2.25, 9.0]):
            with self.subTest(data=data):
                self.assertTrue(math.isclose(mean(data), float(np.mean(data)), rel_tol=1e-12))
                self.assertEqual(median(data), float(np.median(data)))


if __name__ == "__main__":
    unittest.main()
