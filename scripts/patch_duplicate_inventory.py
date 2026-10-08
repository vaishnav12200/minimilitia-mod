#!/usr/bin/env python3
"""Patch slot routing only, layering on the exact device-tested ammo/fuel build.
No original or working native/APK files are overwritten.
"""
import argparse,hashlib,io,json,zipfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ROOT=Path(__file__).resolve().parents[1]
WORKING_SHA='8cac1bfb7c7c523bbfbb2c33ea3c446acb2d8db24d0a639799b04d74b8026f60'
FUNCTION='_ZN22SoldierLocalController9addWeaponEP6Weapon'
BLOCK=0x8e6d50;BLOCK_END=0x8e6e54

def sha(data):return hashlib.sha256(data).hexdigest()
def working_native():
 with zipfile.ZipFile(ROOT/'builds/fixed_ammo_dual_weapon_splits/split_config.arm64_v8a.apk') as z:return z.read('lib/arm64-v8a/libcocos2dcpp.so')
def controller_call(offset,argument=False):
 return f'ldur x0, [x29, #-0x18]\nldr x8, [x0]\nldr x8, [x8, #{offset}]\n'+('ldur x1, [x29, #-0x10]\n' if argument else '')+'blr x8\n'
def slot_code():
 source='''
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
 ldr x9, [x8, #0x1c8]
 cbz x9, add_primary
 ldr x9, [x8, #0x1d0]
 cbz x9, add_secondary
 ldur x0, [x29, #-0x10]
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 str w0, [sp]
 ldur x8, [x29, #-0x18]
 ldr x0, [x8, #0x1c8]
 ldr x8, [x0]
 ldr x8, [x8, #0x520]
 blr x8
 ldr w9, [sp]
 cmp w0, w9
 b.ne replace_primary
'''
 source+=controller_call(0x5b8)
 source+='replace_primary:\n'+controller_call(0x418)
 source+='add_primary:\n'+controller_call(0x690,True)+'b sound\n'
 source+='add_secondary:\n'+controller_call(0x438,True)+controller_call(0x5b8)
 source+='''sound:
 mov w1, #4
 adrp x8, 0x13bf000
 ldr x8, [x8, #0x4d0]
 ldr x0, [x8]
 bl 0x4c0ce0
 done:
 b 0x8e6e54
'''
 code=bytes(Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN).asm(source,addr=BLOCK)[0])
 if len(code)>BLOCK_END-BLOCK:raise ValueError(f'Slot routine too big: {len(code)}')
 return code+bytes.fromhex('1f2003d5')*((BLOCK_END-BLOCK-len(code))//4),source,len(code)

def patch(data):
 if sha(data)!=WORKING_SHA:raise ValueError('Exact latest device-tested build required; refusing old combined/reload-bug input')
 elf=ELFFile(io.BytesIO(data));symtab=elf.get_section_by_name('.dynsym');syms={s.name:s for s in symtab.iter_symbols()}
 if elf['e_machine']!='EM_AARCH64':raise ValueError('Expected AArch64')
 f=syms[FUNCTION]
 if f['st_value']!=0x8e6934 or f['st_size']!=1324:raise ValueError('Function extent mismatch')
 original=(ROOT/'native-analysis/backup/libcocos2dcpp.so').read_bytes()
 if sha(original)!='2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401':raise ValueError('Original backup hash mismatch')
 def offset(va,size):
  for segment in elf.iter_segments():
   if segment['p_type']=='PT_LOAD' and segment['p_vaddr']<=va and va+size<=segment['p_vaddr']+segment['p_filesz']:
    if not segment['p_flags']&1:raise ValueError('Non-executable patch')
    return segment['p_offset']+va-segment['p_vaddr']
  raise ValueError('Unmapped patch')
 entry=offset(f['st_value'],f['st_size'])
 if data[entry:entry+f['st_size']]!=original[entry:entry+f['st_size']]:raise ValueError('addWeapon already differs from original')
 # Verify controller vtable slots via dynamic RELATIVE relocations.
 rels={r['r_offset']:r for r in elf.get_section_by_name('.rela.dyn').iter_relocations()}
 vt=syms['_ZTV22SoldierLocalController']['st_value']+16
 virtuals={0x418:'_ZN22SoldierLocalController19removePrimaryWeaponEv',0x438:'_ZN22SoldierLocalController18addSecondaryWeaponEP6Weapon',0x5b8:'_ZN22SoldierLocalController13switchWeaponsEv',0x690:'_ZN22SoldierLocalController26addPrimaryWeaponRemoveDualEP6Weapon'}
 for slot,name in virtuals.items():
  r=rels[vt+slot]
  if r['r_info_type']==1027:target=r['r_addend']
  elif r['r_info_sym']:target=symtab.get_symbol(r['r_info_sym'])['st_value']+r['r_addend']
  else:raise ValueError('Unsupported vtable relocation')
  if target!=syms[name]['st_value']:raise ValueError('Wrong controller vtable target')
 weapon_vt=syms['_ZTV6Weapon']['st_value']+16
 r=rels[weapon_vt+0x520]
 target=(r['r_addend'] if r['r_info_type']==1027 else symtab.get_symbol(r['r_info_sym'])['st_value']+r['r_addend'])
 if target!=syms['_ZN6Weapon7getTypeEv']['st_value']:raise ValueError('Wrong weapon type getter')
 cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM);cs.detail=True;changes=[];out=bytearray(data)
 def replace(va,expected,new,purpose,assembly=None):
  off=offset(va,len(expected))
  if not f['st_value']<=va<va+len(expected)<=f['st_value']+f['st_size']:raise ValueError('Outside addWeapon')
  if data[off:off+len(expected)]!=expected or len(expected)!=len(new):raise ValueError('Original bytes/size mismatch')
  if va%4 or len(new)%4:raise ValueError('Unaligned code')
  out[off:off+len(new)]=new
  changes.append(dict(function=FUNCTION,elf_virtual_address=hex(va),file_offset=hex(off),original=expected.hex(),replacement=new.hex(),purpose=purpose,assembly=assembly))
 va=0x8e698c;ins=next(cs.disasm(data[offset(va,4):offset(va,4)+4],va))
 if ins.mnemonic!='tbz' or ins.operands[-1].imm!=0x8e6cac:raise ValueError('Unexpected pickup-dual branch')
 code=bytes(Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN).asm('b 0x8e6cac',addr=va)[0])
 replace(va,bytes.fromhex('00190036'),code,'Route ordinary dual-capable pickups through retained dual-only guard to two-slot block')
 code,assembly,size=slot_code();off=offset(BLOCK,BLOCK_END-BLOCK)
 if data[off:off+4]!=bytes.fromhex('a8835ef8') or data[offset(BLOCK_END,4):offset(BLOCK_END,4)+4]!=bytes.fromhex('fd7b44a9'):raise ValueError('Unexpected ordinary block/epilogue')
 replace(BLOCK,data[off:off+len(code)],code,'Preserve matching primary when full; distinct pointers; stock add/remove/switch callbacks',assembly)
 allowed=set()
 for c in changes:allowed.update(range(int(c['file_offset'],16),int(c['file_offset'],16)+len(bytes.fromhex(c['replacement']))))
 if len(out)!=len(data) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(data,out))):raise ValueError('Unexpected mutation')
 protected=[('_ZN6Weapon7getClipEv',0x947954,204),('_ZN6Weapon7getAmmoEv',0x947a20,204),('_ZN6Weapon7subAmmoEi',0x9482e0,syms['_ZN6Weapon7subAmmoEi']['st_size']),('_ZN22SoldierLocalController8getPowerEv',0x8e68e4,8)]
 preserved=[]
 for name,address,length in protected:
  start=offset(address,length)
  if out[start:start+length]!=data[start:start+length]:raise ValueError('Working gameplay patch changed')
  preserved.append(dict(symbol=name,va=hex(address),bytes=length,sha256=sha(data[start:start+length])))
 manifest=dict(input_sha256=sha(data),output_sha256=sha(out),changes=changes,slot_code_bytes=size,protected_gameplay=preserved,calling_convention='Existing AAPCS64 frame: x0=controller, x1=incoming Weapon*, void return; only caller-saved registers used; original saved x29/x30 and epilogue retained',status='Experimental inventory patch; gameplay verification pending')
 return bytes(out),manifest

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 if a.output.exists():raise SystemExit('Refusing overwrite')
 if a.output.resolve() in [ROOT/'native-analysis/libcocos2dcpp.so',ROOT/'native-analysis/backup/libcocos2dcpp.so']:raise SystemExit('Protected native')
 data,manifest=patch(working_native());a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(data);a.output.with_suffix('.patches.json').write_text(json.dumps(manifest,indent=2)+'\n');print(manifest['output_sha256']);print('Slot routine bytes:',manifest['slot_code_bytes'])
if __name__=='__main__':main()
