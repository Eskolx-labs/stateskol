"""Runnable demonstration of Welford's three formulas."""

from stateskol.welford_robel import (
    welford,
    welford_moments,
    welford_products,
)


def show(title, result):
    print("\n" + title)
    print("-" * len(title))
    for key, value in result.items():
        print(f"{key}: {value}")


def main():
    # Formula I: corrected sum of squares and sample variance.
    study_hours = [10, 20, 30, 40, 50]
    show("FORMULA I - VARIANCE", welford(study_hours))

    # Formula II: corrected sum of products and sample covariance.
    x = [1, 2, 3]
    y = [50, 60, 70]
    show("FORMULA II - COVARIANCE", welford_products(x, y))

    # Formula III: corrected sums of third and fourth powers.
    values = [1, 2, 3]
    show("FORMULA III - HIGHER-ORDER SUMS",
         welford_moments(values, max_order=4))

    # Missing-value demonstration.
    show("MISSING-VALUE EXAMPLE",
         welford([10, 20, None, 30, float("nan"), 40]))


if __name__ == "__main__":
    main()
