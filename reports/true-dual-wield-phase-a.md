# SPAS simultaneous dual-wield experiment — Phase A

The corrected goal is two actively held guns, one in each hand, both responding to shooting. Universal compatibility is **not complete**. This candidate enables the stock dual-hand path for a SPAS pair only. Physical visuals must pass before any class expansion or projectile changes.

## Preserved baseline

The user confirmed unlimited ammo, manual reload, fuel and offline play; the latest screenshot confirms two carried SPAS objects. This candidate layers on `duplicate_weapon_fixed_splits`, native SHA-256 `46e01584ccf9aafafe09c7d1601364ddc4d6158d762e14554830139550d23db4`. The complete carried build is preserved in `backup/true-dual-wield-20261008/`, with its hash manifest. Originals and existing working outputs are unchanged.

## Verified architecture and first blocked transition

Addresses below are ELF virtual addresses. For code in this library PT_LOAD maps these to equal file offsets. Ghidra displays these addresses with an additional 0x100000; scripts map the ELF independently.

| Function/field | Verified role |
|---|---|
| SoldierLocalController +0x1c8 | Primary held instance |
| +0x1d0 | Stowed/switchable instance |
| +0x1d8 | Second active held instance |
| addWeapon 0x8e6934 | Pickup routing; latest carried build jumps past ordinary dual routing at 0x8e698c |
| addDualWeapon 0x8e724c | Stores +0x1d8, retains incoming, sets owner/delegate, notifies pickup, configures and attaches it |
| SoldierView +0x1e0 / +0x1e8 | Primary and dual weapon attachment nodes; +0x1f0 is alternate dual attachment selected by Weapon +0x28a |
| updateStep 0x8e4d5c | Updates primary and dual aim/timers independently; activates view dual state when +0x1d8 is occupied |
| fire 0x8ec46c | Calls each non-null primary/dual weapon's triggerPull once, with the same input delta |
| SHOTGUN::triggerPull 0x8a3920 | Uses stock per-instance basicTriggerPull; no projectile change in candidate |
| Item::setHostDualConfiguration 0x67dd14 | Calls virtual +0x3d8; original SHOTGUN slot resolves to empty Item::setDualConfiguration 0x67dcf4 |
| SHOTGUN::setPrimaryConfiguration 0x8a3ca4 | Existing held gun transform, reused only for SHOTGUN dual slot |
| Weapon::getDesignFiringPoint 0x948eb8 | Uses the instance's local muzzle vector and node transformations to calculate world position |
| weaponDidFire 0x8ee648 | Distinguishes dual instance for recoil/aim and calls that same instance's doFire virtual |
| Weapon::doFire 0x948adc | Posts WeaponFired with the instance and firing data; unchanged |

SPAS is ItemType 9: factory jump table index 8 points to 0x94ff68, which calls PLT 0x4dd0f0; its GOT 0x13aabc8 resolves to SHOTGUN::create. SHOTGUN init uses `shotgun.png` and model type 9.

Weapon classification has actual flags +0x287 dual-only, +0x288 dual-capable, +0x289 primary-only and +0x28a alternate dual attachment. `WeaponStructures::isValidDualType` excludes type 9. No conceptual IsTwoHanded property was confirmed. Those global flags and valid-type tables are unchanged. The patch admits one explicitly checked pair at local pickup routing rather than disabling every classification restriction.

## Candidate changes

1. `addWeapon` branch at ELF/file 0x8e698c: original working `c8000014` becomes `01000014`, entering a SPAS guard in the original dual-routing region skipped by the carried build.
2. Starting ELF/file 0x8e6990, the guard rejects pointers already present in any slot. A distinct incoming type-9 instance, with type-9 active primary and empty dual slot, calls stock virtual +0x440 addDualWeapon. Primary and stowed instances remain owned as before. Other cases rejoin the existing carried routing at 0x8e6cac. Existing stack frame and epilogue are preserved; only caller-saved registers are used.
3. The SHOTGUN vtable +0x3d8 slot at ELF VA 0x134f9c8 gets a new ABS64 dynamic relocation target: SHOTGUN::setPrimaryConfiguration. It is a class-scoped rendering change, not a global Item change. The exact relocation file offset and original/replacement bytes are in `verification.json`.

The machine-code and relocation mutations are restricted to these three spans. Full bytes and assembly are recorded in build `verification.json` and `reports/dual-wield-evidence/package-verification.json`. Ownership uses the stock retained dual instance; no allocations, releases, shared gun pointers or projectile callbacks are added. The distinct pointer guard prevents reacquiring an already owned weapon. An occupied dual slot follows existing inventory behavior rather than overwriting a live pointer.

