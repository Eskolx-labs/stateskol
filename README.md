# Stateskol

Descriptive statistics in pure Python, rebuilt from scratch.

Stateskol is the code side of the Eskolx Labs program. We read Ross, Introduction to Probability and Statistics for Engineers and Scientists, turn what we read into small tested functions, and prove each one by hand and against a trusted library. Pure Python with no black boxes: the package and the test suite run on the standard library alone. Numpy, pandas, scipy, and statsmodels appear only in `examples/reference_check.py` and in the vault notes, as the reference we check against, never as something our code needs.

This repo holds the package. Notes and diagrams live in the public vault, [Eskolx-labs/Eskolx-Open-Knowledge](https://github.com/Eskolx-labs/Eskolx-Open-Knowledge). Every code PR links to a vault note.

The person by person plan for the current week sits in the week brief PDF shared with the team. Read it before you touch code.

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

## Links

- Program: [eskolxlabs.org/program](https://eskolxlabs.org/program)
- Notes vault: [Eskolx-labs/Eskolx-Open-Knowledge](https://github.com/Eskolx-labs/Eskolx-Open-Knowledge)
- Book: Ross, Introduction to Probability and Statistics for Engineers and Scientists, 6th ed, Academic Press 2020.

## License

MIT. See LICENSE.
