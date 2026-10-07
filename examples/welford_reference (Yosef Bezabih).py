"""Controlled comparison of welford() against numpy.

Tolerance: relative 1e-9 (np.isclose rtol=1e-9, atol=0).
Why: float64 rounding is about 2.2e-16 per operation. Welford's error
grows roughly with the number of values n, so even n = 1e5 gives about
1e-11 or less, well inside 1e-9. A real formula error (a wrong n or
n - 1) would show up as 1e-1 to 1e-3, so 1e-9 separates rounding noise
from mistakes. numpy is used here only as the reference, never in the
package.
"""
import importlib
import random
from fractions import Fraction

import numpy as np

welford = importlib.import_module("stateskol.welford (Yosef Bezabih)").welford

RTOL = 1e-9
random.seed(0)

cases = {
    "hand example": [2, 4, 4, 4, 5, 5, 7, 9],
    "small floats": [0.1, 0.2, 0.3, 0.4, 0.5],
    "negatives": [-5.5, -1.0, 0.0, 2.5, 9.0],
    "1000 uniform": [random.uniform(-100, 100) for _ in range(1000)],
    "100000 normal": [random.gauss(50, 15) for _ in range(100_000)],
    "constant": [7.0] * 10,
}

print(f"tolerance: rtol={RTOL}, atol=0 (ddof=1 on both sides)")
print(f"{'case':<15}{'welford':>22}{'numpy':>22}  ok")
all_ok = True
for name, data in cases.items():
    mine = welford(data).variance
    ref = float(np.var(data, ddof=1))
    ok = bool(np.isclose(mine, ref, rtol=RTOL, atol=0))
    all_ok &= ok
    print(f"{name:<15}{mine:>22.12g}{ref:>22.12g}  {ok}")

# Numerical stability: huge mean, tiny spread. True variance = 30 exactly.
data = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
n = len(data)
exact = float(Fraction(sum(Fraction(x) ** 2 for x in data)
                       - sum(Fraction(x) for x in data) ** 2 / n, n - 1))
naive = (sum(x * x for x in data) - sum(data) ** 2 / n) / (n - 1)
print("\nstability dataset: [1e9+4, 1e9+7, 1e9+13, 1e9+16]")
print("exact (Fractions) :", exact)
print("naive sum-of-squares:", naive)
print("welford           :", welford(data).variance)
print("numpy var         :", float(np.var(data, ddof=1)))
all_ok &= bool(np.isclose(welford(data).variance, exact, rtol=RTOL))

print("\nALL OK" if all_ok else "\nMISMATCH")