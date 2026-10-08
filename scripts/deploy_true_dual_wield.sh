#!/usr/bin/env bash
# Verify then update only; never uninstall/clear data. Approve phone-side prompt.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
serial="${1:-}"
adb_args=()
if [[ -n "$serial" ]]; then adb_args=(-s "$serial"); fi
python3 "$project_dir/scripts/build_true_dual_wield.py" --verify
adb "${adb_args[@]}" install-multiple --no-incremental -r \
 "$project_dir/builds/universal_dual_wield_splits/base.apk" \
 "$project_dir/builds/universal_dual_wield_splits/split_config.arm64_v8a.apk" \
 "$project_dir/builds/universal_dual_wield_splits/split_config.xxhdpi.apk" \
 "$project_dir/builds/universal_dual_wield_splits/split_config.en.apk"
