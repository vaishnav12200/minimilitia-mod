#!/usr/bin/env python3
"""
Isolated Native Patch: Unlimited Jetpack Fuel
Target: SoldierLocalController::getPower()
ELF File Offset: 0x008e68e4
Patch: fmov s0, #1.0 (0x1E2E1000) ; ret (0xC0035FD6)
"""

import os
import sys
import shutil

SO_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/decoded/lib/arm64-v8a/libcocos2dcpp.so"
SO_NATIVE_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/libcocos2dcpp.so"
BACKUP_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/backup/libcocos2dcpp.so"

OFFSET = 0x008e68e4
PATCH_BYTES = bytes.fromhex("00102e1ec0035fd6") # fmov s0, #1.0 ; ret

def apply_patch():
    print(f"[*] Applying Unlimited Jetpack Fuel patch at ELF offset 0x{OFFSET:08x}...")
    
    # Apply to native-analysis directory
    with open(SO_NATIVE_PATH, "r+b") as f:
        f.seek(OFFSET)
        f.write(PATCH_BYTES)
    print(f"[+] Patched {SO_NATIVE_PATH}")
    
    # Copy to decoded APK folder if present
    if os.path.exists(os.path.dirname(SO_PATH)):
        shutil.copy2(SO_NATIVE_PATH, SO_PATH)
        print(f"[+] Synced patched binary to decoded APK folder: {SO_PATH}")

if __name__ == "__main__":
    apply_patch()
