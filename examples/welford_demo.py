"""Runnable standard-library demonstration of Welford's algorithm."""

from stateskol.welford import WelfordAccumulator


def main():
    values = [2, 4, 6]
    accumulator = WelfordAccumulator()

    print("Hand-worked example:", values)
    for value in values:
        accumulator.update(value)
        print(
            f"After {value}: count={accumulator.count}, "
            f"mean={accumulator.mean:.6f}"
        )

    print(f"Population variance: {accumulator.variance():.6f}")
    print(f"Sample variance:     {accumulator.variance(ddof=1):.6f}")
    print(
        "Population std dev: "
        f"{accumulator.standard_deviation():.6f}"
    )

    large_values = [1e12 + i for i in range(1000)]
    stable = WelfordAccumulator()
    for value in large_values:
        stable.update(value)

    print("\nLarge values with small differences:")
    print(f"Count: {stable.count}")
    print(f"Mean: {stable.mean:.6f}")
    print(f"Population variance: {stable.variance():.6f}")
    print("Expected population variance: 83333.250000")


if __name__ == "__main__":
    main()
