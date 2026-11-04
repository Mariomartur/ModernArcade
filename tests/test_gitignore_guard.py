"""Exercise repository safeguards using synthetic, non-game data only."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GitignoreGuardTests(unittest.TestCase):
    def test_loose_ds_image_is_ignored_without_modifying_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copyfile(ROOT / ".gitignore", root / ".gitignore")
            game = root / "example.nds"
            game.write_bytes(b"synthetic fixture, not a game")
            original = hashlib.sha256(game.read_bytes()).digest()
            environment = dict(os.environ, HOME=directory, TMPDIR=directory)

            def git(*arguments):
                return subprocess.run(
                    ["git", *arguments], cwd=root, env=environment,
                    capture_output=True, text=True, check=False,
                )

            self.assertEqual(git("init", "-q").returncode, 0)
            ignored = git("check-ignore", "-v", "--", game.name)
            self.assertEqual(ignored.returncode, 0, ignored.stderr)
            self.assertIn(f"*.nds\t{game.name}", ignored.stdout)
            self.assertNotIn(game.name, git("status", "--short").stdout)
            rejected = git("add", "--", game.name)
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            self.assertIn("ignored", rejected.stderr)
            self.assertEqual(git("ls-files", "--", "*.nds").stdout, "")
            self.assertEqual(hashlib.sha256(game.read_bytes()).digest(), original)
            for path in ("README.md", "src/retrostation/__main__.py", "tests/test_cli.py"):
                self.assertEqual(git("check-ignore", "-q", "--no-index", "--", path).returncode, 1)


if __name__ == "__main__":
    unittest.main()
