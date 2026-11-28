"""Tests for the Week 4 Numerics lane: the bivariate state.

Every test names the rule it defends. Standard library only, as in week 2 and
week 3; the reference comparison lives in examples/numerics_reference_check.py.

    python -m pytest tests/test_numerics.py -q

The numbers were computed twice before being written here: once with
fractions.Fraction for the exact truth, and once by stepping the Chan, Golub &
LeVeque (1983) update by hand. Nothing in this file was guessed.
"""

import doctest
import math
import unittest
from fractions import Fraction as F

import stateskol.descriptive as descriptive
from stateskol.descriptive import (
    BivariateState,
    as_numeric,
    bivariate_online_update,
    iqr,
    variance,
)
from stateskol.errors import (
    ContractError,
    DimensionMismatchError,
    DomainError,
    EmptyDataError,
)

NAN = float("nan")

# The brief's shifted pair. Deviations from the two means are dyadic, so every
# step of the update lands on an exactly representable double.
X9 = [1e9 + 1, 1e9 + 2, 1e9 + 3, 1e9 + 4]
Y9 = [1e9 + 2, 1e9 + 4, 1e9 + 6, 1e9 + 8]

# Hand-worked: dx = [-1.5, -0.5, 0.5, 1.5], dy = [-3, -1, 1, 3], so
# m2_x = 5, m2_y = 20, co_moment = 10, and the sample covariance is 10 / 3.
COV9 = 10 / 3                      # 3.3333333333333335
VAR_X9 = 5 / 3                     # 1.6666666666666667
VAR_Y9 = 20 / 3                    # 6.666666666666667

# A twelve-pair sample whose exact covariance is 25/33. The values are ordinary
# integers, so this is the case the brief's dyadic pair cannot see.
XA = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]
YA = [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5]


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


def exact_covariance(x, y, ddof=1):
    """The covariance computed in rationals, so the test has a truth to aim at."""
    n = len(x)
    mean_x = sum(F(v) for v in x) / n
    mean_y = sum(F(v) for v in y) / n
    co = sum((F(a) - mean_x) * (F(b) - mean_y) for a, b in zip(x, y))
    return co / (n - ddof)


def naive_covariance(x, y):
    """The textbook one-line formula, kept here so its failure stays tested."""
    n = len(x)
    return (sum(a * b for a, b in zip(x, y)) - sum(x) * sum(y) / n) / (n - 1)


def shifted_data_covariance(x, y):
    """Chan, Golub & LeVeque's shifted-data variant, algorithm S of their 1983 paper.

    Subtracting the first observation from both columns before averaging keeps
    every running sum near zero, where a double has room for the deviations.
    This is not what the package ships; it is the diagnosis of what the shipped
    online update loses, so the test states a cause instead of a surprise.
    """
    x0, y0 = x[0], y[0]
    n = len(x)
    a = [v - x0 for v in x]
    b = [v - y0 for v in y]
    ma = sum(a) / n
    mb = sum(b) / n
    return math.fsum((u - ma) * (w - mb) for u, w in zip(a, b)) / (n - 1)


