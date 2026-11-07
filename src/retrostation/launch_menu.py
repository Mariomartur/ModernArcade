"""Pure controller confirmation state for a configured emulator launch."""

from dataclasses import dataclass, replace

from .menu import ACTIONS


@dataclass(frozen=True)
class LaunchState:
    entries: tuple[str, ...]
    selected: int = 0
    screen: str = "menu"
    message: str = ""
    launched: bool = False


def advance_launch(state: LaunchState, action: str) -> tuple[LaunchState, bool]:
    """Return the new screen and whether a second select confirmed launch."""
    if action not in ACTIONS:
        raise ValueError(f"Unknown menu action: {action}")
    if state.screen == "confirm":
        if action == "back":
            return replace(state, screen="menu", message=""), False
        if action == "select":
            return replace(state, screen="running", launched=True), True
    elif state.screen == "result":
        if action == "back":
            return replace(state, screen="menu", message=""), False
    elif state.screen == "menu":
        if action == "up":
            return replace(state, selected=(state.selected - 1) % len(state.entries)), False
        if action == "down":
            return replace(state, selected=(state.selected + 1) % len(state.entries)), False
        if action == "select" and not state.launched:
            return replace(state, screen="confirm"), False
    return state, False


def finish_launch(state: LaunchState, message: str) -> LaunchState:
    return replace(state, screen="result", message=message)


def render_launch(state: LaunchState) -> str:
    name = state.entries[state.selected]
    if state.screen == "confirm":
        return f"Launch {name}? Saves may change.\nPress A to start; B to cancel."
    if state.screen == "running":
        return f"Running {name}; close the emulator to return."
    if state.screen == "result":
        return f"{state.message}\nPress B to return to the menu."
    lines = [
        f"{'>' if index == state.selected else ' '} {entry}"
        for index, entry in enumerate(state.entries)
    ]
    if state.launched:
        lines.append("One launch completed; close the window.")
    return "\n".join(lines)
