"""Exercise the user-facing RetroStation CLI without installed emulators."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SystemsCommandTests(unittest.TestCase):
    def test_lists_multiple_configured_systems_without_changing_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            contents = (
                '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\n'
                '\n[[systems]]\nid = "gamecube"\nname = "GameCube"\nemulator = "Dolphin"\n'
            )
            config.write_text(contents, encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            result = subprocess.run(
                [sys.executable, "-B", "-m", "retrostation", "--config", str(config), "systems"],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "nes\tNES\tRetroArch\ngamecube\tGameCube\tDolphin\n")
            self.assertEqual(result.stderr, "")
            self.assertEqual(config.read_text(encoding="utf-8"), contents)

    def test_rejects_unrecognized_profile_fields_without_changing_file(self):
        cases = (
            '[system]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\n',
            '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\nexecutable = "/missing/emulator"\n',
            '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\nenabled = false\n',
        )
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            for contents in cases:
                with self.subTest(contents=contents):
                    config.write_text(contents, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", "-m", "retrostation", "--config", str(config), "systems"],
                        cwd=directory, env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("error:", result.stderr)
                    self.assertEqual(config.read_text(encoding="utf-8"), contents)

    def test_rejects_repeated_config_option(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            contents = '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\n'
            config.write_text(contents, encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [sys.executable, "-B", "-m", "retrostation", "--config", str(config.parent / "missing.toml"), "--config", str(config), "systems"],
                cwd=directory, env=environment, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("error:", result.stderr)
            self.assertEqual(config.read_text(encoding="utf-8"), contents)


if __name__ == "__main__":
    unittest.main()
