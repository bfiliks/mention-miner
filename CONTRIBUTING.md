# Contributing
1. Open an issue describing the change.
2. Fork and create a feature branch.
3. Add tests for new behavior.
4. Submit a PR with a concise description and screenshots if UI changes.

## Dev setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
python -m spacy download en_core_web_trf
```
