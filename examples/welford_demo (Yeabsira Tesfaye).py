"""Demo of welford (Yeabsira Tesfaye).

Needs nothing except Python and the welford file next to it / in src/stateskol.
Run:  python "welford_demo (Yeabsira Tesfaye).py"
"""

import importlib.util
from pathlib import Path


def load_welford():
    folder = Path(__file__).resolve().parent
    name = "welford (Yeabsira Tesfaye).py"
    for path in (folder / name, folder.parent / "src" / "stateskol" / name):
        if path.exists():
            spec = importlib.util.spec_from_file_location("welford_yt", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.welford
    raise FileNotFoundError(name)


welford = load_welford()

# 1. The hand-worked example
print("1. Data: 2, 4, 4, 4, 5, 5, 7, 9")
r = welford([2, 4, 4, 4, 5, 5, 7, 9])
print("   code:    count =", r["count"], " mean =", r["mean"],
      " variance =", round(r["variance"], 6), " std =", round(r["std"], 6))
print("   by hand: count = 8  mean = 5  variance = 32/7 = 4.571429"
      "  std = 2.13809")

# 2. Missing values
print()
print("2. Missing values are dropped and counted")
r = welford([2, None, 4, float("nan"), 4, 4, 5, 5, 7, 9])
print("   count =", r["count"], " dropped =", r["dropped"],
      " variance =", round(r["variance"], 6))

# 3. Special cases
print()
print("3. Special cases")
r = welford([42])
print("   one value:  count =", r["count"], " variance =", r["variance"])
r = welford([3.7, 3.7, 3.7, 3.7, 3.7])
print("   constant:   variance =", r["variance"])

for label, bad in [("empty", []), ("string", ["a"]), ("infinity", [1, float("inf")])]:
    try:
        welford(bad)
    except (TypeError, ValueError) as error:
        print("  ", label + ":", type(error).__name__ + ":", error)

# 4. Numerical stability
print()
print("4. Big numbers: 1e9+4, 1e9+7, 1e9+13, 1e9+16   (true variance = 30)")
big = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
n = len(big)
naive = (sum(x * x for x in big) - sum(big) ** 2 / n) / (n - 1)
print("   naive formula:", naive)
print("   welford:      ", welford(big)["variance"])

