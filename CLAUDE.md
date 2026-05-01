# CLAUDE.md

Guidance for Claude Code agent when working on this repository.

## Git commit conventions

CRITICAL: All commits in this repository must reflect Kenny Ramadhan as sole author. Specifically:

1. NEVER add Co-Authored-By footer mentioning Claude or anthropic.com to commit messages
2. NEVER add "Generated with Claude Code" or any AI attribution lines
3. NEVER override the local git config user.name or user.email
4. NEVER include any AI attribution, signature, or footer in commit messages
5. Commit messages follow conventional commits style (feat, fix, docs, refactor, chore, test) without AI attribution

The commit history is a public artifact of Kenny Ramadhan's QA engineering work. AI assistance is welcome and effective in development, but commit attribution stays human-only by design.

A commit-msg git hook is installed locally that will REJECT commits with AI attribution. Don't try to bypass it.

## Repository purpose

This is a public QA automation portfolio showcasing production-grade test architecture using Practice Software Testing demo app.

Stack:
- Python 3.12+
- Playwright async API
- pytest + pytest-asyncio
- Allure reporting
- uv package manager

## Architectural rules

Refer to ARCHITECTURE.md for design decisions, ALLURE_TEST_IDS.md for test naming convention.

Key non-negotiables:
- All test functions are async
- Page Object Model strict (no selectors in tests)
- BaseService pattern for API clients
- Pydantic models for API responses
- Allure decorators @allure.id and @allure.title mandatory on every test
- Type hints on all public functions, mypy strict mode

## Demo target

Practice Software Testing (Toolshop):
- Web UI: practicesoftwaretesting.com
- REST API: api.practicesoftwaretesting.com

Do not target other apps unless explicitly instructed.

---

# Agent execution rules

## ⚡ Read this first

Before executing ANY complex task (> 5 minutes or > 3 files):

1. **STOP** — do not start coding immediately
2. **DECOMPOSE** — break into subtasks (max 3–5 items per batch)
3. **SUBAGENT** — use subagents for parallel execution where possible
4. **CHECKPOINT** — validate after each subtask
5. **ASK** — if unclear, ask. Don't guess for hours.

```
❌ NEVER: start coding a multi-step task without planning
✅ ALWAYS: decompose → delegate → coordinate → validate
```

## Subagent strategy (mandatory for complex tasks)

| Task type | Use subagent? | Reason |
|---|---|---|
| File scanning / exploration | ✅ YES | Keeps main context clean |
| Research existing patterns | ✅ YES | Parallel analysis |
| Generate single test file | ✅ YES | Focused execution |
| Simple edits (< 20 lines) | ❌ NO | Overhead not worth it |
| Cross-file refactoring | ✅ YES | Isolated scope |
| Reading > 3 files | ✅ YES | Prevent context bloat |

Rules:
- One task per subagent for focused execution
- Offload research, exploration, parallel analysis to subagents
- Main agent coordinates; subagents execute
- Return SUMMARY to main agent, not full content

## Task decomposition

For any task estimated > 5 minutes:

```
STEP 1: Identify scope
├── How many files involved?
├── How many endpoints/features?
└── Any dependencies between steps?

STEP 2: Break into subtasks
├── Each subtask = 1 focused deliverable
├── Max 5 subtasks per batch
└── Clear input/output for each

STEP 3: Assign execution mode
├── Independent → parallel subagents
├── Dependent → sequential with checkpoints
└── Simple → direct execution
```

## File operations priority

Before reading any file, ask:
1. Do I NEED this file right now? (not "might be useful")
2. Can I grep / search instead of full read?
3. Is there a shorter file with the same info?

```bash
# ✅ DO: search first, read targeted
grep -r "class.*Service" src/api_clients/ --include="*.py" -l
grep -r "def.*login" src/api_clients/ --include="*.py" -A 10

# ✅ DO: preview structure before full read
head -50 src/api_clients/auth_service.py

# ❌ DON'T: read every file in a directory
# ❌ DON'T: read 500+ line files when you need 1 function
```

## Checkpoint & validation gates

After each major step, validate before continuing:

