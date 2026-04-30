# Adding a new test

A short walkthrough so the test catalog stays consistent. The full naming convention lives in `ALLURE_TEST_IDS.md`.

## 1. Pick the surface

| Surface | Where it lives | Lib |
|---|---|---|
| API | `tests/api/` | httpx via `BaseService` subclasses |
| Web | `tests/web/` | Playwright async + Page Objects |
| Mobile (Phase 2) | `tests/mobile/` | Appium |

## 2. Pick a feature and Allure ID

1. Open `ALLURE_TEST_IDS.md` Section 3 — pick from the FEATURE vocabulary or add a new entry there first.
2. For API tests, the variant is the expected HTTP status (`200`, `401`, `422`, ...).
3. For Web tests, the variant is optional — use `NEG`/`EDGE` only when scenarios need disambiguation.
4. Find the next available `NUM` for that feature/variant pair. Don't renumber existing IDs.

## 3. Write the test

Every test must:

- Be `async def`
- Have `@allure.id("...")` and `@allure.title("...")`
- Follow AAA with explicit comment markers
- Use `@allure.severity(allure.severity_level.CRITICAL)` for happy paths

```python
import allure

from src.api_clients.auth_service import AuthService


@allure.epic("Practice Software Testing")
@allure.feature("Authentication")
class TestLogin:
    @allure.id("API-AUTH-200-001")
    @allure.title("Valid login returns access token")
    @allure.severity(allure.severity_level.CRITICAL)
    async def test_valid_login_returns_token(
        self, auth_service: AuthService, credentials
    ):
        # Arrange
        email = credentials.admin_email
        password = credentials.admin_password

        # Act
        response = await auth_service.login(email, password)

        # Assert
        assert response.access_token
        assert response.expires_in > 0
```

## 4. Don't reach into selectors or raw HTTP

- **Web:** add page methods to the appropriate `src/pages/*_page.py`. Tests only call page methods.
- **API:** add a method to the right `src/api_clients/*_service.py`. Tests don't construct httpx requests.

If you need a model field, add it to `src/models/`. Pydantic validates the response on parse — schema drift surfaces immediately.

## 5. Run locally before committing

```bash
uv run ruff check .
uv run ruff format .
uv run mypy src/
uv run pytest tests/api/test_my_feature.py -v
```

If the test passes locally and shows up in `reports/allure-results/`, you're good. Push the branch and let CI publish the updated Allure report.

## 6. If the test is flaky

Mark it explicitly so others don't lose time:

```python
@allure.id("WEB-SEARCH-FLAKY-001")
@pytest.mark.flaky(reruns=2, reruns_delay=2)
```

Then file a follow-up to investigate. Flaky markers are tracked, not hidden.
