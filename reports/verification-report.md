# Mini Militia Classic — Native Analysis Independent Verification Report

**Target Binary:** `libcocos2dcpp.so` (ARM64 v8-A, 64-bit ELF)  
**File SHA-256:** `2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401`  
**Verification Date:** 2026-10-08  
**Tools Used:** Python `pyelftools`, Capstone 5.0.9, Keystone 0.9.2, Ghidra 12.1.4  

---

## 1. Address Resolution & ELF Mapping (Requirement 1 & 2)

In ARM64 ELF shared objects (`libcocos2dcpp.so`), Ghidra applies a default image base offset of `0x00100000` (or `0x00400000`) to memory virtual addresses. When patching binary files directly on disk, **ELF File Offsets** must be used instead of Ghidra RAM addresses to avoid patching incorrect instructions.

| Target Function | Ghidra RAM Address | ELF Symbol Address (`st_value`) | ELF File Offset | Original Instruction Bytes | Return Type |
|---|---|---|---|---|---|
| `Weapon::subAmmo(int)` | `0x00A482e0` | `0x009482e0` | **`0x009482e0`** | `a1431fb8a0835ff8` | `int` |
| `Weapon::setAmmo(int, bool)` | `0x00A481e0` | `0x009481e0` | **`0x009481e0`** | `081540f9a8831ff8` | `ulong` |
| `Weapon::setClip(int)` | `0x00A48104` | `0x00948104` | **`0x00948104`** | `081540f9a8831ff8` | `ulong` |
| `SoldierLocalController::setPower(float)` | `0x009E68c4` | `0x008e68c4` | **`0x008e68c4`** | `e00740bd007802bd` | `void` |
| `SoldierLocalController::getPower()` | `0x009E68e4` | `0x008e68e4` | **`0x008e68e4`** | `ff430091c0035fd6` | `float` (in `s0`) |
| `SoldierLocalController::hasPower()` | `0x009EC7b8` | `0x008ec7b8` | **`0x008ec7b8`** | `080040f908cd42f9` | `bool` |
| `SoldierLocalController::addWeapon(Weapon*)` | `0x009E6934` | `0x008e6934` | **`0x008e6934`** | `a1031ff8a0835ff8` | `void` |
| `ClientRoom::validateLoadout(...)` | **`0x009596ac`** | **`0x008596ac`** | **`0x008596ac`** | `e10700f9ff830091` | `undefined8` (bool) |

> [!CRITICAL]
> Note the discrepancy for `ClientRoom::validateLoadout`: Its ELF File Offset is `0x008596ac`. Using the Ghidra RAM address `0x009596ac` as a file offset would incorrectly write to `ClientRoomLAN::validateBallistics` (`0x008596c8`)!

---

## 2. Caller Analysis for `Weapon::subAmmo(int)` (Requirement 3)

- `Weapon::subAmmo(int param_2)` subtracts `param_2` from current clip (`+0x362`) and reserve ammo (`+0x360`).
- Callers (such as `Weapon::weaponDidFire` and `SoldierLocalController::fire`) call `subAmmo` during weapon discharge.
- **Return Value Analysis:** `subAmmo` returns the total amount of ammunition actually subtracted (`int`). However, main firing loops do not check the return integer value to grant/deny shots; shot permission is validated prior to firing via `getClip()` / `getAmmo()`.
- **Patch Plan:** Returning early from `subAmmo` with `RET` (`0xC0035FD6`) prevents clip and reserve ammo from being subtracted.

---

## 3. Jetpack Fuel Consumption Call Path (Requirement 4)

- Fuel / jetpack power is stored as a 32-bit single-precision float (`float`) at offset `+0x278` in `SoldierLocalController`.
- **Call Chain:**
  1. `SoldierLocalController::updateStep(...)` updates flight physics when jetpack thrust is active.
  2. `SoldierLocalController::hasPower()` verifies if jetpack power remains by calling `getPower()` via vtable slot `0x598`.
  3. `SoldierLocalController::getPower()` reads `*(float *)(this + 0x278)` and returns it in ARM64 float register `s0`.
  4. `SoldierLocalController::setPower(float)` writes to `*(float *)(this + 0x278)`.
- **Patch Plan:** Modifying `SoldierLocalController::getPower()` to return `1.0f` (`fmov s0, #1.0` -> `0x1E2E1000`, `ret` -> `0xD65F03C0`) guarantees `hasPower()` always evaluates to `true` and HUD/flight physics receive full power.

---

## 4. Duplicate Weapon & Loadout Serialization (Requirement 5)

- **Inventory Slot Layout in `SoldierLocalController`:**
  - Primary Weapon: `*(Weapon**)(this + 0x1C8)`
  - Secondary Weapon: `*(Weapon**)(this + 0x1D0)`
  - Dual Wield Weapon: `*(Weapon**)(this + 0x1D8)`
- **Serialization & Host Sync:**
  - Host validation in LAN games: `ClientRoom::validateLoadout(...)` @ ELF `0x008596ac` unconditionally returns `1` (true).
  - LAN network synchronization via `ClientRoomLAN` and `RakNet` transmits `LoadoutObject` payloads without server-side duplicate weapon restrictions.

---

## 5. Summary of Distinctions: Confirmed Findings vs. Assumptions

| Feature / Area | Confirmed Finding | Assumption / Unverified Hypothesis |
|---|---|---|
| **Ammunition Subtraction** | Confirmed: `subAmmo` @ `0x009482e0` modifies clip (`+0x362`) and reserve (`+0x360`). | Assumption: Patching `subAmmo` alone is sufficient for infinite reload-less firing (requires runtime testing to confirm no secondary check exists in `weaponDidFire`). |
| **Jetpack Power** | Confirmed: Offset `+0x278` holds jetpack power; `getPower` @ `0x008e68e4` loads it into `s0`. | Assumption: `fmov s0, #1.0` in `getPower` overrides all power depletion without causing visual glitches in HUD meter. |
| **Loadout Sync** | Confirmed: `ClientRoom::validateLoadout` @ `0x008596ac` returns 1. | Assumption: Client-side UI loadout picker allows selecting duplicate weapons without Smali/Java level UI adjustment. |
| **Runtime Execution** | Confirmed: Baseline build compiles and signs clean (`base-signed.apk`). | Assumption: Game behavior verified (CANNOT be declared complete until ADB runtime testing on actual Android hardware). |

---

## 6. Safety, Integrity & Rollback Plan (Requirements 7, 9, 10)

- **Rollback Plan:** Unmodified baseline library preserved at `native-analysis/backup/libcocos2dcpp.so`. Re-copying backup restores exact baseline.
- **Scope Limitation:** Modifications apply ONLY to gameplay logic (`libcocos2dcpp.so`) for personal testing and private LAN matches.
- **Security & Integrity Guardrails:** No changes to authentication, billing, account services, public server APIs, or app integrity verification mechanisms.
