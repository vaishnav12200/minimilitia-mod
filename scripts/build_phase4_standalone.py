#!/usr/bin/env python3
"""Incrementally repack the existing combined standalone APK for phone testing.
Preserves its manifest, DEX, resources and other native libraries byte-for-byte.
"""
import json, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from patch_duplicate_loadout import ROOT, patch, sha256
from build_split_package import update_split_arm64_apk, ZIPALIGN, APKSIGNER, KEYSTORE, KEY_ALIAS, KEY_PASS
from verify_phase4_package import signer, application_payloads

def main():
 source=ROOT/'builds/standalone/mmc-standalone-combined-signed.apk'
 destination=ROOT/'builds/phase4-standalone/mmc-phase4-duplicates-experimental.apk'
 if destination.exists(): raise SystemExit('Refusing to overwrite existing experimental APK')
 source_certificate,_=signer(source)
 with zipfile.ZipFile(source) as z: native,manifest=patch(z.read('lib/arm64-v8a/libcocos2dcpp.so'))
 destination.parent.mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='phase4-standalone-',dir=ROOT/'builds') as folder:
  temporary=Path(folder); library=temporary/'libcocos2dcpp.so'; library.write_bytes(native)
  unsigned=temporary/'unsigned.apk'; aligned=temporary/'aligned.apk'; signed=temporary/'signed.apk'
  update_split_arm64_apk(source,library,unsigned)
  subprocess.run([ZIPALIGN,'-p','-f','4',str(unsigned),str(aligned)],capture_output=True,text=True,check=True)
  subprocess.run([APKSIGNER,'sign','--ks',str(KEYSTORE),'--ks-key-alias',KEY_ALIAS,'--ks-pass','pass:'+KEY_PASS,'--out',str(signed),str(aligned)],capture_output=True,text=True,check=True)
  certificate,verification=signer(signed)
  if certificate!=source_certificate: raise ValueError('Signer mismatch')
  subprocess.run([ZIPALIGN,'-c','-p','4',str(signed)],capture_output=True,text=True,check=True)
  with zipfile.ZipFile(signed) as z,zipfile.ZipFile(source) as old:
   if z.testzip() is not None: raise ValueError('Bad ZIP CRC')
   if z.read('lib/arm64-v8a/libcocos2dcpp.so')!=native: raise ValueError('Bad native patch')
   if application_payloads(z)!=application_payloads(old): raise ValueError('Unexpected application change')
  result=dict(status='EXPERIMENTAL; installation and gameplay NOT TESTED',source_apk=str(source.relative_to(ROOT)),source_sha256=sha256(source.read_bytes()),apk_sha256=sha256(signed.read_bytes()),certificate_sha256=certificate,native_patch=manifest,signature='PASS',zip_alignment='PASS',zip_crc='PASS',application_payload_preservation='PASS')
  shutil.copy2(signed,destination)
  sidecar=signed.with_suffix('.apk.idsig')
  if sidecar.exists(): shutil.copy2(sidecar,destination.with_suffix('.apk.idsig'))
  destination.with_suffix('.verification.json').write_text(json.dumps(result,indent=2)+'\n')
  evidence=ROOT/'reports/phase4-evidence'; (evidence/'standalone-verification.json').write_text(json.dumps(result,indent=2)+'\n')
  (evidence/'standalone-signature.txt').write_text(verification)
 print('Built:',destination); print('SHA256:',result['apk_sha256']); print('PASS: static signature, alignment, native patch and payload preservation')
if __name__=='__main__': main()
