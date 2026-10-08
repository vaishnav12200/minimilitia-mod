# Mini Militia Classic — Phase 5 two-action pickup test

[Two-action SPAS APK](builds/universal_dual_wield_ui_standalone/mmc-spas-two-action-pickup-experimental.apk) · [signed split set](builds/universal_dual_wield_ui_splits/) · [root cause, call graphs and test checklist](reports/dual-wield-ui-phase5.md).

The user confirms the prior SPAS + SPAS held pair works. This candidate separates **Swap** (normal pickup) from **Dual** (keep the active SPAS and equip another in the opposite hand), reusing both stock icons and touch handlers. The verified SPAS rendering and ammo/reload/fuel code are preserved.

176 ARM64 cases and structural package checks pass. Installed successfully; the installed ARM64 split matches the package and launch succeeded. **Physical SPAS Test A passed:** both actions work, both guns fire, buttons hide. This is not a completed universal build. [Sniper candidate APK](builds/universal_dual_wield_ui_sniper_standalone/mmc-two-action-sniper-experimental.apk) adds the M93BA sniper same-class pair using shared eligibility policy; mixed pairs and other classes are not enabled yet. Its 428 ARM64 checks and package verification pass. It has not been installed: ADB found the phone disconnected. See [sniper investigation and test checklist](reports/dual-wield-ui-sniper.md). When already dual wielding, Dual is disabled and Swap follows the existing drop rules.

Update using `./scripts/deploy_dual_wield_ui.sh 241266d60c20`. Roll back using `./scripts/deploy_true_dual_wield.sh 241266d60c20`. Neither script uninstalls or clears data. The exact working SPAS outputs are preserved in `backup/dual-wield-ui-20261008/`.

Earlier build history follows.

# Mini Militia Classic — simultaneous dual-wield experiment

Latest requirement: two active held guns, one in each hand. A **Phase A SPAS-only candidate** is ready; universal compatibility and physical gameplay are not yet verified. The working carried-duplicate build is preserved.

[Download SPAS Phase A APK](builds/universal_dual_wield_standalone/mmc-spas-true-dual-wield-phase-a.apk) · [split set](builds/universal_dual_wield_splits/) · [patch evidence and manual test sequence](reports/true-dual-wield-phase-a.md).

127 ARM64 routing/fire-dispatch fixture cases and package checks pass. USB installation succeeded on the third attempt. The installed ARM64 split matches the build byte-for-byte, and the game launch command succeeded. Deployment script: `./scripts/deploy_true_dual_wield.sh 241266d60c20`. Ammo/reload/fuel code is unchanged. Pick up a second SPAS while a SPAS is active to exercise the new hand attachment. Physical SPAS validation is required before expanding to other guns.

The prior carried-slot implementation and its history follow.

# Mini Militia Classic — duplicate inventory test build

Package `com.appsomniacs.mmc`, version 0.14.4 (88), ARM64, updated 2026-10-08.

The user confirms `fixed_ammo_dual_weapon_splits` works for unlimited ammo, firing after manual reload, continuous boosting and offline play. Duplicate weapons still fail. That exact working build is preserved; the new inventory candidate changes only `SoldierLocalController::addWeapon` and retains all working ammo/reload/fuel bytes.

## New candidate APK

[mmc-duplicate-weapon-fixed-experimental.apk](builds/duplicate_weapon_fixed_standalone/mmc-duplicate-weapon-fixed-experimental.apk)

SHA-256: `44dc2350fec0c1696fb18a879bcac84206cb4435dc50329ac35958134be7da66`.

Matching four-split set: [duplicate_weapon_fixed_splits](builds/duplicate_weapon_fixed_splits/). Native SHA-256: `46e01584ccf9aafafe09c7d1601364ddc4d6158d762e14554830139550d23db4`.

Static package checks and 128 ARM64 slot-routing/ownership fixture cases pass. **New duplicate gameplay is not yet verified.** The first USB update was refused for insufficient storage. After the user freed space, the retry succeeded; the new inventory build is installed and its installed ARM64 split matches the built APK byte-for-byte. The game launch command succeeded. Final deployment status and manual checks are recorded in [duplicate-inventory-tests.md](reports/duplicate-inventory-tests.md).

## What changed

The previous selection/pickup eligibility patch left actual equipment routing unchanged. With Sniper active + Pistol stowed, a second Sniper replaced the active Sniper, leaving Sniper + Pistol. The new ordinary-slot routine switches before that matching full-inventory replacement, so it drops the old stowed Pistol and retains two distinct Sniper instances. Matching-stowed pickups and unrelated pickups retain ordinary active-slot replacement. Empty slots still use stock add methods.

