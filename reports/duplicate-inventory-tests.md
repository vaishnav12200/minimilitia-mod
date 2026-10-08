# Duplicate inventory device test plan/results — 2026-10-08

Working baseline: `fixed_ammo_dual_weapon_splits`. User-confirmed PASS: unlimited ammunition, shooting after manual reload, continuous boost, offline play, installation and launch. Duplicate support FAIL on that baseline.

New candidate: `duplicate_weapon_fixed_splits` / `mmc-duplicate-weapon-fixed-experimental.apk`. Native hash `46e01584ccf9aafafe09c7d1601364ddc4d6158d762e14554830139550d23db4`.

## Performed checks

| Check | Actual result |
| --- | --- |
| Original/working native hashes and slot/vtable mappings | PASS |
| Baseline failed slot routing in ARM64 fixtures | Reproduced active replacement and third-slot routing |
| Patched ARM64 control flow and ownership fixtures | PASS: 128 cases; virtual callbacks modelled |
| Exact working gameplay-byte preservation | PASS |
| Split/standalone signatures, storage/alignment, CRC, native and payload checks | PASS |
| USB phone connection | PASS: Xiaomi M2010J19CI, Android 12, ARM64 |
| First new-build installation attempt | BLOCKED: insufficient internal storage, install-create refused |
| USB installation retry | PASS: install-multiple returned Success |
| Installed ARM64 split read-back | PASS: identical to verified build |
| Launch command | PASS: am start accepted |
| Free storage at that attempt | 631 MB available, /data 99% used |
| New inventory gameplay | NOT TESTED |
| New ammo/reload/fuel regression | NOT TESTED; baseline features user-confirmed |
| New private LAN | NOT TESTED; two consenting devices required after local success |

Device input automation was previously denied by MIUI (INJECT_EVENTS). If that restriction persists, manual tests are required. No result is marked PASS merely because a package builds or installs.

## Manual tests

Use an offline mode with the intended weapon pickups. Do not use public matchmaking. Record mode, current active/stowed weapons, incoming pickup and final two slots; a screenshot of the selector alone does not prove functional inventory.

| Test | Procedure and expected result | New-build status |
| --- | --- | --- |
| Sniper + Sniper | Hold Sniper active + a different stowed gun. Pick up another Sniper. Different gun drops; both distinct Snipers remain. Switch and fire each. | PENDING |
| Rocket + Rocket | Repeat with two Rocket instances; each switches, renders, fires normal projectiles and reloads. | PENDING |
| Shotgun + Shotgun | Repeat; both copies remain in switchable slots. | PENDING |
| Machine Gun + Machine Gun | Repeat with the same exact machine-gun type, checking extended shooting. | PENDING |
| Pistol + Pistol | Repeat; ordinary two-slot support should avoid forcing the new pistol into simultaneous dual wielding. | PENDING |
| Matching stowed gun | Hold Pistol active + Sniper stowed, then pick up Sniper. Pistol drops; two Snipers remain. | PENDING |
| Sniper + Rocket | Equip both in either order; switch, render and fire both. | PENDING |
| Switching | Switch at least 20 times; both icons/sprites and actual selected weapon stay consistent. | PENDING |
| Dropping | Drop one of two matching guns. Other instance stays usable; pick the dropped gun back up and switch/fire. | PENDING |
| Full-inventory replacement | With two different guns, incoming different type retains stock active-slot replacement. With incoming matching active type, previous stowed gun is replaced so the matching active instance is preserved. | PENDING |
| Manual reload | Reload each copy, wait for completion and fire; repeat after long shooting. | PENDING |
| Continuous shooting | Fire each slot for at least 60 seconds, checking actual shots and ammo display. | PENDING |
| Continuous boost | Boost at least 30 seconds; shoot and switch while flying; land and boost again. | PENDING |
| Respawn | Save/select duplicate loadout in a mode that supports it; die and respawn, switch and fire both. Also test normal stock/default-loadout modes separately. | PENDING |
| Restart/persistence | Restart, reopen saved loadout and spawn; verify both numeric type choices survive and actual guns work. | PENDING |

The patch changes pickup slot routing. Spawn already creates separate primary/secondary instances and is unchanged. If duplicates selected in the editor still disappear before/at spawn, report that mode and the exact before/after choices; do not assume a pickup test proves saved-loadout behavior.

## Private LAN

Only after local inventory succeeds: use two consenting physical phones on private Wi-Fi with this same version. Reverse host/client roles and verify duplicate pickups, switching, drops, respawn, normal projectiles/damage, ammo and boost from both views. Packet formats, UUID creation and host validation remain stock. Inventory notifications may interact with authoritative equipment tracking; structural preservation alone does not establish synchronization. Every LAN scenario remains NOT TESTED.

## Installation and rollback

After freeing internal storage, unlock the phone and approve USB install:

```bash
./scripts/deploy_duplicate_inventory.sh 241266d60c20
```

Alternative standalone installer:

```bash
adb install --no-incremental -r builds/duplicate_weapon_fixed_standalone/mmc-duplicate-weapon-fixed-experimental.apk
```

Rollback to the **current corrected-ammo/fuel working build**, without uninstalling or clearing data:

```bash
./scripts/deploy_fixed_gameplay.sh 241266d60c20
```

The working split/standalone files and pre-inventory documentation are preserved under `backup/duplicate-inventory-20261008/` with hashes. Do not roll back to the old `combined_mod_splits`, which retains the reported reload bug. Existing saved loadout data can persist across code rollback.

Device storage follow-up initially showed 572 MB free. The user later requested a retry, which installed successfully. [Device evidence](duplicate-inventory-evidence/device-installation.json) records the exact failure; the existing working app is retained.
