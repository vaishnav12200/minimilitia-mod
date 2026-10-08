# Mini Militia Classic — Mod Project

## Project Overview

This repository contains the tooling and analysis for modifying Mini Militia Classic (`com.appsomniacs.mmc` v0.14.4) for personal testing and private LAN gameplay.

**Requested features:**
- Feature A: Unlimited ammunition
- Feature B: Unlimited jetpack fuel
- Feature C: Any two weapons (including duplicates)
- Feature D: Offline gameplay (already supported)
- Feature E: Private Wi-Fi/LAN multiplayer support

---

## ⚠️ Critical Architecture Note

The game is built on **Cocos2d-x (C++)** and delivered as a **split APK bundle**. All gameplay logic (ammo, jetpack, weapons, physics, networking) resides in `libcocos2dcpp.so`, which is **NOT** in `base.apk` — it is in the **ABI split APK** (e.g., `split_config.arm64_v8a.apk`).

**The ABI split APK is required to implement Features A, B, C, and E.**

---

## Project Structure

```
MiniMilitiaMod/
├── base.apk                    ← Original APK (DO NOT MODIFY)
├── backup/
│   ├── base.apk.bak            ← SHA-256 verified backup
│   └── mmcDatabase.sqlite      ← Extracted database backup
├── decoded/                    ← apktool-decoded APK (Smali + resources)
├── jadx-output/                ← JADX decompiled Java (read-only reference)
├── scripts/
│   ├── apktool.jar             ← apktool 2.10.0
│   ├── jadx-bin/               ← jadx 1.5.1 binary
│   ├── inspect.sh              ← APK inspection tool
│   ├── build.sh                ← Rebuild + sign pipeline
│   ├── sign.sh                 ← APK signing only
│   └── verify.sh               ← APK verification
├── builds/
│   ├── baseline-unsigned.apk   ← Rebuild baseline (unsigned)
│   ├── baseline-aligned.apk    ← Zip-aligned baseline
│   └── baseline-signed.apk     ← ✅ Signed baseline (ready to install)
├── signing/
│   └── mmc-test.keystore       ← Test signing keystore (PKCS12)
├── reports/
│   ├── apk-analysis.md         ← Full technical analysis
│   ├── modification-report.md  ← Per-feature modification log
│   └── test-results.md         ← Test results log
└── README.md
```

---

## Checksums

| File | SHA-256 |
|---|---|
| `base.apk` (original) | `9da04d4a0102922b57b626c9bb898e727f0dde2f8f9f9a0d8caaa2964f03ef6f` |
| `backup/base.apk.bak` | `9da04d4a0102922b57b626c9bb898e727f0dde2f8f9f9a0d8caaa2964f03ef6f` |

---

## Tools Required

| Tool | Version | Install |
|---|---|---|
| Java (OpenJDK) | 25.x | Pre-installed |
| apktool | 2.10.0 | `scripts/apktool.jar` |
| jadx | 1.5.1 | `scripts/jadx-bin/` |
| Android SDK Build Tools | 35.0.0 | `/home/vaishnavkm/Android/Sdk/build-tools/35.0.0/` |
| Python 3 | 3.14.x | Pre-installed |
| ADB | latest | Android SDK |
| Ghidra (for native) | 11.x | https://github.com/NationalSecurityAgency/ghidra |
| radare2 (optional) | latest | `dnf install radare2` |

---

## Quick Start

### 1. Inspect the APK
```bash
chmod +x scripts/*.sh
./scripts/inspect.sh
```

### 2. Rebuild from decoded (baseline)
```bash
./scripts/build.sh
```

### 3. Install on device
```bash
adb install builds/<latest>-signed.apk
```

### 4. Verify a signed APK
```bash
./scripts/verify.sh builds/<latest>-signed.apk
```

---

## Baseline Rebuild Status

✅ **The baseline APK rebuilds and signs cleanly.**

- Rebuilt with: `apktool 2.10.0`
- Signed with: `apksigner 35.0.0` (v1+v2+v3 signatures)
- Keystore: `signing/mmc-test.keystore` (PKCS12, 2048-bit RSA)

---

## Implementation Status

| Feature | Status | Blocker |
|---|---|---|
| A — Unlimited Ammo | 🔴 BLOCKED | Requires `libcocos2dcpp.so` (ABI split APK) |
| B — Unlimited Jetpack | 🔴 BLOCKED | Requires `libcocos2dcpp.so` (ABI split APK) |
| C — Any Two Weapons | 🟡 PARTIAL | Loadout JSON accessible; validation in native |
| D — Offline Gameplay | 🟢 READY | No modification needed |
| E — LAN Multiplayer | 🔴 BLOCKED | Requires `libcocos2dcpp.so` analysis |
| Baseline rebuild | ✅ DONE | — |
| Ad removal (optional) | 🟡 POSSIBLE | Smali-level stub of Applovin |
| Force offline session | 🟡 POSSIBLE | Smali patch of online check |

---

## How to Get the ABI Split APK

You need the ABI split APK to proceed with Features A, B, C, and E.

### Method 1 — From an Android device with the game installed
```bash
# Find all installed paths
adb shell pm path com.appsomniacs.mmc

# Pull the ABI split (use the arm64-v8a version for modern devices)
adb pull /data/app/~~<hash>/com.appsomniacs.mmc-<hash>/split_config.arm64_v8a.apk ./
adb pull /data/app/~~<hash>/com.appsomniacs.mmc-<hash>/split_config.armeabi_v7a.apk ./
```

### Method 2 — XAPK bundle from APKPure
1. Download the `.xapk` bundle from APKPure
2. Rename `.xapk` to `.zip` and extract
3. Inside you will find `base.apk` + `split_config.arm64_v8a.apk` etc.

### Method 3 — Google Play split APK extractor (on-device)
Use the **Split APKs Installer (SAI)** app to export the full APK bundle from an installed game.

---

## Native Library Modification Plan (pending ABI split APK)

Once `libcocos2dcpp.so` is obtained:

1. **Ghidra analysis** — open the library, let auto-analysis run (~1 hour for a large Cocos2d game)
2. **Symbol recovery** — search for Cocos2d-x open source function signatures
3. **Ammo search** — find `decrementAmmo`, `setAmmo`, or pattern-match the ammo-decrement logic
4. **Jetpack search** — find `fuelConsume`, `updateFuel`, or energy-drain pattern
5. **Weapon slot search** — find loadout validation / weapon ID dedup logic
6. **Patching** — NOP the decrement instructions or replace with constant assignments
7. **Rebuild** — repack the modified `.so` back into the ABI split APK and sign it

---

## Legal Notice

This project is for **personal use and private testing only** among consenting participants on a private LAN. Do not:
- Use modifications in public/competitive multiplayer
- Bypass account authentication or server anti-cheat
- Redistribute modified proprietary APKs without authorization
- Claim redistribution rights from this modification work
