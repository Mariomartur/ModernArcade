"""Public, game-free catalog CLI contract using synthetic temp fixtures."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.folder = Path(self.scratch.name)
        self.config = self.folder / "profiles.toml"
        self.catalog = self.folder / "catalog.toml"
        self.marker = self.folder / "process-started"
        (self.folder / "synthetic-game.bin").write_bytes(b"fixture; never open or launch")
        script = f"from pathlib import Path; Path({str(self.marker)!r}).write_text('started')"
        self.command = [sys.executable, "-c", script, "{game}"]
        self.config.write_text(
            '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "Fixture"\n'
            f'command = {json.dumps(self.command)}\n'
            '\n[[systems]]\nid = "gamecube"\nname = "GameCube"\nemulator = "Fixture"\n',
            encoding="utf-8",
        )
        self.catalog.write_text(
            '[[games]]\nid = "first"\ntitle = "First"\nsystem = "nes"\npath = "missing/game.bin"\n'
            '\n[[games]]\nid = "second"\ntitle = "Second"\nsystem = "gamecube"\npath = "other.bin"\n',
            encoding="utf-8",
        )

    def invoke(self, *args, cwd=None):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1", COLUMNS="100")
        before = {p.name: p.read_bytes() for p in self.folder.iterdir() if p.is_file()}
        result = subprocess.run(
            [sys.executable, "-B", "-m", "retrostation.catalog", "--config", str(self.config),
             "--catalog", str(self.catalog), *args], cwd=cwd or self.folder, env=env,
            capture_output=True, text=True, check=False,
        )
        self.assertEqual({p.name: p.read_bytes() for p in self.folder.iterdir() if p.is_file()}, before)
        self.assertFalse(self.marker.exists())
        self.assertNotIn("Traceback", result.stderr)
        return result

    def rejected(self, message, *args):
        result = self.invoke(*args)
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.endswith(f"error: {message}\n"), result.stderr)

    def test_list_all_in_file_order_and_preview_selected_game_without_opening_nonexistent_game(self):
        elsewhere = self.folder / "elsewhere"
        elsewhere.mkdir()
        result = self.invoke("list", cwd=elsewhere)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, f"first\tFirst\tnes\t{self.folder / 'missing/game.bin'}\n"
                             f"second\tSecond\tgamecube\t{self.folder / 'other.bin'}\n", ""))
        self.assertFalse((self.folder / "missing/game.bin").exists())
        result = self.invoke("preview", "--game-id", "first", cwd=elsewhere)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, json.dumps([*self.command[:-1], str(self.folder / "missing/game.bin")]) + "\n", ""))
        self.rejected("No launch command for system: gamecube", "preview", "--game-id", "second")
        self.rejected("Unknown game id: absent", "preview", "--game-id", "absent")

    def test_absolute_path_is_preserved_and_nonexistent_game_is_not_checked(self):
        absolute = self.folder / "nonexistent.bin"
        self.catalog.write_text(
            f'[[games]]\nid = "absolute"\ntitle = "Absolute"\nsystem = "nes"\npath = {json.dumps(str(absolute))}\n',
            encoding="utf-8",
        )
        self.assertEqual(self.invoke("list").stdout, f"absolute\tAbsolute\tnes\t{absolute}\n")
        result = self.invoke("preview", "--game-id", "absolute")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, json.dumps([*self.command[:-1], str(absolute)]) + "\n", ""))
        self.assertFalse(absolute.exists())

    def test_invalid_entries_and_document_structure_are_rejected(self):
        base = '[[games]]\nid = "first"\ntitle = "First"\nsystem = "nes"\npath = "x.bin"\n'
        cases = (
            ('[other]\nvalue = 1\n', "Unknown catalog field: other"),
            ('games = "text"\n', "Expected [[games]] entries in the catalog file"),
            ('games = [2]\n', "Invalid game at entry 1"),
            (base + 'extra = true\n', "Unknown field at game entry 1: extra"),
            (base + '\n[[games]]\nid = "first"\ntitle = "Again"\nsystem = "nes"\npath = "y"\n', "Duplicate game id: first"),
            (base.replace('system = "nes"', 'system = "missing"'), "Unknown system: missing"),
        )
        for content, message in cases:
            with self.subTest(message=message):
                self.catalog.write_text(content, encoding="utf-8")
                self.rejected(message, "list")
                self.rejected(message, "preview", "--game-id", "first")

    def test_required_fields_must_be_nonempty_strings_without_tsv_control_characters(self):
        base = {'id': '"first"', 'title': '"First"', 'system': '"nes"', 'path': '"x.bin"'}
        for field in base:
            for value in (None, '"  "', '7', '"bad\\tvalue"', '"bad\\nvalue"', '"bad\\rvalue"'):
                with self.subTest(field=field, value=value):
                    row = dict(base)
                    if value is None:
                        del row[field]
                    else:
                        row[field] = value
                    self.catalog.write_text('[[games]]\n' + ''.join(f'{key} = {entry}\n' for key, entry in row.items()), encoding="utf-8")
                    self.rejected(f"Invalid {field} at game entry 1", "list")

    def test_bad_catalog_and_profiles_have_controlled_diagnostics(self):
        for target, label in ((self.catalog, "catalog"), (self.config, "profiles")):
            original = target.read_bytes()
            for content in (b"[", b'[[games]]\ntitle = "\xff"\n'):
                with self.subTest(target=label, content=content):
                    target.write_bytes(content)
                    result = self.invoke("list")
                    self.assertEqual((result.returncode, result.stdout), (2, ""))
                    self.assertIn(f"error: Cannot read {label}:", result.stderr)
            target.write_bytes(original)
            missing = self.folder / (label + "-absent.toml")
            target.rename(missing)
            # Invoke using the original path; no new file may be created by the CLI.
            result = self.invoke("preview", "--game-id", "first")
            self.assertEqual((result.returncode, result.stdout), (2, ""))
            self.assertIn(f"error: Cannot read {label}:", result.stderr)
            missing.rename(target)

    def test_repeated_options_and_missing_options_rejected_before_reading(self):
        for args, message in (
            (("--config", str(self.config), "list"), "--config must be provided exactly once"),
            (("--catalog", str(self.catalog), "list"), "--catalog must be provided exactly once"),
        ):
            with self.subTest(args=args):
                self.rejected(message, *args)
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        for option in ("--config", "--catalog"):
            args = (["--catalog", str(self.catalog)] if option == "--config" else ["--config", str(self.config)])
            result = subprocess.run([sys.executable, "-B", "-m", "retrostation.catalog", *args, "list"],
                                    cwd=self.folder, env=env, capture_output=True, text=True, check=False)
            self.assertEqual((result.returncode, result.stdout), (2, ""))
            self.assertIn("required:", result.stderr)
            self.assertIn(option, result.stderr)

    def test_help_describes_isolated_read_only_interface(self):
        result = self.invoke("--help")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        for text in ("list", "preview", "--config", "--catalog", "read-only", "--game-id"):
            self.assertIn(text, result.stdout)


if __name__ == "__main__":
    unittest.main()
