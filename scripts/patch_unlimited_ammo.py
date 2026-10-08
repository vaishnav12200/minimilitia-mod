#!/usr/bin/env python3
"""
Isolated Native Patch: Unlimited Ammunition
Target: Weapon::subAmmo(int)
ELF File Offset: 0x009482e0
Patch: Replace entry with RET (0xC0035FD6)
"""

import os
import sys
import shutil

SO_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/decoded/lib/arm64-v8a/libcocos2dcpp.so"
SO_NATIVE_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/libcocos2dcpp.so"
BACKUP_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/backup/libcocos2dcpp.so"

OFFSET = 0x009482e0
PATCH_BYTES = bytes.fromhex("c0035fd6") # ret

def apply_patch():
    print(f"[*] Applying Unlimited Ammo patch at ELF offset 0x{OFFSET:08x}...")
    
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
