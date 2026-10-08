#!/usr/bin/env python3
"""Execute real addWeapon ARM64 control flow with virtual ownership fixtures.
Not Android gameplay. Stock virtual callbacks are modelled, not Cocos rendering.
"""
import io,json,struct,zipfile
from pathlib import Path
from unicorn import Uc,UC_ARCH_ARM64,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm64_const import *
from elftools.elf.elffile import ELFFile
ROOT=Path(__file__).resolve().parents[1]
FUNCTION=0x8e6934;SIZE=1324
S=0x2000000;SV=0x2001000;W=[0x2002000,0x2003000,0x2004000];WV=0x2005000;STUB=0x2006000
STACK=0x3000000;SP=STACK+0x10000;STOP=0x4000000

def working():
 with zipfile.ZipFile(ROOT/'builds/fixed_ammo_dual_weapon_splits/split_config.arm64_v8a.apk') as z:return z.read('lib/arm64-v8a/libcocos2dcpp.so')

def execute(native,primary,secondary,incoming,dual=False,pickup_dual=False,primary_only=False,dual_only=False):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x400000,0x1000000);u.mem_map(S,0x10000);u.mem_map(STACK,0x11000);u.mem_map(STOP,0x1000)
 u.mem_write(FUNCTION,native[FUNCTION:FUNCTION+SIZE]);u.mem_write(0x13bf4d0,struct.pack('<Q',S+0x7000))
 def writeq(addr,value):u.mem_write(addr,struct.pack('<Q',value))
 def readq(addr):return struct.unpack('<Q',u.mem_read(addr,8))[0]
 def setslot(off,value):writeq(S+off,value)
 writeq(S,SV);setslot(0x1c8,primary or 0);setslot(0x1d0,secondary or 0);setslot(0x1d8,0)
 types={W[0]:11,W[1]:17,W[2]:incoming[1]};incoming_ptr=incoming[0]
 callbacks={};events=[];retain={p:1 for p in (primary,secondary) if p};dropped=[]
 def addstub(name,handler):
  va=STUB+len(callbacks)*16;callbacks[va]=(name,handler);u.mem_write(va,bytes.fromhex('c0035fd6'));return va
 def setter(off):
  def call():
   p=u.reg_read(UC_ARM64_REG_X1);assert readq(S+off)==0,'overwrite without release'
   assert p not in [readq(S+x) for x in (0x1c8,0x1d0,0x1d8)],'aliased weapon pointer'
   setslot(off,p);retain[p]=retain.get(p,0)+1
  return call
 def remove(off):
  def call():
   p=readq(S+off)
   if p:retain[p]-=1;dropped.append(p)
   setslot(off,0)
  return call
 def swap():
  a,b=readq(S+0x1c8),readq(S+0x1d0);setslot(0x1c8,b);setslot(0x1d0,a)
 def first():remove(0x1d8)();setter(0x1c8)()
 for off,name,callback in ((0x418,'remove_primary',remove(0x1c8)),(0x420,'remove_dual',remove(0x1d8)),(0x430,'add_primary',setter(0x1c8)),(0x438,'add_secondary',setter(0x1d0)),(0x440,'add_dual',setter(0x1d8)),(0x5b8,'switch',swap),(0x690,'add_primary_remove_dual',first)):
  writeq(SV+off,addstub(name,callback))
 def return_value(value):u.reg_write(UC_ARM64_REG_W0,value)
 for off,name,callback in ((0x1d0,'stop_actions',lambda:None),(0x520,'get_type',lambda:return_value(types[u.reg_read(UC_ARM64_REG_X0)])),(0x618,'pickup_dual',lambda:return_value(pickup_dual)),(0x5f8,'is_dual',lambda:return_value(dual)),(0x608,'primary_only',lambda:return_value(primary_only)),(0x600,'dual_only',lambda:return_value(dual_only))):
  writeq(WV+off,addstub(name,callback))
 for p in W:writeq(p,WV)
 u.mem_write(0x4c0ce0,bytes.fromhex('c0035fd6'))
 def hook(uc,address,size,userdata):
  if address in callbacks:
   name,call=callbacks[address]
   if name in ['remove_primary','remove_dual','add_primary','add_secondary','add_dual','switch','add_primary_remove_dual']:assert uc.reg_read(UC_ARM64_REG_X0)==S
   events.append(name);call()
 u.hook_add(UC_HOOK_CODE,hook)
 u.reg_write(UC_ARM64_REG_X0,S);u.reg_write(UC_ARM64_REG_X1,incoming_ptr)
 u.reg_write(UC_ARM64_REG_X19,0x12345678);u.reg_write(UC_ARM64_REG_X29,0x1234);u.reg_write(UC_ARM64_REG_X30,STOP);u.reg_write(UC_ARM64_REG_SP,SP)
 u.emu_start(FUNCTION,STOP,count=3000)
 assert u.reg_read(UC_ARM64_REG_PC)==STOP and u.reg_read(UC_ARM64_REG_SP)==SP
 assert u.reg_read(UC_ARM64_REG_X19)==0x12345678 and u.reg_read(UC_ARM64_REG_X29)==0x1234
 return dict(primary=readq(S+0x1c8),secondary=readq(S+0x1d0),dual=readq(S+0x1d8),events=events,dropped=dropped,retains=retain)

