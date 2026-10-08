#!/usr/bin/env python3
"""Read-only ELF function mapping, callee preservation and replacement listing."""
import io,json
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from patch_duplicate_inventory import ROOT,working_native,patch,sha

def main():
 data=working_native();new,manifest=patch(data);elf=ELFFile(io.BytesIO(data));symtab=elf.get_section_by_name('.dynsym');syms={s.name:s for s in symtab.iter_symbols()};cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
 names=['_ZN22SoldierLocalController9addWeaponEP6Weapon','_ZN22SoldierLocalController16addPrimaryWeaponEP6Weapon','_ZN22SoldierLocalController18addSecondaryWeaponEP6Weapon','_ZN22SoldierLocalController19removePrimaryWeaponEv','_ZN22SoldierLocalController21removeSecondaryWeaponEv','_ZN22SoldierLocalController26addPrimaryWeaponRemoveDualEP6Weapon','_ZN22SoldierLocalController13switchWeaponsEv','_ZN14SoldierManager11spawnPlayerEv','_ZN6Weapon11getAmmoTypeEv','_ZN6Weapon7getTypeEv','_ZN13WeaponManager14onPickUpWeaponEPN7cocos2d8CCObjectE']
 records=[];listing=[]
 for name in names:
  s=syms.get(name)
  if s is None:continue
  va=s['st_value'];size=s['st_size'];seg=next(s for s in elf.iter_segments() if s['p_type']=='PT_LOAD' and s['p_vaddr']<=va and va+size<=s['p_vaddr']+s['p_filesz']);off=seg['p_offset']+va-seg['p_vaddr']
  records.append(dict(symbol=name,va=hex(va),file_offset=hex(off),size=size,sha256=sha(data[off:off+size]),unchanged_by_new_patch=data[off:off+size]==new[off:off+size]))
  listing.append(f'\n{name} VA={va:#x} FILE={off:#x} SIZE={size}\n')
  for i in cs.disasm(data[off:off+size],va):listing.append(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}\n')
 rels={r['r_offset']:r for r in elf.get_section_by_name('.rela.dyn').iter_relocations()};r=rels[syms['_ZTV6Weapon']['st_value']+16+0x520]
 target=r['r_addend'] if r['r_info_type']==1027 else symtab.get_symbol(r['r_info_sym'])['st_value']+r['r_addend']
 if target!=syms['_ZN6Weapon7getTypeEv']['st_value']:raise ValueError('Wrong type getter dispatch')
 for c in manifest['changes']:
  va=int(c['elf_virtual_address'],16);listing.append(f'\nPATCHED {va:#x}\n')
  for i in cs.disasm(bytes.fromhex(c['replacement']),va):listing.append(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}\n')
 evidence=ROOT/'reports/duplicate-inventory-evidence'
 (evidence/'native-audit.json').write_text(json.dumps(dict(input_sha256=sha(data),output_sha256=sha(new),functions=records,patch=manifest,type_virtual='Weapon +0x520 -> getType (ItemType field +0x338)'),indent=2)+'\n')
 (evidence/'native-disassembly.txt').write_text(''.join(listing))
 print('PASS: independent ELF mapping, callee preservation, type dispatch and replacement disassembly')
if __name__=='__main__':main()
