"""Reference check: compare welford against numpy.

Tolerance: relative 1e-9. Double precision carries about 16 significant
digits, so two correct methods differ by roughly 1e-15 or less. 1e-9 absorbs
rounding noise but is far tighter than any real algorithm mistake, such as
dividing by n instead of n - 1, which changes the result by whole percents.

numpy is used here only as a reference, never inside the package.
"""

import importlib.util
import math
import random
from pathlib import Path

import numpy as np

REL_TOL = 1e-9

_path = (
    Path(__file__).resolve().parents[1] / "src" / "stateskol" / "welford (mekhluqat).py"
)
_spec = importlib.util.spec_from_file_location("welford_mekhluqat", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
welford = _module.welford


def check(name, data):
    mine = welford(data)
    ref_mean = float(np.mean(data))
    ref_var = float(np.var(data, ddof=1))
    ref_std = float(np.std(data, ddof=1))

    print(f"== {name} (n={len(data)})")
    print(f"   variance  mine={mine.variance!r}  numpy={ref_var!r}")
    ok = (
        math.isclose(mine.mean, ref_mean, rel_tol=REL_TOL)
        and math.isclose(mine.variance, ref_var, rel_tol=REL_TOL)
        and math.isclose(mine.std, ref_std, rel_tol=REL_TOL)
    )
    rel_diff = abs(mine.variance - ref_var) / ref_var
    print(f"   relative difference {rel_diff:.2e}  tolerance {REL_TOL:.0e}")
    if not ok:
        raise SystemExit(f"FAIL: {name} differs from numpy beyond {REL_TOL:.0e}")
    print("   OK")


random.seed(1)
check("small hand-worked set", [2, 4, 6, 8])
check("1000 random values", [random.gauss(50, 10) for _ in range(1000)])
check("large offset (stability case)", [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16])
print("all reference checks passed")
