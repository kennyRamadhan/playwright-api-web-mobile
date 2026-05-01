"""CredentialManager — single source of truth for environment config and secrets.

Architectural role
------------------
Tests need URLs (API base, web base) and credentials (admin/customer)
that vary by environment. Hardcoding them is fragile; scattering
``os.environ.get(...)`` calls across files is worse. This class
centralizes the lookup and gives every fixture a clean ``credentials``
object to depend on.

Two-tier configuration
----------------------
Values come from two sources, in this priority order:

1. **Environment variables (via ``.env``)** — for secrets that must
   not be committed (real customer passwords if pointed at a private
   environment). Highest priority.
2. **YAML files (``config/env_<env>.yaml``)** — for non-secret
   defaults that ARE committed (the public demo's URLs and seeded
   credentials).

The resolution order means a developer can override any single value
locally by exporting an env var, without editing the YAML.

Why this exists despite the demo using public credentials
---------------------------------------------------------
The pattern mirrors production work (see ``UCO Collect`` reference in
the docstring below). Keeping it in this portfolio repo means readers
see the same shape they'll meet in real engagements: secrets in env,
defaults in YAML, one class to glue them.

Pattern reference for: any future config-loading utilities in ``src/utils/``.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class CredentialManager:
    """Centralized access to credentials and environment config.

    Constructed once per pytest session via the root ``credentials``
    fixture (see ``conftest.py``). All fixtures and test code that
    need URLs or credentials depend on this instance.

    Usage::

        creds = CredentialManager(env="dev")
        client = AuthService(base_url=creds.api_base_url)
        await client.login(creds.admin_email, creds.admin_password)
    """

    def __init__(self, env: str = "dev") -> None:
        # ``load_dotenv`` is idempotent — re-calls in test sessions are
        # safe. We call it eagerly here so anyone constructing this
        # class gets ``.env`` values without a separate setup step.
        load_dotenv()
        self._env = env
        self._config = self._load_yaml()

    def _load_yaml(self) -> dict[str, Any]:
        """Load ``config/env_<env>.yaml`` if it exists, else return ``{}``.

        Returning an empty dict (rather than raising) lets the public
        property defaults below still work in environments where the
        YAML hasn't been provisioned yet — useful in CI where only env
        vars are set.
        """
        # Resolve relative to this file, not the CWD, so the lookup is
        # stable regardless of where pytest is invoked from.
        config_path = (
            Path(__file__).resolve().parent.parent.parent / "config" / f"env_{self._env}.yaml"
        )
        if not config_path.exists():
            return {}
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}

    def get(self, key: str, default: Any = None) -> Any:
        """Look up a config value with env-var precedence.

        ``key`` uses dot-notation for nested YAML (e.g.
        ``"credentials.admin.email"``). The same key as an env var is
        the upper-snake-case form (``CREDENTIALS_ADMIN_EMAIL``).

        Returns ``default`` if neither source has the key.
        """
        # Env var path comes first — highest precedence.
        env_key = key.upper().replace(".", "_")
        if env_value := os.environ.get(env_key):
            return env_value

        # Walk the dotted path through the YAML dict.
        node: Any = self._config
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        # Treat explicit ``null`` in YAML the same as a missing key —
        # callers want the default in either case.
        return node if node is not None else default

    @property
    def env(self) -> str:
        return self._env

    # ------------------------------------------------------------------
    # Convenience properties for the most common lookups.
    # The defaults here point at the public Practice Software Testing
    # demo so the repo works out-of-the-box without any config file.
    # ------------------------------------------------------------------

    @property
    def api_base_url(self) -> str:
        return str(self.get("api.base_url", "https://api.practicesoftwaretesting.com"))

    @property
    def web_base_url(self) -> str:
        return str(self.get("web.base_url", "https://practicesoftwaretesting.com"))

    @property
    def admin_email(self) -> str:
        return str(self.get("credentials.admin.email", "admin@practicesoftwaretesting.com"))

    @property
    def admin_password(self) -> str:
        return str(self.get("credentials.admin.password", "welcome01"))

    @property
    def customer_email(self) -> str:
        return str(self.get("credentials.customer.email", "customer@practicesoftwaretesting.com"))

    @property
    def customer_password(self) -> str:
        return str(self.get("credentials.customer.password", "welcome01"))
