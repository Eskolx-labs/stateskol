
"""Tests for Robel's descriptive statistics functions."""

import pytest
from decimal import Decimal
from fractions import Fraction
from stateskol.descriptive import (
    EmptyDataError,
    MissingReport,
       DataAudit,
        audit,
    count,
    data_range,
    frequency_table,
    max as data_max,
    maximum,
    min as data_min,
    missing_report,
    range as old_data_range,
)


# Shared boundary cases.
BOUNDARY_CASES = [
    ("single value", [8], 1, 8, 8, 0),
    ("constant values", [5, 5, 5, 5], 4, 5, 5, 0),
    ("tied values", [2, 4, 2, 4, 2], 5, 2, 4, 2),
]


@pytest.mark.parametrize(
    "name,data,expected_count,expected_min,expected_max,expected_range",
    BOUNDARY_CASES,
)
def test_boundary_cases(
    name, data, expected_count, expected_min, expected_max,
    expected_range
):
    assert count(data) == expected_count
    assert data_min(data) == expected_min
    assert data_max(data) == expected_max
    assert data_range(data) == expected_range


def test_count_normal_data():
    assert count([10, 20, 30, 40]) == 4


def test_min_normal_data():
    assert data_min([10, 20, 30, 40]) == 10


def test_max_normal_data():
    assert data_max([10, 20, 30, 40]) == 40


def test_range_normal_data():
    assert data_range([10, 20, 30, 40]) == 30


def test_frequency_table_normal_data():
    assert frequency_table([4, 2, 7, 2, 5, 4, 2]) == {
        2: 3,
        4: 2,
        5: 1,
        7: 1,
    }


def test_frequency_table_is_sorted():
    result = frequency_table([7, 2, 5, 2, 4])
    assert list(result.keys()) == [2, 4, 5, 7]


# Empty input.
def test_count_empty_data():
    assert count([]) == 0


@pytest.mark.parametrize(
    "function",
    [data_min, data_max, data_range, frequency_table],
)
def test_other_functions_reject_empty_data(function):
    with pytest.raises(EmptyDataError):
        function([])


# Invalid input types.
@pytest.mark.parametrize(
    "invalid_value",
    ["hello", True, complex(2, 3)],
)
def test_invalid_values_raise_type_error(invalid_value):
    functions = [
        count, data_min, data_max, data_range, frequency_table
    ]

    for function in functions:
        with pytest.raises(TypeError):
            function([1, invalid_value, 3])


# Infinite values.
@pytest.mark.parametrize(
    "infinite_value",
    [float("inf"), float("-inf")],
)
def test_infinite_values_raise_value_error(infinite_value):
    functions = [
        count, data_min, data_max, data_range, frequency_table
    ]

    for function in functions:
        with pytest.raises(ValueError):
            function([1, infinite_value, 3])


# Missing values under the default drop policy.
def test_count_drops_none_and_nan():
    with pytest.warns(UserWarning, match="Dropped 2"):
        assert count([1, None, 2, float("nan")]) == 2


def test_frequency_table_drops_missing_values():
    with pytest.warns(UserWarning):
        result = frequency_table([2, None, 2, float("nan"), 3])

    assert result == {2: 2, 3: 1}


def test_all_missing_data_raises_for_minimum():
    with pytest.warns(UserWarning):
        with pytest.raises(EmptyDataError):
            data_min([None, float("nan")])


def test_count_all_missing_data():
    with pytest.warns(UserWarning):
        assert count([None, float("nan")]) == 0


# Integer precision boundary.
def test_integer_at_precision_limit_is_accepted():
    assert count([2**53]) == 1


def test_integer_above_precision_limit_is_rejected():
    with pytest.raises(ValueError, match="2\\*\\*53"):
        count([2**53 + 1])


def test_negative_integer_above_precision_limit_is_rejected():
    with pytest.raises(ValueError, match="2\\*\\*53"):
        count([-(2**53 + 1)])


# Input must not be modified.
def test_functions_do_not_modify_original_data():
    original = [4, 2, 7, 2, 5]
    original_copy = original.copy()

    count(original)
    data_min(original)
    data_max(original)
    data_range(original)
    frequency_table(original)

    assert original == original_copy


