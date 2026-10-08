#!/usr/bin/env python3
"""
Complete Split-APK Package Build, ZipAlign, and Signing Workflow script.

Produces:
1. Unmodified Baseline Split-APK Set -> builds/baseline_splits/
2. Modded Split-APK Set (Unlimited Ammo & Jetpack) -> builds/modded_splits/
3. Individual Feature Split Sets -> builds/ammo_mod_splits/, builds/fuel_mod_splits/
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

PROJECT_DIR = Path("/home/vaishnavkm/Projects/MiniMilitiaMod")
EXTRACTED_DIR = PROJECT_DIR / "extracted-apks"
NATIVE_DIR = PROJECT_DIR / "native-analysis"
BACKUP_SO = NATIVE_DIR / "backup" / "libcocos2dcpp.so"
WORKING_SO = NATIVE_DIR / "libcocos2dcpp.so"
KEYSTORE = PROJECT_DIR / "signing" / "mmc-test.keystore"
KEY_ALIAS = "mmc-test-key"
KEY_PASS = "mmc_test_store_pw"

ZIPALIGN = "/home/vaishnavkm/Android/Sdk/build-tools/35.0.0/zipalign"
APKSIGNER = "/home/vaishnavkm/Android/Sdk/build-tools/35.0.0/apksigner"

REQUIRED_SPLITS = [
    "base.apk",
    "split_config.arm64_v8a.apk",
    "split_config.xxhdpi.apk",
    "split_config.en.apk"
]

def update_split_arm64_apk(source_apk_path, so_path, output_apk_path):
    """Replaces lib/arm64-v8a/libcocos2dcpp.so in split_config.arm64_v8a.apk cleanly."""
    temp_zip = output_apk_path.with_suffix(".tmp.apk")
    if os.path.exists(temp_zip):
        os.remove(temp_zip)
        
    with zipfile.ZipFile(source_apk_path, 'r') as jin, zipfile.ZipFile(temp_zip, 'w', compression=zipfile.ZIP_DEFLATED) as jout:
        for item in jin.infolist():
            if item.filename == "lib/arm64-v8a/libcocos2dcpp.so":
                continue # skip original so
            data = jin.read(item.filename)
            jout.writestr(item, data)
            
        with open(so_path, 'rb') as f:
            so_data = f.read()
        jout.writestr("lib/arm64-v8a/libcocos2dcpp.so", so_data)
        
    if os.path.exists(output_apk_path):
        os.remove(output_apk_path)
    os.rename(temp_zip, output_apk_path)
    print(f"[+] Updated {output_apk_path.name} with native library from {so_path.name}")

def zipalign_and_sign_split_set(input_dir, output_dir):
    """Zipaligns and signs every APK in input_dir and places aligned+signed APKs in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)
    aligned_signed_files = []
    
    print(f"\n============================================================")
    print(f"Processing Split Set in: {output_dir.name}")
    print(f"============================================================")
    
    for apk_name in REQUIRED_SPLITS:
        in_apk = input_dir / apk_name
        aligned_apk = output_dir / apk_name.replace(".apk", "-aligned.apk")
        signed_apk = output_dir / apk_name
        
        if os.path.exists(aligned_apk): os.remove(aligned_apk)
        if os.path.exists(signed_apk): os.remove(signed_apk)
        
        # 1. Zipalign
        res_align = subprocess.run([ZIPALIGN, "-p", "-f", "4", str(in_apk), str(aligned_apk)], capture_output=True, text=True)
        if res_align.returncode != 0:
            print(f"[!] Zipalign failed for {apk_name}: {res_align.stderr}")
            sys.exit(1)
            
        # 2. Sign
        res_sign = subprocess.run([
            APKSIGNER, "sign",
            "--ks", str(KEYSTORE),
            "--ks-key-alias", KEY_ALIAS,
            "--ks-pass", f"pass:{KEY_PASS}",
            "--out", str(signed_apk),
            str(aligned_apk)
        ], capture_output=True, text=True)
        
        if res_sign.returncode != 0:
            print(f"[!] Sign failed for {apk_name}: {res_sign.stderr}")
            sys.exit(1)
            
        # Remove intermediate aligned file
        if os.path.exists(aligned_apk):
            os.remove(aligned_apk)
            
        # 3. Verify signature
        res_verify = subprocess.run([APKSIGNER, "verify", str(signed_apk)], capture_output=True, text=True)
        if res_verify.returncode != 0:
            print(f"[!] Signature verification failed for {signed_apk.name}: {res_verify.stderr}")
            sys.exit(1)
            
        aligned_signed_files.append(signed_apk)
        print(f"[OK] ZipAligned, Signed & Verified: {signed_apk.name} ({os.path.getsize(signed_apk)} bytes)")
        
    return aligned_signed_files

