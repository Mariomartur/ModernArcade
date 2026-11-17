"""Isolated injected pygame controller adapter for catalog launches."""

from pathlib import Path

from .catalog import load_catalog
from .catalog_launch_menu import advance_catalog, finish_catalog, initial_state, render_catalog
from .launch import launch_game
from .pygame_input import controller_action
from .profiles import ConfigError, load_systems


def run_catalog_window(launch_config: Path, catalog: Path, pygame_module=None, controller_module=None):
    """Validate metadata before opening a window; launch only after controller confirmation."""
    profiles = load_systems(launch_config)
    games = load_catalog(catalog, profiles)
    state = initial_state(profiles, games)
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
            pygame_module.display.set_caption("RetroStation catalog menu")
            font = pygame_module.font.Font(None, 36)
            clock = pygame_module.time.Clock()

            def draw() -> None:
                screen.fill((20, 24, 32))
                for index, line in enumerate(render_catalog(state).splitlines()):
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
                        state, confirmed = advance_catalog(state, action)
                        if confirmed:
                            draw()
                            game = state.selected_games[state.game_index]
                            try:
                                status = launch_game(profiles, game.system, str(game.path), launch_config)
                            except ConfigError as error:
                                state = finish_catalog(state, f"Launch refused: {error}")
                            else:
                                state = finish_catalog(state, f"Emulator exited with status {status}")
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
