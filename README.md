# Mini Militia Classic — Universal Dual Wield

An unofficial modification and reverse-engineering project for **Mini Militia Classic 0.14.4 (88), ARM64**. It adds two distinct weapon pickup actions, enables same-gun and mixed-gun dual wielding, and retains the working unlimited ammo, manual reload, and jetpack changes.

**[Download the single APK](https://github.com/vaishnav12200/minimilitia-mod/releases/download/v1.0.0-universal-dual/MiniMilitiaClassic-Universal-Dual-v1.0.0.apk)** · [Release page](https://github.com/vaishnav12200/minimilitia-mod/releases/tag/v1.0.0-universal-dual) · [SHA256 checksum file](https://github.com/vaishnav12200/minimilitia-mod/releases/download/v1.0.0-universal-dual/SHA256SUMS.txt)

The current release is **v1.0.0 Universal Dual**, a **65.94 MiB standalone APK**. The repository and download are public. The release is marked **pre-release** because the expanded gun roster and mixed-pair visuals still need manual phone testing.

## What we have built

| Feature | How it works |
|---|---|
| Two pickup actions | **Swap** performs normal pickup; **Dual** keeps the active gun and equips the nearby gun in the other hand. |
| Universal gun pairing | A shared eligibility policy enables all 22 supported gun classes, including identical and mixed pairs. |
| Two actively held guns | Both held instances receive firing input through their original weapon methods. This goes beyond carrying two guns and switching between them. |
| Duplicate carried weapons | The inventory routing preserves two distinct instances of a matching gun in the appropriate carried slots. |
| Unlimited ammunition | Owned local weapons refill through their existing clip and reserve capacities. Special guns that read ammo fields directly refresh before firing. |
| Manual reload fix | The original ammo subtraction routine is retained, correcting the earlier patch that broke firing after manual reload. |
| Unlimited jetpack fuel | The local jetpack power getter supplies full power. |
| One-file installation | The release bundles the required ARM64 payload into one signed APK. |

Existing weapon sprites, maps, firing methods, cooldowns, and projectile routines are reused. This release does not add an ad-removal feature or change accounts, payments, authentication, or public-server validation.

## Install

1. Download **MiniMilitiaClassic-Universal-Dual-v1.0.0.apk** using the link above.
2. Open the APK on an **ARM64 Android phone** and allow installation from the app you use to open it, if Android asks.
3. Install it, launch the game, and test in an offline match first.

Only the single APK is needed; there is no separate split package to download. It can update earlier project builds that use the same signing certificate. An unrelated or official installation may have a different signature, which Android will reject as an update. Updating a compatible project build does not require uninstalling or clearing its data.

To verify your download, place the APK and `SHA256SUMS.txt` in the same folder and run:

```bash
sha256sum -c SHA256SUMS.txt
```

Expected APK SHA-256:

```text
a3be60a39955042dd7c63fcfb384e180fbf345bf0fc06baa21b7eb01e5904e2a
```

## Using Swap and Dual

While holding one supported gun, move within pickup range of another gun:

- **Swap** uses the normal pickup and inventory replacement path. It does not explicitly activate dual wielding.
- **Dual** keeps your active gun and places the nearby gun in the opposite hand. Both guns then receive firing input, with each retaining its own firing behavior.

For example, SPAS + SPAS uses two separate shotgun instances; sniper + rocket launcher uses each gun's own firing method. The same eligibility rules apply to both combinations.

Both buttons appear for an eligible pickup when the second hand is available. They hide when there is no valid nearby candidate or you leave pickup range. With both hands occupied, Dual is unavailable; Swap follows the existing drop/replacement rules. Replacing only the second held gun is not implemented. The stowed, switchable weapon slot remains separate from the two active hand slots.

### Supported guns

The shared policy covers these **22 held gun classes**:

| Group | Guns / native class names |
|---|---|
| Pistols | DEAGLE, MAGNUM, GDEAGLE, TEC9, M1881 |
| Rifles and automatic guns | UZI, MP5, AK47, M16, M14, TAVOR, MINIGUN, XM8 |
| Shotguns | SPAS / SHOTGUN, AA12 |
| Sniper | M93BA |
| Launchers and special guns | SMAW, RG6, PHASR, EMP, FLAMETHROWER, SAWGUN |

That is **484 ordered pairings**: 22 identical-gun pairings and 462 mixed-gun pairings when left/right order is counted. This is the enabled policy coverage, not a claim that every combination has passed a physical gameplay test.

Grenades, knives, shields, power-ups, objective items, and standalone projectile objects are excluded from the firearm policy. See the [technical gun roster](reports/universal-guns-release.md#recovered-gun-roster-and-policy) for exact ItemTypes and hand configuration details.

## How the modification works

The project patches the game's ARM64 native library, `libcocos2dcpp.so`, and repackages the application. It is not a rebuild of the original game's source code.

1. **Pickup and HUD:** the existing Swap and Dual icons retain separate callbacks. A shared gun-type mask checks the active weapon and the nearby candidate before offering Dual.
2. **Inventory:** normal pickup follows the preserved carried-weapon path. Explicit Dual attaches the incoming instance to the second active hand, with pointer checks and the original ownership handling.
3. **Rendering:** existing specialized dual-hand configurations are preserved. Guns that inherited an empty dual configuration reuse their own primary held configuration.
4. **Firing and ammo:** each live held gun receives one call to its original trigger method per firing update. Existing ammo getters refresh owned local instances before firing, including charge and spin-up guns that read ammo fields directly.
5. **Packaging:** builders verify the expected input hashes, restrict native edits to the intended regions, repack, align, sign, and check the resulting APKs.

The native library keeps its original file length. Exact patch bytes, preserved methods, package checks, and fixture results are recorded in the [release investigation](reports/universal-guns-release.md) and [evidence directory](reports/universal-guns-evidence/).

## Why the APK size changed

The earlier increase came from storing the **20.74 MB native game library without ZIP compression**, rather than from adding guns or graphics. The recent SPAS, two-action SPAS, and sniper builds were all the same **78.76 MiB** size.

The final standalone APK compresses the library because its manifest permits Android to extract native libraries at installation. This reduces the APK to **65.94 MiB**, saving **12.83 MiB / 16.3%**, while keeping the application payloads and native library length intact. No new map or image assets were added for universal dual wielding.

A standalone APK includes the ARM64 library that a base split alone omits. Android's installed size can also include extracted libraries, app data, and runtime caches, so it differs from the download size.

## Validation and current limits

| Check | Result |
|---|---|
| ARM64 policy, pickup, HUD, ownership, ammo, and fire-dispatch fixtures | **3,566 case records pass**, including all 484 ordered gun pairings |
| APK signatures, alignment, ZIP CRC, exact native payload, and other application payloads | **Pass** |
| Unlimited ammo, manual reload, jetpack, and offline play in earlier working builds | **User confirmed on a phone** |
| SPAS two-action pickup | **User confirmed:** both actions work, both guns fire, and buttons hide |
| Sniper dual wield | **User confirmed on a phone** |
| Remaining gun classes, mixed-pair rendering, and broad gameplay regression | **Manual verification pending** |
| Final universal build in private LAN matches | **Manual verification pending** |

The ARM64 tests execute patched instructions with fixtures for ownership, Cocos, and projectile callbacks. They check control flow and ammo handling; they do not prove rendered Android gameplay or network synchronization. Earlier LAN use reported by the user does not validate the final universal build.

For useful bug reports, include the two gun names, whether you pressed Swap or Dual, your phone/Android version, offline or LAN mode, and steps to reproduce. Helpful checks include both muzzle origins, aiming in both directions, reload, sustained firing and flight, drop/re-pickup, and death/respawn. Reports can be filed in [GitHub Issues](https://github.com/vaishnav12200/minimilitia-mod/issues).

## Development and reproduction

This repository contains patch scripts, build tooling, and investigation reports. Original APKs, native binaries, decoded assets, build outputs, and local signing keystores are excluded from Git. The downloadable APK is attached to the GitHub release.

**Cloning the repository alone is not enough to rebuild the APK.** The current builder expects the exact confirmed sniper baseline split set and standalone APK in the paths defined in `scripts/build_universal_guns.py`, plus the local signing materials. Hash checks deliberately reject incompatible inputs and other game versions.

Tooling requirements are Python 3 with `pyelftools`, `keystone-engine`, `capstone`, and `unicorn`, plus Java and Android SDK Build Tools. Existing scripts use Build Tools 35.0.0 and local SDK/signing paths; configure those for your environment. Ghidra was used for native investigation.

Once the required inputs and tool paths are prepared:

```bash
# Build isolated split and standalone outputs; existing outputs are not overwritten.
python3 scripts/build_universal_guns.py

# Verify the generated packages against their inputs and patch manifest.
python3 scripts/build_universal_guns.py --verify

# Execute the ARM64 fixture suite with Unicorn installed in your Python environment.
python3 scripts/test_universal_guns_arm64.py
```

| Path | Purpose |
|---|---|
| [scripts/patch_universal_guns.py](scripts/patch_universal_guns.py) | Shared gun policy, scoped hand configurations, and local firing helper |
| [scripts/build_universal_guns.py](scripts/build_universal_guns.py) | Final package construction and verification |
| [scripts/test_universal_guns_arm64.py](scripts/test_universal_guns_arm64.py) | Native ARM64 fixtures |
| [scripts/deploy_universal_guns.sh](scripts/deploy_universal_guns.sh) | Verified split update through ADB for development |
| [reports/universal-guns-release.md](reports/universal-guns-release.md) | Current architecture, roster, size audit, and test limits |
| [reports/dual-wield-ui-phase5.md](reports/dual-wield-ui-phase5.md) | Separate pickup actions and SPAS verification history |
| [reports/duplicate-inventory-root-cause.md](reports/duplicate-inventory-root-cause.md) | Why matching carried weapons were previously replaced |
| [reports/reload-root-cause.md](reports/reload-root-cause.md) | Reload failure and corrected unlimited-ammo approach |

Earlier reports document intermediate builds and their status at the time. Use this README and the universal-guns release report for the current release.

Mini Militia Classic belongs to its original developers. This project is unofficial and is not affiliated with them.
