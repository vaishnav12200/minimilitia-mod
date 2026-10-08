#!/usr/bin/env bash
# =============================================================================
# build.sh — Mini Militia Classic Mod Builder
# =============================================================================
# Usage: ./scripts/build.sh
# Rebuilds the decoded APK using apktool, then calls sign.sh
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DECODED_DIR="$PROJECT_DIR/decoded"
BUILDS_DIR="$PROJECT_DIR/builds"
APKTOOL="java -jar $SCRIPT_DIR/apktool.jar"

BUILD_SDK="${ANDROID_SDK_ROOT:-/home/vaishnavkm/Android/Sdk}/build-tools/35.0.0"
ZIPALIGN="$BUILD_SDK/zipalign"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

step()  { echo -e "\n${CYAN}[STEP]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
UNSIGNED_APK="$BUILDS_DIR/mmc-mod-${TIMESTAMP}-unsigned.apk"
ALIGNED_APK="$BUILDS_DIR/mmc-mod-${TIMESTAMP}-aligned.apk"
SIGNED_APK="$BUILDS_DIR/mmc-mod-${TIMESTAMP}-signed.apk"

mkdir -p "$BUILDS_DIR"

echo "============================================================"
echo "  Mini Militia Classic — Mod Builder"
echo "  Timestamp: $TIMESTAMP"
echo "============================================================"

# 1. Verify decoded directory exists
step "Verifying decoded directory"
[[ -d "$DECODED_DIR" ]] || fail "Decoded directory not found: $DECODED_DIR. Run apktool decode first."
ok "Decoded directory exists"

# 2. Rebuild with apktool
step "Rebuilding APK with apktool (this may take 2-5 minutes)..."
$APKTOOL b "$DECODED_DIR" -o "$UNSIGNED_APK" --use-aapt2 2>&1
ok "Unsigned APK created: $UNSIGNED_APK"

# 3. Zip-align
step "Zip-aligning APK..."
if [[ ! -x "$ZIPALIGN" ]]; then
    warn "zipalign not found at $ZIPALIGN — searching..."
    ZIPALIGN=$(find /home/vaishnavkm/Android/Sdk/build-tools/ -name "zipalign" | sort -V | tail -1)
    [[ -x "$ZIPALIGN" ]] || fail "zipalign not found"
fi
"$ZIPALIGN" -v -p 4 "$UNSIGNED_APK" "$ALIGNED_APK" && ok "Zip-aligned APK: $ALIGNED_APK"

# 4. Sign
step "Signing APK..."
SIGN_SCRIPT="$SCRIPT_DIR/sign.sh"
[[ -x "$SIGN_SCRIPT" ]] || chmod +x "$SIGN_SCRIPT"
ALIGNED_APK="$ALIGNED_APK" SIGNED_APK="$SIGNED_APK" "$SIGN_SCRIPT"

echo ""
echo "============================================================"
echo "  BUILD COMPLETE"
echo "  Signed APK: $SIGNED_APK"
echo "  Size: $(ls -lh "$SIGNED_APK" | awk '{print $5}')"
echo "============================================================"
echo ""
echo "Install with: adb install \"$SIGNED_APK\""