class TestHandWorkedStepTable(unittest.TestCase):
    """The state after each pair, checked against the arithmetic in the docstring."""

    def test_each_step_lands_on_the_hand_worked_sums(self):
        # k=1: no deviation yet. k=2: dx=[-0.5, 0.5], dy=[-1, 1].
        # k=3: dx=[-1, 0, 1], dy=[-2, 0, 2]. k=4: dx=[-1.5..1.5], dy=[-3..3].
        steps = [
            (1, 1e9 + 1, 1e9 + 2, 0.0, 0.0, 0.0),
            (2, 1e9 + 1.5, 1e9 + 3.0, 0.5, 2.0, 1.0),
            (3, 1e9 + 2.0, 1e9 + 4.0, 2.0, 8.0, 4.0),
            (4, 1e9 + 2.5, 1e9 + 5.0, 5.0, 20.0, 10.0),
        ]
        state = BivariateState()
        for k, mx, my, m2x, m2y, co in steps:
            state.add(X9[k - 1], Y9[k - 1])
            self.assertEqual(state.n, k)
            self.assertEqual(state.mean_x, mx)
            self.assertEqual(state.mean_y, my)
            self.assertEqual(state.m2_x, m2x)
            self.assertEqual(state.m2_y, m2y)
            self.assertEqual(state.co_moment, co)

    def test_the_whole_state_prints_the_hand_worked_integers(self):
        self.assertEqual(
            repr(bivariate_online_update(X9, Y9)),
            "BivariateState(n=4, mean_x=1000000002.5, mean_y=1000000005.0, "
            "m2_x=5.0, m2_y=20.0, co_moment=10.0, dropped_pairs=0)",
        )

    def test_the_accessors_divide_the_same_sums_by_the_stated_divisor(self):
        state = bivariate_online_update(X9, Y9)
        self.assertEqual(state.covariance(), COV9)
        self.assertEqual(state.covariance(ddof=0), 10 / 4)
        self.assertEqual(state.variance_x(), VAR_X9)
        self.assertEqual(state.variance_y(), VAR_Y9)

    def test_the_correlation_of_an_exactly_linear_pair_is_one(self):
        # y = 2x for these four pairs, so r must be exactly 1.0 and not 0.9999.
        state = bivariate_online_update(X9, Y9)
        self.assertEqual(
            state.co_moment / math.sqrt(state.m2_x * state.m2_y), 1.0
        )


class TestTheBriefsCancellationCase(unittest.TestCase):
    """The case the brief says this lane must reproduce."""

    def test_the_naive_formula_returns_exactly_zero(self):
        self.assertEqual(naive_covariance(X9, Y9), 0.0)

    def test_the_naive_formula_fails_for_the_right_reason(self):
        # sum(x*y) lands near 4e18, where one double step is 512. The answer
        # this formula is chasing is 10/3, so the quantum of the accumulator is
        # 153 times the quantity being measured. The failure is the scale, not
        # a bug in the arithmetic.
        total = sum(a * b for a, b in zip(X9, Y9))
        self.assertGreaterEqual(math.ulp(total) / COV9, 100)

    def test_the_one_pass_update_returns_the_exact_quotient(self):
        self.assertEqual(bivariate_online_update(X9, Y9).covariance(), COV9)

    def test_a_two_pass_sum_agrees_with_the_state(self):
        mean_x = sum(X9) / 4
        mean_y = sum(Y9) / 4
        two_pass = math.fsum(
            (a - mean_x) * (b - mean_y) for a, b in zip(X9, Y9)
        ) / 3
        self.assertEqual(two_pass, bivariate_online_update(X9, Y9).covariance())

    def test_the_state_agrees_with_rationals_on_an_ordinary_sample(self):
        state = bivariate_online_update(XA, YA)
        want = float(exact_covariance(XA, YA))
        # Two ulps of the answer. The update divides twice per pair, by k and
        # by (k - 1) / k, so the last bit of a twelve-step sum is not free.
        self.assertLessEqual(abs(state.covariance() - want), 2 * math.ulp(want))


class TestAccessors(unittest.TestCase):
    def test_ddof_outside_the_defined_pair_is_refused(self):
        state = bivariate_online_update(X9, Y9)
        for bad in (2, -1, 1.0, True, "1"):
            with self.subTest(ddof=bad):
                with self.assertRaises(DomainError):
                    state.covariance(ddof=bad)

    def test_one_pair_cannot_pay_the_sample_divisor(self):
        state = bivariate_online_update([1e9 + 7], [1e9 + 9])
        self.assertEqual(state.n, 1)
        self.assertEqual(state.covariance(ddof=0), 0.0)
        with self.assertRaises(EmptyDataError):
            state.covariance()

    def test_an_empty_state_is_returned_rather_than_raising(self):
        # The week 2 rule: a count of nothing is a finding, not a value.
        state = bivariate_online_update([], [])
        self.assertEqual((state.n, state.dropped_pairs), (0, 0))
        with self.assertRaises(EmptyDataError):
            state.covariance()

    def test_a_state_with_no_complete_pair_reports_the_drop(self):
        state = bivariate_online_update([None, NAN], [1.0, 2.0])
        self.assertEqual((state.n, state.dropped_pairs), (0, 2))
        with self.assertRaises(EmptyDataError):
            state.variance_x()


