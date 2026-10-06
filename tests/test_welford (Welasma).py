"""
Tests for welford(data).
"""

import importlib.util
import math
from pathlib import Path

import pytest


# Path to the source file, matching the real layout on disk:
#   stateskol-welford\src\stateskol\welford (Welasma).py
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_WELFORD_FILE = _ROOT / "src" / "stateskol" / "welford (Welasma).py"

if not _WELFORD_FILE.is_file():
    raise FileNotFoundError(f"Cannot find welford file at: {_WELFORD_FILE}")

_spec = importlib.util.spec_from_file_location("welford_module", _WELFORD_FILE)
_welford_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_welford_module)
welford = _welford_module.welford


def test_normal_case():
    count, mean, variance, std_dev = welford([5, 7, 4, 10])
    assert count == 4
    assert mean == 6.5
    assert variance == 7.0
    assert std_dev == pytest.approx(math.sqrt(7.0))


def test_single_value_raises():
    with pytest.raises(ValueError):
        welford([5])


def test_empty_data_raises():
    with pytest.raises(ValueError):
        welford([])


def test_constant_values_zero_variance():
    count, mean, variance, std_dev = welford([5, 5, 5, 5])
    assert count == 4
    assert mean == 5.0
    assert variance == 0.0
    assert std_dev == 0.0


def test_none_values_are_missing():
    count, mean, variance, std_dev = welford([5, None, 7, None, 4, 10])
    assert count == 4
    assert mean == 6.5
    assert variance == 7.0
    assert std_dev == pytest.approx(math.sqrt(7.0))


def test_nan_values_are_missing():
    data = [5, float("nan"), 7, 4, 10]
    count, mean, variance, std_dev = welford(data)
    assert count == 4
    assert mean == 6.5
    assert variance == 7.0
    assert std_dev == pytest.approx(math.sqrt(7.0))


def test_invalid_value_raises_type_error():
    with pytest.raises(TypeError):
        welford([5, "hello", 7])


def test_numerical_stability_large_offset():
    offset = 1e12
    base = [1.0, 2.0, 3.0, 4.0, 5.0]
    shifted = [offset + x for x in base]

    _, _, var_base, _ = welford(base)
    _, _, var_shifted, _ = welford(shifted)

    assert var_shifted == pytest.approx(var_base, rel=1e-12, abs=1e-12)
    assert var_shifted == pytest.approx(2.5, rel=1e-12, abs=1e-12)