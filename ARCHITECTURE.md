# Architecture — playwright-api-web-mobile

> **Source of truth** for all design decisions in this repository. Every architectural choice is documented here with rationale. Updates to architecture should reflect here first, then propagate to code.
>
> Version: 1.0 · Locked: 2026-04
> Stack: Python · Playwright async · pytest · Allure · uv

---

## 1. Project goal

A public, recruiter-facing QA automation portfolio demonstrating production-grade test architecture using public demo applications. The repo serves three audiences:

1. **Recruiters and hiring managers** — visual proof of senior QA capability, comparable to professional work
2. **Future employers' technical interviewers** — pattern review, code quality assessment, framework design judgment
3. **Owner (Kenny Ramadhan)** — reusable pattern library across future roles, demonstration of mental model

---

## 2. Stack decisions

### 2.1 Language: Python

**Decision:** Python 3.12+

**Rationale:**
- Mirrors the production stack at current role (Noovoleum UCO Collect)
- Strongest ecosystem for cross-discipline QA (Playwright + Appium + locust + behave)
- Career signal alignment: Python-first QA = senior modern QA convention 2024–2026
- Recruiter mental model: banking/fintech QA expects Python > JavaScript

**Alternative considered:** JavaScript/TypeScript — rejected because (1) splits identity from professional Python work, (2) mobile testing weaker in Node ecosystem, (3) fewer banking/fintech recruiters expect TS.

### 2.2 Browser automation: Playwright (async API)

**Decision:** `playwright` Python package, async API only

**Rationale:**
- Same library as professional UCO Collect work — pattern reuse
- Async aligns with modern Python concurrency
- Built-in trace viewer, screenshot/video capture, network interception
- Outpaces Selenium in stability and developer experience for SPAs (target Practice Software Testing is Angular SPA)

**Alternative considered:** Playwright sync API — rejected because async is the production pattern; consistency matters more than initial learning cost.

### 2.3 Test runner: pytest + pytest-asyncio

**Decision:** pytest as test runner, pytest-asyncio for async support, NOT Playwright Test runner

**Rationale:**
- Mirror professional setup
- pytest's fixture composition is more powerful than Playwright Test's built-in
- Existing ecosystem (pytest-xdist for parallelization, pytest-rerunfailures for flaky test handling, pytest-html for fallback reporting)
- Single runner for both API tests (httpx) and Web tests (Playwright) — unified discovery and reporting

**Alternative considered:** Playwright Test runner — rejected because it doesn't integrate cleanly with non-browser tests.

### 2.4 Reporting: Allure

**Decision:** `allure-pytest` plugin, generate XML results, render HTML reports

**Rationale:**
- Professional standard in regulated industry QA
- Same as UCO Collect work (consistency for owner)
- Step-level granularity, attachments, history, trends
- Renders well as GitHub Pages artifact (recruiter can view directly)

**Test ID convention:** Detailed in `ALLURE_TEST_IDS.md`. Pattern: `{SURFACE}-{FEATURE}-{HTTP_OR_FLOW}-{NUM}` (e.g. `WEB-LOGIN-001`, `API-AUTH-200-001`).

#### Allure observability layer

Every API call routed through `BaseService._request()` emits a structured Allure step with full request/response forensics:

- **Step name**: `{METHOD} {path}` (e.g. `POST /users/login`)
- **Pre-request attachments**: request body (JSON), query params (JSON), request headers (JSON, with `Authorization` masked)
- **Post-response attachments**: response meta (status + duration_ms + url) and full response body
- **Sensitive masking**: `password` / `token` / `authorization` keys redacted to `***` before attachment — applied recursively to nested objects

This means every recruiter or reviewer opening the Allure report sees exactly what the test exercised at the protocol level — no need to dig through source code to understand what an endpoint contract looks like.

#### Assertion helpers (`src/utils/assertions.py`)

`expect_status()` and `expect_field()` wrap common assertions in `allure.step()` blocks with actual-vs-expected attachments. Use these for any assertion where the value carries diagnostic weight; raw `assert` is fine for trivial truthiness checks where the `AssertionError` message is self-explanatory.

#### Web visual forensics

Web tests capture diagnostic artifacts at three layers — symmetric to the API observability layer above, but tuned to UI rather than protocol concerns.

**Per-step screenshots (every test, passed or failed)**

Page object public methods are decorated with `@web_step` (custom decorator in `src/utils/web_step.py`) instead of plain `@allure.step`. The decorator wraps `allure.step` with an automatic post-action viewport screenshot. Reports therefore contain a visual storyboard of the user journey — recruiters see *what happened on screen* at every step, not just step titles.

