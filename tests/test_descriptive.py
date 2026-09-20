"""Week 1 tests. Stdlib only, no numpy, no scipy.

The suite must run on bare Python plus pytest. Expected values below are
hand computed or taken from Ross, never from a library. Comparisons against
trusted libraries live in examples/reference_check.py, which is evidence,
not part of this suite. Ownership is by section, same blocks as descriptive.
"""

import math

import pytest

from stateskol.descriptive import (
    apply_missing,
    count,
    data_range,
    max_,
    min_,
    require_nonempty,
    to_float_list,
)

# ----- Kaleb: contract -----


def test_ints_become_floats():
    assert to_float_list([1, 2, 3]) == [1.0, 2.0, 3.0]


def test_strings_and_bools_fail():
    with pytest.raises(TypeError):
        to_float_list("123")
    with pytest.raises(TypeError):
        to_float_list([1, True, 3])
    with pytest.raises(TypeError):
        to_float_list([1, "two", 3])


def test_infinities_fail():
    with pytest.raises(ValueError):
        to_float_list([1.0, math.inf])


def test_empty_needs_data():
    with pytest.raises(ValueError):
        require_nonempty([])


def test_missing_drop_counts():
    clean, dropped = apply_missing(to_float_list([1, None, float("nan"), 4]))
    assert clean == [1.0, 4.0]
    assert dropped == 2


def test_missing_raise():
    with pytest.raises(ValueError):
        apply_missing(to_float_list([1, None]), "raise")


def test_basics_hand_checked():
    data = [4, 8, 6, 5, 3, 7]
    assert count(data) == 6
    assert min_(data) == 3.0
    assert max_(data) == 8.0
    assert data_range(data) == 5.0


def test_basics_empty_fails():
    with pytest.raises(ValueError):
        min_([])


# ----- Philimon: center -----


@pytest.mark.skip(reason="Philimon implements center in week 1")
def test_mean_hand_checked():
    pass


@pytest.mark.skip(reason="Philimon implements center in week 1")
def test_median_even_count():
    pass


@pytest.mark.skip(reason="Philimon implements center in week 1")
def test_mode_ties():
    pass


# ----- Robel: spread -----


@pytest.mark.skip(reason="Robel implements spread in week 1")
def test_quantile_hand_checked():
    pass


@pytest.mark.skip(reason="Robel implements spread in week 1")
def test_variance_sample_denominator():
    pass


@pytest.mark.skip(reason="Robel implements spread in week 1")
def test_constant_values_zero_spread():
    pass


# ----- Yoseph: tables -----


@pytest.mark.skip(reason="Yoseph implements tables in week 1")
def test_frequency_counts_match_hand_count():
    pass


@pytest.mark.skip(reason="Yoseph implements tables in week 1")
def test_histogram_bins_cover_range():
    pass
