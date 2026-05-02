# API Test Coverage

## About this document

This document maps the Practice Software Testing REST API endpoints to
the test cases in this repository. It is **not** an API reference — it
is a coverage map.

For canonical request/response schemas, refer to the upstream Swagger UI:

🔗 **https://api.practicesoftwaretesting.com/api/documentation**

What this document provides that Swagger does not:

- Which endpoints this repo's tests cover, and at what status codes
- Real example payloads observed during test runs (sensitive data masked)
- Quirks and non-standard behaviors discovered during testing
- Pydantic response models defined in `src/models/` for type-safe assertions
- Honest coverage gaps — what is NOT tested yet, and why

How to read this document:

1. **Quick reference table** below for endpoint → test ID lookup
2. **By Resource** sections for endpoint groupings, with detailed scenarios
3. **Quirks discovered** subsections highlight non-obvious API behaviors
4. **Coverage gaps** section sets the roadmap for future test work

Last verified: 2026-05-02

---

## Quick reference

24 API tests total. Test IDs follow the convention defined in
[ALLURE_TEST_IDS.md](../ALLURE_TEST_IDS.md): `API-{FEATURE}-{HTTP_CODE}-{NUM}`.

| Test ID | Method | Endpoint | Status | Scenario |
|---|---|---|---|---|
| API-AUTH-200-001 | POST | /users/login | 200 | Valid login returns access token |
| API-AUTH-200-002 | GET | /users/refresh | 200 | Token refresh returns a new access token |
| API-AUTH-401-001 | POST | /users/login | 401 | Login with invalid password returns 401 |
| API-AUTH-401-002 | GET | /users/me | 401 | Calling protected endpoint without token returns 401 |
| API-AUTH-401-003 | POST | /users/login | 401 | Malformed login body returns 401 (Laravel default) |
| API-CART-200-001 | POST | /carts/{id} | 200 | Add product to cart returns success |
| API-CART-200-002 | POST | /carts/{id} | 200 | Re-adding the same product accumulates the cart quantity |
| API-CART-204-001 | DELETE | /carts/{id}/product/{pid} | 200/204 | Remove cart item succeeds with 200/204 |
| API-CART-422-001 | POST | /carts/{id} | 422 | Add to cart with invalid quantity (0) returns 422 |
| API-ORDERS-200-001 | GET | /invoices/{id} | 200 | GET /invoices/{id} returns order details |
| API-ORDERS-200-002 | GET | /invoices | 200 | GET /invoices returns the user's order history |
| API-ORDERS-201-001 | POST | /invoices | 201 | Create invoice from cart returns 201 with invoice number |
| API-ORDERS-422-001 | POST | /invoices | 422 | Create invoice without payment_details returns 422 |
| API-PRODUCTS-200-001 | GET | /products | 200 | GET /products returns a paginated list |
| API-PRODUCTS-200-002 | GET | /products/{id} | 200 | GET /products/{id} returns a single product |
| API-PRODUCTS-200-003 | GET | /products | 200 | GET /products with category filter returns filtered list |
| API-PRODUCTS-201-001 | POST | /products | 201 | POST /products as admin creates a product |
| API-PRODUCTS-404-001 | GET | /products/{id} | 404 | GET /products/{invalid-id} returns 404 |
| API-PRODUCTS-422-001 | POST | /products | 422 | POST /products with missing required fields returns 422 |
| API-USERS-200-001 | GET | /users | 200 | GET /users as admin returns user list |
| API-USERS-200-002 | GET | /users/me | 200 | GET /users/me returns the current authenticated user |
| API-USERS-200-003 | PUT | /users/{id} | 200/204 | PUT /users/me updates the current user's profile |
| API-USERS-201-001 | POST | /users/register | 201 | POST /users/register creates a new user |
| API-USERS-403-001 | GET | /users | 403 | GET /users as non-admin customer returns 403 |

---

## Authentication (`/users/login`, `/users/refresh`, `/users/logout`)

