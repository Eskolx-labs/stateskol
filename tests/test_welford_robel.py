"""Unit tests for the Welford (1962) implementation."""

import math
import unittest

from stateskol.welford_robel import (
    welford,
    welford_moments,
    welford_products,
)


class TestFormulaI(unittest.TestCase):
    def test_hand_calculated_dataset(self):
        result = welford([10, 20, 30, 40, 50])
        self.assertEqual(result["count"], 5)
        self.assertAlmostEqual(result["mean"], 30.0)
        self.assertAlmostEqual(result["M2"], 1000.0)
        self.assertAlmostEqual(result["sample_variance"], 250.0)
        self.assertAlmostEqual(result["sample_std"], math.sqrt(250.0))

    def test_missing_values_are_dropped_and_counted(self):
        result = welford([10, None, 20, float("nan"), 30])
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["dropped_count"], 2)
        self.assertAlmostEqual(result["mean"], 20.0)
        self.assertAlmostEqual(result["sample_variance"], 100.0)

    def test_empty_input(self):
        result = welford([])
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["mean"])
        self.assertIsNone(result["sample_variance"])
        self.assertIsNone(result["sample_std"])

    def test_single_observation(self):
        result = welford([25])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["mean"], 25.0)
        self.assertIsNone(result["sample_variance"])
        self.assertIsNone(result["sample_std"])

    def test_constant_values(self):
        result = welford([5, 5, 5, 5])
        self.assertAlmostEqual(result["sample_variance"], 0.0)

    def test_rejects_string(self):
        with self.assertRaises(TypeError):
            welford([1, "two", 3])

    def test_rejects_boolean(self):
        with self.assertRaises(TypeError):
            welford([1, True, 3])

    def test_rejects_infinity(self):
        with self.assertRaises(ValueError):
            welford([1, float("inf"), 3])

    def test_rejects_non_iterable(self):
        with self.assertRaises(TypeError):
            welford(42)


class TestFormulaII(unittest.TestCase):
    def test_hand_calculated_corrected_sum_of_products(self):
        result = welford_products([1, 2, 3], [50, 60, 70])
        self.assertEqual(result["paired_count"], 3)
        self.assertAlmostEqual(result["paired_mean_x"], 2.0)
        self.assertAlmostEqual(result["mean_y"], 60.0)
        self.assertAlmostEqual(result["C2"], 20.0)
        self.assertAlmostEqual(result["sample_covariance"], 10.0)

    def test_pairwise_missing_values(self):
        result = welford_products(
            [1, None, 3, 4],
            [10, 20, float("nan"), 40],
        )
        self.assertEqual(result["paired_count"], 2)
        self.assertEqual(result["dropped_pairs"], 2)
        self.assertAlmostEqual(result["C2"], 45.0)

    def test_unequal_lengths_fail(self):
        with self.assertRaises(ValueError):
            welford_products([1, 2], [10])


class TestFormulaIII(unittest.TestCase):
    def test_third_and_fourth_corrected_sums(self):
        result = welford_moments([1, 2, 3], max_order=4)
        self.assertAlmostEqual(result["M2"], 2.0)
        self.assertAlmostEqual(result["higher_order_sums"]["M3"], 0.0)
        self.assertAlmostEqual(result["higher_order_sums"]["M4"], 2.0)

    def test_formula_iii_r2_matches_formula_i(self):
        data = [2, 4, 6, 8, 10]
        formula_i = welford(data)
        formula_iii = welford_moments(data, max_order=4)
        self.assertAlmostEqual(formula_i["M2"], formula_iii["M2"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
