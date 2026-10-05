import importlib.util, math, pathlib
import pytest

_p = pathlib.Path(__file__).resolve().parents[1] / "src" / "stateskol" / "welford (Maria).py"
_s = importlib.util.spec_from_file_location("welford_mod", _p)
_m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
welford = _m.welford


def test_hand_worked():
    # [2,4,4,4,5,5,7,9]: n=8, mean=5, sum sq dev=32, var=32/7
    r = welford([2, 4, 4, 4, 5, 5, 7, 9])
    assert r.count == 8 and r.mean == 5.0
    assert r.variance == pytest.approx(32 / 7)
    assert r.std == pytest.approx(math.sqrt(32 / 7))


def test_empty():
    with pytest.raises(ValueError):
        welford([])


def test_single():
    r = welford([3.5])
    assert (r.count, r.mean, r.variance, r.std) == (1, 3.5, 0.0, 0.0)


def test_constant():
    assert welford([7] * 100).variance == 0.0


def test_missing_dropped_and_counted():
    r = welford([1, None, 3, float("nan")])
    assert r.count == 2 and r.dropped == 2 and r.mean == 2.0


def test_all_missing():
    with pytest.raises(ValueError):
        welford([None, float("nan")])


@pytest.mark.parametrize("bad", ["a", True, [1]])
def test_invalid_type(bad):
    with pytest.raises(TypeError):
        welford([1, bad])


def test_inf():
    with pytest.raises(ValueError):
        welford([1, float("inf")])


def test_stability_large_offset():
    # Naive sum(x^2)/n - mean^2 loses all digits here; Welford does not.
    base = 1e9
    data = [base + d for d in (4, 7, 13, 16)]
    assert welford(data).variance == pytest.approx(30.0, rel=1e-9)
