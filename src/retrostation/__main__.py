"""Entry point for RetroStation's profile and explicit emulator commands."""

import argparse
import json
from pathlib import Path
import sys

from .launch import launch_game, preview_command
from .profiles import ConfigError, load_systems


def _launch_requested(argv: list[str]) -> bool:
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--config":
            index += 2
        elif token.startswith("--config="):
            index += 1
        else:
            return token == "launch"
    return False


def main() -> int:
    argv = sys.argv[1:]
    launch_only = _launch_requested(argv)
    parser = argparse.ArgumentParser(description="Explore configured console emulator profiles")
    parser.add_argument("--config", type=Path, action="append", required=True, help="Path to one local TOML profile file")
    actions = parser.add_subparsers(dest="action", required=True)
    if launch_only:
        launch = actions.add_parser("launch", help="Run a configured emulator (may change game saves)")
        launch.add_argument("--system", required=True, help="Configured console id")
        launch.add_argument("--game", required=True, help="Existing game outside a Git worktree")
        launch.add_argument("--confirm", action="store_true", help="Acknowledge process execution and possible save changes")
    else:
        actions.add_parser("systems", help="List configured consoles and their emulator names (no launch)")
        preview = actions.add_parser("preview", help="Print emulator arguments for one game as JSON (no launch)")
        preview.add_argument("--system", required=True, help="Configured console id")
        preview.add_argument("--game", required=True, help="Game path to include in the preview; not opened")
    arguments = parser.parse_args(argv)
    if len(arguments.config) != 1:
        parser.error("--config must be provided exactly once")
    try:
        profiles = load_systems(arguments.config[0])
    except ConfigError as error:
        parser.error(str(error))
    if arguments.action == "systems":
        for profile in profiles:
            print(f"{profile.identifier}\t{profile.name}\t{profile.emulator}")
    elif arguments.action == "preview":
        try:
            command = preview_command(profiles, arguments.system, arguments.game)
        except ConfigError as error:
            parser.error(str(error))
        print(json.dumps(command))
    elif arguments.action == "launch":
        if not arguments.confirm:
            parser.error("launch requires --confirm; emulator saves may change")
        try:
            return launch_game(profiles, arguments.system, arguments.game, arguments.config[0])
        except ConfigError as error:
            parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
