#!/usr/bin/env python3
"""Shared pair-policy compiler and scoped held transforms after physical UI pass.
Default next class: M93BA sniper. Mixed pairs are intentionally not yet admitted.
"""
import io,json,struct,zipfile
from elftools.elf.elffile import ELFFile
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from patch_duplicate_inventory import ROOT,sha
WORKING_SHA='77f075ede045373df1f631b2cea0f0ce421bab0f971214e9c38e235de5a87191'
PAIRS=((9,9),(10,10))
CLASSES={9:'SHOTGUN',10:'M93BA'}

def working_native():
 with zipfile.ZipFile(ROOT/'builds/universal_dual_wield_ui_splits/split_config.arm64_v8a.apk') as z:return z.read('lib/arm64-v8a/libcocos2dcpp.so')

def pair_guard(pairs,deny,prefix):
 # w0 primary type, w9 incoming type. One explicit matrix drives UI + inventory.
 code=''
 for idx,(primary,incoming) in enumerate(pairs):
  code+=f'cmp w0, #{primary}\nb.ne {prefix}_{idx}\ncmp w9, #{incoming}\nb.eq {prefix}_ok\n{prefix}_{idx}:\n'
 return code+f'b {deny}\n{prefix}_ok:\n'

def patch(data,pairs=PAIRS):
 if sha(data)!=WORKING_SHA:raise ValueError('Exact physically confirmed two-action SPAS build required')
 if not pairs or any(p not in CLASSES or i not in CLASSES for p,i in pairs):raise ValueError('Uninvestigated class in pair policy')
 elf=ELFFile(io.BytesIO(data));ds=elf.get_section_by_name('.dynsym');sy={s.name:s for s in ds.iter_symbols()};rel=elf.get_section_by_name('.rela.dyn');rels={r['r_offset']:r for r in rel.iter_relocations()}
 def off(va,n):
  for s in elf.iter_segments():
   if s['p_type']=='PT_LOAD' and s['p_vaddr']<=va and va+n<=s['p_vaddr']+s['p_filesz']:return s['p_offset']+va-s['p_vaddr']
  raise ValueError('Unmapped VA')
 saved=json.loads((ROOT/'builds/universal_dual_wield_ui_splits/verification.json').read_text())['native_patch'];assert saved['output_sha256']==sha(data)
 out=bytearray(data);changes=[];ks=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN)
 def replace(offset,new,reason,**meta):
  old=data[offset:offset+len(new)];out[offset:offset+len(new)]=new;changes.append(dict(file_offset=hex(offset),original=old.hex(),replacement=new.hex(),reason=reason,**meta))
 for va,deny,scratch,prefix in [(0x8e6990,'done',8,'pickup_pair'),(0x669d00,'single',0xac,'ui_pair')]:
  previous=next(c for c in saved['changes'] if int(c['elf_virtual_address'],16)==va)
  assert data[off(va,len(bytes.fromhex(previous['replacement']))):off(va,len(bytes.fromhex(previous['replacement'])))+len(bytes.fromhex(previous['replacement']))]==bytes.fromhex(previous['replacement'])
  assembly=previous['assembly'];needle=' cmp w0, #9\n b.ne '+deny+'\n';assert assembly.count(needle)==2
  assembly=assembly.replace(needle,f' str w0, [sp, #{scratch}]\n',1)
  assembly=assembly.replace(needle,f' ldr w9, [sp, #{scratch}]\n'+pair_guard(pairs,deny,prefix),1)
  code=bytes(ks.asm(assembly,addr=va)[0]);end=0x8e6cac if va==0x8e6990 else 0x669f84;assert va+len(code)<end
  f=sy[previous['function']];assert f['st_value']<=va<va+len(code)<=f['st_value']+f['st_size']
  assert len(list(Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(code,va)))*4==len(code)
  replace(off(va,len(code)),code,'Compile same explicit pair matrix into inventory and HUD; independent source-class trigger/projectile paths preserved',function=previous['function'],elf_virtual_address=hex(va),assembly=assembly)
 for ty in sorted({x for p in pairs for x in p}):
  cls=CLASSES[ty];slot=sy['_ZTV'+str(len(cls))+cls]['st_value']+16+0x3d8;r=rels[slot];assert r['r_info_type']==257 and r['r_addend']==0
  target=ds.get_symbol(r['r_info_sym']).name;held='_ZN'+str(len(cls))+cls+'23setPrimaryConfigurationEv'
  if target==held:continue  # SPAS confirmed transform is already installed.
  if target!='_ZN4Item20setDualConfigurationEv':raise ValueError('Class has specialized dual transform; inspect before override')
  assert held in sy
  idx=next(i for i,s in enumerate(ds.iter_symbols()) if s.name==held);ri=next(i for i,r0 in enumerate(rel.iter_relocations()) if r0['r_offset']==slot);ro=rel['sh_offset']+ri*rel['sh_entsize']+8
  replace(ro,struct.pack('<Q',(idx<<32)|257),'Replace only this gun class empty dual configuration with its existing held transform',function=cls+'::dual configuration vtable',elf_virtual_address=hex(slot),target=held,item_type=ty)
 allowed=set()
 for c in changes:allowed.update(range(int(c['file_offset'],16),int(c['file_offset'],16)+len(bytes.fromhex(c['replacement']))))
 assert len(out)==len(data) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,out)))
 return bytes(out),dict(input_sha256=sha(data),output_sha256=sha(out),changes=changes,pair_policy=[dict(primary=p,incoming=i) for p,i in pairs],stage='Physical SPAS UI PASS; same-class sniper candidate pending physical test',firing='No ammo/reload/fuel/trigger/projectile/network changes; per-instance methods preserved',ownership='Same confirmed explicit actions and pointer/occupied-slot guards; shared policy drives HUD and inventory')
