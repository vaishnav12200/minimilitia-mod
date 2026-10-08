#!/usr/bin/env bash
# =============================================================================
# verify.sh — APK Verifier for Mini Militia Mod
# =============================================================================
# Usage: ./scripts/verify.sh <signed-apk>
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

BUILD_SDK="${ANDROID_SDK_ROOT:-/home/vaishnavkm/Android/Sdk}/build-tools/35.0.0"
APKSIGNER="$BUILD_SDK/apksigner"
ZIPALIGN="$BUILD_SDK/zipalign"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

step()  { echo -e "\n${CYAN}[STEP]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

APK="${1:-}"
[[ -n "$APK" ]] || fail "Usage: $0 <signed-apk>"
[[ -f "$APK" ]]  || fail "APK not found: $APK"

echo "============================================================"
echo "  Mini Militia Classic — APK Verifier"
echo "  APK: $APK"
echo "============================================================"

# Find tools
if [[ ! -x "$APKSIGNER" ]]; then
    APKSIGNER=$(find /home/vaishnavkm/Android/Sdk/build-tools/ -name "apksigner" | sort -V | tail -1)
fi
if [[ ! -x "$ZIPALIGN" ]]; then
    ZIPALIGN=$(find /home/vaishnavkm/Android/Sdk/build-tools/ -name "zipalign" | sort -V | tail -1)
fi

# 1. File info
step "APK file info"
ls -lh "$APK"
file "$APK"

# 2. SHA-256
step "SHA-256 checksum"
sha256sum "$APK"

# 3. Signature verification
step "APK signature verification"
"$APKSIGNER" verify --verbose --print-certs "$APK" 2>&1

# 4. Zip alignment
step "Zip alignment check"
"$ZIPALIGN" -c -v 4 "$APK" 2>&1 && ok "Zip alignment: OK" || warn "Zip alignment check failed (may need re-alignment)"

# 5. DEX count
step "DEX file count"
DEX_COUNT=$(unzip -l "$APK" | grep "\.dex" | wc -l)
ok "DEX files: $DEX_COUNT"

# 6. ADB install (if device connected)
step "ADB device check"
DEVICES=$(adb devices 2>/dev/null | grep -v "List of" | grep -v "^$" | grep "device$" | wc -l)
if [[ "$DEVICES" -gt 0 ]]; then
    ok "$DEVICES device(s) connected"
    echo "To install: adb install -r \"$APK\""
else
    warn "No ADB devices connected — skipping install step"
fi

echo ""
echo "============================================================"
echo "  Verification complete."
echo "============================================================"
