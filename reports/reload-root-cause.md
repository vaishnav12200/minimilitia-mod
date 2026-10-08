# Reload/ammunition investigation — 2026-10-08

The latest physical-device report supersedes earlier ammo/LAN success claims: fuel works, ammunition fails after manual reload, duplicate weapons and new LAN behavior are unverified.

## What the original binary actually does

The original ELF SHA-256 is `2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401`. The preserved combined ELF is `b8095e7d005c6b8c9b140a92968d9474a9963bee8ea96e491b4844e2a286b411`; its only modifications are the old `subAmmo` RET and the working fuel return. The analysis source and backup still match the original.

`Weapon::subAmmo(int)` has an integer return: it subtracts reserve first, then the clip, and returns the actual amount removed. Replacing its entry with `ret` preserves neither those writes nor a valid count in w0. This is an incorrect replacement, but the direct-call scan found **no direct BL calls** to this function. We cannot attribute the observed reload failure specifically to its undefined return. Indirect callers are not conclusively excluded.

Firing bypasses that patch. Eight direct clip-decrement stores occur in base/basic/default trigger paths and specialized EMP, M16, MINIGUN, PHASR and SAWGUN paths. Reserve lives at Weapon `+0x360`, clip at `+0x362`. Stock `getAmmo`/`getClip` simply return the signed halfword clamped to zero; they do not replenish anything. Network/state updates also call ordinary `setAmmo` and `setClip`. Preventing one subtraction function from running cannot maintain infinite ammunition across these paths.

Manual reload: HUD `onReload` starts the selected weapon's normal reload, including when its clip is full. Per-type reload implementations preserve their existing animation schedule. `completeReloadWeapon` clears reloading and resets the firing timer, computes `needed=max(capacity-clip,0)`, transfers `min(reserve,needed)`, writes the new clip/reserve through setters, and invokes the completion callback. No `subAmmo` call appears in this reload-completion body. Once the finite reserve is depleted, ordinary reload cannot restore shooting. This explains why the old implementation fails to provide infinite ammunition; the exact sequence that produced the user's disappearing bullets has not yet been reproduced on the phone.

## Correction

Restore the entire stock `subAmmo` function by replacing the obsolete first instruction with its original `sub sp,sp,#0x50`. Replace only the two 204-byte getter bodies with bounded ARM64 routines. When the weapon pointer matches localSoldier's primary (`+0x1c8`), secondary (`+0x1d0`), or simultaneous dual (`+0x1d8`) instance, call its existing virtual clip/reserve capacity, refill the corresponding physical halfword to a positive signed capacity, and return that same value. Zero/negative capacities, null local soldier, world weapons, and other soldiers retain ordinary zero-clamped reads. No arbitrary enormous ammo constants are used.

The pointer is resolved through the existing dynamic GOT relocation at ELF VA `0x13bec80`, verified to reference `localSoldier`. Capacity dispatch uses existing virtual offsets `+0x590` / `+0x588`. x19 and LR are saved, SP stays 16-byte aligned, and w0 contains the count. No new ELF segment or executable cave is introduced. The getter bodies and all patch ranges are checked against the exact original/combined hashes.

This leaves shot authorization, damage, cadence, projectile creation, setters, reload flags, animations, completion callbacks and networking code intact. Local reads replenish fields, so normal completion sees a full clip and does not drain it permanently. All weapons still use their own capacity. Automatic reload normally will not be needed because the clip stays usable; forced/manual reload still follows the existing state machine.

## Lifecycle coverage and limits

Factory creation, per-instance retain/release and separate slot allocations are stock. Initial ammo is assigned normally; reads start replenishing after the object becomes an equipped local instance. Switching swaps ordinary pointers and preserves eligibility for both slots. Dropping removes local-slot eligibility; the dropped object then uses stock reads. Picking up a distinct world object enables replenishment once stock addWeapon assigns the slot. Respawn recreates ordinary objects and refreshes the global localSoldier; no pointer is cached by the patch.

Host/client serialization, reload validation and remote WeaponStateObject counts remain stock. An authoritative update may change raw fields until the next local getter call. Specialized weapons may inspect raw fields before a getter runs; HUD/base getter cadence and every weapon's actual firing require physical-device checks. LAN may reflect finite authoritative ammunition even when local display is full: compatibility is not established by these patches.

## Evidence

- [Ghidra qualified reload export](../native-analysis/reload-fix-decompiled.txt), using the existing project without full reanalysis.
- [Verified mappings and vtables](reload-fix-evidence/native-audit.json).
- [Original instruction listing](reload-fix-evidence/native-disassembly.txt).
- [Direct calls and raw magazine stores](reload-fix-evidence/ammo-call-sites.json).
- [ARM64 emulation results](reload-fix-evidence/arm64-emulation.json): 105 synthetic scenarios, including actual original reload-completion instructions with capacity/setter/callback fixtures. This is not Android gameplay certification.
- Each build's `verification.json` contains every patch's full original/replacement bytes, virtual address, mapped file offset, purpose and assembly.
