# Mini Militia Classic — personal gameplay test build

Package `com.appsomniacs.mmc`, version 0.14.4 (88), ARM64. Updated 2026-10-08.

The corrected combined build **installed successfully over USB** on the connected Xiaomi M2010J19CI (Android 12) and launches to “Touch to Start.” It replaces the incomplete ammunition patch, preserves the user-confirmed fuel patch exactly, and adds duplicate choices and same-type ordinary weapon pickup. Gameplay remains experimental. MIUI denied automated ADB taps, and the user elected to test gameplay manually. Reload, all weapon combinations, fuel regression and private LAN need manual validation. Earlier claims of working unlimited ammo/LAN are superseded by the latest reload-bug report.

## Downloadable APK

[mmc-fixed-ammo-dual-weapon.apk](builds/fixed_ammo_dual_weapon_standalone/mmc-fixed-ammo-dual-weapon.apk)

SHA-256: `3c01bda3d733c64a5e8913af72f8224a666dd502fc8a40c882e2e1ae9411fff1`.

The matching four-split package is in [fixed_ammo_dual_weapon_splits](builds/fixed_ammo_dual_weapon_splits/). Base alone cannot install the game. Both forms contain identical patched ARM64 native code and the existing test certificate. The standalone preserves the earlier standalone manifest/resources; the split set preserves original split application payloads. Artifacts are local for personal/private tests; do not redistribute proprietary game binaries without rights.

## Changes and limits

Ammo now refills local equipped instances through `getClip` / `getAmmo` using each weapon's own capacity, including physical clip/reserve fields. Stock `subAmmo` and reload completion are restored/preserved. Weapon damage, cadence, projectiles, initialization, ownership and network validation stay under stock code. A 105-case ARM64 emulation suite passes, including the original reload-completion body; this is not a device gameplay test.

Duplicate primary/secondary choices and ordinary same-type pickups follow existing instance-creation and inventory paths. Special dual-only utilities, throwables, objective items and paid access retain existing restrictions. Successful duplicate gameplay for every ordinary gun is not yet demonstrated. Local refill does not establish host/client ammo synchronization.

Ads remain unchanged. Advertising SDKs, rewards, purchases, entitlements and licensing were not bypassed.

## Install/update

The connected phone already has the complete corrected split set. To reinstall/update later, unlock it and approve the USB installation prompt:

```bash
./scripts/deploy_fixed_gameplay.sh 241266d60c20
```

Or install the standalone APK:

```bash
adb install --no-incremental -r builds/fixed_ammo_dual_weapon_standalone/mmc-fixed-ammo-dual-weapon.apk
```

You can also copy the standalone APK to the phone and open it with Android's installer. Never uninstall or clear app data to work around a signing/install error. Retain the existing app and record the error. Automated ADB gameplay on MIUI requires its separate “USB debugging (Security settings)” input permission; installation does not grant that permission.

## Reproduce and verify

Python dependencies: pyelftools, Capstone, Keystone; Unicorn is needed only for emulation tests. Existing Android SDK Build Tools 35.0.0 and local signing keystore are used. Builders refuse to overwrite outputs; move an existing output aside before rebuilding.

```bash
# Phase B first: corrected ammo + existing fuel
python3 scripts/build_fixed_gameplay.py
python3 scripts/verify_fixed_gameplay.py

# Phase D only after Phase B structural verification
python3 scripts/build_fixed_gameplay.py --duplicates
python3 scripts/verify_fixed_gameplay.py --duplicates

# Native-only output; original analysis/backup are protected
python3 scripts/patch_fixed_gameplay.py --duplicates --output /tmp/mmc-fixed-native.so

# ARM64 synthetic execution (if Unicorn installed)
python3 scripts/test_fixed_ammo_arm64.py
```

In this session Unicorn was installed in `/tmp/mmc-unicorn-tests`; the exact test command was `PYTHONPATH=/tmp/mmc-unicorn-tests:scripts python3 scripts/test_fixed_ammo_arm64.py`. No dependencies are silently downloaded by tests/builders.

Each build has `verification.json` with full patch bytes, independent VA/file mappings, original/native/APK hashes and signature checks. Native ZIP compression/alignment is verified separately: the inherited packager compressed the game library while the split manifest disallowed extraction, causing an actual install failure; the new builder stores and page-aligns it.

Use the new scripts above. Historical `patch_unlimited_ammo.py` is buggy and its CLI now refuses execution. Historical build workflows overwrite older variants and must not reproduce this correction. Earlier combined/picker-only builds remain preserved but retain the reported ammunition bug. Copies of initial new outputs under `*_packaging_v1` are diagnostic, not recommended install packages.

## Tests and rollback

Follow [test-results.md](reports/test-results.md) for the offline and two-phone private LAN matrix, including continuous fire, manual reload, switching, matching pickups, drops, respawn, all duplicate pairs and boost regression.

Use [mmc-fixed-ammo-jetpack.apk](builds/fixed_ammo_jetpack_standalone/mmc-fixed-ammo-jetpack.apk) to isolate ammo/fuel without inventory changes. It uses the same signer/version for updating while retaining app data. Pre-change snapshots are at `backup/reload-fix-20261008/` and `backup/phase4-working-20261008/`, with SHA-256 manifests. The original analysis library and all previous working outputs are intact. Switching between standalone and split forms should be checked for install errors without uninstalling.

## Reports

- [Root-cause analysis](reports/reload-root-cause.md): actual firing/reload paths, correction and unresolved runtime cause.
- [Modification report](reports/modification-report.md): scope, scripts, artifacts and limits.
- [Verification report](reports/verification-report.md): exact sites, hashes and evidence.
- [Weapon analysis](reports/weapon-system-analysis.md): allocations, lifetime, serialization, restrictions and pickup routing.
- [Gameplay/LAN test report](reports/test-results.md): performed checks and pending manual tests.
- [Ad inspection](reports/ad-integration-analysis.md): unchanged ad/access behavior.
