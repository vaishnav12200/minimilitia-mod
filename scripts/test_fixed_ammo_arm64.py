#!/usr/bin/env python3
"""Execute patched getters and original reload completion in ARM64 Unicorn.
Synthetic memory/capacity/callback fixtures: does not certify Android gameplay.
Install unicorn separately; dependencies are not downloaded by this script.
"""
import json, struct
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import *
from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
from patch_fixed_gameplay import ROOT, GETTERS, GOT, combined, patch
KS=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN)
def asm(source,address):return bytes(KS.asm(source,addr=address)[0])
W=0x2000000; S=0x2001000; V=0x2002000; GLOBAL=0x2003000; STUB=0x2004000; CB=0x2005000
STACK=0x3000000; SP=STACK+0x10000; STOP=0x4000000
u=Uc(UC_ARCH_ARM64,UC_MODE_ARM)
u.mem_map(0x400000,0x1000000)
u.mem_map(W,0x10000);u.mem_map(STACK,0x11000);u.mem_map(STOP,0x1000)
data,manifest=patch(combined())
for _,va,_,_ in GETTERS:u.mem_write(va,data[va:va+204])
u.mem_write(0x947f68,data[0x947f68:0x948104])
u.mem_write(GOT,struct.pack('<Q',GLOBAL));u.mem_write(W,struct.pack('<Q',V))
u.mem_write(W+0x2c8,struct.pack('<Q',CB));u.mem_write(CB,struct.pack('<Q',CB+0x100))
u.mem_write(CB+0x120,struct.pack('<Q',STUB+0x300))
u.mem_write(STUB+0x300,asm('ret',STUB+0x300))
# Replace external PLT imports in emulator only; original reload body stays exact.
for plt,dest in ((0x4d2fa0,0x947954),(0x4c64c0,0x947a20)):
 u.mem_write(plt,asm(f'b {dest}',plt))
for plt,field in ((0x4f3100,0x362),(0x4f8dd0,0x360)):
 u.mem_write(plt,asm(f'strh w1, [x0, #{field}]; ret',plt))
callbacks=[]
def hook(uc,address,size,data):
 if address==STUB+0x300:callbacks.append((uc.reg_read(UC_ARM64_REG_X0),uc.reg_read(UC_ARM64_REG_X1)))
u.hook_add(UC_HOOK_CODE,hook)
def hwrite(addr,value):u.mem_write(addr,struct.pack('<H',value&0xffff))
def hread(addr):return struct.unpack('<h',u.mem_read(addr,2))[0]
def configure(slot=0,local=True,capacity=30,clip=3,reserve=7):
 u.mem_write(S,bytes(0x1000));u.mem_write(GLOBAL,struct.pack('<Q',S if local else 0))
 if slot is not None:u.mem_write(S+0x1c8+8*slot,struct.pack('<Q',W))
 for virtual,stub,value in ((0x590,STUB,capacity),(0x588,STUB+0x100,capacity*3 if capacity>0 else capacity)):
  u.mem_write(V+virtual,struct.pack('<Q',stub))
  # Clobber volatile scratch to check saved this pointer survives virtual calls.
  u.mem_write(stub,asm(f'mov w0, #{value & 0xffff}; mov x8, #0; mov x9, #0; ret',stub))
 u.ctl_flush_tb()
 hwrite(W+0x362,clip);hwrite(W+0x360,reserve);u.mem_write(W+0x285,b'\x01')
 u.mem_write(W+0x190,struct.pack('<I',0x42));callbacks.clear()
def run(va):
 u.reg_write(UC_ARM64_REG_X0,W);u.reg_write(UC_ARM64_REG_X19,0x12345678)
 u.reg_write(UC_ARM64_REG_X29,0x87654321);u.reg_write(UC_ARM64_REG_X30,STOP);u.reg_write(UC_ARM64_REG_SP,SP)
 u.emu_start(va,STOP,count=2000)
 assert u.reg_read(UC_ARM64_REG_PC)==STOP
 assert u.reg_read(UC_ARM64_REG_SP)==SP and u.reg_read(UC_ARM64_REG_X19)==0x12345678
 assert u.reg_read(UC_ARM64_REG_X29)==0x87654321 and u.reg_read(UC_ARM64_REG_X30)==STOP
 return u.reg_read(UC_ARM64_REG_W0)
records=[]
for slot in range(3):
 for cap in (1,2,6,30,100,32767):
  for clip,reserve in ((0,0),(1,1),(-5,-4),(cap,cap),(max(0,cap-1),5)):
   configure(slot,capacity=cap,clip=clip,reserve=reserve)
   actual=run(0x947954)
   assert actual==cap and hread(W+0x362)==cap, (slot,cap,clip,reserve,actual,hread(W+0x362))
   # Reserve fixture uses signed16; cap*3 overflow cases must fall back stock.
   signed_capacity=((cap*3+32768)%65536)-32768
   expected=signed_capacity if signed_capacity>0 else max(reserve,0)
   assert run(0x947a20)==expected
   assert u.mem_read(W+0x285,1)==b'\x01'
   if cap*3<=32767:
    run(0x947f68)
    assert hread(W+0x362)==cap and hread(W+0x360)==cap*3
    assert u.mem_read(W+0x285,1)==b'\x00'
    assert struct.unpack('<I',u.mem_read(W+0x190,4))[0]==0
    assert callbacks==[(CB,W)]
   records.append(dict(slot=slot,capacity=cap,clip=clip,reserve=reserve,status='PASS'))
# Nonlocal/dropped weapon and null local pointer retain stock clamped reads/fields.
for local,slot in ((False,None),(True,None)):
 for value in (-32768,-1,0,1,32767):
  configure(slot,local,clip=value,reserve=value)
  for va,field in ((0x947954,0x362),(0x947a20,0x360)):
   assert run(va)==max(value,0) and hread(W+field)==value
  records.append(dict(local=local,equipped=False,value=value,status='PASS'))
for cap in (0,-1,-32768):
 configure(capacity=cap);assert run(0x947954)==3 and run(0x947a20)==7
 records.append(dict(invalid_capacity=cap,status='PASS'))
configure(slot=None,capacity=30,clip=3,reserve=7);run(0x947f68)
assert hread(W+0x362)==10 and hread(W+0x360)==0 and len(callbacks)==1
records.append(dict(stock_reload='3+7 -> clip10,reserve0',status='PASS'))
configure(capacity=30)
for shot in range(1000):
 run(0x947954);hwrite(W+0x362,hread(W+0x362)-1)
assert run(0x947954)==30
records.append(dict(simulated_raw_decrements=1000,status='PASS'))
out=dict(status='ARM64 emulation PASS; synthetic fixtures, not device gameplay',cases=len(records),native_sha256=manifest['output_sha256'],records=records)
(ROOT/'reports/reload-fix-evidence/arm64-emulation.json').write_text(json.dumps(out,indent=2)+'\n')
print(out['status'],len(records),'scenarios')
