"""Exercise a game-free window through a fake pygame-ce boundary."""

import os
import hashlib
import json
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
    def _synthetic_profile(self, folder, marker):
        config = folder / "profiles.toml"
        script = (
            "from pathlib import Path; import sys; "
            f"Path({str(marker)!r}).write_text('started'); sys.exit(7)"
        )
        config.write_text(
            '[[systems]]\nid = "nds"\nname = "Nintendo DS"\nemulator = "Synthetic"\n'
            f'command = {json.dumps([sys.executable, "-c", script, "{game}"])}\n',
            encoding="utf-8",
        )
        return config

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

    def test_launch_confirmation_can_be_cancelled_without_starting_process(self):
        from retrostation.pygame_menu import run_window

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            marker = folder / "started"
            game = folder / "synthetic.bin"
            game.write_bytes(b"not a real game")
            config = self._synthetic_profile(folder, marker)
            original = (config.read_bytes(), game.read_bytes())
            pygame = FakePygame()
            pygame.batches = [
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A)],
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_B)],
                [SimpleNamespace(type=pygame.QUIT)],
            ]
            state = run_window(pygame, FakeControllers(pygame.calls), launch_config=config, game=str(game))
            self.assertEqual((state.screen, state.selected), ("menu", 0))
            self.assertEqual(pygame.screen.frames, [
                ("Launch Nintendo DS? Saves may change.", "Press A to start; B to cancel."),
                ("> Nintendo DS",),
            ])
            self.assertFalse(marker.exists())
            self.assertEqual((config.read_bytes(), game.read_bytes()), original)

    def test_confirmed_synthetic_process_returns_to_menu_with_status(self):
        from retrostation.pygame_menu import run_window

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            marker = folder / "started"
            game = folder / "synthetic.bin"
            game.write_bytes(b"synthetic game fixture")
            config = self._synthetic_profile(folder, marker)
            original = (config.read_bytes(), game.read_bytes())
            pygame = FakePygame()
            pygame.batches = [
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A)],
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A)],
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_B)],
                [SimpleNamespace(type=pygame.QUIT)],
            ]
            state = run_window(pygame, FakeControllers(pygame.calls), launch_config=config, game=str(game))
            self.assertEqual(state.screen, "menu")
            self.assertEqual(marker.read_text(encoding="utf-8"), "started")
            self.assertEqual((config.read_bytes(), game.read_bytes()), original)
            self.assertEqual(pygame.screen.frames, [
                ("Launch Nintendo DS? Saves may change.", "Press A to start; B to cancel."),
                ("Running Nintendo DS; close the emulator to return.",),
                ("Emulator exited with status 7", "Press B to return to the menu."),
                ("> Nintendo DS", "One launch completed; close the window."),
            ])

    def test_window_allows_only_one_confirmed_launch_per_session(self):
        from retrostation.pygame_menu import run_window

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            marker = folder / "runs"
            game = folder / "synthetic.bin"
            game.write_bytes(b"synthetic fixture, not a game")
            script = (
                "from pathlib import Path; "
                f"p=Path({str(marker)!r}); p.write_text((p.read_text() if p.exists() else '') + 'x')"
            )
            config = folder / "profiles.toml"
            config.write_text(
                '[[systems]]\nid="nds"\nname="Nintendo DS"\nemulator="Fixture"\n'
                f'command={json.dumps([sys.executable, "-c", script, "{game}"])}\n', encoding="utf-8",
            )
            original = (config.read_bytes(), game.read_bytes())
            pygame = FakePygame()
            pygame.batches = [
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=button)]
                for button in (pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_A,
                               pygame.CONTROLLER_BUTTON_B, pygame.CONTROLLER_BUTTON_A,
                               pygame.CONTROLLER_BUTTON_A)
            ] + [[SimpleNamespace(type=pygame.QUIT)]]
            state = run_window(pygame, FakeControllers(pygame.calls),
                               launch_config=config, game=str(game))
            self.assertEqual(marker.read_text(encoding="utf-8"), "x")
            self.assertEqual((state.screen, state.selected), ("menu", 0))
            self.assertIn("One launch completed; close the window.", pygame.screen.frames[-1])
            self.assertEqual((config.read_bytes(), game.read_bytes()), original)

    def test_refused_attempt_cannot_be_reconfirmed_in_same_window(self):
        from retrostation.pygame_menu import run_window

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            project = folder / "repository"
            project.mkdir()
            self.assertEqual(subprocess.run(["git", "init", "-q"], cwd=project,
                                            capture_output=True, check=False).returncode, 0)
            game = project / "synthetic.bin"
            game.write_bytes(b"synthetic fixture")
            marker = folder / "started"
            config = self._synthetic_profile(folder, marker)
            original = (config.read_bytes(), game.read_bytes())
            pygame = FakePygame()
            pygame.batches = [
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=button)]
                for button in (pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_A,
                               pygame.CONTROLLER_BUTTON_B, pygame.CONTROLLER_BUTTON_A,
                               pygame.CONTROLLER_BUTTON_A)
            ] + [[SimpleNamespace(type=pygame.QUIT)]]
            state = run_window(pygame, FakeControllers(pygame.calls),
                               launch_config=config, game=str(game))
            self.assertEqual((state.screen, state.launched), ("menu", True))
            self.assertIn("Launch refused: Game must be outside a Git worktree",
                          pygame.screen.frames[2][0])
            self.assertIn("One launch completed; close the window.", pygame.screen.frames[-1])
            self.assertFalse(marker.exists())
            self.assertEqual((config.read_bytes(), game.read_bytes()), original)

    def test_rejected_synthetic_game_stays_unchanged_and_reports_error(self):
        from retrostation.pygame_menu import run_window

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            project = folder / "repository"
            project.mkdir()
            self.assertEqual(subprocess.run(["git", "init", "-q"], cwd=project,
                                            capture_output=True, check=False).returncode, 0)
            marker = folder / "started"
            game = project / "synthetic.bin"
            game.write_bytes(b"synthetic fixture")
            config = self._synthetic_profile(folder, marker)
            original = (config.read_bytes(), game.read_bytes())
            pygame = FakePygame()
            pygame.batches = [
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A)],
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A)],
                [SimpleNamespace(type=pygame.QUIT)],
            ]
            state = run_window(pygame, FakeControllers(pygame.calls), launch_config=config, game=str(game))
            self.assertEqual(state.screen, "result")
            self.assertIn("Game must be outside a Git worktree", pygame.screen.frames[-1][0])
            self.assertFalse(marker.exists())
            self.assertEqual((config.read_bytes(), game.read_bytes()), original)

    def test_launch_rejects_executable_inside_git_without_changing_data(self):
        from retrostation.pygame_menu import run_window

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            project = folder / "repository"
            project.mkdir()
            self.assertEqual(subprocess.run(["git", "init", "-q"], cwd=project,
                                            capture_output=True, check=False).returncode, 0)
            executable = project / "synthetic-emulator"
            executable.write_bytes(b"not an executable")
            game = folder / "synthetic.bin"
            game.write_bytes(b"not a game")
            config = folder / "profiles.toml"
            config.write_text(
                '[[systems]]\nid = "nds"\nname = "Nintendo DS"\nemulator = "Fixture"\n'
                f'command = {json.dumps([str(executable), "{game}"])}\n', encoding="utf-8",
            )
            original = tuple(path.read_bytes() for path in (config, game, executable))
            pygame = FakePygame()
            pygame.batches = [
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A)],
                [SimpleNamespace(type=pygame.CONTROLLERBUTTONDOWN, button=pygame.CONTROLLER_BUTTON_A)],
                [SimpleNamespace(type=pygame.QUIT)],
            ]
            state = run_window(pygame, FakeControllers(pygame.calls),
                               launch_config=config, game=str(game))
            self.assertEqual(state.screen, "result")
            self.assertEqual(pygame.screen.frames[-1][0],
                             "Launch refused: Emulator executable must be outside a Git worktree")
            self.assertEqual(tuple(path.read_bytes() for path in (config, game, executable)), original)

    def test_launch_mode_requires_explicit_matching_options(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            game = folder / "synthetic.bin"
            game.write_bytes(b"synthetic fixture")
            config = self._synthetic_profile(folder, folder / "started")
            original = (config.read_bytes(), game.read_bytes())
            for options in (
                ("--confirm",),
                ("--config", str(config), "--game", str(game)),
                ("--config", str(config), "--config", str(config), "--game", str(game), "--confirm"),
            ):
                with self.subTest(options=options):
                    result = subprocess.run(
                        [sys.executable, "-S", "-B", "-m", "retrostation.pygame_launch_menu", "--window", *options],
                        cwd=directory, env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual((result.returncode, result.stdout), (2, ""))
                    self.assertIn("--config, --game and --confirm", result.stderr)
                    self.assertEqual((config.read_bytes(), game.read_bytes()), original)

            game_free = subprocess.run(
                [sys.executable, "-S", "-B", "-m", "retrostation.pygame_menu", "--window",
                 "--config", str(config), "--game", str(game), "--confirm"],
                cwd=directory, env=environment, capture_output=True, text=True, check=False,
            )
            self.assertEqual((game_free.returncode, game_free.stdout), (2, ""))
            self.assertIn("unrecognized arguments", game_free.stderr)
            self.assertFalse((folder / "started").exists())

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
