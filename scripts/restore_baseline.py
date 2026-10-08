#!/usr/bin/env python3
"""
Restore baseline unmodified libcocos2dcpp.so from backup
"""

import os
import sys
import shutil

SO_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/decoded/lib/arm64-v8a/libcocos2dcpp.so"
SO_NATIVE_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/libcocos2dcpp.so"
BACKUP_PATH = "/home/vaishnavkm/Projects/MiniMilitiaMod/native-analysis/backup/libcocos2dcpp.so"

def restore():
    print("[*] Restoring original unmodified libcocos2dcpp.so from backup...")
    shutil.copy2(BACKUP_PATH, SO_NATIVE_PATH)
    print(f"[+] Restored {SO_NATIVE_PATH}")
    
    if os.path.exists(os.path.dirname(SO_PATH)):
        shutil.copy2(BACKUP_PATH, SO_PATH)
        print(f"[+] Restored {SO_PATH}")

if __name__ == "__main__":
    restore()
