#!/usr/bin/env python3
"""Build a new experimental split set from the existing combined package.
Never runs restore_baseline.py or rebuilds/overwrites a working package.
"""
import json, shutil, tempfile
from pathlib import Path
from patch_duplicate_loadout import ROOT, read_combined, patch
from build_split_package import REQUIRED_SPLITS, update_split_arm64_apk, zipalign_and_sign_split_set
from verify_phase4_package import verify

def main():
 builds=ROOT/'builds'; destination=builds/'phase4_duplicate_experimental_splits'
 if destination.exists(): raise SystemExit('Output exists; verify it or choose an isolated new build directory in this script')
 native,manifest=patch(read_combined())
 with tempfile.TemporaryDirectory(prefix='phase4-',dir=builds) as folder:
  temporary=Path(folder); source=temporary/'input'; signed=temporary/'signed'; source.mkdir()
  library=temporary/'libcocos2dcpp.so'; library.write_bytes(native)
  for name in REQUIRED_SPLITS:
   original=builds/'combined_mod_splits'/name
   if name=='split_config.arm64_v8a.apk': update_split_arm64_apk(original,library,source/name)
   else: shutil.copy2(original,source/name)
  zipalign_and_sign_split_set(source,signed)
  result=verify(signed)
  (signed/'phase4-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
  signed.rename(destination)
 print('Built:',destination)
 print('EXPERIMENTAL: no device gameplay or LAN results available')
if __name__=='__main__': main()
