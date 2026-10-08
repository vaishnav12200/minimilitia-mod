#!/usr/bin/env python3
"""Execute real HUD visibility/reset/layout instructions, with Cocos calls modelled."""
import struct
from dual_wield_arm64_fixture import *
HUD=S+0x8000;NV=S+0x9000;AUX=S+0xa000
NODE={0x218:S+0xb000,0x250:S+0xb200,0x1a8:S+0xb400,0x160:S+0xb600,0x168:S+0xb800}

def execute_ui(native,primary=0,secondary=0,dual_slot=0,incoming=W[2],types=None,enabled=True,dual_only=False,dual_capable=False,scale=1.0,separate=False):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x400000,0x1100000);u.mem_map(S,0x10000);u.mem_map(STACK,0x11000);u.mem_map(STOP,0x1000)
 for va,size in [(0x669b3c,1960),(0x66d7cc,388)]:u.mem_write(va,native[va:va+size])
 def q(a,v):u.mem_write(a,struct.pack('<Q',v))
 def rq(a):return struct.unpack('<Q',u.mem_read(a,8))[0]
 def point(a,x,y):u.mem_write(a,struct.pack('<ff',x,y))
 def rp(a):return struct.unpack('<ff',u.mem_read(a,8))
 def ret(v):u.reg_write(UC_ARM64_REG_X0,v)
 u.reg_write(UC_ARM64_REG_TPIDR_EL0,S+0xf000);q(S+0xf028,0xabcdef123456)
 q(0x13bec80,AUX);q(AUX,S);q(0x13c1140,AUX+0x10);q(0x13c15c0,AUX+0x10);point(AUX+0x10,scale,0)
 u.mem_write(0x1085f40,native[0x1085f40:0x1085f40+4]);u.mem_write(0x1081720,native[0x1081720:0x1081720+4])
 q(S,SV);q(S+0x1c8,primary);q(S+0x1d0,secondary);q(S+0x1d8,dual_slot)
 for w in W:q(w,WV)
 types=types or {W[0]:9,W[1]:9,W[2]:9}
 visible={n:False for n in NODE.values()};positions={n:(0.0,0.0) for n in NODE.values()};events=[];callbacks={}
 def stub(name,handler,va=None):
  va=va or STUB+len(callbacks)*16;callbacks[va]=(name,handler);u.mem_write(va,bytes.fromhex('c0035fd6'));return va
 def setpos():
  n=u.reg_read(UC_ARM64_REG_X0);positions[n]=rp(u.reg_read(UC_ARM64_REG_X1));point(n+0x100,*positions[n])
 def setvisible():visible[u.reg_read(UC_ARM64_REG_X0)]=bool(u.reg_read(UC_ARM64_REG_W1)&1)
 for off,name,handler in [(0x98,'setPosition',setpos),(0xa0,'getPosition',lambda:ret(u.reg_read(UC_ARM64_REG_X0)+0x100)),(0x120,'setVisible',setvisible),(0x128,'isVisible',lambda:ret(visible[u.reg_read(UC_ARM64_REG_X0)])),(0x410,'setString',lambda:None)]:q(NV+off,stub(name,handler))
 for off,n in NODE.items():q(HUD+off,n);q(n,NV);point(n+0x100,0,0)
 point(HUD+0x300,0,0);point(HUD+0x308,300,200);point(HUD+0x320,500 if separate else 300,200)
 u.mem_write(HUD+0x393,bytes([enabled]))
 for off,name,handler in [(0x3f0,'primary',lambda:ret(rq(S+0x1c8))),(0x3f8,'secondary',lambda:ret(rq(S+0x1d0))),(0x400,'dual',lambda:ret(rq(S+0x1d8)))]:q(SV+off,stub(name,handler))
 for off,name,handler in [(0x520,'type',lambda:ret(types[u.reg_read(UC_ARM64_REG_X0)])),(0x600,'dualOnly',lambda:ret(dual_only)),(0x5f8,'dualCapable',lambda:ret(dual_capable)),(0x608,'primaryOnly',lambda:ret(False)),(0x530,'weaponName',lambda:u.mem_write(u.reg_read(UC_ARM64_REG_X8),bytes(24)))]:q(WV+off,stub(name,handler))
 # Run actual hidePickUpWeapon through its original PLT call-site.
 from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
 u.mem_write(0x4e0110,bytes(Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN).asm('b 0x66d7cc',addr=0x4e0110)[0]))
 def constructor():point(u.reg_read(UC_ARM64_REG_X0),struct.unpack('<f',struct.pack('<I',u.reg_read(UC_ARM64_REG_S0)))[0],struct.unpack('<f',struct.pack('<I',u.reg_read(UC_ARM64_REG_S1)))[0])
 def addpoints():
  a=rp(u.reg_read(UC_ARM64_REG_X0));b=rp(u.reg_read(UC_ARM64_REG_X1));point(u.reg_read(UC_ARM64_REG_X8),a[0]+b[0],a[1]+b[1])
 stub('CCPoint_ctor',constructor,0x4c7c60);stub('point_add',addpoints,0x667924);stub('ammoType',lambda:ret(types[u.reg_read(UC_ARM64_REG_X0)]),0x4fd3b0)
 def hook(uc,va,size,user):
  if va in callbacks:
   name,call=callbacks[va];events.append(name);call()
 u.hook_add(UC_HOOK_CODE,hook);u.reg_write(UC_ARM64_REG_X0,HUD);u.reg_write(UC_ARM64_REG_X1,incoming);u.reg_write(UC_ARM64_REG_X30,STOP);u.reg_write(UC_ARM64_REG_SP,SP);u.reg_write(UC_ARM64_REG_X29,0x1234);u.reg_write(UC_ARM64_REG_X28,0x5678)
 u.emu_start(0x669b3c,STOP,count=1500)
 assert u.reg_read(UC_ARM64_REG_PC)==STOP and u.reg_read(UC_ARM64_REG_SP)==SP and u.reg_read(UC_ARM64_REG_X29)==0x1234 and u.reg_read(UC_ARM64_REG_X28)==0x5678
 initial=dict(swap=visible[NODE[0x218]],dual=visible[NODE[0x250]],swap_position=positions[NODE[0x218]],dual_position=positions[NODE[0x250]])
 # Invoke actual end-of-proximity reset and assert controls disappear.
 u.reg_write(UC_ARM64_REG_X0,HUD);u.reg_write(UC_ARM64_REG_X30,STOP);u.emu_start(0x66d7cc,STOP,count=500)
 assert not visible[NODE[0x218]] and not visible[NODE[0x250]]
 return initial