class TestCompleteCasePairing(unittest.TestCase):
    """ASK 02: paired inputs are dropped as pairs, never as columns."""

    def test_a_gap_in_one_column_drops_the_pair_and_is_counted(self):
        state = bivariate_online_update([1, None, 3], [10, 20, 30])
        self.assertEqual(state.n, 2)
        self.assertEqual(state.dropped_pairs, 1)
        self.assertEqual(state.covariance(), 20.0)

    def test_dropping_each_column_on_its_own_would_pair_the_wrong_values(self):
        # Independent column dropping pairs 3 with 20 instead of 30 and reports
        # 10.0, a different number from a sample nobody had. The pair rule is
        # what keeps x[i] and y[i] describing the same observation.
        xs = as_numeric([1, None, 3])
        ys = as_numeric([10, 20, 30])
        wrong = bivariate_online_update(xs, ys[:2])
        self.assertEqual(wrong.covariance(), 10.0)
        self.assertEqual(bivariate_online_update([1, None, 3], [10, 20, 30]).covariance(), 20.0)

    def test_a_gap_in_either_column_drops_the_pair(self):
        self.assertEqual(
            bivariate_online_update([1, 2], [None, 2]).dropped_pairs, 1
        )
        self.assertEqual(
            bivariate_online_update([1, None], [2, None]).dropped_pairs, 1
        )

    def test_add_refuses_a_missing_pair_rather_than_inventing_a_rule(self):
        state = BivariateState()
        with self.assertRaises(ContractError):
            state.add(1.0, None)
        with self.assertRaises(ContractError):
            state.add(NAN, 1.0)
        self.assertEqual(state.n, 0)


class TestLengthMismatch(unittest.TestCase):
    def test_different_lengths_are_refused_and_both_sizes_are_reported(self):
        with self.assertRaises(DimensionMismatchError) as caught:
            bivariate_online_update([1, 2, 3], [1, 2])
        self.assertEqual((caught.exception.len_x, caught.exception.len_y), (3, 2))

    def test_the_longer_series_is_never_truncated_to_fit(self):
        # zip() would stop at the shorter input and report a covariance for a
        # sample the caller never handed over. That is the bug this test exists
        # to keep out of the function.
        with self.assertRaises(DimensionMismatchError):
            bivariate_online_update([1, 2, 3, 4], [1, 2])
        with self.assertRaises(DimensionMismatchError):
            bivariate_online_update([1, 2], [1, 2, 3, 4])

    def test_a_mismatch_leaves_both_input_lists_untouched(self):
        x = [1, 2, 3]
        y = [1, 2]
        with self.assertRaises(DimensionMismatchError):
            bivariate_online_update(x, y)
        self.assertEqual((x, y), ([1, 2, 3], [1, 2]))

    def test_generators_are_drained_by_the_refusal_and_says_so(self):
        # A generator cannot be measured without consuming it, so the length
        # check has to read both. Documented, tested, and the reason the
        # docstring tells a caller with one-shot inputs to pass lists.
        xs, ys = OneShot([1, 2, 3]), OneShot([1, 2])
        with self.assertRaises(DimensionMismatchError):
            bivariate_online_update(xs, ys)
        self.assertEqual((xs.iterations, ys.iterations), (1, 1))


class TestOnePassPerPair(unittest.TestCase):
    def test_each_series_is_read_exactly_once(self):
        xs, ys = OneShot(XA), OneShot(YA)
        state = bivariate_online_update(xs, ys)
        self.assertEqual(state.n, 12)
        self.assertEqual((xs.iterations, ys.iterations), (1, 1))

    def test_streaming_pairs_matches_one_call_over_the_same_pairs(self):
        streamed = BivariateState()
        for a, b in zip(XA, YA):
            streamed.add(a, b)
        batch = bivariate_online_update(XA, YA)
        self.assertEqual(streamed.co_moment, batch.co_moment)
        self.assertEqual(streamed.mean_x, batch.mean_x)
        self.assertEqual(streamed.m2_y, batch.m2_y)

    def test_the_state_matches_week_3_variance_column_by_column(self):
        # The same Welford update, run inside the pair, must give the same
        # double as variance() gives for the column on its own.
        state = bivariate_online_update(XA, YA)
        self.assertEqual(state.variance_x(), variance(XA))
        self.assertEqual(state.variance_y(), variance(YA))


