import numpy as np
from stateskol.descriptive import mean, variance

TOL = 1e-12
data = [70, 85, 85, 90, 100]
print("mean", mean(data), np.mean(data))
print("variance", variance(data), np.var(data, ddof=1))
assert abs(mean(data) - np.mean(data)) < TOL
assert abs(variance(data) - np.var(data, ddof=1)) < TOL
print("matches numpy within", TOL)
from stateskol.descriptive import median
for d in ([7, 1, 5], [4, 1, 3, 2], [70, 85, 85, 90, 100]):
    print("median", median(d), np.median(d))
    assert abs(median(d) - np.median(d)) < TOL
print("median matches numpy within", TOL)
from stateskol.descriptive import quantile, iqr
for q in (0, 0.1, 0.25, 0.5, 0.75, 0.9, 1):
    assert abs(quantile([70, 85, 85, 90, 100], q) - np.quantile([70, 85, 85, 90, 100], q)) < TOL
assert abs(iqr([1, 2, 3, 4]) - (np.quantile([1, 2, 3, 4], 0.75) - np.quantile([1, 2, 3, 4], 0.25))) < TOL
print("quantile and iqr match numpy (linear method) within", TOL)
from stateskol.descriptive import variance_welford
assert abs(variance_welford([1e9+1, 1e9+2, 1e9+3]) - np.var([1e9+1, 1e9+2, 1e9+3], ddof=1)) < TOL
print("welford matches numpy on large-mean data within", TOL)
from stateskol.descriptive import std
assert abs(std([70, 85, 85, 90, 100]) - np.std([70, 85, 85, 90, 100], ddof=1)) < TOL
print("std matches numpy within", TOL)
from stateskol.descriptive import count, minimum, maximum, data_range
for d in ([7, 1, 5], [4, 1, 3, 2], [70, 85, 85, 90, 100]):
    assert count(d) == len(d) and minimum(d) == np.min(d) and maximum(d) == np.max(d) and data_range(d) == np.ptp(d)
print("count, min, max, range match numpy")
from stateskol.descriptive import frequency_table
d = [1, 2, 2, 3, 3, 3]
vals, cnts = np.unique(d, return_counts=True)
assert [(v, c) for v, c, r in frequency_table(d)] == list(zip(vals.tolist(), cnts.tolist()))
print("frequency_table matches numpy")
from stateskol.descriptive import histogram_counts
d = [0, 1, 2, 2, 3, 4, 5, 6]
e, c = histogram_counts(d, [0, 2, 4, 6])
assert c == np.histogram(d, bins=e)[0].tolist()
e, c = histogram_counts(d)
assert c == np.histogram(d, bins=e)[0].tolist()
print("histogram_counts matches numpy, edges:", e, "counts:", c)
from scipy import stats
from stateskol.descriptive import mode
for d in ([1, 2, 2, 3], [4, 4, 4], [5, 1, 1, 5, 9]):
    assert mode(d)[0] == stats.mode(d, keepdims=False).mode
print("mode matches scipy (first of the tied winners)")
