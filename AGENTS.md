# RetroStation agent notes

## Run and verify

- This is a Python 3.11+ app core, not an emulator. Run from the repository root with `PYTHONPATH=src`; there is no package install step for the current core.
- Safe CLI smoke checks (neither starts an emulator):
  - `PYTHONPATH=src python3 -B -m retrostation --config config/examples/profiles.toml systems`
  - `PYTHONPATH=src python3 -B -m retrostation --config config/examples/profiles.toml preview --system nes --game example.rom`
- Tests: `python3 -B -m unittest discover -s tests -v`. In PowerShell, set `$env:PYTHONPATH = "src"` for CLI commands and use `python` instead of `python3`.
- Headless menu: `PYTHONPATH=src python3 -B -m retrostation.menu --simulate down select back`. `retrostation.pygame_menu --window` remains game-free; only separate `retrostation.pygame_launch_menu --window --config ... --game ... --confirm` can start a process after a second controller confirmation. Do not run it with real assets without separate authorization and protected saves.
- The sample TOML contains illustrative emulator/core names; `preview` only prints argv and does not check installation or game existence. Pass `--config` exactly once.

## Code and evidence boundaries

- CLI entrypoint: `src/retrostation/__main__.py`; profile validation: `src/retrostation/profiles.py`; argument preview and actual process execution: `src/retrostation/launch.py`. `launch --confirm` is a real process call and can change saves, unlike `systems` and `preview`.
- Never launch or use the repository's original `.nds` file for tests. Real launch requires an explicitly authorized isolated game copy, private profile and absolute emulator executable outside Git; protect existing saves and use a backup. Synthetic unit tests need no real games or emulator.
- Never stage games, firmware, saves, credentials or other private assets. `.gitignore` does not make staging safe; inspect staged paths before committing.
- `README.md` describes the current CLI; `docs/RetroStation_Master_Plan.md` is the planning source, not proof that proposed features exist. `docs/test-matrix.md` records owner-observed manual and app-driven DS boot/save reload; controller flow and offline replay remain unverified. A zero exit code alone does not prove gameplay.
