#!/usr/bin/env python3
"""Read-only ELF audit; compares the preserved combined package with original ELF."""
import hashlib, io, json, struct, subprocess, zipfile
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/phase4-evidence'
TARGETS = ('SoldierLocalController::addWeapon(', 'SoldierLocalController::addPrimaryWeapon(',
 'SoldierLocalController::addSecondaryWeapon(', 'SoldierLocalController::switchWeapons(',
 'SoldierLocalController::dropWeaponByID(', 'SoldierLocalController::removePrimaryWeapon(',
 'SoldierLocalController::removeSecondaryWeapon(', 'ClientRoom::validateLoadout(',
 'ClientRoom::setLoadoutUUIDs(', 'ClientEntry::applyLoadout(', 'ItemLibrary::applyItems(',
 'WeaponFactory::createWeaponFromAmmoType(', 'Weapon::isDualWield(',
 'Weapon::isDualWieldDualOnly(', 'Weapon::isDualWieldPrimaryOnly(', 'Weapon::isMeleeOnlyWeapon(',
 'LoadoutMenu::onPrimary(', 'LoadoutMenu::onSecondary(', 'LoadoutMenu::updateState(',
 'LoadoutMenu::validateWeapons(', 'LoadoutLayer::testValid(', 'Weapon::subAmmo(',
 'SoldierLocalController::getPower(')
def digest(b): return hashlib.sha256(b).hexdigest()
def main():
 OUT.mkdir(exist_ok=True)
 original = (ROOT/'native-analysis/backup/libcocos2dcpp.so').read_bytes()
 with zipfile.ZipFile(ROOT/'builds/combined_mod_splits/split_config.arm64_v8a.apk') as z:
  combined = z.read('lib/arm64-v8a/libcocos2dcpp.so')
 assert digest(original) == '2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401'
 expected = bytearray(original)
 expected[0x9482e0:0x9482e4] = bytes.fromhex('c0035fd6')
 expected[0x8e68e4:0x8e68ec] = bytes.fromhex('00102e1ec0035fd6')
 assert combined == expected, 'Combined build contains unexpected modifications'
 elf = ELFFile(io.BytesIO(original)); assert elf['e_machine']=='EM_AARCH64'
 loads = [s for s in elf.iter_segments() if s['p_type']=='PT_LOAD']
 def offset(va):
  for s in loads:
   if s['p_vaddr'] <= va < s['p_vaddr']+s['p_filesz']: return s['p_offset']+va-s['p_vaddr']
  raise ValueError(hex(va))
 syms = list(elf.get_section_by_name('.dynsym').iter_symbols())
 names = subprocess.run(['c++filt'], input='\n'.join(s.name for s in syms), capture_output=True,text=True,check=True).stdout.splitlines()
 demangled = dict(zip((s.name for s in syms), names))
 byaddr={s['st_value']:n for s,n in zip(syms,names) if s['st_value']}
 # Resolve PLT calls using AArch64 ADRP/LDR GOT lookup and dynamic relocations.
 relocs={}
 for section in elf.iter_sections():
  if section['sh_type'] in ('SHT_RELA','SHT_REL'):
   table=elf.get_section(section['sh_link'])
   for r in section.iter_relocations():
    if r['r_info_sym']: relocs[r['r_offset']]=table.get_symbol(r['r_info_sym']).name
    elif r.is_RELA(): relocs[r['r_offset']]=byaddr.get(r['r_addend'],hex(r['r_addend']))
 cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM); cs.detail=True
 plt=elf.get_section_by_name('.plt')
 for pos in range(plt['sh_addr'],plt['sh_addr']+plt['sh_size'],4):
  off=offset(pos); ins=list(cs.disasm(original[off:off+8],pos))
  if len(ins)==2 and ins[0].mnemonic=='adrp' and ins[1].mnemonic=='ldr':
   got=ins[0].operands[1].imm+ins[1].operands[1].mem.disp
   if got in relocs:
    byaddr[pos]=demangled.get(relocs[got],relocs[got])
 records=[]; dis=[]
 for s,n in zip(syms,names):
  if not s['st_value'] or not any(n.startswith(t) for t in TARGETS): continue
  va=s['st_value']; off=offset(va); size=s['st_size']
  records.append(dict(name=n,symbol=s.name,va=hex(va),file_offset=hex(off),size=size,original=original[off:off+8].hex(),combined=combined[off:off+8].hex()))
  dis.append(f'\n{n} VA={va:#x} FILE={off:#x} SIZE={size}\n')
  for i in cs.disasm(original[off:off+size],va):
   comment=''
   if i.mnemonic in ('bl','b') and i.operands[0].type==2: comment=byaddr.get(i.operands[0].imm,'')
   dis.append(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic:8} {i.op_str:40} {comment}\n')
 # Vtable offset 0 denotes the address point, following offset-to-top and RTTI.
 vtables={}
 for s,n in zip(syms,names):
  if n in ('vtable for Weapon','vtable for SoldierLocalController','vtable for SoldierRemoteController'):
   slots={}
   for slot in range(0,s['st_size']-16,8):
    va=s['st_value']+16+slot; raw=struct.unpack_from('<Q',original,offset(va))[0]
    slots[hex(slot)]=relocs.get(va,byaddr.get(raw,hex(raw)))
   vtables[n]=slots
 report=dict(original_sha256=digest(original),combined_sha256=digest(combined),baseline_patch_check='PASS',functions=records,vtables=vtables)
 (OUT/'native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
 (OUT/'native-disassembly.txt').write_text(''.join(dis))
 print('PASS: combined differs only by the two working patches; mapped',len(records),'functions')
if __name__=='__main__': main()
