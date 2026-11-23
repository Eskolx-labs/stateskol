"""Tests for descriptive.py, by lane.

Each test names the reason it exists.
"""

import math
import unittest

import stateskol.descriptive as descriptive
from stateskol.descriptive import as_numeric, checked_difference, count, float_spacing
from stateskol.errors import ContractError


# --------------------------------------------------------------------------
# Numerics lane (Hanna Desalegn). Week 2.
# --------------------------------------------------------------------------

NAN = float("nan")
INF = float("inf")


class TheTwoToThe53Boundary(unittest.TestCase):
    """Why the contract stops ints at 2**53, worked out by hand.

    A double has a 53-bit significand. Up to 2**53 every integer has its own
    float. Past it the floats are 2 apart, so 2**53 + 1 has nowhere to go.
    """

    def test_every_int_up_to_2_53_survives_float(self):
        # reason: the accepted side of the boundary must be exact
        for n in (2**53, 2**53 - 1, -(2**53), -(2**53) + 1):
            self.assertEqual(int(float(n)), n)

    def test_2_53_plus_1_rounds_silently_in_plain_python(self):
        # reason: this is the failure the rule prevents
        self.assertEqual(float(2**53 + 1), float(2**53))
        self.assertNotEqual(2**53 + 1, 2**53)

    def test_contract_accepts_2_53_and_refuses_2_53_plus_1(self):
        # reason: the boundary itself is inside, the next int is outside
        self.assertEqual(as_numeric([2**53]), [9007199254740992.0])
        self.assertEqual(as_numeric([-(2**53)]), [-9007199254740992.0])
        for n in (2**53 + 1, -(2**53 + 1)):
            with self.assertRaises(ContractError) as ctx:
                as_numeric([1, n])
            self.assertEqual(ctx.exception.index, 1)

    def test_bound_is_conservative(self):
        # reason: 2**60 is exact as a float but one simple bound is easier to defend
        self.assertEqual(int(float(2**60)), 2**60)
        with self.assertRaises(ContractError):
            as_numeric([2**60])

    def test_large_floats_are_accepted(self):
        # reason: the 2**53 rule is about converting ints, floats need no conversion
        self.assertEqual(as_numeric([1e16, 1e308, -1e308]), [1e16, 1e308, -1e308])

    def test_spacing_doubles_at_2_53(self):
        # reason: the hand-worked numbers behind the rule
        self.assertEqual(float_spacing(2**52), 1.0)
        self.assertEqual(float_spacing(2**53), 2.0)
        self.assertEqual(float_spacing(1.0), 2.0**-52)
        self.assertEqual(1e16 + 1, 1e16)  # spacing at 1e16 is 2, so +1 vanishes


class NanAndInf(unittest.TestCase):
    def test_nan_makes_builtin_min_depend_on_order(self):
        # reason: why nan must be removed before min and max run
        self.assertTrue(math.isnan(min([NAN, 3.0, 1.0])))
        self.assertEqual(min([3.0, NAN, 1.0]), 1.0)

    def test_as_numeric_removes_nan_in_any_position(self):
        # reason: after the policy, order no longer changes the answer
        for data in ([NAN, 3, 1], [3, NAN, 1], [3, 1, NAN]):
            self.assertEqual(min(as_numeric(data)), 1.0)
            self.assertEqual(count(data), 2)

    def test_negative_nan_is_missing(self):
        # reason: nan has a sign bit too, it is still missing
        self.assertEqual(as_numeric([-NAN, 2]), [2.0])

    def test_inf_is_refused_not_dropped(self):
        # reason: an infinite observation is a data error, not missing
        for bad in (INF, -INF):
            with self.assertRaises(ContractError):
                as_numeric([1, bad])

    def test_inf_from_overflowing_literal_is_refused(self):
        # reason: 1e309 is already inf when Python reads it
        with self.assertRaises(ContractError):
            as_numeric([1e309])


