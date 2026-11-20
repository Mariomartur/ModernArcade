# First hardware test — Nintendo DS

**Result:** the owner reports successful boot and restored saved progress both in standalone melonDS and from RetroStation's explicit launch. The owner also reports D-pad, A and B working in a separate game-free menu test, and a later isolated game opening from the controller menu and returning to a menu controllable without a keyboard. These are user-observed results, not a stable-game or offline verdict. Keep game images, firmware, saves, and private paths outside Git.

| Check | Observed evidence | Status |
| --- | --- | --- |
| Game and system | Owner identifies Pokémon Platinum Version on Nintendo DS and affirms local-use rights; “Europe” appears in the file name but was not independently verified | Candidate, not distributed |
| Emulator and environment | melonDS 1.1 Windows x64, launched from a copied test setup outside the repository on 2026-10-23 | Process start observed |
| Game boot and play | Owner reported on 2026-10-28: “Abrió el juego e iba perfectamente bien” | User-observed success; session length/FPS not measured |
| Native save and reload | Owner reports that the saved progress loaded without error after reopening the copied game; the 512 KiB `.sav` is still present beside it. The save and state have a byte-checked local safety snapshot outside Git | Save and reload user-observed; no automated proof |
| Game-free menu with controller | On 2026-11-05 the owner reported seeing the pygame-ce sample window, moving the selection with D-pad, opening a mock preview with A, and returning to the menu with B | User-observed synthetic UI success; no emulator/game involved |
| Return from running game to menu without keyboard | On 2026-11-17 the owner reported opening the copied DS game from the opt-in controller menu and, after closing it, returning to the RetroStation menu and controlling it with the controller without a keyboard. The first window run ended without a visible verdict; the owner confirmed this after a second, separately requested window run. Process exit alone did not establish the result. | Owner-observed isolated success; not an automated or offline verdict |
| Offline replay | No Wi-Fi-disconnected run was reported | Not verified |
| App-driven launch | RetroStation's explicit `launch --confirm` passed synthetic tests and independent recheck. One isolated invocation exited 0 after melonDS closed; copied `.sav` and state files were written during the run, while the repository original remained unchanged. The owner later reported: “No hubo ningún problema, todo se ejcutó y se cargó bien” | Game and loaded progress user-observed from the app; no automated gameplay proof |

## Synthetic catalog launcher trial (2026-11-17)

- In an actual pygame-ce window with one mapped controller, the owner confirmed navigation, B cancellation, the displayed process status 7 after selecting the second NES test, and refusal of a second launch attempt in that session. This is owner-observed UI behavior, not inferred from process exit alone.
- The corrected synthetic fixture's window run exited 0; its synthetic process exited 7 as expected. One launch-log entry named the second NES fixture, all six fixture files had unchanged SHA-256 hashes, and no unexpected files appeared. An earlier fixture preparation was rejected with exit 2 before the window opened because an argument contained an embedded newline; the fixture was corrected without app code changes.
- No ROM, emulator or save was used in this trial. It adds no real-game validation; offline replay and prolonged session stability remain unverified.

## Synthetic catalog scroll trial (2026-11-20)

- In an actual pygame-ce window with a mapped controller, the owner reported smooth scrolling, selection remaining visible while scrolling, and Down past the last item wrapping to the first. The owner deliberately selected Test 01-01, not the initially expected Test 01-08; the expected-title probe mismatch was not an app failure.
- The fixture held 8 systems with 10 synthetic titles each (80 total). The window exited 0, the synthetic process exited 7 as expected, and exactly one launch-log entry named `s01-g01.fixture`. SHA-256 checks found all 82 protected files unchanged, with no unexpected files.
- No ROM, emulator or save was used. This does not establish real-game scroll behavior, offline replay or session stability; those remain unverified.

## Synthetic catalog browser trial (2026-11-20)

- In an actual pygame-ce window with a mapped controller, the owner confirmed inspecting a long preview and using B to leave both the test selection and system selection; the owner called the check correct.
- The catalog held 8 systems with 10 synthetic titles each (80 total). The browser window exited 0 with no output. Before/after SHA-256 checks found all 84 protected files unchanged (82 fixture files, the original baseline file, and the previous launch log); no unexpected files appeared apart from the reference snapshot. The old synthetic launch log was unchanged, with no new launches recorded.
- No real game, emulator or save was used. This does not verify offline replay or prolonged session stability.

## Next check

Preserve the `.sav`, state file, and their local snapshots; the two fresh pre-window snapshots were hash-verified and the live save/state hashes were unchanged after each run. They are on the same disk, not an independent backup. Next check offline replay separately. The [master plan](RetroStation_Master_Plan.md#11-hito-1-definición-de-terminado-definition-of-done) reserves “stable” for a representative session with save/load and no data loss.
