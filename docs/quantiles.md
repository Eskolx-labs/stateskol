# Quantiles and Interquartile Range

The quantile and IQR functions are implemented and verified locally. Sample variance and standard deviation remain outside the current implementation.

## Interface

Implemented in [src/stateskol/descriptive.py](../src/stateskol/descriptive.py):

| Function | Result |
| --- | --- |
| `quantile(data, probability)` | The specified quantile, using Ross's percentile rule. |
| `iqr(data)` | The third quartile minus the first quartile. |

Both return `StatisticResult(value, dropped_count)` and follow the [numeric input contract](input-contract.md).

With `src` on the Python import path:

```python
from stateskol.descriptive import iqr, quantile

data = [8, None, 2, 6, 4]
print(quantile(data, 0.25))
print(quantile(data, 0.75))
print(iqr(data))
```

Expected output:

```text
StatisticResult(value=3, dropped_count=1)
StatisticResult(value=7, dropped_count=1)
StatisticResult(value=4, dropped_count=1)
```

These original examples apply the cited definitions; they are not copied textbook exercises.

## Calculation Rules

**Quantile:** Validate and clean the data, validate the probability, and sort a copy. For an interior probability, calculate `n * probability`. At an integer position, average that observation and the next; otherwise take the next whole-number position. Positions in this rule start at one. This follows Ross, sec. 2.3.3, printed pp. 26-27 (PDF pp. 41-42).

The project defines endpoints explicitly: probability `0` returns the minimum and `1` returns the maximum. Unsupported probability types raise `TypeError`; out-of-range probabilities, `NaN`, and infinity raise `ValueError`.

**IQR:** Compute $Q_{0.75}-Q_{0.25}$, following Ross, sec. 2.3.3, printed p. 29, before sec. 2.4 (PDF p. 44). IQR reuses the internal quantile calculation. It cleans and sorts once, so missing observations are not counted twice.

Both functions require at least one retained observation, preserve the caller's data, and reject invalid observations even when an endpoint is requested. A singleton has its own value as every quantile and an IQR of zero.

## Numeric Behavior

- Rank calculation uses Python's `n * probability`, without a tolerance near integer positions.
- Standard-library `Fraction` arithmetic is used internally for midpoint averaging and quartile subtraction, avoiding overflow in intermediate sums and loss of small differences between large integers. `Fraction` observations are still rejected by the input contract.
- Integral results are returned as exact Python integers, even when input observations are floats. Nonintegral results are converted to floats with ordinary rounding and possible underflow.
- A nonintegral result outside the finite float range raises `OverflowError`. Integral results have no fixed magnitude limit.

These are implementation decisions, not additional textbook definitions. IQR subtracts internal exact quartiles before rounding its final result, so it can be more accurate than subtracting two separately returned, rounded quantiles.

## Verification

Run from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_descriptive.py -v
python -m doctest src/stateskol/descriptive.py -v
```

The [test suite](../tests/test_descriptive.py) contains 29 tests: 13 for input validation and 16 for quantiles and IQR. The module includes seven executable docstring examples. Coverage includes hand-computed quartiles, noninteger positions, endpoints, adjacent floating-point probabilities, singleton and constant data, ties, negative and fractional observations, missing counts, unchanged input, invalid inputs, and numeric limits.

The package and tests use only the standard library. The [controlled NumPy comparison](reference-validation.md) passed 176 quantile and 22 IQR comparisons using `method="averaged_inverted_cdf"`, identical retained observations, and explicit tolerances. Passing local checks does not establish upstream CI, a clean package installation, or PR approval.

## References

- Ross, Sheldon M. *Introduction to Probability and Statistics for Engineers and Scientists*, 6th ed., sec. 2.3.3: percentile definition and selection, printed pp. 26-27 (PDF pp. 41-42); IQR, printed p. 29 (PDF p. 44). PDF pages refer to the supplied study copy, which is not distributed with the repository.
- [Unit tests](../tests/test_descriptive.py): hand-computed expected quartiles and IQR values for small datasets.
- [NumPy quantile documentation](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html): reference-method naming.