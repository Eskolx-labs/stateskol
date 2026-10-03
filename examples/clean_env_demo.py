from stateskol.descriptive import welford


def main():
    data = [2, 4, 6, 8, 10]

    result = welford(data)

    print("Input:", data)
    print("Count:", result["count"])
    print("Mean:", result["mean"])
    print("Sample variance:", result["variance"])
    print("Sample standard deviation:", result["std_dev"])
    print("Missing values:", result["missing_count"])


if __name__ == "__main__":
    main()