class TestContractInheritance(unittest.TestCase):
    def test_a_string_in_either_column_is_refused_with_its_pair_index(self):
        for bad_x, bad_y in (("8", 1.0), (1.0, "8")):
            with self.subTest(bad=(bad_x, bad_y)):
                with self.assertRaises(ContractError) as caught:
                    bivariate_online_update([1, bad_x], [1, bad_y])
                self.assertEqual(caught.exception.index, 1)

    def test_bool_is_refused_because_true_is_an_int_but_not_a_measurement(self):
        with self.assertRaises(ContractError):
            bivariate_online_update([1, True], [1, 2])

    def test_infinity_is_refused_rather_than_treated_as_large(self):
        with self.assertRaises(ContractError):
            bivariate_online_update([1, math.inf], [1, 2])

    def test_the_2_pow_53_conversion_bound_applies_to_both_columns(self):
        with self.assertRaises(ContractError):
            bivariate_online_update([1, 2**53 + 1], [1, 2])
        with self.assertRaises(ContractError):
            bivariate_online_update([1, 2], [1, 2**53 + 1])

    def test_an_int_is_accepted_and_becomes_a_float_in_the_state(self):
        state = bivariate_online_update([1, 2], [3, 4])
        self.assertIsInstance(state.mean_x, float)
        self.assertIsInstance(state.co_moment, float)


class TestToleranceAnalysis(unittest.TestCase):
    """Where the online update loses, by how much, and why.

    The bound the lane states is not a round number picked after the fact. It
    is the grid the running mean lives on: a double near 1e9 has ulp 2**-23,
    about 1.19e-7, and the increment mean += dx / k is smaller than that, so it
    is quantised. The co-moment inherits the error through dx = x - mean_x.
    """

    def test_the_error_is_scaled_by_the_magnitude_of_the_mean_not_of_the_answer(self):
        unshifted = bivariate_online_update(XA, YA).covariance()
        shifted = bivariate_online_update(
            [v + 1e9 for v in XA], [v + 1e9 for v in YA]
        ).covariance()
        want = float(exact_covariance(XA, YA))
        self.assertLessEqual(abs(unshifted - want), 2 * math.ulp(want))
        # At 1e9 the mean is stored on a 1.19e-7 grid, so the covariance drifts
        # by orders of magnitude more than one ulp of its own value.
        self.assertGreater(abs(shifted - want), 1e4 * math.ulp(want))
        self.assertLess(abs(shifted - want), 8 * math.ulp(1e9))

    def test_the_shifted_data_variant_removes_the_loss_so_the_cause_is_the_mean(self):
        xs = [v + 1e9 for v in XA]
        ys = [v + 1e9 for v in YA]
        want = float(exact_covariance(XA, YA))
        recovered = shifted_data_covariance(xs, ys)
        self.assertLessEqual(abs(recovered - want), math.ulp(want))

    def test_week_3_variance_carries_the_same_limit(self):
        # Disclosed rather than hidden: the week 2/3 Welford update stores its
        # mean the same way, so shifting ordinary integer data by 1e9 costs the
        # same grid. The brief's own 1e9 case has a dyadic mean and cannot see
        # it, which is why this sample is used here instead.
        want = float(sum((F(v) - sum(F(z) for z in XA) / 12) ** 2 for v in XA) / 11)
        shifted = variance([v + 1e9 for v in XA])
        self.assertGreater(abs(shifted - want), 1e4 * math.ulp(want))
        self.assertLess(abs(shifted - want), 8 * math.ulp(1e9))

    def test_the_bound_holds_in_both_directions_for_the_naive_formula(self):
        # The naive formula is not merely inaccurate at 1e9, it is zero. The
        # online update is inaccurate in the last digits. Those are different
        # failures and the tolerance analysis has to keep them apart.
        self.assertEqual(naive_covariance(X9, Y9), 0.0)
        self.assertNotEqual(
            bivariate_online_update([v + 1e9 for v in XA], [v + 1e9 for v in YA]).covariance(),
            0.0,
        )


