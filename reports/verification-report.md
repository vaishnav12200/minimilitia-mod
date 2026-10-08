# Verification — 2026-10-08

Both corrected Phase B and combined builds pass signature, alignment, CRC, ELF mutation-scope, original-byte checks and non-native application payload preservation. Verification separately checks native ZIP storage and 4096-byte ZIP data alignment. These structural checks do not establish gameplay success.

| Function/site | ELF VA | File offset | Change |
| --- | --- | --- | --- |
| Weapon::subAmmo(int) entry | 0x9482e0 | 0x9482e0 | c0035fd6 → ff4301d1 (restore stock) |
| Weapon::getClip() | 0x947954 | 0x947954 | Original 204 bytes → 116-byte routine + NOP padding |
| Weapon::getAmmo() | 0x947a20 | 0x947a20 | Original 204 bytes → 116-byte routine + NOP padding |
| LoadoutMenu::onPrimary | 0x69f3d4 | 0x69f3d4 | a1000054 → 05000014; destination 0x69f3e8 |
| LoadoutMenu::onSecondary | 0x69f514 | 0x69f514 | a1000054 → 05000014; destination 0x69f528 |
| WeaponManager::weaponProximity primary type | 0x9578c8 | 0x9578c8 | e1030054 → 1f000014; destination 0x957944 |
| WeaponManager::weaponProximity secondary type | 0x957980 | 0x957980 | a1030054 → 1d000014; destination 0x9579f4 |
| SoldierLocalController::getPower() | 0x8e68e4 | 0x8e68e4 | 00102e1ec0035fd6 preserved exactly |

Virtual addresses are mapped through PT_LOAD independently; equality with file offsets here is verified, not assumed. Ghidra displays these addresses plus 0x100000. Patched getters use AAPCS64 x0=this, w0=count, preserve x19/LR, and restore aligned SP. Existing capacity virtual dispatch and dynamic GOT relocation are validated. Full original/replacement bytes and assembly are in each `verification.json`.

Original ELF: `2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401`.

Phase B ELF: `6a0ab3ca5dce5ea76f806c92671f45224b394792adc8ab18f7d94c4f69ee1743`.

Combined ELF: `8cac1bfb7c7c523bbfbb2c33ea3c446acb2d8db24d0a639799b04d74b8026f60`.

Signing certificate SHA-256: `a19c717feeee28b67070bfd3e1f6f519785d804c68e39e55be59710e55451f5e`, identical to preserved test builds across all four splits and standalone. Original distribution certificate is not claimed.

Combined standalone APK SHA-256: `3c01bda3d733c64a5e8913af72f8224a666dd502fc8a40c882e2e1ae9411fff1`.

ARM64 emulation: 105 synthetic cases PASS. Includes original reload-completion instructions with stub capacities, setters and callback, register/stack preservation, invalid capacities, local three-slot matching, nonlocal/null/dropped behavior, and 1000 simulated direct clip decrements with intervening getter reads. It does not exercise actual projectile creation, game UI, networking or Android scheduling.

Machine-readable outputs: [ammo/fuel package](reload-fix-evidence/fixed_ammo_jetpack-verification.json), [combined package](reload-fix-evidence/fixed_ammo_dual_weapon-verification.json), [emulation](reload-fix-evidence/arm64-emulation.json). APK signature verbose logs are beside those files. Original call/store audit and disassembly are in the same evidence directory.

First install attempt found the inherited packaging bug: compressed native entry cannot satisfy the split base manifest's extractNativeLibs=false. The current packager corrects it without changing the manifest. Subsequent attempts were blocked by the phone's USB installation prompt; final device outcome is recorded in test-results.md.

Physical deployment PASS: the final split set installed over USB and launched. The installed ARM64 split was pulled back and compared byte-for-byte with the build. Gameplay input was blocked by MIUI; the user chose manual tests. See [device-installation.json](reload-fix-evidence/device-installation.json).
