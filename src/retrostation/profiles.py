"""Read console/emulator profiles without touching games or starting processes."""

from dataclasses import dataclass
from pathlib import Path
import tomllib


class ConfigError(ValueError):
    """The selected local profile file cannot be used."""


@dataclass(frozen=True)
class SystemProfile:
    identifier: str
    name: str
    emulator: str
    command: tuple[str, ...] | None = None


def load_systems(path: Path) -> tuple[SystemProfile, ...]:
    try:
        with path.open("rb") as source:
            document = tomllib.load(source)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ConfigError(f"Cannot read profiles: {error}") from error

    unknown = set(document) - {"systems"}
    if unknown:
        raise ConfigError(f"Unknown profile field: {sorted(unknown)[0]}")
    rows = document.get("systems", [])
    if not isinstance(rows, list):
        raise ConfigError("Expected [[systems]] entries in the profile file")

    profiles = []
    seen = set()
    for position, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ConfigError(f"Invalid system at entry {position}")
        unknown = set(row) - {"id", "name", "emulator", "command"}
        if unknown:
            raise ConfigError(f"Unknown field at system entry {position}: {sorted(unknown)[0]}")
        values = []
        for field in ("id", "name", "emulator"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip() or any(char in value for char in "\t\r\n"):
                raise ConfigError(f"Invalid {field} at system entry {position}")
            values.append(value.strip())
        identifier, name, emulator = values
        if identifier in seen:
            raise ConfigError(f"Duplicate system id: {identifier}")
        command = None
        if "command" in row:
            tokens = row["command"]
            if (not isinstance(tokens, list) or not tokens or tokens[0] == "{game}"
                    or any(not isinstance(token, str) or not token.strip()
                           or any(char in token for char in "\t\r\n") for token in tokens)
                    or tokens.count("{game}") != 1):
                raise ConfigError(f"Invalid command at system entry {position}: expected one {{game}} token")
            command = tuple(tokens)
        seen.add(identifier)
        profiles.append(SystemProfile(identifier, name, emulator, command))
    return tuple(profiles)