All ammo getters, subAmmo/manual-reload, fuel, projectile, damage, network, input and animation functions are byte-identical to the working build. Other weapon classes keep carried-slot behavior. The shared SHOTGUN transform also applies if a remote SHOTGUN enters its stock dual slot; private LAN behavior remains untested.

## LAN findings and limits

`SoldierRemoteController::addDualWeapon` at 0x8f5a18 stores +0x1d8, retains it, invokes the same +0x3d8 configuration and attaches it to the dual hand. Remote updateStep at 0x8f3bf8 updates dual aiming/weapon step and view state when that slot is occupied. This confirms an existing remote representation, not end-to-end synchronization. `ClientRoom::updateWeaponTracking` tracks ammo, but a full pickup/slot packet round trip is not yet proven. No transport, authentication or server protections are changed. Phase E requires two consenting phones on private Wi-Fi after local SPAS verification.

## Validation and known pending work

Package verification: PASS signatures (existing certificate), alignment, uncompressed split native libraries, 4096-byte native offsets, CRC, exact native bytes and identical other application payloads.

127 ARM64 cases: PASS real addWeapon machine-code routing, distinct ownership fixture, alias rejection, occupied dual fallback, non-SPAS inventory preservation, and unchanged fire dispatch calling each held instance once. Virtual ownership callbacks are simulated. This is not Cocos rendering or Android projectile evidence.

| Required physical result | Status |
|---|---|
| Two SPAS visible in separate hands | NOT TESTED |
| Both guns fire / two muzzle origins | NOT TESTED |
| Aim all directions / facing flips | NOT TESTED |
| Jump, flight and animations | NOT TESTED |
| Manual reload preserves firing | NOT TESTED; previous fix preserved |
| Drop/pickup / death/respawn | NOT TESTED |
| No gameplay crashes | NOT TESTED |
| Unlimited ammo and fuel regression | NOT TESTED; exact working code preserved |
| Private LAN | NOT TESTED |

Important Phase C findings: stock switchWeapons can remove the dual gun when switching to a non-dual-capable stowed gun. HUD onReload explicitly targets the primary only. This candidate does not yet change these behaviors. Saved carried SPAS pairs are not automatically moved to the dual slot on spawn: activate this experiment by picking up a new second SPAS while one SPAS is active. Do not treat two active pointers as proof of visual correctness.

## Deployment and test sequence

Latest retry: **installation succeeded**. All four split paths were confirmed, installed ARM64 APK matches the candidate byte-for-byte, and the game launch command succeeded. Manual gameplay remains pending. The two earlier storage refusals below are history.

USB device `241266d60c20` is connected. Both initial update and user-requested retry failed with `INSTALL_FAILED_INSUFFICIENT_STORAGE`. After the retry Android reported only 591 MB free. No uninstall or data clear was issued. `pm path` and `pm list packages -u` currently return no game package, so previous device installation/data preservation cannot be confirmed. Workspace working APK backups are verified intact. Free another 1–2 GB and retry:

```bash
./scripts/deploy_true_dual_wield.sh 241266d60c20
```

Standalone APK: `builds/universal_dual_wield_standalone/mmc-spas-true-dual-wield-phase-a.apk`.

1. Start offline, equip one SPAS as active, then pick up another SPAS from the map. Verify one gun in each hand. A back-mounted gun does not pass.
2. Aim up/down/left/right and turn both ways. Report orientation, overlap or detached gun problems. This is the Phase A gate.
3. Once visuals pass, shoot and verify separate muzzle origins and SPAS pellet behavior, then test flight/reload/drop/death. Existing stock firing is already available; no new projectile code is introduced.
4. Expand sniper, rocket, machine gun and mixed pairs individually only after the SPAS checks pass. Then validate LAN.

Rollback uses `./scripts/deploy_duplicate_inventory.sh 241266d60c20`, preserving data and the working corrected-ammo carried build. Do not use the obsolete RET-ammo combined build.

Reproduce structural verification with `python3 scripts/build_true_dual_wield.py --verify`; ARM64 fixtures with `PYTHONPATH=/tmp/mmc-unicorn-tests:scripts python3 scripts/test_true_dual_wield_arm64.py`. Builder refuses overwrite. Read-only Ghidra exports: `true-dual-wield-decompiled.txt`, `dual-detail-decompiled.txt`, `dual-network-decompiled.txt` in native-analysis.

Native candidate SHA-256: `b6f87aed1e1898c55b726720d6cb45d0796d54177ce94ed0be2c64d889262102`.
Standalone APK SHA-256: `2c0f9ab0fb6d76a13688f8efd9094b7dd2ab0424506df1330ca121770d41ad57`.
