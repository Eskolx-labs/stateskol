from stateskol.descriptive import mean, median, mode


def test_mean():
    assert mean([2, 4, 6, 8]) == 5
    assert mean([10]) == 10
    assert mean([1, 2, 3]) == 2


def test_mean_skewed_data():
    data = [1, 2, 2, 3, 100]
    assert mean(data) == 21.6


def test_median():
    assert median([3, 1, 5]) == 3
    assert median([2, 4, 6, 8]) == 5
    assert median([10]) == 10


def test_median_unsorted_data():
    assert median([9, 1, 5, 3, 7]) == 5


def test_mode():
    assert mode([1, 2, 2, 3, 4]) == [2]
    assert mode([1, 2, 2, 3, 3, 4]) == [2, 3]
    assert mode([5, 5, 5, 5]) == [5]
    assert mode([7]) == [7]


def test_mode_returns_sorted_tied_values():
    assert mode([4, 2, 4, 2, 3]) == [2, 4]

def test_mean_with_negative_and_decimal_values():
    assert mean([-2, 0, 2]) == 0
    assert mean([1.5, 2.5, 3.0]) == 7 / 3


def test_mean_floating_point_accuracy():
    assert mean([1e16, 1, -1e16]) == 1 / 3


def test_median_with_negative_values():
    assert median([-5, -1, 3, 7]) == 1


def test_functions_do_not_modify_input():
    data = [4, 1, 3, 2]
    original = data.copy()

    mean(data)
    median(data)
    mode(data)

    assert data == original