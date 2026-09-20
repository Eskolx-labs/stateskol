# Stateskol

Descriptive statistics in pure Python, rebuilt from scratch.

Stateskol is the code side of the Eskolx Labs program. We read Ross, Introduction to Probability and Statistics for Engineers and Scientists, turn what we read into small tested functions, and prove each one by hand and against a trusted library. No wrappers around numpy or scipy inside the package. The package itself stays pure Python. Numpy, pandas, and scipy appear only in tests and examples, as the reference we check against.

This repo holds the package. Notes and diagrams live in the public vault, Eskolx-labs/Eskolx-Open-Knowledge. Every code PR links to a vault note.

## Week 1 scope

Ross chapter 1 plus chapter 2 sections 1 to 4. Package skeleton, numeric input contract, one missing data rule, count, min, max, range, mean, median, mode, quantiles, IQR, sample variance, sample standard deviation, frequency tables, histogram bin counts.

The full person by person plan sits in `docs/week-1-brief.pdf`. Read it before you touch code.

## Layout

```text
src/stateskol/      the package, pure Python only
  _validate.py      numeric input contract (Kaleb)
  _missing.py       missing data policy (Kaleb)
  basics.py         count, min, max, range (Kaleb)
  center.py         mean, median, mode (Philimon)
  spread.py         quantiles, IQR, variance, std (Robel)
  tables.py         frequency tables, histogram counts (Yoseph)
tests/              pytest suite, reference checks live here (Yonas assembles)
examples/           one clean environment demo per feature
docs/               week briefs and release notes
```

## Quick start

```bash
git clone https://github.com/Eskolx-labs/stateskol.git
cd stateskol
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python examples/clean_env_demo.py
```

## How work gets in

Main is protected. Only the merge holders merge, Natnael Getahun and Barkilign Mulatu. Everyone else forks the repo, branches, and opens a pull request against main. No direct pushes to main. The full workflow sits in CONTRIBUTING.md.

## Links

- Program: https://eskolxlabs.org/program
- Notes vault: https://github.com/Eskolx-labs/Eskolx-Open-Knowledge
- Book: Ross, Introduction to Probability and Statistics for Engineers and Scientists, 6th ed, Academic Press 2020. Chapters 1 and 2.1 to 2.4 for week 1.

## License

MIT. See LICENSE.