```
─────────────────────────────────────────
CHECKPOINT
─────────────────────────────────────────
✅ Completed: [what was done]
📁 Files: [created/modified]
🔍 Verified: [how confirmed — command run]
➡️ Next: [next subtask]
⚠️ Blockers: [any issues found]
─────────────────────────────────────────
```

## Context window management

Keep context lean:
- Summarize findings, don't paste entire files
- Use references: "as seen in `src/api_clients/auth.py:45-60`"
- Clear completed subtask context before starting new one
- Maximum 3 files in focus at any time

## Error recovery protocol

When stuck or confused for > 2 minutes:

```
1. STOP   → don't retry the same approach
2. STATE  → clearly state what's blocking
3. ASK    → request clarification OR suggest 2–3 alternatives
4. WAIT   → don't proceed without confirmation
```

Stop format:

```
## ⚠️ Need direction

**Error:** [description]
**Tried:**
1. [approach 1] → [result]
2. [approach 2] → [result]
3. [approach 3] → [result]

**Possible solutions:**
- [option A]
- [option B]

Which should I try, or is there another approach?
```

## Decision tree for execution mode

```
Task > 15 minutes estimated?
├── YES → decompose into subtasks first
│   └── Can subtasks run in parallel?
│       ├── YES → spawn subagents (1 task each)
│       └── NO → sequential with checkpoints
└── NO → execute directly with checkpoint at end

Task requires reading > 3 files?
├── YES → use subagent for file analysis first
└── NO → read directly

Stuck or confused?
├── YES → STOP, STATE problem, ASK
└── NO → continue
```

---

# Test execution rules

**Don't run the entire test file unless explicitly asked.**

| Situation | ✅ Correct command | ❌ Wrong command |
|---|---|---|
| Created 2 new tests | `pytest file.py::test_new_1 file.py::test_new_2 -v` | `pytest file.py -v` |
| Debugging 1 failing test | `pytest file.py::test_that_failed -v` | `pytest file.py -v` |
| Fix specific test | `pytest file.py::TestClass::test_method -v` | `pytest file.py -v` |

Rules:
```
✅ DO: run only the test cases newly created or modified
✅ DO: run only the failing test when debugging
✅ DO: run full file ONLY when user explicitly asks "run all"

❌ DON'T: run the whole file when you only added 1–2 tests
❌ DON'T: run the whole file when debugging a single failure
❌ DON'T: run the whole suite unprompted
```

Pytest command reference:

```bash
# Single test function
uv run pytest tests/api/test_auth.py::test_login_success -v

# Multiple specific tests
uv run pytest tests/api/test_auth.py::test_login_success tests/api/test_auth.py::test_login_invalid -v

# By keyword
uv run pytest tests/api/test_auth.py -k "login" -v

# By Allure ID (mandatory tag pattern — see ALLURE_TEST_IDS.md)
uv run pytest tests/ -k "API-AUTH-200-001" -v
```

This applies across API and Web (and Mobile in Phase 2).

---

# Retry / loop limits

Don't retry indefinitely. Hard limits:

| Situation | Max retries | After limit |
|---|---|---|
| Fix syntax error | 3× | Stop, ask user |
| Fix test failure | 3× | Stop, explain error, ask user |
| API / connection error | 2× | Stop, report issue |
| Same error repeating | 2× | Stop, don't retry same approach |

Rules:
```
✅ DO: try a different approach each retry
✅ DO: explain what was tried before asking
✅ DO: stop and ask if 3× failed with the same error

❌ DON'T: retry more than 3× for the same error
❌ DON'T: retry with the exact same approach
❌ DON'T: loop without progress for > 5 minutes
```

---

# Existing code modification rules

Be careful when modifying existing code.

| Action | Allowed when | Not allowed when |
|---|---|---|
| Edit existing method | Bug fix, add optional parameter | Changing working logic |
| Add new method | New feature requested | — |
| Delete code | User explicitly asks | Without confirmation |
| Refactor | User explicitly asks | While doing other tasks |

Rules:
```
✅ DO: add a new method instead of modifying existing (when in doubt)
✅ DO: preserve existing functionality
✅ DO: add parameters with default values (backward compatible)
✅ DO: comment if some code needs attention

❌ DON'T: delete code without being asked
❌ DON'T: rename functions/methods without being asked
❌ DON'T: change existing logic unrelated to the task
❌ DON'T: "improve" or "refactor" unprompted
```

