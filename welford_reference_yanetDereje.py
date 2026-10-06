import numpy as np
from src.stateskol.welford_yanetDereje import welford

def compare_with_numpy():
    test_values = [12.5, 14.8, 18.2, 11.1, 15.6]
    count, mean, var, std = welford(test_values)
    
    np_mean = np.mean(test_values)
    np_var = np.var(test_values, ddof=1)
    
    tolerance_threshold = 1e-9
    assert abs(mean - np_mean) < tolerance_threshold
    assert abs(var - np_var) < tolerance_threshold
    print("Verification successful.")

if __name__ == "__main__":
    compare_with_numpy()
