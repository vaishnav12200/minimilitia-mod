#!/usr/bin/env python3
"""Read-only call-site and ammo-store inventory on the original ELF."""
import bisect,io,json,struct,subprocess
from pathlib import Path
from elftools.elf.elffile import ELFFile
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
ROOT=Path(__file__).resolve().parents[1]
def main():
 data=(ROOT/'native-analysis/backup/libcocos2dcpp.so').read_bytes(); elf=ELFFile(io.BytesIO(data))
 symbols=list(elf.get_section_by_name('.dynsym').iter_symbols())
 names=subprocess.run(['c++filt'],input='\n'.join(s.name for s in symbols),capture_output=True,text=True,check=True).stdout.splitlines()
 names_by_symbol=dict(zip((s.name for s in symbols),names))
 functions=sorted((s['st_value'],s['st_size'],n) for s,n in zip(symbols,names) if s['st_info']['type']=='STT_FUNC' and s['st_value'] and s['st_size'])
 starts=[r[0] for r in functions]
 def owner(va):
  i=bisect.bisect_right(starts,va)-1
  return functions[i][2] if i>=0 and va<functions[i][0]+functions[i][1] else 'unknown'
 def offset(va):
  for s in elf.iter_segments():
   if s['p_type']=='PT_LOAD' and s['p_vaddr']<=va<s['p_vaddr']+s['p_filesz']:return s['p_offset']+va-s['p_vaddr']
  raise ValueError(hex(va))
 relocs={}
 for sec in elf.iter_sections():
  if sec['sh_type']=='SHT_RELA':
   symtab=elf.get_section(sec['sh_link'])
   for r in sec.iter_relocations():
    if r['r_info_sym']:relocs[r['r_offset']]=names_by_symbol.get(symtab.get_symbol(r['r_info_sym']).name,'')
 cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM); cs.detail=True; targets={}
 plt=elf.get_section_by_name('.plt')
 for va in range(plt['sh_addr'],plt['sh_addr']+plt['sh_size'],4):
  ins=list(cs.disasm(data[offset(va):offset(va)+8],va))
  if len(ins)==2 and ins[0].mnemonic=='adrp' and ins[1].mnemonic=='ldr':
   got=ins[0].operands[1].imm+ins[1].operands[1].mem.disp
   if got in relocs and relocs[got].startswith(('Weapon::subAmmo(', 'Weapon::setClip(', 'Weapon::setAmmo(')):targets[va]=relocs[got]
 calls=[]; stores=[]; txt=elf.get_section_by_name('.text'); code=txt.data()
 for index in range(0,len(code)-3,4):
  word=struct.unpack_from('<I',code,index)[0]; va=txt['sh_addr']+index
  if word&0xfc000000==0x94000000:
   imm=word&0x3ffffff; imm=imm-(1<<26) if imm&(1<<25) else imm; dest=va+imm*4
   if dest in targets:calls.append(dict(va=hex(va),function=owner(va),target=targets[dest]))
  if word&0xffc00000==0x79000000 and ((word>>10)&0xfff)*2 in (0x360,0x362):
   context=list(cs.disasm(code[max(0,index-16):index+4],va-16))
   stores.append(dict(va=hex(va),file_offset=hex(offset(va)),field=hex(((word>>10)&0xfff)*2),function=owner(va),context=[f'{i.address:#x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in context]))
 result=dict(calls=calls,stores=stores)
 out=ROOT/'reports/reload-fix-evidence/ammo-call-sites.json';out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
