#!/usr/bin/env python3
"""Phase A only: SPAS pair pickup + scoped held transform; stock firing unchanged."""
import io,json,struct,zipfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
from patch_duplicate_inventory import ROOT,sha,controller_call
WORKING_SHA='46e01584ccf9aafafe09c7d1601364ddc4d6158d762e14554830139550d23db4'
START=0x8e6990;LIMIT=0x8e6cac

def working_native():
 with zipfile.ZipFile(ROOT/'builds/duplicate_weapon_fixed_splits/split_config.arm64_v8a.apk') as z:return z.read('lib/arm64-v8a/libcocos2dcpp.so')

def patch(data):
 if sha(data)!=WORKING_SHA:raise ValueError('Exact working carried-duplicate build required')
 elf=ELFFile(io.BytesIO(data));ds=elf.get_section_by_name('.dynsym');sy={s.name:s for s in ds.iter_symbols()};rel=elf.get_section_by_name('.rela.dyn')
 def off(va,size):
  for seg in elf.iter_segments():
   if seg['p_type']=='PT_LOAD' and seg['p_vaddr']<=va and va+size<=seg['p_vaddr']+seg['p_filesz']:return seg['p_offset']+va-seg['p_vaddr']
  raise ValueError('Unmapped VA')
 f=sy['_ZN22SoldierLocalController9addWeaponEP6Weapon'];assert (f['st_value'],f['st_size'])==(0x8e6934,1324)
 # The previous carried build unconditionally skips this original dual routing.
 assert data[off(0x8e698c,4):off(0x8e698c,4)+4]==bytes.fromhex('c8000014')
 def target(r):return r['r_addend'] if r['r_info_type']==1027 else ds.get_symbol(r['r_info_sym'])['st_value']+r['r_addend']
 rels={r['r_offset']:r for r in rel.iter_relocations()}
 vt=sy['_ZTV22SoldierLocalController']['st_value']+16
 assert target(rels[vt+0x440])==sy['_ZN22SoldierLocalController13addDualWeaponEP6Weapon']['st_value']
 assert target(rels[sy['_ZTV6Weapon']['st_value']+16+0x520])==sy['_ZN6Weapon7getTypeEv']['st_value']
 assembly='''
 ldur x8, [x29, #-0x18]
 ldur x10, [x29, #-0x10]
 ldr x9, [x8, #0x1c8]
 cmp x9, x10
 b.eq done
 ldr x9, [x8, #0x1d0]
 cmp x9, x10
 b.eq done
 ldr x9, [x8, #0x1d8]
 cmp x9, x10
 b.eq done
 cbnz x9, fallback
 ldr x9, [x8, #0x1c8]
 cbz x9, fallback
 mov x0, x10
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 cmp w0, #9
 b.ne fallback
 ldur x8, [x29, #-0x18]
 ldr x0, [x8, #0x1c8]
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 cmp w0, #9
 b.ne fallback
'''+controller_call(0x440,True)+'''
 mov w1, #4
 adrp x8, 0x13bf000
 ldr x8, [x8, #0x4d0]
 ldr x0, [x8]
 bl 0x4c0ce0
 done:
 b 0x8e6e54
 fallback:
 b 0x8e6cac
'''
 ks=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN);code=bytes(ks.asm(assembly,addr=START)[0]);assert START+len(code)<=LIMIT
 out=bytearray(data);changes=[]
 def replace(file_offset,expected,new,reason,**meta):
  assert len(expected)==len(new) and data[file_offset:file_offset+len(expected)]==expected
  out[file_offset:file_offset+len(new)]=new;changes.append(dict(file_offset=hex(file_offset),original=expected.hex(),replacement=new.hex(),reason=reason,**meta))
 fn='_ZN22SoldierLocalController9addWeaponEP6Weapon'
 replace(off(0x8e698c,4),bytes.fromhex('c8000014'),bytes(ks.asm('b 0x8e6990',addr=0x8e698c)[0]),'Enter SPAS pair guard before retained ordinary routing',function=fn,elf_virtual_address='0x8e698c')
 replace(off(START,len(code)),data[off(START,len(code)):off(START,len(code))+len(code)],code,'Distinct SPAS+SPAS with empty dual slot uses stock addDualWeapon; every other pickup falls back to working carried routing',function=fn,elf_virtual_address=hex(START),assembly=assembly)
 # SPAS host-dual wrapper invokes its empty Item::setDualConfiguration slot.
 # Redirect ONLY this class slot to its existing primary/held transform.
 slot=sy['_ZTV7SHOTGUN']['st_value']+16+0x3d8;r=rels[slot]
 assert r['r_info_type']==257 and r['r_addend']==0
 assert target(r)==sy['_ZN4Item20setDualConfigurationEv']['st_value']
 idx=next(i for i,s in enumerate(ds.iter_symbols()) if s.name=='_ZN7SHOTGUN23setPrimaryConfigurationEv')
 entry_idx=next(i for i,x in enumerate(rel.iter_relocations()) if x['r_offset']==slot)
 ro=rel['sh_offset']+entry_idx*rel['sh_entsize']+8
 replace(ro,struct.pack('<Q',r['r_info']),struct.pack('<Q',(idx<<32)|257),'Dynamic relocation changes SHOTGUN dual-configuration vtable slot to its held transform; ownership untouched',function='_ZN4Item24setHostDualConfigurationEv -> SHOTGUN::setPrimaryConfiguration',elf_virtual_address=hex(slot),relocation_target='_ZN7SHOTGUN23setPrimaryConfigurationEv')
 allowed=set()
 for c in changes:allowed.update(range(int(c['file_offset'],16),int(c['file_offset'],16)+len(bytes.fromhex(c['replacement']))))
 assert len(out)==len(data) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,out)))
 # Everything else including the full getter/reload/fuel/fire/projectile code is byte-identical.
 return bytes(out),dict(input_sha256=sha(data),output_sha256=sha(out),changes=changes,stage='Phase A SPAS-only hand-attachment candidate; device visual confirmation pending',affected_types=[9],stub_bytes=len(code),ownership='Stock addDualWeapon retains distinct incoming instance exactly once; primary and secondary untouched; occupied dual slot falls back to existing inventory behavior',firing='No firing, projectile, reload, network or fuel code changes',compatibility='Other classes retain working carried behavior; universal expansion requires physical SPAS verification')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists()
 native,manifest=patch(working_native());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(native);a.output.with_suffix('.patches.json').write_text(json.dumps(manifest,indent=2)+'\n');print(manifest['output_sha256'])
