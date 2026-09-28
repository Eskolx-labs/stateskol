# Input Validation

The `prepare_data` helper implements the [numeric input contract](input-contract.md) and is shared by quantile and IQR calculations. Implementation is not a record of team approval of the contract.

## Interface

`prepare_data(data, *, min_count=1)` accepts a built-in list or tuple. `min_count` is keyword-only and must be a positive built-in integer.

It returns a `PreparedData` named tuple:

| Field | Contents |
| --- | --- |
| `values` | An immutable tuple of retained integers and finite floats, preserving order, duplicates, and numeric types. |
| `dropped_count` | The number of removed `None` and floating-point `NaN` observations. |

With `src` on the Python import path:

```python
from stateskol.descriptive import prepare_data

prepared = prepare_data([2, None, 4, float("nan")])
print(prepared.values)
print(prepared.dropped_count)
```

Expected output:

```text
(2, 4)
2
```

Use `min_count=2` when preparing data for future sample variance or standard deviation functions. The minimum-count check runs after missing values are removed. Statistical functions must carry the dropped count into their public results.

## Validation Rules

1. Reject unsupported collection types and invalid `min_count` values.
2. Inspect observations in their original order.
3. Remove `None` and floating-point `NaN`, incrementing the dropped count.
4. Reject unsupported observation types, including booleans and numeric subclasses, with `TypeError`. Reject infinity with `ValueError`.
5. Report invalid observations using their original zero-based indexes, including positions occupied by missing values.
6. Reject insufficient retained data with `ValueError`, stating the required count, retained count, and dropped count.
7. Return a new immutable result without modifying the input or returning partially validated data.

The helper preserves Python integers exactly, including very large integers, and accepts finite Python floats. It performs no numeric conversion or statistical arithmetic. Successful validation does not guarantee every calculation is representable as a float; each statistical function documents its conversion, rounding, and overflow behavior.

## Verification

Implementation: [src/stateskol/descriptive.py](../src/stateskol/descriptive.py). Tests: [tests/test_descriptive.py](../tests/test_descriptive.py).

Run from the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_descriptive.py -v
python -m doctest src/stateskol/descriptive.py -v
```

`PYTHONPATH=src` makes the local source importable without a package installation; it can be omitted after installing the package. Neither command requires third-party dependencies. Package metadata requires Python 3.10 or newer; upstream CI tests Python 3.10, 3.11, and 3.12.

Input coverage includes lists and tuples; negatives, zero, and duplicates; mixed missing values; unsupported types; infinity; empty and all-missing data; post-removal minimum sizes; original error indexes; unchanged input; and large integers and finite float limits. The suite also covers the [quantile and IQR implementation](quantiles.md).

These checks do not establish a clean package installation or upstream CI success. See [reference validation](reference-validation.md) for the separate NumPy comparison.

## References

- [Numeric input contract](input-contract.md): software rules for input types, missing values, errors, and results.
- Stateskol Week 1 brief: numeric input contract, missing-data policy, fail-fast validation, and boundary evidence; supplied separately.
- Ross, Sheldon M. *Introduction to Probability and Statistics for Engineers and Scientists*, 6th ed., sec. 2.3.2, printed p. 24 (PDF p. 39): sample variance uses `n - 1`, requiring at least two retained observations. PDF pages refer to the supplied study copy.