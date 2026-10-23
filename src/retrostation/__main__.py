"""The first, read-only entry point for the RetroStation application."""

import argparse
import json
from pathlib import Path

from .launch import preview_command
from .profiles import ConfigError, load_systems


def main() -> int:
    parser = argparse.ArgumentParser(description="Explore configured console emulator profiles")
    parser.add_argument("--config", type=Path, action="append", required=True, help="Path to one local TOML profile file")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("systems", help="List configured consoles and their emulator names (no launch)")
    preview = actions.add_parser("preview", help="Print emulator arguments for one game as JSON (no launch)")
    preview.add_argument("--system", required=True, help="Configured console id")
    preview.add_argument("--game", required=True, help="Game path to include in the preview; not opened")
    arguments = parser.parse_args()
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
