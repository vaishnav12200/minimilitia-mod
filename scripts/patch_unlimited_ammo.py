#!/usr/bin/env python3
"""
Isolated Native Patch: Unlimited Ammunition
Target: Weapon::subAmmo(int)
ELF File Offset: 0x009482e0
Patch: Replace entry instruction with RET (0xC0035FD6)
Includes original-bytes validation before modification.
"""

import os
import sys
import shutil

SO_NATIVE_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/libcocos2dcpp.so"
SPLIT_APK_DIR = "/home/vaishnavkm/Projects/MiniMilitiaMod/builds/splits"
BACKUP_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/backup/libcocos2dcpp.so"

OFFSET = 0x009482e0
EXPECTED_ORIGINAL_BYTES = bytes.fromhex("ff4301d1fd7b04a9") # sub sp, sp, #0x50; stp x29, x30, [sp, #0x40]
PATCH_BYTES = bytes.fromhex("c0035fd6") # ret

def apply_patch(target_so_path=SO_NATIVE_PATH):
    print(f"[*] Validating and applying Unlimited Ammo patch to {target_so_path}...")
    
    if not os.path.exists(target_so_path):
        print(f"[!] Error: Target binary not found at {target_so_path}")
        sys.exit(1)
        
    with open(target_so_path, "r+b") as f:
        f.seek(OFFSET)
        current_bytes = f.read(len(EXPECTED_ORIGINAL_BYTES))
        
        if current_bytes[:len(PATCH_BYTES)] == PATCH_BYTES:
            print(f"[=] Target at 0x{OFFSET:08x} is ALREADY patched with RET. Skipping.")
            return True
            
        if current_bytes != EXPECTED_ORIGINAL_BYTES:
            print(f"[!] ERROR: Original bytes mismatch at 0x{OFFSET:08x}!")
            print(f"    Found:    {current_bytes.hex()}")
            print(f"    Expected: {EXPECTED_ORIGINAL_BYTES.hex()}")
            sys.exit(1)
            
        f.seek(OFFSET)
        f.write(PATCH_BYTES)
        print(f"[+] Successfully validated original bytes and applied RET patch at 0x{OFFSET:08x}")
        return True

if __name__ == "__main__":
    apply_patch()
