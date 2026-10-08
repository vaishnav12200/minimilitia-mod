# Phase 5 — shared pairing policy and sniper candidate

The physical SPAS UI gate passed: user reports “Both actions work; both guns fire; buttons hide”. The exact confirmed package is preserved in `backup/dual-wield-ui-verified-20261008/`. This revision adds one gun class, M93BA (ItemType 10), and remains experimental until the physical sniper test passes.

The shared `pair_guard` compiler takes explicit `(primary type, incoming type)` pairs and emits the same policy for HUD visibility and controller acceptance. Current matrix: `(9,9)` SPAS and `(10,10)` M93BA. Mixed pairs and other classes are rejected by Dual and show normal Swap only. This removes the SPAS-only eligibility implementation; new pairs are policy entries rather than new inventory/firing implementations.

Only three spans change from confirmed UI native SHA `77f075ede045373df1f631b2cea0f0ce421bab0f971214e9c38e235de5a87191`:

| File offset | Bytes | Change |
|---|---:|---|
| 0x8e6990 | 224 | Shared pair predicate in existing explicit-Dual pickup guard; normal routing and pointer/occupied-slot checks preserved |
| 0x669d00 | 216 | Identical pair matrix in UI eligibility; existing button rendering/spacing/reset retained |
| 0x39fbf0 | 8 | M93BA ABS64 vtable relocation for dual configuration (+0x3d8, ELF VA 0x133a328) now resolves to its existing setPrimaryConfiguration instead of inherited empty Item::setDualConfiguration |

The real per-instance M93BA::triggerPull at ELF 0x6c1c5c uses Weapon::basicTriggerPull(true), and M93BA::setPrimaryConfiguration at 0x6c2064 sets the held sprite/anchor/root transform. Existing dual input dispatch and per-frame update already address the two distinct instances. All ammo, reload, fuel, trigger/projectile/damage/input/network functions and SPAS held transform are unchanged. A scope check ensures all other library bytes are identical.

428 ARM64 cases PASS: shared HUD/controller policy, both same-class pairs, disabled mixed and unsupported pairs, normal pickup preservation, occupied dual, alias/null guards, utilities, enabled state, scaling/spacing, positions and hide reset. Virtual Cocos/ownership callbacks are modelled; this is not physical rendering/projectile validation. Package alignment, signature, native storage, CRC and application-payload equality PASS. Full replacement/original bytes and assembly are in the split verification.json.

Deployment attempt: ADB returned `device 241266d60c20 not found`; this candidate has not been installed or physically tested. The last successful installed build is the confirmed SPAS two-action UI. USB reconnection or manual APK installation is required.

## Physical sniper Test B

1. Offline, use the M93BA sniper (type 10), hold one and approach another. Confirm both Swap and Dual icons appear.
2. Swap must remain normal pickup; Dual must show a separate rifle in each hand.
3. Fire repeatedly; verify both rifles shoot from their own muzzle positions, with sniper projectiles and normal individual cooldowns.
4. Aim in all directions, change facing, try primary scope/zoom and flight, reload, then drop/pick up, die/respawn, and retest sustained ammo/fuel.
5. Confirm the already verified SPAS UI still works. Other sniper models (e.g. M14), rocket launchers and mixed pairs are not enabled in this revision.

Only after this class passes should the next class (SMAW rocket launcher) be added. Shared-policy mixed pairs follow same-class checks. Reload animations for both hands and safe second-held replacement remain part of pending broader regression. Private LAN remains pending offline validation.

Builder: scripts/build_dual_wield_sniper.py. Deployment: scripts/deploy_dual_wield_sniper.sh. Verify with `python3 scripts/build_dual_wield_sniper.py --verify`; tests with `PYTHONPATH=/tmp/mmc-unicorn-tests:scripts python3 scripts/test_dual_wield_sniper_arm64.py`. Builders refuse overwrite. Rollback: scripts/deploy_dual_wield_ui.sh restores the physically confirmed SPAS UI package without clearing data.

Native SHA: `a7a01b33290e7de4c8e0d799c310edf00e886b470bd8b745cbc2bdf3dfc2555f`.
Standalone APK SHA: `4f5223272bb4205f5c7dcdac45b4aa9858f0a531227752e71a33754efd16687b`.
