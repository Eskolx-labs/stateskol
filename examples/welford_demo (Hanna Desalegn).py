"""How to use welford(). Standard library only.

Runs in a clean environment with nothing but the package installed:

    python -m venv .venv && source .venv/bin/activate
    pip install -e .
    python "examples/welford_demo (Hanna Desalegn).py"

The module file name has spaces and parentheses, so it is loaded by path.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "stateskol"
    / "welford (Hanna Desalegn).py"
)
SPEC = spec_from_file_location("welford_hanna", MODULE_PATH)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
welford = MODULE.welford


def show(label, result):
    print(
        f"  {label:28s} count={result.count} mean={result.mean} "
        f"variance={result.variance} std={result.std} dropped={result.dropped}"
    )


print("1. Usual case (by hand: mean 5, S 20, variance 20/3)")
show("[2, 4, 6, 8]", welford([2, 4, 6, 8]))

print("2. Missing values are dropped and counted, never filled")
show("[2, 4, None, 6, 8, nan]", welford([2, 4, None, 6, 8, float("nan")]))

print("3. Streaming: a generator is read once, nothing is stored")
show("squares of 1..5", welford(x * x for x in range(1, 6)))

print("4. Boundary cases")
show("empty []", welford([]))
show("single value [7]", welford([7]))
show("constant [5, 5, 5]", welford([5, 5, 5]))

print("5. Invalid input stops at the first bad value")
for label, bad in [
    ("string element", [1, "x", 3]),
    ("bool element", [1, True, 3]),
    ("infinity", [1, 2, float("inf")]),
    ("huge integer", [1, 10**400]),
    ("text as data", "123"),
]:
    try:
        welford(bad)
    except (TypeError, ValueError) as err:
        print(f"  {label:28s} -> {type(err).__name__}: {err}")

print("6. Numerical stability: 1e9 + [4, 7, 13, 16], true variance 30")
data = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
n = len(data)
naive = (sum(x * x for x in data) - sum(data) ** 2 / n) / (n - 1)
print(f"  naive formula: {naive}")
print(f"  welford      : {welford(data).variance}")