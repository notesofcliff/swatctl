# swatctl

swatctl: a small management CLI for SWAT projects.

Features:
- create-project
- create-page
- swat-set-version (replace lib/ from a git repo@tag)
- plugin-install
- plugin-set-version
- info

Install for development:
```bash
pip install -e ".[test]"
```

Run tests:

```bash
pytest -q
```

Run CLI:

```bash
swatctl --help
```