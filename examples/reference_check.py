"""Compare count and minimum (Core A) with numpy and pandas.

numpy and pandas are used ONLY here, as the trusted answer. count and
minimum never use them.

Run on its own:  python examples/reference_core_a.py

TOLERANCE: 0 (exact equality), for both functions.
Why: count is a whole number. minimum does no arithmetic: it returns one of
the input values, and every accepted int (abs <= 2**53) converts to float
exactly. So there is no rounding to forgive. Any difference at all is a bug.

What is compared:
  count(x)    == pandas Series(x).count()      (pandas counts non-missing)
  count(x)    == numpy  count of non-NaN
  minimum(x)  == numpy  np.nanmin(x)
  minimum(x)  == pandas Series(x).min()        (pandas skips missing)
Where numpy and pandas raise or warn (all missing), we compare the
EXPECTED behaviour: count 0 and minimum raises EmptyDataError.
"""

import random
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from stateskol.descriptive import count, minimum  # noqa: E402
from stateskol.errors import EmptyDataError  # noqa: E402

LAMPS = """
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


def compare(name, values):
    mine_count = count(list(values))
    pd_count = int(pd.Series(values, dtype="float64").count())
    np_count = int(np.sum(~np.isnan(np.array(values, dtype="float64"))))
    count_ok = mine_count == pd_count == np_count

    if pd_count == 0:
        try:
            minimum(list(values))
            min_ok = False
        except EmptyDataError:
            min_ok = True
        shown = "raises EmptyDataError"
    else:
        mine_min = minimum(list(values))
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            np_min = float(np.nanmin(np.array(values, dtype="float64")))
        pd_min = float(pd.Series(values, dtype="float64").min())
        min_ok = mine_min == np_min == pd_min
        shown = repr(mine_min)

    ok = count_ok and min_ok
    print(f"{name:<34} count={mine_count:>6}  min={shown:<24} {'OK' if ok else 'FAIL'}")
    return ok


def check_core_a():
    """Run every comparison. Return True if all pass."""
    rng = np.random.default_rng(2024)
    lamps = [int(t) for t in LAMPS.split()]
    nan = float("nan")

    sets = [
        ("Ross lamps (hand: min 521)", lamps),
        ("hand set 2,4,4,4,5,5,7,9", [2, 4, 4, 4, 5, 5, 7, 9]),
        ("with None and NaN", [4, None, 2.5, nan, 7]),
        ("normal(0,1) 100000", rng.normal(0, 1, 100000).tolist()),
        ("uniform(-1e6,1e6) 100000", rng.uniform(-1e6, 1e6, 100000).tolist()),
        ("normal(1e9,1) big offset", rng.normal(1e9, 1, 100000).tolist()),
        ("integers up to 2**53", [2 ** 53, 5, -(2 ** 53), 0]),
        ("negative zero and zero", [0.0, -0.0, 1.0]),
        ("tiny numbers 1e-300", [1e-300, 5e-324, 2e-300]),
        ("single value", [42]),
        ("constant", [3.7] * 1000),
        ("ties for the minimum", [5, 2, 2, 9, 2]),
        ("empty", []),
        ("all missing", [None, nan, None]),
        ("10% missing, 50000", [None if rng.random() < 0.1 else float(v)
                                for v in rng.normal(10, 3, 50000)]),
    ]
    all_ok = True
    for name, values in sets:
        all_ok = compare(name, values) and all_ok

    r = random.Random(11)
    different = 0
    for _ in range(3000):
        n = r.randint(0, 300)
        vals = []
        for _ in range(n):
            u = r.random()
            if u < 0.15:
                vals.append(None if r.random() < 0.5 else nan)
            elif u < 0.5:
                vals.append(r.randint(-10 ** 6, 10 ** 6))
            else:
                vals.append(r.uniform(-1000, 1000))
        if not compare_quiet(vals):
            different += 1
    print()
    print(f"3000 random mixed datasets: {different} different from numpy/pandas")
    print("tolerance: 0 (exact equality)")
    return all_ok and different == 0


def compare_quiet(values):
    mine_count = count(list(values))
    s = pd.Series(values, dtype="float64")
    if mine_count != int(s.count()):
        return False
    if mine_count == 0:
        try:
            minimum(list(values))
            return False
        except EmptyDataError:
            return True
    return minimum(list(values)) == float(s.min()) == float(np.nanmin(s.to_numpy()))


if __name__ == "__main__":
    assert check_core_a(), "a Core A comparison failed"
    print("ALL CORE A COMPARISONS MATCH")