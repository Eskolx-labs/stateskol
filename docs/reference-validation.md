# NumPy Reference Validation

**Verified:** 2026-09-27; direct execution rechecked 2026-09-28.

**Scope:** Quantiles and IQR. Sample variance and standard deviation remain pending.

## Reproduce the Comparison

Run [examples/reference_check.py](../examples/reference_check.py) from the repository root:

```bash
python examples/reference_check.py
```

The script locates the local `src` directory relative to its own file. No `PYTHONPATH` setting is required; an absolute script path also works from another working directory.

| Verified interpreter | NumPy version |
| --- | --- |
| Python 3.13.5 | 2.1.3 |
| Python 3.14.7 (`/usr/bin/python`) | 2.5.2 |

Both environments produced the counts and maximum errors reported below. These are observed environments, not a supported-version matrix. NumPy 1.22 introduced the named method; use a NumPy release compatible with the chosen interpreter. To reproduce the original comparison, install `numpy==2.1.3` in a separate Python 3.13 evidence environment.

NumPy is imported only by the reference script. Package code and unit tests remain standard-library-only. The script imports local source directly; this is not a clean package-installation check.

## Method

| Setting | Value |
| --- | --- |
| NumPy quantile method | `averaged_inverted_cdf` |
| Reference data type | `float64` |
| Quantile probabilities | `0`, `0.1`, `0.25`, `0.5`, `0.6`, `0.75`, `0.9`, `1` |
| IQR reference | NumPy's 0.75 quantile minus its 0.25 quantile |
| Relative tolerance | `1e-12` |
| Absolute tolerance | `1e-12` |
| Generated-data seed | `20260927`, using Python's `random.Random` |

For each finite result, the acceptance condition is:

$$
|\mathrm{actual}-\mathrm{reference}| \leq 10^{-12} + 10^{-12}|\mathrm{reference}|
$$

The relative tolerance permits rounding differences at the reference's scale; the absolute tolerance handles values near zero. Nonfinite results fail. This checks numerical agreement, not identical types or bit-for-bit equality. Absolute errors are reported alongside pass/fail results.

The script supplies original data to Stateskol and independently specified retained observations to NumPy. It does not use `prepare_data` to construct NumPy's input. Generated cases insert missing markers after generating the retained dataset. Each result's dropped count is checked exactly against the expected count.

## Coverage

The comparison uses 12 fixed datasets and 10 seeded datasets. Fixed cases cover hand-worked values, odd-length data, a singleton, constants, ties, negatives, zero, tuples, fractional and decimal floats, skew, missing observations, and a large offset.

Generated datasets have sizes `1, 2, 3, 4, 5, 8, 16, 31, 64, 127`, with values drawn from `[-100, 100]` and two missing observations inserted per case.

## Results

| Measurement | Result |
| --- | --- |
| Datasets | 22 |
| Quantile comparisons | 176 passed |
| IQR comparisons | 22 passed |
| Dropped-count checks | All 198 passed |
| Maximum quantile absolute error | `1.3877787807814457e-17` |
| Maximum IQR absolute error | `0` |
| Failures | 0 |
| Exit code | 0 |

The small quantile difference occurred in the decimal dataset. All other datasets had zero observed quantile error. For `[2, 4, 6, 8]`, both implementations give a first quartile of 3, a third quartile of 7, and IQR of 4.

Any value mismatch, incorrect dropped count, or unexpected nonfinite result causes a failed comparison and exit code 1. Unexpected runtime errors also terminate the script unsuccessfully.

## Limitations

- These comparisons cover ordinary float64-compatible data, not every accepted input. Arbitrary-size integers and extreme floating-point arithmetic are covered separately in the [unit tests](../tests/test_descriptive.py).
- Empty input, invalid values, invalid probabilities, and adjacent floating-point probability boundaries remain unit-test cases. NumPy's error policies differ from the project's input contract and are not compared here.
- Stateskol uses exact rational intermediate arithmetic for quartiles and IQR; NumPy uses floating-point arithmetic. Small differences can occur, particularly when separately rounded quartiles are subtracted.
- Local comparison results do not establish upstream CI, PR approval, a published research note, or completion of the remaining variance work. This contribution fills the shared reference-script placeholder for quantiles and IQR only.

## References

- Ross, Sheldon M. *Introduction to Probability and Statistics for Engineers and Scientists*, 6th ed., sec. 2.3.3: printed pp. 26-27 (PDF pp. 41-42), percentile selection; printed p. 29 before sec. 2.4 (PDF p. 44), IQR. PDF pages refer to the supplied study copy, which is not distributed with the repository.
- [NumPy quantile documentation](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html): method names and behavior.
- [NumPy allclose documentation](https://numpy.org/doc/stable/reference/generated/numpy.allclose.html): the tolerance formula used explicitly in the script.
- [Unit tests](../tests/test_descriptive.py) and [quantile implementation](quantiles.md): expected values, numeric policies, and local tests.