# CI / CD Overview

Two GitHub Actions workflows run this repo:

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | push, PR, manual | Lint + run API + Web tests, upload Allure artifacts |
| `publish-report.yml` | on successful `ci.yml` (main) | Merge artifacts, render Allure HTML, deploy to GitHub Pages |

## Conditional routing — boolean flags

Manual runs from the Actions tab accept boolean inputs to route which suites execute. This mirrors the production pattern at Noovoleum UCO Collect — one workflow, multiple modes.

```yaml
on:
  workflow_dispatch:
    inputs:
      run_api:
        description: 'Run API tests'
        type: boolean
        default: true
      run_web:
        description: 'Run web tests'
        type: boolean
        default: true
```

Each test job is gated:

```yaml
api-tests:
  if: ${{ github.event_name != 'workflow_dispatch' || inputs.run_api }}
```

Result:

- **PR / push:** both flags default-true → full suite
- **Smoke (UI debug):** open Actions → Run workflow → uncheck `run_api` → Web only
- **Targeted regression:** flip the matching flag, leave the rest off

## Triggering manually

1. GitHub → Actions tab → CI workflow → **Run workflow**
2. Pick the branch (default: `main`)
3. Toggle the suite flags
4. Run

The Allure publish workflow is fully automated — no manual trigger needed.

## Artifact and Allure flow

```
ci.yml
 ├─ lint           (ruff check / ruff format / mypy)
 ├─ api-tests      → uploads `allure-results-api` artifact
 └─ web-tests      → uploads `allure-results-web` artifact
                            │
                            ▼ (on success, main only)
publish-report.yml
 ├─ download artifacts via workflow_run.id
 ├─ merge into combined-results/
 ├─ render Allure HTML (history kept across last 20 runs)
 └─ deploy to GitHub Pages
```

Live report URL: **https://kennyRamadhan.github.io/playwright-api-web-mobile/**

## Local equivalents

```bash
# Lint
uv run ruff check . && uv run ruff format --check . && uv run mypy src/
# Tests with Allure output
uv run pytest --alluredir=reports/allure-results
# Render report
allure serve reports/allure-results
```