class TestConstantAndTiedColumns(unittest.TestCase):
    """The two boundary cases the week 4 pack adds beyond length and magnitude.

    A constant column is where a correlation dies. A majority of identical
    values is where Freedman-Diaconis binning dies, because Q1 = Q3 and the bin
    width comes out zero. Neither is a reason the co-moment should misbehave,
    so the state reports the zero and the tie exactly, and the refusal stays in
    the lane that owns it: Core C cannot refuse on s_x = 0 unless this lane
    hands it a true zero rather than a small number near one.
    """

    # Seven of nine values identical in each column, shifted to 1e9 so the
    # sample is degenerate for binning and hostile for the naive formula at the
    # same time. Exact covariance is 13/3; exact m2_x is 4.
    TIED_X = [1e9 + 5] * 7 + [1e9 + 6, 1e9 + 7]
    TIED_Y = [1e9 + 2] * 7 + [1e9 + 9, 1e9 + 20]

    def test_a_constant_column_reports_an_exact_zero(self):
        state = bivariate_online_update([7, 7, 7, 7], [1, 2, 4, 8])
        self.assertEqual(state.m2_x, 0.0)
        self.assertEqual(state.variance_x(), 0.0)
        self.assertEqual(state.co_moment, 0.0)
        self.assertEqual(state.covariance(), 0.0)
        self.assertEqual(state.n, 4)

    def test_the_zero_is_exact_enough_that_dividing_by_it_raises(self):
        # Pearson r is co_moment / sqrt(m2_x * m2_y). If this lane reported a
        # residual like 4e-14 for a constant column, Core C would return an
        # enormous or a meaningless r instead of raising ZeroVarianceError. The
        # exact zero is the handover between the two lanes.
        state = bivariate_online_update([7, 7, 7, 7], [1, 2, 4, 8])
        with self.assertRaises(ZeroDivisionError):
            state.co_moment / math.sqrt(state.m2_x * state.m2_y)

    def test_zero_iqr_kills_the_bin_width_not_the_covariance(self):
        # iqr() is week 3's, called here to prove the claim rather than assert
        # it: both columns are degenerate for Freedman-Diaconis while x and y
        # still move together, so Core A raises DegenerateBinError and this
        # state has nothing to refuse.
        self.assertEqual(iqr(self.TIED_X), 0.0)
        self.assertEqual(iqr(self.TIED_Y), 0.0)
        state = bivariate_online_update(self.TIED_X, self.TIED_Y)
        self.assertEqual(state.covariance(), float(exact_covariance(
            [v - 1e9 for v in self.TIED_X], [v - 1e9 for v in self.TIED_Y])))
        self.assertEqual(state.covariance(), 13 / 3)

    def test_the_sums_still_carry_the_mean_grid_even_when_the_quotient_lands(self):
        # The covariance above is exact, which is cancellation, not accuracy:
        # m2_x is 3.999999925494194 against an exact 4. Pinned so nobody reads
        # the previous test as proof that a shifted sample costs nothing.
        state = bivariate_online_update(self.TIED_X, self.TIED_Y)
        self.assertNotEqual(state.m2_x, 4.0)
        self.assertLess(abs(state.m2_x - 4.0), math.ulp(1e9))

    def test_the_naive_formula_is_wrong_by_at_least_the_answer_itself(self):
        # Not a predicted residue, a structural one. Every product here is near
        # 1e18, where a double resolves to 128, and every partial sum is near
        # 9e18, where it resolves to 1024. So the subtraction can only return a
        # multiple of 1024 and the covariance only a multiple of 128, while the
        # truth is 13/3. That makes the error at least as large as the answer on
        # any implementation, which is the claim worth keeping.
        want = 13 / 3
        naive = naive_covariance(self.TIED_X, self.TIED_Y)
        self.assertEqual((naive * 8) % 1024, 0.0)
        self.assertGreaterEqual(abs(naive - want), want)

    def test_which_multiple_survives_is_a_cpython_version_artifact(self):
        # Found by CI, not by me. This test asserted 256.0 and failed on the
        # 3.12 matrix row with 0.0, because CPython 3.12 gave sum() Neumaier
        # compensation for floats, so the naive formula stopped leaving its own
        # accumulation error behind. sum([0.1] * 10) detects the behaviour:
        # 0.9999999999999999 before 3.12, 1.0 from 3.12 on.
        #
        # The residue is therefore not part of the benchmark, only the size of
        # the failure is. Pinning the residue made the suite a hostage of the
        # interpreter, which is exactly the mistake this lane is about.
        compensated = sum([0.1] * 10) == 1.0
        naive = naive_covariance(self.TIED_X, self.TIED_Y)
        self.assertEqual(naive, 0.0 if compensated else 256.0)

    def test_an_exact_accumulator_still_returns_zero_because_the_products_carry_it(self):
        # math.fsum removes the summation error completely, so this is the half
        # of the failure no interpreter version can repair: summed exactly, the
        # rounded products still differ from sum(x) * sum(y) / n by less than the
        # grid they live on.
        total = math.fsum(a * b for a, b in zip(self.TIED_X, self.TIED_Y))
        naive = (total - sum(self.TIED_X) * sum(self.TIED_Y) / 9) / 8
        self.assertEqual(naive, 0.0)


