# Universal guns and mixed-pair release — 2026-10-09

One consolidated ARM64 APK is available: `builds/universal_dual_wield_final/MiniMilitiaClassic-Universal-Dual-v1.0.0.apk`. Native SHA-256: `e57f7598839ff65dd6e71e354fd2fc02ab65f414be0a1c23f2aac4a1727c1cce`. APK SHA-256: `a3be60a39955042dd7c63fcfb384e180fbf345bf0fc06baa21b7eb01e5904e2a`.

User confirms both the SPAS two-action UI and sniper pair work physically. The consolidated extension enables 22 held gun classes, giving 484 ordered same/mixed pairings, with separate Swap/Dual buttons. New classes, mixed visuals, reload/drop/respawn regressions and private LAN remain physically unverified. This is a release candidate, not a claim of every pair passing device tests.

## Recovered gun roster and policy

| ItemType | Class | Dual-hand configuration |
|---:|---|---|
| 3 | DEAGLE | Existing specialized/verified held dual transform preserved |
| 4 | MAGNUM | Existing specialized/verified held dual transform preserved |
| 5 | UZI | Existing specialized/verified held dual transform preserved |
| 6 | MP5 | Existing primary held transform reused for dual hand |
| 7 | AK47 | Existing primary held transform reused for dual hand |
| 8 | M16 | Existing primary held transform reused for dual hand |
| 9 | SHOTGUN | Existing specialized/verified held dual transform preserved |
| 10 | M93BA | Existing specialized/verified held dual transform preserved |
| 11 | SMAW | Existing primary held transform reused for dual hand |
| 16 | M14 | Existing primary held transform reused for dual hand |
| 17 | PHASR | Existing primary held transform reused for dual hand |
| 18 | GDEAGLE | Existing specialized/verified held dual transform preserved |
| 19 | FLAMETHROWER | Existing primary held transform reused for dual hand |
| 21 | EMP | Existing primary held transform reused for dual hand |
| 25 | SAWGUN | Existing primary held transform reused for dual hand |
| 26 | TAVOR | Existing primary held transform reused for dual hand |
| 27 | MINIGUN | Existing primary held transform reused for dual hand |
| 28 | TEC9 | Existing specialized/verified held dual transform preserved |
| 29 | RG6 | Existing primary held transform reused for dual hand |
| 31 | XM8 | Existing primary held transform reused for dual hand |
| 37 | AA12 | Existing primary held transform reused for dual hand |
| 39 | M1881 | Existing specialized/verified held dual transform preserved |

The factory mappings, each class's own triggerPull and its held/dual transforms were checked against ELF vtables and read-only Ghidra decompilation. ROCKET type 12 is a projectile with an inherited no-op trigger, not the SMAW launcher; SAW and MORTAR similarly represent projectiles. Grenades, knives, shields, power-ups and objective flags/bombs are excluded from the gun whitelist. Existing dedicated dual-only utility routing is preserved.

The 64-bit gun mask is embedded into the shared HUD and inventory guards. Both incoming and primary type must be below 64 and present in that mask; negative/invalid types are rejected before shifting. All same and mixed gun combinations use the same machinery. No new copy of a gun instance, projectile routine or separate input system is created. Existing pointer-alias checks, stock retain/release and occupied-dual guards remain. Normal Swap follows the confirmed normal stow/drop path; Dual keeps the primary and adds the incoming instance to the opposite hand. When both hands are occupied the Dual action stays disabled; normal Swap may drop the current dual through stock inventory rules.

Specialized DEAGLE, MAGNUM, UZI, GDEAGLE, TEC9 and M1881 dual configurations remain untouched. Verified SPAS/sniper held transforms remain. Empty inherited dual configurations for the other guns are mapped to each class's original primary held transform through class-scoped ABS64 vtable relocations. Weapon sprites, initial geometry and firing-point data remain original. Opposite-hand alignment/flip correctness for every larger class still needs visual device testing.

## Direct-ammo guns and firing dispatch

EMP, PHASR, MINIGUN and SAWGUN read their own clip/reserve fields directly instead of querying the patched getters at every shot. This can leave a newly acquired dual instance at zero because stock pickup clears those fields. Local fire dispatch now queries the exact working getClip/getAmmo functions for each non-null held instance before invoking its original virtual triggerPull once. The existing getters refill only owned local instances and use that gun's virtual capacities.

