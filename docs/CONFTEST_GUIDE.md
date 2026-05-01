# conftest.py Guide

A conftest is the unit of fixture sharing in pytest. Get this right and
the rest of the test code stays clean. Get it wrong and you fight
duplication, scope leaks, and import cycles.

This repo has multiple `conftest.py` files **on purpose**. This guide
explains where each one lives, what belongs in it, and why.

---

## Why multiple conftest files exist

The conftest files in this repo:

- `conftest.py` (repo root)
- `tests/conftest.py`
- `tests/api/conftest.py`
- `tests/web/conftest.py`
- `tests/mobile/conftest.py` *(planned for Phase 2 — not yet present)*

This is not duplication. It is hierarchical fixture discovery, which
is a first-class pytest feature.

---

## How pytest discovers fixtures

When pytest runs a test, it walks **up the directory tree** from the
test file looking for `conftest.py` files. Every conftest it finds
contributes its fixtures to the test's available pool. Closer fixtures
shadow further ones.

For a test at `tests/api/test_auth.py`, pytest sees:

```
tests/api/test_auth.py            ← the test
tests/api/conftest.py             ← API-layer fixtures (auth_service, admin_token, ...)
tests/conftest.py                 ← test-level fixtures (random_user, ...)
conftest.py (repo root)           ← root fixtures (credentials, browser, page, ...)
```

All four files contribute fixtures to that test. By the time `pytest`
calls the test, every fixture name listed in the function signature is
resolved.

```
                  ┌─────────────────────────┐
                  │   conftest.py (root)    │
                  │   credentials, browser, │
                  │   context, page         │
                  └────────────┬────────────┘
                               │
                  ┌────────────▼────────────┐
                  │   tests/conftest.py     │
                  │   random_user           │
                  └────────────┬────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
   ┌──────────▼──────────┐         ┌────────────▼────────────┐
   │ tests/api/conftest  │         │  tests/web/conftest     │
   │ auth_service,       │         │  login_page,            │
   │ admin_token, ...    │         │  listing_page, ...      │
   └─────────────────────┘         └─────────────────────────┘
              │                                 │
   ┌──────────▼──────────┐         ┌────────────▼────────────┐
   │  tests/api/test_*   │         │  tests/web/test_*       │
   └─────────────────────┘         └─────────────────────────┘
```

A web test cannot accidentally use `auth_service` (it isn't in scope),
and an API test cannot accidentally launch a browser (it never sees
`page`). The hierarchy enforces the architectural separation.

---

## What lives in each conftest

### conftest.py (repo root)

**Purpose:** fixtures and configuration that apply to **every** test,
across surfaces.

**What belongs here:**

- `credentials` — loaded once per session from YAML + `.env`
- `browser` / `context` / `page` — Playwright primitives (web only,
  but kept at root because nothing below cares about *where* `page`
  comes from)
- Async event loop policy and any other process-level setup

**Why at root:** API and Web tests both consume `credentials`. Defining
it once at the highest level avoids duplication and keeps the
"single source of truth" property.

### tests/conftest.py

**Purpose:** test-level fixtures shared by all surfaces but not needed
at session/process level.

**What belongs here:**

- `random_user` — Faker-driven `UserCreate` payload; used by
  `tests/api/test_users.py::test_register_creates_user` and by
  `tests/web/test_account.py::test_register_*`

**Why scoped here:** test data factories are conceptually a test
concern, not a process-level concern. Putting them under `tests/`
keeps the repo-root conftest focused on infrastructure.

### tests/api/conftest.py

**Purpose:** fixtures specific to the API testing layer.

**What belongs here:**

- `auth_service` — unauthenticated `AuthService` for tests that
  exercise the login flow themselves
- `admin_token` / `customer_token` — pre-authenticated access tokens
  for tests that need to skip the login dance
- `product_service`, `admin_product_service`, `cart_service`,
  `customer_order_service`, `admin_user_service`,
  `customer_user_service`, `public_user_service` — service clients
  scoped to the relevant identity

**Why scoped here:** web tests don't need API service clients. Putting
these fixtures at root would pollute every web test session with
imports that aren't relevant to it (and would also encourage tests
to mix surfaces in ways that defeat the architectural separation).

