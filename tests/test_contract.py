"""Tests for the v0.1 data contract.

Every test names the rule it defends, so a failure reads as a sentence about
the contract rather than as a broken assertion. Standard library only.

    python -m pytest tests/test_contract.py -q
"""

import doctest
import unittest
from decimal import Decimal
from fractions import Fraction

import stateskol.descriptive as descriptive
from stateskol.descriptive import ASSUMPTION, POLICIES, as_numeric, count
from stateskol.errors import ContractError, UnknownPolicyError

NAN = float("nan")


class OneShot:
    """An iterable that fails loudly if it is iterated twice."""

    def __init__(self, values):
        self._values = tuple(values)
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("the input was consumed more than once")
        return iter(self._values)


class TestAcceptedInput(unittest.TestCase):
    def test_int_and_float_are_accepted_and_returned_as_floats(self):
        # The only numeric types v0.1 understands. int becomes float so a
        # summary never has to guess what it is adding.
        self.assertEqual(as_numeric([1, 2.5, 3]), [1.0, 2.5, 3.0])

    def test_input_order_is_preserved(self):
        # A reordered list is a different sample. The contract must not sort.
        self.assertEqual(as_numeric([3, 1, 2]), [3.0, 1.0, 2.0])

    def test_negative_and_zero_are_measurements(self):
        self.assertEqual(as_numeric([-2.0, 0, 2]), [-2.0, 0.0, 2.0])

    def test_2_pow_53_is_the_last_int_that_survives_the_conversion(self):
        self.assertEqual(as_numeric([2**53]), [float(2**53)])

    def test_large_finite_float_is_accepted_because_no_conversion_happens(self):
        # The 2**53 rule is about int -> float rounding, not about size.
        # 1e300 is already a float, so the contract has nothing to refuse.
        self.assertEqual(as_numeric([1e300]), [1e300])

    def test_empty_input_gives_an_empty_list_not_an_error(self):
        # An empty file is a finding. It is not a value, and it is not a bug.
        self.assertEqual(as_numeric([]), [])

    def test_count_hand_checked_on_a_small_sample(self):
        self.assertEqual(count([4, 8, 6, 5, 3, 7]), 6)


class TestRejectedInput(unittest.TestCase):
    def assert_refused(self, value, reason):
        with self.assertRaises(ContractError) as caught:
            as_numeric([1, value, 3])
        self.assertIn(reason, str(caught.exception))
        return caught.exception

    def test_bool_is_rejected_because_true_is_an_int_but_not_a_measurement(self):
        self.assert_refused(True, "bool is not a measurement")
        self.assert_refused(False, "bool is not a measurement")

    def test_str_is_rejected_because_the_package_never_coerces(self):
        # "3" is not a number because it looks like one.
        self.assert_refused("3", "str is not accepted and is never coerced")

    def test_bytes_is_rejected_for_the_same_reason_as_str(self):
        self.assert_refused(b"3", "bytes is not accepted and is never coerced")

    def test_complex_is_rejected_because_it_has_no_ordering(self):
        self.assert_refused(3 + 2j, "complex has no ordering")

    def test_decimal_is_rejected_as_the_v01_boundary(self):
        self.assert_refused(Decimal("1.5"), "unsupported type Decimal")

    def test_fraction_is_rejected_as_the_v01_boundary(self):
        self.assert_refused(Fraction(1, 2), "unsupported type Fraction")

    def test_inf_is_rejected_as_a_data_error_not_a_large_number(self):
        self.assert_refused(float("inf"), "infinite observation")

    def test_minus_inf_is_rejected_as_a_data_error(self):
        self.assert_refused(float("-inf"), "infinite observation")

    def test_int_above_2_pow_53_is_rejected_because_float_would_round_it(self):
        err = self.assert_refused(2**53 + 1, "abs(n) > 2**53")
        self.assertEqual(err.index, 1)

    def test_negative_int_above_the_bound_is_rejected_too(self):
        self.assert_refused(-(2**53) - 1, "abs(n) > 2**53")

    def test_rejection_also_applies_to_count(self):
        with self.assertRaises(ContractError):
            count([1, "two"])


