from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.notes_db import NotesDatabase, WindowFingerprint
from core.tutor_engine import LocalTutorEngine


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LocalFeatureTests(unittest.TestCase):
    def test_curated_commands_are_searchable_and_not_executed(self) -> None:
        engine = LocalTutorEngine(PROJECT_ROOT / "data" / "viable_commands.json", PROJECT_ROOT / "data" / "onboarding_rules.json")
        result = engine.search_commands("show network status")
        self.assertEqual(result[0].command, "ip -br a")
        self.assertGreaterEqual(len(engine.commands), 20)
        destructive = [cmd for cmd in engine.commands if cmd.is_destructive]
        self.assertTrue(any("reboot" in cmd.command for cmd in destructive))

    def test_tip_matches_terminal(self) -> None:
        engine = LocalTutorEngine(PROJECT_ROOT / "data" / "viable_commands.json", PROJECT_ROOT / "data" / "onboarding_rules.json")
        self.assertTrue(engine.matching_tips("org.gnome.Terminal", "Terminal"))

    def test_note_uses_escaped_exact_window_title(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = NotesDatabase(Path(temporary) / "context_notes.db")
            fingerprint = WindowFingerprint.from_window("org.gnome.Terminal", "[project] (safe)")
            saved = database.save_note(fingerprint, "Remember this.")
            self.assertEqual(database.matching_notes("org.gnome.Terminal", "[project] (safe)")[0].id, saved.id)
            self.assertEqual(database.matching_notes("org.gnome.Terminal", "project safe"), [])


if __name__ == "__main__":
    unittest.main()
