# ModernArcade — RetroStation

RetroStation is an **application we build** to organize and launch existing console emulators from one place. The ASUS laptop is its first controller-driven, offline-capable target, not the whole product. Begin the safe Python core in parallel with [Sprint 0](docs/sprint-0.md); verify the machine and protect existing data before further installations or changing an operating system.

## Quick path

1. Read the [master plan](docs/RetroStation_Master_Plan.md), especially sections 8–11. Its earlier hardware readings are from October 17, 2026, not a fresh diagnosis.
2. Work through the [Sprint 0 checklist](docs/sprint-0.md). Record safe, non-sensitive findings in the [hardware inventory](docs/hardware-inventory.md). This does not block read-only app development.
3. Use [ADR-001](docs/decisions/ADR-001-platform-and-frontend.md) for the Windows 11 first-prototype choice; the UI toolkit and final OS remain undecided. Sprint 0 safety checks must be completed before treating the hardware milestone as finished or making system changes.
4. Track the first DS trial in the [test matrix](docs/test-matrix.md); owner-observed boot and save/load from the app do not yet verify controller navigation, offline replay, or a stable session.

## Run the app core

The Python 3.11+ core lists configured consoles and previews argument vectors for a selected system/game. `systems` and `preview` never start an emulator. The separate `launch` command **does** run the executable named by a trusted local profile after explicit confirmation; it does not install emulators or implement the controller interface. `config/examples/profiles.toml` is synthetic, not a claim that its emulators or core are installed.

```sh
PYTHONPATH=src python3 -B -m retrostation --config config/examples/profiles.toml systems
PYTHONPATH=src python3 -B -m retrostation --config config/examples/profiles.toml preview --system nes --game example.rom
python3 -B -m unittest discover -s tests -v
```

The synthetic menu still runs independently of pygame-ce and does not open a window or game:

```sh
PYTHONPATH=src python3 -B -m retrostation.menu --simulate down select back
```

Provide `--simulate` once with the actions in order. It shows a sample two-system menu, a mock preview and a return to the menu. The optional **game-free** window uses the same state and pygame-ce's mapped controller button events. An isolated Windows Python 3.14 environment under the owner's Desktop test sandbox contains the pinned optional dependency in `requirements-ui.txt`; global Python and games are untouched. From PowerShell at the repository root, after connecting the controller:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
$uiPython = Join-Path ([Environment]::GetFolderPath("Desktop")) 'prueba_emu_nds_1\ui-venv\Scripts\python.exe'
& $uiPython -B -m retrostation.pygame_menu --window
```

D-pad moves, A selects the mock preview, B returns, and the window's close button exits. No real emulator is launched. A successful window process does not prove DualShock 4 mapping, return from a real game, or offline replay; record those only after observing them on the device.

In Windows PowerShell, set `$env:PYTHONPATH = "src"` and replace `python3` with `python` in these commands. `systems` prints tab-separated `id`, `name`, and `emulator` per configured system in file order. `preview` prints a JSON argument array; it never executes it, checks whether the named emulator is installed, or requires the game path to exist. Provide `--config` **exactly once**. Each `[[systems]]` entry requires `id`, `name`, and `emulator`; an optional `command` is a nonempty list of argument strings with exactly one standalone `"{game}"` token. Unknown fields are rejected rather than silently ignored. The example `command` contains a placeholder core and cannot be used to launch a real emulator. The current code needs no downloaded dependencies or real games for its tests. For the ongoing work units, see [the feature log](odd/tasks/retrostation-app-foundation.md).

**Real process boundary:** `launch --system nds --game <copied-game-path> --confirm` requires a private `--config` file outside Git, an absolute existing emulator executable outside Git, and an existing game outside Git. It reuses the previewed arguments, starts the emulator **without a shell** in the executable's directory, and returns its exit code after it closes. This is not an OS sandbox: the emulator may write saves or config files. Use only your own profile and isolated game copy with a backup; never point `launch` at a game in this repository. The [test matrix](docs/test-matrix.md) distinguishes the earlier standalone melonDS trial from the later owner-observed app-driven launch and save reload.

## Boundaries

- Keep Windows 11 and existing files intact. No partitioning or OS installation without a reasoned decision and a verified independent backup.
- Do not commit games, disc images, BIOS/firmware, credentials, personal records, private saves, populated databases, or artwork without appropriate rights. The `.gitignore` helps with local folders; it is **not** a privacy guarantee. Inspect staged files before every commit.
- The Python core is the first implemented part of the app. pygame-ce is a first-prototype UI candidate, not a final toolkit decision; the SQLite catalog, Linux installation, public repository, and license remain open.

The [master plan](docs/RetroStation_Master_Plan.md) is the single reference copy in this repository. Update its dated status/history when decisions or real test results change; do not maintain a second copy here.
