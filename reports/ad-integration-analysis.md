# Phase 4 — advertisement integration and limits

Date: 2026-10-08. No advertisement, entitlement, purchase, reward, consent, security or lifecycle code was changed.

## Inspected implementation

- Launcher `MmcActivity` extends `DA2Activity` and obtains `PitBoss`.
- Native `ApplicationInterface::showInterstitialAd` (ELF `0x989710`) reads `AccountInterface::getPlayerProfileData()` and calls `PlayerProfileData::getPlayerAccessLevel()`. It presents an interstitial only when access level is below 1.
- `ApplicationInterface::showInterstitial` (ELF `0x9a54c8`) resets `QuitCount` and invokes Java `DA2Activity.showInterstitial()` through JNI.
- Java `DA2Activity.showAdBanner()` and `showInterstitial()` call `PitBoss`, using the UI thread when needed.
- `PitBoss` forwards to `AdsImperator`, which constructs AppLovin MAX and AdMob adapters. Initialization consults `ComplianceManager.canRequestAds()`.
- The manifest also includes `MobileAdsInitProvider`. Removing only an activity initialization call would not eliminate all SDK startup paths.
- Native `AdBannerNode::hide(bool)` can detach the banner node; the boolean can schedule showing it again after 20 seconds. This is not proof of a persistent ad-free setting.

The access-level gate is evidence that ad presentation is associated with account access. Its entitlement source has not been fully traced. Overriding that level or unconditionally skipping presentation would bypass the game's existing distinction. The request explicitly requires leaving proprietary monetization protections unchanged, so no such patch was produced. No rewarded completion callbacks were fabricated.

## Existing behavior and next verification

No persistent ad-free user setting was found in the inspected Java bridge, native banner/interstitial functions, or targeted resource searches. This is not an exhaustive proof that no legitimate option exists. An authorized account with the game's qualifying access level uses its existing interstitial suppression path; banner behavior must be checked independently. Do not modify account records to obtain that level.

Offline behavior remains NOT TESTED. A private Wi-Fi network without internet can prevent new ad downloads, but cached ads, retry loops and banners may still appear. Local Wi-Fi connectivity is not equivalent to internet connectivity: Java `DA2Activity.isConnected()` uses `NetworkInfo.isConnected()`. Do not disable networking in the binary, because LAN gameplay depends on it.

Suggested device test: cold launch offline, navigate loadouts, play/quit/respawn repeatedly, then use isolated Wi-Fi without upstream internet. Repeat after a previously online session to check cached ads. Record banners, interstitials, popups and initialization logs separately. Do not click rewarded ads or infer reward delivery from a skipped presentation.

A guaranteed ad-free build is **not delivered**. Ad SDKs and lifecycle forwarding remain present. Permissible alternatives are the application's existing authorized access options or verified offline behavior. Both require device observation; account access is never fabricated.

Evidence: `native-analysis/phase4-ownership-decompiled.txt`, `decoded/smali/com/appsomniacs/c2/PitBoss.smali`, `decoded/smali/com/appsomniacs/core/adminion/AdsImperator.smali`, `decoded/smali/com/appsomniacs/mmc/DA2Activity.smali`, and `decoded/AndroidManifest.xml`. The experimental package verifier confirms base/application payloads remain unchanged.
