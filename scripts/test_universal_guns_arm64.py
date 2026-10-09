#!/usr/bin/env python3
"""Real ARM64 policy/HUD/ammo/fire dispatcher; Cocos/projectiles modelled."""
import json,struct,zipfile
from itertools import product
from patch_universal_guns import patch,working_native,ROOT,GUNS,FIRE_HELPER
from dual_wield_arm64_fixture import *
from dual_wield_ui_arm64_fixture import execute_ui

def equivalent(a,b):
 for r in [a,b]:r['events']=[n for n in r['events'] if n not in ['get_type','dual_only']]
 return a==b

def execute_fire(native,pt,it,slots=(True,True)):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x400000,0x1100000);u.mem_map(S,0x10000);u.mem_map(STACK,0x11000);u.mem_map(STOP,0x1000)
 def q(a,v):u.mem_write(a,struct.pack('<Q',v))
 def short(a,v):u.mem_write(a,struct.pack('<h',v))
 def readshort(a):return struct.unpack('<h',u.mem_read(a,2))[0]
 u.mem_write(0x8ec46c,native[0x8ec46c:0x8ec46c+116]);u.mem_write(FIRE_HELPER,native[FIRE_HELPER:FIRE_HELPER+256]);u.mem_write(0x947954,native[0x947954:0x947954+204]);u.mem_write(0x947a20,native[0x947a20:0x947a20+204])
 q(S,SV);q(S+0x1c8,W[0] if slots[0] else 0);q(S+0x1d0,0);q(S+0x1d8,W[1] if slots[1] else 0);q(0x13bec80,S+0x7000);q(S+0x7000,S)
 for w in W[:2]:q(w,WV);short(w+0x362,0);short(w+0x360,0)
 caps={W[0]:(3+pt%7,70+pt),W[1]:(3+it%7,70+it)};calls=[]
 # Capacities are modelled; the actual existing getters perform field refill.
 callbacks={STUB:lambda:u.reg_write(UC_ARM64_REG_W0,caps[u.reg_read(UC_ARM64_REG_X0)][0]),STUB+16:lambda:u.reg_write(UC_ARM64_REG_W0,caps[u.reg_read(UC_ARM64_REG_X0)][1])}
 def trigger():
  w=u.reg_read(UC_ARM64_REG_X0);assert (readshort(w+0x362),readshort(w+0x360))==caps[w]
  assert u.reg_read(UC_ARM64_REG_S0)==0x3c888889
  calls.append(w);short(w+0x362,caps[w][0]-1)
 callbacks[STUB+32]=trigger
 for a in callbacks:u.mem_write(a,bytes.fromhex('c0035fd6'))
 for off,a in [(0x590,STUB),(0x588,STUB+16),(0x4f8,STUB+32)]:q(WV+off,a)
 def hook(uc,a,size,data):
  if a in callbacks:callbacks[a]()
 u.hook_add(UC_HOOK_CODE,hook)
 for frame in range(2):
  u.reg_write(UC_ARM64_REG_X0,S);u.reg_write(UC_ARM64_REG_S0,0x3c888889);u.reg_write(UC_ARM64_REG_X30,STOP);u.reg_write(UC_ARM64_REG_SP,SP);u.reg_write(UC_ARM64_REG_X29,0x1234);u.reg_write(UC_ARM64_REG_X19,0x5678)
  u.emu_start(0x8ec46c,STOP,count=1000)
  assert u.reg_read(UC_ARM64_REG_PC)==STOP and u.reg_read(UC_ARM64_REG_SP)==SP and u.reg_read(UC_ARM64_REG_X29)==0x1234 and u.reg_read(UC_ARM64_REG_X19)==0x5678
 expected=[w for w,active in zip(W[:2],slots) if active]*2;assert calls==expected
 return dict(primary_type=pt,dual_type=it,slots=slots,calls=calls)

