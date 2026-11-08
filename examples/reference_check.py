"""Compare histogram_counts (owner: yeabsira) with numpy.

numpy is used ONLY in this file, as the trusted answer to compare with.
histogram_counts itself never uses numpy.

WHAT IS COMPARED, AND THE TOLERANCES

1. Bin counts: must be EQUAL, exactly. Counts are whole numbers, so there
   is no rounding to forgive. Tolerance: 0.
   - mine vs np.histogram(x, bins=<my edges>)   (same edges, so the same
     counting rule must give the same counts)
   - mine vs np.histogram(x, bins="fd")          (numpy picks its own edges)
   - explicit Ross edges vs np.histogram(x, bins=<those edges>)

2. Default edges (Freedman-Diaconis): compared with
   np.histogram_bin_edges(x, bins="fd"). The edges are floats, so a tiny
   difference is allowed. Tolerance: 1e-12 * (max - min), for each edge.
   Why: float64 rounding is about 1e-16 per operation. The edges come from
   the IQR, the width, and low + i * step. That is a handful of operations,
   so a difference of 1e-12 of the data range is a safe ceiling that is
   still far smaller than any real bug (a wrong bin rule moves edges by a
   large fraction of the range). We print the measured worst difference.

The bin rule matches numpy's "fd" rule: width = 2 * IQR * n ** (-1/3),
bins = ceil(range / width), equal bins from the minimum to the maximum,
last bin closed on the right.
"""

import importlib.util
import random
from pathlib import Path

import numpy as np

EDGE_TOL = 1e-12  # times the data range


