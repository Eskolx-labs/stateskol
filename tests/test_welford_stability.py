from stateskol.welford import WelfordAccumulator


def test_large_values_with_small_differences():
    values = [1e12 + i for i in range(1000)]
    acc = WelfordAccumulator()

    for value in values:
        acc.update(value)

    # Exact population variance for the sequence 0, 1, ..., 999.
    assert abs(acc.variance() - 83333.25) < 1e-4
