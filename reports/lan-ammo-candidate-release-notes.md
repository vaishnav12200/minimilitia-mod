Manual-test candidate for Mini Militia Classic 0.14.4 (88), ARM64.

- RakNet LAN now uses finite ammunition reads and normal ammo/reload bookkeeping instead of the local unlimited refill.
- Offline unlimited ammunition and jetpack are retained. Custom Swap/Dual behavior and firing methods are retained.
- Only two native ammo-getter bodies changed from the preceding release. Host validation, notification display, security, authentication and network packet schemas are unchanged.

This is NOT a verified LAN fix. The exact runtime WA-triggering field remains unknown. No two-device match was performed; the user will test manually. Jetpack/custom dual compatibility with a stock host remains unverified, including finite second-hand ammo initialization.

Package checks and 1,749 instruction-fixture records pass. Original offline release is preserved. Feature-isolation split sets A-E and candidate F were prepared locally; this release contains only the single candidate APK and its checksum.

Install over a compatible project-signed build, then test offline first. In LAN, expect finite ammo and normal reloads. Start with one ordinary gun before testing same/mixed dual pairs. Verify ten-minute matches in both host/join directions before reporting a fix.

APK size: 65.94 MiB. Base app version remains 0.14.4 (88).
SHA-256: d526fbaa7d53b1b1e0c8bcfee2b98ea676de21961626bf0f875110b69860b7e5