When modification IS needed, confirm first:

```
"I need to change method X in file Y.
Change: [describe].
OK to proceed?"
```

---

# Import / dependency consistency

Follow the existing import patterns in this project.

Rules:
```
✅ DO: scan import patterns in similar files before writing
✅ DO: use uv for package management — not pip directly
✅ DO: group imports (stdlib → third-party → local)
✅ DO: check if module exists in project before suggesting install

❌ DON'T: add new dependencies without confirmation
❌ DON'T: mix import styles (sometimes relative, sometimes absolute)
❌ DON'T: leave unused imports
```

Adding a new dependency:

```bash
# Use uv, never pip directly
uv add <package>          # production
uv add --dev <package>    # dev/test only
```

Before suggesting a new dependency, ask:

```
"For this feature, I need library [X].
It's not in the project yet.
OK to add it via uv?"
```

Import order:

```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party
import pytest
import allure
from playwright.async_api import Page

# 3. Local / project
from src.api_clients.auth_service import AuthService
from src.utils.helpers import generate_email
```

---

# Test data strategy

Test data must be unique and not hardcoded.

Rules:
```
✅ DO: generate unique data each test run
✅ DO: use timestamp / random for uniqueness
✅ DO: store generated data in fixtures for cross-test reference
✅ DO: cleanup test data when an endpoint is available

❌ DON'T: hardcode emails, usernames, IDs
❌ DON'T: use data that might conflict with other tests
❌ DON'T: assume data still exists from a previous run
```

Pattern for unique data (Practice Software Testing context):

```python
import time
from faker import Faker

fake = Faker()

# ✅ GOOD — unique per run
email = f"test_{int(time.time())}_{fake.user_name()}@example.com"
first_name = fake.first_name()
phone = fake.phone_number()

# ❌ BAD — hardcoded, will conflict with other runs
email = "test@example.com"
```

Cleanup pattern:

```python
@pytest.fixture
async def created_user(api_client):
    user = await api_client.users.register({...})
    yield user
    # Teardown if endpoint exists
    await api_client.users.delete(user.id)
```

For Practice Software Testing demo: customer accounts and orders persist across runs against the public demo backend. Use unique emails per run; do NOT delete the seeded admin account; do NOT mass-create data that could pollute the demo for other users.

---

# Output / response length control

Keep responses concise and readable.

| Situation | Output format |
|---|---|
| Scan results | Summary list, not full content |
| File content | Reference line numbers, not full paste |
| API response | Relevant fields only, not entire JSON |
| Error analysis | Error message + root cause + fix |

Rules:
```
✅ DO: summarize findings in 5–10 lines
✅ DO: reference with "see file.py:45-60"
✅ DO: extract only relevant fields from responses
✅ DO: use tables for comparisons

❌ DON'T: paste the entire file content
❌ DON'T: dump the entire API response
❌ DON'T: repeat info already provided
❌ DON'T: wall-of-text without structure
```

---

# Assertion best practices

Assertions must be specific and meaningful.

Rules:
```
✅ DO: check status code FIRST, then body
✅ DO: include meaningful error messages
✅ DO: assert specific fields, not the entire object
✅ DO: use the appropriate assertion method

❌ DON'T: assert without an error message
❌ DON'T: compare entire response objects (fragile)
❌ DON'T: assert implementation details
```

Pattern (API):

```python
# ✅ GOOD — specific with meaningful message
assert response.status == 200, f"Login failed: {await response.text()}"

# Pydantic-validated assertion (preferred — fail-fast on schema)
login = LoginResponse.model_validate(await response.json())
assert login.access_token, "access_token empty in valid login response"

# Lists
items = (await response.json()).get("data", [])
assert len(items) > 0, "Expected items but got empty list"
assert any(item["category"]["slug"] == "hand-tools" for item in items), \
    "No hand-tools category in result"
```

Assertion order:

```python
# 1. Status code first
assert response.status == 200, f"Expected 200, got {response.status}: {await response.text()}"

# 2. Required fields
body = await response.json()
assert "access_token" in body, "access_token field missing"

# 3. Field values
assert body["user"]["role"] == "user", "Wrong role returned"

# 4. Business logic
assert order.total >= 0, "Order total cannot be negative"
```