def main():
 native,m=patch(working_native());records=[]
 with zipfile.ZipFile(ROOT/'builds/duplicate_weapon_fixed_splits/split_config.arm64_v8a.apk') as z:carried=z.read('lib/arm64-v8a/libcocos2dcpp.so')
 # Complete factory domain: includes every ordered gun pair and nonguns.
 for pt,it in product(range(40),repeat=2):
  allowed=pt in GUNS and it in GUNS;types={W[0]:pt,W[1]:pt,W[2]:it}
  r=execute(native,W[0],0,(W[2],it),pickup_dual=True,type_overrides=types)
  assert (r['primary'],r['secondary'],r['dual'])==(W[0],0,W[2] if allowed else 0) and not r['dropped'],r
  h=execute_ui(native,primary=W[0],types=types)
  assert h['swap'] and h['dual']==allowed,h
  records.append(dict(test='pickup+HUD factory matrix',pt=pt,it=it,allowed=allowed,status='PASS'))
 for pt,it in product(GUNS,repeat=2):
  types={W[0]:pt,W[1]:pt,W[2]:it}
  for s in [0,W[1]]:
   args=dict(type_overrides=types,stock_switch=True)
   assert equivalent(execute(native,W[0],s,(W[2],it),**args),execute(carried,W[0],s,(W[2],it),**args))
   records.append(dict(test='normal Swap preserved',pt=pt,it=it,secondary=s,status='PASS'))
  r=execute(native,W[0],0,(W[2],it),pickup_dual=True,type_overrides=types,initial_dual=W[1]);assert r['dual']==W[1] and r['primary']==W[0] and not r['dropped']
  h=execute_ui(native,primary=W[0],dual_slot=W[1],types=types);assert h['swap'] and not h['dual']
  records.append(dict(test='occupied dual guard',pt=pt,it=it,status='PASS'))
  records.append(dict(test='actual refill + one fire per live instance',result=execute_fire(native,pt,it),status='PASS'))
 for pt,it in [(0xffffffff,9),(9,0xffffffff),(64,9),(9,64),(63,9),(9,63),(0x7fffffff,9)]:
  r=execute(native,W[0],0,(W[2],it),pickup_dual=True,type_overrides={W[0]:pt,W[2]:it});assert r['dual']==0;records.append(dict(test='mask unsigned range bounds',pt=pt,it=it,status='PASS'))
 for held,explicit in product(W,[False,True]):
  r=execute(native,W[0],W[1],(held,9),pickup_dual=explicit,initial_dual=W[2],type_overrides={w:9 for w in W});assert (r['primary'],r['secondary'],r['dual'])==tuple(W) and not r['dropped'];records.append(dict(test='pointer alias guard',status='PASS'))
 for slot in [(False,False),(True,False),(False,True)]:records.append(dict(test='fire null slot guards',result=execute_fire(native,9,10,slot),status='PASS'))
 for scale,enabled in product([0.5,1,1.5],[False,True]):
  r=execute_ui(native,primary=W[0],types={W[0]:10,W[2]:11},scale=scale,enabled=enabled);assert r['swap']==enabled and r['dual']==enabled
  assert r['swap_position']==(300+38*scale,200) and r['dual_position']==(300-38*scale,200);records.append(dict(test='mixed layout/enable/hide',scale=scale,status='PASS'))
 for active in [0,W[0],W[1],W[2]]:
  r=execute_ui(native,primary=W[0],secondary=W[1],dual_slot=W[2],incoming=active);assert not r['swap'] and not r['dual'];records.append(dict(test='stale/null UI',status='PASS'))
 for enabled,cap in product([False,True],[False,True]):
  h=execute_ui(native,primary=W[0],dual_only=True,dual_capable=cap,enabled=enabled);assert not h['swap'] and h['dual']==bool(enabled and cap);records.append(dict(test='utility UI preserved',status='PASS'))
 out=dict(status='PASS',cases=len(records),factory_domain_cases=1600,ordered_gun_pairs=len(GUNS)**2,native_sha256=m['output_sha256'],scope='Real ARM64 UI/inventory/ammo getters/fire dispatcher; Cocos virtual callbacks and projectile engine modelled, not physical rendering/LAN',records=records)
 (ROOT/'reports/universal-guns-evidence/arm64-tests.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS',len(records),'cases;',len(GUNS)**2,'same/mixed gun pairs; actual getters refresh both instances before one fire each')
if __name__=='__main__':main()
