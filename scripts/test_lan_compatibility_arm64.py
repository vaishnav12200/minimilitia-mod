#!/usr/bin/env python3
"""Feature isolation and finite-LAN/offline-refill instruction fixtures; no LAN PASS."""
import json
import struct
from itertools import product
from keystone import Ks,KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN
from unicorn.arm64_const import UC_ARM64_REG_S0
from build_lan_test_matrix import variants, EVIDENCE
from patch_universal_guns import GUNS
from test_lan_notification_arm64 import fixture,call,W,CTRL,GLOBAL,VT,STACK,STOP
from test_universal_guns_arm64 import execute_fire
from dual_wield_arm64_fixture import execute, W as INVENTORY_WEAPONS
from dual_wield_ui_arm64_fixture import execute_ui

MODE = 0x2007000


def short(u, address, value):
    u.mem_write(address,struct.pack('<h',value))


def h(u,address):
    return struct.unpack('<h',u.mem_read(address,2))[0]


def mode(u,value):
    u.mem_write(0x13bf448,struct.pack('<Q',MODE))
    u.mem_write(MODE,struct.pack('<i',value))


def main():
    natives,notes,manifest=variants()
    records=[]
    for tag,native in natives.items():
        u=fixture(native)
        for connection,slot,local,value in product([0,2],[0x1c8,0x1d0,0x1d8,None],[True,False],[-1,0,3]):
            mode(u,connection)
            u.mem_write(CTRL+0x1c8,bytes(24))
            u.mem_write(GLOBAL,struct.pack('<Q',CTRL if local else 0))
            if slot is not None:u.mem_write(CTRL+slot,struct.pack('<Q',W))
            short(u,W+0x360,value);short(u,W+0x362,value)
            u.mem_write(W+0x285,b'\x01');u.mem_write(W+0x298,struct.pack('<ii',15,17))
            refill=tag in ['C_ammo_getters_only','E_combined','F_lan_ammo_candidate'] and local and slot is not None
            if tag=='F_lan_ammo_candidate' and connection==2:refill=False
            clip,ammo=call(u,0x947954),call(u,0x947a20)
            assert (clip,ammo)==((7,29) if refill else (max(value,0),max(value,0)))
            assert (h(u,W+0x362),h(u,W+0x360))==((7,29) if refill else (value,value))
            assert u.mem_read(W+0x285,1)==b'\x01' and bytes(u.mem_read(W+0x298,8))==struct.pack('<ii',15,17)
            records.append(dict(build=tag,test='ammo ownership/mode/read side effects',mode=connection,slot=slot,local=local,input=value,status='PASS'))
        u=fixture(native)
        u.mem_write(CTRL+0x278,struct.pack('<f',0.25))
        call(u,0x8e68e4,x0=CTRL)
        # Original getPower reads controller +0x278; mod returns full power.
        expected=0x3f800000 if tag in ['B_jetpack_only','E_combined','F_lan_ammo_candidate'] else 0x3e800000
        assert u.reg_read(UC_ARM64_REG_S0)==expected
        records.append(dict(build=tag,test='actual fuel getter',status='PASS'))
    # Exercise the actual useRakNetLAN and setter; only imported setUseHostedServer is redirected to its original body.
    native=natives['F_lan_ammo_candidate'];u=fixture(native);mode(u,0)
    from elftools.elf.elffile import ELFFile
    import io
    ds=ELFFile(io.BytesIO(native)).get_section_by_name('.dynsym')
    target=ds.get_symbol_by_name('_ZN14NetworkManager18setUseHostedServerEb')[0]['st_value']
    ks=Ks(KS_ARCH_ARM64,KS_MODE_LITTLE_ENDIAN)
    for plt,address in [(0x4d3620,0x718608),(0x4d8da0,target)]:
        u.mem_write(plt,bytes(ks.asm(f'b {address}',addr=plt)[0]))
    call(u,0x7186bc,x0=CTRL)
    assert struct.unpack('<i',u.mem_read(MODE,4))[0]==2
    short(u,W+0x362,0);assert call(u,0x947954)==0
    mode(u,0);assert call(u,0x947954)==7
    records.append(dict(test='actual LAN setter then finite getter; mode transition to offline refills',status='PASS'))
    # Real retained reload-completion code with original external setters represented in the fixture.
    for connection in [0,2]:
        u=fixture(native);mode(u,connection)
        callback=0x2008000;callback_vt=0x2008100;stub=0x2000900
        u.mem_write(W+0x2c8,struct.pack('<Q',callback));u.mem_write(callback,struct.pack('<Q',callback_vt));u.mem_write(callback_vt+0x20,struct.pack('<Q',stub));u.mem_write(stub,bytes.fromhex('c0035fd6'))
        for plt,address in [(0x4d2fa0,0x947954),(0x4c64c0,0x947a20)]:u.mem_write(plt,bytes(ks.asm(f'b {address}',addr=plt)[0]))
        for plt,field in [(0x4f3100,0x362),(0x4f8dd0,0x360)]:u.mem_write(plt,bytes(ks.asm(f'strh w1, [x0, #{field}]; ret',addr=plt)[0]))
        short(u,W+0x362,3);short(u,W+0x360,5);u.mem_write(W+0x285,b'\x01')
        call(u,0x947f68)
        assert (h(u,W+0x362),h(u,W+0x360))==((7,29) if connection==0 else (7,1))
        assert u.mem_read(W+0x285,1)==b'\x00'
        records.append(dict(test='actual reload completion',mode=connection,status='PASS'))
    for tag,connection,finite in [('D_dual_only',2,True),('F_lan_ammo_candidate',2,True),('F_lan_ammo_candidate',0,False)]:
        native=natives[tag]
        for pt,it in product(GUNS,repeat=2):
            execute_fire(native,pt,it,connection_type=connection,finite_ammo=finite)
            types={INVENTORY_WEAPONS[0]:pt,INVENTORY_WEAPONS[2]:it}
            r=execute(native,INVENTORY_WEAPONS[0],0,(INVENTORY_WEAPONS[2],it),pickup_dual=True,type_overrides=types)
            assert r['primary']==INVENTORY_WEAPONS[0] and r['dual']==INVENTORY_WEAPONS[2]
            ui=execute_ui(native,primary=INVENTORY_WEAPONS[0],types=types)
            assert ui['swap'] and ui['dual']
            records.append(dict(build=tag,test='two-frame distinct firing and pair pickup/HUD',mode=connection,pt=pt,it=it,status='PASS'))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/'arm64-tests.json').write_text(json.dumps(dict(status='PASS',cases=len(records),
        scope='Real instructions; virtual capacities, shots, ownership and Cocos are fixtures. No device/LAN verification.',records=records),indent=2)+'\n')
    print('PASS',len(records),'instruction fixture records; physical LAN NOT TESTED')


if __name__=='__main__':main()
