"""Compare stateskol with numpy and pandas on four datasets.

Quantile rule: stateskol ships Hyndman & Fan type 7. numpy method="linear"
and pandas interpolation="linear" are type 7, so both are set explicitly.

Tolerance: relative 1e-12. Doubles carry about 16 digits (eps = 2.2e-16).
Summing 1000 values in a different order can move the last digits by roughly
n * eps = 2e-13, so 1e-12 allows for rounding order only. A real difference
in rule is far larger (type 6 vs type 7 differ by 1.0 on the ten-value set),
so this tolerance cannot hide a wrong formula.
"""
import math
import random
import sys

import numpy as np
import pandas as pd

from stateskol.descriptive import (
    mean, median, mode, quantile, iqr, variance, stdev, coefficient_variation,
)

REL = 1e-12
TEN = [2, 4, 4, 5, 7, 9, 11, 13, 15, 18]

rng = random.Random(3)
DATASETS = {
    "ten values": TEN,
    "outlier demo": [1, 2, 2, 3, 4, 4, 5, 6, 7, 48],
    "1e9 case": [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4],
    "skewed 1000": [rng.expovariate(1 / 5) for _ in range(1000)],
}

failures = 0


def check(label, ours, *refs):
    global failures
    ok = all(math.isclose(ours, r, rel_tol=REL) for r in refs)
    failures += not ok
    print(f"  {'ok ' if ok else 'BAD'} {label:<8} {ours!r}")


for name, data in DATASETS.items():
    print(name)
    a = np.array(data, dtype=float)
    s = pd.Series(data, dtype=float)
    check("mean", mean(data), np.mean(a), s.mean())
    check("median", median(data), np.median(a), s.median())
    check("var", variance(data), np.var(a, ddof=1), s.var())
    check("stdev", stdev(data), np.std(a, ddof=1), s.std())
    for p in (0.25, 0.75):
        check(f"q{int(p * 100)}", quantile(data, p),
              np.quantile(a, p, method="linear"),
              s.quantile(p, interpolation="linear"))
    check("iqr", iqr(data),
          np.quantile(a, 0.75, method="linear") - np.quantile(a, 0.25, method="linear"))
    check("cv", coefficient_variation(data),
          np.std(a, ddof=1) / abs(np.mean(a)))
    same_mode = mode(data) == s.mode().tolist()
    failures += not same_mode
    print(f"  {'ok ' if same_mode else 'BAD'} mode     {len(mode(data))} value(s)")

print()
print("The rule matters: p75 of the ten values")
print("  type 7 (ours)         ", quantile(TEN, 0.75))
print("  type 6 (numpy weibull)", float(np.quantile(TEN, 0.75, method="weibull")))

print()
print("ALL MATCH" if failures == 0 else f"{failures} MISMATCH(ES)")
sys.exit(1 if failures else 0)
