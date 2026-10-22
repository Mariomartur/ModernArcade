"""The first, read-only entry point for the RetroStation application."""

import argparse
from pathlib import Path

from .profiles import ConfigError, load_systems


def main() -> int:
    parser = argparse.ArgumentParser(description="Explore configured console emulator profiles")
    parser.add_argument("--config", type=Path, action="append", required=True, help="Path to one local TOML profile file")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("systems", help="List configured consoles and their emulator names (no launch)")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
