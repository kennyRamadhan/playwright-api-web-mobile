# Allure Test ID naming convention

> Naming standard for `@allure.id` decorators across all tests in this repository. Adopted from production work (UCO Collect, Noovoleum) for consistency. Every test MUST have an Allure ID following this convention.

---

## 1. Pattern

```
{SURFACE}-{FEATURE}-{VARIANT}-{NUM}
```

| Component | Required | Description | Examples |
|---|---|---|---|
| `SURFACE` | Yes | Test target type | `API`, `WEB`, `MOB` |
| `FEATURE` | Yes | Feature area or domain | `LOGIN`, `CART`, `CHECKOUT` |
| `VARIANT` | Yes for API, optional for Web/Mobile | HTTP code (API) or scenario tag (Web/Mobile) | `200`, `400`, `401`, `NEG`, `EDGE` |
| `NUM` | Yes | 3-digit zero-padded sequence within feature/variant | `001`, `002`, `003` |

---

## 2. SURFACE codes

### API — REST API tests against `api.practicesoftwaretesting.com`

```
API-{FEATURE}-{HTTP_CODE}-{NUM}
```

The HTTP code in the variant slot indicates the **expected response code** for that specific test scenario.

**Examples:**
- `API-AUTH-200-001` — POST /login with valid credentials returns 200
- `API-AUTH-401-001` — POST /login with invalid password returns 401
- `API-AUTH-422-001` — POST /login with malformed body returns 422
- `API-PRODUCTS-200-001` — GET /products returns 200 with paginated list
- `API-PRODUCTS-404-001` — GET /products/{invalid-id} returns 404
- `API-CART-200-001` — POST /cart/add with valid product returns 200
- `API-CART-400-001` — POST /cart/add with invalid quantity returns 400

### WEB — Browser tests against `practicesoftwaretesting.com`

```
WEB-{FEATURE}-{NUM}
WEB-{FEATURE}-{VARIANT}-{NUM}     # When variant adds clarity
```

For web tests, the variant is optional. Use it when there are multiple flavors of the same feature.

**Examples:**
- `WEB-LOGIN-001` — login with valid credentials succeeds
- `WEB-LOGIN-002` — login with invalid credentials shows error
- `WEB-LOGIN-003` — login form validation prevents empty submission
- `WEB-CART-001` — add single product to cart updates count
- `WEB-CART-002` — remove product from cart updates count
- `WEB-CHECKOUT-001` — full purchase flow completes successfully
- `WEB-CHECKOUT-NEG-001` — checkout with declined card displays error

### MOB — Mobile tests via Appium (Phase 2, deferred)

```
MOB-{FEATURE}-{NUM}
```

**Examples (planned):**
- `MOB-LOGIN-001` — login with valid credentials on Android
- `MOB-CART-001` — add product to cart via mobile app

---

## 3. FEATURE codes (current vocabulary)

This list grows as the test suite expands. Maintain consistency.

### API features

| Code | Description |
|---|---|
| `AUTH` | Authentication (login, logout, token refresh) |
| `PRODUCTS` | Product CRUD and listing |
| `CATEGORIES` | Product categories |
| `BRANDS` | Product brands |
| `CART` | Shopping cart operations |
| `ORDERS` | Order creation, lifecycle, history |
| `USERS` | User CRUD (admin-level) |
| `INVOICES` | Invoice generation and retrieval |

### Web features

| Code | Description |
|---|---|
| `LOGIN` | Sign-in flow |
| `REGISTER` | Sign-up flow |
| `LOGOUT` | Sign-out flow |
| `SEARCH` | Product search and filtering |
| `BROWSE` | Category navigation, product listing |
| `PRODUCT` | Product detail page interactions |
| `CART` | Add/remove/update cart |
| `CHECKOUT` | Checkout flow (address, payment) |
| `ACCOUNT` | User account management |
| `ADMIN` | Admin dashboard (if used) |

---

## 4. VARIANT semantics

### HTTP codes (API tests)

Use the **expected response status code** as the variant. This makes test discovery by status code trivial in Allure UI.

Common codes:
- `200` — success
- `201` — created
- `204` — no content (delete)
- `400` — bad request (validation failure)
- `401` — unauthorized (auth missing/invalid)
- `403` — forbidden (auth valid but lacks permission)
- `404` — not found
- `409` — conflict
- `422` — unprocessable entity (validation rejected)
- `429` — too many requests (rate limit)
- `500` — server error (rare in tests, but useful for resilience checks)

### Scenario tags (Web/Mobile tests, optional)

Use when needed for clarity:
- `NEG` — negative scenario (intentionally testing failure)
- `EDGE` — edge case (boundary values, unusual inputs)
- `SLOW` — known slow test (excluded from fast CI runs)
- `FLAKY` — known intermittent test (under investigation)

---

