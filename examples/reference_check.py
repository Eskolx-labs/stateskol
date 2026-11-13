
"""Controlled comparison of the Week 2 contract against numpy and pandas.
 
Needs numpy and pandas (this is the reference check, not the demo).
Run:  python examples/reference_check.py
 
TOLERANCE = 0 (exact equality).
Why: count, minimum and maximum only count or compare values, so there is no
rounding to tolerate. data_range is a single subtraction, max - min, and numpy
and pandas perform the same IEEE-754 double subtraction on the same two
doubles, so the results must be bit-identical. Any difference, however small,
is a bug, not rounding. (Week 3+ summaries that accumulate sums will need a
non-zero tolerance, and that tolerance must be justified separately.)
"""
import math
 
import numpy as np
import pandas as pd
 
from stateskol.descriptive import count, data_range, maximum, minimum
 
TOLERANCE = 0.0
NAN = float("nan")
 
DATASETS = {
    "plain ints": [3, 1, 2],
    "floats": [2.5, -1.25, 9.75, 0.0],
    "constant": [5, 5, 5],
    "single value": [7],
    "negatives": [-4, -9, -1],
    "with None and nan": [4, 1, None, 9, NAN, 6],
    "large (below 2**53)": [2**52, 2**52 + 1, 1],
    "tiny floats": [1e-300, 3e-300, 2e-300],
}
 
 
def close(a, b):
    return abs(a - b) <= TOLERANCE
 
 
failures = 0
print(f"tolerance = {TOLERANCE} (exact)\n")
for name, data in DATASETS.items():
    s = pd.Series(data, dtype="float64")          # pandas: None -> NaN, skipna
    arr = np.array([x for x in data if x is not None], dtype="float64")
    arr = arr[~np.isnan(arr)]                      # numpy: drop missing by hand
 
    mine = {
        "count": count(data),
        "min": minimum(data),
        "max": maximum(data),
        "range": data_range(data),
    }
    ref_pandas = {
        "count": int(s.count()),
        "min": float(s.min()),
        "max": float(s.max()),
        "range": float(s.max() - s.min()),
    }
    ref_numpy = {
        "count": int(arr.size),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "range": float(np.ptp(arr)),
    }
 
    ok = True
    for key in mine:
        for label, ref in (("pandas", ref_pandas), ("numpy", ref_numpy)):
            if not close(mine[key], ref[key]):
                ok = False
                failures += 1
                print(f"  MISMATCH {name}: {key} mine={mine[key]!r} {label}={ref[key]!r}")
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {mine}")
 
print()
if failures:
    raise SystemExit(f"{failures} mismatch(es)")
print("All datasets match numpy and pandas exactly.")
 
