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

def execute(native,primary,secondary,incoming,dual=False,pickup_dual=False,primary_only=False,dual_only=False,type_overrides=None,initial_dual=0,stock_switch=False):
 u=Uc(UC_ARCH_ARM64,UC_MODE_ARM);u.mem_map(0x400000,0x1000000);u.mem_map(S,0x10000);u.mem_map(STACK,0x11000);u.mem_map(STOP,0x1000)
 u.mem_write(FUNCTION,native[FUNCTION:FUNCTION+SIZE]);u.mem_write(0x13bf4d0,struct.pack('<Q',S+0x7000))
 def writeq(addr,value):u.mem_write(addr,struct.pack('<Q',value))
 def readq(addr):return struct.unpack('<Q',u.mem_read(addr,8))[0]
 def setslot(off,value):writeq(S+off,value)
 writeq(S,SV);setslot(0x1c8,primary or 0);setslot(0x1d0,secondary or 0);setslot(0x1d8,initial_dual)
 types={W[0]:11,W[1]:17,W[2]:incoming[1]};incoming_ptr=incoming[0]
 if type_overrides:types.update(type_overrides)
 callbacks={};events=[];retain={p:1 for p in (primary,secondary,initial_dual) if p};dropped=[]
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
  if stock_switch and not (dual or dual_only):remove(0x1d8)()
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

