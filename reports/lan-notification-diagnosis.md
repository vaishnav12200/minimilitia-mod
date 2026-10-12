> Follow-up: the user deferred runtime capture and requested a manual-test APK. See [feature isolation and the finite-LAN-ammo candidate](lan-feature-isolation.md). The diagnosis below records the preceding investigation; its runtime cause remains unconfirmed.

# Private LAN notification diagnosis — 2026-10-12

**Status: the original error condition and static call path are identified. No physical LAN reproduction, runtime root-cause confirmation, or fix verification has been completed. No gameplay patch or replacement APK was made.**

The supplied screenshot reads **`Error:(L337H4X-WA)`**, including the hyphen and `WA` suffix. The typed `L337H4XWn` string is not present in the original ARM64 library. This distinction matters because the native library contains eleven separate `L337H4X` diagnostics.

The user reports that a friend hosts with the Play Store installation and the user joins with the modified game. The host's installed APK/version/ABI and the user's exact installed modification have not been measured. The user also reports that online servers cannot be joined. That second symptom has no captured failure reason and must not be treated as proof of a ban, authentication failure, or this same LAN error.

## Current official version

On October 12, 2026, the [official Google Play listing for `com.appsomniacs.mmc`](https://play.google.com/store/apps/details?id=com.appsomniacs.mmc&hl=en&gl=IN) described **v0.14.4, build 88**, updated March 26, 2025. This project uses that base version too. The public listing's release notes do not establish the installed version or account/device release track on the friend's phone.

Consequently, a numbered version mismatch is **not established**. Different gameplay modifications are established by the user's report: the host uses the Play Store game, while the guest uses custom ammo/fuel/dual-wield behavior. Matching version labels alone do not make those behaviors compatible.

[Recorded listing evidence](lan-notification-evidence/play-store-check.json).

## Inputs and comparison

The existing Ghidra project `native-analysis/MiniMilitiaAnalysis` was opened with `-process libcocos2dcpp.so -noanalysis -readOnly`. The latest universal-guns report, reload correction, and pickup/inventory scripts were reviewed.

| Input | SHA-256 |
|---|---|
| Preserved original ARM64 library | `2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401` |
| Final universal-dual ARM64 library | `e57f7598839ff65dd6e71e354fd2fc02ab65f414be0a1c23f2aac4a1727c1cce` |
| Final v1.0.0 standalone APK | `a3be60a39955042dd7c63fcfb384e180fbf345bf0fc06baa21b7eb01e5904e2a` |

Searches covered native strings and decoded resources/assets/smali. The error text and popup title were found in the original native library, rather than in a new mod resource. All eleven error strings remain identical in the final library. **566 exported room, networking, and weapon-state function bodies remain byte-identical** between original and final inputs, including the trigger, sender, display handler, host ammo subtraction, security flag accessor, and loadout validator. This comparison covers those ELF function bodies; it does not prove every indirect runtime behavior is unchanged.

The Ghidra project uses an image base of `0x100000`. All addresses below are **ELF virtual addresses**; add `0x100000` to find them in that project. Ghidra's recovered signatures for some large functions omit/mistype implicit parameters and leave jump tables unresolved. The `this`/data/client roles and message dispatch below were checked against ARM64 instructions, jump-table entries, and ELF vtable relocations rather than relying on the decompiler signatures alone.

## Exact triggering condition

The screenshot's diagnostic string starts at ELF/file offset **`0x108d0df`**. Its references are in:

**`ClientRoom::processWeaponCreate(char*, int, ClientEntry*)` — `0x83dae4`.**

Despite the function name, it handles multiple equip actions. Action **2** is the drop action: `WeaponManager::itemDrop` calls `addItem(item, 2)`, and the packet serializer stores that action in its event byte.

For this action, the receiver first requires an existing tracked weapon whose type and owner match the sending client. A mismatch takes a separate branch that can report **WD**. Once those checks pass, it checks the following **signed 16-bit tracked fields**:

```text
if equipAction == 2 and tracked weapon/type/owner match:
    if tracked.STID > tracked.SOID or tracked.clip < 0:
        log "BAD WEAPON STATS TYPE:... WUID:... STID:... SOID:... GUID:... C:..."
        SendClientAlert(sender, "Error:(L337H4X-WA) ...")
        take rejection/cleanup path; do not perform the normal accepted drop
    else:
        perform the normal drop and tracking update
```

| Field / branch | Exact location |
|---|---|
| Action-2 dispatch | `0x84309c`–`0x8430a4` |
| Owner/type checks | `0x8430a8`–`0x8430d8` |
| STID | `WeaponStateObject + 0x64` |
| SOID | `WeaponStateObject + 0x66` |
| STID > SOID comparison | `0x8430dc`–`0x8430f0` |
| Tracked clip | `WeaponStateObject + 0x2a` |
| Negative clip check | `0x8430f4`–`0x8430fc` |
| Bad-state branch | `0x843100` |
| Valid-state branch | `0x843a90` |
| Virtual SendClientAlert call | `0x843918`, room vtable slot `+0xd0` |

STID/SOID are the labels used by the game's own diagnostic for its tracked shot identifiers/counters. They are not the reserve/clip fields. `WeaponStateObject::init` confirms `+0x28` is reserve and `+0x2a` is clip; `reload` and `reduceMagazine` use those fields accordingly.

The WA guard is an actual room-state consistency check. The error's name alone does not classify the entire failure as anti-cheat. Elsewhere in this handler, some ownership/tracking checks consult `ServerState::isSecurityEnabled`; **the WA predicate itself has no such flag gate**. Disabling that flag would neither address the underlying ammo disagreement nor be an acceptable fix.

[Original/final disassembly](lan-notification-evidence/original-final-disassembly.txt) · [String references and original decompilation](lan-notification-evidence/original-decompiled.txt).

## Call path and event origin

The recovered drop path is:

```text
Joining client's weapon drop / stock replacement path
  WeaponManager::itemDrop                       0x95559c
  WeaponManager::addItem(item, action=2)         0x95828c
  CCNotificationCenter "WeaponCreated"
  NetworkManager::sendWeaponCreate              0x716748
  NetworkMessageDispatcher::getWeaponCreateData 0x780ac4
    message 0x1d, action 2, UUID/type/ammo/tracking fields
  NetworkManager::sendDataMessageToAll          0x718e48
  existing connection transport

LAN host receives player message
  ServerState::ProcessMessage                   0x8358d8
  ServerLAN::processPlayerMessage                0x8297fc
    unhandled gameplay message continues to the client's room
  ClientRoomLAN::processPlayerMessage            0x83d7fc
  ClientRoom::processPlayerMessage               0x85d370
    message 0x1d -> jump target 0x85d658 -> room vtable +0x180
  ClientRoom::processWeaponCreate                0x83dae4
    action 2 -> WA predicate -> rejection
  ClientRoom::SendClientAlert                    0x83aea8
    packet header 0x88, alert subtype 9, diagnostic text
    sends to the originating ClientEntry's RakNet GUID
  ServerState::Send                             0x8281fc
    existing RakNet send

Joining client receives alert
  existing receive queue / subtype dispatch
  NetworkMessageDispatcher::updateNetworkObjects 0x767868
    case 9 creates "Server Notification", received text, "CLOSE"
  AMessageBox::showAlert
```

The title string is at **`0x1089497`**. The case-9 popup construction is in the display handler around **`0x7682b8`–`0x76847f`**. It formats received alert text; it does not itself evaluate ammunition or originate WA.

The `ClientRoomLAN` vtable resolves both weapon-create and alert callbacks to the shared `ClientRoom` implementations. The room's server pointer sends through `ServerState::Send`, whose implementation uses RakNet. Thus **the original code has a complete LAN-host-originating path for this diagnostic**; an external HTTP/service response is not required. The guest's gameplay event triggers host-side evaluation and an alert back to that guest.

This establishes the static path applicable to the reported host/guest setup. It is not a packet trace identifying the sender in the user's actual match; that remains a runtime verification item. The shared room code can also be used outside LAN, so a popup title alone cannot identify an external official server.

[Event, sender, and state helpers](lan-notification-evidence/flow-decompiled.txt) · [Packet serialization/tracking](lan-notification-evidence/tracking-decompiled.txt) · [Transport](lan-notification-evidence/transport-decompiled.txt) · [Vtable and binary comparison](lan-notification-evidence/binary-comparison.json).

## Likely root cause and modification review

**The strongest current explanation is that the modified guest's locally replenished ammunition disagrees with the stock host's finite-ammo ledger.** The exact failing branch—negative clip, STID > SOID, or both—has not been observed on the phones.

The original `Weapon::getClip` and `getAmmo` read/clamp existing ammo. Their modified versions replenish owned local weapons to the original per-type capacities. The custom local fire helper invokes those getters before each held weapon's original firing method, which lets a guest keep firing without an ordinary depletion/reload cycle.

In contrast, the host's unchanged **`ClientRoom::reduceMagazine` (`0x84b164`)** subtracts reported/tracked consumption from `WeaponStateObject.clip`. Its unchanged `updateWeaponTracking` advances tracked shot IDs and accounts for consumption using the weapon model. It does not inherit the guest's unlimited-ammo policy. Sending another drop packet with a locally full clip does not repair the receiver's already-invalid ledger: **WA is checked before the normal drop's tracking update**.

The following reviews distinguish plausible causes:

| Change | Evidence and implication |
|---|---|
| Unlimited ammo | Direct mechanism for local ammo and host ammo to diverge. Highest-priority reproduction: single ordinary gun, fire beyond stock clip capacity without a normal reload, then drop/Swap. |
| Custom dual wield | Enables additional active instances and more drop/replacement situations. It may expose the same ammo failure sooner or reveal ordering/identity problems. The screenshot does not prove dual wield is required. Test one gun before same/mixed pairs. |
| Unlimited jetpack | Changes local power availability. The WA condition reads weapon tracking and clip fields, not fuel; no direct fuel-only trigger was found in this path. A separate flight/location compatibility problem remains possible. |
| Version / modifications | The base release label matches the currently advertised Play Store release; installed versions remain unmeasured. Host/guest gameplay policies differ. |
| Online joining | Unexplained without exact errors/logs. Original network/authentication/loadout checks were retained. No claim that official services permit the modified client or that rejection is confirmed. |

**Installing the same mod on both phones is a diagnostic comparison, not an established fix.** The modified APK still contains the same host ledger and WA guard, so matching guest-side refills do not automatically make unlimited ammo acceptable to the host.

The host can legitimately reject unexpected state even on a private LAN. A valid private-LAN synchronization correction must address actual state/ownership/event ordering while retaining validation. It cannot simply reset shot IDs, falsify clip reports, conceal rejection, or relax the host's checks.

## Automated evidence from this investigation

Eighteen real ARM64 instruction-fixture records pass for original and final libraries:

- Matching valid state and a zero clip take the accepted drop branch.
- A negative clip or STID > SOID takes the WA branch.
- Wrong ownership takes the separate ownership branch before WA.
- Executing the original `reduceMagazine` with clip 7 and consumption 8 produces -1; the actual WA guard then rejects that fixture state.
- Executing original local getters with clip 0/reserve 5 returns 0/5 and keeps fields unchanged. The final getters return/store fixture capacities 7/29 for the owned local weapon.

The host subtraction/guard bytes are identical in the two inputs. The experiment demonstrates the mechanism and predicate, **not a reproduced LAN match or the runtime cause of this screenshot**. Object memory, ownership, virtual capacities, and input values are fixtures.

[ARM64 results](lan-notification-evidence/arm64-fixture-results.json). The read-only log collector passed syntax and CLI checks; its two-device capture path has not been exercised because no devices are attached.

## Proposed correction

No gameplay correction is justified as verified yet. First reproduce and identify the host's failing fields and preceding events.

1. **If stock host finite-ammo enforcement is the cause:** respect its authoritative ammunition rules during LAN gameplay. A compatibility mode could retain unlimited ammo/fuel offline while using original ammo/depletion/reload behavior in LAN. Any LAN unlimited-ammo behavior would need an already-supported host configuration; none has been established here. This is a proposed behavior change, not an implemented patch.
2. **If a genuine event-order/ownership bug is demonstrated:** correct only the private-LAN path that sends or applies legitimate pickup/drop/shot events for each distinct weapon instance. Retain original UUIDs, real shot IDs, original validations, public matchmaking, and offline behavior. Validate the change against the exact failing match and control cases before packaging a candidate.
3. **If official online services reject the modified client:** report that limitation and use the official client for those services. Do not change authentication, service validation, or public-server enforcement. The current online symptom remains undiagnosed.

No popup suppression, fabricated response, security/anti-cheat toggle, or public-matchmaking alteration has been introduced.

## Two-device reproduction and log plan

**Required:** two consenting physical Android devices, authorized ADB connections, the game open on both, and a shared private Wi-Fi LAN. Current `adb devices -l` returns no devices, so no live logcat was collected. [Recorded availability/user report](lan-notification-evidence/device-status.json).

Use the collector below with the actual serials shown by ADB. It collects both game processes, package versions, ABI/model, connectivity snapshots, and optional native-library hashes from temporary APK reads. It does not install/uninstall, clear data/logs, change settings, or send game packets.

```bash
adb devices -l
python3 scripts/capture_lan_diagnostics.py \
  --host HOST_SERIAL --client CLIENT_SERIAL --seconds 300 \
  --network-mode isolated --hash-native \
  --notes "Friend stock host; modified guest; single gun fire then drop"
```

`--network-mode` records the operator's condition; it does not establish or disable internet. Turn mobile data off on both phones and use Wi-Fi with its WAN disconnected to test internet independence. Airplane mode followed by Wi-Fi alone does not isolate a router whose WAN is still connected. Repeat the same LAN test with WAN connected, keeping other conditions fixed.

Outputs stay under git-ignored `builds/lan_diagnostics/<timestamp>/`. Runtime logs can contain player/network data and should remain local. The PID-filtered log stream includes existing buffered entries; use capture times and observed popup times to identify the reproduced event. If the app restarts, repeat the capture with its new PID. The native diagnostic calls the optional FileLogger; "BAD WEAPON STATS" may not appear in Android logcat if that logger is disabled or writes only to an app file. If needed, collect an app-supported log export or add diagnostic-only logging of the existing fields without changing validation; ordinary logcat capture alone cannot guarantee field visibility.

### Test matrix

| Test | Actions / comparison | Evidence to record |
|---|---|---|
| Installed compatibility | Measure versionName/versionCode and ABIs on both; identify official vs exact modified APK/native hash | Actual builds, host/guest roles, saved loadout |
| Stock control | On an existing stock/stock test pair, shoot, reload, drop, and re-pickup the same ordinary gun | Establish whether stock behavior reproduces the error; do not delete the user's working app/data for this control |
| Reported mixed setup | Friend stock host, modified guest; one ordinary gun; no Dual | Popup time, gun UUID/type if logged, amount fired, reload/drop timing |
| Clip boundary | Shoot fewer than capacity, then exactly capacity, then beyond capacity on the mod; drop/Swap after each | First failing boundary; clip/STID/SOID from host diagnostic if available |
| Pickup/Swap control | Repeated pickup/drop without firing; stowed slot empty vs full | Separate inventory ordering from ammo consumption |
| Same and mixed dual | SPAS+SPAS, sniper+sniper, SPAS+sniper, then an automatic/special pair | Two distinct instances, shot sources, per-weapon fields, replacement/drop behavior |
| Reload / lifecycle | Manual reload, exhausted stock reserve, death/respawn, leave/rejoin | Correct counter/ownership reset and no stale UUID reuse |
| Fuel isolation | Boost without firing, then repeat weapon cases without boosting | Whether flight alone produces any notification; keep WA separate from other codes |
| Host reversal / same-mod comparison | Reverse roles; separately compare identical modified builds | Whether error follows the modified player, host, ammo boundary, or a specific action; matching mods is not a presumed fix |
| Internet isolation | Repeat on WAN-disconnected Wi-Fi with mobile data off, then WAN-connected Wi-Fi | Actual isolated reproduction or absence; same map/role/action sequence |

Do not repeat failed actions merely by closing the popup; record the preceding shot/reload/drop sequence and let the next test start from a fresh match/state.

**Acceptance for a future fix:** reproduce WA on the old build, demonstrate valid receiver clip and shot IDs on the candidate while retaining the check, then pass the same cases in both host/guest directions during actual LAN matches. Retest offline unlimited ammo, manual reload, jetpack, two-action UI, and dual wield. An emulator PASS or disappearance of a dialog alone is insufficient.

## Reproducing the static investigation

With the existing matching inputs, pyelftools/Capstone, and Unicorn available:

```bash
python3 scripts/audit_lan_notification.py
python3 scripts/test_lan_notification_arm64.py
```

For this session Unicorn was installed only under `/tmp/mmc-lan-unicorn`; the actual fixture invocation was `PYTHONPATH=/tmp/mmc-lan-unicorn python3 scripts/test_lan_notification_arm64.py`.

The Ghidra exporters are retained under `scripts/ghidra/`. Use the existing project in read-only mode, first `ExportLanNotification.java` for string references/display/trigger functions, then `ExportLanFlow.java` for helpers and transport. The flow exporter accepts an output path followed by optional qualified function names to restrict exports. The scripts do not modify the analyzed program.

**Remaining:** actual host/client versions and fingerprints, WAN-isolated reproduction, simultaneous ADB logs, the failing field values, and any narrowly scoped candidate correction plus LAN verification.
