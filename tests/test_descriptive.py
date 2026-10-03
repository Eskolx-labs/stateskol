import pytest

from stateskol.descriptive import welford


def test_normal_data():
    result = welford([2, 4, 6])

    assert result["count"] == 3
    assert result["mean"] == 4.0
    assert result["variance"] == 4.0
    assert result["std_dev"] == 2.0
    assert result["missing_count"] == 0


def test_missing_values():
    result = welford([2, 4, None, 6])

    assert result["count"] == 3
    assert result["missing_count"] == 1
    assert result["mean"] == 4.0
    assert result["variance"] == 4.0


def test_single_value():
    result = welford([5])

    assert result["count"] == 1
    assert result["mean"] == 5.0
    assert result["variance"] is None
    assert result["std_dev"] is None


def test_constant_values():
    result = welford([5, 5, 5, 5])

    assert result["count"] == 4
    assert result["mean"] == 5.0
    assert result["variance"] == 0.0
    assert result["std_dev"] == 0.0


def test_invalid_value():
    with pytest.raises(ValueError):
        welford([2, "hello", 6])


def test_empty_input():
    with pytest.raises(ValueError):
        welford([])


def test_matches_numpy_sample_variance():
    import numpy as np

    data = [2, 4, 6, 8, 10]

    result = welford(data)
    expected = np.var(data, ddof=1)

    assert result["variance"] == pytest.approx(expected, rel=1e-12, abs=1e-12)

def test_numerical_stability_case():
    import numpy as np

    data = [1000000001, 1000000002, 1000000003]

    result = welford(data)
    expected = np.var(data, ddof=1)

    assert result["mean"] == pytest.approx(1000000002.0)
    assert result["variance"] == pytest.approx(expected, rel=1e-12, abs=1e-12)