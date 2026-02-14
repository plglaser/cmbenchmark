# Workspace Instructions

## Python environment
- Always use the project virtualenv for Python commands.
- Use `.venv/bin/python` instead of `python` or `python3`.
- Use `.venv/bin/python -m pytest` for tests.

## Quick checks
- Parser/unit tests: `.venv/bin/python -m pytest -q tests/unit/test_ecore_parser.py`
- Full unit tests: `.venv/bin/python -m pytest -q tests/unit`

## If `.venv` is missing
- Create it: `python3 -m venv .venv`
- Install deps: `.venv/bin/python -m pip install -e .`
- Install test deps: `.venv/bin/python -m pip install pytest`
