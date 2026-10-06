from src.stateskol.welford_yanetDereje import welford

if __name__ == "__main__":
    example_data = [4.2, 5.8, 7.1, 3.9, 9.4]
    result = welford(example_data)
    print(f"Dataset under evaluation: {example_data}")
    print(f"Calculated Parameters -> Count: {result[0]}, Mean: {result[1]}, Sample Variance: {result[2]}, Std Dev: {result[3]}")
