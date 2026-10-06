"""
Compare welford() against numpy on several datasets.

Run from the repo root:
    python "examples/welford_reference (Welasma).py"
"""

import importlib.util
from pathlib import Path

import numpy as np


_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_WELFORD_FILE = _ROOT / "src" / "stateskol" / "welford (Welasma).py"

_spec = importlib.util.spec_from_file_location("welford_module", _WELFORD_FILE)
_welford_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_welford_module)
welford = _welford_module.welford


DATASETS = {
    "small":        [5.0, 7.0, 4.0, 10.0],
    "medium":       [5.0, 7.0, 4.0, 10.0, 6.0, 8.0, 3.0, 9.0, 5.5, 7.5],
    "constant":     [3.0, 3.0, 3.0, 3.0, 3.0],
    "wide_range":   [1e-6, 1e-3, 1.0, 1e3, 1e6],
    "large_offset": [1e12 + 1, 1e12 + 2, 1e12 + 3, 1e12 + 4],
}

RTOL = 1e-12
ATOL = 1e-12


def main():
    print("Welford vs numpy - sample variance (ddof=1) and std. dev.")
    print(f"Tolerance: rtol={RTOL}, atol={ATOL}\n")

    ok = True
    for name, values in DATASETS.items():
        arr = np.asarray(values, dtype=float)
        count, mean, variance, std_dev = welford(values)

        np_mean = float(np.mean(arr))
        np_var = float(np.var(arr, ddof=1))
        np_std = float(np.std(arr, ddof=1))

        m_ok = np.isclose(mean,     np_mean, rtol=RTOL, atol=ATOL)
        v_ok = np.isclose(variance, np_var,  rtol=RTOL, atol=ATOL)
        s_ok = np.isclose(std_dev,  np_std,  rtol=RTOL, atol=ATOL)

        print(f"[{name}] n={count}")
        print(f"  mean     welford={mean!r:>22}  numpy={np_mean!r:>22}  ok={m_ok}")
        print(f"  variance welford={variance!r:>22}  numpy={np_var!r:>22}  ok={v_ok}")
        print(f"  std      welford={std_dev!r:>22}  numpy={np_std!r:>22}  ok={s_ok}\n")

        if not (count == arr.size and m_ok and v_ok and s_ok):
            ok = False

    if ok:
        print("PASS: every dataset matched numpy within tolerance.")
    else:
        raise AssertionError("One or more datasets did not match numpy.")


if __name__ == "__main__":
    main()