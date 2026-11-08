"""Histogram section of tests/test_descriptive.py (owner: Yeabsira).

Standard library and pytest only. Every expected number below was
counted by hand, or comes from Ross, section 2.2.3.
"""

import math
import random

import pytest

from stateskol.descriptive import histogram_counts


# ----------------------------------------------------------------------------
# HISTOGRAM TESTS
# ----------------------------------------------------------------------------

# Ross Table 2.3: the lifetimes in hours of 200 lamps.
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

# Ross Table 2.4: class intervals of length 100 starting at 500
ROSS_EDGES = [500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500]
ROSS_COUNTS = [2, 5, 12, 25, 58, 41, 43, 7, 6, 1]


# ---------- hand-worked ----------
def test_histogram_ross_table_2_4():
    r = histogram_counts(LAMPS, edges=ROSS_EDGES)
    assert r["counts"] == ROSS_COUNTS
    assert sum(r["counts"]) == 200
    assert r["dropped"] == 0


def test_histogram_small_hand_count():
    # edges 0, 2, 4, 6. [0,2) holds 1.  [2,4) holds 2,2,3,3,3.  [4,6] holds 4,4,4,4
    r = histogram_counts([1, 2, 2, 3, 3, 3, 4, 4, 4, 4], edges=[0, 2, 4, 6])
    assert r["counts"] == [1, 5, 4]
    assert r["edges"] == [0.0, 2.0, 4.0, 6.0]


def test_histogram_default_rule_by_hand():
    # data 1..16. n = 16. Q1 = 4.75, Q3 = 12.25, IQR = 7.5.
    # width h = 2 * 7.5 * 16 ** (-1/3) = 5.9528.  range = 15.
    # bins k = ceil(15 / 5.9528) = ceil(2.52) = 3.  step = 15 / 3 = 5.
    # edges 1, 6, 11, 16.  [1,6) = 1..5 (5)   [6,11) = 6..10 (5)   [11,16] = 11..16 (6)
    r = histogram_counts(list(range(1, 17)))
    assert r["edges"] == [1.0, 6.0, 11.0, 16.0]
    assert r["counts"] == [5, 5, 6]


def test_histogram_default_rule_on_ross_lamps():
    # n = 200, IQR = 197.25, h = 2 * 197.25 * 200 ** (-1/3) = 67.4586
    # range = 1425 - 521 = 904.  k = ceil(904 / 67.4586) = ceil(13.40) = 14
    r = histogram_counts(LAMPS)
    assert len(r["counts"]) == 14
    assert r["edges"][0] == 521.0
    assert r["edges"][-1] == 1425.0
    assert sum(r["counts"]) == 200


# ---------- the edge rules ----------
def test_histogram_left_end_is_included():
    # 1 sits exactly on the middle edge: it belongs to the RIGHT bin [1, 2)
    r = histogram_counts([0, 1, 2], edges=[0, 1, 2])
    assert r["counts"] == [1, 2]


def test_histogram_right_end_of_last_bin_is_included():
    # 2 equals the last edge: the last bin is closed, so it is counted
    r = histogram_counts([2], edges=[0, 1, 2])
    assert r["counts"] == [0, 1]


def test_histogram_value_on_first_edge_is_counted():
    r = histogram_counts([0], edges=[0, 1, 2])
    assert r["counts"] == [1, 0]


def test_histogram_default_edges_start_at_min_and_end_at_max():
    data = [3.5, 9.25, 1.0, 7.75, 4.0, 6.5, 2.25, 8.0]
    r = histogram_counts(data)
    assert r["edges"][0] == min(data)
    assert r["edges"][-1] == max(data)


def test_histogram_nothing_lost_at_the_borders():
    data = [3.5, 9.25, 1.0, 7.75, 4.0, 6.5, 2.25, 8.0]
    r = histogram_counts(data)
    assert sum(r["counts"]) == len(data)
    assert r["counts"][0] >= 1    # the minimum is in the first bin
    assert r["counts"][-1] >= 1   # the maximum is in the last bin


def test_histogram_default_bins_have_equal_width():
    r = histogram_counts(list(range(1, 17)))
    widths = [r["edges"][i + 1] - r["edges"][i] for i in range(len(r["edges"]) - 1)]
    for w in widths:
        assert w == pytest.approx(widths[0], rel=1e-12)


def test_histogram_total_equals_number_of_values_random():
    rng = random.Random(1)
    for _ in range(200):
        n = rng.randint(2, 300)
        data = [rng.gauss(rng.uniform(-50, 50), rng.uniform(0.5, 20)) for _ in range(n)]
        r = histogram_counts(data)
        assert sum(r["counts"]) == n
        assert r["edges"][0] == min(data)
        assert r["edges"][-1] == max(data)


