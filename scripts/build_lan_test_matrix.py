#!/usr/bin/env python3
"""Build isolated A-E split sets plus F finite-LAN-ammo candidate and single APK.
Never overwrites the working release or existing matrix outputs.
"""
import argparse
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
from elftools.elf.elffile import ELFFile
from patch_fixed_gameplay import ROOT, GETTERS, sha
from patch_lan_ammo_compat import patch, FINAL_SHA
from build_fixed_gameplay import repack_native, check
from build_split_package import REQUIRED_SPLITS, zipalign_and_sign_split_set, ZIPALIGN, APKSIGNER, KEYSTORE, KEY_ALIAS, KEY_PASS
from build_universal_guns import repack_standalone

DEST = ROOT/'builds/lan_feature_isolation_20261012'
EVIDENCE = ROOT/'reports/lan-feature-isolation-evidence'
SOURCES = ROOT/'builds/universal_dual_wield_final_splits'
OLD_APK = ROOT/'builds/universal_dual_wield_final/MiniMilitiaClassic-Universal-Dual-v1.0.0.apk'
APK_NAME = 'MiniMilitiaClassic-LAN-Ammo-Compatibility-Test.apk'
ORIGINAL_SHA = '2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401'
TAGS = ['A_original', 'B_jetpack_only', 'C_ammo_getters_only', 'D_dual_only', 'E_combined', 'F_lan_ammo_candidate']


def inputs():
    original = (ROOT/'native-analysis/backup/libcocos2dcpp.so').read_bytes()
    with zipfile.ZipFile(OLD_APK) as z:
        final = z.read('lib/arm64-v8a/libcocos2dcpp.so')
    assert sha(original) == ORIGINAL_SHA and sha(final) == FINAL_SHA
    assert (ROOT/'native-analysis/libcocos2dcpp.so').read_bytes() == original
    with zipfile.ZipFile(SOURCES/'split_config.arm64_v8a.apk') as z:
        assert z.read('lib/arm64-v8a/libcocos2dcpp.so') == final
    return original, final


def variants():
    original, final = inputs()
    ds = ELFFile(io.BytesIO(original)).get_section_by_name('.dynsym')
    def extent(name):
        s = ds.get_symbol_by_name(name)[0]
        return s['st_value'], s['st_size']  # these targeted executable spans have file offset == VA
    b, c, d = bytearray(original), bytearray(original), bytearray(final)
    fuel, size = extent('_ZN22SoldierLocalController8getPowerEv')
    b[fuel:fuel+8] = final[fuel:fuel+8]
    for name, va, field, virtual in GETTERS:
        assert extent(name) == (va,204)
        c[va:va+204] = final[va:va+204]
        d[va:va+204] = original[va:va+204]
    d[fuel:fuel+8] = original[fuel:fuel+8]
    fire, size = extent('_ZN22SoldierLocalController4fireEf')
    d[fire:fire+size] = original[fire:fire+size]
    manifest = json.loads((ROOT/'reports/universal-guns-evidence/native-patches.json').read_text())
    helper = next(x for x in manifest['changes'] if x.get('function') == 'SoldierLocalController::fire helper')
    off = int(helper['file_offset'],16)
    length = len(bytes.fromhex(helper['replacement']))
    assert final[off:off+length] == bytes.fromhex(helper['replacement'])
    d[off:off+length] = original[off:off+length]
    candidate, candidate_manifest = patch(final)
    natives = dict(zip(TAGS,[original,bytes(b),bytes(c),bytes(d),final,candidate]))
    assert natives['A_original'] == original and natives['E_combined'] == final
    # C cannot transplant E's helper: its code space is live in original inventory.
    # D intentionally restores original finite-ammo firing rather than using that helper.
    notes = {
        'A_original': 'Original native gameplay, re-signed with project test certificate; not the official Play Store signature.',
        'B_jetpack_only': 'Original native plus existing eight-byte unlimited jetpack patch.',
        'C_ammo_getters_only': 'Original native plus corrected unlimited getClip/getAmmo; E direct-ammo fire helper is excluded because its code space is live in original inventory. Use ordinary guns first; this is a getter-component isolation, not full special-gun equivalence with E.',
        'D_dual_only': 'Custom inventory/pickup/UI and 22-gun hand transforms; original finite ammo, original fuel and original two-slot firing dispatcher. Second-hand finite-ammo initialization remains a runtime test item.',
        'E_combined': 'Native byte-identical to preserved working offline universal-dual release.',
        'F_lan_ammo_candidate': 'E with only two ammo getters gated for verified LAN ConnectionType 2; fuel and custom dual behavior retained. Not a verified LAN fix.',
    }
    for tag,native in natives.items():
        assert len(native) == len(original)
        # Every room/network/weapon-state body from the prior audit stays original.
        audit = json.loads((ROOT/'reports/lan-notification-evidence/binary-comparison.json').read_text())
        for record in audit['functions']:
            if record['function'].startswith(('ClientRoom::','ClientRoomLAN::','ServerState::','ServerLAN::','NetworkManager::','NetworkMessageDispatcher::','RakNetLocalServer::','WeaponStateObject::')):
                va, length = int(record['elf_va'],16), record['bytes']
                assert sha(native[va:va+length]) == record['original_sha256']
    return natives, notes, candidate_manifest


