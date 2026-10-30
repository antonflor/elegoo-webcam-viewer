# Contributing

## Development setup

Use Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
python scripts/demo_camera.py   # simulated printer cameras, no hardware needed
```

Use a focused branch, update the SDD when behavior or scope changes, and include tests for new
domain or persistence behavior. Do not commit printer IP addresses, credentials, screenshots,
or proprietary ELEGOO application assets. README screenshots must come from the demo camera
(`scripts/demo_camera.py`), never from a real printer or home network.

## Commit and pull request expectations

- Explain the user problem and acceptance criteria.
- Keep platform claims tied to actual test results.
- Update `CHANGELOG.md` for user-visible changes.
- Include before/after screenshots for UI changes.
- Mark printer-control changes as safety-sensitive.
