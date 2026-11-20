"""Independent read-only pygame controller catalog browser (never launches processes)."""

import argparse
from pathlib import Path

from .catalog import load_catalog
from .catalog_browser import advance_browser, initial_state, list_lines
from .pygame_input import controller_action
from .profiles import ConfigError, load_systems


def wrap_text(text: str, font: object, width: int = 592) -> tuple[str, ...]:
    """Break even long unspaced JSON tokens without losing a character or argument."""
    lines = []
    line = ""
    for char in text:
        if line and font.size(line + char)[0] > width:
            lines.append(line)
            line = ""
        line += char
    lines.append(line)
    return tuple(lines)


def run_browser_window(config: Path, catalog: Path, pygame_module=None, controller_module=None):
    """Validate metadata before pygame import; never open or check selected game files."""
    profiles = load_systems(config)
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
            pygame_module.display.set_caption("RetroStation catalog browser - preview only")
            font = pygame_module.font.Font(None, 36)
            clock = pygame_module.time.Clock()

            def preview_lines():
                return wrap_text(state.preview, font)

            def draw():
                screen.fill((20, 24, 32))
                if state.screen == "preview":
                    game = state.selected_games[state.game_index]
                    system = state.systems[state.system_index]
                    lines = ("PREVIEW ONLY - NO LAUNCH", f"{game.title} ({system.name})",
                             *preview_lines()[state.preview_offset:state.preview_offset + 4])
                else:
                    lines = list_lines(state)
                for index, line in enumerate(lines):
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
                        count = len(preview_lines()) if state.screen == "preview" else 0
                        state = advance_browser(state, action, count)
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
    parser = argparse.ArgumentParser(
        description="Browse a read-only game catalog and preview JSON argv with a controller; no launches",
        epilog="Use --window --config PROFILES --catalog CATALOG exactly once each. "
               "D-pad navigates (including wrapped preview lines); A selects/previews; B returns. "
               "Games need not exist; this command cannot start an emulator.",
    )
    parser.add_argument("--window", action="count", default=0, help="Open the preview-only controller window")
    parser.add_argument("--config", type=Path, action="append", help="UTF-8 TOML system profiles")
    parser.add_argument("--catalog", type=Path, action="append", help="UTF-8 TOML game catalog")
    args = parser.parse_args()
    if args.window != 1 or args.config is None or len(args.config) != 1 or args.catalog is None or len(args.catalog) != 1:
        parser.error("--window, --config and --catalog must be provided exactly once")
    try:
        run_browser_window(args.config[0], args.catalog[0])
    except ConfigError as error:
        parser.error(str(error))
    except ModuleNotFoundError as error:
        if error.name != "pygame" and not error.name.startswith("pygame."):
            raise
        parser.error("pygame-ce is required for --window; use the authorized isolated environment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
