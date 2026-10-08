#!/usr/bin/env python3
"""
Isolated Native Patch: Unlimited Jetpack Fuel
Target: SoldierLocalController::getPower()
ELF File Offset: 0x008e68e4 (SoldierLocalController::getPower Entry)
Patch: fmov s0, #1.0 (0x1E2E1000) ; ret (0xC0035FD6)
Includes original-bytes validation before modification.
"""

import os
import sys
import shutil

SO_NATIVE_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/libcocos2dcpp.so"
BACKUP_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/backup/libcocos2dcpp.so"

OFFSET = 0x008e68e4
EXPECTED_ORIGINAL_BYTES = bytes.fromhex("ff4300d1e00700f9") # sub sp, sp, #0x10; str x0, [sp, #8]
PATCH_BYTES = bytes.fromhex("00102e1ec0035fd6") # fmov s0, #1.0 ; ret

def apply_patch(target_so_path=SO_NATIVE_PATH):
    print(f"[*] Validating and applying Unlimited Jetpack Fuel patch to {target_so_path}...")
    
    if not os.path.exists(target_so_path):
        print(f"[!] Error: Target binary not found at {target_so_path}")
        sys.exit(1)
        
    with open(target_so_path, "r+b") as f:
        f.seek(OFFSET)
        current_bytes = f.read(len(EXPECTED_ORIGINAL_BYTES))
        
        if current_bytes == PATCH_BYTES:
            print(f"[=] Target at 0x{OFFSET:08x} is ALREADY patched with fmov s0, #1.0; ret. Skipping.")
            return True
            
        if current_bytes != EXPECTED_ORIGINAL_BYTES:
            print(f"[!] ERROR: Original bytes mismatch at 0x{OFFSET:08x}!")
            print(f"    Found:    {current_bytes.hex()}")
            print(f"    Expected: {EXPECTED_ORIGINAL_BYTES.hex()}")
            sys.exit(1)
            
        f.seek(OFFSET)
        f.write(PATCH_BYTES)
        print(f"[+] Successfully validated original bytes and applied Jetpack patch at 0x{OFFSET:08x}")
        return True

if __name__ == "__main__":
    apply_patch()
