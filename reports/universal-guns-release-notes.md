Consolidated Mini Militia Classic 0.14.4 (88) ARM64 build.

- Separate Swap and Dual pickup actions.
- 22 held gun classes: every same-gun and mixed-gun pairing is enabled (484 ordered combinations).
- Original per-gun firing/charge/burst/pellet/projectile methods retained; empty dual-hand setups reuse each gun's held transform.
- Unlimited ammo, manual-reload fix and jetpack preserved. Direct-ammo charge/spin guns refresh active ammo before firing.
- One standalone APK, 65.94 MiB, down from 78.76 MiB through valid native ZIP compression.

Validation: 3,566 ARM64 case records plus signatures, alignment, native payload, CRC and application payload checks PASS. SPAS and sniper are user-verified on a physical phone. The remaining gun classes, mixed-pair rendering, broad regression and private LAN still require manual verification; this release is marked pre-release for those limits.

Install the APK as an update without uninstalling or clearing app data. ARM64 only. The app version and signing certificate remain compatible with previous project builds.

SHA-256: a3be60a39955042dd7c63fcfb384e180fbf345bf0fc06baa21b7eb01e5904e2a

The repository is public. The release contains one downloadable APK and SHA256SUMS.txt.
