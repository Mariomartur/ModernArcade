# Sprint 0 — Safe starting point

**Outcome:** a repeatable, non-destructive diagnosis, a protected-data plan, and a documented choice for the first hardware test. This checklist coordinates sections 8–11 of the [master plan](RetroStation_Master_Plan.md); it does not replace them. Development of the own app's read-only Python core may proceed in parallel, without installing emulators or changing the ASUS.

## Current evidence (October 22, 2026)

- [x] Local Git repository exists on `main`; `README.md` and `.gitattributes` were already tracked in an initial commit. The master's October 17 entry saying Git was not initialized is historical; its October 22 update reflects the current local state.
- [ ] Confirm the current Windows hardware inventory. Earlier measurements in the master plan are historical, **not** proof of today's temperatures, drive health, or controller state.
- [ ] Verify the external 2 TB drive's connection, capacity, filesystem, and health without writing to or reformatting it.
- [ ] Identify files to preserve and **verify an independent backup** before any OS or partition experiment.
- [x] Record the owner's Windows 11 first-prototype platform choice in [ADR-001](decisions/ADR-001-platform-and-frontend.md); the own-app UI technology and final OS remain undecided.
- [ ] Choose one legal, available homebrew/free/owned test title and document its provenance without adding the game to Git.
- [ ] Decide remote visibility and license **before** any publication. A local `origin` tracking reference does not establish whether a remote is safe or public; no remote action is part of this checklist.

## Run the diagnosis

1. On the ASUS in Windows, use the **read-only** PowerShell inventory commands in master-plan section 10 (S0-01). Do not run the obsolete `git init` instructions: this repository is already initialized.
2. Summarize only non-sensitive observations in [hardware-inventory.md](hardware-inventory.md). Redact serial numbers, full personal paths, accounts, tokens, and game files. An unavailable tool is not evidence of faulty hardware.
3. Record where the originals and the independent backup live **without recording private paths in Git**. Test backup recovery on a harmless representative file before claiming verification. Do not move originals or modify partitions to make a checklist pass.
4. Follow the Windows 11 first-prototype choice in ADR-001. Verify the remaining controller and offline checks; choosing this platform does not authorize OS changes or a GUI toolkit.
5. Before staging changes, inspect `git status --short --untracked-files=all`; inspect the staged names and contents before committing. Ignore rules cannot prevent forced additions or files placed in unexpected directories.

## Exit check

- [ ] Diagnosis can be repeated safely and the inventory is current.
- [ ] Data-protection status is explicit; a verified independent backup precedes any risky system experiment.
- [x] The first-prototype platform is recorded; controller/offline evidence and the independent backup remain pending.
- [ ] Repository documentation contains no protected/private material.

**Next hardware slice, not Sprint 0:** one legal game, one emulator integrated into the own application, DualShock 4 navigation, return to menu, and offline replay. See the master plan's phase 1 and milestone 1. The read-only Python core can be developed now; do not assume the catalog or controller interface exists yet.
