# Development workflow

1. Activate `.venv`.
2. Make one focused change at a time.
3. Run `python -m unittest discover -s tests -v`.
4. Run `python main.py` and check the UI.
5. Review `git diff`.
6. Commit a working milestone.

Suggested commit format: `feat(ui): add compact companion mode`.

Do not commit `.venv`, secrets, local databases, or machine-specific files.
