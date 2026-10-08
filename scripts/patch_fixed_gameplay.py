#!/usr/bin/env python3
"""Local equipped-weapon refill and isolated duplicate-selection/pickup experiment.
Input is the preserved combined build. Never edits the original analysis library.
"""
import argparse, hashlib, io, json, zipfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_SHA = '2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401'
COMBINED_SHA = 'b8095e7d005c6b8c9b140a92968d9474a9963bee8ea96e491b4844e2a286b411'
GOT = 0x13bec80
GETTERS = (('_ZN6Weapon7getClipEv', 0x947954, 0x362, 0x590),
           ('_ZN6Weapon7getAmmoEv', 0x947a20, 0x360, 0x588))
DUPLICATES = (
 ('_ZN11LoadoutMenu9onPrimaryEPN7cocos2d8CCObjectE',0x69f3d4,0x69f3e8,'a1000054','3f010a6b'),
 ('_ZN11LoadoutMenu11onSecondaryEPN7cocos2d8CCObjectE',0x69f514,0x69f528,'a1000054','3f010a6b'),
 ('_ZN13WeaponManager15weaponProximityEP6Weapon',0x9578c8,0x957944,'e1030054','5f01006b'),
 ('_ZN13WeaponManager15weaponProximityEP6Weapon',0x957980,0x9579f4,'a1030054','5f01006b'))
def sha(data): return hashlib.sha256(data).hexdigest()
def combined():
 with zipfile.ZipFile(ROOT/'builds/combined_mod_splits/split_config.arm64_v8a.apk') as z:
  return z.read('lib/arm64-v8a/libcocos2dcpp.so')
def getter_code(va, field, virtual):
 source=f'''
 stp x19, x30, [sp, #-16]!
 mov x19, x0
 adrp x8, {GOT & ~0xfff}
 ldr x8, [x8, #{GOT & 0xfff}]
 ldr x8, [x8]
 cbz x8, stock
 ldr x9, [x8, #0x1c8]
 cmp x9, x19
 b.eq refill
 ldr x9, [x8, #0x1d0]
 cmp x9, x19
 b.eq refill
 ldr x9, [x8, #0x1d8]
 cmp x9, x19
 b.ne stock
refill:
 ldr x8, [x19]
 ldr x8, [x8, #{virtual}]
 mov x0, x19
 blr x8
 sxth w0, w0
 cmp w0, #0
 b.le stock
 strh w0, [x19, #{field}]
 b done
stock:
 ldrsh w0, [x19, #{field}]
 cmp w0, #0
 csel w0, w0, wzr, gt
 done:
 ldp x19, x30, [sp], #16
 ret
'''
 encoded,_=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN).asm(source,addr=va)
 return bytes(encoded),source

def patch(data, duplicates=False):
 if sha(data)!=COMBINED_SHA: raise ValueError('Exact preserved combined ELF required')
 original=(ROOT/'native-analysis/backup/libcocos2dcpp.so').read_bytes()
 if sha(original)!=ORIGINAL_SHA: raise ValueError('Original backup hash mismatch')
 elf=ELFFile(io.BytesIO(data)); syms={s.name:s for s in elf.get_section_by_name('.dynsym').iter_symbols()}
 if elf['e_machine']!='EM_AARCH64': raise ValueError('Expected ARM64')
 # Verify that this GOT entry resolves the global localSoldier pointer.
 rel=next(r for r in elf.get_section_by_name('.rela.dyn').iter_relocations() if r['r_offset']==GOT)
 assert rel['r_info_type']==1025
 assert elf.get_section_by_name('.dynsym').get_symbol(rel['r_info_sym']).name=='localSoldier'
 def offset(va, size=4):
  s=next(s for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz'])
  assert s['p_flags']&1
  return s['p_offset']+va-s['p_vaddr']
 result=bytearray(data); changes=[]; cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 def replace(name,va,old,new,why,assembly=None):
  off=offset(va,len(old)); symbol=syms[name]
  assert symbol['st_value']<=va and va+len(old)<=symbol['st_value']+symbol['st_size']
  assert data[off:off+len(old)]==old and len(old)==len(new)
  result[off:off+len(old)]=new
  changes.append(dict(symbol=name,virtual_address=hex(va),file_offset=hex(off),original=old.hex(),replacement=new.hex(),purpose=why,assembly=assembly,calling_convention='AAPCS64; x0=this; w0=count for ammo getters'))
 off=offset(0x9482e0)
 assert original[off:off+8]==bytes.fromhex('ff4301d1fd7b04a9')
 replace('_ZN6Weapon7subAmmoEi',0x9482e0,bytes.fromhex('c0035fd6'),original[off:off+4],'Restore complete stock subtraction and integer return')
 for name,va,field,virtual in GETTERS:
  symbol=syms[name]; assert symbol['st_value']==va and symbol['st_size']==204
  off=offset(va,204); assert data[off:off+204]==original[off:off+204]
  code,assembly=getter_code(va,field,virtual); assert len(code)<=204
  replace(name,va,data[off:off+204],code+bytes.fromhex('1f2003d5')*((204-len(code))//4),'Refill only local equipped instances to positive type capacity; stock clamped read otherwise',assembly)
 if duplicates:
  for name,va,dest,expected,comparison in DUPLICATES:
   off=offset(va); assert data[off-4:off]==bytes.fromhex(comparison)
   symbol=syms[name]; assert symbol['st_value']<=va<dest<symbol['st_value']+symbol['st_size']
   ins=next(cs.disasm(bytes.fromhex(expected),va)); assert ins.mnemonic=='b.ne' and ins.op_str==f'#{hex(dest)}'
   new=(0x14000000|((dest-va)//4)).to_bytes(4,'little')
   replace(name,va,bytes.fromhex(expected),new,'Allow matching ordinary type through existing selector/pickup path; retain allocations and ownership')
 assert result[offset(0x8e68e4,8):offset(0x8e68e4,8)+8]==bytes.fromhex('00102e1ec0035fd6')
 allowed=set()
 for r in changes:
  allowed.update(range(int(r['file_offset'],16),int(r['file_offset'],16)+len(bytes.fromhex(r['original']))))
 assert len(result)==len(data) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,result)))
 return bytes(result),dict(input_sha256=sha(data),original_sha256=sha(original),output_sha256=sha(result),fuel='exact existing patch preserved',duplicates=duplicates,changes=changes,status='Experimental until physical gameplay verification')
def main():
 p=argparse.ArgumentParser(description=__doc__); p.add_argument('--duplicates',action='store_true'); p.add_argument('--output',required=True,type=Path); a=p.parse_args()
 if a.output.resolve() in (ROOT/'native-analysis/libcocos2dcpp.so',ROOT/'native-analysis/backup/libcocos2dcpp.so'): p.error('Protected source')
 data,manifest=patch(combined(),a.duplicates)
 if a.output.exists(): raise SystemExit('Refusing overwrite')
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(data); a.output.with_suffix('.patches.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(manifest['output_sha256'])
if __name__=='__main__': main()
