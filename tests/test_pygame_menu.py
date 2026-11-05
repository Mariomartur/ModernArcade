"""Exercise a game-free window through a fake pygame-ce boundary."""

import os
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class FakeScreen:
    def __init__(self):
        self.frames = []
        self.current = []

    def fill(self, color):
        self.current = []

    def blit(self, text, position):
        self.current.append(text)


class FakePygame:
    QUIT = 1
    CONTROLLERBUTTONDOWN = 2
    CONTROLLER_BUTTON_DPAD_UP = 10
    CONTROLLER_BUTTON_DPAD_DOWN = 11
    CONTROLLER_BUTTON_A = 12
    CONTROLLER_BUTTON_B = 13

    def __init__(self):
        self.screen = FakeScreen()
        self.calls = []
        self.batches = [
            [SimpleNamespace(type=self.CONTROLLERBUTTONDOWN, button=self.CONTROLLER_BUTTON_DPAD_DOWN)],
            [SimpleNamespace(type=self.CONTROLLERBUTTONDOWN, button=self.CONTROLLER_BUTTON_A)],
            [SimpleNamespace(type=self.CONTROLLERBUTTONDOWN, button=self.CONTROLLER_BUTTON_B)],
            [SimpleNamespace(type=self.QUIT)],
        ]
        self.display = SimpleNamespace(
            set_mode=lambda size: self.screen,
            set_caption=lambda title: self.calls.append("caption"),
            flip=self.flip,
        )
        self.font = SimpleNamespace(Font=lambda family, size: SimpleNamespace(
            render=lambda text, antialias, color: text,
        ))
        self.event = SimpleNamespace(get=lambda: self.batches.pop(0))
        self.time = SimpleNamespace(Clock=lambda: SimpleNamespace(tick=lambda fps: None))

    def init(self):
        self.calls.append("pygame.init")

    def quit(self):
        self.calls.append("pygame.quit")

    def flip(self):
        self.screen.frames.append(tuple(self.screen.current))


class FakeControllers:
    def __init__(self, calls):
        self.calls = calls

    def init(self):
        self.calls.append("controller.init")

    def get_count(self):
        return 1

    def is_controller(self, index):
        return index == 0

    def Controller(self, index):
        self.calls.append("controller.open")
        return SimpleNamespace(quit=lambda: self.calls.append("controller.close"))

    def quit(self):
        self.calls.append("controller.quit")


class PygameMenuTests(unittest.TestCase):
    def test_window_navigates_preview_returns_to_menu_and_closes(self):
        from retrostation.pygame_menu import run_window

        pygame = FakePygame()
        state = run_window(pygame, FakeControllers(pygame.calls))
        self.assertEqual((state.selected, state.showing_preview), (1, False))
        self.assertEqual(pygame.screen.frames, [
            ("  NES", "> Nintendo DS"),
            ("Preview: Nintendo DS (synthetic; no emulator started)",),
            ("  NES", "> Nintendo DS"),
        ])
        self.assertEqual(pygame.calls,
                         ["pygame.init", "controller.init", "controller.open", "caption",
                          "controller.close", "controller.quit", "pygame.quit"])

    def test_missing_dependency_refuses_window_without_other_effects(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [sys.executable, "-S", "-B", "-m", "retrostation.pygame_menu", "--window"],
            cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("pygame-ce is required for --window", result.stderr)

    def test_rejected_window_arguments_leave_synthetic_data_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "profiles.toml"
            data.write_bytes(b'[[systems]]\nid="nes"\nname="NES"\nemulator="Fixture"\n')
            original_hash = hashlib.sha256(data.read_bytes()).digest()
            environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
            cases = (
                ((), "--window must be provided exactly once"),
                (("--window", "--window"), "--window must be provided exactly once"),
                (("--window", "--garbage"), "unrecognized arguments: --garbage"),
            )
            for arguments, diagnostic in cases:
                with self.subTest(arguments=arguments):
                    result = subprocess.run(
                        [sys.executable, "-S", "-B", "-m", "retrostation.pygame_menu", *arguments],
                        cwd=directory, env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertIn(diagnostic, result.stderr)
                    self.assertEqual(hashlib.sha256(data.read_bytes()).digest(), original_hash)


if __name__ == "__main__":
    unittest.main()
