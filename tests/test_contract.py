
"""Contract tests: accepted, rejected, empty, missing, boundary pack."""
import math
from decimal import Decimal
from fractions import Fraction
 
import pytest
 
from stateskol.descriptive import (
    as_numeric, audit, count, data_range, maximum, minimum, missing_report,
)
from stateskol.errors import (
    EmptyDataError, InvalidTypeError, InvalidValueError, MissingDataError,
)
 
NAN = float("nan")
 
 
# ---- accepted ----
def test_int_and_float_accepted():
    assert as_numeric([1, 2.5, -3]) == [1.0, 2.5, -3.0]
 
 
def test_2_to_53_itself_is_accepted():
    assert as_numeric([2**53]) == [float(2**53)]
 
 
# ---- rejected: types ----
@pytest.mark.parametrize("bad", [True, False, "3", b"3", Decimal("1"), Fraction(1, 2), [1], 1j])
def test_wrong_types_rejected(bad):
    with pytest.raises(InvalidTypeError):
        as_numeric([1, bad])
 
 
def test_bare_string_rejected():
    with pytest.raises(InvalidTypeError):
        as_numeric("123")
 
 
def test_non_iterable_rejected():
    with pytest.raises(InvalidTypeError):
        as_numeric(5)
 
 
# ---- rejected: values ----
@pytest.mark.parametrize("bad", [math.inf, -math.inf, 2**53 + 1, -(2**53) - 1])
def test_bad_values_rejected(bad):
    with pytest.raises(InvalidValueError):
        as_numeric([bad])
 
 
# ---- missing ----
def test_missing_dropped_and_positions_recorded():
    data = [1, 2, None, 4, NAN, 6]
    assert as_numeric(data) == [1.0, 2.0, 4.0, 6.0]
    r = missing_report(data)
    assert (r.n_total, r.n_present, r.n_missing, r.positions) == (6, 4, 2, (2, 4))
 
 
def test_strict_raises_on_missing():
    with pytest.raises(MissingDataError):
        as_numeric([1, None], policy="strict")
 
 
def test_strict_passes_when_nothing_missing():
    assert as_numeric([1, 2], policy="strict") == [1.0, 2.0]
 
 
def test_unknown_policy_rejected():
    with pytest.raises(ValueError):
        as_numeric([1], policy="impute")
 
 
# ---- empty and all-missing ----
def test_empty_input():
    assert as_numeric([]) == []
    assert count([]) == 0
    for f in (minimum, maximum, data_range):
        with pytest.raises(EmptyDataError):
            f([])
 
 
def test_all_missing_raises_and_audit_reports():
    data = [None, NAN]
    assert count(data) == 0
    for f in (minimum, maximum, data_range):
        with pytest.raises(EmptyDataError):
            f(data)
    a = audit(data)
    assert (a.n_total, a.n_present, a.n_missing) == (2, 0, 2)
    assert a.minimum is a.maximum is a.data_range is None
 
 
# ---- single value, constant ----
def test_single_value():
    assert (minimum([7]), maximum([7]), data_range([7])) == (7.0, 7.0, 0.0)
 
 
def test_constant():
    assert data_range([3, 3, 3]) == 0.0
 
 
# ---- hand-worked numbers ----
def test_hand_worked_summaries():
    data = [4, 1, None, 9, NAN, 6]   # present: 4, 1, 9, 6
    assert count(data) == 4
    assert minimum(data) == 1.0
    assert maximum(data) == 9.0
    assert data_range(data) == 8.0
 
 
# ---- generator read once ----
def test_generator_consumed_once():
    gen = (x for x in [1, None, 3])
    a = audit(gen)
    assert (a.n_total, a.n_present, a.n_missing) == (3, 2, 1)
    assert list(gen) == []   # nothing left: it was read exactly once
 
 
# ---- audit ----
def test_audit_records_assumption_and_types():
    a = audit([1, 2.5, None])
    assert a.policy == "drop"
    assert "MCAR" in a.assumption and "caller must state" in a.assumption
    assert a.dropped_positions == (2,)
    assert a.types_seen == ("NoneType", "float", "int")
    assert (a.minimum, a.maximum, a.data_range) == (1.0, 2.5, 1.5)
    assert "1 missing" in a.summary and "MCAR" in a.summary

