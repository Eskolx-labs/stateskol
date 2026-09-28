# Stateskol

Statistical and Machine Learning packages in pure Python, rebuilt from scratch.

Stateskol is the code side of the Eskolx Labs program. We read Ross, Introduction to Probability and Statistics for Engineers and Scientists, turn what we read into small tested functions, and prove each one by hand and against a trusted library. Pure Python with no black boxes: the package and the test suite run on the standard library alone. Numpy, pandas, scipy, and statsmodels appear mostly only in `examples/reference_check.py` and in the vault notes, as the reference we check against, never as something our code needs.

This repo holds the package. Notes and diagrams live in the public vault, [Eskolx-labs/Eskolx-Open-Knowledge](https://github.com/Eskolx-labs/Eskolx-Open-Knowledge). Every code PR links to a vault note.

## Layout

```text
src/stateskol/
  descriptive.py    the whole week: contract, missing rule, summaries
tests/
  test_descriptive.py   pytest suite, stdlib only, hand computed values
examples/
  clean_env_demo.py     runs with nothing installed but the package
  reference_check.py    the one file allowed to import numpy
```

## Quick start

```bash
git clone https://github.com/Eskolx-labs/stateskol.git
cd stateskol
python -m venv .venv && source .venv/bin/activate
pip install -e . --no-deps
pip install pytest
python -m pytest
python examples/clean_env_demo.py
```

## Input Validation, Quantiles, and IQR

The current contribution implements three functions in `stateskol.descriptive`:

| Function | Result |
| --- | --- |
| `prepare_data(data, *, min_count=1)` | `PreparedData(values, dropped_count)` |
| `quantile(data, probability)` | `StatisticResult(value, dropped_count)` |
| `iqr(data)` | `StatisticResult(value, dropped_count)` |

Inputs are built-in lists or tuples of built-in integers and finite floats.
`None` and floating-point `NaN` are removed and counted. Invalid observations
raise an error; the original collection is preserved. Quantiles follow Ross's
percentile rule, equivalent to NumPy's `averaged_inverted_cdf` convention, not
its default linear method (Ross, 6th ed., sec. 2.3.3, printed pp. 26-27).

With the package installed:

```python
from stateskol.descriptive import iqr, quantile

data = [8, None, 2, 6, 4]
print(quantile(data, 0.25))
print(iqr(data))
```

Expected output:

```text
StatisticResult(value=3, dropped_count=1)
StatisticResult(value=4, dropped_count=1)
```

The standard-library test suite can also be run without pytest:

```bash
python -m unittest discover -s tests -p test_descriptive.py -v
python -m doctest src/stateskol/descriptive.py -v
```

The optional reference check requires NumPy with the named quantile method
(introduced in NumPy 1.22), using a release compatible with the interpreter:

```bash
python examples/reference_check.py
```

Local verification covers 29 unit tests, seven docstring examples, and 198
NumPy comparisons. See the [input contract](docs/input-contract.md),
[validation interface](docs/input-validation.md),
[quantile and IQR documentation](docs/quantiles.md), and
[reference results](docs/reference-validation.md) for details and limitations.

Sample variance, standard deviation, the published vault note and diagram,
and a populated clean-environment demo remain pending. The shared input
contract also awaits team approval. These local checks do not establish
upstream CI or PR approval.

## Links

- Program: [eskolxlabs.org/program](https://eskolxlabs.org/program)
- Notes vault: [Eskolx-labs/Eskolx-Open-Knowledge](https://github.com/Eskolx-labs/Eskolx-Open-Knowledge)
- Book: Ross, Introduction to Probability and Statistics for Engineers and Scientists, 6th ed, Academic Press 2020.

## License

MIT. See LICENSE.
