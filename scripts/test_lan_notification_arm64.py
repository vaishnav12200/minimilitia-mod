#!/usr/bin/env python3
"""Execute original/final ARM64 WA guard, host subtraction, and local getters.
This is an instruction fixture, not LAN reproduction or a gameplay validation.
"""
import hashlib
import json
from pathlib import Path
import struct
import zipfile
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2, UC_ARM64_REG_X30, UC_ARM64_REG_SP, UC_ARM64_REG_PC, UC_ARM64_REG_TPIDR_EL0

ROOT = Path(__file__).resolve().parents[1]
W, CTRL, GLOBAL, VT, PEER = 0x2001000, 0x2002000, 0x2003000, 0x2004000, 0x2005000
STOP, CAP_CLIP, CAP_AMMO, STACK = 0x2000000, 0x2000800, 0x2000804, 0x2020000
BAD, GOOD, WRONG_OWNER = 0x843100, 0x843a90, 0x844310


def fixture(data):
    u = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    u.mem_map(0x400000, 0x1100000)
    u.mem_write(0x400000, data[0x400000:0x12f13c8])
    u.mem_map(0x2000000, 0x40000)
    u.reg_write(UC_ARM64_REG_TPIDR_EL0, 0x2006000)
    u.mem_write(CAP_CLIP, bytes.fromhex('c0035fd6c0035fd6'))
    u.mem_write(W, struct.pack('<Q', VT))
    u.mem_write(0x13bec80, struct.pack('<Q', GLOBAL))
    u.mem_write(GLOBAL, struct.pack('<Q', CTRL))
    u.mem_write(CTRL+0x1c8, struct.pack('<Q', W))
    u.mem_write(VT+0x590, struct.pack('<Q', CAP_CLIP))
    u.mem_write(VT+0x588, struct.pack('<Q', CAP_AMMO))
    def hook(uc, address, size, user):
        if address in [STOP, BAD, GOOD, WRONG_OWNER]:
            uc.emu_stop()
        elif address in [CAP_CLIP, CAP_AMMO]:
            uc.reg_write(UC_ARM64_REG_X0, 7 if address == CAP_CLIP else 29)
    u.hook_add(UC_HOOK_CODE, hook)
    return u


def call(u, address, x0=W, x1=0, x2=0):
    u.reg_write(UC_ARM64_REG_SP, STACK)
    for reg, value in [(UC_ARM64_REG_X0,x0), (UC_ARM64_REG_X1,x1),
                       (UC_ARM64_REG_X2,x2), (UC_ARM64_REG_X30,STOP)]:
        u.reg_write(reg, value)
    u.emu_start(address, STOP+4, count=2000)
    assert u.reg_read(UC_ARM64_REG_PC) == STOP
    return u.reg_read(UC_ARM64_REG_X0)


def guard(u, clip, stid=0, soid=0, owner=1):
    u.mem_write(W, struct.pack('<i', 10))
    u.mem_write(W+0x3c, struct.pack('<i', owner))
    u.mem_write(PEER+0x90, b'\x01')
    u.mem_write(W+0x2a, struct.pack('<h', clip))
    u.mem_write(W+0x64, struct.pack('<hh', stid, soid))
    u.mem_write(STACK+0xe40, struct.pack('<Q', W))
    u.mem_write(STACK+0xe98, struct.pack('<Q', PEER))
    u.mem_write(STACK+0xe8c, struct.pack('<h', 10))
    u.mem_write(STACK+0xe60, b'\x02')
    u.reg_write(UC_ARM64_REG_SP, STACK)
    u.emu_start(0x84309c, STOP+4, count=100)
    pc = u.reg_read(UC_ARM64_REG_PC)
    assert pc in [BAD, GOOD, WRONG_OWNER]
    return pc


def main():
    original = (ROOT/'native-analysis/backup/libcocos2dcpp.so').read_bytes()
    with zipfile.ZipFile(ROOT/'builds/universal_dual_wield_final/MiniMilitiaClassic-Universal-Dual-v1.0.0.apk') as z:
        modified = z.read('lib/arm64-v8a/libcocos2dcpp.so')
    assert hashlib.sha256(original).hexdigest() == '2ee486729d9fb12599c6b56070c935b7a24757463191ce725a28592aef8df401'
    assert hashlib.sha256(modified).hexdigest() == 'e57f7598839ff65dd6e71e354fd2fc02ab65f414be0a1c23f2aac4a1727c1cce'
    results = []
    for label, data in [('original',original),('final',modified)]:
        u = fixture(data)
        for clip, stid, soid, owner, expected in [(1,0,0,1,GOOD), (0,0,0,1,GOOD),
                (-1,0,0,1,BAD), (1,2,1,1,BAD), (1,1,2,1,GOOD), (-1,2,1,1,BAD),
                (-1,0,0,2,WRONG_OWNER)]:
            actual = guard(u, clip, stid, soid, owner)
            assert actual == expected
            results.append(dict(build=label, test='actual drop guard', clip=clip, stid=stid,
                                soid=soid, owner=owner, destination=hex(actual)))
        u.mem_write(W+0x2a, struct.pack('<h',7))
        call(u, 0x84b164, x0=CTRL, x1=W, x2=8)
        clip = struct.unpack('<h',u.mem_read(W+0x2a,2))[0]
        assert clip == -1 and guard(u,clip) == BAD
        results.append(dict(build=label, test='actual host reduceMagazine 7 minus 8',clip=clip,
                            drop_guard='WA branch'))
        u = fixture(data)
        u.mem_write(W+0x360, struct.pack('<hh',5,0))
        clip = call(u, 0x947954)
        ammo = call(u, 0x947a20)
        assert (clip,ammo) == ((0,5) if label == 'original' else (7,29))
        fields = struct.unpack('<hh',u.mem_read(W+0x360,4))
        assert fields == ((5,0) if label == 'original' else (29,7))
        results.append(dict(build=label,test='actual local ammo getters',clip=clip,reserve=ammo,
                            stored_reserve=fields[0],stored_clip=fields[1]))
    output = ROOT/'reports/lan-notification-evidence/arm64-fixture-results.json'
    output.write_text(json.dumps(dict(status='PASS',records=results,
        scope='Real ARM64 instruction fixtures; capacities/ownership are fixtures. No LAN match reproduced.'),indent=2)+'\n')
    print(f'PASS: {len(results)} ARM64 records; original/final WA guard agrees, host clip can underflow, final local getters refill')
    print('This does not establish the runtime cause on the two phones or verify a fix.')


if __name__ == '__main__':
    main()
