"""Sync allure step decorator with auto-screenshot for mobile screens.

Mirrors the @web_step decorator pattern in src/utils/web_step.py but
sync (because Appium Python Client is sync). Captures a screenshot
after each decorated method completes, providing a visual storyboard
of the mobile user journey in Allure reports.

Usage::

    from src.utils.mobile_step import mobile_step

    class LoginScreen(BaseScreen):
        @mobile_step("Enter username {username}")
        def enter_username(self, username: str) -> None:
            self.find(By.ACCESSIBILITY_ID, "Username input field").send_keys(username)

The decorator expects the decorated method to be on a class with
``self.driver`` (Appium WebDriver). If ``self.driver`` is missing or
screenshot capture fails, the step still completes - the screenshot
is best-effort.
"""

from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast

import allure

P = ParamSpec("P")
R = TypeVar("R")
logger = logging.getLogger(__name__)


def mobile_step(title: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator: allure.step + auto-screenshot after sync method completes."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            self_obj = args[0] if args else None
            formatted_title = _format_title(title, func, args, kwargs)
            with allure.step(formatted_title):
                result = func(*args, **kwargs)
                _attach_screenshot(self_obj, formatted_title)
                return result

        return cast(Callable[P, R], wrapper)

    return decorator


def _format_title(
    title: str,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """Resolve {param} placeholders using bound function arguments."""
    try:
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        params = dict(bound.arguments)
        if params:
            first_key = next(iter(params))
            if first_key == "self":
                params.pop(first_key)
        return title.format(**params)
    except (KeyError, ValueError, TypeError, IndexError):
        return title


def _attach_screenshot(self_obj: Any, step_title: str) -> None:
    """Capture and attach a screenshot from self.driver."""
    if self_obj is None:
        return
    driver = getattr(self_obj, "driver", None)
    if driver is None:
        logger.debug("mobile_step: no self.driver on %s", type(self_obj).__name__)
        return
    try:
        screenshot = driver.get_screenshot_as_png()
        allure.attach(
            screenshot,
            name=f"After: {step_title}",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as e:  # noqa: BLE001
        # Driver may be in a bad state mid-test (app crashed, etc.) -
        # swallow and log rather than failing the test on missing screenshot.
        logger.debug("mobile_step: screenshot failed for %s: %s", step_title, e)
