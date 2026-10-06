"""
Usage demonstration of welford(data).

Run from the repo root:
    python "examples\welford_demo (welasma).py"
"""

import importlib.util
from pathlib import Path


_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_WELFORD_FILE = _ROOT / "src" / "stateskol" / "welford (welasma).py"

_spec = importlib.util.spec_from_file_location("welford_module", _WELFORD_FILE)
_welford_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_welford_module)
welford = _welford_module.welford


def main():
    data = [5, 7, 4, 10]
    count, mean, variance, std_dev = welford(data)

    print("Input data:        ", data)
    print("Count:             ", count)
    print("Mean:              ", mean)
    print("Sample variance:   ", variance)
    print("Sample std. dev.:  ", std_dev)
    print()

    n = 0
    running_mean = 0.0
    S = 0.0

    print("Online updates (single pass):")
    for x in data:
        n += 1
        delta = x - running_mean
        running_mean += delta / n
        S += delta * (x - running_mean)
        print(f"  x={x:>3}  n={n}  mean={running_mean:.6f}  S={S:.6f}")

    print()
    print(f"Sample variance = S / (n - 1) = {S / (n - 1):.6f}")


if __name__ == "__main__":
    main()