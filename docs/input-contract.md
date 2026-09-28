# Numeric Input Contract

**Status:** Proposed shared contract; team approval is not recorded. Input validation, quantiles, and IQR are implemented locally. Sample variance and standard deviation remain planned.

## Scope

This contract defines numeric input validation, missing-data handling, and spread-function requirements for Stateskol. Python types, missing markers, result structures, and exceptions are project decisions rather than textbook definitions.

References use printed page numbers. PDF page numbers indicate one-based viewer positions in the supplied study copies; those files are not distributed with the repository.

## Accepted Input

| Category | Requirement |
| --- | --- |
| Collection | A built-in, one-dimensional Python list or tuple; subclasses are not accepted. |
| Numeric observations | Built-in integers and finite floats, including negatives, zero, and repeated values. |
| Missing observations | `None` and built-in floating-point `NaN`. |
| Unsupported observations | Strings, booleans, complex numbers, infinity, nested collections, numeric subclasses, and other numeric types. |
| Unsupported collections | Scalars, strings, mappings, sets, generators, and other collection types. |

Functions preserve duplicate observations and do not modify the caller's collection. Automatic text-to-number conversion and flattening are not permitted. Each function documents its numeric representation and arithmetic limits.

## Missing-Data Policy

- Remove missing observations before calculation; do not replace them with zero, averages, or other values.
- Return the computed `value` and a nonnegative integer `dropped_count`. The current implementation uses a `StatisticResult` named tuple; the shared interface remains subject to team approval.
- Report `dropped_count = 0` when no observations are removed. Count each removed observation once, including when functions call other functions.
- Use the retained observation count, `n`, for all calculations and minimum-size checks.
- Reject invalid observations immediately rather than treating them as missing. Do not return a result based on partially validated data.
- Raise a clear error when the input is empty or no observations remain after removal.

Results describe retained observations; dropping missing data does not establish that the remaining sample is representative.

## Spread Functions

| Function | Minimum retained count | Required behavior | Mathematical source |
| --- | --- | --- | --- |
| Quantile | 1 | Use Ross's percentile rule; probability `p` must be a finite built-in integer or float in `[0, 1]`, excluding booleans. | Ross, sec. 2.3.3, pp. 26-27 (PDF pp. 41-42). |
| IQR | 1 | Return the difference between the 0.75 and 0.25 quantiles using the same method. | Ross, sec. 2.3.3, p. 29, before sec. 2.4 (PDF p. 44). |
| Sample variance (planned) | 2 | Use denominator `n - 1` and Welford's stable calculation. | Definition: Ross, sec. 2.3.2, p. 24 (PDF p. 39). Algorithm: Welford (1962), pp. 419-420. |
| Sample standard deviation (planned) | 2 | Return the square root of sample variance. | Ross, sec. 2.3.2, p. 26 (PDF p. 41). |

**Quantile convention:** For sorted data and `0 < p < 1`, use the observation at one-based position `ceil(n * p)` when `n * p` is noninteger; otherwise average positions `n * p` and `n * p + 1` (Ross, sec. 2.3.3, p. 27; PDF p. 42). The contract explicitly defines the endpoints: at `p = 0` return the minimum; at `p = 1` return the maximum.

For one retained observation, quantiles equal that observation and IQR is zero; planned sample variance and standard deviation functions must raise an error. For constant data with at least two retained observations, variance, standard deviation, and IQR are zero. These requirements follow from the cited definitions and the contract's endpoint and error policies; they are not quotations from Ross.

## Errors

| Condition | Exception |
| --- | --- |
| Unsupported collection, observation type, or probability type | `TypeError` |
| Infinity in data, invalid numeric probability, or insufficient retained observations | `ValueError` |
| Numeric conversion or arithmetic exceeds documented limits | `OverflowError` |

Error messages identify the violated requirement. Invalid-observation errors include the original zero-based index; insufficient-data errors state the required and retained counts. Arithmetic overflow must not silently produce a nonfinite result.

## Acceptance Criteria

These original examples apply the cited definitions and project rules; they are not Ross textbook exercises. Input validation, quantile, and IQR cases are covered by local tests. Variance and standard deviation expectations remain implementation requirements.

| Case | Expected outcome |
| --- | --- |
| `[2, None, 4, NaN]` | Retain `[2, 4]`; report two dropped observations. |
| `[2, "4", 6]` or `[2, True, 6]` | `TypeError` at index 1. |
| `[]` or `[None, NaN]` | `ValueError` for no retained observations. |
| `[5, None]` | Quantiles return `5`; IQR returns `0`; report one dropped observation on success. Planned sample variance and standard deviation functions raise `ValueError`. |
| `[5, 5, 5]` | IQR returns zero; planned variance and standard deviation functions also return zero. |
| `[2, 4, 6, 8]` | First quartile `3`, third quartile `7`, IQR `4`; planned sample variance result `20/3`. |
| Unsorted input | Correct result without modifying the original collection. |
| Probability outside `[0, 1]`, `NaN`, or infinity | `ValueError`. |

`NaN` denotes a floating-point NaN, not a string. Tests also cover tuples, negatives, zero, ties, unsupported types, numeric limits, and probability endpoints.

Docstrings state inputs, outputs, parameters, supported values, assumptions, errors, and examples. Package code and tests use only the standard library. Controlled library comparisons state their tolerance and use matching conventions: NumPy `method="averaged_inverted_cdf"` for quantiles and `ddof=1` for future sample variance and standard deviation checks. External-library imports are restricted to the reference-check script.

## Approval

Team approval of this contract, the shared result structure, and documented numeric limits remains pending. Subsequent changes require corresponding documentation and test updates and team agreement.

## References

- Stateskol Week 1 brief: project requirements and ownership; supplied separately.
- Ross, Sheldon M. *Introduction to Probability and Statistics for Engineers and Scientists*, 6th ed.: sec. 2.3.2, pp. 24-26 (PDF pp. 39-41); sec. 2.3.3, pp. 26-29 (PDF pp. 41-44).
- Welford, B. P. (1962). *Note on a Method for Calculating Corrected Sums of Squares and Products*. *Technometrics*, 4(3), pp. 419-420 (PDF pp. 2-3).
- [NumPy quantile methods](https://numpy.org/doc/stable/reference/generated/numpy.quantile.html) and [NumPy variance](https://numpy.org/doc/stable/reference/generated/numpy.var.html): reference-library parameter settings, not Ross's Python API.