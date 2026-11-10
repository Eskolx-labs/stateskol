"""Spread of Ross's noise data, standard library only.

Run from the repo root: python "examples/spread_demo (Hanna Desalegn).py"
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "src" / "stateskol" / "spread (Hanna Desalegn).py"
spec = spec_from_file_location("spread_hanna", path)
sp = module_from_spec(spec)
spec.loader.exec_module(sp)

# Ross 2.3.i, noise in dB outside Grand Central Station, two readings lost
noise = [82, 89, 94, 110, 74, 122, 112, 95, 100, 78, 65, 60, 90, 83, 87, 75, 114, 85,
         69, 94, 124, 115, 107, 88, 97, 74, 72, 68, 83, 91, 90, 102, 77, 125, 108, 65,
         None, float("nan")]

r = sp.spread(noise)
print(f"count {r.count}, dropped {r.dropped}")
print(f"Q1 {r.q1}, median {r.median}, Q3 {r.q3}, IQR {r.iqr}")
print(f"sample variance {r.variance:.4f}, sample std {r.std:.4f}")

# large mean, small spread: true variance is 30
data = [1e9 + v for v in [4, 7, 13, 16]]
naive = (sum(x * x for x in data) - sum(data) ** 2 / 4) / 3
print(f"1e9 + [4, 7, 13, 16]: naive {naive}, welford {sp.sample_variance(data)}")

assert (r.count, r.dropped, r.q1, r.median, r.q3) == (36, 2, 76, 89.5, 104.5)
assert sp.sample_variance(data) == 30.0
