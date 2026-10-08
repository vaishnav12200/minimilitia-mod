#!/usr/bin/env python3
"""Create a local download ZIP with the four verified experimental splits."""
import hashlib, json, zipfile
from pathlib import Path
from patch_duplicate_loadout import ROOT
from build_split_package import REQUIRED_SPLITS
from verify_phase4_package import verify

def main():
 source=ROOT/'builds/phase4_duplicate_experimental_splits'
 verification=verify(source)
 output=ROOT/'builds/mmc-phase4-duplicates-experimental-splits.zip'
 with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as z:
  for name in REQUIRED_SPLITS: z.write(source/name,name)
  z.writestr('verification.json',json.dumps(verification,indent=2)+'\n')
  z.write(ROOT/'README.md','INSTALLATION.md')
 with zipfile.ZipFile(output) as z:
  if z.testzip() is not None: raise ValueError('Download ZIP integrity failure')
 digest=hashlib.sha256(output.read_bytes()).hexdigest()
 output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n')
 print(output); print('SHA256:',digest)
if __name__=='__main__': main()
