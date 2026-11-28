"""Compare Welford results with NumPy's trusted variance implementation.

Run after installing the project reference extra:
    python -m pip install -e ".[dev,reference]"
    python examples/welford_reference.py

Comparison tolerance: relative 1e-12 and absolute 1e-12.
"""

import numpy as np

from stateskol.welford import WelfordAccumulator


def main():
    datasets = [
        [2, 4, 6],
        [1, 2, 3, 4, 5],
        [10, 10, 10, 10],
        [-5, -2, 0, 3, 8],
        [1.5, 2.5, 3.5, 4.5],
        [1e12 + i for i in range(1000)],
    ]

    for values in datasets:
        accumulator = WelfordAccumulator()
        for value in values:
            accumulator.update(value)

        reference = np.asarray(values, dtype=np.float64)
        np.testing.assert_allclose(
            accumulator.mean, np.mean(reference), rtol=1e-12, atol=1e-12
        )
        np.testing.assert_allclose(
            accumulator.variance(0),
            np.var(reference, ddof=0),
            rtol=1e-12,
            atol=1e-12,
        )
        np.testing.assert_allclose(
            accumulator.variance(1),
            np.var(reference, ddof=1),
            rtol=1e-12,
            atol=1e-12,
        )
        print(
            f"PASS n={len(values)} mean={accumulator.mean:.6f} "
            f"population_variance={accumulator.variance():.6f}"
        )


if __name__ == "__main__":
    main()
