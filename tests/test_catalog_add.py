"""Public catalog add CLI: atomic append and rejection without side effects."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class AddTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.folder = Path(scratch.name)
        self.config = self.folder / "profiles.toml"
        self.catalog = self.folder / "catalog.toml"
        self.config.write_text(
            '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "Fixture"\n'
            'command = ["fixture", "{game}"]\n'
            '[[systems]]\nid = "other"\nname = "Other"\nemulator = "Fixture"\n', encoding="utf-8")
        self.catalog.write_bytes(b'# keep this comment\n[[games]]\nid = "first"\ntitle = "First"\n'
                                 b'system = "nes"\npath = "original/relative.bin"\n')
        self.fields = ("--id", " second ", "--title", " New title ", "--system", " nes ",
                       "--path", " missing/relative.bin ")

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.folder.iterdir() if p.is_file()}

    def invoke(self, *args, cwd=None):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(
            [sys.executable, "-B", "-m", "retrostation.catalog", "--config", str(self.config),
             "--catalog", str(self.catalog), *args], cwd=cwd or self.folder, env=env,
            capture_output=True, text=True, check=False)

    def rejected(self, message, *args):
        before = self.snapshot()
        result = self.invoke("add", *args)
        self.assertEqual((result.returncode, result.stdout), (2, ""))
        self.assertTrue(result.stderr.endswith(f"error: {message}\n"), result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_append_preserves_prefix_line_endings_comments_and_missing_final_newline(self):
        for prefix in (b"", b"# comment only", b"# CRLF\r\n", b"# LF\n",
                       b'[[games]]\r\nid = "first"\r\ntitle = "First"\r\n'
                       b'system = "nes"\r\npath = "old.bin"\r\n# trailing',
                       b'[[games]]\nid = "first"\ntitle = "First"\n'
                       b'system = "nes"\npath = "old.bin"\n# trailing'):
            with self.subTest(prefix=prefix):
                self.catalog.write_bytes(prefix)
                before = self.snapshot()
                result = self.invoke("add", *self.fields)
                self.assertEqual((result.returncode, result.stdout, result.stderr),
                                 (0, "Added game: second\n", ""))
                after = self.snapshot()
                self.assertEqual(set(after), set(before))
                self.assertEqual(after[self.config.name], before[self.config.name])
                self.assertTrue(after[self.catalog.name].startswith(prefix))
                row = (b'[[games]]\nid = "second"\ntitle = "New title"\n'
                       b'system = "nes"\npath = "missing/relative.bin"\n')
                ending = b"\r\n" if b"\r\n" in prefix else b"\n"
                self.assertEqual(after[self.catalog.name], prefix + (ending if prefix else b"")
                                 + row.replace(b"\n", ending))
                self.assertFalse((self.folder / "missing/relative.bin").exists())

    def test_list_and_preview_after_append_are_read_only_and_resolve_relative_path(self):
        elsewhere = self.folder / "elsewhere"
        elsewhere.mkdir()
        self.assertEqual((self.invoke("add", *self.fields, cwd=elsewhere).returncode), 0)
        before = self.snapshot()
        result = self.invoke("list", cwd=elsewhere)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, f"first\tFirst\tnes\t{self.folder / 'original/relative.bin'}\n"
                             f"second\tNew title\tnes\t{self.folder / 'missing/relative.bin'}\n", ""))
        result = self.invoke("preview", "--game-id", "second", cwd=elsewhere)
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, json.dumps(["fixture", str(self.folder / "missing/relative.bin")]) + "\n", ""))
        self.assertEqual(self.snapshot(), before)

    def test_unicode_quotes_backslash_and_profile_without_command(self):
        fields = ("--id", 'é"\\', "--title", 'Café "quoted" \\ ',
                  "--system", "other", "--path", 'folder\\name "x".bin')
        before = self.snapshot()
        result = self.invoke("add", *fields)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, 'Added game: é"\\\n', ""))
        self.assertTrue(self.catalog.read_bytes().startswith(before[self.catalog.name]))
        result = self.invoke("list")
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, f"first\tFirst\tnes\t{self.folder / 'original/relative.bin'}\n"
                             f'é"\\\tCafé "quoted" \\ \x01\tother\t{self.folder / "folder\\name \"x\".bin"}\n', ""))

    def test_invalid_fields_and_existing_catalog_reject_without_changes(self):
        for field, value, message in (("id", " first ", "Duplicate game id: first"),
                                      ("system", "absent", "Unknown system: absent"),
                                      *((name, "  ", f"Invalid {name} at game entry 2")
                                        for name in ("id", "title", "system", "path")),
                                      ("title", "bad\nline", "Invalid title at game entry 2"),
                                      ("path", "bad\tpath", "Invalid path at game entry 2")):
            with self.subTest(field=field, value=value):
                fields = list(self.fields)
                fields[fields.index("--" + field) + 1] = value
                self.rejected(message, *fields)
        for content, message in ((b"[", "Cannot read catalog:"),
                                 (b"\xff", "Cannot read catalog:"),
                                 (b"[unexpected]\n", "Unknown catalog field: unexpected"),
                                 (b"games = [2]\n", "Invalid game at entry 1"),
                                 (b'[[games]]\nid = 7\ntitle = "First"\nsystem = "nes"\npath = "x"\n',
                                  "Invalid id at game entry 1"),
                                 (b"games = []\n", "Cannot append [[games]] to catalog representation"),
                                 (b'games = [{id="first",title="First",system="nes",path="x"}]\n',
                                  "Cannot append [[games]] to catalog representation")):
            with self.subTest(content=content):
                self.catalog.write_bytes(content)
                before = self.snapshot()
                result = self.invoke("add", *self.fields)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertIn("error: " + message, result.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_missing_or_invalid_profiles_and_missing_catalog_reject_without_creation(self):
        for target in (self.config, self.catalog):
            with self.subTest(missing=target):
                original = target.read_bytes()
                target.unlink()
                before = self.snapshot()
                result = self.invoke("add", *self.fields)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertIn("error: Cannot read " + ("profiles" if target == self.config else "catalog") + ":", result.stderr)
                self.assertEqual(self.snapshot(), before)
                target.write_bytes(original)
        for content in (b"[", b"\xff", b"[wrong]\n"):
            with self.subTest(profile=content):
                self.config.write_bytes(content)
                before = self.snapshot()
                result = self.invoke("add", *self.fields)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertIn("error: ", result.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_missing_and_repeated_field_flags_reject_before_writing(self):
        for name in ("id", "title", "system", "path"):
            with self.subTest(name=name):
                fields = list(self.fields)
                at = fields.index("--" + name)
                del fields[at:at + 2]
                before = self.snapshot()
                result = self.invoke("add", *fields)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertIn("--" + name, result.stderr)
                self.assertEqual(self.snapshot(), before)
                self.rejected("--" + name + " must be provided exactly once",
                              *self.fields, "--" + name, "another")

    def test_read_only_catalog_replace_failure_cleans_own_temporary(self):
        from retrostation.catalog import main
        original_mode = stat.S_IMODE(self.catalog.stat().st_mode)
        os.chmod(self.catalog, stat.S_IREAD)
        try:
            before = self.snapshot()
            mode = stat.S_IMODE(self.catalog.stat().st_mode)
            argv = ["retrostation.catalog", "--config", str(self.config), "--catalog", str(self.catalog),
                    "add", *self.fields]
            out, err = io.StringIO(), io.StringIO()
            with patch.object(sys, "argv", argv), patch("retrostation.catalog.os.replace",
                side_effect=OSError("injected failure")), redirect_stdout(out), redirect_stderr(err):
                with self.assertRaises(SystemExit) as caught:
                    main()
            self.assertEqual((caught.exception.code, out.getvalue()), (2, ""))
            self.assertTrue(err.getvalue().endswith("error: Cannot update catalog: injected failure\n"),
                            err.getvalue())
            self.assertNotIn("cannot clean temporary", err.getvalue())
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(stat.S_IMODE(self.catalog.stat().st_mode), mode)
        finally:
            os.chmod(self.catalog, original_mode)

    def test_replacement_and_write_failure_remove_temporary_and_keep_original(self):
        from retrostation.catalog import main
        argv = ["retrostation.catalog", "--config", str(self.config), "--catalog", str(self.catalog),
                "add", *self.fields]
        for failure in ("replace", "fsync"):
            with self.subTest(failure=failure):
                before = self.snapshot()
                out, err = io.StringIO(), io.StringIO()
                with patch.object(sys, "argv", argv), patch("retrostation.catalog.os." + failure,
                    side_effect=OSError("injected failure")), redirect_stdout(out), redirect_stderr(err):
                    with self.assertRaises(SystemExit) as caught:
                        main()
                self.assertEqual((caught.exception.code, out.getvalue()), (2, ""))
                self.assertIn("error: Cannot update catalog: injected failure", err.getvalue())
                self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