class TestDocstringShape(unittest.TestCase):
    """Week 4 point 1: the algorithm, the pairing rule, the divisor, the citation."""

    PUBLIC = (bivariate_online_update, BivariateState.add, BivariateState.covariance,
              BivariateState.variance_x, BivariateState.variance_y)

    def test_every_public_name_states_the_whole_shape(self):
        for fn in self.PUBLIC:
            for heading in ("Inputs:", "Outputs:", "Assumptions:", "Missing:",
                            "Errors:", "Example:"):
                self.assertIn(heading, fn.__doc__, "{}: {}".format(fn.__name__, heading))

    def test_the_update_names_its_paper_and_the_one_it_extends(self):
        doc = bivariate_online_update.__doc__
        self.assertIn("Chan, Golub & LeVeque (1983)", doc)
        self.assertIn("Welford", doc)

    def test_the_pairing_rule_and_the_refusal_are_written_down(self):
        doc = bivariate_online_update.__doc__
        self.assertIn("complete-case", doc)
        self.assertIn("dropped_pairs", doc)
        self.assertIn("DimensionMismatchError", doc)

    def test_the_accessors_state_the_divisor(self):
        for fn in (BivariateState.covariance, BivariateState.variance_x,
                   BivariateState.variance_y):
            self.assertIn("ddof", fn.__doc__, fn.__name__)

    def test_the_class_docstring_lists_every_field_a_caller_can_read(self):
        doc = BivariateState.__doc__
        for field in ("n", "mean_x", "mean_y", "m2_x", "m2_y", "co_moment",
                      "dropped_pairs"):
            self.assertIn(field, doc)

    def test_the_module_records_the_paired_refusals(self):
        self.assertIn("DimensionMismatchError", descriptive.__doc__)
        self.assertIn("Week 4", descriptive.__doc__)


class TestThePackageStillImportsNothingExtra(unittest.TestCase):
    def test_no_reference_library_in_the_package_or_these_tests(self):
        for name in ("descriptive.py", "errors.py", "__init__.py"):
            with open("src/stateskol/" + name, encoding="utf-8") as handle:
                source = handle.read()
            for library in ("numpy", "pandas", "scipy"):
                self.assertNotIn("import " + library, source, name)
        with open(__file__, encoding="utf-8") as handle:
            mine = handle.read()
        for library in ("numpy", "pandas", "scipy"):
            self.assertNotIn("import " + library, mine)

    def test_the_docstrings_run(self):
        results = doctest.testmod(descriptive, verbose=False)
        self.assertEqual(results.failed, 0)
        self.assertGreater(results.attempted, 20)


if __name__ == "__main__":
    unittest.main()
