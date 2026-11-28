import numpy as np
import pytest

from stateskol.welford import WelfordAccumulator


@pytest.mark.parametrize(
    "values",
    [
        [2, 4, 6],
        [1, 2, 3, 4, 5],
        [10, 10, 10, 10],
        [-5, -2, 0, 3, 8],
        [1.5, 2.5, 3.5, 4.5],
    ],
)
def test_welford_matches_numpy(values):
    acc = WelfordAccumulator()

    for value in values:
        acc.update(value)

    reference = np.asarray(values, dtype=np.float64)

    assert acc.count == len(values)
    assert acc.mean == pytest.approx(
        float(np.mean(reference)), rel=1e-12, abs=1e-12
    )
    assert acc.variance(ddof=0) == pytest.approx(
        float(np.var(reference, ddof=0)), rel=1e-12, abs=1e-12
    )
    assert acc.variance(ddof=1) == pytest.approx(
        float(np.var(reference, ddof=1)), rel=1e-12, abs=1e-12
    )
