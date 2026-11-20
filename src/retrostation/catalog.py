"""TOML game catalog and independent, game-free CLI."""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat
import tempfile
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
    return _validate_catalog(document, path, profiles)


def _validate_catalog(document: dict, path: Path, profiles: tuple[SystemProfile, ...]) -> tuple[Game, ...]:
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


def add_game(path: Path, profiles: tuple[SystemProfile, ...], fields: dict[str, str]) -> str:
    """Validate the whole candidate in memory, then atomically replace only this catalog."""
    try:
        original = path.read_bytes()
        document = tomllib.loads(original.decode("utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise ConfigError(f"Cannot read catalog: {error}") from error
    existing = _validate_catalog(document, path, profiles)
    position = len(existing) + 1
    normalized = {}
    for field in ("id", "title", "system", "path"):
        value = fields[field]
        if not value.strip() or any(char in value for char in "\t\r\n"):
            raise ConfigError(f"Invalid {field} at game entry {position}")
        normalized[field] = value.strip()
    if normalized["id"] in {game.identifier for game in existing}:
        raise ConfigError(f"Duplicate game id: {normalized['id']}")
    if normalized["system"] not in {profile.identifier for profile in profiles}:
        raise ConfigError(f"Unknown system: {normalized['system']}")

    newline = b"\r\n" if b"\r\n" in original else b"\n"
    row = "[[games]]\n" + "".join(
        f"{field} = {json.dumps(value, ensure_ascii=False)}\n"
        for field, value in normalized.items()
    )
    try:
        candidate = original + (newline if original else b"") + row.encode("utf-8").replace(b"\n", newline)
        parsed = tomllib.loads(candidate.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ConfigError(f"Cannot append [[games]] to catalog representation: {error}") from error
    _validate_catalog(parsed, path, profiles)

    temporary = None
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".catalog-",
                                         delete=False) as output:
            temporary = Path(output.name)
            os.chmod(temporary, mode)
            output.write(candidate)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except OSError as error:
        if temporary is not None:
            try:
                if temporary.exists():
                    os.chmod(temporary, stat.S_IMODE(temporary.stat().st_mode) | stat.S_IWUSR)
                temporary.unlink(missing_ok=True)
            except OSError as cleanup_error:
                raise ConfigError(f"Cannot update catalog: {error}; cannot clean temporary: {cleanup_error}") from error
        raise ConfigError(f"Cannot update catalog: {error}") from error
    return normalized["id"]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List and preview a read-only local game catalog, or add a title (no game or emulator access)",
        epilog="Use --config PROFILES --catalog CATALOG list, preview --game-id ID, "
               "or add --id ID --title TITLE --system SYSTEM --path PATH. "
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
    add = actions.add_parser("add", help="Append one validated title to an existing catalog (no launch)")
    for field in ("id", "title", "system", "path"):
        add.add_argument("--" + field, required=True, action="append", help="New game's " + field + " (exactly once)")
    args = parser.parse_args()
    if len(args.config) != 1:
        parser.error("--config must be provided exactly once")
    if len(args.catalog) != 1:
        parser.error("--catalog must be provided exactly once")
    if args.action == "add":
        for field in ("id", "title", "system", "path"):
            if len(getattr(args, field)) != 1:
                parser.error("--" + field + " must be provided exactly once")
    try:
        profiles = load_systems(args.config[0])
        if args.action == "add":
            identifier = add_game(args.catalog[0], profiles, {
                field: getattr(args, field)[0] for field in ("id", "title", "system", "path")
            })
        else:
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
    elif args.action == "preview":
        print(json.dumps(command))
    else:
        print(f"Added game: {identifier}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
