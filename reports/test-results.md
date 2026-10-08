# Mini Militia Classic — Test Results

**Last updated:** 2026-10-08

---

## Legend

| Status | Meaning |
|---|---|
| ✅ PASS | Test executed and passed |
| ❌ FAIL | Test executed and failed |
| 🔴 BLOCKED | Cannot run — prerequisite missing |
| ⏳ NOT RUN | Scheduled but not yet executed |
| ⚠️ PARTIAL | Partially tested |

---

## Phase 1 — Baseline Build Tests

| Test | Status | Notes |
|---|---|---|
| APK SHA-256 matches backup | ✅ PASS | `9da04d4a...` confirmed |
| apktool decode (no errors) | ✅ PASS | 793 files decoded |
| apktool rebuild (no errors) | ✅ PASS | All 3 DEX + resources |
| Zip alignment | ✅ PASS | `zipalign -c` passes |
| APK v1 signature | ✅ PASS | JAR signing verified |
| APK v2 signature | ✅ PASS | APK Signature Scheme v2 |
| APK v3 signature | ✅ PASS | APK Signature Scheme v3 |
| ADB install | ⏳ NOT RUN | No device connected |
| Game launch | ⏳ NOT RUN | No device connected |
| Offline match start | ⏳ NOT RUN | No device connected |
| LAN match (2 devices) | 🔴 BLOCKED | No device connected |

---

## Phase 2 — Feature A: Unlimited Ammunition

| Test | Status | Notes |
|---|---|---|
| Smali ammo code found | ❌ NONE FOUND | Confirmed in native `.so` |
| Native library obtained | 🔴 BLOCKED | Need ABI split APK |
| Ammo function in Ghidra | ⏳ NOT RUN | — |
| Ammo patch applied | ⏳ NOT RUN | — |
| Continuous fire (offline) | ⏳ NOT RUN | — |
| Ammo display shows ∞ | ⏳ NOT RUN | — |
| Weapon switch preserves ammo | ⏳ NOT RUN | — |
| Reload animation preserved | ⏳ NOT RUN | — |
| LAN: ammo sync | ⏳ NOT RUN | — |

---

## Phase 2 — Feature B: Unlimited Jetpack

| Test | Status | Notes |
|---|---|---|
| Smali fuel code found | ❌ NONE FOUND | Confirmed in native `.so` |
| Native library obtained | 🔴 BLOCKED | Need ABI split APK |
| Fuel function in Ghidra | ⏳ NOT RUN | — |
| Fuel patch applied | ⏳ NOT RUN | — |
| Continuous flight (offline) | ⏳ NOT RUN | — |
| No movement instability | ⏳ NOT RUN | — |
| Landing physics preserved | ⏳ NOT RUN | — |
| Jetpack animation preserved | ⏳ NOT RUN | — |
| LAN: flight sync | ⏳ NOT RUN | — |

---

## Phase 2 — Feature C: Any Two Weapons

| Test | Status | Notes |
|---|---|---|
| Loadout JSON format known | ⏳ NOT RUN | Requires first device run |
| Duplicate weapon JSON crafted | ⏳ NOT RUN | — |
| Weapon validation bypass | 🔴 BLOCKED | Need ABI split APK |
| Two different weapons | ⏳ NOT RUN | — |
| Two identical weapons | ⏳ NOT RUN | — |
| Weapon switching works | ⏳ NOT RUN | — |
| Respawn with same loadout | ⏳ NOT RUN | — |
| LAN: weapon sync | ⏳ NOT RUN | — |

---

## Phase 2 — Feature D: Offline Gameplay

| Test | Status | Notes |
|---|---|---|
| Game launches offline | ⏳ NOT RUN | Expected: works without mod |
| Offline match playable | ⏳ NOT RUN | Expected: works without mod |
| AI enemies function | ⏳ NOT RUN | Expected: works without mod |
| Maps load correctly | ⏳ NOT RUN | Expected: works without mod |

---

## Phase 2 — Feature E: Private LAN Multiplayer

| Test | Status | Notes |
|---|---|---|
| LAN host discovery | 🔴 BLOCKED | Need ABI split APK analysis |
| Client join | 🔴 BLOCKED | — |
| Weapon sync | 🔴 BLOCKED | — |
| Movement sync | 🔴 BLOCKED | — |
| Ammo sync (both modded) | 🔴 BLOCKED | — |
| No desync crashes | 🔴 BLOCKED | — |

---

## Regression Tests

| Test | Status | Notes |
|---|---|---|
| Game launch | ⏳ NOT RUN | Blocked — no device |
| Menu navigation | ⏳ NOT RUN | — |
| Audio playback | ⏳ NOT RUN | — |
| Map loading | ⏳ NOT RUN | — |
| Player health system | ⏳ NOT RUN | — |
| Projectile collision | ⏳ NOT RUN | — |
| Match restart | ⏳ NOT RUN | — |
| Game does not crash at launch | ⏳ NOT RUN | — |

---

## Notes

- All tests marked ⏳ NOT RUN or 🔴 BLOCKED are awaiting the ABI split APK and a connected test device
- The baseline signed APK (`builds/baseline-signed.apk`) is structurally valid and ready to install
- **No test results have been fabricated** — only actual results are marked PASS/FAIL
