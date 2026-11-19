"""Configuration-driven tutoring, command matching, and optional LLM transport."""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from core.config import ConfigurationError, ModelRegistry, SettingsStore


class ConfigError(ValueError):
    """Raised when a community JSON data file does not meet the required schema."""


class LLMRequestError(RuntimeError):
    """Raised when an optional local or remote model endpoint rejects a request."""


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9][a-z0-9+._/-]*", value.casefold()) if len(token) > 1}


def _read_json_array(path: Path) -> list[dict[str, Any]]:
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"missing required data file: {path}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"invalid JSON in {path}: line {error.lineno}, column {error.colno}") from error
    if not isinstance(decoded, list):
        raise ConfigError(f"{path.name} must contain a JSON array")
    if not all(isinstance(item, dict) for item in decoded):
        raise ConfigError(f"every entry in {path.name} must be an object")
    return decoded


@dataclass(frozen=True)
class SafeCommand:
    """A command record preserving original JSON fields for downstream customizations."""

    command: str
    description: str
    category: str
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any], index: int) -> "SafeCommand":
        command = payload.get("cmd", payload.get("command"))
        description = payload.get("desc", payload.get("description"))
        category = payload.get("category", "General")
        if not isinstance(command, str) or not command.strip():
            raise ConfigError(f"viable_commands.json entry {index} needs non-empty 'cmd'")
        if not isinstance(description, str) or not description.strip():
            raise ConfigError(f"viable_commands.json entry {index} needs non-empty 'desc'")
        if not isinstance(category, str) or not category.strip():
            raise ConfigError(f"viable_commands.json entry {index} has an invalid 'category'")
        return cls(command.strip(), description.strip(), category.strip(), dict(payload))

    @property
    def is_destructive(self) -> bool:
        lower = self.command.casefold()
        markers = (" rm -rf", "mkfs", "dd if=", ":(){", "shutdown", "reboot", "poweroff")
        return any(marker in f" {lower}" for marker in markers)


@dataclass(frozen=True)
class OnboardingRule:
    """A deterministic tip rule preserving the community-provided shape."""

    window_keyword: str
    tip_text: str
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any], index: int) -> "OnboardingRule":
        keyword = payload.get("window_keyword")
        tip = payload.get("tip_text")
        if not isinstance(keyword, str) or not keyword.strip():
            raise ConfigError(f"onboarding_rules.json entry {index} needs non-empty 'window_keyword'")
        if not isinstance(tip, str) or not tip.strip():
            raise ConfigError(f"onboarding_rules.json entry {index} needs non-empty 'tip_text'")
        return cls(keyword.strip(), tip.strip(), dict(payload))

    def matches(self, app_id: str, title: str) -> bool:
        haystack = f"{app_id or ''} {title or ''}".casefold()
        app_filter = self.payload.get("app_id")
        if isinstance(app_filter, str) and app_filter.strip() and app_filter.casefold() != (app_id or "").casefold():
            return False
        try:
            return bool(re.search(self.window_keyword, haystack, re.IGNORECASE))
        except re.error:
            return self.window_keyword.casefold() in haystack