def verify():
    natives, notes, manifest = variants()
    saved = json.loads((DEST/'verification.json').read_text())
    assert saved['candidate_patch'] == manifest
    for tag,native in natives.items():
        assert saved['variants'][tag]['native_sha256'] == sha(native)
        for name in REQUIRED_SPLITS:
            record,_ = check(DEST/tag/name,SOURCES/name,native)
            assert record == next(r for r in saved['variants'][tag]['splits'] if r['apk'] == name)
    record,_ = check(DEST/APK_NAME,OLD_APK,natives[TAGS[-1]],require_stored=False)
    assert record == saved['candidate_standalone']
    assert sha(OLD_APK.read_bytes()) == saved['preserved_offline_apk_sha256']
    print('PASS: six signed split sets and candidate single APK; scope/payload/alignment/signatures; offline source preserved')
    return saved


def build():
    if DEST.exists():
        raise SystemExit('Refusing overwrite of existing LAN matrix')
    natives, notes, manifest = variants()
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    saved = dict(status='PACKAGE CHECKS ONLY; LAN runtime NOT TESTED',candidate_patch=manifest,
                 preserved_offline_apk_sha256=sha(OLD_APK.read_bytes()),variants={})
    logs = []
    with tempfile.TemporaryDirectory(prefix='lan-matrix-',dir=ROOT/'builds') as folder:
        temp = Path(folder)
        output = temp/'outputs'
        output.mkdir()
        for tag,native in natives.items():
            source = temp/tag
            source.mkdir()
            lib = source/'libcocos2dcpp.so'
            lib.write_bytes(native)
            for name in REQUIRED_SPLITS:
                if name == 'split_config.arm64_v8a.apk':
                    repack_native(SOURCES/name,lib,source/name)
                else:
                    shutil.copy2(SOURCES/name,source/name)
            signed = output/tag
            zipalign_and_sign_split_set(source,signed)
            records = []
            for name in REQUIRED_SPLITS:
                record,log = check(signed/name,SOURCES/name,native)
                records.append(record)
                logs.append(tag+'/'+name+'\n'+log)
            result = dict(native_sha256=sha(native),notes=notes[tag],splits=records,
                          runtime='NOT TESTED',base_version='0.14.4 (88)')
            saved['variants'][tag] = result
            (signed/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
            (signed/'SHA256SUMS.txt').write_text(''.join(r['sha256']+'  '+r['apk']+'\n' for r in records))
        lib = temp/'candidate.so'
        lib.write_bytes(natives[TAGS[-1]])
        unsigned,aligned,final = temp/'unsigned.apk',temp/'aligned.apk',output/APK_NAME
        repack_standalone(OLD_APK,lib,unsigned)
        subprocess.run([ZIPALIGN,'-p','-f','4',str(unsigned),str(aligned)],check=True,capture_output=True,text=True)
        subprocess.run([APKSIGNER,'sign','--ks',str(KEYSTORE),'--ks-key-alias',KEY_ALIAS,
                        '--ks-pass','pass:'+KEY_PASS,'--out',str(final),str(aligned)],check=True,capture_output=True,text=True)
        record,log = check(final,OLD_APK,natives[TAGS[-1]],require_stored=False)
        saved['candidate_standalone'] = record
        logs.append(APK_NAME+'\n'+log)
        (output/'verification.json').write_text(json.dumps(saved,indent=2)+'\n')
        (output/'SHA256SUMS.txt').write_text(record['sha256']+'  '+APK_NAME+'\n')
        output.rename(DEST)
    (EVIDENCE/'package-verification.json').write_text(json.dumps(saved,indent=2)+'\n')
    (EVIDENCE/'signatures.txt').write_text('\n'.join(logs))
    verify()
    print(DEST/APK_NAME)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    verify() if args.verify else build()
