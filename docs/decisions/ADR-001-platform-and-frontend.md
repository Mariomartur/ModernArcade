# ADR-001 — First-prototype platform and own-app interface

Date: 2026-10-22<br>
Status: Proposed (no selection made)

## Context

The [master plan](../RetroStation_Master_Plan.md#8-alternativas-de-plataforma-sin-elección-definitiva) now makes RetroStation's own application the target. It calls for one non-destructive, controller-driven and offline-capable playable test. Windows 11 must not be erased. A first-prototype platform is **not** the final operating-system decision; an independent backup must be verified before OS or partition experiments. The initial Python core can be developed safely before that hardware test.

## Options to evaluate

| Option from the master plan | What to validate | Status |
| --- | --- | --- |
| Windows 11 + RetroStation + an emulator | Existing drivers, own-app controller navigation, return to menu, offline use | First-prototype candidate, not selected |
| ES-DE, Playnite or RetroBat on Windows | Controller-first interaction ideas | Optional experience references, not the product |
| General-purpose Linux + RetroStation | NVIDIA hybrid drivers, input, filesystem access and rollback | Deferred until safe test and backup |
| Batocera on separate media | Boot safety and controller workflow | Optional comparison, not authorized to boot/install yet |

Direct repartitioning or reinstalling is **not authorized** by the master plan. Compare normal laptop use, GPU compatibility, controller support, performance, offline operation, reproducibility, and zero-cost setup. Confirm current tool availability and licensing at evaluation time rather than treating historical proposals as tested facts.

## Decision and justification

Pending: gather the [Sprint 0](../sprint-0.md) evidence and record the owner's first-prototype platform choice here. Choose the own-app UI library separately after examining controller requirements; no GUI toolkit is selected by this ADR. Record the final-OS choice separately if it ever becomes necessary. No emulator software has been installed or evaluated by this ADR.

## Consequences and next check

Once a first-prototype choice is recorded, test one legally usable title without changing existing partitions. Document launch, controller behavior, save/load when supported, return to the menu, and a repeat with Wi-Fi disconnected; keep protected content outside Git.