**Failure forensics (failed only)**

When a web test body fails, the conftest hook + async fixture teardown attaches:

- Final full-page screenshot
- Page HTML at the moment of failure
- Console errors and warnings collected during the test
- Network request failures collected during the test
- Final page URL
- Playwright `trace.zip` (replayable in the Playwright trace viewer)

**Playwright tracing (continuous)**

Tracing is started at context creation and stopped at context teardown. The `trace.zip` is attached to Allure only on failure (kept on disk for passes but not attached, so report size stays manageable).

**Why captures live in fixture teardown, not the makereport hook**

`pytest_runtest_makereport` runs synchronously, but Playwright is async-only in this codebase. Rather than wrestle with `loop.run_until_complete()`, the hook only stamps `item.rep_call` with the report; the async `page` and `context` fixture teardowns then decide whether to capture forensics inside the still-live event loop. See `tests/web/conftest.py` for the full pattern.

**Trade-off**

Per-step screenshots add ~200–500 ms per page interaction. Acceptable for portfolio demonstration; for high-volume CI suites this would become opt-in via marker.

### 2.5 Package manager: uv

**Decision:** `uv` (modern 2026 standard, written in Rust)

**Rationale:**
- 10x+ faster than Poetry / pip-tools for installs and lockfile generation
- Single binary, no Python version pinning issues
- Native pyproject.toml support
- Recruiter-impressive: shows awareness of modern Python tooling

**Alternative considered:** Poetry — rejected because slower and less ergonomic in 2026. requirements.txt — rejected because no lockfile = non-deterministic builds.

**Note for recruiters:** `pyproject.toml` is universally compatible with pip/Poetry/uv. Anyone can install via standard tooling regardless of preference.

### 2.6 Configuration: YAML + .env

**Decision:** YAML files for environment-specific config, `.env` for secrets (gitignored), `python-dotenv` for loading

**Rationale:**
- Mirror production pattern (.auth/credentials/{env}.yaml from UCO Collect)
- YAML readable for non-Python audiences
- .env keeps secrets out of version control
- Standard pattern recruiter recognizes

---

## 3. Architectural patterns

### 3.1 Page Object Model (POM)

**Decision:** Strict POM with base class hierarchy

**Structure:**
```
src/pages/
├── base_page.py          # BasePage — common methods (goto, wait, screenshot)
├── login_page.py         # LoginPage(BasePage)
├── product_listing_page.py
├── product_detail_page.py
├── cart_page.py
├── checkout_page.py
└── account_page.py
```

**Rules:**
- Page classes own all selectors (locators) for that page
- Page methods are user-action-named (e.g. `add_to_cart()`, NOT `click_add_to_cart_button()`)
- Page methods return Page objects (or new pages on navigation) for fluent chaining
- Tests NEVER reference selectors directly — only via page methods
- Locators use `page.get_by_role()`, `page.get_by_label()`, `page.get_by_test_id()` (semantic locators) over CSS/XPath when possible

### 3.2 BaseService pattern (API client)

**Decision:** API testing uses class-based clients extending `BaseService`, mirror UCO Collect

**Structure:**
```
src/api_clients/
├── base_service.py       # BaseService — http client, auth header injection, response parsing
├── auth_service.py       # AuthService(BaseService) — login, logout, token refresh
├── product_service.py    # ProductService — CRUD products
├── cart_service.py       # CartService — add/remove/update items
└── order_service.py      # OrderService — checkout, order history
```

**Rules:**
- Each service maps to a single resource/feature in the target API
- Methods return parsed Pydantic models, not raw dicts
- HTTP errors raise typed exceptions (not silent failures)
- Auth token managed at base level, not per service
- Services support test data setup via direct API (faster than UI for fixtures)

### 3.3 Pydantic models for API responses

**Decision:** Pydantic v2 models for all API request/response bodies

**Structure:**
```
src/models/
├── product.py            # Product, ProductList, ProductCreate, ProductUpdate
├── user.py               # User, UserCredentials, UserCreate
├── cart.py               # CartItem, Cart
└── order.py              # Order, OrderStatus, OrderCreate
```

**Rules:**
- Models validate API responses on parse — catches schema drift early
- Tests assert against model fields, not dict keys
- Models double as documentation of API contract

### 3.4 Pytest fixtures

**Decision:** Layered fixtures — root, surface-specific, feature-specific

