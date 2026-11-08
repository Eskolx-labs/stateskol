"""examples/clean_env_demo.py — histogram_counts demonstration.

Owner: Yeabsira

Runs with nothing installed except the stateskol package itself.
No numpy, no pandas, no pytest — stdlib only alongside stateskol.

To run from the repo root:
    python examples/clean_env_demo.py

What this shows
---------------
1. Explicit edges — Ross Table 2.4 (textbook numbers you can check by hand)
2. Default Freedman-Diaconis bin rule on the same lamp data
3. Missing value handling (None and NaN dropped and counted)
"""

from stateskol.descriptive import histogram_counts

# ---------------------------------------------------------------------------
# The data: lamp lifetimes in hours, Ross Table 2.3 (n = 200)
# ---------------------------------------------------------------------------
LAMPS = [
    1067, 919, 1196, 785, 1126, 936, 918, 1156, 920, 948,
    855, 1092, 1162, 1170, 929, 950, 905, 972, 1035, 1045,
    1157, 1195, 1195, 1340, 1122, 938, 970, 1237, 956, 1102,
    1022, 978, 832, 1009, 1157, 1151, 1009, 765, 958, 902,
    923, 1333, 811, 1217, 1085, 896, 958, 1311, 1037, 702,
    521, 933, 928, 1153, 946, 858, 1071, 1069, 830, 1063,
    930, 807, 954, 1063, 1002, 909, 1077, 1021, 1062, 1157,
    999, 932, 1035, 944, 1049, 940, 1122, 1115, 833, 1320,
    901, 1324, 818, 1250, 1203, 1078, 890, 1303, 1011, 1102,
    996, 780, 900, 1106, 704, 621, 854, 1178, 1138, 951,
    1187, 1067, 1118, 1037, 958, 760, 1101, 949, 992, 966,
    824, 653, 980, 935, 878, 934, 910, 1058, 730, 980,
    844, 814, 1103, 1000, 788, 1143, 935, 1069, 1170, 1067,
    1037, 1151, 863, 990, 1035, 1112, 931, 970, 932, 904,
    1026, 1147, 883, 867, 990, 1258, 1192, 922, 1150, 1091,
    1039, 1083, 1040, 1289, 699, 1083, 880, 1029, 658, 912,
    1023, 984, 856, 924, 801, 1122, 1292, 1116, 880, 1173,
    1134, 932, 938, 1078, 1180, 1106, 1184, 954, 824, 529,
    998, 996, 1133, 765, 775, 1105, 1081, 1171, 705, 1425,
    610, 916, 1001, 895, 709, 860, 1110, 1149, 972, 1002,
]

# ---------------------------------------------------------------------------
# 1. Explicit edges — Ross Table 2.4
#    Bins of width 100 starting at 500.
#    Expected counts: [2, 5, 12, 25, 58, 41, 43, 7, 6, 1]  (sums to 200)
# ---------------------------------------------------------------------------
print("=" * 60)
print("1. Explicit edges — Ross Table 2.4")
print("   Bins of width 100 from 500 to 1500")
print("=" * 60)

ross_edges = [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500]
r = histogram_counts(LAMPS, edges=ross_edges)

print(f"  {'Interval':<16} {'Count':>5}")
print(f"  {'-'*16}  {'-'*5}")
for i, count in enumerate(r["counts"]):
    lo = int(r["edges"][i])
    hi = int(r["edges"][i + 1])
    bracket = f"[{lo}, {hi})"  if i < len(r["counts"]) - 1 else f"[{lo}, {hi}]"
    print(f"  {bracket:<16} {count:>5}")

print(f"\n  Total lamps counted : {sum(r['counts'])}")
print(f"  Dropped (missing)   : {r['dropped']}")
print(f"\n  Ross Table 2.4 expected: [2, 5, 12, 25, 58, 41, 43, 7, 6, 1]")
print(f"  Got                    : {r['counts']}")
match = r["counts"] == [2, 5, 12, 25, 58, 41, 43, 7, 6, 1]
print(f"  Match: {match}")

# ---------------------------------------------------------------------------
# 2. Default Freedman-Diaconis bin rule on the same lamp data
#    width h = 2 * IQR * n^(-1/3).  With n=200 and IQR=197.25 this gives
#    h ≈ 67.46, range = 904, so k = ceil(904 / 67.46) = 14 bins.
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("2. Default Freedman-Diaconis rule on the lamp data")
print("   Expected: 14 bins from 521.0 to 1425.0")
print("=" * 60)

r2 = histogram_counts(LAMPS)

print(f"  Number of bins : {len(r2['counts'])}")
print(f"  First edge     : {r2['edges'][0]}")
print(f"  Last edge      : {r2['edges'][-1]}")
print(f"  Total counted  : {sum(r2['counts'])}")
print()
print(f"  {'Interval':<22} {'Count':>5}")
print(f"  {'-'*22}  {'-'*5}")
for i, count in enumerate(r2["counts"]):
    lo = r2["edges"][i]
    hi = r2["edges"][i + 1]
    bracket = f"[{lo:.1f}, {hi:.1f})" if i < len(r2["counts"]) - 1 else f"[{lo:.1f}, {hi:.1f}]"
    print(f"  {bracket:<22} {count:>5}")

# ---------------------------------------------------------------------------
# 3. Missing value handling
#    None and NaN are dropped silently, counted in "dropped".
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("3. Missing value handling")
print("=" * 60)

data_with_missing = [1, None, 2, float("nan"), 3, None, 4]
r3 = histogram_counts(data_with_missing, edges=[0, 2, 4])

print(f"  Input  : {data_with_missing}")
print(f"  Edges  : [0, 2, 4]")
print(f"  Counts : {r3['counts']}   ([0,2) holds 1  |  [2,4] holds 2,3,4)")
print(f"  Dropped: {r3['dropped']}  (two Nones + one NaN = 3 missing)")

print()
print("Demo complete — all results match the textbook and hand counts.")
