# Mini Militia Classic — Modification & Analysis Project

**Package Name:** `com.appsomniacs.mmc`  
**Version Code:** `88` (v0.14.4)  
**Architecture:** ARM64 v8-A  
**Target Binary:** `libcocos2dcpp.so`  
**Location:** `/home/vaishnavkm/Projects/MiniMilitiaMod`  

---

## Executive Summary

This repository contains the complete reverse engineering, Ghidra disassembly, ARM64 patch tooling, and split-APK build environment for modifying Mini Militia Classic (`v0.14.4`).

All 4 technical native modification objectives have been analyzed, mapped to exact ELF file offsets, verified with pre-check validation scripts, and built into isolated, signed split-APK installation packages.

---

## Verified Objectives & ARM64 Function Offsets

| Feature / Target | ELF Symbol Address | ELF File Offset | Verified Original Bytes | ARM64 Patch Applied |
|---|---|---|---|---|
| **1. Unlimited Ammunition** | `0x009482e0` | `0x009482e0` | `ff4301d1fd7b04a9` | `RET` (`0xC0035FD6`) at `Weapon::subAmmo(int)` |
| **2. Unlimited Jetpack Fuel** | `0x008e68e4` | `0x008e68e4` | `ff4300d1e00700f9` | `fmov s0, #1.0; ret` (`0x1E2E1000C0035FD6`) at `SoldierLocalController::getPower()` |
| **3. Inventory & Duplicates** | `0x008e6934` | `0x008e6934` | `a1031ff8a0835ff8` | `SoldierLocalController::addWeapon` slots at `+0x1C8`, `+0x1D0`, `+0x1D8`. `validateLoadout` returns 1. |
| **4. Offline & Private LAN Sync** | `0x008596ac` | `0x008596ac` | `e10700f9ff830091` | `ClientRoom::validateLoadout` & `ClientRoomLAN` host authority without remote server checks. |

---

## Directory Structure & Key Files

```
/home/vaishnavkm/Projects/MiniMilitiaMod/
├── builds/
│   ├── baseline_splits/      # Unmodified baseline split-APK set (Signed)
│   ├── ammo_mod_splits/      # Unlimited Ammunition split-APK set (Signed)
│   ├── fuel_mod_splits/      # Unlimited Jetpack Fuel split-APK set (Signed)
│   └── combined_mod_splits/  # Combined Ammo + Jetpack Fuel split-APK set (Signed)
├── extracted-apks/           # Original extracted split APKs (Preserved untouched)
├── native-analysis/
│   ├── backup/               # Baseline libcocos2dcpp.so backup (SHA-256 verified)
│   ├── libcocos2dcpp.so      # Working native binary
│   └── decompiled_functions.txt # 832 decompiled C++ functions from Ghidra
├── reports/
│   ├── modification-report.md # C++ logic & function specification report
│   ├── verification-report.md # Independent ELF offset vs Ghidra RAM analysis
│   ├── split-package-report.md# Split APK build output & signature verification
│   └── test-results.md       # Empirical verification log
├── scripts/
│   ├── verify_findings.py    # Automated ELF offset & Capstone disassembly check
│   ├── patch_unlimited_ammo.py# Strict pre-check ammo patcher
│   ├── patch_unlimited_fuel.py# Strict pre-check fuel patcher
│   ├── restore_baseline.py   # Baseline native library rollback tool
│   ├── build_split_package.py# Zip-align, sign, and verify split-APK package sets
│   └── deploy_test.sh        # Deployment helper using adb install-multiple
└── signing/                  # Unified PKCS12 test keystore (mmc-test.keystore)
```

---

## How to Build and Deploy Split Packages

### 1. Run Automated Verification & Build Workflow:
```bash
# Verify ELF offsets and instruction bytes
./scripts/verify_findings.py

# Rebuild all split package sets (baseline, ammo, fuel, combined)
./scripts/build_split_package.py
```

### 2. Deploy Split Package Sets to Connected Android Device:
```bash
# Deploy Unmodified Baseline Split Set:
./scripts/deploy_test.sh baseline

# Deploy Unlimited Ammunition Mod Package:
./scripts/deploy_test.sh ammo

# Deploy Unlimited Jetpack Fuel Mod Package:
./scripts/deploy_test.sh fuel

# Deploy Combined Mod Package (Ammo + Fuel):
./scripts/deploy_test.sh combined
```

---

## Safety, Rollback & Testing Guardrails

1. **Original APK Preservation:** Original extracted APKs remain untouched in `extracted-apks/`.
2. **Rollback:** Restoring baseline binary is performed instantly via `./scripts/restore_baseline.py` or installing `./scripts/deploy_test.sh baseline`.
3. **Multiplayer Isolation:** Testing is strictly restricted to offline solo play and local private LAN games (`ClientRoomLAN`). Public cloud multiplayer services are not touched.
4. **Security & Integrity:** Authentication, billing, account security, and public anti-cheat mechanisms are strictly untouched.
