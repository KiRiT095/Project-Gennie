# Contributing to Tuna

Thanks for your interest in Tuna.

Tuna is an experimental local-first AI companion. Contributions should support its core principles: persistent identity, local-first operation, understandable architecture, privacy and reliability.

## Before making changes

- Check existing issues and current project documentation.
- Keep changes focused.
- Avoid large rewrites when a small change will do.
- Do not commit `.env`, credentials, personal conversations, database dumps, voice recordings or speaker profiles.

## Development

Use a virtual environment and install the dependencies listed by the project.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the test suite before submitting changes:

```bash
pytest
```

If a change introduces a new dependency, update both dependency manifests where applicable and explain why it is needed.

## Pull requests

Include:
- What changed.
- Why it changed.
- How it was tested.
- Any new configuration or migration steps.
- Known limitations.

Please do not describe an experimental feature as production-ready unless it has been tested accordingly.
