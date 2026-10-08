# Mini Militia Classic — Modification Report

**Last updated:** 2026-10-08  
**APK version:** 0.14.4 (build 88)

---

## Phase 1 — Baseline Establishment

### ✅ Steps Completed

| Step | Result |
|---|---|
| Original APK SHA-256 | `9da04d4a0102922b57b626c9bb898e727f0dde2f8f9f9a0d8caaa2964f03ef6f` |
| Backup created | `backup/base.apk.bak` |
| Git repo initialized | `.git/` |
| apktool 2.10.0 installed | `scripts/apktool.jar` |
| jadx 1.5.1 installed | `scripts/jadx-bin/` |
| APK decoded (Smali) | `decoded/` — 793 files |
| Database extracted | `backup/mmcDatabase.sqlite` |
| Baseline rebuild | ✅ SUCCESS — `builds/baseline-unsigned.apk` |
| Zip alignment | ✅ SUCCESS — `builds/baseline-aligned.apk` |
| Signing (PKCS12 keystore) | ✅ SUCCESS — `builds/baseline-signed.apk` |
| Signature verification | ✅ v1 + v2 + v3 schemes verified |
| Device install | ⏳ PENDING — no ADB device connected |

---

## Phase 2 — Feature Modifications

### Feature A — Unlimited Ammunition

**Status: 🔴 BLOCKED — Native library required**

**Root cause:**  
Ammo logic is in `libcocos2dcpp.so` (Cocos2d-x C++ game engine). The base APK contains no Smali-level ammo counter, decrement, or reload logic. All `ammo`/`bullet`/`reload` Smali searches returned zero results in game packages.

**Required:** ABI split APK containing `libcocos2dcpp.so`

**Planned implementation (post-split-APK):**
1. Open `libcocos2dcpp.so` in Ghidra
2. Search for patterns like:
   - Integer field decrement followed by zero-check branch
   - Call chains from input handler → weapon fire → ammo check
   - String references to "ammo", "reload", "magazine" (if not stripped)
3. NOP the decrement instruction (e.g., `SUB W0, W0, #1` → `NOP` in ARM64)
   OR replace the branch condition `CBZ W0, reload_label` → always jump to fire path
4. Validate in Ghidra that surrounding code is not broken
5. Repack into modified ABI split APK
6. Test on device

**Expected Smali change:** None (zero Java-side ammo code found)  
**Expected native change:** 1–4 instructions patched in `libcocos2dcpp.so`

---

### Feature B — Unlimited Jetpack

**Status: 🔴 BLOCKED — Native library required**

**Root cause:**  
Same as Feature A. Jetpack fuel is a per-frame decremented float field in the player physics update loop inside `libcocos2dcpp.so`. Zero `fuel`/`jetpack`/`boost` results in game Smali.

**Planned implementation (post-split-APK):**
1. In Ghidra, search for float-subtract patterns in physics update
2. Identify the jetpack activation check and fuel consumption call
3. Common pattern in Cocos2d games:
   ```c
   // Original C++
   if (_fuelLevel > 0.0f) {
       _fuelLevel -= FUEL_BURN_RATE * dt;
       applyJetpackForce();
   }
   ```
4. Patch: either NOP the fuel decrement, or force `_fuelLevel = MAX_FUEL` each frame
5. Preserve jetpack animation triggers (typically driven by the same `isJetpackActive` bool)

**Expected Smali change:** None  
**Expected native change:** 1–6 instructions in physics update method

---

### Feature C — Any Two Weapons (Including Duplicates)

**Status: 🟡 PARTIAL — Two-part implementation**

**Part 1 — Loadout JSON (Smali/DB level):**

The `mmcDatabase.sqlite` `loadout` table stores weapon selections as JSON in the `json` column. The table is empty in the bundled DB and populated at runtime by the C++ engine.

To pre-populate a loadout with duplicate weapons, we need to:
1. Run the game once on a device to see what the JSON format looks like
2. Craft a JSON payload with two identical weapon slot IDs
3. Insert it into the `mmcDatabase.sqlite` before repacking

**Part 2 — Validation bypass (Native level):**

The C++ engine likely validates weapon uniqueness when applying a loadout. This check must be patched in `libcocos2dcpp.so`.

**Planned implementation:**
1. Run stock game → dump `mmcDatabase.sqlite` via ADB → inspect JSON format
2. Craft duplicate-weapon JSON
3. In Ghidra, find weapon slot validation (`if (weapon1_id == weapon2_id) reject`)
4. NOP or invert the rejection branch

**Files to modify:**
- `assets/mmcDatabase.sqlite` (JSON payload — if format is known)
- `libcocos2dcpp.so` (validation bypass)

---

### Feature D — Offline Gameplay

**Status: 🟢 NO MODIFICATION NEEDED**

The game supports offline play natively. All maps, physics, AI enemies, and single-player modes function without a network connection. Offline gameplay is preserved by default in the baseline rebuild.

**Optional enhancement (Smali-level):**  
The `DA2Activity.isOnlineActivityAllowed()` method checks network connectivity before allowing certain features. This can be patched to always return `false` (offline mode) to prevent any network dependency at startup:

```smali
# File: decoded/smali/com/appsomniacs/mmc/DA2Activity.smali
# Method: isOnlineActivityAllowed() (approx. line 3185)
# Change: return false unconditionally to skip online session init
```

This patch is **low risk** but **not strictly required** for offline play.

---

### Feature E — Private LAN Multiplayer

**Status: 🔴 BLOCKED — Native library analysis required**

The entire multiplayer stack (UDP discovery, match hosting, state sync, weapon packets) is implemented in `libcocos2dcpp.so`. No Java-side networking for gameplay was found.

**Analysis needed (post-split-APK):**
1. Identify UDP socket creation in Ghidra (typically via `socket()` → `bind()` → `sendto()`)
2. Find the broadcast discovery address (often `255.255.255.255` or subnet broadcast)
3. Identify weapon inventory serialization in the network packets
4. Determine whether ammo/fuel is validated by host or locally

**LAN compatibility rule:** Both devices must run the same modified build for modified features to work consistently. The host may reject clients whose gameplay state (ammo/fuel) differs from expected values.

---

## Phase 3 — Pending (Requires ABI Split APK)

| Step | Status |
|---|---|
| Obtain ABI split APK | ⏳ PENDING — requires device with game installed |
| Extract `libcocos2dcpp.so` | ⏳ PENDING |
| Ghidra analysis | ⏳ PENDING |
| Identify ammo decrement | ⏳ PENDING |
| Identify fuel decrement | ⏳ PENDING |
| Identify weapon validation | ⏳ PENDING |
| Patch ammo logic | ⏳ PENDING |
| Patch jetpack logic | ⏳ PENDING |
| Patch weapon validation | ⏳ PENDING |
| Repack ABI split APK | ⏳ PENDING |
| Build combined install package | ⏳ PENDING |
| Device testing | ⏳ PENDING |
| LAN testing | ⏳ PENDING |

---

## Modified Files (Current)

| File | Change | Risk |
|---|---|---|
| `decoded/` | Decoded from base.apk — no modifications yet | N/A |
| `signing/mmc-test.keystore` | New test keystore generated | None |
| `builds/baseline-signed.apk` | Clean rebuild of original — unchanged gameplay | None |
