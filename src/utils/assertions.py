"""Allure-aware assertion helpers.

These wrap common assertion patterns in `with allure.step()` blocks so
each assertion appears as a visible node in the Allure report tree,
with the actual vs expected values attached.
"""

from typing import Any

import allure


def expect_status(response: Any, expected: int | tuple[int, ...]) -> None:
    """Assert HTTP status code matches expected, with Allure step + attachment."""
    expected_tuple = (expected,) if isinstance(expected, int) else expected
    expected_str = " or ".join(str(s) for s in expected_tuple)
    with allure.step(f"Expect status code = {expected_str}"):
        actual = response.status_code
        allure.attach(
            f"Expected: {expected_str}\nActual: {actual}",
            name="Status assertion",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert actual in expected_tuple, (
            f"Expected status {expected_str}, got {actual}: {response.text[:500]}"
        )


def expect_field(obj: Any, field: str, expected: Any = ...) -> Any:
    """Assert object has field, optionally matching expected value.

    Returns the actual value for chaining.
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
    """Get field from dict, Pydantic model, or object via attribute."""
    if isinstance(obj, dict):
        return obj.get(field)
    return getattr(obj, field, None)
