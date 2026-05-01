"""Allure-aware assertion helpers.

Why these exist
---------------
A raw ``assert response.status_code == 200`` works fine, but the Allure
report just shows a generic test failure with a Python traceback —
useful for the engineer who wrote the test, not for a recruiter or
non-technical reviewer reading the report.

These helpers wrap common assertion patterns in ``with allure.step()``
blocks and attach actual-vs-expected text so the report tree shows:

    Expect status code = 200
        Status assertion (attachment)
            Expected: 200
            Actual: 401

Use these for assertions where the actual-vs-expected diff carries
diagnostic value. Raw ``assert`` is still acceptable (and preferred)
for trivial truthiness checks where the AssertionError message is
self-explanatory — assertion ceremony is not the goal.

When to add a new helper
------------------------
When a particular assertion shape is repeated across multiple tests
and would benefit from a labelled step in the report. Keep helpers
narrow and well-named — a generic ``expect_anything`` would defeat
the purpose.

Pattern reference for: any future assertion utilities.
"""

from typing import Any

import allure


def expect_status(response: Any, expected: int | tuple[int, ...]) -> None:
    """Assert HTTP status code matches expected, with Allure step + attachment.

    Accepts either a single status code or a tuple — useful when an
    endpoint legitimately returns different success codes (e.g. 200 or
    204 for ``logout``).

    The attached text shows expected and actual side by side, so a
    failure in CI is debuggable from the published report alone
    without re-running the test locally.
    """
    expected_tuple = (expected,) if isinstance(expected, int) else expected
    expected_str = " or ".join(str(s) for s in expected_tuple)
    with allure.step(f"Expect status code = {expected_str}"):
        actual = response.status_code
        allure.attach(
            f"Expected: {expected_str}\nActual: {actual}",
            name="Status assertion",
            attachment_type=allure.attachment_type.TEXT,
        )
        # Truncate body to 500 chars on failure — long error pages
        # bloat the assertion message without adding diagnostic value
        # beyond what's already attached as a step child.
        assert actual in expected_tuple, (
            f"Expected status {expected_str}, got {actual}: {response.text[:500]}"
        )


def expect_field(obj: Any, field: str, expected: Any = ...) -> Any:
    """Assert object has field, optionally matching expected value.

    Two modes, distinguished by whether ``expected`` was passed:

    - ``expect_field(model, "access_token")`` — assert the field is
      present and truthy (covers "exists and non-empty" in one call).
      Used to verify response shape without pinning specific values.

    - ``expect_field(model, "role", "admin")`` — assert the field
      equals an exact value. Used for business-logic assertions.

    The sentinel ``...`` (Ellipsis) is used as the "not provided"
    marker because ``None`` is a legitimate expected value — a real
    test might want to assert that a field IS ``None``.

    Returns the actual field value so callers can chain further
    assertions on it without a redundant lookup.
    """
    if expected is ...:
        with allure.step(f"Expect field '{field}' present and truthy"):
            actual = _get_field(obj, field)
            allure.attach(
                f"Field: {field}\nActual: {actual!r}",
                name=f"Field check: {field}",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert actual, f"Field '{field}' missing or falsy in {obj!r}"
            return actual
    else:
        with allure.step(f"Expect {field} = {expected!r}"):
            actual = _get_field(obj, field)
            allure.attach(
                f"Field: {field}\nExpected: {expected!r}\nActual: {actual!r}",
                name=f"Field assertion: {field}",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert actual == expected, f"Expected {field}={expected!r}, got {actual!r}"
            return actual


def _get_field(obj: Any, field: str) -> Any:
    """Get field from dict, Pydantic model, or plain object via attribute.

    Handles both ``obj["field"]`` (dict) and ``obj.field`` (model /
    object) so callers don't have to branch on the type. Returns
    ``None`` if the field is absent — the calling helper handles the
    presence check.
    """
    if isinstance(obj, dict):
        return obj.get(field)
    return getattr(obj, field, None)
