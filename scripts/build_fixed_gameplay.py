#!/usr/bin/env python3
"""Build isolated signed splits and standalone; strict native/payload verification.
Run without --duplicates for Phase B, then with --duplicates for Phase D.
"""
import argparse, json, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from patch_fixed_gameplay import ROOT, combined, patch, sha
from build_split_package import REQUIRED_SPLITS, update_split_arm64_apk, zipalign_and_sign_split_set, ZIPALIGN, APKSIGNER, KEYSTORE, KEY_ALIAS, KEY_PASS
from verify_phase4_package import signer, application_payloads

def repack_native(source,library,destination):
 # Split manifests disable extraction: every native library must be stored,
 # then zipalign -p aligns it for direct Android mmap loading.
 with zipfile.ZipFile(source) as old,zipfile.ZipFile(destination,'w') as new:
  for item in old.infolist():
   if item.filename=='lib/arm64-v8a/libcocos2dcpp.so': continue
   new.writestr(item,old.read(item.filename))
  new.writestr('lib/arm64-v8a/libcocos2dcpp.so',library.read_bytes(),compress_type=zipfile.ZIP_STORED)

def check(apk,source,native,require_stored=True):
 cert,log=signer(apk);oldcert,_=signer(source);assert cert==oldcert
 subprocess.run([ZIPALIGN,'-c','-p','4',str(apk)],capture_output=True,text=True,check=True)
 with zipfile.ZipFile(apk) as z,zipfile.ZipFile(source) as old:
  assert z.testzip() is None
  import struct
  with apk.open('rb') as raw:
   for item in z.infolist():
    if item.filename.startswith('lib/') and item.filename.endswith('.so'):
     if require_stored: assert item.compress_type==zipfile.ZIP_STORED
     if item.compress_type!=zipfile.ZIP_STORED: continue
     raw.seek(item.header_offset+26);name_length,extra_length=struct.unpack('<HH',raw.read(4))
     assert (item.header_offset+30+name_length+extra_length)%4096==0
  assert application_payloads(z)==application_payloads(old)
  if 'lib/arm64-v8a/libcocos2dcpp.so' in z.namelist():assert z.read('lib/arm64-v8a/libcocos2dcpp.so')==native
 return dict(apk=apk.name,sha256=sha(apk.read_bytes()),certificate_sha256=cert,signature='PASS',alignment='PASS',crc='PASS',non_native_application_payloads='identical'),log

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--duplicates',action='store_true');a=p.parse_args()
 tag='fixed_ammo_dual_weapon' if a.duplicates else 'fixed_ammo_jetpack'
 dest=ROOT/'builds'/f'{tag}_splits';standalone=ROOT/'builds'/f'{tag}_standalone';evidence=ROOT/'reports/reload-fix-evidence'
 if dest.exists() or standalone.exists():raise SystemExit('Refusing overwrite of existing build')
 if a.duplicates:
  previous=ROOT/'builds/fixed_ammo_jetpack_splits/verification.json'
  if not previous.exists():raise SystemExit('Phase B verification required before inventory changes')
  assert json.loads(previous.read_text())['static_checks']=='PASS'
 native,manifest=patch(combined(),a.duplicates)
 with tempfile.TemporaryDirectory(prefix=tag+'-',dir=ROOT/'builds') as folder:
  temp=Path(folder);inputdir=temp/'input';inputdir.mkdir();signed=temp/'signed';lib=temp/'libcocos2dcpp.so';lib.write_bytes(native)
  sources=ROOT/'builds/combined_mod_splits'
  for name in REQUIRED_SPLITS:
   if name=='split_config.arm64_v8a.apk':repack_native(sources/name,lib,inputdir/name)
   else:shutil.copy2(sources/name,inputdir/name)
  zipalign_and_sign_split_set(inputdir,signed)
  records=[];logs=[]
  for name in REQUIRED_SPLITS:
   record,log=check(signed/name,sources/name,native);records.append(record);logs.append(name+'\n'+log)
  assert len({r['certificate_sha256'] for r in records})==1
  result=dict(static_checks='PASS',runtime='NOT TESTED',native_patch=manifest,splits=records)
  (signed/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
  # Repack the existing standalone container, preserving its manifest/DEX/resources.
  old=ROOT/'builds/standalone/mmc-standalone-combined-signed.apk';out=temp/'standalone';out.mkdir()
  unsigned=out/'unsigned.apk';aligned=out/'aligned.apk';final=out/f'mmc-{tag.replace("_","-")}.apk'
  repack_native(old,lib,unsigned)
  subprocess.run([ZIPALIGN,'-p','-f','4',str(unsigned),str(aligned)],capture_output=True,text=True,check=True)
  subprocess.run([APKSIGNER,'sign','--ks',str(KEYSTORE),'--ks-key-alias',KEY_ALIAS,'--ks-pass','pass:'+KEY_PASS,'--out',str(final),str(aligned)],capture_output=True,text=True,check=True)
  record,log=check(final,old,native,require_stored=False);result['standalone']=record;logs.append(final.name+'\n'+log)
  (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');unsigned.unlink();aligned.unlink()
  (signed/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
  signed.rename(dest);out.rename(standalone)
  (evidence/f'{tag}-verification.json').write_text(json.dumps(result,indent=2)+'\n')
  (evidence/f'{tag}-signatures.txt').write_text('\n'.join(logs))
 print('PASS: signatures, alignment, native patch and all other app payloads')
 print(dest);print(standalone/final.name)
if __name__=='__main__':main()