## 5. Numbering rules

- Always 3-digit zero-padded: `001`, `002`, ..., `099`, `100`
- Number is **per-FEATURE-per-VARIANT** — restart at `001` for each combination
- Skip numbers if a test is removed; do NOT renumber existing tests (history continuity)
- If a feature reaches `999`, the feature scope is too broad — split it

---

## 6. Decorator usage

Every test function in the repository MUST have BOTH decorators:

```python
import allure
import pytest

@allure.id("WEB-LOGIN-001")
@allure.title("Login with valid credentials redirects to account page")
async def test_login_with_valid_credentials(login_page, account_page):
    # Arrange
    valid_user = make_user()

    # Act
    await login_page.login(valid_user.email, valid_user.password)

    # Assert
    assert await account_page.is_loaded()
```

### `@allure.id`

- Machine-readable, unique within the repository
- Format follows the convention above
- Used by Allure for grouping, filtering, and historical tracking

### `@allure.title`

- Human-readable test name (shown in Allure UI)
- Sentence case, descriptive
- Should describe both the action and the expected outcome
- NOT a copy of the function name — should be more readable

---

## 7. Optional Allure decorators

Use when they add value:

```python
@allure.feature("Authentication")          # Top-level grouping
@allure.story("Login")                     # Sub-grouping
@allure.severity(allure.severity_level.CRITICAL)  # Test importance
@allure.tag("smoke", "regression")         # Custom filter tags
@allure.epic("E-commerce platform")        # Highest-level grouping
@allure.id("WEB-LOGIN-001")
@allure.title("Login with valid credentials redirects to account page")
```

**Rule of thumb:** Always use `@allure.id` and `@allure.title`. Use `@allure.severity` for critical tests. Use `@allure.feature` / `@allure.story` for grouping when test count grows beyond ~30 per feature area.

---

## 8. Examples — full test IDs catalog

### Day 1 expected test set (Practice Software Testing)

#### API tests (~25 tests)

```
API-AUTH-200-001    Valid login returns token
API-AUTH-200-002    Token refresh returns new token
API-AUTH-401-001    Invalid password returns 401
API-AUTH-401-002    Missing token on protected endpoint returns 401
API-AUTH-422-001    Malformed login body returns 422

API-PRODUCTS-200-001    GET /products returns paginated list
API-PRODUCTS-200-002    GET /products/{id} returns single product
API-PRODUCTS-200-003    GET /products with category filter
API-PRODUCTS-404-001    GET /products/invalid-id returns 404
API-PRODUCTS-201-001    POST /products (admin) creates product
API-PRODUCTS-403-001    POST /products (non-admin) returns 403

API-CART-200-001    Add product to cart returns updated cart
API-CART-200-002    Update cart item quantity
API-CART-204-001    Remove cart item returns 204
API-CART-400-001    Add with invalid quantity returns 400

API-ORDERS-201-001    Create order from cart returns 201
API-ORDERS-200-001    Get order by ID returns details
API-ORDERS-200-002    Get user order history returns list
API-ORDERS-400-001    Create order from empty cart returns 400

API-USERS-200-001    GET /users (admin) returns user list
API-USERS-201-001    POST /users (admin) creates user
API-USERS-200-002    GET /users/me returns current user
API-USERS-200-003    PATCH /users/me updates current user
API-USERS-403-001    Non-admin GET /users returns 403
```

#### Web tests (~15 tests)

```
WEB-LOGIN-001    Login with valid credentials redirects to account
WEB-LOGIN-002    Login with invalid password shows error
WEB-LOGIN-003    Login form validation prevents empty submission

WEB-REGISTER-001    Register new user creates account and logs in
WEB-REGISTER-002    Register with existing email shows error

WEB-BROWSE-001    Browse all products displays product grid
WEB-BROWSE-002    Filter by category narrows results
WEB-BROWSE-003    Sort by price ascending orders products

WEB-SEARCH-001    Search by product name returns matches
WEB-SEARCH-002    Search with no results shows empty state

WEB-CART-001    Add product to cart updates cart count
WEB-CART-002    Remove product from cart updates count
WEB-CART-003    Update quantity recalculates subtotal

WEB-CHECKOUT-001    Full purchase flow completes successfully
WEB-CHECKOUT-NEG-001    Checkout with invalid card displays error
```

---

## 9. Maintenance

When adding new tests:

1. Determine SURFACE (API/WEB/MOB)
2. Choose FEATURE from existing vocabulary, or add new one to this doc
3. Determine VARIANT (HTTP code or scenario tag)
4. Find next available NUM (review existing tests for that feature/variant)
5. Apply both `@allure.id` and `@allure.title` decorators
6. If a new FEATURE was added, update this doc's Section 3 vocabulary list

When removing tests:
- Do NOT renumber. Leave gaps. History matters.
