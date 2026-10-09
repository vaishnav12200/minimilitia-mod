#!/usr/bin/env python3
"""Universal held-gun pair policy on the physically confirmed SPAS/sniper build."""
import io,json,re,struct,zipfile
from elftools.elf.elffile import ELFFile
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from patch_duplicate_inventory import ROOT,sha
WORKING_SHA='a7a01b33290e7de4c8e0d799c310edf00e886b470bd8b745cbc2bdf3dfc2555f'
GUNS={3:'DEAGLE',4:'MAGNUM',5:'UZI',6:'MP5',7:'AK47',8:'M16',9:'SHOTGUN',10:'M93BA',11:'SMAW',16:'M14',17:'PHASR',18:'GDEAGLE',19:'FLAMETHROWER',21:'EMP',25:'SAWGUN',26:'TAVOR',27:'MINIGUN',28:'TEC9',29:'RG6',31:'XM8',37:'AA12',39:'M1881'}
MASK=sum(1<<i for i in GUNS)
FIRE_HELPER=0x8e6b00

def working_native():
 with zipfile.ZipFile(ROOT/'builds/universal_dual_wield_ui_sniper_splits/split_config.arm64_v8a.apk') as z:return z.read('lib/arm64-v8a/libcocos2dcpp.so')

def membership_guard(deny):
 s='cmp w0, #64\nb.hs '+deny+'\ncmp w9, #64\nb.hs '+deny+'\n'
 for shift in [0,16,32,48]:s+=f'{"movz" if shift==0 else "movk"} x10, #{(MASK>>shift)&65535}, lsl #{shift}\n'
 return s+f'lsrv x11, x10, x0\ntbz w11, #0, {deny}\nlsrv x11, x10, x9\ntbz w11, #0, {deny}\n'

def fire_helper():
 code='sub sp, sp, #0x40\nstp x29, x30, [sp, #0x30]\nadd x29, sp, #0x30\nstr x0, [sp, #0x20]\nstr s0, [sp, #0xc]\n'
 for slot,label,next_label in [(0x1c8,'primary','dual'),(0x1d8,'dual','done')]:
  code+=f'''{label}:
 ldr x8, [sp, #0x20]
 ldr x0, [x8, #{slot}]
 cbz x0, {next_label}
 str x0, [sp, #0x10]
 bl 0x947954
 ldr x0, [sp, #0x10]
 bl 0x947a20
 ldr x0, [sp, #0x10]
 ldr x8, [x0]
 ldr x8, [x8, #0x4f8]
 ldr s0, [sp, #0xc]
 blr x8
'''
 return code+'''done:
 ldp x29, x30, [sp, #0x30]
 add sp, sp, #0x40
 ret
'''

