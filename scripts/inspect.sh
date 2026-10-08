#!/usr/bin/env bash
# =============================================================================
# inspect.sh — Mini Militia Classic APK Inspector
# =============================================================================
# Usage: ./scripts/inspect.sh [APK_PATH]
# Default APK: ./base.apk
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APK="${1:-$PROJECT_DIR/base.apk}"

# Tool paths
APKTOOL="java -jar $SCRIPT_DIR/apktool.jar"
JADX="$SCRIPT_DIR/jadx-bin/bin/jadx"
ZIPALIGN="${ANDROID_SDK_ROOT:-/home/vaishnavkm/Android/Sdk}/build-tools/35.0.0/zipalign"
APKSIGNER="${ANDROID_SDK_ROOT:-/home/vaishnavkm/Android/Sdk}/build-tools/35.0.0/apksigner"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

check() { echo -e "${CYAN}[CHECK]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; }

echo "============================================================"
echo "  Mini Militia Classic — APK Inspector"
echo "  APK: $APK"
echo "============================================================"

# 1. File existence and basic info
check "APK file presence and type"
if [[ ! -f "$APK" ]]; then
    fail "APK not found: $APK"
    exit 1
fi
ok "APK found: $(ls -lh "$APK" | awk '{print $5, $9}')"
file "$APK"

# 2. SHA-256 checksum
check "SHA-256 checksum"
sha256sum "$APK"

# 3. DEX files
check "DEX files inside APK"
unzip -l "$APK" | grep "\.dex" || warn "No DEX files found"

# 4. Native libraries
check "Native libraries (.so files)"
NATIVE=$(unzip -l "$APK" | grep "\.so$" || true)
if [[ -z "$NATIVE" ]]; then
    warn "No .so files in base APK — likely delivered via ABI split APK"
else
    echo "$NATIVE"
fi

# 5. Required split APKs
check "Split APK requirement"
SPLITS=$(unzip -p "$APK" AndroidManifest.xml | strings | grep -i "split\|required" | head -5 || true)
echo "$SPLITS"

# 6. Database
check "SQLite databases"
unzip -l "$APK" | grep "\.sqlite\|\.db" || warn "No SQLite databases found"

# 7. Assets
check "Game assets (maps, sounds, fonts)"
unzip -l "$APK" | grep "^.*assets/" | wc -l
unzip -l "$APK" | grep "\.tmx" | wc -l
echo "  Map files (.tmx) found"

# 8. Manifest summary
check "AndroidManifest package info"
python3 - <<'PYEOF'
import subprocess, re
out = subprocess.check_output(["unzip", "-p", "/home/vaishnavkm/Projects/MiniMilitiaMod/base.apk", "AndroidManifest.xml"])
text = out.decode(errors='replace')
for kw in ["package=", "versionName=", "versionCode=", "minSdkVersion=", "targetSdkVersion="]:
    m = re.search(rf'{kw}"([^"]+)"', text)
    if m:
        print(f"  {kw} {m.group(1)}")
PYEOF

echo ""
echo "============================================================"
echo "  Inspection complete."
echo "============================================================"