# Core B: maximum and data_range.
def test_maximum_normal_data():
    assert maximum([10, 20, 30, 40]) == 40


def test_data_range_normal_data():
    assert data_range([10, 20, 30, 40]) == 30


def test_maximum_single_value():
    assert maximum([8]) == 8


def test_data_range_constant_values():
    assert data_range([5, 5, 5, 5]) == 0


def test_maximum_with_tied_values():
    assert maximum([2, 4, 2, 4, 2]) == 4


def test_data_range_with_tied_values():
    assert data_range([2, 4, 2, 4, 2]) == 2


def test_maximum_empty_data():
    with pytest.raises(EmptyDataError):
        maximum([])


def test_data_range_empty_data():
    with pytest.raises(EmptyDataError):
        data_range([])


# Core B: MissingReport.
def test_missing_report_with_none_and_nan():
    result = missing_report([10, None, 20, float("nan"), 30])

    assert result == MissingReport(
        n_total=5,
        n_present=3,
        n_missing=2,
        missing_positions=(1, 3),
    )


def test_missing_report_without_missing_values():
    result = missing_report([10, 20, 30])

    assert result == MissingReport(
        n_total=3,
        n_present=3,
        n_missing=0,
        missing_positions=(),
    )


def test_missing_report_empty_data():
    result = missing_report([])

    assert result == MissingReport(
        n_total=0,
        n_present=0,
        n_missing=0,
        missing_positions=(),
    )


def test_missing_report_all_missing():
    result = missing_report([None, float("nan"), None])

    assert result == MissingReport(
        n_total=3,
        n_present=0,
        n_missing=3,
        missing_positions=(0, 1, 2),
    )


def test_missing_report_accepts_generator():
    data = (value for value in [10, None, 20])

    result = missing_report(data)

    assert result.n_total == 3
    assert result.n_present == 2
    assert result.n_missing == 1
    assert result.missing_positions == (1,)


# Missingness policy tests.
def test_count_drop_policy():
    with pytest.warns(UserWarning, match="Dropped 1"):
        assert count([10, None, 20], policy="drop") == 2


def test_count_strict_policy_rejects_none():
    with pytest.raises(ValueError, match="Missing observations"):
        count([10, None, 20], policy="strict")


def test_count_strict_policy_rejects_nan():
    with pytest.raises(ValueError, match="Missing observations"):
        count([10, float("nan"), 20], policy="strict")


def test_count_strict_policy_accepts_complete_data():
    assert count([10, 20, 30], policy="strict") == 3


def test_maximum_strict_policy():
    assert maximum([10, 20, 30], policy="strict") == 30


def test_data_range_strict_policy():
    assert data_range([10, 20, 30], policy="strict") == 20


def test_frequency_table_strict_policy_rejects_missing():
    with pytest.raises(ValueError, match="Missing observations"):
        frequency_table([2, None, 3], policy="strict")


def test_invalid_missingness_policy():
    with pytest.raises(ValueError, match="Policy"):
        count([10, 20], policy="ignore")


def test_missing_report_strict_policy_rejects_missing():
    with pytest.raises(ValueError, match="Missing observations"):
        missing_report([10, None, 20], policy="strict")


def test_missing_report_validates_invalid_values():
    with pytest.raises(TypeError):
        missing_report([10, "invalid", 20])


def test_missing_report_rejects_infinity():
    with pytest.raises(ValueError, match="Infinite"):
        missing_report([10, float("inf")])


def test_missing_report_does_not_warn_when_reporting():
    result = missing_report([10, None, 20])
    assert result.n_missing == 1


def test_data_range_wrapper_matches_original_range():
    assert data_range([3, 8, 10]) == old_data_range([3, 8, 10])


# Generator behavior.
def test_count_accepts_generator():
    data = (value for value in [1, 2, 3])
    assert count(data) == 3


def test_generator_is_consumed_only_once():
    data = (value for value in [1, None, 3])

    with pytest.warns(UserWarning):
        result = count(data)

    assert result == 2
    assert list(data) == []


