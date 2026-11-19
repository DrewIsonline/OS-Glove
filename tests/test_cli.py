from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import main


class CliTests(unittest.TestCase):
    def test_cli_check_data(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main.main(["--check-data"])
        self.assertEqual(exit_code, 0)
        output = json.loads(buffer.getvalue())
        self.assertIn("commands", output)
        self.assertGreaterEqual(output["commands"], 20)
        self.assertIn("Networking", output["categories"])

    def test_cli_show_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main.main(["--config-dir", temporary, "--show-config"])
            self.assertEqual(exit_code, 0)
            output = json.loads(buffer.getvalue())
            self.assertEqual(output["mode"], "active")
            self.assertFalse(output["screen_read_enabled"])

    def test_cli_screen_read_toggle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            exit_code = main.main(["--config-dir", temporary, "--screen-read", "on"])
            self.assertEqual(exit_code, 0)
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                main.main(["--config-dir", temporary, "--show-config"])
            output = json.loads(buffer.getvalue())
            self.assertTrue(output["screen_read_enabled"])


if __name__ == "__main__":
    unittest.main()
