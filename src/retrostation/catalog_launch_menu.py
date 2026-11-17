"""Pure system -> catalog game -> one-shot confirmation state."""

from dataclasses import dataclass, replace

from .catalog import Game
from .menu import ACTIONS
from .profiles import ConfigError, SystemProfile


@dataclass(frozen=True)
class CatalogState:
    profiles: tuple[SystemProfile, ...]
    games: tuple[Game, ...]
    system_index: int = 0
    game_index: int = 0
    screen: str = "systems"
    message: str = ""
    attempted: bool = False

    @property
    def systems(self) -> tuple[SystemProfile, ...]:
        available = {game.system for game in self.games}
        return tuple(profile for profile in self.profiles if profile.identifier in available)

    @property
    def selected_games(self) -> tuple[Game, ...]:
        system = self.systems[self.system_index].identifier
        return tuple(game for game in self.games if game.system == system)


def initial_state(profiles: tuple[SystemProfile, ...], games: tuple[Game, ...]) -> CatalogState:
    if not games:
        raise ConfigError("Catalog requires at least one game")
    return CatalogState(profiles, games)


def advance_catalog(state: CatalogState, action: str) -> tuple[CatalogState, bool]:
    """Advance navigation; return True only for the first confirmed attempt."""
    if action not in ACTIONS:
        raise ValueError(f"Unknown menu action: {action}")
    if state.screen == "systems":
        if action in ("up", "down"):
            step = -1 if action == "up" else 1
            return replace(state, system_index=(state.system_index + step) % len(state.systems)), False
        if action == "select":
            return replace(state, screen="games", game_index=0), False
    elif state.screen == "games":
        if action in ("up", "down"):
            step = -1 if action == "up" else 1
            return replace(state, game_index=(state.game_index + step) % len(state.selected_games)), False
        if action == "back":
            return replace(state, screen="systems"), False
        if action == "select" and not state.attempted:
            return replace(state, screen="confirm"), False
    elif state.screen == "confirm":
        if action == "back":
            return replace(state, screen="games"), False
        if action == "select":
            return replace(state, screen="running", attempted=True), True
    elif state.screen == "result" and action == "back":
        return replace(state, screen="games", message=""), False
    return state, False


def finish_catalog(state: CatalogState, message: str) -> CatalogState:
    return replace(state, screen="result", message=message)


def render_catalog(state: CatalogState) -> str:
    if state.screen in ("confirm", "running"):
        game = state.selected_games[state.game_index]
        name = f"{game.title} ({state.systems[state.system_index].name})"
        if state.screen == "confirm":
            return f"Launch {name}? Saves may change.\nPress A to start; B to cancel."
        return f"Running {name}; close the emulator to return."
    if state.screen == "result":
        return f"{state.message}\nPress B to return to games."
    if state.screen == "systems":
        names = [profile.name for profile in state.systems]
        selected = state.system_index
    else:
        names = [game.title for game in state.selected_games]
        selected = state.game_index
    lines = [f"{'>' if index == selected else ' '} {name}" for index, name in enumerate(names)]
    if state.attempted:
        lines.append("One launch attempted; close the window.")
    return "\n".join(lines)