**Source code:** `src/api_clients/auth_service.py`
**Test file:** `tests/api/test_auth.py`
**Pydantic models:** `src/models/user.py` (`LoginRequest`, `LoginResponse`)

### Endpoints covered

| Method | Path | Test IDs | Coverage notes |
|---|---|---|---|
| POST | /users/login | API-AUTH-200-001, API-AUTH-401-001, API-AUTH-401-003 | Happy path + invalid-password + malformed-body |
| GET | /users/refresh | API-AUTH-200-002 | Happy path only |
| GET | /users/logout | (none directly) | Called as side-effect in `AuthService.logout`; no dedicated test |
| GET | /users/me | API-AUTH-401-002 | Auth-missing case (used as a representative protected endpoint) |

### Detailed scenarios

#### API-AUTH-200-001 — Valid login returns access token

**Test:** `tests/api/test_auth.py::TestLogin::test_valid_login_returns_token`

**Scenario:** Submit valid admin credentials and verify the response
contains a non-empty access token, a "bearer" token type (case-insensitive),
and a positive `expires_in`.

**Example request:**

```http
POST /users/login HTTP/1.1
Content-Type: application/json
Accept: application/json

{
  "email": "admin@practicesoftwaretesting.com",
  "password": "***"
}
```

**Example response (200):**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJh... (JWT, truncated)",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Pydantic model validating this response:** `LoginResponse` (`src/models/user.py`)

#### API-AUTH-401-003 — Malformed login body returns 401

**Test:** `tests/api/test_auth.py::TestLogin::test_malformed_body_returns_401`

**Scenario:** Send a body that has neither `email` nor `password` keys
and verify the response is `401 Unauthorized` rather than the
`422 Unprocessable Entity` that most REST APIs would return for a
validation failure. The test bypasses `AuthService` here on purpose
because the `LoginRequest` Pydantic model would refuse the malformed
body before sending.

**Example request:**

```http
POST /users/login HTTP/1.1
Content-Type: application/json
Accept: application/json

{
  "foo": "bar"
}
```

**Example response (401):**

```json
{
  "message": "Unauthorized"
}
```

### Quirks discovered

- **Malformed body returns 401, not 422.** Practice Software Testing's
  auth controller treats any invalid login payload as Unauthorized
  rather than triggering a validation error response. Pinned by
  `API-AUTH-401-003`. Practical implication: when writing tests for
  any auth endpoint here, expect 401 even for malformed JSON.

- **`/users/refresh` and `/users/logout` use GET, not POST.** Most REST
  APIs use POST for these state-changing operations because they
  invalidate or rotate tokens. PST routes them as GET — likely because
  the token travels in the `Authorization` header, so the operation
  reads as a "lookup with side effect" from the API's perspective.
  Worth noting when comparing this codebase to production
  banking/fintech APIs that follow stricter REST conventions. The
  ``AuthService.logout`` method also accepts both `200` and `204` as
  success because the demo backend has historically alternated between
  them.

---

## Products (`/products`, `/products/{id}`)

**Source code:** `src/api_clients/product_service.py`
**Test file:** `tests/api/test_products.py`
**Pydantic models:** `src/models/product.py` (`Product`, `ProductList`, `ProductCreate`, `ProductUpdate`)

### Endpoints covered

| Method | Path | Test IDs | Coverage notes |
|---|---|---|---|
| GET | /products | API-PRODUCTS-200-001, API-PRODUCTS-200-003 | Listing + category-filter |
| GET | /products/{id} | API-PRODUCTS-200-002, API-PRODUCTS-404-001 | Happy path + invalid ID |
| POST | /products | API-PRODUCTS-201-001, API-PRODUCTS-422-001 | Admin create + missing-fields |
| DELETE | /products/{id} | (cleanup only) | Exercised by `API-PRODUCTS-201-001` cleanup; no dedicated assertion |

### Detailed scenarios

#### API-PRODUCTS-200-001 — GET /products returns a paginated list

**Test:** `tests/api/test_products.py::TestProductListing::test_list_products_returns_paginated_list`

