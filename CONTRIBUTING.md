# Contributing to stateskol

Same rules as the open vault. Main is protected and only the merge holders merge to it. Everyone else forks and opens pull requests.

Merge holders: Natnael Getahun and Barkilign Mulatu. Nobody else merges, including week leads and reviewers. An approval from a reviewer is a green light for a merge holder, not a merge.

## First setup

1. Fork `Eskolx-labs/stateskol` on GitHub. Use the Fork button, you do not need write access to this repo.
2. Clone your fork:

```bash
git clone https://github.com/<your-username>/stateskol.git
cd stateskol
git remote add upstream https://github.com/Eskolx-labs/stateskol.git
```

3. Check your identity. This repo is public and everything lands in history, so use the noreply address:

```bash
git config user.name "Your Name"
git config user.email "your-github-username@users.noreply.github.com"
```

4. Set up Python:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Branch and work

One branch per piece of work, branched from an updated main:

```bash
git fetch upstream
git checkout -b kaleb/basics-count-min-max upstream/main
```

Branch names start with your first name, for example `philimon/center-mean-median`, `robel/spread-variance`, `yoseph/tables-histogram`, `yonas/reference-checks`.

Commit with plain messages:

```text
feat: add count min max range with input contract
test: hand checked variance cases from Ross 2.3
docs: note link and examples for median
```

## Push and open a PR

```bash
git push -u origin kaleb/basics-count-min-max
```

Open the pull request against `Eskolx-labs/stateskol` main, not against your fork main. Fill in the PR template. A draft PR is fine from Thursday on, but it must already contain real work, not an empty skeleton.

Never push to upstream main. If GitHub refuses, that is the protection working. Do not ask for write access, the fork path is the workflow.

## What a finished PR holds

Same bar as the program page. Each feature PR holds all seven:

1. Inputs, outputs, parameterization, support, assumptions, error report, and examples, written in the docstring.
2. A vault note in Eskolx-Open-Knowledge linked to the textbook section, plus a tldraw diagram drawn with the tldraw Obsidian plugin, plus the deeper source if you used one. Link the note from the PR.
3. Hand worked results, usual cases, boundary cases, and tests.
4. A controlled comparison against a trusted library (numpy, pandas, scipy, or statsmodels) with tolerance stated.
5. Review by somebody other than the author.
6. Proof you reviewed at least two other PRs that week.
7. One documentation example that runs in a clean environment (`python examples/clean_env_demo.py` must pass on a fresh clone).

## Notes and diagrams

Notes live in the vault, not here. Create them from a template (Concept for ideas, Research for small studies), fill the properties (`type`, `status`, `author`, `created`, `updated`, `tags`, `publish-status`), and link the note to the textbook section, the papers you read, and the sibling notes it relates to. A note that links to nothing is a dead end, link it up.

Most notes carry a tldraw diagram. Draw the concept or the flow, save the scene under `90 Attachments/animations/` in the vault, and embed it in the note. Diagrams must open on a fresh clone with no local setup.

## Reviewing

The PR is the review. When you review, check correctness first, then clarity:

1. Does the math match the book, by hand, on a small dataset you can verify?
2. Do boundary cases behave: empty input, single value, constant values, tied values, invalid values?
3. Does the reference comparison run and pass with a stated tolerance?
4. Does the linked vault note stand alone for someone who was not in the room?
5. Is there a diagram where one would help?
6. Is the code pure Python inside `src/stateskol`, with numpy and friends only in tests and examples?

Approve only when all six hold. Leave a comment naming what you checked by hand.

## Before you push

Search for secrets first. This repo is public:

```bash
rg -i "password|api[_-]?key|token|BEGIN.*PRIVATE KEY" .
```

No passwords, keys, tokens, or private keys in any file, ever.

## Conduct

Be direct and kind. Critique the work, not the person. Notes are written by learners, not experts, and that is the point.
