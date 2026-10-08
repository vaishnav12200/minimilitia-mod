# Latest equipment-routing findings — 2026-10-08

The preceding selector/proximity patch failed to guarantee two actual slots. Stock addWeapon replaces primary when both slots are full, discarding the matching active gun, and may route dual-capable ordinary guns to +0x1d8 instead of switchable secondary +0x1d0. The new patch is confined to addWeapon: ordinary two-slot routing, preserving matching primary before full replacement, and guarding identical pointers. Factory/retain/release/rendering/UUID/spawn logic are unchanged. Client/host/database parsers read pw/sw separately; spawn independently creates both instances. See [root cause](duplicate-inventory-root-cause.md) and [native audit](duplicate-inventory-evidence/native-audit.json). Earlier investigations below are historical and superseded where they describe picker-only/current build status.

# Current correction status — 2026-10-08

The historical picker-only experiment below is superseded by `scripts/patch_fixed_gameplay.py --duplicates`. The new combined build also changes same-type pickup branches at ELF VA `0x9578c8` and `0x957980` to unconditional branches to the existing next-check blocks (`0x957944`, `0x9579f4`). Original comparisons and branch bytes are strictly validated. Primary/secondary same-type incoming guns now follow ordinary pickup instead of the ammo-transfer exit. Allocation, ownership, UUID creation, switching, host validation and simultaneous dual restrictions are untouched. Picker branches remain those previously audited. This supports ordinary listed guns structurally; actual duplicate gameplay still requires testing. Dual-only utilities, throwables, objective objects and paid loadout access remain under existing rules.

# Phase 4 — weapon restrictions, ownership, and LAN synchronization

Date: 2026-10-08. Target: Mini Militia Classic 0.14.4 / version code 88, ARM64.

This is static analysis plus an experimental build, not a validated two-weapon implementation. No connected Android devices were available. Addresses below are ELF virtual addresses/file offsets, independently mapped through PT_LOAD. The existing Ghidra project adds `0x100000` to these addresses. Ghidra output has inaccurate signatures and sometimes includes adjacent exception paths; the ELF disassembly controls patch decisions.

## Inventory and selection

Verified fields in `SoldierLocalController`:

| Offset | Meaning | Evidence |
|---|---|---|
| `+0x1c8` | Active primary Weapon pointer | `addPrimaryWeapon` writes and retains it; `switchWeapons` swaps it |
| `+0x1d0` | Stowed secondary Weapon pointer | `addSecondaryWeapon` writes and retains it; `switchWeapons` swaps it |
| `+0x1d8` | Simultaneous dual-wield Weapon pointer | `addDualWeapon`, primary-to-dual transitions |

The two inventory slots differ from simultaneous dual wielding. The requested sniper/sniper combination is two switchable weapons, not two sniper rifles firing simultaneously.

| Function | ELF address/file offset | Finding |
|---|---|---|
| `SoldierLocalController::addWeapon` | `0x8e6934` | Category-dependent routing based on Weapon virtual calls |
| `addPrimaryWeapon` | `0x8e6ebc` | Stores pointer, retains, applies mods, player ID and sprite configuration |
| `addSecondaryWeapon` | `0x8e70b0` | Separate pointer, retain, ID and stowed sprite configuration |
| `switchWeapons` | `0x8ebea0` | Swaps primary and secondary pointers, refreshes rendering; no type-equality rejection observed |
| `removePrimaryWeapon` | `0x8eade4` | Drop physics, notifications and reference-release path |
| `removeSecondaryWeapon` | `0x8eb12c` | Separate removal path |
| `dropWeaponByID` | `0x8e8184` | Compares string instance identifiers, not simply weapon types |
| `LoadoutMenu::onPrimary` | `0x69f2a0` | Cycles list, handles wrap, skips dual-only and equal secondary index |
| `LoadoutMenu::onSecondary` | `0x69f410` | Same list, skips dual-only and equal primary index |
| `LoadoutMenu::getLoadoutObject` | `0x6a652c` | Independently writes type fields `+0x28`, `+0x2c`, `+0x30` |
| `LoadoutMenu::updateState` | `0x6a7624` | Draws primary/secondary separately; keeps third-slot dual checks and cost display |
| `LoadoutLayer::testValid` | `0x697f70` | Checks selected loadout list bounds; not a weapon-equality check |

