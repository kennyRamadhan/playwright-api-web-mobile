# Playwright API · Web · Mobile — QA Automation Framework

Production-grade test automation framework covering REST API, Web UI, and Mobile testing through public demo applications. Built with Python, Playwright async, pytest, Appium, and Allure — the same stack I use in regulated industry production work.

> **Status:** API + Web tests live (Day 1). Mobile testing (Appium) is Phase 2 — currently in development. The framework is designed mobile-ready from day one.

[![CI](https://github.com/kennyRamadhan/playwright-api-web-mobile/actions/workflows/ci.yml/badge.svg)](https://github.com/kennyRamadhan/playwright-api-web-mobile/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/playwright-async-green.svg)](https://playwright.dev/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> The live Allure report badge / link will be added once the publish-report workflow has run on `main` and GitHub Pages is enabled. See `docs/CI_OVERVIEW.md`.

---

## What this is

A complete QA automation portfolio piece showcasing:

- **Production-grade architecture** — Page Object Model, BaseService API client pattern, layered pytest fixtures, async-everywhere
- **Multi-surface testing** — REST API + Web UI live; Mobile (Phase 2) sharing data factories, credential management, and Allure reporting in a unified framework
- **CI/CD integration** — GitHub Actions workflows with conditional routing, Allure reports auto-published to GitHub Pages
- **Recruiter-friendly** — Live Allure report viewable without cloning, comprehensive documentation, clean code patterns

This is **NOT** a tutorial repository or a basic Playwright starter. The patterns mirror real production testing infrastructure from regulated banking, fintech, and capital markets work (anonymized per NDA).

---

## For QA learners

If you're a junior QA engineer or transitioning into automation, this repo is designed to be a learning resource. Start here:

- [docs/LEARNING_PATH.md](docs/LEARNING_PATH.md) — recommended reading order
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) — folder-by-folder guide
- [docs/CONFTEST_GUIDE.md](docs/CONFTEST_GUIDE.md) — fixture inheritance explained

Representative sample files have full technical comments. Other files follow the same pattern — see file headers for cross-references.

---

## Demo targets

Tests run against publicly available demo applications. **No real banking/fintech client data is ever used** (NDA compliance).

### Day 1 (live)

**Practice Software Testing (Toolshop)** — full-stack e-commerce demo:

- Web UI: [practicesoftwaretesting.com](https://practicesoftwaretesting.com)
- REST API: [api.practicesoftwaretesting.com](https://api.practicesoftwaretesting.com/api/documentation)

The web UI and REST API share the same backend, enabling hybrid testing strategies (API-driven test data setup + UI assertions, etc).

### Phase 2 (in development)

**Sauce Labs Demo App** — React Native mobile application:

- Source: [github.com/saucelabs/my-demo-app-rn](https://github.com/saucelabs/my-demo-app-rn)
- Coverage: Android-first via Appium, iOS later if scope allows

> **Disclaimer:** I am not affiliated with Practice Software Testing or Sauce Labs. Their applications are used solely as public testing targets under respective terms of use. Thanks to maintainers for providing high-quality demo platforms for the QA community.

---

## Live Allure report

After every push to `main`, the latest Allure report is published to GitHub Pages at `https://kennyRamadhan.github.io/playwright-api-web-mobile/` (link goes live after the first successful CI run on `main`).

The report includes:
- **Per-API-call request/response forensics** — every HTTP call routed through BaseService emits a structured step with request body, headers (auth-masked), response status, duration, and response body
- Pass/fail summary with trend over time
- Per-test execution detail with steps, screenshots, network logs
- Categorization by feature area, severity, and test type
- Historical comparison across the last 20 runs

---

## Quick start (60 seconds)

Prerequisites: Python 3.12+, [`uv`](https://github.com/astral-sh/uv) (recommended) or pip.

```bash
# Clone
git clone https://github.com/kennyRamadhan/playwright-api-web-mobile.git
cd playwright-api-web-mobile

# Install dependencies (uv is fastest)
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Run all tests
uv run pytest

# Run only API tests
uv run pytest tests/api

# Run only Web tests
uv run pytest tests/web

# Generate Allure report
uv run allure serve reports/allure-results
```

Alternative without uv:
```bash
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# or .venv\Scripts\activate         # Windows
pip install -e .
playwright install chromium
pytest
```

See [`docs/ENVIRONMENT_SETUP.md`](docs/ENVIRONMENT_SETUP.md) for detailed setup including CI environment.

---

## Repository structure

```
.
├── tests/
│   ├── api/                  # REST API tests
│   │   ├── test_auth.py
│   │   ├── test_products.py
│   │   ├── test_cart.py
│   │   ├── test_orders.py
│   │   └── test_users.py
│   └── web/                  # Web UI tests
│       ├── test_login.py
│       ├── test_search.py
│       ├── test_e2e_purchase.py
│       └── test_account.py
├── src/
│   ├── api_clients/          # BaseService pattern API clients
│   ├── pages/                # Page Object Model
│   ├── models/               # Pydantic models for API responses
│   └── utils/                # Faker-based data factories, helpers
├── config/
│   ├── env_dev.yaml
│   ├── env_qa.yaml
│   └── credentials.example.yaml
├── docs/
│   ├── ADDING_NEW_TEST.md
│   ├── ENVIRONMENT_SETUP.md
│   └── CI_OVERVIEW.md
├── .github/workflows/
│   ├── ci.yml
│   ├── api-tests.yml
│   ├── web-tests.yml
│   └── publish-report.yml
├── ARCHITECTURE.md
├── ALLURE_TEST_IDS.md
└── pyproject.toml
```

---

## Architectural choices

A summary — for full rationale see [`ARCHITECTURE.md`](ARCHITECTURE.md).

| Decision | Choice | Why |
|---|---|---|
| Language | Python 3.12+ | Mirrors production stack; strong cross-discipline ecosystem (web, API, mobile) |
| Browser | Playwright async | Trace viewer, network interception, modern SPA support |
| Runner | pytest + pytest-asyncio | Mature fixtures, parallel execution, unified for API + Web |
| Reporting | Allure | Industry standard; step-level granularity; live GitHub Pages publication |
| API testing | httpx async + Pydantic models | Type-safe, fast, mirrors BaseService production pattern |
| Page model | Strict POM with base hierarchy | Selector encapsulation, readable tests, refactor-resilient |
| Package manager | uv | Modern 2026 standard, 10x faster than Poetry |

---

## Test ID convention

All tests use Allure IDs following a structured naming pattern:

- API tests: `API-{FEATURE}-{HTTP_CODE}-{NUM}` (e.g. `API-AUTH-200-001`)
- Web tests: `WEB-{FEATURE}-{NUM}` (e.g. `WEB-CHECKOUT-001`)
- Mobile tests (Phase 2): `MOB-{FEATURE}-{NUM}` (e.g. `MOB-LOGIN-001`)

See [`ALLURE_TEST_IDS.md`](ALLURE_TEST_IDS.md) for the full convention.

---

## CI/CD pipeline

The CI architecture mirrors my production work — boolean-flag-driven workflow that routes test suites:

```yaml
# Trigger from GitHub Actions UI:
- run_api: true/false
- run_web: true/false
- run_mobile: true/false   # Phase 2
```

This allows:
- **Smoke runs** — quick API-only execution on every PR
- **Full regression** — all surfaces on main branch push
- **Targeted debugging** — single suite for investigating failures

See [`docs/CI_OVERVIEW.md`](docs/CI_OVERVIEW.md) for the full pipeline architecture.

---

## Roadmap

- [x] **Day 1**: API tests (24 covering auth/products/cart/orders/users) + Web UI tests (10 covering login/browse/search/cart-add) + CI + Allure publishing
- [ ] **Phase 2**: Mobile testing via Appium ([Sauce Labs Demo App](https://github.com/saucelabs/my-demo-app-rn)); also restoring the deferred web checkout flow with `storageState`-backed auth + API-seeded cart fixtures (5 tests currently skipped with documented reasons)
- [ ] **Phase 3**: Visual regression (Playwright snapshot comparison)
- [ ] **Phase 4**: Performance testing layer (locust integration on same API endpoints)

---

## About

I'm **Kenny Ramadhan**, a Senior QA Engineer based in Jakarta with 6+ years across regulated industries — banking, fintech, capital markets, and multi-region SaaS. This repository represents my approach to QA engineering as an architectural discipline.

- Portfolio: [kennyramadhan.com](https://kennyramadhan.com)
- LinkedIn: [linkedin.com/in/kenny-ramadhan-704849184](https://linkedin.com/in/kenny-ramadhan-704849184)
- GitHub: [github.com/kennyRamadhan](https://github.com/kennyRamadhan)

Open for Senior QA and QA Automation roles. Available for full-time and freelance collaboration.

---

## License

[MIT](LICENSE) — feel free to fork and adapt for your own portfolio. Credit is appreciated but not required.

---

## Acknowledgments

- [Practice Software Testing](https://practicesoftwaretesting.com) by Vincent Bouvier and the QA community for providing a high-quality demo platform
- [Playwright](https://playwright.dev/) team at Microsoft
- [Allure Report](https://allurereport.org/) team
- The QA community for sharing patterns and conventions
