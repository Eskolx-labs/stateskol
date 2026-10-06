import pytest
from src.stateskol.welford_yanetDereje import welford

def test_hand_worked():
    # Hand Calculations on small dataset [10.0, 20.0, 30.0]
    # Total Count = 3, Mean = 20.0, Sample Variance = 100.0, Std Dev = 10.0
    count, mean, var, std = welford([10.0, 20.0, 30.0])
    assert count == 3
    assert mean == 20.0
    assert var == 100.0
    assert std == 10.0

def test_boundary_cases():
    # Test empty list input
    assert welford([]) == (0, 0.0, 0.0, 0.0)
    
    # Test a single item dataset
    assert welford([5.0]) == (1, 5.0, 0.0, 0.0)
    
    # Test constant values dataset [5.0, 5.0, 5.0]
    count, mean, var, std = welford([5.0, 5.0, 5.0])
    assert var == 0.0

def test_numerical_stability():
    # Extreme values pushing calculation precision boundaries
    huge_data = [1e9 + 1, 1e9 + 2, 1e9 + 3]
    count, mean, var, std = welford(huge_data)
    assert count == 3
    assert mean == 1000000002.0
    assert var == 1.0
