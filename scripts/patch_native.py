#!/usr/bin/env python3
"""
Native Library Analysis & Patching Script for Mini Militia Classic (ARM64 v8-A)

Targets:
1. Unlimited Ammunition: Weapon::subAmmo(int) @ ELF Offset 0x009482e0
   - Original: Substracts ammo from clip and reserve ammo
   - Patch: Replace entry with RET (0xd65f03c0) or NOP ammo decrements
2. Unlimited Jetpack: SoldierLocalController::setPower(float) @ ELF Offset 0x008e68c4
   - Original: Writes float power to offset +0x278
   - Patch: Prevent fuel depletion by bypassing power decrement in updateStep or forcing max power in getPower
"""

import sys
import os
import struct
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

SO_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/libcocos2dcpp.so"
BACKUP_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/backup/libcocos2dcpp.so"

TARGETS = {
    "Weapon::subAmmo": 0x009482e0,
    "Weapon::setAmmo": 0x009481e0,
    "Weapon::setClip": 0x00948104,
    "SoldierLocalController::setPower": 0x008e68c4,
    "SoldierLocalController::getPower": 0x008e68e4,
    "SoldierLocalController::hasPower": 0x008ec7b8,
    "SoldierLocalController::addWeapon": 0x008e6934,
    "ClientRoom::validateLoadout": 0x009596ac,
}

def inspect_functions():
    with open(SO_PATH, "rb") as f:
        data = f.read()
    
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    print("=== Function Disassembly Inspection ===")
    
    for name, offset in TARGETS.items():
        print(f"\n--- {name} @ ELF 0x{offset:08x} ---")
        code = data[offset:offset+32]
        for insn in md.disasm(code, offset):
            print(f"  0x{insn.address:08x}: {insn.bytes.hex()} \t {insn.mnemonic} {insn.op_str}")

if __name__ == "__main__":
    inspect_functions()
