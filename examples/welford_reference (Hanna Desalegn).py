"""Compare Welford's results with NumPy."""

import math
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "stateskol"
    / "welford (Hanna Desalegn).py"
)

SPEC = spec_from_file_location("welford_hanna", MODULE_PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

welford = MODULE.welford


# NumPy is used only as an independent reference.
data = [
    2.0,
    4.0,
    6.0,
    8.0,
    10.0,
    12.0,
]

result = welford(data)

expected_mean = np.mean(data)
expected_variance = np.var(data, ddof=1)
expected_std = np.std(data, ddof=1)

relative_tolerance = 1e-12

print("Welford result:")
print(f"  count:    {result.count}")
print(f"  mean:     {result.mean}")
print(f"  variance: {result.variance}")
print(f"  std:      {result.std}")

print("\nNumPy reference:")
print(f"  mean:     {expected_mean}")
print(f"  variance: {expected_variance}")
print(f"  std:      {expected_std}")

print(f"\nRelative tolerance: {relative_tolerance}")

assert math.isclose(
    result.mean,
    expected_mean,
    rel_tol=relative_tolerance,
    abs_tol=0.0,
)

assert math.isclose(
    result.variance,
    expected_variance,
    rel_tol=relative_tolerance,
    abs_tol=0.0,
)

assert math.isclose(
    result.std,
    expected_std,
    rel_tol=relative_tolerance,
    abs_tol=0.0,
)

print("\nNumerical stability check:")

stability_data = [
    1_000_000_000_001,
    1_000_000_000_002,
    1_000_000_000_003,
    1_000_000_000_004,
    1_000_000_000_005,
]

stability_result = welford(stability_data)

naive_mean = sum(stability_data) / len(stability_data)
naive_variance = (
    sum(x * x for x in stability_data)
    - len(stability_data) * naive_mean * naive_mean
) / (len(stability_data) - 1)

numpy_variance = np.var(stability_data, ddof=1)

print(f"  Welford variance: {stability_result.variance}")
print(f"  Naive variance:   {naive_variance}")
print(f"  NumPy variance:   {numpy_variance}")

assert math.isclose(
    stability_result.variance,
    numpy_variance,
    rel_tol=relative_tolerance,
    abs_tol=0.0,
)

print("Numerical stability check passed.")

print("\nComparison passed.")