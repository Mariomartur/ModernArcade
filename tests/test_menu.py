"""Exercise the synthetic menu without pygame-ce, a controller, or games."""

import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]


def simulate(*actions: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, "-B", "-m", "retrostation.menu", "--simulate", *actions],
        cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
    )


class MenuTests(unittest.TestCase):
    def test_simulated_navigation_selection_and_return(self):
        result = simulate("down", "select", "back")
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(
            result.stdout,
            "> NES\n  Nintendo DS\n---\n"
            "  NES\n> Nintendo DS\n---\n"
            "Preview: Nintendo DS (synthetic; no emulator started)\n---\n"
            "  NES\n> Nintendo DS\n",
        )

    def test_simulated_navigation_wraps_and_rejects_invalid_actions(self):
        wrapped = simulate("up")
        self.assertEqual((wrapped.returncode, wrapped.stderr), (0, ""))
        self.assertEqual(wrapped.stdout, "> NES\n  Nintendo DS\n---\n  NES\n> Nintendo DS\n")

        invalid = simulate("launch")
        self.assertEqual(invalid.returncode, 2)
        self.assertEqual(invalid.stdout, "")
        self.assertIn("invalid choice: 'launch'", invalid.stderr)

    def test_repeated_simulation_option_is_rejected_instead_of_dropping_actions(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        result = subprocess.run(
            [sys.executable, "-B", "-m", "retrostation.menu", "--simulate", "down",
             "--simulate", "up"],
            cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("--simulate must be provided exactly once", result.stderr)

    def test_candidate_controller_button_mapping(self):
        sys.path.insert(0, str(ROOT / "src"))
        try:
            from retrostation.pygame_input import controller_action
        finally:
            sys.path.pop(0)

        pygame = SimpleNamespace(
            CONTROLLERBUTTONDOWN=1, CONTROLLERBUTTONUP=2,
            CONTROLLER_BUTTON_DPAD_UP=10, CONTROLLER_BUTTON_DPAD_DOWN=11,
            CONTROLLER_BUTTON_A=12, CONTROLLER_BUTTON_B=13,
        )
        for button, action in ((10, "up"), (11, "down"), (12, "select"), (13, "back")):
            with self.subTest(button=button):
                self.assertEqual(controller_action(SimpleNamespace(type=1, button=button), pygame), action)
        self.assertIsNone(controller_action(SimpleNamespace(type=2, button=12), pygame))
        self.assertIsNone(controller_action(SimpleNamespace(type=1, button=20), pygame))


if __name__ == "__main__":
    unittest.main()
