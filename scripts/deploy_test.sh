#!/usr/bin/env bash
# =============================================================================
# deploy_test.sh — Split Package Deployment Helper for Mini Militia Classic
# =============================================================================
# Usage:
#   ./scripts/deploy_test.sh baseline
#   ./scripts/deploy_test.sh ammo
#   ./scripts/deploy_test.sh fuel
#   ./scripts/deploy_test.sh combined
# =============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILDS_DIR="$PROJECT_DIR/builds"

TARGET="${1:-combined}"

case "$TARGET" in
    baseline)
        DIR="$BUILDS_DIR/baseline_splits"
        DESC="Unmodified Baseline Split Package"
        ;;
    ammo)
        DIR="$BUILDS_DIR/ammo_mod_splits"
        DESC="Unlimited Ammunition Mod Split Package"
        ;;
    fuel)
        DIR="$BUILDS_DIR/fuel_mod_splits"
        DESC="Unlimited Jetpack Fuel Mod Split Package"
        ;;
    combined)
        DIR="$BUILDS_DIR/combined_mod_splits"
        DESC="Combined Mod Split Package (Ammo + Fuel)"
        ;;
    *)
        echo "Usage: $0 [baseline|ammo|fuel|combined]"
        exit 1
        ;;
esac

if ! command -v adb >/dev/null 2>&1; then
    echo "[!] Error: adb tool not found in PATH"
    exit 1
fi

if ! adb devices | grep -q "device$"; then
    echo "[!] Error: No Android device detected via ADB."
    echo "    Connect your device via USB/Wi-Fi and enable USB Debugging."
    exit 1
fi

echo "============================================================"
echo " Deploying $DESC"
echo " Target Directory: $DIR"
echo "============================================================"

adb install-multiple -r \
    "$DIR/base.apk" \
    "$DIR/split_config.arm64_v8a.apk" \
    "$DIR/split_config.xxhdpi.apk" \
    "$DIR/split_config.en.apk"

echo ""
echo "[OK] Deployment complete! Launch Mini Militia Classic on device to test."
