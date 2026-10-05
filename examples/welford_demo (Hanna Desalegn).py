"""Basic usage example for Welford's online variance."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


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


data = [2, 4, 6, 8]

result = welford(data)

print("Input:", data)
print("Count:", result.count)
print("Mean:", result.mean)
print("Sample variance:", result.variance)
print("Sample standard deviation:", result.std)
print("Dropped values:", result.dropped)


data_with_missing = [2, 4, None, 6, 8, float("nan")]

result_with_missing = welford(data_with_missing)

print("\nInput with missing values:", data_with_missing)
print("Count:", result_with_missing.count)
print("Mean:", result_with_missing.mean)
print("Sample variance:", result_with_missing.variance)
print("Sample standard deviation:", result_with_missing.std)
print("Dropped values:", result_with_missing.dropped)