**Scenario:** Hit the list endpoint with no parameters and verify the
response is a Laravel-style paginated payload — non-empty `data` array,
`current_page == 1`, and a `total` count that's at least the size of
the first page.

**Example response (200, shape representative):**

```json
{
  "current_page": 1,
  "data": [
    {
      "id": "01HQK000PRODUCT01",
      "name": "Combination Pliers",
      "description": "shape representative — see Pydantic model or upstream Swagger",
      "price": 14.99,
      "is_location_offer": false,
      "is_rental": false,
      "in_stock": true,
      "category_id": "01HQK000CATEGORY01",
      "brand_id": "01HQK000BRAND01",
      "product_image_id": "01HQK000IMAGE01"
    }
  ],
  "total": 50,
  "per_page": 9,
  "last_page": 6
}
```

**Pydantic model validating this response:** `ProductList` (`src/models/product.py`)

#### API-PRODUCTS-201-001 — POST /products as admin creates a product

**Test:** `tests/api/test_products.py::TestProductMutations::test_admin_creates_product`

**Scenario:** Authenticate as admin, fetch a real `category_id`,
`brand_id`, and `product_image_id` from the demo's reference endpoints
(`/categories`, `/brands`, `/images`), then create a new product with
those references. The test cleans up its created product in a `finally`
block to keep the demo tidy for other users.

**Example request:**

```http
POST /products HTTP/1.1
Authorization: Bearer ***
Content-Type: application/json
Accept: application/json

{
  "name": "Test Product (auto)",
  "description": "Created by automated test suite",
  "price": 9.99,
  "category_id": "01HQK000CATEGORY01",
  "brand_id": "01HQK000BRAND01",
  "product_image_id": "01HQK000IMAGE01",
  "is_location_offer": false,
  "is_rental": false
}
```

### Quirks discovered

- **`POST /products` does not enforce admin-only access.** The original
  test plan included a `403 RBAC` test that was removed because the
  demo's `/products` endpoint accepts unauthenticated POSTs. The repo
  pins validation behaviour (`API-PRODUCTS-422-001`) instead.
  Practical implication: you cannot rely on the demo to model
  admin-only mutations the way a production backend would.

- **422 surfaces when `Accept: application/json` is set.** Without that
  header, Laravel may return an HTML error page or a 302 redirect.
  `BaseService` always sets the JSON Accept header, so all tests in
  this repo see the structured 422 response. This is a Laravel
  convention worth knowing if you ever bypass `BaseService` (as the
  malformed-body auth test does).

---

## Users (`/users`, `/users/me`, `/users/register`, `/users/{id}`)

**Source code:** `src/api_clients/user_service.py`
**Test file:** `tests/api/test_users.py`
**Pydantic models:** `src/models/user.py` (`User`, `UserCreate`)

### Endpoints covered

| Method | Path | Test IDs | Coverage notes |
|---|---|---|---|
| GET | /users | API-USERS-200-001, API-USERS-403-001 | Admin list + non-admin RBAC |
| POST | /users/register | API-USERS-201-001 | Happy path with structured address |
| GET | /users/me | API-USERS-200-002 | Customer self-fetch |
| PUT | /users/{id} | API-USERS-200-003 | Profile update (routed through `/users/{id}` — see quirks) |
| DELETE | /users/{id} | (none) | Client method exists; no test yet |

### Detailed scenarios

#### API-USERS-201-001 — POST /users/register creates a new user

**Test:** `tests/api/test_users.py::TestUsers::test_register_creates_user`

**Scenario:** Generate a Faker-backed user payload, reshape the address
fields into the demo's expected nested object, and POST. Verify the
response carries an `id` and the email round-trips.

**Example request:**

```http
POST /users/register HTTP/1.1
Content-Type: application/json
Accept: application/json

{
  "first_name": "Avery",
  "last_name": "Stone",
  "email": "avery1234@example.test",
  "password": "***",
  "dob": "1992-04-18",
  "phone": "0411223344",
  "address": {
    "street": "1 Test Lane",
    "city": "Testville",
    "state": "Test State",
    "country": "AU",
    "postcode": "12345"
  }
}
```

