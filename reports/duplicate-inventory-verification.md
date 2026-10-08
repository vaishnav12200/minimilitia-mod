USB installation update: the user-requested retry succeeded. The new duplicate inventory build is installed; its ARM64 split was read back and matches the verified build exactly. The launch command succeeded. Gameplay and LAN remain pending manual verification. Earlier storage failures below are historical.

# Inventory-only patch verification — 2026-10-08

The new experimental build is `builds/duplicate_weapon_fixed_splits/`, with standalone `builds/duplicate_weapon_fixed_standalone/mmc-duplicate-weapon-fixed-experimental.apk`. Static verification and 128 ARM64 slot-routing/ownership fixture cases PASS. On-device duplicate gameplay is not yet verified.

## Exact mutation

Input native SHA-256: `8cac1bfb7c7c523bbfbb2c33ea3c446acb2d8db24d0a639799b04d74b8026f60`, read directly from the user's confirmed working corrected-ammo build.

Output native SHA-256: `46e01584ccf9aafafe09c7d1601364ddc4d6158d762e14554830139550d23db4`.

| Function/site | ELF VA | Actual file offset | Original/replacement |
| --- | --- | --- | --- |
| addWeapon pickup-dual branch | 0x8e698c | 0x8e698c | `00190036` (tbz) → `c8000014` (b), same target 0x8e6cac |
| addWeapon ordinary slot block | 0x8e6d50 | 0x8e6d50 | Original 260 bytes → 228-byte routine + 32 bytes NOP padding |

Both changes lie inside the verified 1324-byte `SoldierLocalController::addWeapon(Weapon*)` at ELF VA `0x8e6934`. The original function body is verified equal to the original backup before modification. Every original/replacement byte, assembly source, purpose, preserved-function hash and mapped offset is recorded in [package-verification.json](duplicate-inventory-evidence/package-verification.json).

The original stack prologue/epilogue are retained. x29 remains the frame pointer; original saved this/incoming pointers at x29-0x18/-0x10 are reused. Only caller-saved registers x0/x1/x8/x9/x10 are used; comparison state is saved at an existing scratch word [sp], below the saved locals. All calls pass x0=controller or weapon as appropriate, and x1=incoming for stock add methods. Return type remains void, SP remains aligned and original LR is restored.

Controller virtual slots are independently verified via dynamic ELF relocations: +0x418 removePrimaryWeapon, +0x438 addSecondaryWeapon, +0x5b8 switchWeapons, +0x690 addPrimaryWeaponRemoveDual. Weapon virtual +0x520 is **getType**, which reads the same ItemType field (+0x338) as getAmmoType. The new comparison uses the actual getType slot, matching stock weaponProximity's type comparison; it does not compare UUID or pointer equality as a substitute for type equality.

No new allocation, reference-count implementation, sprite code or ELF segment is added. Existing functions retain/release distinct objects and switch/drop by instance. The ordinary block explicitly rejects an incoming pointer already present in any equipped slot, preventing duplicate slot ownership from repeated events. It permits separate objects with equal types.

## Preserved working features

Full-file mutation-scope verification proves every byte outside the two addWeapon ranges is identical to the working input, including:

- Corrected getClip/getAmmo routines: all 204 bytes each.
- Restored subAmmo: entire function.
- Fuel entry: all existing 8 bytes.
- Manual reload start/completion, shooting and projectile functions, factory allocation, slot add/remove methods, switch rendering, saved-loadout/spawn construction and public/network validation.
- Previous four selector/proximity branches.

The working build's unlimited ammo, post-reload firing, continuous boost and offline play were **user-confirmed before this patch**. Runtime regression in the new inventory build remains pending; byte preservation is not substituted for gameplay testing.

## Package checks

All four required splits and standalone pass apksigner verification, zipalign checks, ZIP CRC, exact native-byte comparison and non-native payload comparison with the working containers. Split native libraries are uncompressed and their ZIP data offsets are aligned to 4096 bytes. Manifests, DEX, resources, assets and other library contents are unchanged.

Certificate SHA-256: `a19c717feeee28b67070bfd3e1f6f519785d804c68e39e55be59710e55451f5e`, same test certificate across all outputs and the working build.

Standalone APK SHA-256: `44dc2350fec0c1696fb18a879bcac84206cb4435dc50329ac35958134be7da66`.

The builder never invokes baseline restoration or old ammo/fuel patch scripts. Output directories must be absent; it refuses overwrite. [build_duplicate_inventory.py](../scripts/build_duplicate_inventory.py) `--verify` independently checks existing artifacts against reproduced native bytes, saved hashes and preserved payloads.

## Execution evidence and limits

Baseline ARM64 execution demonstrates active matching-gun replacement and third-slot routing. Patched execution tests empty/partial/full inventory, matching active/stowed types, different types, dual capability and priority flag combinations, duplicate-pointer rejection, null input, preserved dual-only path, and incorrect-input rejection. All 128 fixtures pass. Virtual callbacks model stock ownership; actual Cocos rendering, firing, respawn and LAN are not emulated.

Read-only Ghidra exports reuse the existing analyzed project; no full ELF reanalysis is performed. [native-audit.json](duplicate-inventory-evidence/native-audit.json), [disassembly](duplicate-inventory-evidence/native-disassembly.txt), [baseline cases](duplicate-inventory-evidence/baseline-slot-routing.json), [patched cases](duplicate-inventory-evidence/patched-slot-routing.json) and verbose signature logs record the checks.

Android initially refused installation with `Requested internal only, but not enough space`. The phone reported only 631 MB free; Android can require additional space above a low-storage threshold for an update. No app was uninstalled and no data/cache was deleted. Final deployment status is recorded in the device test report.

Device storage follow-up: 572 MB free, so installation remains blocked. [Device evidence](duplicate-inventory-evidence/device-installation.json) records the exact failure; the existing working app is retained.