Ordinary dual-capable firearms now use the two switchable inventory slots; dedicated dual-only equipment retains its existing guarded path. The same object pointer is never assigned again to another ordinary slot. Stock instance allocation, retain/release, UUIDs, rendering, firing, switching and respawn construction are preserved. This targets ordinary supported guns, not throwables/objective equipment. No payment, account, host validation, advertising, damage, projectile or map changes were added.

The replacement is limited to one existing addWeapon branch and its 260-byte ordinary block. Full original/replacement bytes, verified mappings and calling convention are in each build's `verification.json`.

## Install and test

Free enough internal storage, unlock the phone, and approve the USB prompt. Update without uninstalling or clearing data:

```bash
./scripts/deploy_duplicate_inventory.sh 241266d60c20
```

Or copy/open the standalone APK on the phone, or install it via ADB:

```bash
adb install --no-incremental -r builds/duplicate_weapon_fixed_standalone/mmc-duplicate-weapon-fixed-experimental.apk
```

Base.apk alone is insufficient for split installation. The deployment script verifies and installs all four components together with the same existing test certificate/version. If Android refuses installation, retain the working app and record the error. Do not uninstall or erase data as a workaround.

Test offline first: Sniper + Sniper, Rocket + Rocket, Shotgun + Shotgun, Machine Gun + Machine Gun, Pistol + Pistol, and Sniper + Rocket. Verify both slots by switching and shooting; reload both, drop/pick up one independently, test full replacement, then die/respawn. Retest ammo and sustained boost. See the [detailed matrix](reports/duplicate-inventory-tests.md). MIUI previously blocked ADB taps; if still blocked, the user must perform these manually. Runtime PASS requires actual gameplay evidence.

Private LAN is unverified. Test with two consenting physical phones only after local behavior is confirmed. Keep experiments out of public matches. Native code and application binaries remain local for personal testing; do not redistribute proprietary game assets/binaries without rights.

## Reproduce and verify

Requirements: existing Python pyelftools, Keystone and Capstone, Android SDK Build Tools 35.0.0 and local test keystore. Unicorn is needed only for ARM64 fixtures. Builders refuse overwrite; preserve/move the new candidate output aside before rebuilding, and keep the working source directories intact.

```bash
python3 scripts/audit_duplicate_inventory.py
python3 scripts/patch_duplicate_inventory.py --output /tmp/mmc-duplicate-inventory.so
python3 scripts/build_duplicate_inventory.py
python3 scripts/build_duplicate_inventory.py --verify

# If Unicorn is installed in the session's temporary location:
PYTHONPATH=/tmp/mmc-unicorn-tests:scripts python3 scripts/test_duplicate_inventory_arm64.py
PYTHONPATH=/tmp/mmc-unicorn-tests:scripts python3 scripts/test_duplicate_inventory_arm64.py --patched
```

The patch accepts only the exact confirmed working native hash (`8cac1bfb7c7c523bbfbb2c33ea3c446acb2d8db24d0a639799b04d74b8026f60`). It verifies original function bytes, executable PT_LOAD mappings, vtable targets and bounds, then checks whole-file mutation scope. All non-native APK payloads match the working containers. Split native entries are uncompressed and 4096-byte aligned.

Read-only Ghidra exports reuse the existing project, using `ExportDuplicateInventory.java` and `ExportDuplicateParsers.java` in `native-analysis/ghidra_scripts/` with `-process libcocos2dcpp.so -noanalysis -readOnly`. Decompiled output is under `native-analysis/duplicate-*-decompiled.txt`; original and patched instruction listings and signature logs are under `reports/duplicate-inventory-evidence/`.

## Rollback

Reinstall the user-confirmed corrected-ammo/fuel build as an update:

```bash
./scripts/deploy_fixed_gameplay.sh 241266d60c20
```

Or use [mmc-fixed-ammo-dual-weapon.apk](builds/fixed_ammo_dual_weapon_standalone/mmc-fixed-ammo-dual-weapon.apk). Do not roll back to the obsolete combined RET-ammo variant, which retains the reload bug. No original/working APKs were overwritten. `backup/duplicate-inventory-20261008/` snapshots the working split/standalone files, earlier documents and patch script with a SHA-256 manifest. Earlier baseline/phase4 backups remain intact. Code rollback retains saved loadout data.

## Reports

- [Duplicate inventory root cause](reports/duplicate-inventory-root-cause.md): previous missed routes, ownership, parsers and spawn.
- [Inventory verification](reports/duplicate-inventory-verification.md): exact bytes, hashes, package and emulation evidence.
- [Device results/manual tests](reports/duplicate-inventory-tests.md): actual installation results and pending checks.
- [Prior reload correction](reports/reload-root-cause.md): now user-confirmed working on the preserved build.
- [General modification history](reports/modification-report.md) and [weapon analysis](reports/weapon-system-analysis.md).
