"""Week 1 tests for Welasma's counting and boundary-case pack.

Standard library only. The suite is unittest based and also runs under
pytest. From the repository root:

    python -m unittest discover -s tests -v

The canonical boundary inputs come from the shared pack in
``stateskol.descriptive``, so the rest of the team can reuse the same cases
without copying magic numbers.
"""

import math
import unittest
from decimal import Decimal
from fractions import Fraction

from stateskol import descriptive
from stateskol.descriptive import (
    ALL_MISSING,
    BOUNDARY_CASES,
    CONSTANT_VALUES,
    EMPTY_INPUT,
    INVALID_BOUNDARY_CASES,
    INVALID_VALUES,
    MISSING_VALUES,
    MissingPolicy,
    SINGLE_VALUE,
    TIED_VALUES,
    VALID_BOUNDARY_CASES,
    apply_missing,
    boundary_case_names,
    clean_values,
    count,
    count_missing,
    data_range,
    frequency_table,
    get_boundary_case,
    is_missing,
    max_,
    min_,
    prepare_data,
    require_nonempty,
    to_float_list,
)


class OneShot:
    """Iterable that raises if it is iterated more than once."""

    def __init__(self, values):
        self._values = tuple(values)
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("iterable was consumed more than once")
        return iter(self._values)


