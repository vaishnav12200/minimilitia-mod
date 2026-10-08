#!/usr/bin/env python3
"""Build/verify isolated inventory splits and phone-installable standalone APK.
Inputs are the latest device-tested corrected-ammo build, never old combined.
"""
import argparse,json,shutil,subprocess,tempfile
from pathlib import Path
from patch_duplicate_inventory import ROOT,patch,working_native,sha
from build_fixed_gameplay import repack_native,check
from build_split_package import REQUIRED_SPLITS,zipalign_and_sign_split_set,ZIPALIGN,APKSIGNER,KEYSTORE,KEY_ALIAS,KEY_PASS
DEST=ROOT/'builds/duplicate_weapon_fixed_splits'
STANDALONE=ROOT/'builds/duplicate_weapon_fixed_standalone'
SOURCES=ROOT/'builds/fixed_ammo_dual_weapon_splits'
OLD_STANDALONE=ROOT/'builds/fixed_ammo_dual_weapon_standalone/mmc-fixed-ammo-dual-weapon.apk'
APK_NAME='mmc-duplicate-weapon-fixed-experimental.apk'
EVIDENCE=ROOT/'reports/duplicate-inventory-evidence'

def verify():
 native,manifest=patch(working_native());saved=json.loads((DEST/'verification.json').read_text());records=[]
 if saved['native_patch']!=manifest:raise ValueError('Native manifest mismatch')
 for name in REQUIRED_SPLITS:
  record,_=check(DEST/name,SOURCES/name,native);records.append(record)
 if records!=saved['splits']:raise ValueError('Split hash/verification mismatch')
 record,_=check(STANDALONE/APK_NAME,OLD_STANDALONE,native,require_stored=False)
 if record!=saved['standalone']:raise ValueError('Standalone verification mismatch')
 print('PASS: exact inventory-only ELF, gameplay bytes preserved, signatures, ZIP storage/alignment, CRC and application payloads')
 return saved

def build():
 if DEST.exists() or STANDALONE.exists():raise SystemExit('Refusing overwrite of existing inventory output')
 native,manifest=patch(working_native());logs=[];records=[]
 with tempfile.TemporaryDirectory(prefix='duplicate-inventory-',dir=ROOT/'builds') as folder:
  temp=Path(folder);inputdir=temp/'input';inputdir.mkdir();signed=temp/'signed';lib=temp/'libcocos2dcpp.so';lib.write_bytes(native)
  for name in REQUIRED_SPLITS:
   if name=='split_config.arm64_v8a.apk':repack_native(SOURCES/name,lib,inputdir/name)
   else:shutil.copy2(SOURCES/name,inputdir/name)
  zipalign_and_sign_split_set(inputdir,signed)
  for name in REQUIRED_SPLITS:
   record,log=check(signed/name,SOURCES/name,native);records.append(record);logs.append(name+'\n'+log)
  if len({r['certificate_sha256'] for r in records})!=1:raise ValueError('Mixed split signers')
  standalone=temp/'standalone';standalone.mkdir();unsigned=temp/'unsigned.apk';aligned=temp/'aligned.apk';final=standalone/APK_NAME
  repack_native(OLD_STANDALONE,lib,unsigned)
  subprocess.run([ZIPALIGN,'-p','-f','4',str(unsigned),str(aligned)],capture_output=True,text=True,check=True)
  subprocess.run([APKSIGNER,'sign','--ks',str(KEYSTORE),'--ks-key-alias',KEY_ALIAS,'--ks-pass','pass:'+KEY_PASS,'--out',str(final),str(aligned)],capture_output=True,text=True,check=True)
  record,log=check(final,OLD_STANDALONE,native,require_stored=False);logs.append(APK_NAME+'\n'+log)
  result=dict(static_checks='PASS',runtime_inventory='NOT TESTED',native_patch=manifest,splits=records,standalone=record,source_build='fixed_ammo_dual_weapon_splits; user confirmed ammo/reload/fuel/offline working')
  for directory in [signed,standalone]:(directory/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
  signed.rename(DEST);standalone.rename(STANDALONE)
  (EVIDENCE/'package-verification.json').write_text(json.dumps(result,indent=2)+'\n');(EVIDENCE/'signatures.txt').write_text('\n'.join(logs))
 verify();print(DEST);print(STANDALONE/APK_NAME)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();verify() if a.verify else build()
if __name__=='__main__':main()
