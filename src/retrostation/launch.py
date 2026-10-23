"""Build a read-only launch preview; process execution is a separate slice."""

from .profiles import ConfigError, SystemProfile


def preview_command(profiles: tuple[SystemProfile, ...], system: str, game: str) -> tuple[str, ...]:
    profile = next((profile for profile in profiles if profile.identifier == system), None)
    if profile is None:
        raise ConfigError(f"Unknown system: {system}")
    if profile.command is None:
        raise ConfigError(f"No launch command for system: {system}")
    if not game:
        raise ConfigError("Game path is required")
    return tuple(game if token == "{game}" else token for token in profile.command)
