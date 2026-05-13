# Project Structure

A folder-by-folder map of the repository. Use this alongside
`docs/LEARNING_PATH.md` to find your way around. Every path below is
real and was generated from the actual repository layout, not assumed.

---

## Top-level layout

```
playwright-api-web-mobile/
├── .github/                 # CI/CD workflows (GitHub Actions)
├── config/                  # Per-environment YAML config (URLs, defaults)
├── docs/                    # Project documentation (you are here)
├── src/                     # Production framework code (clients, pages, models, utils)
├── tests/                   # Test specifications (api/, web/, future mobile/)
├── conftest.py              # Root pytest fixtures — browser, page, credentials
├── pyproject.toml           # Project metadata, dependencies, tool configs (uv-managed)
├── uv.lock                  # Pinned dependency versions for reproducible installs
├── ALLURE_TEST_IDS.md       # Naming convention for @allure.id() across tests
├── ARCHITECTURE.md          # Design decisions and the rationale for each
├── CLAUDE.md                # Agent collaboration rules (for AI-assisted work)
├── README.md                # Project intro, badges, quick start, recruiter view
├── README_TEMPLATE.md       # Reference template kept for future fork-ability
└── LICENSE                  # MIT
```

Each top-level entry is intentional. Anything not on this list (caches,
virtual environments, build artifacts) is ignored by `.gitignore`.

---

## src/ — Production code under test

The `src/` folder holds everything that is **not** a test specification
itself: API clients, page objects, data models, and shared utilities.
Tests import from here; nothing in `src/` imports from `tests/`.

```
src/
├── api_clients/
├── pages/
├── models/
└── utils/
```

### src/api_clients/

**Purpose:** HTTP client classes for the Practice Software Testing REST API.

**Pattern:** every client extends `BaseService` (in `base_service.py`).
`BaseService` owns the httpx async client, auth token state, error
handling, and Allure step instrumentation. Subclasses define
resource-specific methods like `login()` or `list_products()`.

To add a new client: create a new file here, subclass `BaseService`,
write methods that call `self._request(...)`. No plumbing required.

```
src/api_clients/
├── base_service.py          # Foundation — every client extends this
├── auth_service.py          # /users/login, /users/refresh, /users/logout
├── user_service.py          # /users/me, /users (admin list/CRUD)
├── product_service.py       # /products listing, search, CRUD
├── cart_service.py          # /carts (create, add item, update, remove)
└── order_service.py         # /orders (create from cart, list, fetch)
```

**Sample to read first:** `auth_service.py` — fully commented as the
canonical example of a `BaseService` subclass.

### src/pages/

**Purpose:** Playwright page objects for the Practice Software Testing
web UI. One class per page (or per coherent UI region).

**Pattern:** every page extends `BasePage`. `BasePage` owns the
Playwright `Page` reference, base URL, navigation helpers, and the
`by_test_id()` convenience for `data-test` attribute selectors.
Subclasses define `@property` accessors for locators and async methods
for user actions (`login`, `add_to_cart`).

Selectors live on the page class, never in tests. Tests call methods.

```
src/pages/
├── base_page.py             # Foundation — every page extends this
├── login_page.py            # /auth/login form
├── register_page.py         # /auth/register form
├── product_listing_page.py  # / (home grid + search/sort/filter)
├── product_detail_page.py   # /product/<id>
├── cart_page.py             # /checkout step 1 (cart contents)
├── checkout_page.py         # /checkout step 2-4 (address, payment, confirm)
└── account_page.py          # /account (post-login dashboard)
```

**Sample to read first:** `login_page.py` — fully commented as the
canonical example of a page object.

### src/models/

**Purpose:** Pydantic v2 models representing API request and response
contracts. Models validate structure on construction, so a contract
change in the upstream API surfaces as a clear validation error
instead of a `KeyError` deep inside a test.

```
src/models/
├── user.py                  # LoginRequest, LoginResponse, User, UserCreate
├── product.py               # Product, ProductList, ProductCreate
├── cart.py                  # Cart, CartItem
└── order.py                 # Order, OrderCreate, OrderItem
```

**Sample to read first:** `user.py` — fully commented.

### src/utils/

**Purpose:** cross-cutting helpers used by both API and Web tests.

```
src/utils/
├── credential_manager.py    # Load credentials/URLs from YAML + .env
├── data_factory.py          # Faker-based test data factories
├── assertions.py            # Allure-aware assertion helpers (expect_status, expect_field)
├── web_step.py              # @web_step decorator: allure.step + auto-screenshot (async)
└── mobile_step.py           # @mobile_step decorator: allure.step + auto-screenshot (sync)
```

### src/mobile/