### tests/web/conftest.py

**Purpose:** fixtures specific to the Web UI testing layer.

**What belongs here:**

- `login_page`, `register_page`, `listing_page`, `detail_page`,
  `cart_page`, `checkout_page`, `account_page` — page objects
  constructed against the shared `page` fixture

**Why scoped here:** API tests don't need page objects. The page
objects also depend on the `page` fixture (which costs ~1 s of
browser launch per test). Keeping them in the web conftest signals
that this cost is paid only when running web tests.

### tests/mobile/conftest.py (Phase 2)

**Purpose:** Appium driver, Sauce Labs config, mobile-specific page
objects. Currently a placeholder; will be added when Phase 2 begins.

---

## Fixture scope deep-dive

Pytest fixtures have a `scope` parameter that controls how often the
fixture is set up and torn down. The choices are:

| Scope | Set up... | Used by |
|---|---|---|
| `function` (default) | Once per test function | Most fixtures in this repo |
| `class` | Once per test class | Rarely needed here |
| `module` | Once per test file | Rarely needed |
| `package` | Once per package directory | Rarely needed |
| `session` | Once per pytest invocation | `credentials` |

**`credentials` is `scope="session"`** because reading YAML and `.env`
is read-only and idempotent. Reading them once per process saves time
across hundreds of tests.

**`browser`, `context`, `page` are function-scoped** even though
session scope would be faster. The reason is documented in the root
`conftest.py`: pytest-asyncio creates a fresh event loop per function,
and Playwright's transport breaks if reused across loops.

**Service clients (`auth_service`, etc.) are function-scoped** so each
test starts with a fresh, unauthenticated client and there is no token
state leaking between tests.

---

## Adding a new fixture — decision tree

```
Is the fixture used by tests in multiple layers (API + Web + Mobile)?
├── YES → conftest.py at repo root, OR tests/conftest.py
│         (root for infrastructure; tests/ for test-data concepts)
└── NO  → Is the fixture specific to one layer?
         ├── YES → tests/<layer>/conftest.py
         └── No, even narrower? → tests/<layer>/<feature>/conftest.py
                                   (sub-conftest is fine for specialized fixtures)
```

When in doubt, place the fixture as close to its consumers as possible.
Fixtures placed too high in the tree become invisible coupling — every
test inherits them whether it needs them or not.

---

## Common gotchas

### 1. Forgetting `pytest_asyncio.fixture` for async fixtures

A plain `@pytest.fixture` on an `async def` function returns a
coroutine, not the awaited value. Tests then receive a coroutine object
and crash with confusing errors. Use `@pytest_asyncio.fixture` for
async fixtures (see every async fixture in this repo for examples).

### 2. `yield` vs `return` in fixtures

- Use `yield` when the fixture has teardown work (closing a client,
  closing a browser context). Code after `yield` runs after the test.
- Use `return` for plain values that need no teardown.

Pattern in this repo: every service-client fixture uses `yield service`
followed by `await service.close()`. This is what guarantees the
underlying httpx connection is released even if the test raises.

### 3. Function-scoped vs session-scoped state pollution

Session-scoped fixtures persist across all tests in a run. If a
session-scoped fixture mutates state (e.g. logs in and stores a token),
**every** test that follows sees that mutation. Most of the time you
want function scope so each test starts fresh.

### 4. Fixture parameter order

Pytest resolves fixtures by **name**, not by position. The order you
list fixtures in `def test_x(a, b, c)` does not change resolution
order — pytest still computes the dependency graph and instantiates
in the right order. So you don't need to worry about "putting
credentials first" — name it and pytest figures it out.

### 5. Two fixtures with the same name in different conftests

The closer one wins. If `tests/conftest.py` defines `random_user` and
`tests/api/conftest.py` also defines `random_user`, tests under
`tests/api/` get the API one; tests under `tests/web/` get the
test-level one. Avoid this on purpose — it works but is confusing.