class TestInputContract(unittest.TestCase):
    def test_ints_become_floats(self):
        self.assertEqual(to_float_list([1, 2, 3]), [1.0, 2.0, 3.0])

    def test_fraction_and_decimal_are_accepted(self):
        self.assertEqual(
            to_float_list([Fraction(1, 2), Decimal("1.5")]),
            [0.5, 1.5],
        )

    def test_none_and_nan_pass_through(self):
        contracted = to_float_list([None, float("nan")])
        self.assertIsNone(contracted[0])
        self.assertTrue(math.isnan(contracted[1]))

    def test_decimal_nan_is_missing(self):
        contracted = to_float_list([Decimal("NaN")])
        self.assertTrue(math.isnan(contracted[0]))

    def test_empty_input_is_allowed(self):
        self.assertEqual(to_float_list([]), [])

    def test_strings_bytes_and_non_iterables_fail(self):
        for bad in ("123", b"123", bytearray(b"123"), 5, None):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    to_float_list(bad)

    def test_bools_fail(self):
        for bad in (True, False):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    to_float_list([bad])

    def test_non_numeric_elements_fail(self):
        for bad in ("two", 2 + 3j, object()):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    to_float_list([1, bad, 3])

    def test_infinities_fail(self):
        for bad in (
            math.inf,
            -math.inf,
            Decimal("Infinity"),
            Decimal("-Infinity"),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    to_float_list([1, bad])

    def test_huge_fraction_fails_as_value_error(self):
        with self.assertRaises(ValueError):
            to_float_list([Fraction(10 ** 400, 1)])


class TestMissingPolicy(unittest.TestCase):
    def test_drop_removes_none_and_nan(self):
        clean, dropped = apply_missing(to_float_list([1, None, float("nan"), 4]))
        self.assertEqual(clean, [1.0, 4.0])
        self.assertEqual(dropped, 2)

    def test_raise_stops_on_none(self):
        with self.assertRaises(ValueError):
            apply_missing(to_float_list([1, None]), "raise")

    def test_raise_stops_on_nan(self):
        with self.assertRaises(ValueError):
            apply_missing(to_float_list([1, float("nan")]), MissingPolicy.RAISE)

    def test_enum_and_string_policies_agree(self):
        self.assertEqual(
            count([1, None, 2], MissingPolicy.DROP),
            count([1, None, 2], "drop"),
        )
        with self.assertRaises(ValueError):
            count([1, None, 2], MissingPolicy.RAISE)

    def test_unknown_policy_fails_before_iteration(self):
        for fn in (
            count,
            min_,
            max_,
            data_range,
            frequency_table,
            clean_values,
            prepare_data,
        ):
            with self.subTest(fn=fn.__name__):
                data = OneShot([1, 2, 3])
                with self.assertRaises(ValueError):
                    fn(data, policy="explode")
                self.assertEqual(data.iterations, 0)

    def test_apply_missing_also_validates_before_iteration(self):
        data = OneShot([1.0, None])
        with self.assertRaises(ValueError):
            apply_missing(data, policy="explode")
        self.assertEqual(data.iterations, 0)

    def test_apply_missing_rejects_uncontracted_values(self):
        with self.assertRaises(TypeError):
            apply_missing([1, 2, 3])

    def test_apply_missing_empty(self):
        self.assertEqual(apply_missing([]), ([], 0))


class TestBoundaryPack(unittest.TestCase):
    def test_required_cases_are_present(self):
        names = boundary_case_names()
        for required in ("empty", "single", "constant", "tied", "invalid"):
            self.assertIn(required, names)

    def test_case_names_are_unique(self):
        names = boundary_case_names()
        self.assertEqual(len(names), len(set(names)))

    def test_pack_is_the_valid_and_invalid_cases(self):
        self.assertEqual(
            BOUNDARY_CASES,
            VALID_BOUNDARY_CASES + INVALID_BOUNDARY_CASES,
        )
        self.assertIn(INVALID_VALUES, INVALID_BOUNDARY_CASES)
        self.assertNotIn(INVALID_VALUES, VALID_BOUNDARY_CASES)

    def test_get_boundary_case(self):
        self.assertIs(get_boundary_case("empty"), EMPTY_INPUT)
        self.assertIs(get_boundary_case("single"), SINGLE_VALUE)
        self.assertIs(get_boundary_case("constant"), CONSTANT_VALUES)
        self.assertIs(get_boundary_case("tied"), TIED_VALUES)
        self.assertIs(get_boundary_case("missing"), MISSING_VALUES)
        self.assertIs(get_boundary_case("all-missing"), ALL_MISSING)
        self.assertIs(get_boundary_case("invalid"), INVALID_VALUES)

    def test_unknown_case_raises_key_error(self):
        with self.assertRaises(KeyError):
            get_boundary_case("nope")

    def test_is_missing(self):
        self.assertTrue(is_missing(None))
        self.assertTrue(is_missing(float("nan")))
        self.assertFalse(is_missing(0.0))
        self.assertFalse(is_missing(False))
        self.assertFalse(is_missing("two"))

    def test_count_missing(self):
        self.assertEqual(count_missing([1, None, float("nan"), 4]), 2)
        self.assertEqual(count_missing([]), 0)

    def test_prepare_data_and_clean_values(self):
        self.assertEqual(prepare_data([1, None, 2]), ([1.0, 2.0], 1))
        self.assertEqual(clean_values([1, None, 2]), [1.0, 2.0])


class TestEmptyInput(unittest.TestCase):
    def test_count_is_zero(self):
        self.assertEqual(count(EMPTY_INPUT.data), 0)

    def test_frequency_table_is_empty(self):
        self.assertEqual(frequency_table(EMPTY_INPUT.data), {})

    def test_extremes_raise_value_error(self):
        for fn in (min_, max_, data_range):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(ValueError):
                    fn(EMPTY_INPUT.data)


class TestSingleValue(unittest.TestCase):
    def test_count(self):
        self.assertEqual(count(SINGLE_VALUE.data), 1)

    def test_extremes(self):
        self.assertEqual(min_(SINGLE_VALUE.data), 7.0)
        self.assertEqual(max_(SINGLE_VALUE.data), 7.0)
        self.assertEqual(data_range(SINGLE_VALUE.data), 0.0)

    def test_frequency_table(self):
        self.assertEqual(frequency_table(SINGLE_VALUE.data), {7.0: 1})


class TestConstantValues(unittest.TestCase):
    def test_count(self):
        self.assertEqual(count(CONSTANT_VALUES.data), 4)

    def test_extremes(self):
        self.assertEqual(min_(CONSTANT_VALUES.data), 4.0)
        self.assertEqual(max_(CONSTANT_VALUES.data), 4.0)
        self.assertEqual(data_range(CONSTANT_VALUES.data), 0.0)

    def test_frequency_table(self):
        self.assertEqual(frequency_table(CONSTANT_VALUES.data), {4.0: 4})


class TestTiedValues(unittest.TestCase):
    def test_count(self):
        self.assertEqual(count(TIED_VALUES.data), 5)

    def test_extremes(self):
        self.assertEqual(min_(TIED_VALUES.data), 1.0)
        self.assertEqual(max_(TIED_VALUES.data), 3.0)
        self.assertEqual(data_range(TIED_VALUES.data), 2.0)

    def test_frequency_table_keeps_every_tie(self):
        self.assertEqual(
            frequency_table(TIED_VALUES.data),
            {1.0: 1, 2.0: 2, 3.0: 2},
        )


class TestMissingValues(unittest.TestCase):
    def test_default_drop(self):
        self.assertEqual(count(MISSING_VALUES.data), 2)
        self.assertEqual(min_(MISSING_VALUES.data), 1.0)
        self.assertEqual(max_(MISSING_VALUES.data), 4.0)
        self.assertEqual(data_range(MISSING_VALUES.data), 3.0)
        self.assertEqual(
            frequency_table(MISSING_VALUES.data),
            {1.0: 1, 4.0: 1},
        )

    def test_raise_policy(self):
        for fn in (count, min_, max_, data_range, frequency_table):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(ValueError):
                    fn(MISSING_VALUES.data, policy="raise")


class TestAllMissing(unittest.TestCase):
    def test_count_is_zero(self):
        self.assertEqual(count(ALL_MISSING.data), 0)

    def test_frequency_table_is_empty(self):
        self.assertEqual(frequency_table(ALL_MISSING.data), {})

    def test_extremes_raise(self):
        for fn in (min_, max_, data_range):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(ValueError):
                    fn(ALL_MISSING.data)

    def test_raise_policy(self):
        with self.assertRaises(ValueError):
            count(ALL_MISSING.data, policy="raise")


class TestInvalidValues(unittest.TestCase):
    def test_every_public_function_raises_type_error(self):
        for fn in (count, min_, max_, data_range, frequency_table):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(TypeError):
                    fn(INVALID_VALUES.data)

    def test_helpers_raise_type_error(self):
        for fn in (to_float_list, count_missing, clean_values, prepare_data):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(TypeError):
                    fn(INVALID_VALUES.data)


class TestCount(unittest.TestCase):
    def test_hand_checked(self):
        self.assertEqual(count([4, 8, 6, 5, 3, 7]), 6)

    def test_empty(self):
        self.assertEqual(count([]), 0)

    def test_missing_drop(self):
        self.assertEqual(count([1, None, float("nan"), 4]), 2)

    def test_raise(self):
        with self.assertRaises(ValueError):
            count([1, None], policy="raise")

    def test_invalid(self):
        with self.assertRaises(TypeError):
            count([1, "two"])


class TestExtremes(unittest.TestCase):
    def test_hand_checked(self):
        data = [4, 8, 6, 5, 3, 7]
        self.assertEqual(min_(data), 3.0)
        self.assertEqual(max_(data), 8.0)
        self.assertEqual(data_range(data), 5.0)

    def test_negative_values(self):
        data = [-5, -1, -3]
        self.assertEqual(min_(data), -5.0)
        self.assertEqual(max_(data), -1.0)
        self.assertEqual(data_range(data), 4.0)

    def test_float_values(self):
        data = [1.5, 2.5]
        self.assertEqual(min_(data), 1.5)
        self.assertEqual(max_(data), 2.5)
        self.assertEqual(data_range(data), 1.0)

    def test_missing_drop(self):
        data = [4, None, 8, float("nan"), 6]
        self.assertEqual(min_(data), 4.0)
        self.assertEqual(max_(data), 8.0)
        self.assertEqual(data_range(data), 4.0)

    def test_raise(self):
        for fn in (min_, max_, data_range):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(ValueError):
                    fn([1, None], policy="raise")

    def test_invalid(self):
        for fn in (min_, max_, data_range):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(TypeError):
                    fn([1, "two"])


class TestFrequencyTable(unittest.TestCase):
    def test_hand_checked(self):
        self.assertEqual(
            frequency_table([4, 8, 6, 5, 3, 7]),
            {3.0: 1, 4.0: 1, 5.0: 1, 6.0: 1, 7.0: 1, 8.0: 1},
        )

    def test_empty(self):
        self.assertEqual(frequency_table([]), {})

    def test_single(self):
        self.assertEqual(frequency_table([7]), {7.0: 1})

    def test_constant(self):
        self.assertEqual(frequency_table([4, 4, 4]), {4.0: 3})

    def test_tied(self):
        self.assertEqual(
            frequency_table([1, 2, 2, 3, 3]),
            {1.0: 1, 2.0: 2, 3.0: 2},
        )

    def test_missing_drop(self):
        self.assertEqual(
            frequency_table([1, None, 2, float("nan"), 2]),
            {1.0: 1, 2.0: 2},
        )

    def test_raise(self):
        with self.assertRaises(ValueError):
            frequency_table([1, None], policy="raise")

    def test_invalid(self):
        with self.assertRaises(TypeError):
            frequency_table([1, "two"])

    def test_keys_are_sorted(self):
        self.assertEqual(
            list(frequency_table([3, 1, 2, 1])),
            [1.0, 2.0, 3.0],
        )

    def test_int_and_float_share_a_key(self):
        self.assertEqual(frequency_table([1, 1.0]), {1.0: 2})

    def test_negative_zero_and_zero_share_a_key(self):
        self.assertEqual(frequency_table([0.0, -0.0]), {0.0: 2})


class TestOneShotIterators(unittest.TestCase):
    def test_one_shot_iterator(self):
        cases = (
            (count, 3),
            (min_, 1.0),
            (max_, 3.0),
            (data_range, 2.0),
            (frequency_table, {1.0: 1, 2.0: 1, 3.0: 1}),
        )
        for fn, expected in cases:
            with self.subTest(fn=fn.__name__):
                data = OneShot([1, 2, 3])
                self.assertEqual(fn(data), expected)
                self.assertEqual(data.iterations, 1)

    def test_one_shot_iterator_with_missing_values(self):
        data = OneShot([1, None, float("nan"), 4])
        self.assertEqual(count(data), 2)
        self.assertEqual(data.iterations, 1)

    def test_one_shot_iterator_for_helpers(self):
        for fn, expected in (
            (count_missing, 1),
            (clean_values, [1.0, 2.0]),
            (prepare_data, ([1.0, 2.0], 1)),
        ):
            with self.subTest(fn=fn.__name__):
                data = OneShot([1, None, 2])
                self.assertEqual(fn(data), expected)
                self.assertEqual(data.iterations, 1)


class TestAliases(unittest.TestCase):
    def test_prompt_names_point_at_the_same_functions(self):
        self.assertIs(descriptive.min, descriptive.min_)
        self.assertIs(descriptive.max, descriptive.max_)
        self.assertIs(descriptive.range, descriptive.data_range)

    def test_prompt_names_are_importable(self):
        from stateskol.descriptive import max as max_fn
        from stateskol.descriptive import min as min_fn
        from stateskol.descriptive import range as range_fn

        self.assertEqual(min_fn([3, 1, 2]), 1.0)
        self.assertEqual(max_fn([3, 1, 2]), 3.0)
        self.assertEqual(range_fn([3, 1, 2]), 2.0)

    def test_short_names_do_not_shadow_builtins_in_module_globals(self):
        for name in ("min", "max", "range"):
            with self.subTest(name=name):
                self.assertNotIn(name, descriptive.__dict__)
                self.assertIn(name, dir(descriptive))

    def test_descriptive_aliases(self):
        self.assertIs(descriptive.minimum, descriptive.min_)
        self.assertIs(descriptive.maximum, descriptive.max_)
        self.assertIs(descriptive.value_range, descriptive.data_range)


class TestDocumentedBoundaryTable(unittest.TestCase):
    def test_every_valid_case_has_one_answer(self):
        expected = {
            "empty": (0, {}, True),
            "single": (1, {7.0: 1}, False),
            "constant": (4, {4.0: 4}, False),
            "tied": (5, {1.0: 1, 2.0: 2, 3.0: 2}, False),
            "missing": (2, {1.0: 1, 4.0: 1}, False),
            "all-missing": (0, {}, True),
        }
        for case in VALID_BOUNDARY_CASES:
            with self.subTest(case=case.name):
                expected_count, expected_table, empty_after_policy = expected[
                    case.name
                ]
                self.assertEqual(count(case.data), expected_count)
                self.assertEqual(frequency_table(case.data), expected_table)
                if empty_after_policy:
                    for fn in (min_, max_, data_range):
                        with self.assertRaises(ValueError):
                            fn(case.data)
                else:
                    cleaned = clean_values(case.data)
                    self.assertEqual(min_(case.data), min(cleaned))
                    self.assertEqual(max_(case.data), max(cleaned))
                    self.assertEqual(
                        data_range(case.data),
                        max(cleaned) - min(cleaned),
                    )


class TestRequireNonempty(unittest.TestCase):
    def test_nonempty_is_returned(self):
        values = [1, 2, 3]
        self.assertIs(require_nonempty(values), values)

    def test_empty_raises_value_error(self):
        with self.assertRaises(ValueError):
            require_nonempty([])

    def test_name_appears_in_message(self):
        with self.assertRaisesRegex(ValueError, "sample"):
            require_nonempty([], name="sample")


if __name__ == "__main__":
    unittest.main()