**Purpose:** Appium-driven mobile test layer targeting the
[Sauce Labs my-demo-app-rn](https://github.com/saucelabs/my-demo-app-rn)
React Native demo. **Sync, not async** — Appium Python Client has no
async API; see `ARCHITECTURE.md` for rationale.

**Pattern:** every screen extends `BaseScreen`. The driver factory is
the single choke point for platform abstraction (Android first,
iOS-ready stub).

```
src/mobile/
├── driver_factory.py        # get_driver(platform) — Appium WebDriver
├── base_screen.py           # Foundation — every screen extends this
├── capabilities/
│   ├── android.py           # UiAutomator2 caps (env-overridable)
│   └── ios.py               # Stub — raises NotImplementedError (Phase 2.2)
└── screens/
    ├── login_screen.py      # Sign-in flow (canonical example)
    ├── product_list_screen.py
    ├── product_detail_screen.py
    ├── cart_screen.py
    └── checkout_screen.py
```

**Sample to read first:** `login_screen.py` — fully commented.

**Samples to read first:** `credential_manager.py` and `assertions.py`
— both fully commented.

---

## tests/ — Test specifications

Tests are organized by surface (API vs Web vs future Mobile). Each
surface has its own `conftest.py` with surface-specific fixtures —
see `docs/CONFTEST_GUIDE.md` for the full picture.

```
tests/
├── conftest.py              # Test-level fixtures (data factories) — applies to all tests
├── api/
│   ├── conftest.py          # API-only fixtures (service clients, tokens)
│   ├── test_auth.py         # Login, refresh, logout, 401 contracts
│   ├── test_users.py        # /users CRUD and admin/non-admin authorization
│   ├── test_products.py     # /products listing, filtering, admin mutations
│   ├── test_cart.py         # /carts add/update/remove
│   └── test_orders.py       # /orders lifecycle
├── web/
│   ├── conftest.py          # Web-only fixtures (page objects)
│   ├── test_login.py        # Login form happy/error paths
│   ├── test_search.py       # Product search + empty state
│   ├── test_account.py      # Register + post-login browse
│   └── test_e2e_purchase.py # End-to-end cart/checkout flows
└── mobile/
    ├── conftest.py          # Sync driver + screen fixtures + failure forensics
    ├── test_login.py        # MOB-LOGIN-001/002
    ├── test_browse.py       # MOB-BROWSE-001/002
    ├── test_cart.py         # MOB-CART-001
    └── test_checkout.py     # MOB-CHECKOUT-001 (E2E purchase)
```

### tests/conftest.py at root vs nested

Three layers of `conftest.py` exist on purpose:

1. **`/conftest.py` (repo root)** — provides browser/page fixtures,
   credentials, and the async event loop policy. Available to every test.
2. **`tests/conftest.py`** — test-level shared fixtures (e.g. random
   user factory). Available to every test under `tests/`.
3. **`tests/api/conftest.py` and `tests/web/conftest.py`** — surface-specific
   fixtures (service clients vs page objects). Available only to tests
   in that surface.

The reasoning behind the split is documented in `docs/CONFTEST_GUIDE.md`.

---

## docs/ — Project documentation

```
docs/
├── LEARNING_PATH.md         # Recommended reading order for new readers
├── PROJECT_STRUCTURE.md     # This file
├── CONFTEST_GUIDE.md        # Fixture inheritance, scopes, decision tree
├── ENVIRONMENT_SETUP.md     # Local environment + credential setup
├── ADDING_NEW_TEST.md       # Step-by-step for adding a new test
└── CI_OVERVIEW.md           # GitHub Actions workflow + Allure publish flow
```

The three top files are the suggested entry points for someone new to
the repo. The remaining three are task-oriented references to come back
to when you actually need them.

---

## .github/workflows/ — CI/CD

```
.github/workflows/
├── ci.yml                   # Main pipeline: lint + API + Web on push/PR
├── api-tests.yml            # Standalone API test run (manual / scheduled)
├── web-tests.yml            # Standalone Web test run (manual / scheduled)
└── publish-report.yml       # Build Allure report and deploy to GitHub Pages
```

`ci.yml` is the gate for `main`. `publish-report.yml` runs on both
success and failure so the live report shows real signal, not a curated
green-only view.

---

## config/ — Environment configuration

```
config/
├── credentials.example.yaml # Template — copy and fill in for your env
├── env_dev.yaml             # Dev environment URLs and default test users
└── env_qa.yaml              # QA environment (placeholder for future use)
```

`credential_manager.py` (in `src/utils/`) reads these files. Real
secrets, when needed, come from a `.env` file (gitignored) — env vars
take precedence over YAML.

---

## Configuration files at root

- **`pyproject.toml`** — project metadata, runtime/dev dependencies,
  and tool configs:
  - `[tool.pytest.ini_options]` — test discovery rules, asyncio mode, markers
  - `[tool.ruff]` — linter rules
  - `[tool.mypy]` — type checker rules (strict)
  - `[tool.uv]` — uv-specific settings
- **`uv.lock`** — pinned, hashed dependency tree for reproducible installs
- **`.python-version`** — Python interpreter version pin (used by uv)
- **`.gitignore`** — caches, venv, build artifacts, secrets

There is no separate `pytest.ini`, `mypy.ini`, or `.ruff.toml` — all
tool config is consolidated in `pyproject.toml`.

---

## How to navigate — quick reference

| I want to... | Open |
|---|---|
| Add a new API test | `tests/api/` — copy the closest existing `test_*.py` |
| Add a new Web test | `tests/web/` — copy the closest existing `test_*.py` |
| Add a new API endpoint client | `src/api_clients/` — extend `BaseService` (model on `auth_service.py`) |
| Add a new page object | `src/pages/` — extend `BasePage` (model on `login_page.py`) |
| Add a new Pydantic model | `src/models/` — group by resource family (model on `user.py`) |
| Add a fixture used by all tests | `tests/conftest.py` (test-level) or root `conftest.py` (browser/page) |
| Add a fixture used by only API or Web | `tests/api/conftest.py` or `tests/web/conftest.py` |
| Change credentials or environment URLs | `config/env_<env>.yaml` and/or `.env` (gitignored) |
| Modify CI behaviour | `.github/workflows/` |
| Understand a design choice | `ARCHITECTURE.md` |
| Find the test ID convention | `ALLURE_TEST_IDS.md` |
| Understand fixture inheritance | `docs/CONFTEST_GUIDE.md` |
