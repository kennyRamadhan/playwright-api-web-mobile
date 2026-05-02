"""Web-aware allure step decorator.

Wraps ``allure.step`` to additionally capture a screenshot of the
current page state AFTER each step completes. Replaces ``@allure.step``
in page-object methods so the report shows the visual progression of
the user journey rather than only a tree of step titles.

Usage
-----
::

    from src.utils.web_step import web_step

    @web_step("Login as {email}")
    async def login(self, email: str, password: str) -> None:
        ...

The decorator expects the decorated method to live on a class with
a ``self.page`` attribute exposing a Playwright ``Page``. If
``self.page`` is missing (e.g. the decorator is used on a non-page
class), the decorator falls back to plain ``allure.step`` behaviour
and logs a debug message instead of raising.

Why screenshot AFTER the step body
----------------------------------
The reader of the report wants to see the *result* of each action
(post-fill, post-click), not the page state before the action. A
"before" screenshot is already implicitly the "after" of the previous
step.

Why ``PlaywrightError`` is swallowed
------------------------------------
Some methods navigate away or close the page (logout, exit). The
final screenshot may then fail because the target context is gone.
That's expected — we log at debug level and move on rather than
masking the test outcome with a screenshot-capture failure.
"""

from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar, cast

import allure
from playwright.async_api import Error as PlaywrightError

P = ParamSpec("P")
R = TypeVar("R")
logger = logging.getLogger(__name__)


def web_step(title: str) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator: ``allure.step`` + auto-screenshot after the body runs.

    Parameters
    ----------
    title:
        Step title shown in the Allure report. Supports ``{param}``
        placeholders that resolve from the decorated method's named
        arguments — same syntax as ``allure.step`` itself.
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            self_obj = args[0] if args else None
            formatted_title = _format_title(title, func, args, kwargs)
            with allure.step(formatted_title):
                result = await func(*args, **kwargs)
                await _attach_screenshot(self_obj, formatted_title)
                return result

        return cast(Callable[P, Awaitable[R]], async_wrapper)

    return decorator


def _format_title(
    title: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """Resolve ``{param}`` placeholders in the title.

    Mirrors the behaviour of ``allure.step``'s implicit formatting so
    callers can swap ``@allure.step`` for ``@web_step`` without
    rewriting titles. Falls back to the raw title on any formatting
    error — a malformed step name is preferable to a crashed test.
    """
    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        params = dict(bound.arguments)
        # Drop ``self`` — it's never useful in a step title.
        if params:
            first_key = next(iter(params))
            if first_key == "self":
                params.pop(first_key)
        return title.format(**params)
    except (KeyError, ValueError, TypeError, IndexError):
        return title


async def _attach_screenshot(self_obj: Any, step_title: str) -> None:
    """Capture and attach a viewport screenshot from ``self.page``.

    Viewport (not full-page) is intentional: per-step screenshots
    are cheap visual breadcrumbs, not the forensic full-page capture
    used on failure. Keeping them small reduces report size.
    """
    if self_obj is None:
        return
    page = getattr(self_obj, "page", None)
    if page is None:
        logger.debug(
            "web_step: no self.page on %s, skipping screenshot",
            type(self_obj).__name__,
        )
        return
    try:
        screenshot_bytes = await page.screenshot(full_page=False)
        allure.attach(
            screenshot_bytes,
            name=f"After: {step_title}",
            attachment_type=allure.attachment_type.PNG,
        )
    except PlaywrightError as e:
        logger.debug("web_step: screenshot failed for %s: %s", step_title, e)
