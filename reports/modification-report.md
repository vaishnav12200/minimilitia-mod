# Current gameplay correction — 2026-10-08

Status: native correction implemented; static checks and ARM64 emulation pass. Physical gameplay and private LAN require recorded device results. Earlier unlimited-ammo success claims are superseded by the latest user report of depletion after reload. Working fuel was preserved.

## Implemented

- Restored stock `Weapon::subAmmo(int)` and its meaningful integer return.
- Replaced `Weapon::getClip` / `getAmmo` with local-equipped-instance refill routines using each weapon's existing capacities. Physical counts and returned/UI counts agree after each read. Other soldiers and unequipped objects use stock clamped reads. Zero/invalid capacities are preserved.
- Combined variant: two selector branches permit matching primary/secondary choices; two `weaponProximity` branches route matching incoming primary/secondary types through ordinary pickup instead of the same-type reserve-transfer exit.
- Existing factory allocation, retain/release, slot switching, UUID generation, reload state machine, damage, cadence, projectile creation, host validation and networking remain unchanged.
- Fuel entry remains `fmov s0,#1.0; ret`, bytes `00102e1ec0035fd6`, at verified ELF VA/file offset `0x8e68e4`.
- New packager stores the modified native library uncompressed and verifies 4096-byte ZIP data alignment, required by the original split manifest. It preserves all manifest, DEX, resources and other application payloads byte-for-byte relative to the corresponding preserved split or standalone container.

## Artifacts and reproducibility

Phase B: `builds/fixed_ammo_jetpack_splits/` and `builds/fixed_ammo_jetpack_standalone/mmc-fixed-ammo-jetpack.apk`.

Phase D: `builds/fixed_ammo_dual_weapon_splits/` and `builds/fixed_ammo_dual_weapon_standalone/mmc-fixed-ammo-dual-weapon.apk`.

Scripts: [patch_fixed_gameplay.py](../scripts/patch_fixed_gameplay.py), [build_fixed_gameplay.py](../scripts/build_fixed_gameplay.py), [verify_fixed_gameplay.py](../scripts/verify_fixed_gameplay.py), [test_fixed_ammo_arm64.py](../scripts/test_fixed_ammo_arm64.py), [deploy_fixed_gameplay.sh](../scripts/deploy_fixed_gameplay.sh). Obsolete `patch_unlimited_ammo.py` CLI now refuses to apply the buggy historical RET patch. Old builders should not be used.

Original, earlier combined, and picker-only builds remain intact. Pre-edit backups: `backup/phase4-working-20261008/` and `backup/reload-fix-20261008/`. The first new outputs with compressed native entries remain under `builds/*_packaging_v1/` solely for diagnosis; use the current directories without that suffix.

## Scope and limitations

Ordinary supported gun types are the target. Dual-only utilities, throwables, objective equipment, monetized access and costs keep existing rules; universal two-slot support for every item is not claimed. Duplicate selection/pickup is implemented, but two independent working gun instances must be demonstrated on Android before calling duplicate support successful. Same-type pickups intentionally stop prioritizing ammo transfer to ordinary primary/secondary weapons.

Ads are unchanged. The earlier [advertisement inspection](ad-integration-analysis.md) found an existing access-level gate and native/Java ad SDK paths; no supported ad-free setting was demonstrated. No rewarded callback, entitlement or licensing bypass was added. Gameplay stability is a prerequisite for additional advertising changes.

Root-cause details: [reload-root-cause.md](reload-root-cause.md). Runtime results and remaining matrix: [test-results.md](test-results.md). Package evidence: [verification-report.md](verification-report.md).
