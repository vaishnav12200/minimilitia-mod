# LAN feature isolation and ammo compatibility candidate — 2026-10-12

**A signed candidate is ready for manual testing. It is not a verified LAN fix.** The user explicitly deferred connecting phones and asked for an APK to test later. The exact runtime triggering field remains unknown; no two-device capture or ten-minute match was performed.

The user confirms the Play Store game works in private LAN, the modified game repeatedly reports WA, and the previous modified offline build works. These observations narrow the investigation but do not distinguish negative clip, STID/SOID disagreement, or another event sequence that produces either condition.

## Deliverable status

| Requested result | Current evidence |
|---|---|
| Root cause and triggering field | WA predicate statically established; actual failing field not measured. Ammo-policy mismatch remains a hypothesis. |
| Feature isolation | A–E signed split sets prepared; additional F compatibility candidate prepared. |
| Before/after behavior | Instruction fixtures: E refills in LAN; F does not. Real match before/after pending. |
| Smallest correction | Candidate changes only `Weapon::getClip` and `getAmmo`, adding a LAN-only gate. It is a proposed compatibility policy, not a verified bookkeeping repair. |
| Ghidra findings | Existing project reused read-only; original LAN mode setter/export and call-site disassembly added. |
| Signed test build | Six four-APK split sets and one standalone F APK verified. |
| Two-device results | Not performed: no devices connected, then user elected to test manually later. |
| Offline behavior | Offline refill, jetpack getter, pickup/HUD and two-hand dispatch fixtures pass; working release preserved exactly. Candidate physical offline regression pending. |
| Stock-host limitations | Finite ammo respected by F; custom pairs, finite second-hand initialization, jetpack and ownership/shot tracking still require actual host acceptance. |

## What changed in candidate F

Original Ghidra findings establish that **`NetworkManager::useRakNetLAN` (`0x7186bc`) calls `setConnectionType(2)`**. `setConnectionType` at `0x718608` writes `_currentConnectionType` through GOT `0x13bf448`; the dynamic relocation resolves that exact global. `MenuLayer::init` resets the connection type to zero. The original methods and their call sites are retained in [mode decompilation](lan-notification-evidence/mode-decompiled.txt) and [mode call-site disassembly](lan-notification-evidence/mode-callers.txt). Addresses are ELF virtual addresses; the existing Ghidra image base adds `0x100000`.

The final universal build's two local ammo getters were the only candidate mutation spans:

| Function | ELF VA | Reserved body |
|---|---:|---:|
| `Weapon::getClip` | `0x947954` | 204 bytes |
| `Weapon::getAmmo` | `0x947a20` | 204 bytes |

They now check the existing connection type before their owned-weapon refill:

```text
LAN type 2: original clamped read of actual clip/reserve; do not refill fields
Other connection types: retain the preceding mod's existing behavior
Missing mode pointer: finite read fallback
```

The gate uses the existing getter stack frame and its existing stock-read branch. It adds no new global state, allocation, code cave, network message or acknowledgement. Candidate machine code occupies 140 bytes per 204-byte body; remaining space stays NOP padded. No negative host field is rewritten or hidden. Clamping a returned negative local value to zero is the original read behavior, not a repair of the host ledger.

**All bytes outside these two bodies match the preserved universal build**, including fuel, dual controls/routing/hand transforms, local firing helper, reload code, shot/projectile routines, host validation, notification display and networking. Public matchmaking/authentication/integrity/security methods were not changed. In particular, WA still rejects the same invalid receiver state.

This policy is expected to stop local ammo replenishment from extending shots beyond the stock host's ledger. It is not evidence that the actual screenshot was caused by that mechanism. It cannot repair an independently incorrect shot ID, aliased weapon or event-order defect.

## Isolation builds

All sets are under `builds/lan_feature_isolation_20261012/`, use base version **0.14.4 (88)** and the existing project test certificate, and contain `base.apk`, `split_config.arm64_v8a.apk`, `split_config.en.apk`, and `split_config.xxhdpi.apk`.

