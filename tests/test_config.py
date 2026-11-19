from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.config import ConfigurationError, ModelRegistry, SettingsStore, validate_local_endpoint


class ConfigTests(unittest.TestCase):
    def test_accepts_explicit_ipv4_loopback(self) -> None:
        self.assertEqual(validate_local_endpoint("http://127.0.0.1:8080/v1/"), "http://127.0.0.1:8080/v1")

    def test_rejects_remote_and_ambiguous_endpoints(self) -> None:
        for endpoint in ("https://api.example.com/v1", "http://localhost:8080/v1", "http://192.168.1.10:8080/v1"):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ConfigurationError):
                    validate_local_endpoint(endpoint)

    def test_only_enabled_reviewed_route_can_be_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = root / "models.lock.json"
            lock.write_text(json.dumps({
                "schema_version": "1.0",
                "routes": [{
                    "route_id": "opens-lite-qwen3-4b",
                    "api_model": "qwen3-4b",
                    "model_family": "Qwen3",
                    "revision": "example-pinned-revision",
                    "artifact_sha256": "a" * 64,
                    "enabled": True,
                }],
            }), encoding="utf-8")
            store = SettingsStore(root / "config")
            store.configure_local_gateway("http://127.0.0.1:8080/v1", "opens-lite-qwen3-4b", ModelRegistry(lock))
            self.assertTrue((root / "config" / "settings.json").is_file())
            self.assertEqual(store.read()["llm"]["route_id"], "opens-lite-qwen3-4b")

    def test_unknown_route_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = root / "models.lock.json"
            lock.write_text('{"schema_version":"1.0","routes":[]}', encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                SettingsStore(root / "config").configure_local_gateway("http://127.0.0.1:8080/v1", "unknown", ModelRegistry(lock))


if __name__ == "__main__":
    unittest.main()
