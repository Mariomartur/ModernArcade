"""Read-only catalog browser: public CLI and injected window boundary."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

from test_pygame_menu import FakeControllers, FakePygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.config = self.folder / "profiles.toml"
        self.catalog = self.folder / "catalog.toml"
        self.game = self.folder / "synthetic.bin"
        self.marker = self.folder / "executed"
        self.game.write_bytes(b"synthetic, not a ROM")
        script = f"from pathlib import Path; Path({str(self.marker)!r}).write_text('executed')"
        self.command = [sys.executable, "-c", script, "{game}"]
        self.config.write_text("".join(
            f'[[systems]]\nid="s{i}"\nname="System {i}"\nemulator="Fixture"\n'
            + (f'command={json.dumps(self.command)}\n' if i != 1 else "")
            for i in range(8)), encoding="utf-8")
        self.catalog.write_text("".join(
            f'[[games]]\nid="g{i}_{j}"\ntitle="Game {i}-{j}"\nsystem="s{i}"\n'
            f'path="{"synthetic.bin" if j == 0 else "absent.bin"}"\n'
            for i in range(8) for j in range(8 if i == 0 else 1)), encoding="utf-8")
        self.before = {p.name: p.read_bytes() for p in (self.config, self.catalog, self.game)}

    def unchanged(self):
        self.assertEqual({p.name: p.read_bytes() for p in (self.config, self.catalog, self.game)}, self.before)
        self.assertEqual(set(self.folder.iterdir()), {self.config, self.catalog, self.game})

    def window(self, *buttons, pygame=None):
        from retrostation.pygame_catalog_browser import run_browser_window
        pygame = pygame or FakePygame()
        pygame.font = SimpleNamespace(Font=lambda family, size: SimpleNamespace(
            render=lambda text, antialias, color: text, size=lambda text: (len(text) * 4, 36)))
        pygame.batches = [[SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=b)]
                          for b in buttons] + [[SimpleNamespace(type=pygame.QUIT)]]
        state = run_browser_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
        self.unchanged()
        self.assertEqual(pygame.calls, ["pygame.init", "controller.init", "controller.open", "caption",
                                        "controller.close", "controller.quit", "pygame.quit"])
        return state, pygame.screen.frames

    def test_wrap_scroll_and_return_to_same_visible_game_without_launch(self):
        state, frames = self.window(10, 12, 13, 11, 12, *([11] * 7), 11, 10, 12, 12, 11, 10, 13, 13, 12)
        self.assertEqual((state.screen, state.system_index, state.game_index), ("games", 0, 0))
        self.assertEqual(frames[0], tuple((">" if i == 7 else " ") + f" System {i}" for i in range(2, 8)))
        self.assertEqual(frames[1], ("> Game 7-0",))
        self.assertEqual(frames[3], tuple((">" if i == 0 else " ") + f" System {i}" for i in range(6)))
        self.assertEqual(frames[11], tuple((">" if i == 7 else " ") + f" Game 0-{i}" for i in range(2, 8)))
        self.assertEqual(frames[12], tuple((">" if i == 0 else " ") + f" Game 0-{i}" for i in range(6)))
        self.assertEqual(frames[13], frames[11])
        preview = frames[14]
        self.assertIn("PREVIEW ONLY - NO LAUNCH", preview)
        self.assertIn("Game 0-7 (System 0)", preview)
        self.assertEqual("".join(preview[2:]), json.dumps(self.command[:-1] + [str(self.folder / "absent.bin")]))
        self.assertEqual(frames[15], preview)  # A cannot confirm/launch.
        self.assertEqual(frames[18], frames[11])  # B restores the selected visible game.
        self.assertEqual(frames[19], frames[3])
        self.assertEqual(frames[20], ("> Game 0-0", *[f"  Game 0-{i}" for i in range(1, 6)]))

    def test_missing_command_is_controlled_preview_and_b_returns(self):
        state, frames = self.window(11, 12, 12, 12, 13)
        self.assertEqual((state.screen, state.system_index, state.game_index), ("games", 1, 0))
        self.assertEqual(frames[3], frames[2])
        self.assertIn("PREVIEW ONLY - NO LAUNCH", frames[2])
        self.assertIn("Game 1-0 (System 1)", frames[2])
        self.assertIn("Preview unavailable: No launch command for system: s1", frames[2])
        self.assertEqual(frames[-1], ("> Game 1-0",))

    def test_long_json_wrap_uses_font_width_and_scrolls_all_content(self):
        from retrostation.pygame_catalog_browser import run_browser_window
        long_token = "abcdefgh" * 170
        self.command.insert(1, long_token)
        self.config.write_text(self.config.read_text(encoding="utf-8").replace(
            json.dumps([sys.executable, "-c", self.command[3], "{game}"]), json.dumps(self.command)), encoding="utf-8")
        self.before["profiles.toml"] = self.config.read_bytes()
        pygame = FakePygame()
        pygame.font = SimpleNamespace(Font=lambda family, size: SimpleNamespace(
            render=lambda text, antialias, color: text,
            size=lambda text: (len(text) * 9, 36)))
        pygame.batches = [[SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=b)]
                          for b in (12, 12, *([11] * 60), 13)] + [[SimpleNamespace(type=pygame.QUIT)]]
        state = run_browser_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
        self.unchanged()
        frames = pygame.screen.frames
        self.assertEqual((state.screen, state.game_index), ("games", 0))
        previews = frames[1:62]
        self.assertTrue(all("PREVIEW ONLY - NO LAUNCH" in frame and "Game 0-0 (System 0)" in frame
                            for frame in previews))
        self.assertTrue(all(len(line) * 9 <= 592 for frame in previews for line in frame[2:]))
        expected = json.dumps(self.command[:-1] + [str(self.game)])
        wrapped = [line for frame in previews for line in frame if "abcdefgh" in line]
        self.assertTrue(wrapped)
        # Every JSON segment is accessible by D-pad, including the last argument after the long token.
        self.assertIn(expected[:40], "".join(previews[0][2:]))
        self.assertTrue(any(json.dumps(str(self.game))[1:-1] in "".join(frame[2:]) for frame in previews))
        self.assertEqual(frames[-1][0], "> Game 0-0")

    def test_validation_before_pygame_and_cleanup_on_exception(self):
        from retrostation.pygame_catalog_browser import run_browser_window
        from retrostation.profiles import ConfigError
        for text, error in (("", "Catalog requires at least one game"),
                            ('[[games]]\nid="x"\ntitle="X"\nsystem="bad"\npath="x"\n', "Unknown system: bad")):
            with self.subTest(error=error):
                self.catalog.write_text(text, encoding="utf-8")
                pygame = FakePygame()
                with self.assertRaisesRegex(ConfigError, error):
                    run_browser_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
                self.assertEqual(pygame.calls, [])
        self.catalog.write_bytes(self.before["catalog.toml"])
        pygame = FakePygame()
        pygame.event = SimpleNamespace(get=lambda: (_ for _ in ()).throw(RuntimeError("synthetic failure")))
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            run_browser_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
        self.assertEqual(pygame.calls[-3:], ["controller.close", "controller.quit", "pygame.quit"])
        self.unchanged()

    def test_cli_rejects_flags_invalid_data_and_missing_pygame(self):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        base = [sys.executable, "-S", "-B", "-m", "retrostation.pygame_catalog_browser"]
        valid = ("--window", "--config", str(self.config), "--catalog", str(self.catalog))
        cases = (((), "--window, --config and --catalog must be provided exactly once"),
                 (("--window", "--config", str(self.config)), "--window, --config and --catalog must be provided exactly once"),
                 (valid + ("--window",), "--window, --config and --catalog must be provided exactly once"),
                 (valid + ("--config", str(self.config)), "--window, --config and --catalog must be provided exactly once"),
                 (valid + ("--catalog", str(self.catalog)), "--window, --config and --catalog must be provided exactly once"),
                 (valid + ("--game", str(self.game)), "unrecognized arguments: --game"),
                 (valid + ("--confirm",), "unrecognized arguments: --confirm"),
                 (("--window", "--config", str(self.config), "--catalog", str(self.folder / "missing.toml")), "Cannot read catalog:"),
                 (valid, "pygame-ce is required for --window; use the authorized isolated environment"))
        for flags, message in cases:
            with self.subTest(flags=flags):
                result = subprocess.run([*base, *flags], cwd=self.folder, env=env,
                                        capture_output=True, text=True, check=False)
                self.assertEqual((result.returncode, result.stdout), (2, ""))
                self.assertIn("error: " + message, result.stderr)
                self.unchanged()


if __name__ == "__main__":
    unittest.main()
