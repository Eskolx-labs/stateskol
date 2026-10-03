# Contributing to stateskol

Main is protected. Only the merge holders merge to it. Everyone else forks and
opens a pull request. Merge holders: Natnael Getahun and Barkilign Mulatu.

Code and the documentation that ships with it go to this repository. Notes,
diagrams, and explanations go to the open vault,
[Eskolx-labs/Eskolx-Open-Knowledge](https://github.com/Eskolx-labs/Eskolx-Open-Knowledge).
Every code PR links its vault note.

## Setup

1. Fork `Eskolx-labs/stateskol` on GitHub. You do not need write access.
2. Clone your fork and point it upstream:

   ```bash
   git clone https://github.com/<your-username>/stateskol.git
   cd stateskol
   git remote add upstream https://github.com/Eskolx-labs/stateskol.git
   ```

3. Use the noreply address. This repository is public and everything lands in
   history:

   ```bash
   git config user.name "Your Name"
   git config user.email "your-github-username@users.noreply.github.com"
   ```

4. Set up Python:

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   python -m pytest
   ```

## Branch and work

Branch from an updated main:

```bash
git fetch upstream
git checkout -b your-name/short-topic upstream/main
```

One branch per piece of work. Keep the package and its tests on the standard
library. Reference libraries belong only in the reference examples, never in
the package or its tests.

Commit with plain messages:

```text
feat: add ...
test: ...
docs: ...
```

## The quality bar

A finished PR holds:

1. A docstring that states inputs, outputs, parameterization, assumptions, the
   missing-value rule, errors, and examples.
2. A linked vault note, plus a tldraw diagram where one helps.
3. Hand-worked results, usual cases, boundary cases, and tests.
4. A controlled comparison against a trusted reference, with the tolerance
   stated.
5. A documentation example that runs in a clean environment.
6. A review from someone other than the author.

## Notes and diagrams

Notes live in the vault, not here:

- Create them from a template and fill the properties (`type`, `status`,
  `author`, `created`, `updated`, `tags`, `publish-status`).
- Link the note to the sources and the sibling notes it relates to.
- Most notes carry a tldraw diagram, saved under `90 Attachments/animations/`
  and embedded in the note. It must open on a fresh clone with no local setup.

New to the vault? Start at its contributing guide.

## Reviewing

The PR is the review. Check correctness first, then clarity:

1. Does the math match the source, by hand, on a small dataset you can verify?
2. Do the boundary cases behave?
3. Does the reference comparison run and pass with a stated tolerance?
4. Does the linked vault note stand alone for someone who was not in the room?
5. Is there a diagram where one would help?

Approve only when all of it holds. Leave a comment naming what you checked.

## Before you push

Search for secrets first. This repository is public:

```bash
rg -i "password|api[_-]?key|token|BEGIN.*PRIVATE KEY" .
```

No passwords, keys, tokens, or private keys in any file, ever.

## Conduct

Be direct and kind. Critique the work, not the person.
