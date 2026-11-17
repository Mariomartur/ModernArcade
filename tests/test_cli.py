"""Exercise the user-facing RetroStation CLI without installed emulators."""

import os
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SystemsCommandTests(unittest.TestCase):
    def test_lists_multiple_configured_systems_without_changing_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            contents = (
                '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\n'
                '\n[[systems]]\nid = "gamecube"\nname = "GameCube"\nemulator = "Dolphin"\n'
            )
            config.write_text(contents, encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            result = subprocess.run(
                [sys.executable, "-B", "-m", "retrostation", "--config", str(config), "systems"],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "nes\tNES\tRetroArch\ngamecube\tGameCube\tDolphin\n")
            self.assertEqual(result.stderr, "")
            self.assertEqual(config.read_text(encoding="utf-8"), contents)


class CliContractTests(unittest.TestCase):
    def test_non_utf8_profiles_report_config_errors_without_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            config = folder / "profiles.toml"
            game = folder / "synthetic-game.bin"
            game_contents = b"synthetic fixture; never launch"
            game.write_bytes(game_contents)
            contents = b'[[systems]]\nid = "nes"\nname = "\xff"\nemulator = "Fixture"\n'
            try:
                contents.decode("utf-8")
            except UnicodeDecodeError as error:
                diagnostic = f"Cannot read profiles: {error}"
            environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
                               PYTHONDONTWRITEBYTECODE="1", COLUMNS="80")
            cases = (
                ("retrostation", ("systems",)),
                ("retrostation", ("preview", "--system", "nes", "--game", str(game))),
                ("retrostation", ("launch", "--system", "nes", "--game", str(game), "--confirm")),
                ("retrostation.pygame_launch_menu",
                 ("--window", "--game", str(game), "--confirm")),
            )
            for module, arguments in cases:
                with self.subTest(module=module, arguments=arguments):
                    command = [sys.executable, "-B", "-m", module,
                               "--config", str(config), *arguments]
                    config.write_bytes(b"[")
                    malformed = subprocess.run(
                        command, cwd=directory, env=environment,
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual((malformed.returncode, malformed.stdout), (2, ""))
                    self.assertIn("error: Cannot read profiles:", malformed.stderr)
                    usage = malformed.stderr.partition("error: ")[0]
                    config.write_bytes(contents)
                    result = subprocess.run(
                        command, cwd=directory, env=environment,
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual((result.returncode, result.stdout, result.stderr),
                                     (2, "", f"{usage}error: {diagnostic}\n"))
                    self.assertEqual(config.read_bytes(), contents)
                    self.assertEqual(game.read_bytes(), game_contents)
                    self.assertEqual({path.name for path in folder.iterdir()},
                                     {config.name, game.name})

    def test_existing_root_help_keeps_its_previous_body(self):
        environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), COLUMNS="80")
        result = subprocess.run(
            [sys.executable, "-B", "-m", "retrostation", "--help"],
            cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
        )
        expected_body = (
            "\nExplore configured console emulator profiles\n"
            "\npositional arguments:\n"
            "  {systems,preview}\n"
            "    systems          List configured consoles and their emulator names (no\n"
            "                     launch)\n"
            "    preview          Print emulator arguments for one game as JSON (no launch)\n"
            "\noptions:\n"
            "  -h, --help         show this help message and exit\n"
            "  --config CONFIG    Path to one local TOML profile file\n"
        )
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertEqual(result.stdout.partition("\n")[2], expected_body)

    def test_previews_selected_system_without_executing_or_modifying_files(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            config = folder / "profiles.toml"
            game = folder / "legal-test-game.bin"
            marker = folder / "emulator-was-started"
            game.write_bytes(b"synthetic game fixture")
            script = f"from pathlib import Path; Path({str(marker)!r}).write_text('started')"
            arguments = [sys.executable, "-c", script, "{game}"]
            contents = (
                '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "Fixture"\n'
                f'command = {json.dumps(arguments)}\n'
                '\n[[systems]]\nid = "gamecube"\nname = "GameCube"\nemulator = "Dolphin"\n'
            )
            config.write_text(contents, encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            def invoke(*args):
                return subprocess.run(
                    [sys.executable, "-B", "-m", "retrostation", "--config", str(config), *args],
                    cwd=directory, env=environment, capture_output=True, text=True, check=False,
                )

            preview = invoke("preview", "--system", "nes", "--game", str(game))
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(preview.stdout, json.dumps([*arguments[:-1], str(game)]) + "\n")
            self.assertEqual(preview.stderr, "")
            self.assertFalse(marker.exists())
            self.assertEqual(game.read_bytes(), b"synthetic game fixture")
            self.assertEqual(config.read_text(encoding="utf-8"), contents)

            listing = invoke("systems")
            self.assertEqual((listing.returncode, listing.stdout, listing.stderr),
                             (0, "nes\tNES\tFixture\ngamecube\tGameCube\tDolphin\n", ""))

            missing = invoke("preview", "--system", "gamecube", "--game", str(game))
            self.assertEqual(missing.returncode, 2, missing.stderr)
            self.assertEqual(missing.stdout, "")
            self.assertIn("No launch command for system: gamecube", missing.stderr)
            unknown = invoke("preview", "--system", "missing-system", "--game", str(game))
            self.assertEqual(unknown.returncode, 2, unknown.stderr)
            self.assertEqual(unknown.stdout, "")
            self.assertIn("Unknown system: missing-system", unknown.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual(game.read_bytes(), b"synthetic game fixture")
            self.assertEqual(config.read_text(encoding="utf-8"), contents)

    def test_rejects_invalid_launch_templates_without_changing_configuration(self):
        commands = ('[]', '["emu", "no-game"]', '["emu", "{game}", "{game}"]', '"emu {game}"')
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            for command in commands:
                with self.subTest(command=command):
                    contents = (
                        '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\n'
                        f'command = {command}\n'
                    )
                    config.write_text(contents, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", "-m", "retrostation", "--config", str(config), "systems"],
                        cwd=directory, env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("Invalid command at system entry 1", result.stderr)
                    self.assertEqual(config.read_text(encoding="utf-8"), contents)

    def test_rejects_unrecognized_profile_fields_without_changing_file(self):
        cases = (
            '[system]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\n',
            '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\nexecutable = "/missing/emulator"\n',
            '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\nenabled = false\n',
        )
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            for contents in cases:
                with self.subTest(contents=contents):
                    config.write_text(contents, encoding="utf-8")
                    result = subprocess.run(
                        [sys.executable, "-B", "-m", "retrostation", "--config", str(config), "systems"],
                        cwd=directory, env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("error:", result.stderr)
                    self.assertEqual(config.read_text(encoding="utf-8"), contents)

    def test_rejects_repeated_config_option(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            contents = '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "RetroArch"\n'
            config.write_text(contents, encoding="utf-8")
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT / "src")
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [sys.executable, "-B", "-m", "retrostation", "--config", str(config.parent / "missing.toml"), "--config", str(config), "systems"],
                cwd=directory, env=environment, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertIn("error:", result.stderr)
            self.assertEqual(config.read_text(encoding="utf-8"), contents)

    def test_existing_commands_reject_launch_confirmation_option(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "profiles.toml"
            contents = '[[systems]]\nid = "nes"\nname = "NES"\nemulator = "Fixture"\ncommand = ["not-installed", "{game}"]\n'
            config.write_text(contents, encoding="utf-8")
            environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
            cases = (("systems", "--confirm"), ("preview", "--system", "nes", "--game", "example.nds", "--confirm"))
            for arguments in cases:
                with self.subTest(action=arguments[0]):
                    result = subprocess.run(
                        [sys.executable, "-B", "-m", "retrostation", "--config", str(config), *arguments],
                        cwd=directory, env=environment, capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("unrecognized arguments: --confirm", result.stderr)
                    self.assertIn("{systems,preview}", result.stderr)
                    self.assertNotIn("launch", result.stderr)
                    self.assertEqual(config.read_text(encoding="utf-8"), contents)


if __name__ == "__main__":
    unittest.main()
