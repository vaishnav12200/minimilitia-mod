#!/usr/bin/env python3
"""Experimental duplicate picker patch, layered on the user-tested ammo/fuel ELF.
No inventory, weapon allocation, paid access, or validation functions are changed.
"""
import argparse, hashlib, io, json, zipfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
ROOT = Path(__file__).resolve().parents[1]
COMBINED_SHA256 = 'b8095e7d005c6b8c9b140a92968d9474a9963bee8ea96e491b4844e2a286b411'
PATCHES = (
 ('_ZN11LoadoutMenu9onPrimaryEPN7cocos2d8CCObjectE', 0x69f3d4, 0x69f3e8),
 ('_ZN11LoadoutMenu11onSecondaryEPN7cocos2d8CCObjectE', 0x69f514, 0x69f528),
)
def sha256(data): return hashlib.sha256(data).hexdigest()
def read_combined():
 with zipfile.ZipFile(ROOT/'builds/combined_mod_splits/split_config.arm64_v8a.apk') as z:
  return z.read('lib/arm64-v8a/libcocos2dcpp.so')
def patch(data):
 if sha256(data) != COMBINED_SHA256: raise ValueError('Expected the exact user-tested combined library')
 elf=ELFFile(io.BytesIO(data))
 if elf['e_machine'] != 'EM_AARCH64': raise ValueError('Wrong architecture')
 symbols={s.name:s for s in elf.get_section_by_name('.dynsym').iter_symbols()}
 patched=bytearray(data); records=[]; cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM); cs.detail=True
 for name,va,dest in PATCHES:
  symbol=symbols[name]
  if not symbol['st_value'] <= va < dest < symbol['st_value']+symbol['st_size']:
   raise ValueError('Patch is outside verified function')
  segment=next(s for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_vaddr']<=va<s['p_vaddr']+s['p_filesz'])
  if not segment['p_flags']&1: raise ValueError('Patch is not in executable segment')
  off=segment['p_offset']+va-segment['p_vaddr']
  original=data[off:off+4]
  if original!=bytes.fromhex('a1000054'): raise ValueError('Original branch bytes do not match')
  if data[off-4:off]!=bytes.fromhex('3f010a6b'): raise ValueError('Expected slot-index comparison')
  ins=next(cs.disasm(original,va))
  if ins.mnemonic!='b.ne' or ins.operands[0].imm!=dest: raise ValueError('Unexpected conditional branch')
  # Same destination, unconditional branch. Bounds/category/null checks before it remain.
  replacement=(0x14000000 | ((dest-va)//4 & 0x03ffffff)).to_bytes(4,'little')
  branch=next(cs.disasm(replacement,va))
  if branch.mnemonic!='b' or branch.operands[0].imm!=dest: raise ValueError('Bad replacement instruction')
  patched[off:off+4]=replacement
  records.append(dict(symbol=name,va=hex(va),file_offset=hex(off),original=original.hex(),replacement=replacement.hex(),destination=hex(dest)))
 # Full-file comparison bounds the mutation; both functioning patches must remain exact.
 allowed={int(r['file_offset'],16)+i for r in records for i in range(4)}
 assert len(data)==len(patched)
 assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,patched)))
 assert patched[0x9482e0:0x9482e4]==bytes.fromhex('c0035fd6')
 assert patched[0x8e68e4:0x8e68ec]==bytes.fromhex('00102e1ec0035fd6')
 return bytes(patched),dict(status='EXPERIMENTAL — runtime NOT TESTED',input_sha256=sha256(data),output_sha256=sha256(patched),patches=records)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,default=ROOT/'builds/phase4-native/libcocos2dcpp.so')
 args=p.parse_args(); output=args.output.resolve()
 protected=[ROOT/'native-analysis/libcocos2dcpp.so', ROOT/'native-analysis/backup/libcocos2dcpp.so']
 if output in protected: p.error('Refusing to overwrite preserved native libraries')
 data,manifest=patch(read_combined()); output.parent.mkdir(parents=True,exist_ok=True)
 if output.exists():
  if output.read_bytes()!=data: p.error('Refusing to overwrite a different existing file')
 else: output.write_bytes(data)
 output.with_suffix('.patches.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('PASS: two duplicate-selection branches patched; ammo/fuel preserved')
 print(output); print(manifest['output_sha256'])
if __name__=='__main__': main()