def patch(data):
 if sha(data)!=WORKING_SHA:raise ValueError('Exact user-confirmed sniper build required')
 elf=ELFFile(io.BytesIO(data));ds=elf.get_section_by_name('.dynsym');sy={s.name:s for s in ds.iter_symbols()};rel=elf.get_section_by_name('.rela.dyn');rels={r['r_offset']:r for r in rel.iter_relocations()}
 def off(va,n,executable=False):
  for s in elf.iter_segments():
   if s['p_type']=='PT_LOAD' and s['p_vaddr']<=va and va+n<=s['p_vaddr']+s['p_filesz']:
    if executable and not s['p_flags']&1:raise ValueError('Non-executable code patch')
    return s['p_offset']+va-s['p_vaddr']
  raise ValueError('Unmapped VA')
 saved=json.loads((ROOT/'builds/universal_dual_wield_ui_sniper_splits/verification.json').read_text())['native_patch'];assert saved['output_sha256']==sha(data)
 roster=json.loads((ROOT/'reports/dual-wield-ui-evidence/weapon-roster.json').read_text())['roster'];roster={r['item_type']:r for r in roster}
 for ty,cls in GUNS.items():
  assert roster[ty]['create']==cls+'::create()'
  assert roster[ty]['virtuals']['triggerPull']['symbol']==cls+'::triggerPull(float)'
 out=bytearray(data);changes=[];ks=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN);cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 def replace(offset,new,reason,assembly=None,**meta):
  assert offset>=0 and offset+len(new)<=len(data)
  old=data[offset:offset+len(new)];out[offset:offset+len(new)]=new
  c=dict(file_offset=hex(offset),original=old.hex(),replacement=new.hex(),reason=reason,assembly=assembly,**meta)
  if assembly:
   listing=[dict(address=hex(i.address),instruction=i.mnemonic+' '+i.op_str) for i in cs.disasm(new,int(meta['elf_virtual_address'],16))];assert len(listing)*4==len(new);c['disassembly']=listing
  changes.append(c)
 for va,deny,prefix in [(0x8e6990,'done','pickup_pair'),(0x669d00,'single','ui_pair')]:
  previous=next(c for c in saved['changes'] if int(c['elf_virtual_address'],16)==va)
  expected=bytes.fromhex(previous['replacement']);assert data[off(va,len(expected)):off(va,len(expected))+len(expected)]==expected
  pattern='cmp w0, #9\\nb.ne '+prefix+'_0\\n.*?'+prefix+'_ok:\\n'
  assembly,count=re.subn(pattern,lambda _:membership_guard(deny),previous['assembly'],flags=re.S);assert count==1
  code=bytes(ks.asm(assembly,addr=va)[0]);limit=FIRE_HELPER if va==0x8e6990 else 0x669f84;assert va+len(code)<limit
  replace(off(va,len(code),True),code,'Same 22-gun mask drives explicit Dual acceptance and UI visibility; accepts every same/mixed gun pair, rejects nonguns',assembly,function=previous['function'],elf_virtual_address=hex(va))
 renderers=[]
 for ty,cls in GUNS.items():
  slot=sy['_ZTV'+str(len(cls))+cls]['st_value']+16+0x3d8;r=rels[slot];assert r['r_info_type']==257 and r['r_addend']==0
  target=ds.get_symbol(r['r_info_sym']).name;held='_ZN'+str(len(cls))+cls+'23setPrimaryConfigurationEv'
  if target!='_ZN4Item20setDualConfigurationEv':
   assert target==held or target=='_ZN'+str(len(cls))+cls+'20setDualConfigurationEv'
   renderers.append(dict(item_type=ty,gun=cls,status='Existing specialized/verified held dual transform preserved',target=target));continue
  assert held in sy
  idx=next(i for i,s in enumerate(ds.iter_symbols()) if s.name==held);ri=next(i for i,r0 in enumerate(rel.iter_relocations()) if r0['r_offset']==slot);ro=rel['sh_offset']+ri*rel['sh_entsize']+8
  replace(ro,struct.pack('<Q',(idx<<32)|257),'Gun-scoped empty dual slot uses existing held transform',function=cls+'::dual configuration vtable',elf_virtual_address=hex(slot),target=held,item_type=ty)
  renderers.append(dict(item_type=ty,gun=cls,status='Existing primary held transform reused for dual hand',target=held))
 # Custom charge/spin weapons read physical ammo directly; refresh via exact
 # previously tested getters before each distinct instance's original trigger.
 assert sy['_ZN22SoldierLocalController4fireEf']['st_value']==0x8ec46c
 assert data[off(0x8ec46c,4):off(0x8ec46c,4)+4]==bytes.fromhex('ffc300d1')
 asm=fire_helper();helper=bytes(ks.asm(asm,addr=FIRE_HELPER)[0]);assert FIRE_HELPER+len(helper)<=0x8e6cac
 replace(off(FIRE_HELPER,len(helper),True),helper,'Use unreachable former pickup routing space for ABI-compliant active ammo refresh and one trigger call per weapon',asm,function='SoldierLocalController::fire helper',elf_virtual_address=hex(FIRE_HELPER))
 branch='b '+hex(FIRE_HELPER)
 replace(off(0x8ec46c,4,True),bytes(ks.asm(branch,addr=0x8ec46c)[0]),'Local fire dispatch refreshes both live ammo fields for custom guns through working getters; original per-instance trigger/timing/projectile methods unchanged',branch,function='_ZN22SoldierLocalController4fireEf',elf_virtual_address='0x8ec46c')
 allowed=set()
 for c in changes:allowed.update(range(int(c['file_offset'],16),int(c['file_offset'],16)+len(bytes.fromhex(c['replacement']))))
 assert len(out)==len(data) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,out)))
 protected=[]
 for ty,cls in GUNS.items():
  names=['_ZN'+str(len(cls))+cls+'11triggerPullEf','_ZN'+str(len(cls))+cls+'23setPrimaryConfigurationEv']
  for name in names:
   s=sy[name];o=off(s['st_value'],s['st_size']);assert out[o:o+s['st_size']]==data[o:o+s['st_size']];protected.append(dict(function=name,sha256=sha(data[o:o+s['st_size']])))
 for name in ['_ZN6Weapon7getClipEv','_ZN6Weapon7getAmmoEv','_ZN6Weapon7subAmmoEi','_ZN22SoldierLocalController8getPowerEv']:
  s=sy[name];o=off(s['st_value'],s['st_size']);assert out[o:o+s['st_size']]==data[o:o+s['st_size']];protected.append(dict(function=name,sha256=sha(data[o:o+s['st_size']])))
 return bytes(out),dict(input_sha256=sha(data),output_sha256=sha(out),changes=changes,gun_classes={str(k):v for k,v in GUNS.items()},gun_mask=hex(MASK),ordered_pairs=len(GUNS)**2,renderers=renderers,preserved_functions=protected,stage='Consolidated universal-gun build; SPAS/sniper physical PASS, remaining gun/mixed physical regression pending',ownership='Confirmed distinct-instance/occupied-slot guards and normal Swap behavior preserved; dual replacement remains disabled',firing='One original trigger per live gun; existing getter refresh before direct-ammo custom gun triggers; no projectile/damage/timer method edits')
if __name__=='__main__':
 n,m=patch(working_native());print(m['output_sha256']);print('guns',len(GUNS),'pairs',m['ordered_pairs']);(ROOT/'reports/universal-guns-evidence/native-patches.json').write_text(json.dumps(m,indent=2)+'\n')
