"""One dataset, eight summaries, and the audit. Needs only stateskol."""
from stateskol.descriptive import (
    audit, mean, median, mode, quantile, iqr, variance, stdev,
    coefficient_variation,
)

data = [2, 4, 4, 5, None, 7, 9, 11, 13, 15, 18]

print(audit(data).summary)
print()
print("mean                 ", mean(data))
print("median               ", median(data))
print("mode                 ", mode(data))
print("quantile p=0.25      ", quantile(data, 0.25), "(type 7)")
print("iqr                  ", iqr(data), "(type 7)")
print("variance (ddof=1)    ", variance(data))
print("stdev (ddof=1)       ", stdev(data))
print("coeff. of variation  ", coefficient_variation(data))

print()
print("Numerics: variance of 1e9+1 .. 1e9+4 (true value 1.6667)")
x = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
m = sum(x) / len(x)
print("  naive sum(x*x)/n - m**2 ->", sum(v * v for v in x) / len(x) - m ** 2)
print("  stateskol (Welford)     ->", variance(x))