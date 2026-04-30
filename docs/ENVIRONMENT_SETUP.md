# Environment Setup

## Prerequisites

- **Python 3.12+** — verify with `python --version`
- **uv** — fast Python package manager. Install:
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **Git** for cloning, **internet access** to install Playwright browsers and reach the demo target.

## Local install (60 seconds)

```bash
git clone https://github.com/kennyRamadhan/playwright-api-web-mobile.git
cd playwright-api-web-mobile
uv sync
uv run playwright install chromium --with-deps
```

`uv sync` installs runtime deps. To include dev deps (ruff, mypy):

```bash
uv sync --extra dev
```

## Run tests

```bash
# Everything
uv run pytest

# API only
uv run pytest tests/api

# Web only
uv run pytest tests/web

# Single test by Allure ID (matches title substring)
uv run pytest -k "API-AUTH-200-001"

# Mark filters
uv run pytest -m smoke
uv run pytest -m "not slow"

# Parallel
uv run pytest -n auto
```

## Allure reporting

Test runs write XML to `reports/allure-results/`. Render the HTML report:

```bash
# Requires Allure CLI: `brew install allure` or `scoop install allure`
allure serve reports/allure-results
```

The CI pipeline auto-publishes the latest report to GitHub Pages — see `docs/CI_OVERVIEW.md`.

## Configuration

- Environment defaults: `config/env_dev.yaml` (selected by default)
- Override per-shell with environment variables:
  ```bash
  export API_BASE_URL=https://staging.api.example.com
  export CREDENTIALS_ADMIN_EMAIL=alt@example.com
  ```
  Env vars take precedence over YAML. See `src/utils/credential_manager.py`.
- Personal secrets: copy `config/credentials.example.yaml` to `config/credentials.local.yaml` (gitignored).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `playwright._impl._errors.Error: Executable doesn't exist` | Run `uv run playwright install chromium --with-deps` |
| `httpx.ConnectError` against demo API | Check internet; demo target may be down — ping `https://api.practicesoftwaretesting.com/products` |
| `uv: command not found` after install | Restart shell or `source ~/.zshrc` (uv adds itself to PATH) |
| mypy errors on first run | `uv sync --extra dev` then `uv run mypy src/` |
