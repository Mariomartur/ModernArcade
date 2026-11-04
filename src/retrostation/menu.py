"""Synthetic menu state; no emulator, game, or UI dependency is opened."""

import argparse
from dataclasses import dataclass


SYSTEMS = ("NES", "Nintendo DS")  # Illustrative entries, not installed systems.
ACTIONS = ("up", "down", "select", "back")


@dataclass(frozen=True)
class MenuState:
    selected: int = 0
    showing_preview: bool = False


def advance(state: MenuState, action: str) -> MenuState:
    if action not in ACTIONS:
        raise ValueError(f"Unknown menu action: {action}")
    if state.showing_preview:
        return MenuState(state.selected) if action == "back" else state
    if action == "up":
        return MenuState((state.selected - 1) % len(SYSTEMS))
    if action == "down":
        return MenuState((state.selected + 1) % len(SYSTEMS))
    if action == "select":
        return MenuState(state.selected, showing_preview=True)
    return state


def render(state: MenuState) -> str:
    if state.showing_preview:
        return f"Preview: {SYSTEMS[state.selected]} (synthetic; no emulator started)"
    return "\n".join(
        f"{'>' if index == state.selected else ' '} {name}"
        for index, name in enumerate(SYSTEMS)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate a controller-first menu without pygame-ce or games")
    parser.add_argument("--simulate", nargs="+", choices=ACTIONS, required=True, action="append",
                        help="Menu actions to simulate in order; provide once (up, down, select, back)")
    args = parser.parse_args()
    if len(args.simulate) != 1:
        parser.error("--simulate must be provided exactly once")
    state = MenuState()
    frames = [render(state)]
    for action in args.simulate[0]:
        state = advance(state, action)
        frames.append(render(state))
    print("\n---\n".join(frames))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
