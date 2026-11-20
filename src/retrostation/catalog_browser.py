"""Pure navigation and read-only argument preview for the controller catalog browser."""

from dataclasses import dataclass, replace
import json

from .catalog import Game
from .launch import preview_command
from .menu import ACTIONS
from .profiles import ConfigError, SystemProfile


@dataclass(frozen=True)
class BrowserState:
    profiles: tuple[SystemProfile, ...]
    games: tuple[Game, ...]
    system_index: int = 0
    game_index: int = 0
    screen: str = "systems"
    preview: str = ""
    preview_offset: int = 0

    @property
    def systems(self) -> tuple[SystemProfile, ...]:
        available = {game.system for game in self.games}
        return tuple(profile for profile in self.profiles if profile.identifier in available)

    @property
    def selected_games(self) -> tuple[Game, ...]:
        identifier = self.systems[self.system_index].identifier
        return tuple(game for game in self.games if game.system == identifier)


def initial_state(profiles: tuple[SystemProfile, ...], games: tuple[Game, ...]) -> BrowserState:
    if not games:
        raise ConfigError("Catalog requires at least one game")
    return BrowserState(profiles, games)


def advance_browser(state: BrowserState, action: str, preview_lines: int = 0) -> BrowserState:
    if action not in ACTIONS:
        raise ValueError(f"Unknown menu action: {action}")
    if state.screen == "systems":
        if action in ("up", "down"):
            step = -1 if action == "up" else 1
            return replace(state, system_index=(state.system_index + step) % len(state.systems))
        if action == "select":
            return replace(state, screen="games", game_index=0)
    elif state.screen == "games":
        if action in ("up", "down"):
            step = -1 if action == "up" else 1
            return replace(state, game_index=(state.game_index + step) % len(state.selected_games))
        if action == "back":
            return replace(state, screen="systems")
        if action == "select":
            game = state.selected_games[state.game_index]
            try:
                preview = json.dumps(preview_command(state.profiles, game.system, str(game.path)))
            except ConfigError as error:
                preview = f"Preview unavailable: {error}"
            return replace(state, screen="preview", preview=preview, preview_offset=0)
    else:
        if action == "back":
            return replace(state, screen="games")
        if action in ("up", "down"):
            step = -1 if action == "up" else 1
            return replace(state, preview_offset=max(0, min(state.preview_offset + step,
                                                            max(0, preview_lines - 4))))
    return state


def list_lines(state: BrowserState) -> tuple[str, ...]:
    if state.screen == "systems":
        items, selected = state.systems, state.system_index
        label = lambda item: item.name
    else:
        items, selected = state.selected_games, state.game_index
        label = lambda item: item.title
    start = max(0, selected - 5)
    return tuple(f"{'>' if index == selected else ' '} {label(item)}"
                 for index, item in enumerate(items[start:start + 6], start))
