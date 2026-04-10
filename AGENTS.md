# Repository Guidelines

## Project Structure & Module Organization
This repository uses a `src/` layout. The reusable client lives in `src/ruzclient/`, with HTTP transports in `src/ruzclient/http/` and endpoint-specific modules under `src/ruzclient/http/endpoints/`. The Telegram bot code is in `src/ruzbot/`; bot-oriented env loading lives in `src/ruzbot/settings.py` (not in `ruzclient`). Tests are under `tests/` and use fake transports and fixtures to avoid real network calls. CSV data files in the repo root are sample inputs, not generated build artifacts.

## Build, Test, and Development Commands
- `python -m pip install -e .[dev]` installs the package in editable mode with test dependencies.
- `python -m pytest` runs the full test suite from `tests/`.
- `python -m ruzclient` runs the package entry point if you want to exercise the client CLI/module behavior.
- `python -m ruzbot.main` starts the bot entry point; it expects `BOT_TOKEN` and related settings in the environment or `.env`.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, `snake_case` for functions and modules, `PascalCase` for classes, and explicit type hints on public APIs. Prefer small, focused modules and keep HTTP-specific logic inside `src/ruzclient/http/`. There is no formatter or linter configured in `pyproject.toml`, so match the surrounding code and keep docstrings/comments short and specific.

## Testing Guidelines
The project uses `pytest` with `pytest-asyncio` in auto mode. Name tests `test_*.py` and keep fixtures in `tests/conftest.py` when they are shared. Prefer deterministic tests with mocked transports; do not hit the real server unless you are writing an integration test that is clearly marked and isolated.

## Commit & Pull Request Guidelines
Recent commits use short, imperative prefixes such as `fix(bot): ...` and `feat(bot): ...`. Follow that pattern when possible. Pull requests should include a clear summary, the behavioral change, and the tests you ran. If the change affects bot output or UI flow, include screenshots or sample messages when useful.

## Security & Configuration Tips
Do not commit secrets. Local settings belong in `.env`, and the repo has a history of token leakage, so double-check environment files before pushing. When changing auth or transport code, verify both `X-API-Key` and fallback behaviors in tests.