Web UI assertion (Playwright `expect()` preferred):

```python
import re
from playwright.async_api import expect

await expect(page).to_have_url(re.compile(r"/account"))
await expect(page.get_by_role("heading", name="My account")).to_be_visible()
await expect(page.get_by_role("listitem")).to_have_count(9)
```

## Allure step visibility for assertions

Use the helpers from `src/utils/assertions.py` for assertions where the
actual vs expected diff carries diagnostic value:

- `expect_status(response, 200)` — wraps status assertion in Allure step
- `expect_field(model, "access_token")` — wraps field presence/value check

Raw `assert` remains acceptable for trivial truthiness or when no
diagnostic attachment is needed. The goal is recruiter-readable reports,
not assertion ceremony.

API request/response visibility is automatic — `BaseService._request()`
attaches all request/response data as Allure step children. Tests do
not need to manually attach API payloads.

---

# Wait strategy — Web (Playwright)

Playwright has built-in auto-waiting. Use it before writing manual waits.

| Need | ❌ Wrong | ✅ Right |
|---|---|---|
| Element appears | `time.sleep(2)` | `expect(locator).to_be_visible()` |
| Navigation completes | `time.sleep(3)` | `page.wait_for_url(...)` |
| Network done | `time.sleep(2)` | `page.wait_for_load_state("networkidle")` |
| Element disappears | `time.sleep(1)` | `expect(locator).to_be_hidden()` |
| API response | `time.sleep(2)` | `page.wait_for_response(url_pattern)` |

Load state choice:

```
page.wait_for_load_state("load")              → DOM + resources done (default)
page.wait_for_load_state("domcontentloaded")  → DOM only, faster
page.wait_for_load_state("networkidle")       → No network for 500ms
                                                Use ONLY for heavy-async SPAs
```

Rules:
```
✅ DO: rely on Playwright auto-wait as primary mechanism
✅ DO: use networkidle ONLY for pages with heavy async
✅ DO: use wait_for_response for actions that trigger API calls

❌ DON'T: use time.sleep in web page objects
❌ DON'T: default to networkidle everywhere (slow)
❌ DON'T: wait for URL with sleep — use page.wait_for_url()
```

Locator priority (Web):

| Priority | Locator type | Example |
|---|---|---|
| 1 | Role | `get_by_role("button", name="Submit")` |
| 2 | Label | `get_by_label("Email")` |
| 3 | Placeholder | `get_by_placeholder("Enter email")` |
| 4 | Text | `get_by_text("Welcome")` |
| 5 | Test ID | `get_by_test_id("submit-btn")` |
| 6 | CSS | `locator(".btn-primary")` |
| 7 | XPath | `locator("//button[@type='submit']")` |

Always use the highest-priority locator available. Prefer `data-test` attributes from Practice Software Testing markup (e.g. `get_by_test_id("nav-sign-in")`) over CSS class selectors.

---

# Wait strategy — Mobile (Phase 2 reference)

> **Phase 2 status:** Mobile testing via Appium + Sauce Labs `my-demo-app-rn` is upcoming, not yet implemented. The rules below apply once mobile work begins.

**NEVER use `time.sleep` for UI state waiting.**

| Need | ❌ Wrong | ✅ Right |
|---|---|---|
| Element appears | `time.sleep(2)` | `find_visible_element(..., timeout=N)` |
| Animation transition | `time.sleep(1.5)` | `WebDriverWait(...).until(EC.staleness_of(el))` |
| One-of-N locators | nested try/except with `timeout=10` | `_wait_for_any_element([A, B], timeout=10)` |
| Popup dismisses | `time.sleep(1)` | Probe loop with short timeout |
| Keyboard hides | `time.sleep(1)` | `find_visible_element` on next element |

When `time.sleep` is acceptable:
- Animation that can't be detected (max `0.5s`), with a justifying comment
- Deliberate rate limiting between requests
- Example: `time.sleep(0.5)  # deliberate: popup dismiss animation`

Required pattern — `_wait_for_any_element`:

```python
def _wait_for_any_element(self, locators: list, timeout: int = 10):
    """Probe multiple locators until one is found or deadline."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for locator in locators:
            try:
                return self.find_visible_element(*locator, timeout=1)
            except Exception:
                continue
    return None
```