class StabilityCaseRangeOverflow(unittest.TestCase):
    """The stability case for week 2.

    Inputs -1e308 and 1e308 are finite and the contract accepts both. Their
    true range is 2e308, which is larger than the biggest double (about
    1.797e308). Plain subtraction returns inf with no error, an infinite
    summary built from finite data.
    """

    def test_plain_subtraction_returns_inf(self):
        # reason: the failure, shown with the numbers
        values = as_numeric([-1e308, 0.5, 1e308])
        self.assertTrue(math.isinf(max(values) - min(values)))

    def test_checked_difference_refuses_it(self):
        # reason: the guard data_range should use
        with self.assertRaisesRegex(OverflowError, "overflows a float"):
            checked_difference(1e308, -1e308)

    def test_largest_finite_range_still_works(self):
        # reason: the guard must not refuse what does fit
        top = 1.7976931348623157e308  # largest finite double
        self.assertEqual(checked_difference(top, 0.0), top)
        self.assertEqual(checked_difference(top / 2, -top / 2), top)

    def test_ordinary_differences_are_exact(self):
        # reason: hand-checked values
        self.assertEqual(checked_difference(9.0, 2.0), 7.0)
        self.assertEqual(checked_difference(2**53, 1), 9007199254740991.0)
        self.assertEqual(checked_difference(0.0, -0.0), 0.0)
        self.assertEqual(checked_difference(5e-324, 0.0), 5e-324)  # smallest subnormal

    def test_infinite_inputs_are_refused_by_the_contract(self):
        # reason: inf is a data error everywhere, not only inside as_numeric
        for hi, lo in ((INF, 0.0), (0.0, -INF)):
            with self.assertRaises(ContractError):
                checked_difference(hi, lo)

    def test_nan_inputs_are_refused(self):
        # reason: nan here means the missing-value policy was skipped
        for hi, lo in ((NAN, 1.0), (1.0, NAN)):
            with self.assertRaises(ValueError):
                checked_difference(hi, lo)

    def test_refused_types_match_the_contract(self):
        # reason: review on #23, a helper must not accept what as_numeric refuses
        for hi, lo in ((True, 0), (5, False), ("5", "1"), (2**53 + 1, 0)):
            with self.assertRaises(ContractError):
                checked_difference(hi, lo)


class Types(unittest.TestCase):
    def test_float_subclass_is_accepted_exactly(self):
        # reason: numpy.float64 subclasses float, so the value converts exactly
        class MyFloat(float):
            pass

        self.assertEqual(as_numeric([MyFloat(2.5)]), [2.5])

    def test_negative_zero_keeps_its_sign_and_compares_equal(self):
        # reason: -0.0 == 0.0, so min and max may return either sign
        out = as_numeric([0.0, -0.0])
        self.assertEqual(out, [0.0, 0.0])
        self.assertEqual(math.copysign(1, out[1]), -1.0)

    def test_float_spacing_refuses_non_finite(self):
        # reason: a spacing at inf or nan has no meaning
        with self.assertRaises(ContractError):
            float_spacing(INF)
        with self.assertRaises(ValueError):
            float_spacing(NAN)

    def test_float_spacing_refuses_what_the_contract_refuses(self):
        # reason: review on #23, True and "10" used to be converted silently
        for bad in (True, False, "10", b"10", 2**53 + 1):
            with self.assertRaises(ContractError):
                float_spacing(bad)

    def test_numpy_types_if_installed(self):
        # reason: the cohort PRs disagreed on numpy scalars, this pins it
        try:
            import numpy as np
        except ImportError:
            self.skipTest("numpy not installed, the package itself does not need it")
        self.assertEqual(as_numeric([np.float64(2.5)]), [2.5])
        self.assertEqual(as_numeric([np.float64("nan"), 1]), [1.0])
        for bad in (np.int64(2), np.float32(2.5)):
            with self.assertRaises(ContractError):
                as_numeric([bad])


class Doctests(unittest.TestCase):
    def test_numerics_examples_run(self):
        # reason: the docstring examples are part of the contract
        import doctest

        for f in (checked_difference, float_spacing):
            for test in doctest.DocTestFinder().find(f, globs=vars(descriptive)):
                result = doctest.DocTestRunner().run(test)
                self.assertEqual(result.failed, 0, f.__name__)


if __name__ == "__main__":
    unittest.main()
