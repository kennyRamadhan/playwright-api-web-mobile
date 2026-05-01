# Learning Path for Junior QA Engineers

## Who this is for

A junior or transitioning QA engineer who wants to understand
production-grade test automation by reading a real, working framework.

This guide assumes you are comfortable with manual testing concepts
(test cases, assertions, environments, regression suites) and basic
Python (functions, classes, imports). It does **not** assume prior
experience with Python `async` / `await`, Playwright, pytest fixtures,
or Allure reporting — those concepts are introduced in the right order
below.

If you can read a function and roughly guess what it does, you have
enough to start. If a piece of syntax is new, the recommended sample
files all have inline comments explaining the *why* behind the choice.

---

## Recommended reading order

The order matters. Each step builds on the previous one. Skipping ahead
will leave gaps that show up later.

### Step 1 — Understand the repo (15 min)

- [ ] Read `README.md` — project intro, demo target, technology stack
- [ ] Read `docs/PROJECT_STRUCTURE.md` — folder-by-folder map
- [ ] Skim `ARCHITECTURE.md` — design decisions and the rationale behind them. You can skip the deep details on the first pass; come back after Step 4

**Goal:** know what the project is, where files live, and what the
architectural style is. You should be able to answer: *"Where would a
new API test file go?"*

### Step 2 — Understand fixtures (20 min)

Pytest fixtures are how this codebase shares setup between tests.
Understanding them unlocks 80% of the test code.

- [ ] Read `docs/CONFTEST_GUIDE.md`
- [ ] Open `conftest.py` (at repo root) and read it end-to-end with the comments
- [ ] Open `tests/conftest.py` — note how it adds test-data factories
- [ ] Open `tests/api/conftest.py` — note how it builds layer-specific service fixtures
- [ ] Open `tests/web/conftest.py` — same idea, page-object flavour

**Goal:** when you see `def test_x(auth_service, credentials)` you
recognize that pytest is injecting those parameters from a fixture
defined elsewhere, and you know how to find which file defined them.

### Step 3 — Understand a complete API test flow (30 min)

Read in this order so the dependencies build naturally:

- [ ] `src/api_clients/base_service.py` — read every comment. This is the foundation
- [ ] `src/api_clients/auth_service.py` — see how a concrete client is built on top
- [ ] `src/models/user.py` — see the Pydantic models that validate API responses
- [ ] `src/utils/assertions.py` — see the custom assertion helpers used in tests
- [ ] `tests/api/test_auth.py` — see all the pieces above working together

**Goal:** for a sample test like `test_valid_login_returns_token`, you
can trace the data flow: `pytest fixture → AuthService.login → BaseService._request → httpx → API → Pydantic model → assertion helper`.

### Step 4 — Understand a complete Web test flow (30 min)

Same idea, web side:

- [ ] `src/pages/base_page.py` — the BasePage foundation (read every comment)
- [ ] `src/pages/login_page.py` — concrete page object built on BasePage
- [ ] `tests/web/test_login.py` — see the page object used inside an actual test

**Goal:** understand the Page Object Model (POM) discipline used in
this repo: tests never reference selectors, page methods are
user-action-named, and Playwright `Locator` resolution is lazy.

### Step 5 — Allure ID convention (10 min)

- [ ] Read `ALLURE_TEST_IDS.md`
- [ ] Open any test file and notice the `@allure.id(...)` decorator above each test — confirm the IDs follow the convention you just read

**Goal:** understand why every test has a stable ID like
`API-AUTH-200-001` or `WEB-LOGIN-001`, and how these enable filterable,
trendable reports.

### Step 6 — Run the tests yourself (15 min)

```bash
# Install dependencies (first time only)
uv sync

# Run a single test by name
uv run pytest tests/api/test_auth.py::TestLogin::test_valid_login_returns_token -v

# Run all API tests
uv run pytest tests/api -v

# Run all web tests (slower — launches a browser)
uv run pytest tests/web -v

# Filter by Allure ID
uv run pytest tests/ -k "API-AUTH-200-001" -v
```

If a test fails because of a transient issue (the demo backend
occasionally returns 401/500 under load), wait 10–30 seconds and re-run.
This is documented behaviour for this public demo, not a flaky test.

**Goal:** see green output locally and confirm your environment is set up.

---

## What to do next

Once the reading is done, learn by doing:

1. **Add a new test.** Pick the closest existing test to what you want
   to write, copy it, change the inputs and the assertions. Don't write
   from scratch — pattern-matching is the fastest path to correct code
   in a framework you don't fully own yet.

2. **Extend an existing API client.** For example: add a new method to
   `AuthService` that hits the password-reset endpoint. Look at the
   existing `login` method, copy the shape, change the path and the
   request/response models.

3. **Add a new page object.** Pick a page that doesn't yet have one
   (the contact form, for example), follow the `LoginPage` pattern.

4. **Read `CLAUDE.md`** if you use AI tools to assist your work — it
   documents the agent collaboration rules, retry limits, and existing
   code modification policy used on this project.

---

## Glossary

- **POM (Page Object Model)** — design pattern where each page in the
  app is represented by a class that owns the selectors and exposes
  user-action-named methods (`login`, `add_to_cart`). Tests call those
  methods instead of touching selectors.
- **AAA pattern** — Arrange / Act / Assert. The canonical structure for
  a test: set up state, do the thing, check the result. Every test in
  this repo follows it.
- **Fixture** — a reusable setup/teardown function in pytest that gets
  injected into tests by parameter name. The plumbing that gets a test
  the resources it needs (a logged-in client, a page object, etc).
- **Allure step** — a labelled block of work shown as a node in the
  Allure report tree. Created via `@allure.step(...)` decorator or
  `with allure.step(...)` context. Every API call and every page
  action in this repo is wrapped in one.
- **BaseService** — this repo's foundation class for API clients (see
  `src/api_clients/base_service.py`). Every concrete client extends it
  and inherits the request/response Allure instrumentation.
- **BasePage** — the equivalent foundation for page objects (see
  `src/pages/base_page.py`). Every page extends it.
- **Pydantic model** — a typed data class that validates structure
  on construction. Used in this repo to validate API responses
  against an expected schema, catching contract drift early.
