"""Documentation example: runs with only stateskol installed (no numpy).

Run from anywhere after `pip install -e .`:
    python "examples/welford_demo (Yosef Bezabih).py"
"""
import importlib

welford = importlib.import_module("stateskol.welford (Yosef Bezabih)").welford

data = [2, 4, 4, 4, 5, 5, 7, 9]
result = welford(data)
print("data      :", data)
print("count     :", result.count)
print("mean      :", result.mean)
print("variance  :", result.variance, "(sample, ddof=1)")
print("std       :", result.std)
print("dropped   :", result.dropped)

# Missing values are dropped and reported, never filled in.
messy = [2, None, 4, float("nan"), 4, 4, 5, 5, 7, 9]
print("with missing values, dropped =", welford(messy).dropped)

# Population variance instead of sample variance.
print("population variance (ddof=0):", welford(data, ddof=0).variance)

# Bad input fails fast.
try:
    welford([])
except ValueError as err:
    print("empty input ->", type(err).__name__ + ":", err)