**Structure:**
```
conftest.py                   # Root: env config, browser, async event loop
tests/conftest.py             # Test-level: data factories, allure setup
tests/api/conftest.py         # API-only: httpx client, auth tokens
tests/web/conftest.py         # Web-only: page fixtures, auth state
```

**Rules:**
- Fixtures are scoped appropriately (`session`, `module`, `class`, `function`)
- Browser context isolation: each test gets fresh context, NOT fresh browser
- Auth state reused via Playwright's `storageState` for performance
- Test data factories use Faker, parameterizable per test

### 3.5 Async-everywhere

**Decision:** All test functions async, use `pytest-asyncio` with `mode = "auto"`

**Rationale:**
- Playwright async API
- httpx async client for API tests
- Future-proof for any async dependencies

**Rule:** No mixing sync and async tests. If a test is sync, it's a bug.

---

## 4. Test organization

### 4.1 Folder structure

```
tests/
├── api/                  # API tests against api.practicesoftwaretesting.com
│   ├── test_auth.py
│   ├── test_products.py
│   ├── test_cart.py
│   ├── test_orders.py
│   └── test_users.py
└── web/                  # Web UI tests against practicesoftwaretesting.com
    ├── test_e2e_purchase.py
    ├── test_login.py
    ├── test_search.py
    └── test_account.py
```

**Phase 2 addition (deferred):**
```
tests/
└── mobile/               # Mobile tests via Appium
    ├── test_login.py
    └── test_cart.py
```

### 4.2 Test naming

**Pattern:** `test_{feature}_{scenario}_{expected_outcome}.py`

**Examples:**
- `test_login_with_valid_credentials_succeeds`
- `test_add_to_cart_with_invalid_quantity_returns_error`
- `test_checkout_with_expired_card_displays_error`

### 4.3 Test ID convention (Allure)

Detailed in `ALLURE_TEST_IDS.md`. Summary:

- API tests: `API-{FEATURE}-{HTTP_CODE}-{NUM}` (e.g. `API-AUTH-200-001`)
- Web tests: `WEB-{FEATURE}-{NUM}` (e.g. `WEB-CHECKOUT-001`)
- Mobile tests (Phase 2): `MOB-{FEATURE}-{NUM}` (e.g. `MOB-LOGIN-001`)

### 4.4 AAA pattern

Every test follows Arrange-Act-Assert:

```python
@allure.id("WEB-CART-001")
@allure.title("Add product to cart updates cart count")
async def test_add_product_to_cart(login_page, product_listing_page):
    # Arrange
    await login_page.login(VALID_USER)

    # Act
    await product_listing_page.add_first_product_to_cart()

    # Assert
    assert await product_listing_page.get_cart_count() == 1
```

Allure decorators (`@allure.id`, `@allure.title`) are **mandatory** for every test — enables filterable reporting.

---

## 5. Test data strategy

### 5.1 Demo app constraints

Practice Software Testing is **stateful** — orders persist, users are real. This means:

- Tests should clean up after themselves (delete created users, cancel orders) where possible
- Tests should be **idempotent** — same data input = same outcome
- Tests should NOT rely on specific seed data (the demo may reset periodically)

### 5.2 Data factories

**Decision:** Faker-based factories in `src/utils/data_factory.py`

```python
from faker import Faker
from src.models.user import UserCreate

fake = Faker()

def make_user(email_suffix: str = None) -> UserCreate:
    return UserCreate(
        email=email_suffix or f"{fake.user_name()}@example.test",
        password=fake.password(length=12),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
    )
```

**Rule:** Tests NEVER hardcode user/product data. Always factory-generated.

### 5.3 Fixtures for shared data

Static reference data (e.g. known admin credentials for the demo, predefined product categories) lives in `config/credentials.example.yaml` (with `.env` for actual values).

---

## 6. CI/CD architecture

### 6.1 Workflow strategy

**Decision:** Three workflows — main CI orchestrator, plus standalone API and Web runs for granular triggers

```
.github/workflows/
├── ci.yml                # Main: triggers on push/PR, routes via inputs
├── api-tests.yml         # Standalone API run (manual trigger or schedule)
├── web-tests.yml         # Standalone web run (manual trigger or schedule)
└── publish-report.yml    # Allure → GitHub Pages on main branch
```

### 6.2 ci.yml structure

Single workflow with boolean inputs to route which suite runs:

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
      run_mobile:
        description: 'Run mobile tests (Phase 2)'
        type: boolean
        default: false
