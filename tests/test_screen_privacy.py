from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.screen_vision import AccessibilityInspector, AccessibilityUnavailableError


class ScreenPrivacyTests(unittest.TestCase):
    def test_capture_is_blocked_when_accessibility_is_unavailable(self) -> None:
        inspector = AccessibilityInspector()
        with patch.object(inspector, "_load_pyatspi", side_effect=AccessibilityUnavailableError("unavailable")):
            with self.assertRaises(AccessibilityUnavailableError):
                inspector.capture_to_private_file()

    @unittest.skipIf(os.name == "nt", "POSIX permissions are verified on Ubuntu, not Windows")
    def test_private_capture_path_has_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {"XDG_RUNTIME_DIR": temporary}, clear=False):
            target = AccessibilityInspector._new_private_capture_path()
            self.assertFalse(target.exists())
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)


if __name__ == "__main__":
    unittest.main()
