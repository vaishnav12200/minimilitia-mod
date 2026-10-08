#!/usr/bin/env bash
# Update only; never uninstall or clear data. Phone must approve USB installs.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
serial="${1:-}"
adb_args=()
if [[ -n "$serial" ]]; then adb_args=(-s "$serial"); fi
python3 "$project_dir/scripts/verify_fixed_gameplay.py" --duplicates
adb "${adb_args[@]}" install-multiple --no-incremental -r \
 "$project_dir/builds/fixed_ammo_dual_weapon_splits/base.apk" \
 "$project_dir/builds/fixed_ammo_dual_weapon_splits/split_config.arm64_v8a.apk" \
 "$project_dir/builds/fixed_ammo_dual_weapon_splits/split_config.xxhdpi.apk" \
 "$project_dir/builds/fixed_ammo_dual_weapon_splits/split_config.en.apk"