Both ordinary slot selectors use `WeaponStructures::getLoadoutWeaponList()`. No rifle-versus-handgun restriction was found in these two selectors. The explicit equality restriction is a list-index comparison followed by recursive advancement:

- Primary `0x69f3d4`: `a1000054`, `b.ne 0x69f3e8`.
- Secondary `0x69f514`: `a1000054`, `b.ne 0x69f528`.

The experiment replaces each with `05000014` (`b` to the same destination). It retains list bounds, null handling, category checks, costs, special-item rules, and all instance construction. It permits equal indices to reach the ordinary UI update path. Whether saved duplicates survive all game modes requires device testing.

Weapon virtual methods independently resolved through ELF dynamic relocations:

| Weapon vtable slot | Method | Flag offset |
|---|---|---|
| `+0x5f8` | `Weapon::isDualWield` (`0x948818`) | `+0x288` |
| `+0x600` | `Weapon::isDualWieldDualOnly` (`0x948838`) | `+0x287` |
| `+0x608` | `Weapon::isDualWieldPrimaryOnly` (`0x948858`) | `+0x289` |
| `+0x618` | `Weapon::pickupAsDual` | Existing pickup choice |

The experiment does not make dual-only equipment into ordinary weapons or add throwables/objective items to the weapon list. Such objects may lack ordinary rendering/firing behavior. Literal “every existing item in either slot” remains unimplemented. No entitlement or weapon-cost restrictions were removed.

## Instances and ownership

`WeaponFactory::createWeaponFromAmmoType` (`0x94feac`) dispatches to per-type `create()` functions. Directly inspected creators allocate fresh objects:

- `SHOTGUN::create` (`0x950aa4`): `operator_new(0x3d0)`, constructor/init, autorelease.
- `M93BA::create` (`0x950de4`): `operator_new(0x3d8)`, constructor/init, autorelease.
- `ROCKET::create` (`0x950eb4`): `operator_new(1000)`, constructor/init, autorelease.

This supports separate instances for matching types; the patch never copies a pointer between slots. Local add methods retain the object and configure a separate sprite holder. Existing remove methods release their slot reference. `WeaponManager::addItem` (`0x95828c`) uses a host ID plus an incrementing counter (`%s:%d`) to assign new instance UUIDs and keys its dictionary by UUID.

These findings provide a reason to test a picker-only patch. They do not prove absence of aliasing, allocator failures, stale references, or sprite problems across every spawn/respawn path. Per-type render overrides, the complete client spawn dispatch, and live pointer/UUID uniqueness remain unverified.

## World pickup behavior and limitation

`WeaponManager::weaponProximity` (`0x9576c0`) checks the incoming type against primary, secondary and dual weapons. For an already-held non-dual type it can transfer ammunition and exit before offering pickup. Thus the picker experiment does **not** enable acquiring a second ordinary sniper/rocket simply by walking over another copy.

The existing path is proximity → `WeaponCollisionBegan` → `onPickUpWeapon` (`0x955ef4`) → local controller vtable `+0x5b0` (`addWeapon`). `onPickUpWeapon` updates pickup flags/ammo state and forwards the distinct world object. Add/remove notifications feed `itemCreate`, `itemDrop`, `itemPickup` and `itemRemove`.

The same-type world pickup rule and ammo initialization are unchanged. Collecting a different weapon while holding duplicates, dropping either UUID, switching repeatedly, and respawning are mandatory tests. Changing proximity rules before those tests would introduce a second unvalidated inventory change.

## Loadout database and serialization

The actual packaged database `decoded/assets/mmcDatabase.sqlite` contains an empty `loadout` table:

```sql
CREATE TABLE "loadout" (
 "load_id" INTEGER,
 "json" VARCHAR DEFAULT (null),
 "dirty" INTEGER DEFAULT 0,
 "edit" INTEGER DEFAULT 0,
 PRIMARY KEY("load_id")
);
```

No rows were inserted. No runtime application database was accessible.

