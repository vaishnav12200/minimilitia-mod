# Mini Militia Classic — Technical Native Modification Report

**Binary Target:** `libcocos2dcpp.so` (ARM64 v8-A)  
**ELF SHA-256:** `2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401`  
**Ghidra Version:** 12.1.4 (OpenJDK 25)  
**Status:** Automated analysis completed (831s). Symbol export & decompilation verified.

---

## 1. Ghidra Analysis Verification

- **Status:** Automatic analysis completed successfully in Ghidra project `/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/MiniMilitiaAnalysis`.
- **Symbols:** 24,141 demangled C++ symbols preserved in symbol table.
- **Decompilation Artifacts:** Exported to `/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/decompiled_functions.txt`.

---

## 2. Objective Analysis & Verification Findings

### Objective 1 — Ammunition Handling Functions
- **Primary Function:** `Weapon::subAmmo(int)`
  - **ELF Offset:** `0x009482e0` (Ghidra RAM: `0x00a482e0`, Length: 344 bytes)
  - **Signature:** `int Weapon::subAmmo(int amount)`
  - **Related Functions:**
    - `Weapon::setAmmo(int, bool)` @ ELF `0x009481e0` (Modifies reserve ammo at offset `+0x360`)
    - `Weapon::setClip(int)` @ ELF `0x00948104` (Modifies current clip at offset `+0x362`)
    - `Weapon::startReloadWeapon()` @ ELF `0x00947ee8`
    - `ClientRoom::processReloadRequest(...)` @ ELF `0x00873974`
  - **Decompiled Mechanism:**
    ```c
    int Weapon::subAmmo(Weapon* this, int amount) {
        short clip = Weapon::getClip(this);
        if (clip <= amount) amount = clip;
        Weapon::setClip(this, clip - amount, 0); // Decrements clip
        short ammo = Weapon::getAmmo(this);
        Weapon::setAmmo(this, ammo - remaining); // Decrements reserve ammo
        return total_subtracted;
    }
    ```
  - **Patch Verification:** Patching entry point `0x009482e0` with `ret` (`0xc0035fd6`) or returning early bypasses clip and reserve ammo decrements, providing unlimited ammunition.

### Objective 2 — Jetpack Fuel Consumption Functions
- **Primary Functions:**
  - `SoldierLocalController::setPower(float)` @ ELF `0x008e68c4` (Length: 32 bytes)
  - `SoldierLocalController::getPower()` @ ELF `0x008e68e4` (Length: 24 bytes)
  - `SoldierLocalController::hasPower()` @ ELF `0x008ec7b8` (Length: 60 bytes)
- **Decompiled Mechanism:**
  ```c
  void SoldierLocalController::setPower(SoldierLocalController* this, float power) {
      *(float *)(this + 0x278) = power; // Offset +0x278 holds jetpack fuel
  }
  float SoldierLocalController::getPower(SoldierLocalController* this) {
      return *(float *)(this + 0x278);
  }
  ```
- **Patch Verification:** Power value stored as IEEE 754 float at `+0x278`. Patching `setPower` to enforce max power or NOPing fuel reduction during thrust in `updateStep` provides unlimited jetpack fuel.

### Objective 3 — Weapon Inventory & Duplicate Selection Validation
- **Primary Functions:**
  - `SoldierLocalController::addWeapon(Weapon*)` @ ELF `0x008e6934` (Length: 1324 bytes)
  - `SoldierLocalController::addPrimaryWeapon(Weapon*)` @ ELF `0x008e6ebc`
  - `SoldierLocalController::addSecondaryWeapon(Weapon*)` @ ELF `0x008e70b0`
  - `ClientRoom::validateLoadout(LoadoutObject, ClientEntry*)` @ ELF `0x009596ac`
- **Memory Layout:**
  - Primary Weapon pointer: `*(Weapon**)(this + 0x1C8)`
  - Secondary Weapon pointer: `*(Weapon**)(this + 0x1D0)`
  - Dual Wield Weapon pointer: `*(Weapon**)(this + 0x1D8)`
- **Validation Findings:**
  `ClientRoom::validateLoadout` returns `1` (unconditional true), confirming host server synchronization accepts custom and duplicate weapon combinations.

### Objective 4 — Offline Gameplay & Private LAN Synchronization
- **Primary Functions:**
  - `ClientRoomLAN` @ ELF `0x00935bd8`
  - `ClientRoomLAN::validateBallistics` @ ELF `0x009596c8` (Returns `1`)
  - `ClientRoomLAN::validatePlayerDamage` @ ELF `0x009596e4` (Returns `1`)
- **Networking Mechanism:**
  LAN multiplayer uses RakNet P2P/host networking. Host authority operates locally without cloud auth verification.

---

## 3. Incremental Modification Protocol

1. **Backup Verification:** Original native library backed up to `native-analysis/backup/libcocos2dcpp.so`.
2. **Patch Application:** Reproducible Python patching script at `scripts/patch_native.py`.
3. **APK Rebuild & Signing:** `scripts/build.sh` and `scripts/sign.sh`.
4. **Device Testing:** Runtime deployment via ADB before declaring full success.
