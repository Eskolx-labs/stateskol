"""Standard-library tests for input validation, quantiles, and IQR."""

import math
import sys
import unittest
from decimal import Decimal
from fractions import Fraction

from stateskol.descriptive import PreparedData, StatisticResult, iqr, prepare_data, quantile


class TestInputContract(unittest.TestCase):
    def test_accepts_lists_and_tuples(self):
        for data in ([0, -2, 4.5, 4.5], (0, -2, 4.5, 4.5)):
            with self.subTest(data=data):
                result = prepare_data(data)
                self.assertIsInstance(result, PreparedData)
                self.assertEqual(result.values, (0, -2, 4.5, 4.5))
                self.assertEqual(result.dropped_count, 0)
                self.assertIs(type(result.values[0]), int)
                self.assertIs(type(result.values[2]), float)

    def test_drops_none_and_nan_and_preserves_order(self):
        data = [6, None, 2, float("nan"), 4, None]
        result = prepare_data(data)
        self.assertEqual(result.values, (6, 2, 4))
        self.assertEqual(result.dropped_count, 3)
        self.assertEqual(len(result.values) + result.dropped_count, len(data))

    def test_does_not_modify_input(self):
        data = [8, None, 2, 4]
        original = data.copy()
        result = prepare_data(data)
        self.assertEqual(data, original)
        data.append(6)
        self.assertEqual(result.values, (8, 2, 4))
        self.assertIsInstance(result.values, tuple)

    def test_preserves_large_integers_and_finite_float_limits(self):
        large_integer = 10**400
        smallest_float = float.fromhex("0x0.0000000000001p-1022")
        data = [large_integer, -large_integer, sys.float_info.max, smallest_float]
        result = prepare_data(data)
        self.assertEqual(result.values, tuple(data))
        self.assertIs(type(result.values[0]), int)

    def test_rejects_unsupported_collections(self):
        for data in (None, 5, 4.5, "123", b"123", {1, 2}, {"value": 2}, iter([2])):
            with self.subTest(data=data):
                with self.assertRaisesRegex(TypeError, "list or tuple"):
                    prepare_data(data)

    def test_rejects_invalid_observations_at_original_index(self):
        invalid_values = (
            "4",
            "NaN",
            True,
            False,
            3 + 4j,
            [4],
            (4,),
            {"value": 4},
            Decimal("4"),
            Fraction(1, 2),
            object(),
        )
        for invalid in invalid_values:
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(TypeError, "index 2"):
                    prepare_data([None, 2, invalid, 6])

    def test_rejects_numeric_subclasses(self):
        class CustomInteger(int):
            pass

        class CustomFloat(float):
            pass

        for value in (CustomInteger(2), CustomFloat(2), CustomFloat("nan")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(TypeError, "index 0"):
                    prepare_data([value])

    def test_rejects_infinity(self):
        for value in (float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "index 2.*infinity"):
                    prepare_data([None, 2, value])

    def test_rejects_empty_and_all_missing_data(self):
        for data in ([], (), [None], [float("nan")], [None, float("nan")]):
            with self.subTest(data=data):
                with self.assertRaisesRegex(
                    ValueError, f"At least 1.*got 0 after dropping {len(data)}"
                ):
                    prepare_data(data)

    def test_checks_minimum_after_dropping(self):
        self.assertEqual(prepare_data([5, None]), PreparedData((5,), 1))
        with self.assertRaisesRegex(ValueError, "At least 2.*got 1 after dropping 2"):
            prepare_data([5, None, float("nan")], min_count=2)
        self.assertEqual(
            prepare_data([5, None, 5], min_count=2), PreparedData((5, 5), 1)
        )

    def test_rejects_invalid_minimum_type(self):
        for minimum in (True, False, 2.0, "2", None):
            with self.subTest(minimum=minimum):
                with self.assertRaisesRegex(TypeError, "min_count"):
                    prepare_data([2, 4], min_count=minimum)

    def test_rejects_nonpositive_minimum(self):
        for minimum in (0, -1):
            with self.subTest(minimum=minimum):
                with self.assertRaisesRegex(ValueError, "min_count"):
                    prepare_data([2, 4], min_count=minimum)

    def test_checks_entire_collection_before_returning(self):
        data = [2, 4, "invalid"]
        with self.assertRaisesRegex(TypeError, "index 2"):
            prepare_data(data, min_count=2)
        self.assertEqual(data, [2, 4, "invalid"])


class TestQuantile(unittest.TestCase):
    def test_ross_quartiles_and_noninteger_position(self):
        for probability, expected in ((0.25, 3), (0.5, 5), (0.75, 7), (0.6, 6)):
            with self.subTest(probability=probability):
                self.assertEqual(
                    quantile([2, 4, 6, 8], probability), StatisticResult(expected, 0)
                )

    def test_endpoints_and_adjacent_probabilities(self):
        for probability, expected in (
            (0, 2),
            (1, 8),
            (math.nextafter(0.0, 1.0), 2),
            (math.nextafter(1.0, 0.0), 8),
            (math.nextafter(0.5, 0.0), 4),
            (math.nextafter(0.5, 1.0), 6),
        ):
            with self.subTest(probability=probability):
                self.assertEqual(quantile([8, 2, 6, 4], probability).value, expected)

    def test_singleton_constant_and_tied_data(self):
        for data in ([5], [5, 5, 5]):
            for probability in (0, 0.25, 0.5, 0.75, 1):
                with self.subTest(data=data, probability=probability):
                    self.assertEqual(quantile(data, probability), StatisticResult(5, 0))
        self.assertEqual(quantile([1, 1, 3, 3], 0.5).value, 2)

    def test_negative_fractional_and_odd_length_data(self):
        self.assertEqual(quantile((-4, 0, 1, 2), 0.25).value, -2)
        self.assertEqual(quantile([1, 2], 0.5).value, 1.5)
        self.assertEqual(quantile([1.25, 1.75], 0.5).value, 1.5)
        for probability, expected in ((0.25, 1), (0.5, 3), (0.75, 5)):
            self.assertEqual(quantile([1, 3, 5], probability).value, expected)

    def test_counts_missing_values_and_preserves_input(self):
        data = [8, None, 2, 6, 4, float("nan")]
        identities = tuple(map(id, data))
        self.assertEqual(quantile(data, 0.25), StatisticResult(3, 2))
        self.assertEqual(tuple(map(id, data)), identities)

    def test_rejects_invalid_probability_types(self):
        class CustomFloat(float):
            pass

        for probability in (
            None,
            "0.5",
            True,
            False,
            1j,
            Decimal("0.5"),
            Fraction(1, 2),
            CustomFloat(0.5),
        ):
            with self.subTest(probability=probability):
                with self.assertRaisesRegex(TypeError, "probability"):
                    quantile([2, 4], probability)

    def test_rejects_invalid_probability_values(self):
        for probability in (
            -0.1,
            1.1,
            float("nan"),
            float("inf"),
            float("-inf"),
            10**400,
        ):
            with self.subTest(probability=probability):
                with self.assertRaisesRegex(ValueError, "probability"):
                    quantile([2, 4], probability)

    def test_uses_input_contract_at_all_probabilities(self):
        for probability in (0, 0.5, 1):
            for data in ([], [None, float("nan")], [2, float("inf")]):
                with self.subTest(data=data, probability=probability):
                    with self.assertRaises(ValueError):
                        quantile(data, probability)
            with self.assertRaisesRegex(TypeError, "index 2"):
                quantile([None, 2, "4"], probability)
        with self.assertRaises(TypeError):
            quantile("123", 0.5)

    def test_handles_large_integer_midpoints_exactly(self):
        offset = 10**400
        self.assertEqual(quantile([offset, offset + 2], 0.5).value, offset + 1)
        self.assertEqual(quantile([-offset, offset + 1], 0.5).value, 0.5)
        self.assertEqual(quantile([offset], 0).value, offset)
        with self.assertRaisesRegex(OverflowError, "Noninteger result"):
            quantile([offset, offset + 1], 0.5)

    def test_avoids_float_midpoint_overflow_and_underflow(self):
        largest = sys.float_info.max
        smallest = math.ulp(0.0)
        self.assertEqual(quantile([largest, largest], 0.5).value, largest)
        self.assertEqual(quantile([-largest, largest], 0.5).value, 0)
        self.assertEqual(quantile([smallest, smallest], 0.5).value, smallest)


class TestIQR(unittest.TestCase):
    def test_hand_computed_cases(self):
        for data, expected in (
            ([2, 4, 6, 8], 4),
            ([1, 3, 5], 4),
            ([1, 2], 1),
            ((-4, 0, 1, 2), 3.5),
            ([1, 1, 3, 3], 2),
            ([1.25, 1.75], 0.5),
            ([0, 0, 0, 100], 50),
        ):
            with self.subTest(data=data):
                self.assertEqual(iqr(data), StatisticResult(expected, 0))

    def test_singleton_and_constant_data(self):
        for data in ([5], [5, 5, 5], [0], [-3, -3]):
            with self.subTest(data=data):
                self.assertEqual(iqr(data), StatisticResult(0, 0))

    def test_counts_missing_values_once_and_preserves_input(self):
        data = [8, None, 2, 6, 4, float("nan")]
        identities = tuple(map(id, data))
        self.assertEqual(iqr(data), StatisticResult(4, 2))
        self.assertEqual(tuple(map(id, data)), identities)
        self.assertEqual(iqr([None, 5]), StatisticResult(0, 1))

    def test_uses_input_contract(self):
        for data in ([], (), [None, float("nan")], [2, float("inf")]):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    iqr(data)
        for invalid in ("4", True, [4]):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(TypeError, "index 2"):
                    iqr([None, 2, invalid])
        with self.assertRaises(TypeError):
            iqr({2, 4})

    def test_shifted_large_integers_preserve_small_spread(self):
        offset = 10**400
        self.assertEqual(iqr([offset + 1, offset + 2, offset + 3, offset + 4]).value, 2)
        self.assertEqual(iqr([0, offset]).value, offset)
        with self.assertRaisesRegex(OverflowError, "Noninteger result"):
            iqr([0.5, offset])

    def test_preserves_finite_float_extremes(self):
        smallest = math.ulp(0.0)
        self.assertEqual(iqr([0.0, smallest]).value, smallest)
        self.assertEqual(iqr([sys.float_info.max, sys.float_info.max]).value, 0)
        self.assertEqual(
            iqr([-sys.float_info.max, sys.float_info.max]).value,
            2 * int(sys.float_info.max),
        )


if __name__ == "__main__":
    unittest.main()