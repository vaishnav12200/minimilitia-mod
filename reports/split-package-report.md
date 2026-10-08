USB installation update: the user-requested retry succeeded. The new duplicate inventory build is installed; its ARM64 split was read back and matches the verified build exactly. The launch command succeeded. Gameplay and LAN remain pending manual verification. Earlier storage failures below are historical.

# Current split deployment — 2026-10-08

The legacy RET-ammo build descriptions below are obsolete for reproduction/rollback. Use `duplicate_weapon_fixed_splits` for the new inventory candidate and preserve `fixed_ammo_dual_weapon_splits` as the latest user-tested working ammo/reload/fuel build. All new split native libraries are stored uncompressed and page-aligned, fixing the historical installer extraction bug. All four splits have matching test certificates. Latest first install was refused for insufficient device storage. No public-server code was disabled by these patches; testing must be confined to offline/private modes by the user. The old statement about disabled public connection APIs below is not supported by the current patch audit. See [inventory verification](duplicate-inventory-verification.md) and [device tests](duplicate-inventory-tests.md).

# Mini Militia Classic — Split-APK Testing & Installation Report

**Project Directory:** `/home/vaishnavkm/Projects/MiniMilitiaMod`  
**Package Name:** `com.appsomniacs.mmc`  
**Version Code:** `88` (v0.14.4)  
**Architecture:** ARM64 v8-A  
**Build Date:** 2026-10-08  

---

## 1. Extracted APK Inventory & Version Verification

All APK components in `extracted-apks/` were verified using AAPT metadata inspection. Every split belongs to the exact same package version:

| File Name | Split Identifier | Package Name | Version Code | Version Name |
|---|---|---|---|---|
| `base.apk` | (Main APK) | `com.appsomniacs.mmc` | `88` | `0.14.4` |
| `split_config.arm64_v8a.apk` | `config.arm64_v8a` | `com.appsomniacs.mmc` | `88` | (Split) |
| `split_config.xxhdpi.apk` | `config.xxhdpi` | `com.appsomniacs.mmc` | `88` | (Split) |
| `split_config.en.apk` | `config.en` | `com.appsomniacs.mmc` | `88` | (Split) |

---

## 2. Split Package Build & Alignment Outputs

Four isolated split package sets were generated, aligned (`zipalign -p -f 4`), and signed with the test keystore (`mmc-test.keystore`):

### 1. Unmodified Baseline Split Package
- **Location:** `builds/baseline_splits/`
- **Files:** `base.apk`, `split_config.arm64_v8a.apk`, `split_config.xxhdpi.apk`, `split_config.en.apk`
- **Status:** ✅ Signature Verified (v1, v2, v3 scheme)

### 2. Unlimited Ammunition Split Package
- **Location:** `builds/ammo_mod_splits/`
- **Native Modification:** `Weapon::subAmmo(int)` @ ELF `0x009482e0` patched with `RET` (`0xC0035FD6`).
- **Files:** `base.apk`, `split_config.arm64_v8a.apk` (modded), `split_config.xxhdpi.apk`, `split_config.en.apk`
- **Status:** ✅ Signature Verified (v1, v2, v3 scheme)

### 3. Unlimited Jetpack Fuel Split Package
- **Location:** `builds/fuel_mod_splits/`
- **Native Modification:** `SoldierLocalController::getPower()` @ ELF `0x008e68e4` patched with `fmov s0, #1.0; ret` (`0x1E2E1000C0035FD6`).
- **Files:** `base.apk`, `split_config.arm64_v8a.apk` (modded), `split_config.xxhdpi.apk`, `split_config.en.apk`
- **Status:** ✅ Signature Verified (v1, v2, v3 scheme)

### 4. Combined Mod Split Package (Ammo + Fuel)
- **Location:** `builds/combined_mod_splits/`
- **Native Modification:** Both Ammo and Jetpack patches applied to `split_config.arm64_v8a.apk`.
- **Files:** `base.apk`, `split_config.arm64_v8a.apk` (modded), `split_config.xxhdpi.apk`, `split_config.en.apk`
- **Status:** ✅ Signature Verified (v1, v2, v3 scheme)

---

## 3. Strict Original-Bytes Pre-Check Validation

Both `scripts/patch_unlimited_ammo.py` and `scripts/patch_unlimited_fuel.py` contain strict pre-check validation:

```python
# Verification logic prior to writing:
current_bytes = f.read(len(EXPECTED_ORIGINAL_BYTES))
if current_bytes != EXPECTED_ORIGINAL_BYTES:
    sys.exit("ERROR: Original bytes mismatch at offset!")
```

Pre-check validation caught offset shifts during script execution and ensured 100% accurate instruction patching at verified offsets.

---

## 4. Proposed `adb install-multiple` Deployment Commands

> [!IMPORTANT]
> Requirement 11 Enforcement: As requested, no automatic installation or uninstallation has been executed. The following commands are provided for user approval and execution when an Android device is attached.

### Command A — Deploy Baseline Unmodified Split Package:
```bash
adb install-multiple -r \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/baseline_splits/base.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/baseline_splits/split_config.arm64_v8a.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/baseline_splits/split_config.xxhdpi.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/baseline_splits/split_config.en.apk
```

### Command B — Deploy Unlimited Ammunition Mod Package:
```bash
adb install-multiple -r \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/ammo_mod_splits/base.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/ammo_mod_splits/split_config.arm64_v8a.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/ammo_mod_splits/split_config.xxhdpi.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/ammo_mod_splits/split_config.en.apk
```

### Command C — Deploy Unlimited Jetpack Fuel Mod Package:
```bash
adb install-multiple -r \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/fuel_mod_splits/base.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/fuel_mod_splits/split_config.arm64_v8a.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/fuel_mod_splits/split_config.xxhdpi.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/fuel_mod_splits/split_config.en.apk
```

### Command D — Deploy Combined Mod Package (Ammo + Fuel):
```bash
adb install-multiple -r \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/combined_mod_splits/base.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/combined_mod_splits/split_config.arm64_v8a.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/combined_mod_splits/split_config.xxhdpi.apk \
  /home/vaishnavkm/Projects/MiniMilitiaMod/builds/combined_mod_splits/split_config.en.apk
```

---

## 5. Rollback & Testing Isolation Protocol

1. **Original Extraction Rollback:** Original extracted APKs are preserved untouched in `extracted-apks/`.
2. **Baseline Rollback:** Running Command A reinstalls the signed baseline package.
3. **Private LAN Isolation:** All testing is restricted to offline local matches and private LAN sessions (`ClientRoomLAN`). Public server connection APIs are disabled during test sessions.


## Phase 5 pickup action separation — 2026-10-08

The preceding SPAS held pair is user-confirmed. The new two-action SPAS UI candidate is signed, installed and launched; 176 ARM64 cases and package checks pass. Physical SPAS action-selection PASS: user confirms both actions, both guns firing and buttons hiding. Broader regression is pending. A shared pair-policy sniper candidate passes 428 ARM64 cases and package checks; its installation was blocked by the disconnected phone. See [sniper extension](dual-wield-ui-sniper.md). Other gun classes/mixed pairs and LAN remain pending. See [Phase 5 evidence and manual checklist](dual-wield-ui-phase5.md).
