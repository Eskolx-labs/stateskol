# Stateskol

Statistical and Machine Learning packages in pure Python, rebuilt from scratch.

Stateskol is the code side of the Eskolx Labs program: we read the sources,
turn the method into small tested functions, and prove each one by hand and
against a trusted library. The package runs on the standard library alone;
tests and reference examples may use reference libraries. Notes and diagrams
live in the public vault,
[Eskolx-labs/Eskolx-Open-Knowledge](https://github.com/Eskolx-labs/Eskolx-Open-Knowledge).
Every code PR links its vault note.

## Quick start

```bash
git clone https://github.com/Eskolx-labs/stateskol.git
cd stateskol
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,reference]"
python -m pytest
```

## Layout

```text
src/stateskol/    the package
tests/            the test suite
examples/         runnable demos and reference checks
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Links

- Notes vault: [Eskolx-labs/Eskolx-Open-Knowledge](https://github.com/Eskolx-labs/Eskolx-Open-Knowledge)
- Program: [eskolxlabs.org/program](https://eskolxlabs.org/program)

## License

MIT. See [LICENSE](LICENSE).
