#!/usr/bin/env python3
"""Phase 5 action selection, scoped to physically verified SPAS pair mechanics.
Reuse both stock menu items, touch dispatch, spacing and held rendering.
"""
import io,json,zipfile
from elftools.elf.elffile import ELFFile
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from patch_duplicate_inventory import ROOT,sha,controller_call
WORKING_SHA='b6f87aed1e1898c55b726720d6cb45d0796d54177ce94ed0be2c64d889262102'
SUPPORTED_TYPE=9  # Physical SPAS action-selection gate; expand after Test A.

def working_native():
 with zipfile.ZipFile(ROOT/'builds/universal_dual_wield_splits/split_config.arm64_v8a.apk') as z:return z.read('lib/arm64-v8a/libcocos2dcpp.so')

def patch(data):
 if sha(data)!=WORKING_SHA:raise ValueError('Exact user-confirmed SPAS dual build required')
 elf=ELFFile(io.BytesIO(data));ds=elf.get_section_by_name('.dynsym');sy={s.name:s for s in ds.iter_symbols()}
 def offset(va,size):
  for s in elf.iter_segments():
   if s['p_type']=='PT_LOAD' and s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']:
    if not s['p_flags']&1:raise ValueError('Patch must be executable')
    return s['p_offset']+va-s['p_vaddr']
  raise ValueError('Unmapped patch')
 functions={'pickup':'_ZN22SoldierLocalController9addWeaponEP6Weapon','ui':'_ZN3HUD16weaponProxyStartEPN7cocos2d8CCObjectE','proximity':'_ZN13WeaponManager15weaponProximityEP6Weapon'}
 for key,va,size in [('pickup',0x8e6934,1324),('ui',0x669b3c,1960),('proximity',0x9576c0,1360)]:
  s=sy[functions[key]];assert (s['st_value'],s['st_size'])==(va,size)
 ks=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN);out=bytearray(data);changes=[]
 def replace(va,new,reason,key,assembly=None):
  f=sy[functions[key]];assert f['st_value']<=va<va+len(new)<=f['st_value']+f['st_size']
  off=offset(va,len(new));old=data[off:off+len(new)];out[off:off+len(new)]=new
  decoded=[dict(address=hex(i.address),instruction=i.mnemonic+' '+i.op_str) for i in Cs(CS_ARCH_ARM64,CS_MODE_ARM).disasm(new,va)];assert len(decoded)*4==len(new)
  changes.append(dict(function=functions[key],elf_virtual_address=hex(va),file_offset=hex(off),original=old.hex(),replacement=new.hex(),reason=reason,assembly=assembly,disassembly=decoded))
 pickup='''
 str w0, [sp, #4]
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
 ldr w9, [sp, #4]
 tbz w9, #0, normal
 mov x0, x10
 ldr x8, [x0]
 ldr x8, [x8, #0x600]
 blr x8
 tbnz w0, #0, normal
 ldur x8, [x29, #-0x18]
 ldr x9, [x8, #0x1d8]
 cbnz x9, done
 ldr x9, [x8, #0x1c8]
 cbz x9, done
 ldur x0, [x29, #-0x10]
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 cmp w0, #9
 b.ne done
 ldur x8, [x29, #-0x18]
 ldr x0, [x8, #0x1c8]
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 cmp w0, #9
 b.ne done
'''+controller_call(0x440,True)+'''
 mov w1, #4
 adrp x8, 0x13bf000
 ldr x8, [x8, #0x4d0]
 ldr x0, [x8]
 bl 0x4c0ce0
 done:
 b 0x8e6e54
 normal:
 b 0x8e6cac
'''
 code=bytes(ks.asm(pickup,addr=0x8e6990)[0]);assert 0x8e6990+len(code)<0x8e6cac
 replace(0x8e6990,code,'Separate actions using original pickupAsDual result: normal uses retained inventory; explicit Dual accepts only supported distinct SPAS pair with empty dual slot; rejects unsupported Dual without normal swap','pickup',pickup)
 # Stock function already cached primary/stowed/dual and reset both controls.
 # The dedicated dual-only equipment display at 0x669cd4 remains intact.
 ui='''
 ldur x0, [x29, #-0x70]
 cbz x0, hidden
 ldur x9, [x29, #-0x78]
 cmp x0, x9
 b.eq hidden
 ldur x9, [x29, #-0x80]
 cmp x0, x9
 b.eq hidden
 ldur x9, [x29, #-0x88]
 cmp x0, x9
 b.eq hidden
 ldr x8, [x0]
 ldr x8, [x8, #0x600]
 blr x8
 tbnz w0, #0, utility
 ldur x9, [x29, #-0x78]
 cbz x9, single
 ldur x9, [x29, #-0x88]
 cbnz x9, single
 ldur x0, [x29, #-0x70]
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 cmp w0, #9
 b.ne single
 ldur x0, [x29, #-0x78]
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 cmp w0, #9
 b.ne single
 b 0x669f84
 utility:
 ldur x0, [x29, #-0x78]
 cbz x0, secondary_utility
 ldr x8, [x0]
 ldr x8, [x8, #0x5f8]
 blr x8
 tbnz w0, #0, utility_visible
 secondary_utility:
 ldur x0, [x29, #-0x80]
 cbz x0, hidden
 ldr x8, [x0]
 ldr x8, [x8, #0x5f8]
 blr x8
 tbz w0, #0, hidden
 utility_visible:
 b 0x669cd4
 single:
 b 0x66a184
 hidden:
 b 0x66a2bc
'''
 assert data[offset(0x669c14,4):offset(0x669c14,4)+4]==bytes.fromhex('ea031f2a')
 replace(0x669c14,bytes(ks.asm('b 0x669d00',addr=0x669c14)[0]),'Enter explicit compatible-pair UI policy after stock hide/reset and slot caching','ui','b 0x669d00')
 code=bytes(ks.asm(ui,addr=0x669d00)[0]);assert 0x669d00+len(code)<0x669f84
 replace(0x669d00,code,'SPAS pair exposes both stock buttons; no primary or incompatible/occupied dual exposes normal only; dual-only utility keeps original display path','ui',ui)
 assert data[offset(0x957aa4,4):offset(0x957aa4,4)+4]==bytes.fromhex('52000014')
 replace(0x957aa4,bytes.fromhex('1f2003d5'),'Do not suppress nearby third matching gun when both hands have matching instances; stock availability/range checks still run, allowing normal Swap while Dual is disabled','proximity','nop')
 allowed=set()
 for c in changes:allowed.update(range(int(c['file_offset'],16),int(c['file_offset'],16)+len(bytes.fromhex(c['replacement']))))
 assert len(out)==len(data) and all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,out)))
 preserved=[]
 for name in ['_ZN6Weapon7getClipEv','_ZN6Weapon7getAmmoEv','_ZN6Weapon7subAmmoEi','_ZN22SoldierLocalController8getPowerEv','_ZN22SoldierLocalController4fireEf','_ZN7SHOTGUN11triggerPullEf','_ZN3HUD14onPickUpWeaponEPN7cocos2d8CCObjectE','_ZN3HUD18onPickUpDualWeaponEPN7cocos2d8CCObjectE']:
  s=sy[name];off=offset(s['st_value'],s['st_size']);assert out[off:off+s['st_size']]==data[off:off+s['st_size']];preserved.append(dict(function=name,sha256=sha(data[off:off+s['st_size']])))
 return bytes(out),dict(input_sha256=sha(data),output_sha256=sha(out),changes=changes,preserved_functions=preserved,compatibility_stage='SPAS two-action physical Test A pending; other gun combinations not enabled until this gate passes',dual_occupied='Dedicated Dual button hidden, explicit stale Dual rejected. Normal swap follows stock retained inventory/drop routing.',ownership='Distinct pointer checks; stock retain/release callbacks; no new ownership or cached pickup pointers',assets='Existing wepChangeBtn.png and dualBtn.png; stock scaling/positions/opacity/touch menus preserved')
if __name__=='__main__':
 import argparse
 from pathlib import Path
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists();native,m=patch(working_native());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(native);a.output.with_suffix('.patches.json').write_text(json.dumps(m,indent=2)+'\n');print(m['output_sha256'])
