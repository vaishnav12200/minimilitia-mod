#!/usr/bin/env python3
"""
Mini Militia Classic — Independent Verification Script
Verifies ELF file offsets, virtual addresses, original instruction bytes,
and planned ARM64 patch encodings.
"""

import sys
import struct
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN

SO_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/libcocos2dcpp.so"

TARGET_SYMBOLS = [
    ("_ZN6Weapon7subAmmoEi", "Ammunition Handling"),
    ("_ZN6Weapon7setAmmoEib", "Reserve Ammo Handler"),
    ("_ZN6Weapon7setClipEi", "Clip Ammo Handler"),
    ("_ZN22SoldierLocalController8setPowerEf", "Jetpack Power Setter"),
    ("_ZN22SoldierLocalController8getPowerEv", "Jetpack Power Getter"),
    ("_ZN22SoldierLocalController8hasPowerEv", "Jetpack Power Checker"),
    ("_ZN22SoldierLocalController9addWeaponEP6Weapon", "Weapon Inventory Add"),
    ("_ZN10ClientRoom15validateLoadoutE13LoadoutObjectP11ClientEntry", "Loadout Validator"),
]

def run_verification():
    print("==========================================================================")
    print("MINI MILITIA CLASSIC — NATIVE BINARY INDEPENDENT VERIFICATION")
    print("==========================================================================")
    
    with open(SO_PATH, "rb") as f:
        elf = ELFFile(f)
        data = f.read()
        
        symtab = elf.get_section_by_name('.dynsym')
        sym_dict = {}
        for sym in symtab.iter_symbols():
            if sym.name:
                sym_dict[sym.name] = sym
                
        md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
        ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)

        print("\n[1] ELF Address Mapping & Original Instruction Bytes Verification:\n")
        
        for name, desc in TARGET_SYMBOLS:
            if name in sym_dict:
                sym = sym_dict[name]
                vaddr = sym['st_value']
                size = sym['st_size']
                
                # In libcocos2dcpp.so, executable PT_LOAD starts at vaddr 0, so vaddr == file_off
                file_off = vaddr
                bytes_at_off = data[file_off:file_off+16]
                
                print(f"[*] Symbol: {name}")
                print(f"    Description: {desc}")
                print(f"    st_value (VAddr): 0x{vaddr:08x}")
                print(f"    File Offset:      0x{file_off:08x}")
                print(f"    Ghidra RAM (0x100000 base): 0x{vaddr + 0x100000:08x}")
                print(f"    Size: {size} bytes")
                print(f"    Original Bytes: {bytes_at_off.hex()}")
                print("    Disassembly (first 4 insns):")
                for insn in md.disasm(bytes_at_off, vaddr):
                    print(f"      0x{insn.address:08x}: {insn.bytes.hex()}\t{insn.mnemonic} {insn.op_str}")
                print("-" * 70)
            else:
                print(f"[!] Symbol {name} NOT FOUND in dynamic symbol table!")

        print("\n[2] Planned Patch Assembly & Disassembly Verification:\n")
        
        # Patch 1: Unlimited Ammo (Weapon::subAmmo ret)
        patch1_asm = "ret"
        patch1_bytes, _ = ks.asm(patch1_asm)
        print(f"[*] Patch 1 (Unlimited Ammo - Weapon::subAmmo entry @ 0x009482e0):")
        print(f"    Assembled: {bytes(patch1_bytes).hex()}")
        for insn in md.disasm(bytes(patch1_bytes), 0x009482e0):
            print(f"    Verified: 0x{insn.address:08x}: {insn.bytes.hex()}\t{insn.mnemonic} {insn.op_str}")
            
        # Patch 2: Unlimited Jetpack Fuel (SoldierLocalController::getPower return 1.0f)
        patch2_asm = "fmov s0, #1.0\nret"
        patch2_bytes, _ = ks.asm(patch2_asm)
        print(f"\n[*] Patch 2 (Unlimited Jetpack - SoldierLocalController::getPower entry @ 0x008e68e4):")
        print(f"    Assembled: {bytes(patch2_bytes).hex()}")
        for insn in md.disasm(bytes(patch2_bytes), 0x008e68e4):
            print(f"    Verified: 0x{insn.address:08x}: {insn.bytes.hex()}\t{insn.mnemonic} {insn.op_str}")

if __name__ == "__main__":
    run_verification()