# ---------- usual cases ----------
def test_histogram_order_does_not_matter():
    a = histogram_counts([9, 2, 5, 4, 7, 4, 5, 4])
    b = histogram_counts([2, 4, 4, 4, 5, 5, 7, 9])
    assert a == b


def test_histogram_negative_numbers():
    r = histogram_counts([-3, -1, 0, 2], edges=[-4, -2, 0, 2])
    # [-4,-2): -3     [-2,0): -1     [0,2]: 0 and 2
    assert r["counts"] == [1, 1, 2]


def test_histogram_accepts_tuple_and_generator():
    assert histogram_counts((1, 2, 3), edges=[0, 2, 4])["counts"] == [1, 2]
    assert histogram_counts((x for x in [1, 2, 3]), edges=[0, 2, 4])["counts"] == [1, 2]


def test_histogram_does_not_change_the_input():
    data = [3, 1, 2]
    edges = [0, 2, 4]
    histogram_counts(data, edges=edges)
    assert data == [3, 1, 2]
    assert edges == [0, 2, 4]


# ---------- boundary cases ----------
def test_histogram_empty_raises():
    with pytest.raises(ValueError):
        histogram_counts([])


def test_histogram_all_missing_raises():
    with pytest.raises(ValueError):
        histogram_counts([None, float("nan")])


def test_histogram_single_value():
    r = histogram_counts([5])
    assert r["edges"] == [4.5, 5.5]
    assert r["counts"] == [1]


def test_histogram_constant_values():
    r = histogram_counts([3.7] * 50)
    assert r["edges"] == [3.2, 4.2]
    assert r["counts"] == [50]


def test_histogram_tied_values_with_zero_iqr_gives_one_bin():
    # more than half the values are 1, so Q1 = Q3 = 1 and IQR = 0
    r = histogram_counts([1, 1, 1, 1, 1, 1, 1, 1, 1, 100])
    assert r["edges"] == [1.0, 100.0]
    assert r["counts"] == [10]


def test_histogram_tied_values_with_explicit_edges_still_work():
    r = histogram_counts([1, 1, 1, 1, 1, 1, 1, 1, 1, 100], edges=[0, 50, 100])
    assert r["counts"] == [9, 1]


@pytest.mark.parametrize("bad", ["a", "1", True, False, 1 + 2j, [1]])
def test_histogram_invalid_type_raises_typeerror(bad):
    with pytest.raises(TypeError):
        histogram_counts([1.0, bad, 3.0])


@pytest.mark.parametrize("bad", [float("inf"), float("-inf")])
def test_histogram_infinity_raises_valueerror(bad):
    with pytest.raises(ValueError):
        histogram_counts([1.0, bad, 3.0])


# ---------- missing values ----------
def test_histogram_missing_values_dropped_and_counted():
    r = histogram_counts([1, None, 2, float("nan"), 3], edges=[0, 2, 4])
    assert r["dropped"] == 2
    assert r["counts"] == [1, 2]


def test_histogram_nothing_dropped_means_zero():
    assert histogram_counts([1, 2])["dropped"] == 0


# ---------- explicit edges that are wrong ----------
def test_histogram_edges_need_two_numbers():
    with pytest.raises(ValueError):
        histogram_counts([1, 2], edges=[0])
    with pytest.raises(ValueError):
        histogram_counts([1, 2], edges=[])


def test_histogram_edges_must_increase():
    with pytest.raises(ValueError):
        histogram_counts([1, 2], edges=[0, 2, 1])
    with pytest.raises(ValueError):
        histogram_counts([1, 2], edges=[0, 1, 1, 3])


def test_histogram_edges_bad_values():
    with pytest.raises(ValueError):
        histogram_counts([1, 2], edges=[0, float("nan"), 3])
    with pytest.raises(ValueError):
        histogram_counts([1, 2], edges=[0, float("inf")])
    with pytest.raises(TypeError):
        histogram_counts([1, 2], edges=[0, "3"])
    with pytest.raises(TypeError):
        histogram_counts([1, 2], edges=[0, True, 3])


def test_histogram_value_below_first_edge_raises():
    with pytest.raises(ValueError):
        histogram_counts([0.5, 2], edges=[1, 3])


def test_histogram_value_above_last_edge_raises():
    with pytest.raises(ValueError):
        histogram_counts([1, 3.5], edges=[1, 3])
