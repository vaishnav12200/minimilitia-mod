#!/usr/bin/env python3
"""Real ARM64 pickup routing/firing dispatch; callbacks simulated, no visual claim."""
import json,struct
from itertools import product
from patch_true_dual_wield import ROOT,working_native,patch
from dual_wield_arm64_fixture import *

def equivalent(a,b):
 a=dict(a);b=dict(b)
 for r in [a,b]:r["events"]=[x for x in r["events"] if x!="get_type"]
 return a==b

def main():
 old=working_native();native,manifest=patch(old);records=[]
 for p,s in [(0,0),(W[0],0),(0,W[0]),(W[0],W[1]),(W[1],W[0])]:
  for incoming_type,primary_type,dual,pickup in product([9,11,17],[9,11],[False,True],[False,True]):
   types={W[0]:primary_type,W[1]:primary_type,W[2]:incoming_type}
   args=dict(dual=dual,pickup_dual=pickup,type_overrides=types)
   r=execute(native,p,s,(W[2],incoming_type),**args)
   if p and incoming_type==9 and primary_type==9:
    assert (r['primary'],r['secondary'],r['dual'])==(p,s,W[2]),r
    assert r['dropped']==[] and r['retains'][W[2]]==1
   else:assert equivalent(r,execute(old,p,s,(W[2],incoming_type),**args)),r
   records.append(dict(primary=p,secondary=s,incoming_type=incoming_type,primary_type=primary_type,dual_flag=dual,pickup_flag=pickup,status='PASS'))
 for held in [W[0],W[1],W[2]]:
  r=execute(native,W[0],W[1],(held,9),initial_dual=W[2],type_overrides={x:9 for x in W})
  assert (r['primary'],r['secondary'],r['dual'])==tuple(W) and not r['dropped'];records.append(dict(alias_guard=held,status='PASS'))
 for ty in [9,11]:
  args=dict(initial_dual=W[1],type_overrides={W[0]:9,W[2]:ty})
  assert equivalent(execute(native,W[0],0,(W[2],ty),**args),execute(old,W[0],0,(W[2],ty),**args))
  records.append(dict(occupied_dual_fallback=ty,status='PASS'))
 r=execute(native,W[0],W[1],(0,9));assert r['primary']==W[0] and r['secondary']==W[1]
 # Execute ORIGINAL fire() with two mocked triggerPulls; each gets same delta,
 # different weapon pointer and exactly one call. No projectile simulation.
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x8ec000,0x1000);u.mem_map(S,0x10000);u.mem_map(STACK,0x11000);u.mem_map(STOP,0x1000)
 u.mem_write(0x8ec46c,native[0x8ec46c:0x8ec46c+116]);assert native[0x8ec46c:0x8ec46c+116]==old[0x8ec46c:0x8ec46c+116]
 for a,v in [(S+0x1c8,W[0]),(S+0x1d8,W[1]),(W[0],WV),(W[1],WV),(WV+0x4f8,STUB)]:u.mem_write(a,struct.pack('<Q',v))
 u.mem_write(STUB,bytes.fromhex('c0035fd6'));calls=[]
 def hook(uc,a,size,data):
  if a==STUB:calls.append((uc.reg_read(UC_ARM64_REG_X0),uc.reg_read(UC_ARM64_REG_S0)))
 u.hook_add(UC_HOOK_CODE,hook);u.reg_write(UC_ARM64_REG_X0,S);u.reg_write(UC_ARM64_REG_S0,0x3c888889);u.reg_write(UC_ARM64_REG_X30,STOP);u.reg_write(UC_ARM64_REG_SP,SP)
 u.emu_start(0x8ec46c,STOP,count=200);assert calls==[(W[0],0x3c888889),(W[1],0x3c888889)]
 result=dict(status='PASS',scope='ARM64 pickup/ownership fixtures and original dual fire dispatch; rendering/projectiles/Android not tested',cases=len(records)+2,records=records,fire_callbacks=calls,native_patch=manifest)
 (ROOT/'reports/dual-wield-evidence/arm64-tests.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',result['cases'],'ARM64 cases; original fire dispatch called each held instance once')
if __name__=='__main__':main()
