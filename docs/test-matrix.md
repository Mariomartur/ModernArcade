# First hardware test — Nintendo DS

**Result:** the owner reports that Pokémon Platinum opened in melonDS and ran smoothly. This is a successful **manual boot/play observation**, not yet a stable-game verdict or a RetroStation app launch. Keep game images, firmware, saves, and private paths outside Git.

| Check | Observed evidence | Status |
| --- | --- | --- |
| Game and system | Owner identifies Pokémon Platinum Version on Nintendo DS and affirms local-use rights; “Europe” appears in the file name but was not independently verified | Candidate, not distributed |
| Emulator and environment | melonDS 1.1 Windows x64, launched from a copied test setup outside the repository on 2026-10-23 | Process start observed |
| Game boot and play | Owner reported on 2026-10-28: “Abrió el juego e iba perfectamente bien” | User-observed success; session length/FPS not measured |
| Native save and reload | No `.sav` or state file was found beside the copied game at the last readback | Not verified |
| DualShock 4 navigation and return to menu | No specific controller or exit-flow result was reported | Not verified |
| Offline replay | No Wi-Fi-disconnected run was reported | Not verified |
| App-driven launch | RetroStation previewed the isolated emulator/game arguments; melonDS was launched directly for the trial | Not implemented or verified |

## Next check

Confirm an in-game save and reload **using only the copied game in the isolated test folder**. Preserve any new save files. Then check controller navigation, return to the menu, and offline replay separately. The [master plan](RetroStation_Master_Plan.md#11-hito-1-definición-de-terminado-definition-of-done) reserves “stable” for a representative session with save/load and no data loss.
