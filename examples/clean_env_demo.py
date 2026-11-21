"""Documentation example: why the package uses Welford's one-pass variance.

Needs only the package. Run:  python examples/variance_1e9_demo.py
"""

from stateskol.descriptive import (
    _variance_naive, _variance_two_pass, _variance_welford)

# four numbers 1 apart, sitting near one billion. True sample variance = 5/3.
x = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
print("data:", x)
print("true sample variance (by hand: S = 5, n - 1 = 3):", 5 / 3)
print()
print("naive   mean(x*x) - mean**2 :", _variance_naive(x))
print("two-pass (mean, then squares):", _variance_two_pass(x))
print("welford  (one pass)          :", _variance_welford(x))
print()
print("Why the naive formula fails: the squares are about 1e18, and floats that")
print("big are 128 apart, so a spread of 1.67 is smaller than the gap.")

# the edge of what the package accepts: above 2**53 an integer is not a float
top = float(2 ** 53)
y = [top - 3, top - 2, top - 1, top]
print()
print("float(2**53 + 1) == float(2**53):", float(2 ** 53 + 1) == float(2 ** 53))
print("at the edge, data", y)
print("  two-pass:", _variance_two_pass(y), "(the sum is above 2**53, so the mean is off)")
print("  welford :", _variance_welford(y))