def load_histogram_counts():
    here = Path(__file__).resolve().parent
    for path in (here.parent / "src" / "stateskol" / "descriptive.py",):
        if path.exists():
            spec = importlib.util.spec_from_file_location("descriptive_hist", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.histogram_counts
    raise FileNotFoundError("src/stateskol/descriptive.py")


histogram_counts = load_histogram_counts()


def compare(name, values):
    """Compare on a list of numbers. Return (ok, worst edge difference)."""
    x = np.array(values, dtype=float)
    mine = histogram_counts(list(values))

    # 1a. same edges -> same counts
    same_edges_counts = np.histogram(x, bins=mine["edges"])[0].tolist()
    counts_ok = mine["counts"] == same_edges_counts

    # 1b + 2. numpy's own fd edges and counts
    numpy_edges = np.histogram_bin_edges(x, bins="fd")
    numpy_counts = np.histogram(x, bins="fd")[0].tolist()
    same_number_of_bins = len(numpy_edges) == len(mine["edges"])
    if same_number_of_bins:
        data_range = x.max() - x.min()
        scale = data_range if data_range > 0 else 1.0
        worst = float(np.max(np.abs(np.array(mine["edges"]) - numpy_edges)) / scale)
        edges_ok = worst <= EDGE_TOL
        numpy_counts_ok = mine["counts"] == numpy_counts
    else:
        worst = float("inf")
        edges_ok = False
        numpy_counts_ok = False

    ok = counts_ok and edges_ok and numpy_counts_ok
    word = "OK" if ok else "FAIL"
    print(f"{name:<30} n={len(x):>6} bins={len(mine['counts']):>4}  "
          f"counts equal={counts_ok and numpy_counts_ok!s:<5}  "
          f"worst edge diff={worst:.2e}  {word}")
    return ok, worst


def check_histogram():
    """Run every comparison. Return True if all of them pass."""
    rng = np.random.default_rng(12345)  # fixed seed, so results repeat
    ross = [int(t) for t in LAMPS_TEXT.split()]

    datasets = [
        ("Ross Table 2.3 lamps", ross),
        ("normal(0, 1)", rng.normal(0, 1, 100000).tolist()),
        ("normal(100, 15)", rng.normal(100, 15, 100000).tolist()),
        ("uniform(-1000, 1000)", rng.uniform(-1000, 1000, 100000).tolist()),
        ("exponential (skewed right)", rng.exponential(2.0, 100000).tolist()),
        ("normal(1e9, 1) big offset", rng.normal(1e9, 1, 100000).tolist()),
        ("integers 0..9 (many ties)", rng.integers(0, 10, 5000).tolist()),
        ("two humps (bimodal)", np.concatenate(
            [rng.normal(0, 1, 5000), rng.normal(8, 1, 5000)]).tolist()),
        ("small 1..16", list(range(1, 17))),
        ("constant 3, 3, 3", [3, 3, 3]),
        ("single value", [42]),
        ("IQR zero 1,1,...,1,100", [1] * 9 + [100]),
    ]
    all_ok = True
    worst_edge = 0.0
    for name, values in datasets:
        ok, worst = compare(name, values)
        all_ok = all_ok and ok
        if worst != float("inf"):
            worst_edge = max(worst_edge, worst)

    # explicit edges: Ross Table 2.4, same edges in numpy
    ross_edges = list(range(500, 1600, 100))
    mine = histogram_counts(ross, edges=ross_edges)["counts"]
    theirs = np.histogram(np.array(ross, float), bins=ross_edges)[0].tolist()
    ross_ok = mine == theirs == [2, 5, 12, 25, 58, 41, 43, 7, 6, 1]
    print(f"{'Ross edges 500..1500 step 100':<30} counts {mine}  "
          f"{'OK' if ross_ok else 'FAIL'}")
    all_ok = all_ok and ross_ok

    # 2000 small random datasets: any difference at all?
    py_rng = random.Random(7)
    differences = 0
    worst_small = 0.0
    for _ in range(2000):
        n = py_rng.randint(2, 500)
        center = py_rng.uniform(-100, 100)
        spread = py_rng.uniform(0.1, 10)
        values = [py_rng.gauss(center, spread) for _ in range(n)]
        x = np.array(values)
        mine = histogram_counts(values)
        numpy_edges = np.histogram_bin_edges(x, bins="fd")
        numpy_counts = np.histogram(x, bins="fd")[0].tolist()
        if len(numpy_edges) != len(mine["edges"]) or mine["counts"] != numpy_counts:
            differences += 1
        else:
            d = float(np.max(np.abs(np.array(mine["edges"]) - numpy_edges)) / (x.max() - x.min()))
            worst_small = max(worst_small, d)
    print()
    print(f"2000 random small datasets: {differences} different from numpy, "
          f"worst edge difference {worst_small:.2e} of the range")
    print(f"worst edge difference over the big datasets: {worst_edge:.2e} of the range")
    print(f"edge tolerance: {EDGE_TOL:.0e} of the range; count tolerance: 0 (exact)")
    all_ok = all_ok and differences == 0 and worst_small <= EDGE_TOL
    return all_ok


LAMPS_TEXT = """
1067 919 1196 785 1126 936 918 1156 920 948 855 1092 1162 1170 929 950
905 972 1035 1045 1157 1195 1195 1340 1122 938 970 1237 956 1102 1022
978 832 1009 1157 1151 1009 765 958 902 923 1333 811 1217 1085 896 958
1311 1037 702 521 933 928 1153 946 858 1071 1069 830 1063 930 807 954
1063 1002 909 1077 1021 1062 1157 999 932 1035 944 1049 940 1122 1115
833 1320 901 1324 818 1250 1203 1078 890 1303 1011 1102 996 780 900
1106 704 621 854 1178 1138 951 1187 1067 1118 1037 958 760 1101 949
992 966 824 653 980 935 878 934 910 1058 730 980 844 814 1103 1000 788
1143 935 1069 1170 1067 1037 1151 863 990 1035 1112 931 970 932 904
1026 1147 883 867 990 1258 1192 922 1150 1091 1039 1083 1040 1289 699
1083 880 1029 658 912 1023 984 856 924 801 1122 1292 1116 880 1173
1134 932 938 1078 1180 1106 1184 954 824 529 998 996 1133 765 775 1105
1081 1171 705 1425 610 916 1001 895 709 860 1110 1149 972 1002
"""


if __name__ == "__main__":
    passed = check_histogram()
    assert passed, "a histogram comparison failed"
    print("ALL HISTOGRAM COMPARISONS MATCH")
