
import unittest
import math

from stateskol.descriptive import (
    mean,
    variance,
    median,
    mode,
    quantile,
    iqr,
    drop_missing,
    variance_welford,
    std,
    count,
    minimum,
    maximum,
    data_range,
    frequency_table,
    histogram_counts,
)


class TestDescriptiveStatistics(unittest.TestCase):

    def test_mean(self):
        self.assertEqual(mean([2, 4, 6]), 4)

    def test_variance(self):
        self.assertAlmostEqual(variance([2, 4, 6]), 4)

    def test_median(self):
        self.assertEqual(median([1, 2, 3, 4]), 2.5)

    def test_mode(self):
        self.assertEqual(mode([1, 1, 2, 2, 3]), [1, 2])

    def test_quantile(self):
        self.assertAlmostEqual(quantile([1, 2, 3, 4], 0.25), 1.75)

    def test_iqr(self):
        self.assertAlmostEqual(iqr([1, 2, 3, 4]), 1.5)

    def test_drop_missing(self):
        self.assertEqual(
            drop_missing([1, None, 3, float("nan")]),
            ([1, 3], 2)
        )

    def test_variance_welford(self):
        self.assertAlmostEqual(variance_welford([2, 4, 6]), 4)

    def test_std(self):
        self.assertAlmostEqual(std([2, 4, 6]), 2)

    def test_count(self):
        self.assertEqual(count([1, 2, 3]), 3)

    def test_minimum(self):
        self.assertEqual(minimum([3, 1, 2]), 1)

    def test_maximum(self):
        self.assertEqual(maximum([3, 1, 2]), 3)

    def test_data_range(self):
        self.assertEqual(data_range([3, 1, 2]), 2)

    def test_frequency_table(self):
        self.assertEqual(
            frequency_table([1, 2, 2, 2]),
            [(1, 1, 0.25), (2, 3, 0.75)]
        )

    def test_histogram_counts(self):
        self.assertEqual(
            histogram_counts([1, 2, 2, 3, 4, 5], [0, 2, 4, 6]),
            ([0, 2, 4, 6], [1, 3, 2])
        )


if __name__ == "__main__":
    unittest.main()
