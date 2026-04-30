"""Credential management for tests.

Loads from environment variables (via .env) and YAML config.
Mirrors the production pattern (UCO Collect uses .auth/credentials/{env}.yaml).
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class CredentialManager:
    """Centralized access to credentials and environment config."""

    def __init__(self, env: str = "dev") -> None:
        load_dotenv()
        self._env = env
        self._config = self._load_yaml()

    def _load_yaml(self) -> dict[str, Any]:
        config_path = (
            Path(__file__).resolve().parent.parent.parent / "config" / f"env_{self._env}.yaml"
        )
        if not config_path.exists():
            return {}
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value. ENV vars take precedence over YAML."""
        env_key = key.upper().replace(".", "_")
        if env_value := os.environ.get(env_key):
            return env_value

        node: Any = self._config
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node if node is not None else default

    @property
    def env(self) -> str:
        return self._env

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
