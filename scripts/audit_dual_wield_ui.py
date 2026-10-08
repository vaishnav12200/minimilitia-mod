#!/usr/bin/env python3
"""Recover factory roster and class virtual targets; structural evidence only."""
import io,json,struct,subprocess
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from patch_dual_wield_ui import ROOT,working_native,patch,sha

def main():
 native=working_native();elf=ELFFile(io.BytesIO(native));ds=elf.get_section_by_name('.dynsym');sy={s.name:s for s in ds.iter_symbols()};cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM);cs.detail=True
 def offset(a,n):
  for s in elf.iter_segments():
   if s['p_type']=='PT_LOAD' and s['p_vaddr']<=a and a+n<=s['p_vaddr']+s['p_filesz']:return s['p_offset']+a-s['p_vaddr']
  raise ValueError(hex(a))
 def read(a,n):off=offset(a,n);return native[off:off+n]
 rels={r['r_offset']:r for r in elf.get_section_by_name('.rela.dyn').iter_relocations()};plt={r['r_offset']:ds.get_symbol(r['r_info_sym']) for r in elf.get_section_by_name('.rela.plt').iter_relocations()}
 def target(slot):
  r=rels[slot]
  return r['r_addend'] if r['r_info_type']==1027 else ds.get_symbol(r['r_info_sym'])['st_value']+r['r_addend']
 def demangle(name):return subprocess.run(['c++filt',name],capture_output=True,text=True,check=True).stdout.strip()
 rows=[]
 for ty in range(1,40):
  branch=0x1090578+struct.unpack('<i',read(0x1090578+(ty-1)*4,4))[0]
  ins=next(cs.disasm(read(branch,4),branch))
  if ins.mnemonic!='bl':continue
  call=ins.operands[0].imm;pi=list(cs.disasm(read(call,16),call));got=pi[0].operands[1].imm+pi[1].operands[1].mem.disp
  creator=plt[got].name;name=demangle(creator);cls=name.split('::')[0];vname='_ZTV'+str(len(cls))+cls
  row=dict(item_type=ty,factory_branch=hex(branch),create_plt=hex(call),create_got=hex(got),create=name)
  if vname in sy:
   vt=sy[vname]['st_value']+16;entries={}
   for label,slot in [('dual_configuration',0x3d8),('primary_configuration',0x3c8),('triggerPull',0x4f8)]:
    va=target(vt+slot);names=[n for n,s in sy.items() if s['st_value']==va and n.startswith('_ZN')];entries[label]=dict(va=hex(va),symbol=demangle(names[0]) if names else 'unknown')
   row['virtuals']=entries
  row['phase5_status']='SPAS held-pair user confirmed; action UI pending' if ty==9 else 'NOT enabled/verified for generalized dual pairing'
  rows.append(row)
 candidate,manifest=patch(native);result=dict(baseline_sha256=sha(native),candidate_sha256=sha(candidate),roster=rows,limits='Factory classes and virtual targets verified; classifications/render/fire/network correctness must be checked per class. Shared fire dispatcher does not prove class compatibility.')
 p=ROOT/'reports/dual-wield-ui-evidence/weapon-roster.json';p.write_text(json.dumps(result,indent=2)+'\n');print('Recovered',len(rows),'factory ItemTypes; SPAS only is enabled in current UI gate')
if __name__=='__main__':main()
