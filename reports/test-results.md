USB installation update: the user-requested retry succeeded. The new duplicate inventory build is installed; its ARM64 split was read back and matches the verified build exactly. The launch command succeeded. Gameplay and LAN remain pending manual verification. Earlier storage failures below are historical.

# Latest user results and inventory candidate — 2026-10-08

**User-confirmed working on fixed_ammo_dual_weapon_splits:** unlimited ammunition, firing after manual reload, continuous jetpack boost, offline play, installation and launch. **User-confirmed failure:** two matching switchable weapons.

New candidate `duplicate_weapon_fixed_splits` is built and structurally verified, with 128 ARM64 slot-routing fixtures passing. The first USB installation attempt was blocked by insufficient internal storage (631 MB free); no new on-device gameplay success is claimed. See [duplicate-inventory-tests.md](duplicate-inventory-tests.md) for the exact manual matrix and current deployment result. All new inventory, gameplay regression and private LAN tests remain pending. Earlier agent observations below are historical; they do not override the latest user report.

# Device and gameplay test report — 2026-10-08

Current build: `fixed_ammo_dual_weapon_splits` / matching `mmc-fixed-ammo-dual-weapon.apk`. Latest user report supersedes older ammo/LAN results: unlimited fuel previously worked; ammo became unusable after manual reload; duplicate inventory and this build's LAN behavior were unverified.

## Actually performed

| Check | Result | Evidence / scope |
| --- | --- | --- |
| Original/combined ELF and fuel patch audit | PASS | Hashes, PT_LOAD mapping, original bytes |
| Corrected getter and original completion ARM64 emulation | PASS | 105 synthetic scenarios; not game simulation |
| Phase B package structural checks | PASS | Signed ammo/fuel splits and standalone |
| Combined package structural checks | PASS | Four splits and standalone; full payload comparisons |
| Native ZIP direct-loading requirements | PASS after correction | Uncompressed native, 4096-byte alignment |
| USB device | CONNECTED | Xiaomi M2010J19CI, Android 12, arm64-v8a |
| First compressed split installation | FAIL | INSTALL_FAILED_INVALID_APK; native extraction res=-2 |
| Initial standalone / corrected split attempts | BLOCKED then resolved | INSTALL_FAILED_USER_RESTRICTED until phone unlocked/approved |
| Corrected split installation | PASS | ADB install-multiple --no-incremental -r returned Success |
| Installed package/splits | PASS | pm path returns base + arm64 + en + xxhdpi |
| Installed ARM64 read-back | PASS | Pulled installed split matches built APK byte-for-byte |
| Game launch | PASS | am start MmcActivity; splash and Touch to Start screenshots |
| Automated gameplay input | BLOCKED | MIUI denies input tap: INJECT_EVENTS permission required |
| Runtime reload fix | NOT TESTED | No gameplay PASS inferred from install/launch |
| Duplicate inventory | NOT TESTED | Selection/pickup patches do not certify runtime ownership |
| Fuel regression in this build | NOT TESTED | Bytes preserved; previous user result only |
| Private LAN | NOT TESTED | One connected device; needs two consenting phones |
| Ad-free gameplay | NOT IMPLEMENTED | Existing advertising/access rules retained |

The user elected to perform gameplay tests manually after installation. [Device evidence](reload-fix-evidence/device-installation.json) records installation, launcher, running PID and installed split hash.

No uninstall, app-data clear, or system-security bypass was performed. Ads, licensing, public match validation and account authentication remain unchanged. Launching an offline mode, not public matchmaking, is the intended testing route.

## Offline manual sequence

Use the installed combined build. Start Training/Survival or an offline mode that supports your intended weapon/loadout. A random/default loadout mode may ignore saved choices under stock rules. Record model, Android version, weapon(s), mode, action, screenshot/video and PASS/FAIL.

1. Fire the starter weapon for at least 60 seconds. Confirm actual projectiles/damage and displayed ammo.
2. Press reload with a full magazine, wait for completion, then fire. Repeat after extended firing and while briefly partially used. Infinite refill may immediately restore the displayed magazine before a partial state can be captured.
3. Switch to the other weapon after reload, fire, reload it, then switch back. Confirm both remain usable.
4. Test Sniper + Sniper, Rocket + Rocket, Shotgun + Shotgun, Machine Gun + Machine Gun, and Pistol + Pistol; separately test Sniper + Rocket and Shotgun + Pistol in both slot orders. Verify two slot icons, separate visible instances, ordinary firing/switch animation and independent drops.
5. Walk to a second matching weapon, use ordinary pickup, switch and fire both copies. Test replacement when both slots are full. Dropping/picking up must preserve the other slot's usability.
6. Test EMP, M16 burst, MINIGUN, PHASR and SAWGUN individually, since specialized trigger/update code directly accesses magazine state. Existing damage/cadence should remain recognizable.
7. Die/respawn and repeat firing/reload/switch; restart and check loadout persistence. Do not assume selector choices alone prove spawn support.
8. Boost continuously for at least 30 seconds, land, boost again, shoot while flying, and switch weapons while boosting. Confirm no fuel regression.

Every scenario above remains pending unless a separate recorded runtime result is added. Failure after manual reload should be accompanied by the weapon name, before/after ammo display and whether reload animation completed.

## Private LAN manual sequence

Install the same combined version on both consenting devices and use isolated/private Wi-Fi. Host on A and join on B, then reverse roles. Verify ordinary and duplicate pairs, actual shots/damage, weapon switch/drop/pickup, death/respawn, ammo, and sustained boosting from both views. Record crashes, refused reloads, disappearing weapons and mismatched host/client counts. Stock authoritative WeaponStateObject and network setters remain finite/unmodified; local refill does not prove LAN consistency. Do not test this experimental package in public matches.

## Crash log collection

The deployment script does not clear logcat. After reproducing a problem, capture the relevant game/crash log rather than all unrelated phone logs:

```bash
adb logcat -d -b crash
adb shell pidof com.appsomniacs.mmc
# Substitute the returned game PID:
adb logcat -d --pid=GAME_PID
```

Screenshots of the game launch are in `reports/reload-fix-evidence/`. The temporary lock-screen diagnostic screenshot was deleted and is not a deliverable.


## Phase 5 pickup action separation — 2026-10-08

The preceding SPAS held pair is user-confirmed. The new two-action SPAS UI candidate is signed, installed and launched; 176 ARM64 cases and package checks pass. Physical SPAS action-selection PASS: user confirms both actions, both guns firing and buttons hiding. Broader regression is pending. A shared pair-policy sniper candidate passes 428 ARM64 cases and package checks; its installation was blocked by the disconnected phone. See [sniper extension](dual-wield-ui-sniper.md). Other gun classes/mixed pairs and LAN remain pending. See [Phase 5 evidence and manual checklist](dual-wield-ui-phase5.md).
