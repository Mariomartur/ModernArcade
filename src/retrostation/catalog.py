"""Read-only TOML game catalog and independent, game-free CLI."""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import tomllib

from .launch import preview_command
from .profiles import ConfigError, SystemProfile, load_systems


@dataclass(frozen=True)
class Game:
    identifier: str
    title: str
    system: str
    path: Path


def load_catalog(path: Path, profiles: tuple[SystemProfile, ...]) -> tuple[Game, ...]:
    """Validate all rows before returning any; never open a game path."""
    try:
        with path.open("rb") as source:
            document = tomllib.load(source)
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise ConfigError(f"Cannot read catalog: {error}") from error

    unknown = set(document) - {"games"}
    if unknown:
        raise ConfigError(f"Unknown catalog field: {sorted(unknown)[0]}")
    rows = document.get("games", [])
    if not isinstance(rows, list):
        raise ConfigError("Expected [[games]] entries in the catalog file")

    games = []
    seen = set()
    systems = {profile.identifier for profile in profiles}
    for position, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ConfigError(f"Invalid game at entry {position}")
        unknown = set(row) - {"id", "title", "system", "path"}
        if unknown:
            raise ConfigError(f"Unknown field at game entry {position}: {sorted(unknown)[0]}")
        values = []
        for field in ("id", "title", "system", "path"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip() or any(char in value for char in "\t\r\n"):
                raise ConfigError(f"Invalid {field} at game entry {position}")
            values.append(value.strip())
        identifier, title, system, game_path = values
        if identifier in seen:
            raise ConfigError(f"Duplicate game id: {identifier}")
        if system not in systems:
            raise ConfigError(f"Unknown system: {system}")
        resolved = Path(game_path)
        if not resolved.is_absolute():
            resolved = path.absolute().parent / resolved
        seen.add(identifier)
        games.append(Game(identifier, title, system, resolved))
    return tuple(games)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List and preview a read-only local game catalog (no game or emulator access)",
        epilog="Use --config PROFILES --catalog CATALOG list, or preview --game-id ID. "
               "Relative game paths are resolved against the catalog directory; games need not exist.",
    )
    parser.add_argument("--config", type=Path, action="append", required=True,
                        help="One UTF-8 TOML system profile file (exactly once)")
    parser.add_argument("--catalog", type=Path, action="append", required=True,
                        help="One UTF-8 TOML [[games]] catalog (exactly once)")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("list", help="Print id, title, system, resolved path as TSV (no launch)")
    preview = actions.add_parser("preview", help="Print selected game's argument vector as JSON (no launch)")
    preview.add_argument("--game-id", required=True, help="Catalog game id")
    args = parser.parse_args()
    if len(args.config) != 1:
        parser.error("--config must be provided exactly once")
    if len(args.catalog) != 1:
        parser.error("--catalog must be provided exactly once")
    try:
        profiles = load_systems(args.config[0])
        games = load_catalog(args.catalog[0], profiles)
        if args.action == "preview":
            game = next((game for game in games if game.identifier == args.game_id), None)
            if game is None:
                raise ConfigError(f"Unknown game id: {args.game_id}")
            command = preview_command(profiles, game.system, str(game.path))
    except ConfigError as error:
        parser.error(str(error))
    if args.action == "list":
        for game in games:
            print(f"{game.identifier}\t{game.title}\t{game.system}\t{game.path}")
    else:
        print(json.dumps(command))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
