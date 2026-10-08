#!/usr/bin/env bash
# =============================================================================
# sign.sh — APK Signer for Mini Militia Mod
# =============================================================================
# Usage: ALIGNED_APK=<path> SIGNED_APK=<path> ./scripts/sign.sh
#   OR:  ./scripts/sign.sh <aligned-apk> <signed-apk>
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SIGNING_DIR="$PROJECT_DIR/signing"
KEYSTORE="$SIGNING_DIR/mmc-test.keystore"
KEY_ALIAS="mmc-test-key"

BUILD_SDK="${ANDROID_SDK_ROOT:-/home/vaishnavkm/Android/Sdk}/build-tools/35.0.0"
APKSIGNER="$BUILD_SDK/apksigner"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

step()  { echo -e "\n${CYAN}[STEP]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# Resolve input/output paths
ALIGNED_APK="${ALIGNED_APK:-${1:-}}"
SIGNED_APK="${SIGNED_APK:-${2:-}}"

[[ -n "$ALIGNED_APK" ]] || fail "No aligned APK specified. Set ALIGNED_APK env var or pass as arg."
[[ -n "$SIGNED_APK" ]]  || fail "No signed APK path specified. Set SIGNED_APK env var or pass as arg."
[[ -f "$ALIGNED_APK" ]] || fail "Aligned APK not found: $ALIGNED_APK"

mkdir -p "$SIGNING_DIR"

# Find apksigner if not at expected location
if [[ ! -x "$APKSIGNER" ]]; then
    warn "apksigner not at $APKSIGNER — searching..."
    APKSIGNER=$(find /home/vaishnavkm/Android/Sdk/build-tools/ -name "apksigner" | sort -V | tail -1)
    [[ -x "$APKSIGNER" ]] || fail "apksigner not found"
fi

# Generate keystore if it doesn't exist
if [[ ! -f "$KEYSTORE" ]]; then
    step "Generating test keystore (one-time setup)..."
    keytool -genkeypair \
        -alias "$KEY_ALIAS" \
        -keyalg RSA \
        -keysize 2048 \
        -validity 10000 \
        -keystore "$KEYSTORE" \
        -storetype pkcs12 \
        -storepass "mmc_test_store_pw" \
        -keypass "mmc_test_store_pw" \
        -dname "CN=MMC Mod Tester, OU=Testing, O=Local, L=Local, ST=Local, C=US" \
        2>&1
    ok "Keystore created: $KEYSTORE"
    warn "NOTE: This is a TEST keystore. Do not use for production or distribution."
else
    ok "Keystore already exists: $KEYSTORE"
fi

# Sign the APK
step "Signing APK..."
"$APKSIGNER" sign \
    --ks "$KEYSTORE" \
    --ks-pass pass:mmc_test_store_pw \
    --ks-key-alias "$KEY_ALIAS" \
    --out "$SIGNED_APK" \
    "$ALIGNED_APK" 2>&1 | grep -v WARNING

ok "Signed APK: $SIGNED_APK"

# Verify signature
step "Verifying APK signature..."
"$APKSIGNER" verify --verbose "$SIGNED_APK" 2>&1 | head -10

ok "Signature verification complete."
