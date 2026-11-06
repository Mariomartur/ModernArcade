"""Game-free pygame-ce window for the synthetic controller menu."""

import argparse
from pathlib import Path

from .launch import launch_game
from .launch_menu import LaunchState, advance_launch, finish_launch, render_launch
from .menu import MenuState, advance, render
from .pygame_input import controller_action
from .profiles import ConfigError, load_systems


def run_window(pygame_module=None, controller_module=None, *,
               launch_config: Path | None = None, game: str | None = None) -> MenuState | LaunchState:
    """Show a sample menu or an explicitly configured, confirmed launcher."""
    if (launch_config is None) != (game is None):
        raise ConfigError("Launch mode requires both config and game")
    profiles = load_systems(launch_config) if launch_config is not None else None
    if profiles is not None and not profiles:
        raise ConfigError("Launch mode requires at least one configured system")
    if pygame_module is None:
        import pygame as pygame_module
    if controller_module is None:
        from pygame._sdl2 import controller as controller_module

    pygame_module.init()
    opened = []
    try:
        controller_module.init()
        try:
            for index in range(controller_module.get_count()):
                if controller_module.is_controller(index):
                    opened.append(controller_module.Controller(index))
            screen = pygame_module.display.set_mode((640, 360))
            pygame_module.display.set_caption("RetroStation menu prototype")
            font = pygame_module.font.Font(None, 36)
            clock = pygame_module.time.Clock()
            state = (LaunchState(tuple(profile.name for profile in profiles))
                     if profiles is not None else MenuState())

            def draw() -> None:
                screen.fill((20, 24, 32))
                lines = render_launch(state) if isinstance(state, LaunchState) else render(state)
                for index, line in enumerate(lines.splitlines()):
                    screen.blit(font.render(line, True, (240, 240, 240)), (24, 32 + 48 * index))
                pygame_module.display.flip()

            running = True
            while running:
                for event in pygame_module.event.get():
                    if event.type == pygame_module.QUIT:
                        running = False
                        break
                    action = controller_action(event, pygame_module)
                    if action is not None:
                        if isinstance(state, LaunchState):
                            state, confirmed = advance_launch(state, action)
                            if confirmed:
                                draw()
                                try:
                                    status = launch_game(
                                        profiles, profiles[state.selected].identifier, game, launch_config,
                                    )
                                except ConfigError as error:
                                    state = finish_launch(state, f"Launch refused: {error}")
                                else:
                                    state = finish_launch(state, f"Emulator exited with status {status}")
                        else:
                            state = advance(state, action)
                if not running:
                    break
                draw()
                clock.tick(30)
            return state
        finally:
            for device in opened:
                device.quit()
            controller_module.quit()
    finally:
        pygame_module.quit()


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a game-free pygame-ce controller menu")
    parser.add_argument("--window", action="count", default=0,
                        help="Open the sample window (requires pygame-ce; no game is launched)")
    args = parser.parse_args()
    if args.window != 1:
        parser.error("--window must be provided exactly once")
    try:
        run_window()
    except ModuleNotFoundError as error:
        if error.name != "pygame" and not error.name.startswith("pygame."):
            raise
        parser.error("pygame-ce is required for --window; use the authorized isolated environment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
