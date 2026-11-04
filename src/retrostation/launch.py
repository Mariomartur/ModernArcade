"""Preview emulator arguments and explicitly run trusted local profiles."""

from pathlib import Path
import subprocess

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


def _inside_git_worktree(path: Path) -> bool:
    return any((parent / ".git").exists() for parent in path.parents)


def launch_game(profiles: tuple[SystemProfile, ...], system: str, game: str, config: Path) -> int:
    if _inside_git_worktree(config.resolve()):
        raise ConfigError("Launch config must be outside a Git worktree")
    game_path = Path(game).resolve()
    if not game_path.is_file():
        raise ConfigError("Game must be an existing file")
    if _inside_git_worktree(game_path):
        raise ConfigError("Game must be outside a Git worktree")

    arguments = preview_command(profiles, system, str(game_path))
    executable = Path(arguments[0])
    if not executable.is_absolute() or not executable.is_file():
        raise ConfigError("Emulator executable must be an absolute existing file")
    executable = executable.resolve()
    if _inside_git_worktree(executable):
        raise ConfigError("Emulator executable must be outside a Git worktree")
    try:
        result = subprocess.run(
            (str(executable), *arguments[1:]), cwd=executable.parent,
            shell=False, check=False,
        )
    except OSError as error:
        raise ConfigError(f"Cannot start emulator: {error}") from error
    return result.returncode
