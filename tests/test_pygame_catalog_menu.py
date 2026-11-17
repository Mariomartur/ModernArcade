"""Public catalog-launch CLI and synthetic controller/window boundary."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from test_pygame_menu import FakePygame, FakeControllers

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class CatalogWindowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.marker = self.folder / "runs.json"
        script = ("import json, os, sys; from pathlib import Path; "
                  f"p=Path({str(self.marker)!r}); "
                  "p.write_text(json.dumps({'argv':sys.argv[1:], 'cwd':os.getcwd()})); sys.exit(7)")
        self.config = self.folder / "profiles.toml"
        self.config.write_text(
            '[[systems]]\nid="nes"\nname="NES"\nemulator="Fixture"\n'
            f'command={json.dumps([sys.executable, "-c", script, "{game}"])}\n'
            '[[systems]]\nid="unused"\nname="Unused"\nemulator="Fixture"\n'
            '[[systems]]\nid="nds"\nname="Nintendo DS"\nemulator="Fixture"\n'
            f'command={json.dumps([sys.executable, "-c", script, "{game}"])}\n', encoding="utf-8")
        self.catalog = self.folder / "catalog.toml"
        self.game = self.folder / "synthetic.bin"
        self.game.write_bytes(b"synthetic fixture")
        self.second = self.folder / "other.bin"
        self.second.write_bytes(b"synthetic fixture 2")
        self.catalog.write_text(
            '[[games]]\nid="one"\ntitle="First"\nsystem="nes"\npath="synthetic.bin"\n'
            '[[games]]\nid="two"\ntitle="Second"\nsystem="nes"\npath="other.bin"\n'
            '[[games]]\nid="three"\ntitle="Third"\nsystem="nds"\npath="synthetic.bin"\n', encoding="utf-8")

    def window(self, *buttons):
        from retrostation.pygame_catalog_menu import run_catalog_window
        pygame = FakePygame()
        pygame.batches = [[SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=button)]
                          for button in buttons] + [[SimpleNamespace(type=pygame.QUIT)]]
        state = run_catalog_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
        self.assertEqual(pygame.calls,
                         ["pygame.init", "controller.init", "controller.open", "caption",
                          "controller.close", "controller.quit", "pygame.quit"])
        return state, pygame.screen.frames

    def test_wrap_systems_games_back_and_cancel_without_consuming_attempt(self):
        from retrostation.pygame_catalog_menu import run_catalog_window
        p = FakePygame()
        p.batches = [[SimpleNamespace(type=p.CONTROLLERBUTTONDOWN, button=b)] for b in (
            p.CONTROLLER_BUTTON_DPAD_UP, p.CONTROLLER_BUTTON_A, p.CONTROLLER_BUTTON_B,
            p.CONTROLLER_BUTTON_DPAD_DOWN, p.CONTROLLER_BUTTON_A, p.CONTROLLER_BUTTON_DPAD_UP,
            p.CONTROLLER_BUTTON_A, p.CONTROLLER_BUTTON_B,
        )] + [[SimpleNamespace(type=p.QUIT)]]
        state = run_catalog_window(self.config, self.catalog, p, FakeControllers(p.calls))
        self.assertEqual((state.screen, state.system_index, state.game_index, state.attempted),
                         ("games", 0, 1, False))
        self.assertEqual(p.screen.frames, [
            ("  NES", "> Nintendo DS"),
            ("> Third",),
            ("  NES", "> Nintendo DS"),
            ("> NES", "  Nintendo DS"),
            ("> First", "  Second"),
            ("  First", "> Second"),
            ("Launch Second (NES)? Saves may change.", "Press A to start; B to cancel."),
            ("  First", "> Second"),
        ])
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.game.read_bytes(), b"synthetic fixture")

    def test_launch_resolved_catalog_game_status_and_one_attempt_after_browsing(self):
        p = FakePygame()
        p.batches = [[SimpleNamespace(type=p.CONTROLLERBUTTONDOWN, button=b)] for b in (
            p.CONTROLLER_BUTTON_A, p.CONTROLLER_BUTTON_DPAD_DOWN, p.CONTROLLER_BUTTON_A,
            p.CONTROLLER_BUTTON_A, p.CONTROLLER_BUTTON_B, p.CONTROLLER_BUTTON_B,
            p.CONTROLLER_BUTTON_DPAD_DOWN, p.CONTROLLER_BUTTON_A, p.CONTROLLER_BUTTON_A,
        )] + [[SimpleNamespace(type=p.QUIT)]]
        from retrostation.pygame_catalog_menu import run_catalog_window
        original = tuple(path.read_bytes() for path in (self.config, self.catalog, self.game, self.second))
        state = run_catalog_window(self.config, self.catalog, p, FakeControllers(p.calls))
        self.assertEqual((state.screen, state.attempted), ("games", True))
        self.assertEqual(json.loads(self.marker.read_text(encoding="utf-8")),
                         {"argv": [str(self.second.resolve())], "cwd": str(Path(sys.executable).resolve().parent)})
        self.assertIn(("Running Second (NES); close the emulator to return.",), p.screen.frames)
        self.assertIn(("Emulator exited with status 7", "Press B to return to games."), p.screen.frames)
        self.assertEqual(p.screen.frames[-1], ("> Third", "One launch attempted; close the window."))
        self.assertEqual(tuple(path.read_bytes() for path in (self.config, self.catalog, self.game, self.second)), original)

    def test_refused_attempt_keeps_data_and_cannot_be_retried(self):
        # An in-Git game is rejected by launch_game, not by the read-only catalog loader.
        project = self.folder / "project"
        project.mkdir()
        (project / ".git").mkdir()
        rejected = project / "game.bin"
        rejected.write_bytes(b"synthetic")
        self.catalog.write_text(self.catalog.read_text(encoding="utf-8").replace('path="synthetic.bin"',
                                f'path={json.dumps(str(rejected))}', 1), encoding="utf-8")
        before = tuple(path.read_bytes() for path in (self.config, self.catalog, rejected, self.second))
        state, frames = self.window(12, 12, 12, 13, 11, 12, 12, 13, 12, 12)
        self.assertTrue(state.attempted)
        self.assertEqual(state.screen, "games")
        self.assertIn(("Launch refused: Game must be outside a Git worktree", "Press B to return to games."), frames)
        self.assertNotIn("Launch Second (NES)? Saves may change.", (line for frame in frames for line in frame))
        self.assertFalse(self.marker.exists())
        self.assertEqual(tuple(path.read_bytes() for path in (self.config, self.catalog, rejected, self.second)), before)
        self.assertEqual(set(project.iterdir()), {project / ".git", rejected})

    def test_initial_list_and_invalid_catalog_before_window(self):
        from retrostation.pygame_catalog_menu import run_catalog_window
        from retrostation.profiles import ConfigError
        pygame = FakePygame()
        pygame.batches = [[], [SimpleNamespace(type=pygame.QUIT)]]
        state = run_catalog_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
        self.assertEqual((state.screen, state.system_index), ("systems", 0))
        self.assertEqual(pygame.screen.frames, [( "> NES", "  Nintendo DS")])
        self.catalog.write_text('[[games]]\nid="bad"\ntitle="Bad"\nsystem="unknown"\npath="x"\n',
                                encoding="utf-8")
        original = self.catalog.read_bytes()
        unused = FakePygame()
        with self.assertRaisesRegex(ConfigError, "Unknown system: unknown"):
            run_catalog_window(self.config, self.catalog, unused, FakeControllers(unused.calls))
        self.assertEqual(unused.calls, [])
        self.assertFalse(self.marker.exists())
        self.assertEqual(self.catalog.read_bytes(), original)

    def test_empty_catalog_rejected_before_window(self):
        from retrostation.pygame_catalog_menu import run_catalog_window
        from retrostation.profiles import ConfigError
        self.catalog.write_text("", encoding="utf-8")
        original = self.catalog.read_bytes()
        pygame = FakePygame()
        with self.assertRaisesRegex(ConfigError, "Catalog requires at least one game"):
            run_catalog_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
        self.assertEqual(pygame.calls, [])
        self.assertEqual(self.catalog.read_bytes(), original)

    def test_cli_mutually_exclusive_flags_and_missing_dependency(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        base = [sys.executable, "-S", "-B", "-m", "retrostation.pygame_launch_menu", "--window"]
        cases = (
            (("--config", str(self.config), "--catalog", str(self.catalog), "--confirm", "--game", str(self.game)),
             "--game and --catalog are mutually exclusive"),
            (("--config", str(self.config), "--catalog", str(self.catalog)),
             "--config, --catalog and --confirm are required exactly once for catalog launch mode"),
            (("--config", str(self.config), "--catalog", str(self.catalog), "--catalog", str(self.catalog), "--confirm"),
             "--config, --catalog and --confirm are required exactly once for catalog launch mode"),
            (("--config", str(self.config), "--catalog", str(self.catalog), "--confirm"),
             "pygame-ce is required for --window; use the authorized isolated environment"),
        )
        original = tuple(path.read_bytes() for path in (self.config, self.catalog, self.game))
        for flags, message in cases:
            with self.subTest(flags=flags):
                result = subprocess.run([*base, *flags], cwd=self.folder, env=env,
                                        capture_output=True, text=True, check=False)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertTrue(result.stderr.endswith(f"error: {message}\n"), result.stderr)
                self.assertFalse(self.marker.exists())
                self.assertEqual(tuple(path.read_bytes() for path in (self.config, self.catalog, self.game)), original)
        game_free = subprocess.run([sys.executable, "-S", "-B", "-m", "retrostation.pygame_menu",
                                    "--window", "--catalog", str(self.catalog)], cwd=self.folder, env=env,
                                   capture_output=True, text=True, check=False)
        self.assertEqual((game_free.returncode, game_free.stdout), (2, ""))
        self.assertIn("unrecognized arguments: --catalog", game_free.stderr)


if __name__ == "__main__":
    unittest.main()