| Set | Native behavior | Runtime status |
|---|---|---|
| A — `A_original` | Exact original native library; original gameplay logic, re-signed project package | Not tested |
| B — `B_jetpack_only` | A plus the existing eight-byte unlimited jetpack patch | Not tested |
| C — `C_ammo_getters_only` | A plus corrected getClip/getAmmo refill routines | Not tested |
| D — `D_dual_only` | Universal inventory/pickup/HUD/hand changes, with original finite ammo, original fuel and original firing dispatcher | Not tested |
| E — `E_combined` | Exact preserved universal-dual native library | Previous offline user report applies; LAN isolation test not performed |
| F — `F_lan_ammo_candidate` | E plus finite local ammo reads in RakNet LAN type 2 | Not tested |

**Isolation caveat:** C isolates the existing corrected getter component. The final E special-gun firing helper lives inside former `addWeapon` code that is bypassed by the custom inventory route but is still live in A. Transplanting that helper into C would corrupt original inventory; no new relocation/cave patch was invented for this isolation exercise. Therefore C/E differences include both dual modifications and that coupled helper. Use ordinary weapons for the first ammo comparison; a C pass with an E failure does not alone prove dual wield is responsible. D removes the helper and restores the original dispatcher, which already invokes primary and dual triggers independently.

A uses original gameplay logic, but its signing certificate is the project's certificate, not the Play Store certificate. It is not a complete official-installation control for signing/service behavior. It updates project-signed installations; it cannot update a differently signed Play Store app. No installation, uninstall or app-data clear was attempted.

## Artifact fingerprints

Standalone candidate: **`MiniMilitiaClassic-LAN-Ammo-Compatibility-Test.apk`**, 69,139,103 bytes (**65.94 MiB**).

- Candidate APK SHA-256: `d526fbaa7d53b1b1e0c8bcfee2b98ea676de21961626bf0f875110b69860b7e5`
- Candidate native SHA-256: `2c7da19a929d2d5306b0bb6138ae616fac06739c0add8885aa940091d32a1082`
- Preserved offline APK SHA-256: `a3be60a39955042dd7c63fcfb384e180fbf345bf0fc06baa21b7eb01e5904e2a`

The original analysis and backup libraries were untouched. The prior final release and split set were not overwritten. The builder refuses to overwrite existing matrix outputs. Each split directory and the top-level standalone directory contain checksum files and verification manifests.

## Verification performed

**Package checks pass** for all six split sets and the standalone candidate: existing signer, consistent split signer, alignment, ZIP CRC, expected native payload, and equality of every other application payload against the preserved containers. Original room/network/state bodies are checked for all variants; no enforcement method was changed.

**1,749 ARM64 instruction-fixture records pass**, covering:

- Original vs modified getters, LAN/offline mode, all three owned slots, unowned objects, negative/zero/positive stored ammo, and unchanged reload/shot-ID fields during reads.
- Original `useRakNetLAN` and `setConnectionType` execution, followed by finite candidate reads; transition to mode zero restores refill.
- Actual reload-completion instructions: finite LAN fixture clip 3/reserve 5 becomes clip 7/reserve 1 for capacity 7; offline refill remains full.
- Actual fuel getters: original variants return stored power; B/E/F retain the full-power override.
- All 484 ordered gun pairs in D finite mode, F LAN finite mode, and F offline refill mode: distinct firing callbacks over two updates, pickup ownership guards and separate HUD actions.

The preceding offline universal suite also still passes all **3,566** fixture records after the shared firing fixture was extended. Its package/native inputs remain unchanged.

Capacities, ownership callbacks, triggers and Cocos objects are fixtures. They do not execute Android rendering, real projectiles, damage networking, a stock host's receipt, or ten-minute matches. In particular, the dual-fire fixture starts both guns with valid finite ammunition; it does **not** prove stock network pickup assigns valid ammo to every new custom second-hand gun.

[Package manifests and patch assembly](lan-feature-isolation-evidence/package-verification.json) · [ARM64 results](lan-feature-isolation-evidence/arm64-tests.json) · [Signer logs](lan-feature-isolation-evidence/signatures.txt).

## Manual testing

Install the single F APK as an update over an existing project-signed build. The previous offline APK remains available for rollback as an update. Test offline first: unlimited ammo, manual reload, sustained jetpack, Swap and Dual, and both guns firing.