class TestMissingValues(unittest.TestCase):
    def test_none_and_nan_are_missing_rather_than_invalid(self):
        self.assertEqual(as_numeric([None, NAN]), [])

    def test_drop_is_the_default_policy(self):
        self.assertEqual(as_numeric([3, None, 7, NAN, 1]), [3.0, 7.0, 1.0])

    def test_count_drops_missing_values(self):
        self.assertEqual(count([3, None, 7, NAN, 1]), 3)

    def test_all_missing_gives_an_empty_list_and_zero(self):
        # The policy ran and left nothing. Saying 0 is honest; the audit
        # has to say why as well.
        self.assertEqual(as_numeric([None, NAN]), [])
        self.assertEqual(count([None, NAN]), 0)

    def test_strict_refuses_on_none(self):
        with self.assertRaises(ContractError):
            as_numeric([1, None], policy="strict")

    def test_strict_refuses_on_nan(self):
        with self.assertRaises(ContractError):
            as_numeric([1, NAN], policy="strict")

    def test_strict_names_the_index_of_the_missing_value(self):
        with self.assertRaises(ContractError) as caught:
            as_numeric([1.0, 2.0, None], policy="strict")
        self.assertIn("index 2", str(caught.exception))

    def test_strict_leaves_present_values_alone(self):
        self.assertEqual(as_numeric([1, 2, 3], policy="strict"), [1.0, 2.0, 3.0])

    def test_zero_is_a_measurement_and_not_missing(self):
        self.assertEqual(as_numeric([0]), [0.0])
        self.assertEqual(count([0]), 1)


class TestErrorMessageNamesThePosition(unittest.TestCase):
    def test_index_of_a_rejected_value_is_in_the_message(self):
        with self.assertRaises(ContractError) as caught:
            as_numeric([1.0, 2.0, "three", 4.0])
        message = str(caught.exception)
        self.assertIn("index 2", message)
        self.assertIn("'three'", message)

    def test_error_object_carries_index_and_value(self):
        with self.assertRaises(ContractError) as caught:
            as_numeric([1.0, True])
        self.assertEqual(caught.exception.index, 1)
        self.assertIs(caught.exception.value, True)

    def test_contract_error_is_a_type_error_so_old_callers_still_catch_it(self):
        self.assertTrue(issubclass(ContractError, TypeError))
        with self.assertRaises(TypeError):
            as_numeric(["1"])


class TestPolicyArgument(unittest.TestCase):
    def test_documented_policies_are_exactly_drop_and_strict(self):
        self.assertEqual(POLICIES, ("drop", "strict"))

    def test_unknown_policy_raises_value_error(self):
        with self.assertRaises(UnknownPolicyError):
            as_numeric([1, 2], policy="explode")

    def test_unknown_policy_raises_before_the_input_is_consumed(self):
        # A one-shot generator is the whole point: an argument error must
        # not destroy the data it was never allowed to touch.
        for fn in (as_numeric, count):
            with self.subTest(fn=fn.__name__):
                data = OneShot([1, 2, 3])
                with self.assertRaises(UnknownPolicyError):
                    fn(data, policy="impute")
                self.assertEqual(data.iterations, 0)

    def test_policy_must_be_a_string(self):
        with self.assertRaises(UnknownPolicyError):
            as_numeric([1, 2], policy=None)


class TestSinglePassOverTheInput(unittest.TestCase):
    def test_generator_is_consumed_once_by_as_numeric(self):
        data = OneShot([1, None, 3])
        self.assertEqual(as_numeric(data), [1.0, 3.0])
        self.assertEqual(data.iterations, 1)

    def test_generator_is_consumed_once_by_count(self):
        data = OneShot([1, None, 3])
        self.assertEqual(count(data), 2)
        self.assertEqual(data.iterations, 1)

    def test_a_real_generator_works(self):
        self.assertEqual(as_numeric(x for x in [1, 2, 3]), [1.0, 2.0, 3.0])

    def test_a_tuple_or_set_is_fine_but_a_bare_number_is_not(self):
        self.assertEqual(as_numeric((1, 2)), [1.0, 2.0])
        with self.assertRaises(TypeError):
            as_numeric(5)


class TestDocstringShape(unittest.TestCase):
    """The docstring shape is itself part of the contract."""

    def test_every_public_function_documents_the_six_required_sections(self):
        for fn in (as_numeric, count):
            with self.subTest(fn=fn.__name__):
                doc = fn.__doc__
                for section in (
                    "Inputs:",
                    "Outputs:",
                    "Assumptions:",
                    "Missing:",
                    "Errors:",
                    "Example:",
                ):
                    self.assertIn(section, doc)

    def test_the_assumption_is_stated_rather_than_left_out(self):
        # A function that cannot know the mechanism must say so, in the
        # exact words the audit is going to record.
        for fn in (as_numeric, count):
            with self.subTest(fn=fn.__name__):
                self.assertIn(ASSUMPTION, fn.__doc__)

    def test_documented_examples_actually_run(self):
        results = doctest.testmod(descriptive, report=False)
        self.assertEqual(results.failed, 0, "a docstring example is wrong")


if __name__ == "__main__":
    unittest.main()