```

**Rationale:** Mirror UCO Collect CI pattern. One workflow, multiple modes.

### 6.3 Allure report publication

**Decision:** Auto-publish to GitHub Pages on main branch push

**Rationale:**
- Recruiters can view live reports without cloning
- Demonstrates CI/CD competence
- Free hosting via GitHub Pages

**URL pattern:** `https://kennyramadhan.github.io/playwright-api-web-mobile/`

---

## 7. Documentation strategy

### 7.1 Three-audience documentation

| Audience | Document | Purpose |
|---|---|---|
| Recruiters | `README.md` | Hero landing — what, why, how to view reports, badges |
| Technical reviewers | `ARCHITECTURE.md` (this file) | Design decisions, rationale, alternatives considered |
| Contributors / future-self | `docs/ADDING_NEW_TEST.md` | How to add tests without breaking patterns |

### 7.2 README requirements

The README is the **single most important file**. It must:

- Open with one-line value proposition
- Include status badges (CI status, license, Python version)
- Show a screenshot or GIF of test execution OR Allure report
- Provide 60-second setup instructions
- Link to live Allure report
- Explain architectural choices in 1 paragraph (link to ARCHITECTURE.md for depth)
- List demo targets used (with disclaimers about not affiliated)
- Acknowledge inspirations (UCO Collect approach, etc.) — credibility signal

Template provided in `README_TEMPLATE.md`.

---

## 8. Quality gates

### 8.1 Pre-commit checks (manual or via pre-commit hook)

- `ruff check` — linting
- `ruff format` — formatting
- `mypy src/` — type checking (strict mode)

### 8.2 CI checks (mandatory before merge)

- All linters pass (ruff, mypy)
- Tests run successfully against the live demo target
- Allure report generates without errors
- No new flaky tests introduced (tracked via `pytest-rerunfailures`)

### 8.3 Code review checklist

- [ ] New tests follow `@allure.id` + `@allure.title` decorator pattern
- [ ] No hardcoded credentials or sensitive data
- [ ] No selectors leaking into tests (page object encapsulation enforced)
- [ ] Type hints on all public functions
- [ ] Docstrings on Page classes and Service classes

---

## 9. Out of scope (intentional non-goals)

- **Performance testing** — covered separately (lo's existing JMeter/K6 work)
- **Security testing** — out of scope for portfolio repo
- **BDD / Gherkin** — explicit choice to use plain pytest (recruiter-friendly, no domain-specific abstraction)
- **Cypress / WebdriverIO comparison** — single-tool focus
- **Multi-region testing** — Practice Software Testing is single-region; UCO Collect demonstrates this in CV

---

## 9b. Mobile testing layer

The mobile layer mirrors the web layer's screen-object pattern but is
**sync rather than async**. This is a deliberate architectural choice
rooted in tool reality:

- The Appium Python Client is sync (no async API exists)
- Mobile gestures (tap, swipe, type) are inherently sequential
- Async wrapping adds CPU/syntax overhead with no concurrency benefit

The framework remains async for API + Web because:

- `httpx` supports async clients for concurrent HTTP
- Playwright is async-first
- Parallel test execution benefits from async I/O

**Async-where-it-helps, sync-where-it-doesn't is a senior engineering
posture — consistency for its own sake is a code smell.**

Mobile observability mirrors web observability:

- `@mobile_step` decorator captures post-action screenshots
- Failure forensics: page source XML, logcat tail, current activity,
  final screenshot — attached to Allure on test failure

iOS readiness: the driver factory accepts `platform="ios"` and the iOS
capabilities file exists as a stub raising `NotImplementedError`. Real
iOS support is deferred to Phase 2.2 because it requires a macOS host
with Xcode. Screen objects already prefer
`AppiumBy.ACCESSIBILITY_ID` for cross-platform locator portability.

See [`docs/MOBILE_TESTING_GUIDE.md`](docs/MOBILE_TESTING_GUIDE.md)
for the operational guide.

---

## 10. Future expansion roadmap

### Phase 2.2 (mobile follow-up):
- iOS coverage via XCUITest (separate macOS-runner workflow)
- Visual regression testing (Playwright snapshot comparison)

### Phase 3 (long-term):
- Performance testing layer (locust integration) for the same API endpoints
- Multi-target showcase: add Sauce Demo or OrangeHRM as secondary target
- Test impact analysis (only run tests affected by code changes)

### Never:
- Real banking/fintech client data (NDA risk) — always public demo apps
- Proprietary frameworks — open ecosystem only
