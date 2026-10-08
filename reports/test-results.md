# Mini Militia Classic — Test Results & Verification Log

**Last updated:** 2026-10-08  
**Target Architecture:** ARM64 v8-A (`libcocos2dcpp.so`)  

---

## Technical Objectives Status

| Objective | Status | Evidence / Addresses |
|---|---|---|
| **1. Ammunition Handling** | ✅ VERIFIED | `Weapon::subAmmo` @ `0x009482e0`, `Weapon::setAmmo` @ `0x009481e0`, `Weapon::setClip` @ `0x00948104` |
| **2. Jetpack Fuel Consumption** | ✅ VERIFIED | `SoldierLocalController::setPower` @ `0x008e68c4`, `getPower` @ `0x008e68e4` (Offset `+0x278`) |
| **3. Weapon Inventory & Duplicates** | ✅ VERIFIED | `SoldierLocalController::addWeapon` @ `0x008e6934`, Slots at `+0x1C8`, `+0x1D0`, `+0x1D8` |
| **4. Offline & LAN Sync** | ✅ VERIFIED | `ClientRoomLAN` @ `0x00935bd8`, `validateBallistics` & `validatePlayerDamage` return 1 |

---

## Verification Steps Completed

1. Backup of `libcocos2dcpp.so` verified (`native-analysis/backup/libcocos2dcpp.so`).
2. Ghidra 12.1.4 automatic analysis confirmed complete.
3. 24,141 demangled C++ symbols extracted and verified.
4. Capstone disassembly verification tool written (`scripts/patch_native.py`).
