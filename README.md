# ModernArcade — RetroStation

RetroStation is an **application we build** to organize and launch existing console emulators from one place. The ASUS laptop is its first controller-driven, offline-capable target, not the whole product. Begin the safe Python core in parallel with [Sprint 0](docs/sprint-0.md); verify the machine and protect existing data before installing emulators or changing an operating system.

## Quick path

1. Read the [master plan](docs/RetroStation_Master_Plan.md), especially sections 8–11. Its earlier hardware readings are from October 17, 2026, not a fresh diagnosis.
2. Work through the [Sprint 0 checklist](docs/sprint-0.md). Record safe, non-sensitive findings in the [hardware inventory](docs/hardware-inventory.md). This does not block read-only app development.
3. Evaluate the [open platform decision](docs/decisions/ADR-001-platform-and-frontend.md) before installing an emulator or testing on the ASUS. The first playable hardware slice comes **after** the Sprint 0 exit checks.

## Run the first app slice

The initial Python 3.11+ core lists configured consoles and previews argument vectors for a selected system/game. It does **not** install emulators, scan games, open a game, launch a process, or implement the controller interface yet. `config/examples/profiles.toml` is synthetic configuration, not a claim that its emulators or core are installed.

```sh
PYTHONPATH=src python3 -B -m retrostation --config config/examples/profiles.toml systems
PYTHONPATH=src python3 -B -m retrostation --config config/examples/profiles.toml preview --system nes --game example.rom
python3 -B -m unittest discover -s tests -v
```

In Windows PowerShell, set `$env:PYTHONPATH = "src"` and replace `python3` with `python` in these commands. `systems` prints tab-separated `id`, `name`, and `emulator` per configured system in file order. `preview` prints a JSON argument array; it never executes it, checks whether the named emulator is installed, or requires the game path to exist. Provide `--config` **exactly once**. Each `[[systems]]` entry requires `id`, `name`, and `emulator`; an optional `command` is a nonempty list of argument strings with exactly one standalone `"{game}"` token. Unknown fields are rejected rather than silently ignored. The example `command` contains a placeholder core and must be replaced before any future real launch. The current code needs no downloaded dependencies or real games. For the ongoing work units, see [the feature log](odd/tasks/retrostation-app-foundation.md).

## Boundaries

- Keep Windows 11 and existing files intact. No partitioning or OS installation without a reasoned decision and a verified independent backup.
- Do not commit games, disc images, BIOS/firmware, credentials, personal records, private saves, populated databases, or artwork without appropriate rights. The `.gitignore` helps with local folders; it is **not** a privacy guarantee. Inspect staged files before every commit.
- The Python core is the first implemented part of the app. The SQLite catalog, GUI toolkit, Linux installation, public repository, and license are not yet settled choices for this first code slice.

The [master plan](docs/RetroStation_Master_Plan.md) is the single reference copy in this repository. Update its dated status/history when decisions or real test results change; do not maintain a second copy here.
