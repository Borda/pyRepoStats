# Contributing

Any help or suggestions are welcome.

- **Questions and ideas**: use [Discussions](https://github.com/Borda/pyRepoStats/discussions), the Q&A category is the place for usage help.
- **Bugs and feature requests**: open an [issue](https://github.com/Borda/pyRepoStats/issues/new/choose).

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . -r tests/requirements.txt
SHOW_FIGURE=0 pytest tests src
```

Linting and formatting are pinned in `.pre-commit-config.yaml`, run them with `pre-commit run --all-files`.

## Building these docs

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

The site is rebuilt and published to GitHub Pages on every push to `main`.