class LocalTutorEngine:
    """Always-local JSON rule engine used before any LLM request is considered."""

    def __init__(self, commands_path: Path | str, onboarding_path: Path | str) -> None:
        command_rows = _read_json_array(Path(commands_path))
        onboarding_rows = _read_json_array(Path(onboarding_path))
        self.commands = tuple(SafeCommand.from_payload(row, index) for index, row in enumerate(command_rows, 1))
        self.onboarding_rules = tuple(
            OnboardingRule.from_payload(row, index) for index, row in enumerate(onboarding_rows, 1)
        )

    @property
    def categories(self) -> list[str]:
        return sorted({command.category for command in self.commands}, key=str.casefold)

    def search_commands(self, query: str, category: str | None = None, limit: int = 25) -> list[SafeCommand]:
        """Rank commands using transparent lexical scoring, with no model dependency."""
        query_terms = _tokens(query)
        candidates = [item for item in self.commands if not category or item.category == category]
        if not query_terms:
            return sorted(candidates, key=lambda item: (item.category.casefold(), item.description.casefold()))[:limit]

        def score(item: SafeCommand) -> tuple[int, int, str]:
            searchable = f"{item.command} {item.description} {item.category} " + " ".join(
                str(value) for value in item.payload.get("aliases", []) if isinstance(value, str)
            )
            corpus = _tokens(searchable)
            overlap = len(query_terms & corpus)
            phrase_bonus = int(query.casefold().strip() in searchable.casefold())
            return (overlap, phrase_bonus, item.description.casefold())

        ranked = [(score(item), item) for item in candidates]
        ranked = [pair for pair in ranked if pair[0][0] > 0 or pair[0][1] > 0]
        ranked.sort(key=lambda pair: (-pair[0][0], -pair[0][1], pair[0][2]))
        return [item for _, item in ranked[:limit]]

    def matching_tips(self, app_id: str, title: str, limit: int = 3) -> list[OnboardingRule]:
        """Return local onboarding tips applicable to the active window."""
        return [rule for rule in self.onboarding_rules if rule.matches(app_id, title)][:limit]

    def resolve(self, query: str, app_id: str = "", title: str = "") -> str | None:
        """Prefer context tips, then command results; return None for genuine free-text questions."""
        tips = self.matching_tips(app_id, title, limit=1)
        if tips:
            return tips[0].tip_text
        matches = self.search_commands(query, limit=1)
        if matches:
            command = matches[0]
            warning = "\n\nWarning: review this destructive command before running it." if command.is_destructive else ""
            return f"**{command.description}**\n\n`{command.command}`{warning}"
        return None


class RemoteLLMClient:
    """Minimal client for a reviewed, loopback-only OpenS model gateway."""

    def __init__(self, settings_store: SettingsStore, registry: ModelRegistry, timeout_seconds: int = 45) -> None:
        settings = settings_store.read()
        llm = settings.get("llm")
        if not isinstance(llm, dict):
            raise LLMRequestError("No local model gateway is configured. Local notes, tips, and commands still work.")
        try:
            self.endpoint = str(llm["endpoint"])
            self.model = registry.route(str(llm["route_id"])).api_model
        except (KeyError, ConfigurationError) as error:
            raise LLMRequestError(str(error)) from error
        self.timeout_seconds = timeout_seconds

    async def answer(
        self,
        prompt: str,
        *,
        structural_context: dict[str, Any],
        image_path: Path | None = None,
    ) -> str:
        """Send only the explicit prompt, structural context, and optional user-triggered image."""
        cleaned_prompt = prompt.strip()
        if not cleaned_prompt:
            raise LLMRequestError("The assistant question cannot be empty.")
        return await asyncio.to_thread(self._answer_sync, cleaned_prompt, structural_context, image_path)

    def _answer_sync(self, prompt: str, structural_context: dict[str, Any], image_path: Path | None) -> str:
        context_text = json.dumps(structural_context, ensure_ascii=False, sort_keys=True)
        system = (
        "You are Ubuntu Glove, a careful local desktop tutor. Give concise, actionable guidance. "
        "Do not claim to have executed commands. Explain dangerous commands before recommending them. "
        "State uncertainty when structural screen context is incomplete."
        )
        user_text = f"Structural screen context (may be incomplete): {context_text}\n\nUser question: {prompt}"
        encoded_image = base64.b64encode(image_path.read_bytes()).decode("ascii") if image_path else None
        url = f"{self.endpoint}/chat/completions"
        content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        if encoded_image:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}})
        payload = {"model": self.model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}], "stream": False}
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise LLMRequestError(f"LLM endpoint returned HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise LLMRequestError(f"LLM endpoint is unavailable: {error}") from error
        except json.JSONDecodeError as error:
            raise LLMRequestError("LLM endpoint did not return JSON") from error
        try:
            answer = decoded["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise LLMRequestError("LLM response did not contain assistant text") from error
        if not isinstance(answer, str) or not answer.strip():
            raise LLMRequestError("LLM returned an empty response")
        return answer.strip()