def test_decimal_values_are_rejected():
    with pytest.raises(TypeError):
        maximum([1, Decimal("2.5"), 3])


def test_fraction_values_are_rejected():
    with pytest.raises(TypeError):
        maximum([1, Fraction(1, 2), 3])


def test_audit_reports_complete_dataset_summary():
    data = [120, 150, None, 180, 200, float("nan")]

    report = audit(data)

    assert isinstance(report, DataAudit)
    assert report.n_total == 6
    assert report.n_present == 4
    assert report.n_missing == 2
    assert report.missing_positions == (2, 5)
    assert report.policy == "drop"
    assert report.assumption == "Unknown"
    assert report.minimum == 120
    assert report.maximum == 200
    assert report.data_range == 80
    assert report.input_types == ("int", "NoneType", "float")
    assert "Audited 6 observations" in report.summary

def test_audit_with_no_missing_values():
    data = [10, 20, 30, 40]

    report = audit(data)

    assert report.n_total == 4
    assert report.n_present == 4
    assert report.n_missing == 0
    assert report.missing_positions == ()
    assert report.minimum == 10
    assert report.maximum == 40
    assert report.data_range == 30
    assert report.policy == "drop"
    assert report.assumption == "No missing observations; mechanism not assessed"

def test_audit_with_empty_dataset():
    report = audit([])

    assert report.n_total == 0
    assert report.n_present == 0
    assert report.n_missing == 0
    assert report.missing_positions == ()
    assert report.minimum is None
    assert report.maximum is None
    assert report.data_range is None
    assert report.input_types == ()

def test_audit_with_all_missing_values():
    data = [None, float("nan"), None]

    report = audit(data)

    assert report.n_total == 3
    assert report.n_present == 0
    assert report.n_missing == 3
    assert report.missing_positions == (0, 1, 2)
    assert report.minimum is None
    assert report.maximum is None
    assert report.data_range is None
    assert report.assumption == "Unknown"

def test_audit_strict_policy_rejects_missing_values():
    data = [10, None, 20]

    with pytest.raises(ValueError, match="Missing observations"):
        audit(data, policy="strict")

def test_audit_rejects_invalid_policy():
    with pytest.raises(ValueError, match="Policy must be either"):
        audit([10, 20, 30], policy="impute")

def test_audit_consumes_generator_once():
    data = (value for value in [10, None, 20, 30])

    report = audit(data)

    assert report.n_total == 4
    assert report.n_present == 3
    assert report.n_missing == 1
    assert report.missing_positions == (1,)

    # The generator has already been consumed.
    assert list(data) == []

def test_audit_rejects_unsupported_input_types():
    invalid_values = [
        True,
        "100",
        Decimal("10.5"),
        Fraction(1, 2),
    ]

    for value in invalid_values:
        with pytest.raises(TypeError):
            audit([10, value, 20])


def test_audit_rejects_infinite_and_oversized_values():
    invalid_values = [
        float("inf"),
        float("-inf"),
        2**53 + 1,
    ]

    for value in invalid_values:
        with pytest.raises(ValueError):
            audit([10, value, 20])

def test_audit_strict_policy_accepts_complete_data():
    data = [10, 20, 30, 40]

    report = audit(data, policy="strict")

    assert report.policy == "strict"
    assert report.n_total == 4
    assert report.n_present == 4
    assert report.n_missing == 0
    assert report.minimum == 10
    assert report.maximum == 40
    assert report.data_range == 30

def test_audit_records_caller_supplied_missingness_mechanism():
    report = audit(
        [10, 20, None, 30],
        missingness_mechanism="MAR",
    )

    assert report.missingness_mechanism == "MAR"
    assert "mechanism=MAR" in report.summary

@pytest.mark.parametrize("mechanism", ["MCAR", "MAR", "MNAR"])
def test_audit_accepts_valid_missingness_mechanisms(mechanism):
    report = audit([10, 20, None], missingness_mechanism=mechanism)

    assert report.missingness_mechanism == mechanism


def test_audit_rejects_invalid_missingness_mechanism():
    with pytest.raises(ValueError, match="Missingness mechanism"):
        audit([10, 20, None], missingness_mechanism="UNKNOWN_TYPE")