Then use two consenting devices on the same base version and isolated Wi-Fi. Start with a single ordinary gun in F joining the friend's stock host. In LAN, ammunition should now deplete normally and reload normally. Fire fewer than, exactly, and beyond one stock clip with proper reloads; test pickup, drop and Swap after each. Record whether WA occurs before shooting or specifically after reload/pickup/drop, and whether the host disconnects the client. Repeat with same-gun and mixed Dual only after the ordinary-gun case is known.

For isolation, run A–E with an unchanged peer, map, weapon, starting ammo and action sequence. Do not switch builds in the middle of a match. Repeat host and join directions; compare identical test builds on both phones separately. Record the actual installed native fingerprint, not only the common version label.

ADB split installation, when the phones are later available:

```bash
python3 scripts/build_lan_test_matrix.py --verify
adb -s PHONE_SERIAL install-multiple --no-incremental -r \
  builds/lan_feature_isolation_20261012/F_lan_ammo_candidate/base.apk \
  builds/lan_feature_isolation_20261012/F_lan_ammo_candidate/split_config.arm64_v8a.apk \
  builds/lan_feature_isolation_20261012/F_lan_ammo_candidate/split_config.en.apk \
  builds/lan_feature_isolation_20261012/F_lan_ammo_candidate/split_config.xxhdpi.apk
```

Collect both game processes for each ten-minute run with the [existing collector](../scripts/capture_lan_diagnostics.py):

```bash
python3 scripts/capture_lan_diagnostics.py \
  --host HOST_SERIAL --client CLIENT_SERIAL --seconds 660 \
  --network-mode isolated --hash-native \
  --notes "F candidate; host and client builds; map; starting weapon; planned action sequence"
```

Keep raw outputs local under git-ignored `builds/lan_diagnostics/`. Record popup/video times, ammo and reload observations, weapon names, dual state, and disconnects. The host's optional FileLogger may need an app-supported export to obtain clip/STID/SOID values if they are absent from logcat. The collector does not guarantee that these native fields are logged and does not modify the app to force them into logs.

### Required result sheet

For each A–F set, fill host and guest build/ABI, tested direction, weapon, dual state, firing/reload/pickup/drop sequence, exact error suffix/time, host disconnect, host clip/STID/SOID evidence and crashes. Every row is currently **NOT TESTED**:

| Build | Host direction | Join direction | Shooting/reload | Pickup/drop | Death/respawn | 10-minute match |
|---|---|---|---|---|---|---|
| A | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested |
| B | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested |
| C | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested |
| D | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested |
| E | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested |
| F | Not tested | Not tested | Not tested | Not tested | Not tested | Not tested |

F acceptance requires ten minutes in each host/join direction, multiple weapons, manual/automatic reload, pickup/drop, dual projectile/tracking observations, and death/respawn, with no rejection, invalid ammo/counters or crash. Compare the preceding E failure with F using the same failing sequence. Validate receiver state rather than only closing or losing a popup.

## Known limits and next correction decision

- No exact runtime root cause is claimed. A counter-order defect remains possible even if finite ammo stops one symptom.
- Jetpack and custom dual behavior are preserved in F, but their stock-host compatibility is unverified. D/B isolate them. Finite second-hand initialization and all custom pair representations need device evidence.
- F does not manufacture missing ammo or reset negative host fields/IDs. A host or peer that rejects a custom pair retains that authority.
- Online joining remains undiagnosed. No authentication, service rejection or matchmaking workaround was attempted.
- Candidate offline preservation is verified at instruction/package level; physical candidate regression is still required.

Build/test commands:

```bash
# Existing outputs are intentionally not overwritten.
python3 scripts/build_lan_test_matrix.py
python3 scripts/build_lan_test_matrix.py --verify
python3 scripts/test_lan_compatibility_arm64.py
```

For this session Unicorn is installed under `/tmp/mmc-lan-unicorn`, so tests used `PYTHONPATH=/tmp/mmc-lan-unicorn`. Patch source: [patch_lan_ammo_compat.py](../scripts/patch_lan_ammo_compat.py). Full prior call-path investigation: [lan-notification-diagnosis.md](lan-notification-diagnosis.md).
