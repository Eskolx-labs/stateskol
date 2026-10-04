"""Demo of welford(): runs with the standard library only (author: Rebika Yihenew).

Run from the repository root:

    python "examples/welford_demo (Rebika Yihenew).py"

The module file name contains spaces and parentheses, so it cannot be imported
with a normal ``import``; it is loaded by path, relative to this file.
"""

import importlib.util
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "stateskol"
    / "welford (Rebika Yihenew).py"
)
_spec = importlib.util.spec_from_file_location("welford_rebika", _MODULE_PATH)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
welford = _module.welford


def main():
    print("1. Basic use")
    r = welford([2, 4, 4, 4, 5, 5, 7, 9])
    print(f"   count={r.count} mean={r.mean} variance={r.variance:.4f} std={r.std:.4f}")

    print("2. Missing values are dropped and reported, never filled")
    r = welford([2, None, 4, float("nan"), 6])
    print(f"   count={r.count} mean={r.mean} variance={r.variance} dropped={r.n_dropped}")

    print("3. Streaming: a generator is read once, nothing is stored")
    r = welford(x * x for x in range(1, 6))
    print(f"   count={r.count} mean={r.mean} variance={r.variance}")

    print("4. Constant data has exactly zero variance")
    print(f"   variance={welford([7.5] * 5).variance}")

    print("5. Bad input fails fast with a clear message")
    for label, bad in [
        ("empty", []),
        ("single value", [3]),
        ("string element", [1, "x", 3]),
        ("infinity", [1, 2, float("inf")]),
    ]:
        try:
            welford(bad)
        except (TypeError, ValueError) as error:
            print(f"   {label:15s} -> {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()