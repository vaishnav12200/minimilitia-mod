#!/usr/bin/env python3
"""Real pickup and HUD instructions; callbacks/physics/rendering are fixtures."""
import json,zipfile
from itertools import product
from patch_dual_wield_ui import patch,working_native,ROOT
from dual_wield_arm64_fixture import execute,W
from dual_wield_ui_arm64_fixture import execute_ui

def equivalent(a,b):
 for r in [a,b]:r['events']=[n for n in r['events'] if n not in ['get_type','dual_only']]
 return a==b

def main():
 old=working_native();native,m=patch(old)
 with zipfile.ZipFile(ROOT/'builds/duplicate_weapon_fixed_splits/split_config.arm64_v8a.apk') as z:carried=z.read('lib/arm64-v8a/libcocos2dcpp.so')
 records=[]
 for p,s,d in [(0,0,0),(W[0],0,0),(0,W[0],0),(W[0],W[1],0),(W[0],0,W[1])]:
  for pt,it,explicit in product([9,11],[9,11,17],[False,True]):
   types={W[0]:pt,W[1]:pt,W[2]:it};args=dict(pickup_dual=explicit,type_overrides=types,initial_dual=d,stock_switch=True)
   result=execute(native,p,s,(W[2],it),**args)
   if not explicit:assert equivalent(result,execute(carried,p,s,(W[2],it),**args)),result
   elif p and not d and pt==it==9:
    assert (result['primary'],result['secondary'],result['dual'])==(p,s,W[2]) and not result['dropped'] and result['retains'][W[2]]==1,result
   else:assert (result['primary'],result['secondary'],result['dual'])==(p,s,d) and not result['dropped'] and W[2] not in result['retains'],result
   records.append(dict(test='pickup',primary=p,secondary=s,dual=d,primary_type=pt,incoming_type=it,explicit_dual=explicit,status='PASS'))
 # Alias guards in every slot: no reacquisition, dropped owner or extra retain.
 for explicit,held in product([False,True],W):
  r=execute(native,W[0],W[1],(held,9),initial_dual=W[2],type_overrides={w:9 for w in W},pickup_dual=explicit,stock_switch=True)
  assert (r['primary'],r['secondary'],r['dual'])==tuple(W) and not r['dropped'] and all(v==1 for v in r['retains'].values());records.append(dict(test='alias',slot=held,explicit_dual=explicit,status='PASS'))
 for explicit in [False,True]:
  r=execute(native,W[0],W[1],(0,9),pickup_dual=explicit);assert (r['primary'],r['secondary'])==(W[0],W[1]);records.append(dict(test='null',explicit_dual=explicit,status='PASS'))
 # Existing dedicated dual-only utilities retain original guarded path.
 for p,s in [(0,0),(W[0],0),(W[0],W[1])]:
  args=dict(dual_only=True,pickup_dual=True)
  assert equivalent(execute(native,p,s,(W[2],11),**args),execute(carried,p,s,(W[2],11),**args));records.append(dict(test='utility',status='PASS'))
 # Actual HUD hides, eligibility, visibility and stock separation block.
 for p,d,pt,it,enabled,scale in product([0,W[0]],[0,W[1]],[9,11],[9,11],[False,True],[0.5,1.0,1.5]):
  r=execute_ui(native,primary=p,dual_slot=d,types={W[0]:pt,W[1]:pt,W[2]:it},enabled=enabled,scale=scale)
  both=bool(p and not d and pt==it==9)
  assert r['swap']==enabled and r['dual']==bool(enabled and both),r
  if both:
   assert r['swap_position']==(300+38*scale,200) and r['dual_position']==(300-38*scale,200),r
   assert r['swap_position'][0]-r['dual_position'][0]>67*scale
  records.append(dict(test='HUD',primary=p,dual=d,pt=pt,it=it,enabled=enabled,scale=scale,result=r,status='PASS'))
 for w in [0,*W]:
  r=execute_ui(native,primary=W[0],secondary=W[1],dual_slot=W[2],incoming=w);assert not r['swap'] and not r['dual'];records.append(dict(test='HUD stale/null',incoming=w,status='PASS'))
 for enabled,cap in product([False,True],[False,True]):
  r=execute_ui(native,primary=W[0],dual_only=True,dual_capable=cap,enabled=enabled);assert not r['swap'] and r['dual']==bool(enabled and cap);records.append(dict(test='utility HUD',status='PASS'))
 r=execute_ui(native,primary=W[0],separate=True);assert r['swap_position']==(300,200) and r['dual_position']==(500,200);records.append(dict(test='custom HUD positions preserved',status='PASS'))
 result=dict(status='PASS',cases=len(records),scope='Real ARM64 inventory/visibility/reset/layout instructions with mocked stock callbacks; touch hit testing, physics and rendering require physical testing',native_sha256=m['output_sha256'],records=records)
 (ROOT/'reports/dual-wield-ui-evidence/arm64-tests.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(records),'ARM64 cases, including distinct Swap/Dual routing and stock button spacing/reset')
if __name__=='__main__':main()
