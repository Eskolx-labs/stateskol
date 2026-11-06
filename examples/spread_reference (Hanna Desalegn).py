"""Compare the spread block with numpy on random and textbook data.

Variance and std: numpy var/std with ddof=1, relative tolerance 1e-12.
Welford and numpy's two-pass sum round differently, so they can differ in
the last few bits (float64 keeps about 1e-16 relative), and 1e-12 leaves
room for that while still catching any real mistake.
Data with a large mean and a small spread (1e6 + uniform(0, 1)) gets 1e-8:
both methods lose digits there, numpy's two-pass a little less than Welford
(about 1e-10 against exact fractions), the naive formula far more.
Quantile and IQR: numpy quantile with method="averaged_inverted_cdf", the
same rule as Ross 2.3.3. Both pick a data value or average two. On integer
data they must match exactly. On float data the average of two values can
differ in the last bit, because numpy writes it as a + (b - a)/2, so the
tolerance is 1e-14 relative (1e-12 absolute near zero).
"""

import math
import random
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np

path = Path(__file__).resolve().parents[1] / "src" / "stateskol" / "spread (Hanna Desalegn).py"
spec = spec_from_file_location("spread_hanna", path)
sp = module_from_spec(spec)
spec.loader.exec_module(sp)

RTOL = 1e-12
RTOL_BIG_MEAN = 1e-8
PS = [0, 0.01, 0.1, 0.2, 0.25, 0.3, 0.5, 0.7, 0.75, 0.8, 0.9, 0.99, 1]

rng = random.Random(2026)
datasets = [
    [3, 4, 6, 7, 10],
    [25, 20, 21, 18, 13, 13, 7, 9, 18],
    [82, 89, 94, 110, 74, 122, 112, 95, 100, 78, 65, 60, 90, 83, 87, 75, 114, 85,
     69, 94, 124, 115, 107, 88, 97, 74, 72, 68, 83, 91, 90, 102, 77, 125, 108, 65],
    ]
for _ in range(500):
    n = rng.randint(2, 80)
    kind = rng.choice(["int", "float", "big"])
    if kind == "int":
        datasets.append([rng.randint(-20, 20) for _ in range(n)])  # lots of ties
    elif kind == "float":
        datasets.append([rng.gauss(0, 10) for _ in range(n)])
    else:
        datasets.append([1e6 + rng.random() for _ in range(n)])


worst = {RTOL: 0.0, RTOL_BIG_MEAN: 0.0}
q_checks = 0
for data in datasets:
    a = np.array(data)
    tol = RTOL_BIG_MEAN if min(data) > 1e5 else RTOL
    for ours, ref in [(sp.sample_variance(data), np.var(a, ddof=1)),
                      (sp.sample_std(data), np.std(a, ddof=1))]:
        rel = abs(ours - ref) / abs(ref) if ref else abs(ours)
        worst[tol] = max(worst[tol], rel)
        assert rel <= tol, (data[:5], ours, ref)
    for p in PS:
        ours = sp.quantile(data, p)
        ref = float(np.quantile(a, p, method="averaged_inverted_cdf"))
        if all(float(x).is_integer() for x in data):
            assert ours == ref, (data[:5], p, ours, ref)
        else:
            assert math.isclose(ours, ref, rel_tol=1e-14, abs_tol=1e-12), (data[:5], p, ours, ref)
        q_checks += 1
    q1, q3 = np.quantile(a, [0.25, 0.75], method="averaged_inverted_cdf")
    assert math.isclose(sp.iqr(data), q3 - q1, rel_tol=1e-12, abs_tol=1e-12)

# 1e9 + [4, 7, 13, 16]: exact answer 30, numpy and ours both get it
big = [1e9 + v for v in [4, 7, 13, 16]]
assert sp.sample_variance(big) == np.var(big, ddof=1) == 30.0

print(f"{len(datasets)} data sets, {q_checks} quantiles matched")
for tol, err in worst.items():
    print(f"worst relative error for variance/std: {err:.2e} (tolerance {tol:g})")
