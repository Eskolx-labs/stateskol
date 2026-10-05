"""Controlled comparison against numpy (numpy is the reference, not the implementation)."""
import importlib.util, pathlib
import numpy as np
p = pathlib.Path(__file__).resolve().parents[1] / "src" / "stateskol" / "welford (Maria).py"
s = importlib.util.spec_from_file_location("w", p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)

# Tolerance per case, justified: float64 eps ~1.1e-16. Plain data: 1e-9 leaves room for
# rounding over 1e5 additions. Offset 1e9: values near 1e9 have spacing ~1.2e-7, which is
# ~1e-7 of a unit-variance spread, so any two correct methods can differ by ~1e-8..1e-7
# relative; 1e-6 is the honest bound there.
TOL = {"normal": 1e-9, "offset 1e9": 1e-6}
rng = np.random.default_rng(0)
cases = {"normal": rng.normal(0, 1, 100_000),
         "offset 1e9": 1e9 + rng.normal(0, 1, 100_000)}
for name, x in cases.items():
    r = m.welford(x.tolist())
    ref = np.var(x, ddof=1)
    ok = abs(r.variance - ref) <= TOL[name] * abs(ref)
    print(f"{name}: welford={r.variance:.12g} numpy={ref:.12g} ok={ok}")
    assert ok
naive = np.mean(cases["offset 1e9"] ** 2) - np.mean(cases["offset 1e9"]) ** 2
print("naive sum-of-squares on offset 1e9:", naive, "(wrong: catastrophic cancellation)")
