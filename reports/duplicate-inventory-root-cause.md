# Failed duplicate inventory: root cause before new patch

Date: 2026-10-08. The user confirms the current `fixed_ammo_dual_weapon_splits` build works for unlimited ammunition, firing after manual reload, continuous boosting and offline play. Duplicates fail. Preserve native SHA-256 `8cac1bfb7c7c523bbfbb2c33ea3c446acb2d8db24d0a639799b04d74b8026f60` as the working input; do not return to the old reload-bug build.

## Previous changes and missed equipment behavior

The previous patch changed four branches: LoadoutMenu primary/secondary index checks at ELF VA `0x69f3d4` and `0x69f514` now unconditionally reach their UI update paths. WeaponManager same-type primary/secondary checks at `0x9578c8` and `0x957980` now skip the ammunition-transfer/early-exit path and offer ordinary pickup. These affect selection and pickup eligibility. They do not change `SoldierLocalController::addWeapon`, which chooses the equipped slot.

`addWeapon` at ELF VA `0x8e6934`, size 1324, has two obstacles:

1. **Full inventory replaces the active instance before adding the incoming one.** With primary Sniper A, secondary Pistol B, and incoming Sniper C, the ordinary full-inventory path at `0x8e6df8` invokes `removePrimaryWeapon` (virtual `+0x418`) and then `addPrimaryWeaponRemoveDual` (`+0x690`). A is dropped and C replaces it; B remains. The result is still Sniper + Pistol. No weapon-type equality is tested here. Earlier equality-check changes cannot cause this path to preserve A.
2. **Pickup category flags can divert an ordinary dual-capable gun to simultaneous dual wielding.** After stopping its actions, the function tests incoming `pickupAsDual` (`+0x618`), `isDualWield` (`+0x5f8`) and `isDualWieldPrimaryOnly` (`+0x608`). Existing category/occupancy paths may add at `+0x440` (third/simultaneous dual slot), replace primary, or perform no ordinary-slot add. This does not guarantee two switchable primary/secondary slots.

Both behaviors were reproduced by executing the current binary's actual addWeapon instructions in Unicorn with virtual equipment/ownership callbacks modelled. [baseline-slot-routing.json](duplicate-inventory-evidence/baseline-slot-routing.json) records dropped pointers and final slot pointers. This is concrete control-flow evidence, not a claim of observing these exact cases on the user's phone.

## Verified slot assignment, ownership, switching and dropping

Primary `+0x1c8`, secondary `+0x1d0`, simultaneous dual `+0x1d8` are independently verified by loads/stores and vtable relocations. Ordinary `addPrimaryWeapon` (`0x8e6ebc`) / `addSecondaryWeapon` (`0x8e70b0`) assign separate object pointers, retain each, apply mods, set owner ID, bind separate sprite holders (`SoldierView +0x1e0` / `+0x1f8`), notify pickup, and configure active/stowed rendering. The base add helpers apply modifiers, not deduplication.

The corresponding removal methods (`0x8eade4`, `0x8eb12c`) notify/drop, detach rendering, release only the slot's object and clear that slot. `addPrimaryWeaponRemoveDual` (`0x8e6e60`) removes the third slot then calls ordinary primary add. `switchWeapons` (`0x8ebea0`) swaps primary/secondary pointers, stops actions and refreshes rendering; there is no same-type rejection. Instance lookup/drop compare UUID strings, not just ItemType.

Factory creators allocate distinct objects, even for matching numeric ItemTypes. Pickup passes the distinct world object to the local controller. The planned patch must never assign an existing held pointer again, and must use stock removal before replacing an occupied slot. Retain/release/rendering functions need not be rewritten.

## Loadout and respawn trace

LoadoutMenu stores primary/secondary numeric types separately. Serializers use `pw`/`sw` and distinct `pu`/`su` UUID fields. `ClientEntry::applyLoadout` copies the loadout and clears tracking; `ClientRoom::setLoadoutUUIDs` obtains a tracked instance independently for each slot. `SoldierManager::onSpawnData` parses the accepted loadout and saves it to WeaponFactory. `SoldierManager::spawnPlayer` (`0x8f11a4`) calls the factory independently for primary and secondary, applies each UUID and calls controller virtual `+0x430` / `+0x438` directly. It does not call addWeapon for those slots and does not compare the two types. The two identical type values therefore do not intrinsically collapse into one allocation in this path.

Respawn repeats this normal construction. Default/random or loadout-disabled modes can choose other equipment under existing configuration. No global validation, costs, account rules, database defaults or host checks will be bypassed. A reported saved-loadout failure would need its particular mode/selection sequence; the concrete pickup/assignment defects above are established regardless. The client/host/database parser helpers (`FUN_009f1d48`, `FUN_0096d11c`, `FUN_00700884`) independently read numeric `pw` into field +0x28 and `sw` into +0x2c. No equality collapse appears in these inspected paths. UUID strings are parsed separately. [Parser export](../native-analysis/duplicate-parser-decompiled.txt) records the actual helper bodies.

## Minimal targeted correction

Change only addWeapon's routing and ordinary two-slot block, retaining the rest of the working native file exactly:

- Route ordinary pickups through the existing dual-only classification guard, so dual-capable ordinary guns use two switchable slots. Dual-only equipment retains its existing dedicated path.
- Preserve the empty-primary and empty-secondary stock add behavior.
- With both ordinary slots full, compare incoming ItemType with the active primary. If matching, invoke stock switchWeapons first, then stock removePrimaryWeapon and addPrimaryWeaponRemoveDual. This drops the previous stowed weapon and retains the previous matching active instance as secondary. Otherwise retain stock active-primary replacement.
- Reject already-equipped identical pointers before ordinary slot assignment. Two identical types are allowed; the same object cannot acquire duplicate slot ownership.

The existing function stack frame and epilogue, original add/remove callbacks, allocation, UUIDs, sprites, animations and networking stay intact. The current ammo getters, subAmmo restoration, reload callbacks and fuel instructions are protected byte-for-byte. This remains an experimental inventory fix until actual device gameplay passes.

## Ghidra and ELF evidence

Reused the existing read-only analyzed project without full analysis. [duplicate-inventory-decompiled.txt](../native-analysis/duplicate-inventory-decompiled.txt) contains qualified controller/spawn functions and entry-point references. ELF program headers and dynamic vtable relocations are independently inspected; Ghidra addresses are ELF VA +0x100000. Full mapped patch bytes, branch targets, calling convention and preservation evidence will be written to the patch manifest before deployment.