**Example response (201, shape representative):**

```json
{
  "id": "01HQK000USER001",
  "email": "avery1234@example.test",
  "first_name": "Avery",
  "last_name": "Stone",
  "role": "user"
}
```

**Pydantic model validating this response:** `User` (`src/models/user.py`)

#### API-USERS-403-001 — GET /users as non-admin customer returns 403

**Test:** `tests/api/test_users.py::TestUsers::test_non_admin_cannot_list_users`

**Scenario:** Use the `customer_user_service` fixture (a `UserService`
pre-authenticated with the seeded customer's token) to call the admin
listing endpoint. Verify the request is rejected with `403 Forbidden`.

**Example response (403):**

```json
{
  "message": "Forbidden"
}
```

### Quirks discovered

- **Profile updates route through `PUT /users/{id}`, not `/users/me`.**
  `UserService.update_current_user` exists and points at `/users/me`,
  but `API-USERS-200-003` actually issues `PUT /users/{user_id}` after
  reading the user's `id` from `GET /users/me`. The demo's
  `/users/me` PUT handler historically returned 405 / 404 on partial
  payloads — pinning `/users/{id}` is the path that actually works.

- **PUT requires the FULL user payload, not a partial.** Sending only
  the changed field returns 422. The test fetches the current record,
  mutates one field, and writes the whole record back. Practical
  implication: the demo does not implement RFC 7396 JSON Merge Patch
  semantics on this endpoint.

- **Register requires a nested `address` object, not flat fields.** The
  `UserCreate` Pydantic model carries flat fields (`address`, `city`,
  `state`, `country`, `postcode`) that match the **web register form**.
  The API itself wants a nested `address` sub-object. The register test
  reshapes the payload accordingly. The `RegisterPage` web object also
  flattens differently — the model is pulled in two directions and
  this is documented in `src/models/user.py`.

---

## Cart (`/carts`, `/carts/{id}`, `/carts/{id}/product/{product_id}`)

**Source code:** `src/api_clients/cart_service.py`
**Test file:** `tests/api/test_cart.py`
**Pydantic models:** `src/models/cart.py` (`Cart`, `CartItem`, `CartCreate`, `CartItemAdd`, `CartItemUpdate`)

### Endpoints covered

| Method | Path | Test IDs | Coverage notes |
|---|---|---|---|
| POST | /carts | (setup only) | Used by every cart test as Arrange step; no dedicated assertion |
| GET | /carts/{id} | API-CART-200-002 | Read-back to verify accumulated quantity |
| POST | /carts/{id} | API-CART-200-001, API-CART-200-002, API-CART-422-001 | Add item, accumulate, validation |
| DELETE | /carts/{id}/product/{pid} | API-CART-204-001 | Remove item (200 or 204) |

### Detailed scenarios

#### API-CART-200-002 — Re-adding the same product accumulates the cart quantity

**Test:** `tests/api/test_cart.py::TestCart::test_update_cart_item_quantity`

**Scenario:** Add a product with quantity 1, then "update" by re-adding
the same product with quantity 3. Verify the cart now has the product
with quantity 4 (1 + 3). This pins the demo's non-standard "POST same
product accumulates" behavior.

**Example request (second POST):**

```http
POST /carts/01HQK000CART001 HTTP/1.1
Content-Type: application/json
Accept: application/json

{
  "product_id": "01HQK000PRODUCT01",
  "quantity": 3
}
```

**Example cart read-back (200, shape representative):**

```json
{
  "id": "01HQK000CART001",
  "cart_items": [
    {
      "product_id": "01HQK000PRODUCT01",
      "quantity": 4,
      "price": 14.99
    }
  ],
  "total": 59.96
}
```

#### API-CART-422-001 — Add to cart with invalid quantity (0) returns 422

**Test:** `tests/api/test_cart.py::TestCart::test_add_with_invalid_quantity_returns_422`

**Scenario:** Attempt to add a product with `quantity: 0`. Verify the
response is `422 Unprocessable Entity` (the test's catalog originally
specified 400, but Laravel's validation layer with
`Accept: application/json` actually returns 422).

### Quirks discovered

- **No PUT/PATCH for cart items — POSTing the same `product_id`
  accumulates quantity.** This is unusual: most cart APIs expose a
  `PUT /carts/{id}/items/{item_id}` for explicit quantity overwrites.
  PST conflates "add" and "update" through the same POST path. The
  client's `CartService.update_item` is therefore a thin alias around
  `add_item` — preserved for semantic readability in tests.

- **Invalid quantity returns 422, not 400.** As above, this is Laravel
  validation behaviour with `Accept: application/json`. The original
  test catalog specified 400; the contract was pinned at 422 once the
  actual behaviour was observed.

- **Remove returns 200 OR 204.** The demo backend has alternated
  between the two. `CartService.remove_item` accepts both as success.

---

## Orders (`/invoices`, `/invoices/{id}`)

**Source code:** `src/api_clients/order_service.py`
**Test file:** `tests/api/test_orders.py`
**Pydantic models:** `src/models/order.py` (`Order`, `OrderList`, `OrderCreate`)

### Endpoints covered

| Method | Path | Test IDs | Coverage notes |
|---|---|---|---|
| POST | /invoices | API-ORDERS-201-001, API-ORDERS-422-001 | Create from cart + missing payment_details |
| GET | /invoices/{id} | API-ORDERS-200-001 | Fetch by ID |
| GET | /invoices | API-ORDERS-200-002 | List user's orders |

### Detailed scenarios

#### API-ORDERS-201-001 — Create invoice from cart returns 201 with invoice number

**Test:** `tests/api/test_orders.py::TestOrders::test_create_order_from_cart`

**Scenario:** Authenticate as customer, seed a cart with one item, then
POST to `/invoices` with billing address and bank-transfer payment
details. Verify the response carries an `id` and an `invoice_number`
prefixed with `INV-`.

**Example request:**

```http
POST /invoices HTTP/1.1
Authorization: Bearer ***
Content-Type: application/json
Accept: application/json

{
  "cart_id": "01HQK000CART001",
  "billing_street": "10 Downing Street",
  "billing_city": "London",
  "billing_state": "Greater London",
  "billing_country": "UK",
  "billing_postcode": "SW1A 2AA",
  "payment_method": "bank-transfer",
  "payment_details": {
    "bank_name": "First Test Bank",
    "account_name": "Kenny Tester",
    "account_number": "1234567890"
  }
}
```

**Example response (201, shape representative):**

```json
{
  "id": "01HQK000INVOICE01",
  "invoice_number": "INV-20260502-0001",
  "invoice_date": "2026-05-02",
  "total": 59.96,
  "status": "AWAITING_PAYMENT"
}
```

**Pydantic model validating this response:** `Order` (`src/models/order.py`)

#### API-ORDERS-422-001 — Create invoice without payment_details returns 422

**Test:** `tests/api/test_orders.py::TestOrders::test_create_order_without_payment_details_returns_422`

**Scenario:** POST a complete invoice payload but omit `payment_details`.
Verify the response is `422`. This test exists because the demo
silently accepts other malformed inputs (notably an empty cart) — the
missing `payment_details` path was selected as the most reliable
validation contract to pin.

### Quirks discovered

- **The order resource is exposed as `/invoices`, not `/orders`.** The
  client class is named `OrderService` for the natural domain language,
  but every path it calls is `/invoices`. Worth knowing when reading
  the upstream Swagger UI, where these endpoints are grouped under
  "Invoices".

- **`invoice_number` is prefixed with `INV-`.** Tests assert on the
  prefix to detect contract drift if the server-side format changes.

- **`payment_details` is required even for `bank-transfer`.** A naive
  reading of "bank-transfer = no card details needed" suggests
  `payment_details` should be optional; the demo rejects the request
  with 422 if omitted regardless of `payment_method`.

- **Empty carts produce empty invoices silently.** Sending an invoice
  POST with a cart that has no items returns 201 with a zero-line
  invoice rather than 422. The 422 test therefore pivots to the
  missing-`payment_details` path, which is a reliable validation
  contract.

---

## Coverage gaps

This section is intentionally honest about what is NOT tested yet.

### Cross-cutting gaps

- **No 5xx server-error simulation.** PST demo doesn't expose endpoints
  that deterministically return 500. Considered out of scope for a
  black-box test suite against a public demo.
- **No rate-limit (429) testing.** Would require sustained load and
  could pollute the demo for other users; out of scope.
- **No contract testing against the OpenAPI schema.** Future enhancement —
  `schemathesis` or similar against the upstream Swagger spec.
- **No 401-vs-403 disambiguation across all protected endpoints.** Only
  representative endpoints (`/users/me` for 401, `/users` for 403) are
  pinned. Other protected routes are assumed to follow the same
  convention but not individually verified.

### Per-resource gaps

#### Authentication

- **`/users/logout` 200 case not asserted.** Token invalidation as a
  side-effect is not verified — i.e. there's no test that logs out
  then attempts a protected call and expects 401.
- **No token-expiry test.** Would require either mocking time or
  waiting `expires_in` seconds; deferred.
- **No refresh-after-logout test.** Behavioural contract for refresh
  on an invalidated token is unspecified by tests.

#### Products

- **`PUT /products/{id}` not covered.** No client method, no test —
  the upstream API exposes update, this repo does not exercise it yet.
- **`DELETE /products/{id}` 200 case not asserted directly.** It runs
  as cleanup in `API-PRODUCTS-201-001` but failure is suppressed; a
  dedicated assertion would pin the contract.
- **401 unauthenticated POST not pinned.** Would actually pass on the
  demo (no admin enforcement), but the contract isn't documented by
  a test.
- **Reference endpoints (`/categories`, `/brands`, `/images`) used as
  test setup, but not directly tested.**

#### Users

- **`DELETE /users/{id}` not covered.** Client method exists, no test.
- **`PUT /users/{id}` validation paths not covered.** Only the happy
  path is pinned; partial-payload-422 and unauthorized-update-403 are
  not tested.
- **Password change endpoint (if exposed) not investigated.**
- **`/users/me` PUT happy path not tested directly** — see quirks; the
  test routes through `/users/{id}` instead.

#### Cart

- **`GET /carts/{id}` happy path not directly asserted.** Used as
  read-back in `API-CART-200-002` but no test pins the empty-cart vs
  populated-cart response shape contract.
- **404 for non-existent cart ID not pinned.**
- **401 for cart access without auth not pinned.** Cart endpoints are
  public on this demo, but the contract isn't documented by a test.
- **No multi-product cart test.** Tests use a single product; a cart
  with multiple distinct items isn't exercised.

#### Orders

- **404 for invalid invoice ID not pinned.** Symmetric to
  `API-PRODUCTS-404-001` for products; would be a quick add.
- **401 on `/invoices` without auth not pinned.** Empirically rejected
  but not documented by a test.
- **403 cross-customer access not pinned.** A customer attempting to
  GET another customer's invoice should be rejected; not verified.
- **Status-update endpoints (if any) not tested.** The Swagger UI may
  expose admin endpoints to mark invoices paid / shipped — out of
  scope for this iteration.
- **`credit-card` payment_method path not exercised.** Only
  `bank-transfer` is tested, because bank-transfer is the most reliable
  default on the demo; credit-card validation may diverge.

---

## Cross-reference

- **Architectural decisions:** [ARCHITECTURE.md](../ARCHITECTURE.md)
- **Test ID naming convention:** [ALLURE_TEST_IDS.md](../ALLURE_TEST_IDS.md)
- **Project structure:** [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
- **Live Allure report:** https://kennyramadhan.github.io/playwright-api-web-mobile/
- **Upstream API spec:** https://api.practicesoftwaretesting.com/api/documentation
- **Upstream source code:** https://github.com/testsmith-io/practice-software-testing
