#!/usr/bin/env python3
"""Verify experimental split signatures, alignment, ZIP integrity and patch scope."""
import argparse, json, re, subprocess, zipfile
from pathlib import Path
from patch_duplicate_loadout import ROOT, read_combined, patch, sha256
from build_split_package import REQUIRED_SPLITS, ZIPALIGN, APKSIGNER

def application_payloads(archive):
 signature = re.compile(r"^META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$", re.I)
 return {n:archive.read(n) for n in archive.namelist() if not signature.match(n) and n!='lib/arm64-v8a/libcocos2dcpp.so'}

def signer(apk):
 result=subprocess.run([APKSIGNER,'verify','--verbose','--print-certs',str(apk)],capture_output=True,text=True,check=True)
 certificates=[line.split(': ',1)[1] for line in result.stdout.splitlines() if line.startswith('Signer #') and 'certificate SHA-256 digest:' in line]
 if len(certificates)!=1: raise ValueError('Expected one signer for '+str(apk))
 return certificates[0],result.stdout

def verify(directory):
 expected,manifest=patch(read_combined()); certificates=set(); records=[]
 source=ROOT/'builds/combined_mod_splits'
 for name in REQUIRED_SPLITS:
  apk=directory/name
  certificate,log=signer(apk); certificates.add(certificate)
  subprocess.run([ZIPALIGN,'-c','-p','4',str(apk)],capture_output=True,text=True,check=True)
  with zipfile.ZipFile(apk) as z,zipfile.ZipFile(source/name) as old:
   if z.testzip() is not None: raise ValueError('ZIP CRC mismatch')
   if name=='split_config.arm64_v8a.apk':
    native=z.read('lib/arm64-v8a/libcocos2dcpp.so')
    if native!=expected: raise ValueError('Experimental native patch mismatch')
   # All application content except the native patch must be byte-identical.
   if application_payloads(z)!=application_payloads(old): raise ValueError('Unexpected application-content change: '+name)
  records.append(dict(apk=name,sha256=sha256(apk.read_bytes()),signature='PASS',zip_alignment='PASS',zip_crc='PASS',application_content='PASS',certificate_sha256=certificate))
 if len(certificates)!=1: raise ValueError('Split signing certificates differ')
 original_certificate,_=signer(source/'base.apk')
 if certificates!={original_certificate}: raise ValueError('Signer differs from working combined build')
 return dict(status='Static package checks PASS; installation/gameplay/LAN BLOCKED pending devices',native_patch=manifest,splits=records)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('directory',nargs='?',type=Path,default=ROOT/'builds/phase4_duplicate_experimental_splits')
 args=parser.parse_args(); result=verify(args.directory.resolve())
 output=ROOT/'reports/phase4-evidence/package-verification.json'
 output.parent.mkdir(exist_ok=True); output.write_text(json.dumps(result,indent=2)+'\n')
 print(result['status']); print(output)
if __name__=='__main__': main()
