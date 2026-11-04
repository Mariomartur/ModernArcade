"""Check real-process launch boundaries using only synthetic games and Python."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def run_cli(config: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, "-B", "-m", "retrostation", "--config", str(config), "launch", *arguments],
        env=environment, cwd=config.parent, capture_output=True, text=True, check=False,
    )


def write_profile(folder: Path, executable: str, script: str) -> Path:
    config = folder / "profiles.toml"
    config.write_text(
        '[[systems]]\nid = "nds"\nname = "Nintendo DS"\nemulator = "Synthetic"\n'
        f'command = {json.dumps([executable, "-c", script, "{game}"])}\n', encoding="utf-8",
    )
    return config


class LaunchCommandTests(unittest.TestCase):
    def test_game_placeholder_cannot_select_the_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            game = folder / "synthetic.nds"
            marker = folder / "game-was-executed"
            if os.name == "nt":
                game.write_bytes(b"synthetic fixture, not a real game")
            else:
                game.write_text(
                    f"#!{sys.executable}\nfrom pathlib import Path\n"
                    f"Path({str(marker)!r}).write_text('executed')\n", encoding="utf-8",
                )
                game.chmod(0o755)
            config = folder / "profiles.toml"
            config.write_text(
                '[[systems]]\nid = "nds"\nname = "Nintendo DS"\n'
                'emulator = "Fixture"\ncommand = ["{game}"]\n', encoding="utf-8",
            )
            original = (config.read_bytes(), game.read_bytes())

            result = run_cli(config, "--system", "nds", "--game", str(game), "--confirm")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("Invalid command at system entry 1", result.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual((config.read_bytes(), game.read_bytes()), original)

    def test_requires_confirmation_then_runs_selected_synthetic_game(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            game = folder / "test game.nds"
            marker = folder / "emulator-result.txt"
            game.write_bytes(b"synthetic fixture, not a ROM")
            script = (
                "from pathlib import Path; import sys; "
                f"Path({str(marker)!r}).write_text(sys.argv[1] + '|' + str(Path.cwd())); "
                "print('synthetic emulator finished')"
            )
            config = write_profile(folder, sys.executable, script)
            original_config = config.read_bytes()
            original_game = game.read_bytes()

            rejected = run_cli(config, "--system", "nds", "--game", str(game))
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertEqual(rejected.stdout, "")
            self.assertIn("--confirm", rejected.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual((config.read_bytes(), game.read_bytes()), (original_config, original_game))

            launched = run_cli(config, "--system", "nds", "--game", str(game), "--confirm")
            self.assertEqual(launched.returncode, 0, launched.stderr)
            self.assertEqual(launched.stdout, "synthetic emulator finished\n")
            self.assertEqual(launched.stderr, "")
            self.assertEqual(marker.read_text(), str(game.resolve()) + "|" + str(Path(sys.executable).resolve().parent))
            self.assertEqual((config.read_bytes(), game.read_bytes()), (original_config, original_game))

    def test_rejects_game_inside_git_worktree_without_starting_emulator(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            project = folder / "repository"
            project.mkdir()
            initialized = subprocess.run(["git", "init", "-q"], cwd=project, capture_output=True, check=False)
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            game = project / "synthetic.nds"
            game.write_bytes(b"synthetic fixture")
            marker = folder / "started"
            script = f"from pathlib import Path; Path({str(marker)!r}).write_text('started')"
            config = write_profile(folder, sys.executable, script)
            original = game.read_bytes()

            result = run_cli(config, "--system", "nds", "--game", str(game), "--confirm")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("Game must be outside a Git worktree", result.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual(game.read_bytes(), original)

            config_in_project = write_profile(project, sys.executable, script)
            game_outside = folder / "outside.nds"
            game_outside.write_bytes(b"another synthetic fixture")
            original_config = config_in_project.read_bytes()
            rejected_config = run_cli(config_in_project, "--system", "nds", "--game", str(game_outside), "--confirm")
            self.assertEqual(rejected_config.returncode, 2, rejected_config.stderr)
            self.assertEqual(rejected_config.stdout, "")
            self.assertIn("Launch config must be outside a Git worktree", rejected_config.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual(config_in_project.read_bytes(), original_config)
            self.assertEqual(game_outside.read_bytes(), b"another synthetic fixture")

    def test_propagates_synthetic_emulator_failure_without_touching_game(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            game = folder / "synthetic.nds"
            game.write_bytes(b"synthetic data")
            config = write_profile(folder, sys.executable, "import sys; print('synthetic failure', file=sys.stderr); sys.exit(7)")
            contents = (config.read_bytes(), game.read_bytes())

            result = run_cli(config, "--system", "nds", "--game", str(game), "--confirm")
            self.assertEqual((result.returncode, result.stdout, result.stderr), (7, "", "synthetic failure\n"))
            self.assertEqual((config.read_bytes(), game.read_bytes()), contents)

    def test_missing_executable_rejects_without_touching_game(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            game = folder / "synthetic.nds"
            game.write_bytes(b"synthetic data")
            config = write_profile(folder, str(folder / "missing-emulator"), "unused")
            contents = (config.read_bytes(), game.read_bytes())

            result = run_cli(config, "--system", "nds", "--game", str(game), "--confirm")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("Emulator executable must be an absolute existing file", result.stderr)
            self.assertEqual((config.read_bytes(), game.read_bytes()), contents)


if __name__ == "__main__":
    unittest.main()
