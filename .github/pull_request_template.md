## Linked vault note

<!-- Link the vault note for this work: https://github.com/Eskolx-labs/Eskolx-Open-Knowledge. PRs without a note link stay draft. -->

- Note:
- Textbook section (Ross, chapter and pages):

## What this PR builds

<!-- One job per PR. Name the functions and the behavior change. -->

## Proof

- [ ] Hand worked result on a small dataset, shown in the note and in tests
- [ ] Usual cases, boundary cases (empty, single value, constant, ties, invalid), and tests
- [ ] Controlled comparison against numpy, pandas, scipy, or statsmodels with tolerance stated
- [ ] `python examples/clean_env_demo.py` runs on a fresh clone

## Reviews

- [ ] Reviewed by someone other than the author (name them):
- [ ] I reviewed at least two other PRs this week (link them):
  1.
  2.

## Checklist

- [ ] Standard library only in `src/stateskol` and `tests`; reference libraries only in `examples/reference_check.py`
- [ ] Docstrings state inputs, outputs, support, assumptions, and errors
- [ ] No secrets (`rg -i "password|api[_-]?key|token|BEGIN.*PRIVATE KEY" .` is clean)