Required pattern — staleness wait after tap:

```python
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

try:
    WebDriverWait(self.driver, 2).until(EC.staleness_of(element))
except TimeoutException:
    pass  # Not stale is fine, continue
```

Locator priority (Mobile / Appium):

| Priority | Strategy | Example |
|---|---|---|
| 1 | Accessibility ID | `AppiumBy.ACCESSIBILITY_ID, "Submit"` |
| 2 | UIAutomator (Android) | `AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector()..."` |
| 3 | XPath | `AppiumBy.XPATH, "//android.widget.Button[@text='Submit']"` |
| 4 | Class Name | `AppiumBy.CLASS_NAME, "android.widget.EditText"` |
| 5 | ID | `AppiumBy.ID, "com.app:id/button_submit"` |

Avoid XPath when Accessibility ID is available — more stable, faster.

---

# Mobile element interaction (Phase 2 reference)

Decision tree — Appium vs ADB:

```
Element found?
├── NO → TimeoutException → flow done, or raise RuntimeError
└── YES → try element.click() via Appium
    ├── SUCCESS → continue
    └── FAILED (ElementNotInteractableException / StaleElementReferenceException)
        ├── StaleElement → re-find element → retry click
        ├── NotInteractable + overlay → wait_for_overlay() → retry
        └── Still failing → ADB tap (last resort, bypass coordinates)
```

Exception mapping:

| Exception | Meaning | Action |
|---|---|---|
| `TimeoutException` from `find_element` | Element not on screen | Flow done or raise |
| `ElementNotInteractableException` | Element covered by overlay | Wait overlay, or ADB tap |
| `StaleElementReferenceException` | DOM re-rendered, ref expired | Re-find, retry click |
| `Exception` (generic) | Unknown — don't swallow | Log error, raise |

Rules:
```
✅ DO: catch exceptions specifically, not bare except
✅ DO: separate find_element and element.click() into different try-blocks
✅ DO: re-find on StaleElementReferenceException before retry
✅ DO: log warning whenever falling back to ADB

❌ DON'T: bare except Exception to swallow all errors
❌ DON'T: combine find and click in one try-catch
❌ DON'T: assume every exception means "element not found"
❌ DON'T: silent return success when flow didn't complete
```

---

# CI/CD awareness

This repo has GitHub Actions workflows that publish Allure reports to GitHub Pages on every push to `main`:

- `ci.yml` — runs lint (ruff + mypy), API tests, Web tests in parallel
- `publish-report.yml` — generates Allure report from CI artifacts and deploys to Pages
- Pages URL: `https://kennyramadhan.github.io/playwright-api-web-mobile/`

Important behaviors:
- **Publish runs on both success AND failure** — Allure report shows test failures as signal, not noise. Don't add `continue-on-error: true` to test steps to "make CI green" — failures must be visible.
- **History persists** via `gh-pages` branch — preserves trend data across runs.
- **No-AI-attribution rule applies to CI commits too** — workflow files committed by agent must not contain Co-Authored-By footers.

When modifying workflows, prefer minimal patches over full rewrites. Use `workflow_dispatch` triggers for manual recovery flows.

---

# Output format standards

For scan / discovery tasks:

```markdown
## Scan results
**Existing:**
- `src/api_clients/auth_service.py` — AuthService (login, register, logout)
- `src/api_clients/users_service.py` — UsersService (get, update)

**Missing:**
- ProductsService (list, search, get_by_id)

**Recommendation:**
1. Create products_service.py extending BaseService
2. Reuse existing auth flow from auth_service.py
```

For implementation tasks:

```markdown
## Implementation complete
**Created:**
- `src/api_clients/products_service.py`
- `tests/api/test_products.py` (4 tests)

**Modified:**
- `src/api_clients/__init__.py` (added export)

**Verify:**
uv run pytest tests/api/test_products.py -v
```

For error / debug tasks:

```markdown
## Issue analysis
**Error:** AttributeError: 'NoneType' object has no attribute 'get'
**Location:** src/api_clients/auth_service.py:45
**Root cause:** Response not awaited, returned coroutine instead of dict
**Fix:** added `await` before `self.post()`
**Verification:** uv run pytest tests/api/test_auth.py::test_login -v ✅
```