The helper at ELF/file 0x8e6b00 lies in former dual-routing code skipped by the confirmed inventory implementation. Its 64-byte AAPCS64 frame preserves FP/LR, controller, weapon pointer and the original float delta across the getter calls. The fire entry at 0x8ec46c branches to it. The helper fits entirely before the retained normal route at 0x8e6cac; compiled pickup eligibility ends before the helper. Null slots are skipped, and primary and dual pointers are queried independently. No callee-saved general register, timer, recoil, charge/spin state, reload flag or projectile callback is modified by the helper. Two-frame emulation verifies that clip depletion is refilled before the next shot and each live pointer receives exactly one firing call per frame.

Every gun's triggerPull and primary configuration remain byte-identical to the confirmed build. This preserves stock burst, pellet, charge, spin-up and automatic behavior at the method level. Ammo getters, subAmmo and fuel code are unchanged; all mutation spans and original/replacement bytes are recorded in native-patches.json and package-verification.json. Whole-library scope checks exclude accidental changes elsewhere. Remote/network methods and server/authentication code are untouched. The extra getter queries are part of unlimited ammo handling, not duplicate projectile spawning.

## Automated results

3,566 case records PASS: complete factory-domain policy and HUD checks for ItemTypes 0–39, all 484 gun pairings, ordinary Swap preservation with empty/full stowed slots, occupied-dual rejection, pointer aliases, stale/null UI, invalid unsigned shift bounds, scaled mixed-pair button positioning/hiding, preserved utility UI, and actual patched getters plus the new real ARM64 fire dispatcher. Ownership, Cocos and projectile callbacks are fixtures. These are structural/control-flow/ammo tests, not rendered Android gameplay or LAN tests.

The final APK and split set pass matching certificate, ZIP CRC, alignment, exact game native payload and equality of all other application payloads. The compressed single APK's unchanged manifest was verified to have extractNativeLibs=true. The split set retains uncompressed 4096-byte-aligned native entries required by extractNativeLibs=false. Python/shell syntax and preserved working-build hashes pass. No app uninstall, data clear or automatic device install was performed for this release; the user requested manual download.

## Why APK size increased, and final reduction

All recent SPAS, SPAS UI and sniper APKs were exactly 82,590,367 bytes (78.76 MiB); they were not growing with each gun patch. The earlier increase came from the packaging change to an uncompressed 20,736,920-byte game library. In earlier compressed APKs it occupied roughly 7.3 MB. Native methods and new eligibility code do not increase ELF file length, and no new image/map assets are added.

The final standalone APK safely compresses that library to 7,292,331 bytes because its manifest permits extraction. Other application payloads remain identical. Final APK: **69,139,103 bytes (65.94 MiB)**, a saving of **13,451,264 bytes (16.3%)** versus the sniper APK. Base.apk by itself is smaller because it lacks required ARM64 native payloads; a one-file install must include them. Android installed footprint also includes extracted native libraries, app data and runtime caches, so APK download size and installed size differ.

## Reproduce, install, verify and roll back

`python3 scripts/build_universal_guns.py` creates the isolated outputs and refuses overwrite. `python3 scripts/build_universal_guns.py --verify` rechecks them. `PYTHONPATH=/tmp/mmc-unicorn-tests:scripts python3 scripts/test_universal_guns_arm64.py` executes the tests. Pip-installed Unicorn resides only in the session's temporary folder; it must be installed again if that folder is cleared.

For manual installation, download the one APK and open it as an update. Existing app signature/version are retained; no uninstall or clear-data step is needed. Split deployment remains available via `scripts/deploy_universal_guns.sh`. Confirmed sniper outputs are backed up in `backup/universal-guns-20261009/` with a hash manifest. Roll back using the preceding sniper APK or `scripts/deploy_dual_wield_sniper.sh` as an update.

Manual regression checklist: same-class rocket/automatic/energy/pistol pairs; sniper+rocket, SPAS+sniper, shotgun+pistol and automatic+energy mixed pairs; separate muzzle origins; facing and all aim directions; flight and zoom; reload; sustained ammo/fuel; drop/re-pickup; death/respawn; crashes. Only after offline tests pass should two consenting phones test private LAN representations and shots.

GitHub release notes disclose the physical-test limits. The repository is now public and the release asset is available through the public download link. Only the final standalone APK and its checksum are uploaded, not the split set or older intermediate APKs.