def audit_baseline():
 native=working();records=[]
 for label,p,s,ty,flags in [('matching active with full inventory',W[0],W[1],11,{}),('matching stowed with full inventory',W[1],W[0],11,{}),('empty secondary ordinary',W[0],0,11,{}),('dual capable incoming with nondual-compatible two-slot expectation',W[0],W[1],11,dict(dual=True,pickup_dual=True)),('dual primary only',W[0],W[1],11,dict(dual=True,pickup_dual=True,primary_only=True))]:
  result=execute(native,p,s,(W[2],ty),**flags);records.append(dict(case=label,result=result))
 assert records[0]['result']['primary']==W[2] and records[0]['result']['secondary']==W[1]
 assert records[0]['result']['dropped']==[W[0]]
 assert records[1]['result']['secondary']==W[0] and records[1]['result']['primary']==W[2]
 assert records[3]['result']['dual']==W[2]
 out=dict(status='Baseline failure reproduced in synthetic ARM64 control flow',scope='Real addWeapon machine code; virtual callbacks/ownership modelled',records=records)
 (ROOT/'reports/duplicate-inventory-evidence/baseline-slot-routing.json').write_text(json.dumps(out,indent=2)+'\n')
 print(out['status'])
def test_patch():
 from patch_duplicate_inventory import patch,sha
 native,manifest=patch(working());records=[]
 # Same/different types, both orders, full/partial/empty inventory, all ordinary
 # dual capability/priority flags: all must use switchable primary/secondary.
 from itertools import product
 for primary,secondary in [(0,0),(W[0],0),(0,W[0]),(W[0],W[1]),(W[1],W[0])]:
  for ty,dual,pickup_dual,primary_only in product([11,17,23],[False,True],[False,True],[False,True]):
   r=execute(native,primary,secondary,(W[2],ty),dual,pickup_dual,primary_only)
   if not primary:expected=(W[2],secondary);dropped=[]
   elif not secondary:expected=(W[2],primary);dropped=[]
   elif ty==({W[0]:11,W[1]:17}[primary]):expected=(W[2],primary);dropped=[secondary]
   else:expected=(W[2],secondary);dropped=[primary]
   assert (r['primary'],r['secondary'])==expected and r['dual']==0, r
   assert r['dropped']==dropped and r['retains'][W[2]]==1
   if primary and primary not in dropped:assert r['retains'][primary]==1
   if secondary and secondary not in dropped:assert r['retains'][secondary]==1
   records.append(dict(primary=primary,secondary=secondary,type=ty,dual_capable=dual,pickup_dual=pickup_dual,primary_only=primary_only,result=r,status='PASS'))
 # Duplicate pointer inputs cannot obtain a second slot reference or drop inventory.
 for p,s,held in [(W[0],0,W[0]),(W[0],W[1],W[0]),(W[0],W[1],W[1])]:
  r=execute(native,p,s,(held,11));assert (r['primary'],r['secondary'])==(p,s) and r['dropped']==[]
  records.append(dict(alias_guard=held,result=r,status='PASS'))
 # Null incoming and utility dual-only path do not use ordinary two-slot block.
 r=execute(native,W[0],W[1],(0,11));assert (r['primary'],r['secondary'])==(W[0],W[1])
 records.append(dict(null_incoming='PASS'))
 for p,s in [(0,0),(W[0],0),(W[0],W[1])]:
  r=execute(native,p,s,(W[2],11),dual_only=True)
  old=execute(working(),p,s,(W[2],11),dual_only=True)
  assert r==old and r['dual']==W[2]
  records.append(dict(dual_only_stock_path='PASS',result=r))
 # Wrong-build preconditions fail, including old reload-bug input and changed code.
 changed=bytearray(working());changed[FUNCTION]^=1
 try:patch(bytes(changed));raise AssertionError('Wrong build accepted')
 except ValueError:pass
 records.append(dict(input_hash_rejection='PASS'))
 out=dict(status='ARM64 slot-routing/ownership fixtures PASS; NOT Android gameplay',cases=len(records),input_sha256=sha(working()),output_sha256=manifest['output_sha256'],records=records)
 (ROOT/'reports/duplicate-inventory-evidence/patched-slot-routing.json').write_text(json.dumps(out,indent=2)+'\n')
 print(out['status'],len(records),'cases')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--patched',action='store_true');a=p.parse_args()
 test_patch() if a.patched else audit_baseline()

