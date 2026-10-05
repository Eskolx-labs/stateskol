"""Demo: how to use welford. Standard library only, no numpy.

Run it from the repository root:
    python "examples/welford_demo (mekhluqat).py"
"""

import importlib.util
from pathlib import Path

_path = (
    Path(__file__).resolve().parents[1] / "src" / "stateskol" / "welford (mekhluqat).py"
)
_spec = importlib.util.spec_from_file_location("welford_mekhluqat", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
welford = _module.welford

# 1. The usual case. By hand: mean 5, M2 20, variance 20 / 3.
print("usual case [2, 4, 6, 8]")
print("  ", welford([2, 4, 6, 8]))

# 2. Missing values are dropped and counted, never filled in.
print("with missing values [2, 4, None, 6, 8, nan]")
r = welford([2, 4, None, 6, 8, float("nan")])
print(f"   used {r.count}, dropped {r.dropped}, variance {r.variance:.4f}")

# 3. Boundary cases.
print("empty input    ->", welford([]))
print("single value   ->", welford([7]))
print("constant values->", welford([5, 5, 5]))

# 4. Invalid values fail fast.
for bad in (["a"], [True], [float("inf")]):
    try:
        welford([1, 2] + bad)
    except (TypeError, ValueError) as err:
        print(f"invalid {bad!r} -> {type(err).__name__}: {err}")

# 5. Numerical stability. The values sit near 1e9 and the true variance is 30.
data = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
n = len(data)
naive = (sum(x * x for x in data) - sum(data) ** 2 / n) / (n - 1)
print("stability case, true variance 30.0")
print("   naive formula:", naive)
print("   welford      :", welford(data).variance)
