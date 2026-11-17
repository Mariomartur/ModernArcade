"""Explicit controller launcher; never the default game-free menu command."""

import argparse
from pathlib import Path

from .pygame_catalog_menu import run_catalog_window
from .pygame_menu import run_window
from .profiles import ConfigError


def main() -> int:
    parser = argparse.ArgumentParser(description="Open an explicitly configured emulator menu")
    parser.add_argument("--window", action="count", default=0, help="Open the controller menu")
    parser.add_argument("--config", type=Path, action="append", help="Private TOML profile outside Git")
    parser.add_argument("--game", action="append", help="Existing game copy outside Git")
    parser.add_argument("--catalog", type=Path, action="append",
                        help="Read-only TOML game catalog; alternative to --game")
    parser.add_argument("--confirm", action="count", default=0,
                        help="Allow a controller-confirmed emulator launch; saves may change")
    args = parser.parse_args()
    if args.window != 1:
        parser.error("--window must be provided exactly once")
    if args.game is not None and args.catalog is not None:
        parser.error("--game and --catalog are mutually exclusive")
    if args.catalog is not None:
        if (args.config is None or len(args.config) != 1
                or len(args.catalog) != 1 or args.confirm != 1):
            parser.error("--config, --catalog and --confirm are required exactly once for catalog launch mode")
    elif (args.config is None or len(args.config) != 1
          or args.game is None or len(args.game) != 1 or args.confirm != 1):
        parser.error("--config, --game and --confirm are required exactly once for launch mode")
    try:
        if args.catalog is not None:
            run_catalog_window(args.config[0], args.catalog[0])
        else:
            run_window(launch_config=args.config[0], game=args.game[0])
    except ConfigError as error:
        parser.error(str(error))
    except ModuleNotFoundError as error:
        if error.name != "pygame" and not error.name.startswith("pygame."):
            raise
        parser.error("pygame-ce is required for --window; use the authorized isolated environment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