def main():
    builds_dir = PROJECT_DIR / "builds"
    
    # 1. Baseline Split Package
    baseline_dir = builds_dir / "baseline_splits"
    baseline_temp = builds_dir / "baseline_temp"
    baseline_temp.mkdir(parents=True, exist_ok=True)
    
    for apk in REQUIRED_SPLITS:
        shutil.copy2(EXTRACTED_DIR / apk, baseline_temp / apk)
        
    zipalign_and_sign_split_set(baseline_temp, baseline_dir)
    shutil.rmtree(baseline_temp)
    
    # 2. Unlimited Ammo Split Package
    ammo_dir = builds_dir / "ammo_mod_splits"
    ammo_temp = builds_dir / "ammo_temp"
    ammo_temp.mkdir(parents=True, exist_ok=True)
    
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "restore_baseline.py")], check=True)
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "patch_unlimited_ammo.py")], check=True)
    
    for apk in REQUIRED_SPLITS:
        if apk == "split_config.arm64_v8a.apk":
            update_split_arm64_apk(EXTRACTED_DIR / apk, WORKING_SO, ammo_temp / apk)
        else:
            shutil.copy2(EXTRACTED_DIR / apk, ammo_temp / apk)
            
    zipalign_and_sign_split_set(ammo_temp, ammo_dir)
    shutil.rmtree(ammo_temp)

    # 3. Unlimited Fuel Split Package
    fuel_dir = builds_dir / "fuel_mod_splits"
    fuel_temp = builds_dir / "fuel_temp"
    fuel_temp.mkdir(parents=True, exist_ok=True)
    
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "restore_baseline.py")], check=True)
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "patch_unlimited_fuel.py")], check=True)
    
    for apk in REQUIRED_SPLITS:
        if apk == "split_config.arm64_v8a.apk":
            update_split_arm64_apk(EXTRACTED_DIR / apk, WORKING_SO, fuel_temp / apk)
        else:
            shutil.copy2(EXTRACTED_DIR / apk, fuel_temp / apk)
            
    zipalign_and_sign_split_set(fuel_temp, fuel_dir)
    shutil.rmtree(fuel_temp)

    # 4. Combined Mod Split Package (Ammo + Fuel)
    combined_dir = builds_dir / "combined_mod_splits"
    combined_temp = builds_dir / "combined_temp"
    combined_temp.mkdir(parents=True, exist_ok=True)
    
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "restore_baseline.py")], check=True)
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "patch_unlimited_ammo.py")], check=True)
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "patch_unlimited_fuel.py")], check=True)
    
    for apk in REQUIRED_SPLITS:
        if apk == "split_config.arm64_v8a.apk":
            update_split_arm64_apk(EXTRACTED_DIR / apk, WORKING_SO, combined_temp / apk)
        else:
            shutil.copy2(EXTRACTED_DIR / apk, combined_temp / apk)
            
    zipalign_and_sign_split_set(combined_temp, combined_dir)
    shutil.rmtree(combined_temp)

    # Restore native library to baseline state
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "restore_baseline.py")], check=True)
    
    print("\n============================================================")
    print("ALL SPLIT PACKAGE BUILDS COMPLETE AND SIGNATURE VERIFIED")
    print("============================================================")

if __name__ == "__main__":
    main()
