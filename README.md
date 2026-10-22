# ModernArcade — RetroStation

RetroStation is an **application we build** to organize and launch existing console emulators from one place. The ASUS laptop is its first controller-driven, offline-capable target, not the whole product. Begin the safe Python core in parallel with [Sprint 0](docs/sprint-0.md); verify the machine and protect existing data before installing emulators or changing an operating system.

## Quick path

1. Read the [master plan](docs/RetroStation_Master_Plan.md), especially sections 8–11. Its earlier hardware readings are from October 17, 2026, not a fresh diagnosis.
2. Work through the [Sprint 0 checklist](docs/sprint-0.md). Record safe, non-sensitive findings in the [hardware inventory](docs/hardware-inventory.md). This does not block read-only app development.
3. Evaluate the [open platform decision](docs/decisions/ADR-001-platform-and-frontend.md) before installing an emulator or testing on the ASUS. The first playable hardware slice comes **after** the Sprint 0 exit checks.

## Run the first app slice

The initial Python 3.11+ core lists configured consoles and emulator names. It does **not** install emulators, scan games, launch a process, or implement the controller interface yet. `config/examples/profiles.toml` is synthetic configuration, not a claim that its emulators are installed.

```sh
PYTHONPATH=src python3 -B -m retrostation --config config/examples/profiles.toml systems
python3 -B -m unittest discover -s tests -v
```

In Windows PowerShell, use `$env:PYTHONPATH = "src"` and `python -B -m retrostation --config config/examples/profiles.toml systems`. The command prints one tab-separated `id`, `name`, and `emulator` per configured system in file order. Provide `--config` **exactly once**; each `[[systems]]` entry has those three fields, and unknown fields are rejected rather than silently ignored. `systems` is currently the only command. The current code needs no downloaded dependencies or real games. For the ongoing work units, see [the feature log](odd/tasks/retrostation-app-foundation.md).

## Boundaries

- Keep Windows 11 and existing files intact. No partitioning or OS installation without a reasoned decision and a verified independent backup.
- Do not commit games, disc images, BIOS/firmware, credentials, personal records, private saves, populated databases, or artwork without appropriate rights. The `.gitignore` helps with local folders; it is **not** a privacy guarantee. Inspect staged files before every commit.
- The Python core is the first implemented part of the app. The SQLite catalog, GUI toolkit, Linux installation, public repository, and license are not yet settled choices for this first code slice.

The [master plan](docs/RetroStation_Master_Plan.md) is the single reference copy in this repository. Update its dated status/history when decisions or real test results change; do not maintain a second copy here.
