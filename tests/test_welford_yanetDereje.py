import pytest
from src.stateskol.welford_yanetDereje import welford

def test_hand_worked():
    # Mandated small test dataset calculated by hand
    # Hand-calculations for: Count=3, Mean=20, Variance=100, StdDev=10
    count, mean, var, std = welford([10, 20, 30])
    assert count == 3
    assert mean == 20.0
    assert var == 100.0
    assert std == 10.0

def test_boundary_cases():
    # Empty inputs
    assert welford([]) == (0, 0.0, 0.0, 0.0)
    # Single items
    assert welford([5.0]) == (1, 5.0, 0.0, 0.0)
    # Constant lists
    count, mean, var, std = welford([7, 7, 7, 7])
    assert var == 0.0

def test_numerical_stability():
    # Dataset pushing calculation precision limits
    huge_data = [1e9 + 1, 1e9 + 2, 1e9 + 3]
    count, mean, var, std = welford(huge_data)
    assert count == 3
    assert mean == 1000000002.0
    assert var == 1.0
