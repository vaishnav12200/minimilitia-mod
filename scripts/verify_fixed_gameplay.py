#!/usr/bin/env python3
"""Independently recheck existing outputs, native exact bytes and signing scope."""
import argparse,json
from patch_fixed_gameplay import ROOT, combined, patch
from build_fixed_gameplay import check
from build_split_package import REQUIRED_SPLITS

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--duplicates',action='store_true');a=p.parse_args()
 tag='fixed_ammo_dual_weapon' if a.duplicates else 'fixed_ammo_jetpack'
 native,manifest=patch(combined(),a.duplicates);records=[]
 folder=ROOT/'builds'/f'{tag}_splits'
 saved=json.loads((folder/'verification.json').read_text());assert saved['native_patch']==manifest
 for name in REQUIRED_SPLITS:
  r,_=check(folder/name,ROOT/'builds/combined_mod_splits'/name,native);records.append(r)
 assert records==saved['splits']
 r,_=check(ROOT/'builds'/f'{tag}_standalone'/f'mmc-{tag.replace("_","-")}.apk',ROOT/'builds/standalone/mmc-standalone-combined-signed.apk',native,require_stored=False)
 assert r==saved['standalone']
 print('PASS: exact patched ELF, fuel preservation, signatures, native ZIP storage/alignment, application payloads, saved hashes')
if __name__=='__main__':main()
