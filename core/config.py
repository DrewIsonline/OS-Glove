"""Configuration and local-model policy for Ubuntu Glove.

The desktop overlay is useful without a model. When a model is configured, this
module deliberately accepts only a loopback OpenAI-compatible OpenS gateway.
There is no default external endpoint and no API-key storage in this app.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ConfigurationError(ValueError):
    """Raised when a user-controlled configuration is invalid or unsafe."""


LOCAL_HOSTS = frozenset({"127.0.0.1", "::1"})
VALID_MODES = frozenset({"active", "quiet", "off"})


def default_config_root() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "ubuntu-glove"


def _atomic_json_write(path: Path, payload: dict[str, Any], mode: int = 0o600) -> None:
    """Write configuration atomically and restrict it to the logged-in user."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    temporary = Path(temporary_name)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(path)
        try:
            os.chmod(path, mode)
        except OSError:
            pass
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise


def validate_local_endpoint(endpoint: str) -> str:
    """Accept only an explicit loopback HTTP endpoint.

    ``localhost`` is intentionally rejected. A local hosts-file override can
    point it elsewhere; an explicit loopback address is unambiguous.
    """
    candidate = endpoint.strip().rstrip("/")
    parsed = urlparse(candidate)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ConfigurationError("The local model endpoint must be an http:// loopback URL.")
    if parsed.hostname not in LOCAL_HOSTS:
        raise ConfigurationError(
            "Remote model endpoints are disabled. Use an explicit loopback address such as http://127.0.0.1:8080/v1."
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ConfigurationError("The local model endpoint cannot contain credentials, a query string, or a fragment.")
    if parsed.path and not parsed.path.startswith("/v1"):
        raise ConfigurationError("The local model endpoint path must be empty or begin with /v1.")
    return candidate


@dataclass(frozen=True)
class ModelRoute:
    """A pinned local gateway route that the application may call."""

    route_id: str
    api_model: str
    model_family: str
    revision: str
    artifact_sha256: str
    enabled: bool


class ModelRegistry:
    """Reads immutable, reviewed local routes from ``data/models.lock.json``."""

    def __init__(self, lock_path: Path | str) -> None:
        self.path = Path(lock_path)
        self._routes = self._load()

    def _load(self) -> dict[str, ModelRoute]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ConfigurationError(f"Missing model lock file: {self.path}") from error
        except json.JSONDecodeError as error:
            raise ConfigurationError(f"Invalid model lock file: {error}") from error
        if not isinstance(payload, dict) or payload.get("schema_version") != "1.0":
            raise ConfigurationError("models.lock.json must be an object with schema_version 1.0.")
        rows = payload.get("routes")
        if not isinstance(rows, list):
            raise ConfigurationError("models.lock.json routes must be an array.")
        routes: dict[str, ModelRoute] = {}
        for index, row in enumerate(rows, 1):
            if not isinstance(row, dict):
                raise ConfigurationError(f"Model route {index} must be an object.")
            fields = ("route_id", "api_model", "model_family", "revision", "artifact_sha256", "enabled")
            if any(field not in row for field in fields):
                raise ConfigurationError(f"Model route {index} is missing a required field.")
            route_id = row["route_id"]
            api_model = row["api_model"]
            family = row["model_family"]
            revision = row["revision"]
            digest = row["artifact_sha256"]
            enabled = row["enabled"]
            if not all(isinstance(value, str) and value.strip() for value in (route_id, api_model, family, revision)):
                raise ConfigurationError(f"Model route {index} has an invalid text field.")
            if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.casefold()):
                raise ConfigurationError(f"Model route {index} needs a 64-character lowercase SHA-256 value.")
            if not isinstance(enabled, bool) or route_id in routes:
                raise ConfigurationError(f"Model route {index} has an invalid enabled value or duplicate route_id.")
            routes[route_id] = ModelRoute(route_id, api_model, family, revision, digest.casefold(), enabled)
        return routes

    def route(self, route_id: str) -> ModelRoute:
        route = self._routes.get(route_id)
        if route is None:
            raise ConfigurationError(f"Model route '{route_id}' is not in the reviewed models.lock.json file.")
        if not route.enabled:
            raise ConfigurationError(f"Model route '{route_id}' is disabled in models.lock.json.")
        return route


class SettingsStore:
    """Thread-safe, per-user settings with secure atomic writes."""

    def __init__(self, config_root: Path | str | None = None) -> None:
        self.config_root = Path(config_root or default_config_root()).expanduser()
        self.path = self.config_root / "settings.json"
        self._lock = threading.RLock()

    @staticmethod
    def _default() -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "mode": "active",
            "privacy": {"screen_read_enabled": False},
        }

    def read(self) -> dict[str, Any]:
        with self._lock:
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return self._default()
            except json.JSONDecodeError as error:
                raise ConfigurationError(f"Invalid settings.json: line {error.lineno}, column {error.colno}") from error
        if not isinstance(payload, dict):
            raise ConfigurationError("settings.json must be a JSON object.")
        result = self._default()
        if payload.get("schema_version", "1.0") != "1.0":
            raise ConfigurationError("Unsupported settings.json schema version.")
        mode = str(payload.get("mode", "active")).casefold()
        if mode not in VALID_MODES:
            raise ConfigurationError("mode must be active, quiet, or off.")
        result["mode"] = mode
        privacy = payload.get("privacy", {})
        if privacy is not None and not isinstance(privacy, dict):
            raise ConfigurationError("privacy must be an object.")
        if isinstance(privacy, dict) and "screen_read_enabled" in privacy:
            if not isinstance(privacy["screen_read_enabled"], bool):
                raise ConfigurationError("privacy.screen_read_enabled must be true or false.")
            result["privacy"]["screen_read_enabled"] = privacy["screen_read_enabled"]
        llm = payload.get("llm")
        if llm is not None:
            if not isinstance(llm, dict):
                raise ConfigurationError("llm must be an object.")
            endpoint = llm.get("endpoint")
            route_id = llm.get("route_id")
            if not isinstance(endpoint, str) or not isinstance(route_id, str):
                raise ConfigurationError("llm.endpoint and llm.route_id are required text fields.")
            result["llm"] = {
                "provider": "openai_compatible_local",
                "endpoint": validate_local_endpoint(endpoint),
                "route_id": route_id,
            }
        return result

    def _write(self, payload: dict[str, Any]) -> None:
        _atomic_json_write(self.path, payload)

    def mode(self) -> str:
        return str(self.read()["mode"])

    def set_mode(self, mode: str) -> None:
        normalized = mode.casefold().strip()
        if normalized not in VALID_MODES:
            raise ConfigurationError("mode must be active, quiet, or off.")
        with self._lock:
            payload = self.read()
            payload["mode"] = normalized
            self._write(payload)

    def configure_local_gateway(self, endpoint: str, route_id: str, registry: ModelRegistry) -> None:
        cleaned_endpoint = validate_local_endpoint(endpoint)
        cleaned_route = route_id.strip()
        if not cleaned_route:
            raise ConfigurationError("A reviewed local model route ID is required.")
        registry.route(cleaned_route)
        with self._lock:
            payload = self.read()
            payload["llm"] = {
                "provider": "openai_compatible_local",
                "endpoint": cleaned_endpoint,
                "route_id": cleaned_route,
            }
            self._write(payload)

    def set_screen_read_enabled(self, enabled: bool) -> None:
        with self._lock:
            payload = self.read()
            payload["privacy"] = {"screen_read_enabled": bool(enabled)}
            self._write(payload)

    def screen_read_enabled(self) -> bool:
        return bool(self.read()["privacy"]["screen_read_enabled"])
