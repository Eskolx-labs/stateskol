import numpy as np

from stateskol.descriptive import welford


def main():
    data = [2, 4, 6, 8, 10]

    result = welford(data)
    numpy_variance = np.var(data, ddof=1)

    print("Input:", data)
    print("Welford sample variance:", result["variance"])
    print("NumPy sample variance:", numpy_variance)
    print(
        "Difference:",
        abs(result["variance"] - numpy_variance),
    )


if __name__ == "__main__":
    main()