The `json` column is not necessarily raw JSON. The inspected database callback (Ghidra `0x6faf48`, ELF `0x5faf48`) calls `base64StringDecode`, an additional transform (`FUN_006fef80`), and a parser (`FUN_00700364`). The database writer also applies a transform and base64 encoding. Those transforms have not been fully decoded; direct record editing would be unsafe.

The inspected JSON serializer (Ghidra `0x6f8aec`, ELF `0x5f8aec`) and spawn serializer (Ghidra `0x962e1c`, ELF `0x862e1c`) use the following actual keys:

| Key | Native field | Meaning |
|---|---|---|
| `pw` | `LoadoutObject +0x28` | Primary numeric ItemType |
| `sw` | `+0x2c` | Secondary numeric ItemType |
| `dw` | `+0x30` | Third-slot numeric ItemType |
| `pu` | `+0x38` | Primary string UUID |
| `su` | `+0x68` | Secondary string UUID |
| `du` | `+0x50` | Third-slot string UUID |

Equal numeric values can be represented separately by the writer; identical UUID strings must not be reused. The full deserializer and runtime validation order remain unverified.

`DatabaseInterface::initDB(bool)` copies the packaged database when the runtime database is absent or reset is requested, rather than unconditionally on every launch. `loadDefaultLoadouts()` explicitly removes existing loadouts before inserting defaults, and `insertLoadoutsToDatabase()` also replaces rows. Call conditions and account/cloud overwrite behavior require runtime observation. Editing the packaged empty database would not reliably change an installed player's current loadouts.

## Private LAN

`ClientRoom::validateLoadout` is actually at ELF/file `0x8596ac` and already returns true in the original. It was **not patched**. That fact does not prove every subsequent host check accepts duplicate weapons.

`ClientEntry::applyLoadout` (`0x8628d8`) copies the loadout into `ClientEntry +0x2a0` and clears weapon tracking. `ClientRoom::setLoadoutUUIDs` (`0x83a5d4`) separately requests state objects for primary, secondary and dual ItemTypes; it writes UUIDs into `ClientEntry +0x2d8`, `+0x308`, and `+0x2f0`. Host weapon-state creation is invoked independently per slot. Complete tracker implementation and live UUID uniqueness remain to be checked.

`spawnPlayerWithLoadout` uses the original loadout/application/UUID path and serialized spawn payload. Weapon tracking uses UUID string keys. Packet formats, reconciliation, damage, projectiles, authentication, and public validation remain unchanged. No public-server behavior was tested.

Use compatible experimental packages on **both consenting devices** on an isolated Wi-Fi network. Test each device as host, switch/fire/drop each duplicate separately, inspect both views, then respawn and reconnect. Check UUIDs if legitimate debugging access permits, and compare received weapon changes, projectile behavior, damage and crashes. A successful build is not evidence of synchronization. All LAN runtime tests are BLOCKED pending two devices.

## Evidence and reproduction

- `scripts/analyze_phase4.py`: ELF PT_LOAD mapping, working-patch comparison, symbols, vtables and Capstone disassembly.
- `reports/phase4-evidence/native-audit.json` and `native-disassembly.txt`: concrete addresses, bytes and resolved calls.
- `native-analysis/phase4-qualified-decompiled.txt`: named picker, database and loadout paths.
- `native-analysis/phase4-ownership-decompiled.txt`: allocations, pickup paths and serializers.
- `native-analysis/ghidra_scripts/ExportPhase4*.java`: reproducible read-only exports.

The Ghidra project is the original unmodified library. The combined and experimental images are checked separately by full-file comparison against that library plus the explicit patch set.


## Phase 5 pickup action separation — 2026-10-08

The preceding SPAS held pair is user-confirmed. The new two-action SPAS UI candidate is signed, installed and launched; 176 ARM64 cases and package checks pass. Physical SPAS action-selection PASS: user confirms both actions, both guns firing and buttons hiding. Broader regression is pending. A shared pair-policy sniper candidate passes 428 ARM64 cases and package checks; its installation was blocked by the disconnected phone. See [sniper extension](dual-wield-ui-sniper.md). Other gun classes/mixed pairs and LAN remain pending. See [Phase 5 evidence and manual checklist](dual-wield-ui-phase5.md).
