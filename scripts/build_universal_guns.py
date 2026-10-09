#!/usr/bin/env python3
"""Build/verify Consolidated universal-gun split set and compressed single APK."""
import argparse,json,shutil,subprocess,tempfile,zipfile
from pathlib import Path
from patch_universal_guns import ROOT,patch,working_native,sha
from build_fixed_gameplay import repack_native,check
from build_split_package import REQUIRED_SPLITS,zipalign_and_sign_split_set,ZIPALIGN,APKSIGNER,KEYSTORE,KEY_ALIAS,KEY_PASS
DEST=ROOT/'builds/universal_dual_wield_final_splits'
STANDALONE=ROOT/'builds/universal_dual_wield_final'
SOURCES=ROOT/'builds/universal_dual_wield_ui_sniper_splits'
OLD_STANDALONE=ROOT/'builds/universal_dual_wield_ui_sniper_standalone/mmc-two-action-sniper-experimental.apk'
APK_NAME='MiniMilitiaClassic-Universal-Dual-v1.0.0.apk'
EVIDENCE=ROOT/'reports/universal-guns-evidence'

def repack_standalone(source,library,destination):
 # This unchanged standalone manifest enables Android native extraction.
 # Compression is valid here; the extractNativeLibs=false split stays STORED.
 aapt=Path(ZIPALIGN).parent/'aapt'
 manifest=subprocess.run([str(aapt),'dump','xmltree',str(source),'AndroidManifest.xml'],capture_output=True,text=True,check=True).stdout
 if not any('extractNativeLibs' in line and '0xffffffff' in line for line in manifest.splitlines()):raise ValueError('Compressed native needs extractNativeLibs=true')
 with zipfile.ZipFile(source) as old,zipfile.ZipFile(destination,'w') as new:
  for item in old.infolist():
   if item.filename=='lib/arm64-v8a/libcocos2dcpp.so':continue
   new.writestr(item,old.read(item.filename))
  new.writestr('lib/arm64-v8a/libcocos2dcpp.so',library.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def verify():
 native,manifest=patch(working_native());saved=json.loads((DEST/'verification.json').read_text());records=[]
 if saved['native_patch']!=manifest:raise ValueError('Native manifest mismatch')
 for name in REQUIRED_SPLITS:
  record,_=check(DEST/name,SOURCES/name,native);records.append(record)
 if records!=saved['splits']:raise ValueError('Split hash/verification mismatch')
 record,_=check(STANDALONE/APK_NAME,OLD_STANDALONE,native,require_stored=False)
 if record!=saved['standalone']:raise ValueError('Standalone verification mismatch')
 print('PASS: exact action/UI-scoped ELF, gameplay bytes preserved, signatures, ZIP storage/alignment, CRC and application payloads')
 return saved

def build():
 if DEST.exists() or STANDALONE.exists():raise SystemExit('Refusing overwrite of existing inventory output')
 native,manifest=patch(working_native());logs=[];records=[]
 with tempfile.TemporaryDirectory(prefix='dual-wield-ui-',dir=ROOT/'builds') as folder:
  temp=Path(folder);inputdir=temp/'input';inputdir.mkdir();signed=temp/'signed';lib=temp/'libcocos2dcpp.so';lib.write_bytes(native)
  for name in REQUIRED_SPLITS:
   if name=='split_config.arm64_v8a.apk':repack_native(SOURCES/name,lib,inputdir/name)
   else:shutil.copy2(SOURCES/name,inputdir/name)
  zipalign_and_sign_split_set(inputdir,signed)
  for name in REQUIRED_SPLITS:
   record,log=check(signed/name,SOURCES/name,native);records.append(record);logs.append(name+'\n'+log)
  if len({r['certificate_sha256'] for r in records})!=1:raise ValueError('Mixed split signers')
  standalone=temp/'standalone';standalone.mkdir();unsigned=temp/'unsigned.apk';aligned=temp/'aligned.apk';final=standalone/APK_NAME
  repack_standalone(OLD_STANDALONE,lib,unsigned)
  subprocess.run([ZIPALIGN,'-p','-f','4',str(unsigned),str(aligned)],capture_output=True,text=True,check=True)
  subprocess.run([APKSIGNER,'sign','--ks',str(KEYSTORE),'--ks-key-alias',KEY_ALIAS,'--ks-pass','pass:'+KEY_PASS,'--out',str(final),str(aligned)],capture_output=True,text=True,check=True)
  record,log=check(final,OLD_STANDALONE,native,require_stored=False);logs.append(APK_NAME+'\n'+log)
  result=dict(static_checks='PASS',runtime_visual='NOT TESTED', stage='22 gun classes / 484 same and mixed pairs; broader physical regression pending',native_patch=manifest,splits=records,standalone=record,source_build='universal_dual_wield_ui_sniper_splits; user confirms SPAS and sniper working')
  for directory in [signed,standalone]:(directory/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
  signed.rename(DEST);standalone.rename(STANDALONE)
  (EVIDENCE/'package-verification.json').write_text(json.dumps(result,indent=2)+'\n');(EVIDENCE/'signatures.txt').write_text('\n'.join(logs))
  (STANDALONE/'SHA256SUMS.txt').write_text(result['standalone']['sha256']+'  '+APK_NAME+'\n')
 verify();print(DEST);print(STANDALONE/APK_NAME)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();verify() if a.verify else build()
if __name__=='__main__':main()
