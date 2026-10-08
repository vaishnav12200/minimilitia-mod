#!/usr/bin/env python3
"""
Standalone Universal APK Assembly Script for Mini Militia Classic

Assembles base APK, ARM64 native library (patched or baseline), and ARM64 split libraries
into a single, valid standalone universal APK.

Strips split-APK manifest dependencies (android:requiredSplitTypes, com.android.vending.splits).
Sets android:extractNativeLibs="true" for universal installation compatibility.
Zip-aligns and signs the resulting standalone APK with the test keystore.
"""

import os
import sys
import shutil
import zipfile
import subprocess
import re
from pathlib import Path

PROJECT_DIR = Path("/home/vaishnavkm/Projects/MiniMilitiaMod")
DECODED_DIR = PROJECT_DIR / "decoded"
BUILDS_DIR = PROJECT_DIR / "builds" / "standalone"
SPLITS_DIR = PROJECT_DIR / "builds" / "combined_mod_splits"
KEYSTORE = PROJECT_DIR / "signing" / "mmc-test.keystore"
KEY_ALIAS = "mmc-test-key"
KEY_PASS = "mmc_test_store_pw"

APKTOOL_JAR = PROJECT_DIR / "scripts" / "apktool.jar"
ZIPALIGN = "/home/vaishnavkm/Android/Sdk/build-tools/35.0.0/zipalign"
APKSIGNER = "/home/vaishnavkm/Android/Sdk/build-tools/35.0.0/apksigner"

def build_standalone_apk(mode="combined"):
    print("============================================================")
    print(f"ASSEMBLING STANDALONE UNIVERSAL APK ({mode.upper()})")
    print("============================================================")
    
    BUILDS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Prepare native library state
    if mode == "combined":
        print("[*] Applying combined patches (Ammo + Jetpack)...")
        subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "restore_baseline.py")], check=True)
        subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "patch_unlimited_ammo.py")], check=True)
        subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "patch_unlimited_fuel.py")], check=True)
    elif mode == "baseline":
        print("[*] Restoring unmodified baseline native library...")
        subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "restore_baseline.py")], check=True)

    # Copy native library to decoded lib folder
    target_lib_dir = DECODED_DIR / "lib" / "arm64-v8a"
    target_lib_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECT_DIR / "native-analysis" / "libcocos2dcpp.so", target_lib_dir / "libcocos2dcpp.so")
    print(f"[+] Synced {mode} libcocos2dcpp.so into {target_lib_dir}")

    # Copy remaining native libraries from split_config.arm64_v8a.apk into target_lib_dir
    arm64_split_apk = SPLITS_DIR / "split_config.arm64_v8a.apk"
    with zipfile.ZipFile(arm64_split_apk, 'r') as z:
        for fname in z.namelist():
            if fname.startswith("lib/arm64-v8a/") and not fname.endswith("libcocos2dcpp.so"):
                out_path = DECODED_DIR / fname
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(z.read(fname))
    print("[+] Extracted all additional ARM64 native libraries into decoded/lib/arm64-v8a/")

    # 2. Modify AndroidManifest.xml to strip split dependencies & enable native library extraction
    manifest_path = DECODED_DIR / "AndroidManifest.xml"
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove android:requiredSplitTypes and android:splitTypes
    content = re.sub(r'\s*android:requiredSplitTypes="[^"]*"', '', content)
    content = re.sub(r'\s*android:splitTypes="[^"]*"', '', content)

    # Remove com.android.vending.splits meta-data tags
    content = re.sub(r'<meta-data\s+android:name="com\.android\.vending\.splits\.required"\s+[^/>]*/>', '', content)
    content = re.sub(r'<meta-data\s+android:name="com\.android\.vending\.splits"\s+[^/>]*/>', '', content)

    # Set android:extractNativeLibs="true" for standalone extraction compatibility
    content = re.sub(r'android:extractNativeLibs="false"', 'android:extractNativeLibs="true"', content)

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("[+] Modified AndroidManifest.xml: Stripped split requirements & set extractNativeLibs='true'.")

    # 3. Build APK with apktool
    unsigned_apk = BUILDS_DIR / f"mmc-standalone-{mode}-unsigned.apk"
    aligned_apk = BUILDS_DIR / f"mmc-standalone-{mode}-aligned.apk"
    signed_apk = BUILDS_DIR / f"mmc-standalone-{mode}-signed.apk"

    for p in [unsigned_apk, aligned_apk, signed_apk]:
        if p.exists(): os.remove(p)

    print(f"[*] Rebuilding APK with Apktool to {unsigned_apk.name}...")
    res_build = subprocess.run([
        "java", "-jar", str(APKTOOL_JAR), "b", str(DECODED_DIR), "-o", str(unsigned_apk)
    ], capture_output=True, text=True)

    if res_build.returncode != 0:
        print(f"[!] Apktool build failed:\n{res_build.stderr}")
        sys.exit(1)
    print(f"[+] Apktool build successful! Unsigned APK size: {os.path.getsize(unsigned_apk)} bytes")

    # 4. Zipalign
    print(f"[*] Zip-aligning APK...")
    res_align = subprocess.run([ZIPALIGN, "-p", "-f", "4", str(unsigned_apk), str(aligned_apk)], capture_output=True, text=True)
    if res_align.returncode != 0:
        print(f"[!] Zipalign failed:\n{res_align.stderr}")
        sys.exit(1)
    print("[+] Zip-align successful!")

    # 5. Sign with apksigner
    print(f"[*] Signing standalone APK with test keystore...")
    res_sign = subprocess.run([
        APKSIGNER, "sign",
        "--ks", str(KEYSTORE),
        "--ks-key-alias", KEY_ALIAS,
        "--ks-pass", f"pass:{KEY_PASS}",
        "--out", str(signed_apk),
        str(aligned_apk)
    ], capture_output=True, text=True)

    if res_sign.returncode != 0:
        print(f"[!] Apksigner failed:\n{res_sign.stderr}")
        sys.exit(1)

    # Clean intermediate files
    if unsigned_apk.exists(): os.remove(unsigned_apk)
    if aligned_apk.exists(): os.remove(aligned_apk)

    # 6. Verify signature
    res_verify = subprocess.run([APKSIGNER, "verify", str(signed_apk)], capture_output=True, text=True)
    if res_verify.returncode != 0:
        print(f"[!] Signature verification failed for {signed_apk.name}:\n{res_verify.stderr}")
        sys.exit(1)

    # Restore native library baseline state
    subprocess.run(["python3", str(PROJECT_DIR / "scripts" / "restore_baseline.py")], check=True)

    print(f"\n[SUCCESS] Standalone Universal APK created and verified!")
    print(f"  Final Signed APK Path: {signed_apk}")
    print(f"  File Size: {os.path.getsize(signed_apk)} bytes (~{os.path.getsize(signed_apk)//(1024*1024)} MB)")
    print(f"  Install command: adb install -r \"{signed_apk}\"")
    return signed_apk

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "combined"
    build_standalone_apk(mode)
