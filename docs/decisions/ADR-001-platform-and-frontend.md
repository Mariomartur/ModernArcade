# ADR-001 — First-prototype platform and own-app interface

Date: 2026-11-04<br>
Status: Accepted for first-prototype platform only; UI library and final OS remain open

## Context

The [master plan](../RetroStation_Master_Plan.md#8-alternativas-de-plataforma-sin-elección-definitiva) now makes RetroStation's own application the target. It calls for one non-destructive, controller-driven and offline-capable playable test. Windows 11 must not be erased. A first-prototype platform is **not** the final operating-system decision; an independent backup must be verified before OS or partition experiments. The initial Python core can be developed safely before that hardware test.

## Options to evaluate

| Option from the master plan | What to validate | Status |
| --- | --- | --- |
| Windows 11 + RetroStation + an emulator | Existing drivers, own-app controller navigation, return to menu, offline use | Selected for first prototype; controller/menu/offline checks pending |
| ES-DE, Playnite or RetroBat on Windows | Controller-first interaction ideas | Optional experience references, not the product |
| General-purpose Linux + RetroStation | NVIDIA hybrid drivers, input, filesystem access and rollback | Deferred until safe test and backup |
| Batocera on separate media | Boot safety and controller workflow | Optional comparison, not authorized to boot/install yet |

Direct repartitioning or reinstalling is **not authorized** by the master plan. Compare normal laptop use, GPU compatibility, controller support, performance, offline operation, reproducibility, and zero-cost setup. Confirm current tool availability and licensing at evaluation time rather than treating historical proposals as tested facts.

## Decision and justification

The owner selected the current Windows 11 installation for the **first prototype** on 2026-11-04. The isolated melonDS launch and restored progress were user-observed on Windows, so this avoids changing the operating system while developing the own-app interface. This choice does **not** complete the [Sprint 0](../sprint-0.md) safety inventory, authorize an installation or partition change, establish controller/offline acceptance, or settle the final OS. Choose the own-app UI library separately after examining controller requirements; no GUI toolkit is selected by this ADR.

## Consequences and next check

The isolated title boot and save reload are recorded in the [test matrix](../test-matrix.md). Next validate controller navigation, return to the menu, and a repeat with Wi-Fi disconnected on the selected first-prototype platform; do not change partitions or put protected content in Git.
