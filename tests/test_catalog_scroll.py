"""Visible catalog rows through the injected controller/window boundary."""

import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

from test_pygame_menu import FakeControllers, FakePygame

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class CatalogScrollTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.marker = self.folder / "runs.json"
        self.config = self.folder / "profiles.toml"
        self.catalog = self.folder / "catalog.toml"

    def fixture(self, systems, games):
        script = ("import json,sys; from pathlib import Path; "
                  f"Path({str(self.marker)!r}).write_text(json.dumps(sys.argv[1:])); sys.exit(7)")
        self.config.write_text("".join(
            f'[[systems]]\nid="s{i}"\nname="System {i}"\nemulator="Fixture"\n'
            f'command={json.dumps([sys.executable, "-c", script, "{game}"])}\n'
            for i in range(systems)), encoding="utf-8")
        self.files = [self.folder / f"fixture_{i}_{j}.bin"
                      for i in range(systems) for j in range(games if i == 0 else 1)]
        for path in self.files:
            path.write_bytes(b"synthetic")
        self.catalog.write_text("".join(
            f'[[games]]\nid="g{i}_{j}"\ntitle="Game {i}-{j}"\nsystem="s{i}"\n'
            f'path="fixture_{i}_{j}.bin"\n'
            for i in range(systems) for j in range(games if i == 0 else 1)), encoding="utf-8")
        self.before = tuple(path.read_bytes() for path in (self.config, self.catalog, *self.files))

    def window(self, *buttons):
        from retrostation.pygame_catalog_menu import run_catalog_window
        pygame = FakePygame()
        pygame.batches = [[SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=button)]
                          for button in buttons] + [[SimpleNamespace(type=pygame.QUIT)]]
        state = run_catalog_window(self.config, self.catalog, pygame, FakeControllers(pygame.calls))
        self.assertEqual(tuple(path.read_bytes() for path in (self.config, self.catalog, *self.files)), self.before)
        return state, pygame.screen.frames

    def test_short_lists_one_and_six_keep_all_rows_and_selection(self):
        for size in (1, 6):
            with self.subTest(size=size):
                self.fixture(size, size)
                state, frames = self.window(11, 12, 11)
                self.assertEqual((state.screen, state.system_index, state.game_index),
                                 ("games", 0 if size == 1 else 1, 0))
                selected_system = 0 if size == 1 else 1
                self.assertEqual(frames[0], tuple(
                    (">" if i == selected_system else " ") + f" System {i}" for i in range(size)))
                self.assertEqual(frames[1], ("> Game 0-0",) if size == 1 else ("> Game 1-0",))
                self.assertEqual(frames[2], frames[1])
                if size == 6:
                    _, game_frames = self.window(12, 11)
                    self.assertEqual(game_frames[1],
                                     ("  Game 0-0", "> Game 0-1", *[f"  Game 0-{i}" for i in range(2, 6)]))
                self.assertFalse(self.marker.exists())

    def test_seven_systems_scroll_both_directions_wrap_and_back_restores_system(self):
        self.fixture(8, 8)
        state, frames = self.window(*([11] * 7), 10, 12, 13, *([10] * 7), 11)
        self.assertEqual((state.screen, state.system_index), ("systems", 0))
        self.assertEqual(frames[5], tuple(
            (">" if i == 6 else " ") + f" System {i}" for i in range(1, 7)))
        self.assertEqual(frames[6], tuple(
            (">" if i == 7 else " ") + f" System {i}" for i in range(2, 8)))
        self.assertEqual(frames[7], frames[5])
        self.assertEqual(frames[8], ("> Game 6-0",))
        self.assertEqual(frames[9], frames[5])
        self.assertEqual(frames[-1], tuple(
            (">" if i == 0 else " ") + f" System {i}" for i in range(6)))
        self.assertTrue(all(len(frame) <= 6 for frame in frames))
        self.assertFalse(self.marker.exists())

    def test_seven_items_wrap_into_visible_window(self):
        self.fixture(7, 7)
        state, frames = self.window(10, 12, 10)
        self.assertEqual((state.system_index, state.game_index), (6, 0))
        self.assertEqual(frames[0], tuple(
            (">" if i == 6 else " ") + f" System {i}" for i in range(1, 7)))
        self.assertEqual(frames[1], ("> Game 6-0",))
        _, game_frames = self.window(12, 10)
        self.assertEqual(game_frames[1], tuple(
            (">" if i == 6 else " ") + f" Game 0-{i}" for i in range(1, 7)))
        self.assertFalse(self.marker.exists())

    def test_games_scroll_wrap_cancel_and_return_preserve_selection(self):
        self.fixture(7, 8)
        state, frames = self.window(12, *([11] * 7), 11, 10, 12, 13, 13, 12)
        self.assertEqual((state.screen, state.system_index, state.game_index, state.attempted),
                         ("games", 0, 0, False))
        last = tuple((">" if i == 7 else " ") + f" Game 0-{i}" for i in range(2, 8))
        self.assertEqual(frames[6], tuple(
            (">" if i == 6 else " ") + f" Game 0-{i}" for i in range(1, 7)))
        self.assertEqual(frames[7], last)  # crossing the sixth visible row
        self.assertEqual(frames[8], tuple((">" if i == 0 else " ") + f" Game 0-{i}" for i in range(6)))
        self.assertEqual(frames[9], last)  # up wraps from first to last
        self.assertEqual(frames[10], ("Launch Game 0-7 (System 0)? Saves may change.",
                                      "Press A to start; B to cancel."))
        self.assertEqual(frames[11], last)
        self.assertEqual(frames[12], ("> System 0", *[f"  System {i}" for i in range(1, 6)]))
        self.assertEqual(frames[13], ("> Game 0-0", *[f"  Game 0-{i}" for i in range(1, 6)]))
        self.assertFalse(self.marker.exists())

    def test_attempt_footer_fits_and_selected_game_launch_is_one_shot(self):
        self.fixture(7, 8)
        state, frames = self.window(12, *([11] * 7), 12, 12, 13, 11, 12, 12, 10)
        self.assertEqual((state.screen, state.game_index, state.attempted), ("games", 7, True))
        self.assertEqual(json.loads(self.marker.read_text(encoding="utf-8")),
                         [str((self.folder / "fixture_0_7.bin").resolve())])
        self.assertIn(("Running Game 0-7 (System 0); close the emulator to return.",), frames)
        self.assertIn(("Emulator exited with status 7", "Press B to return to games."), frames)
        footer = "One launch attempted; close the window."
        self.assertEqual(frames[11], tuple(
            (">" if i == 7 else " ") + f" Game 0-{i}" for i in range(2, 8)) + (footer,))
        self.assertEqual(frames[12], tuple(
            (">" if i == 0 else " ") + f" Game 0-{i}" for i in range(6)) + (footer,))
        self.assertEqual(frames[-1], frames[11])
        self.assertTrue(all(len(frame) <= 7 for frame in frames))
        self.assertEqual(sum("Running " in line for frame in frames for line in frame), 1)


if __name__ == "__main__":
    unittest.main()
