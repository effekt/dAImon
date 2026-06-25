#!/usr/bin/env bash
# Post-run quota auto-throttle: if the captured transcript shows the agent hit a
# usage limit, set throttle=halt until the reset time (or one hour out).
# Reads $DAIMON_TRANSCRIPT. Sourced/run after common.sh is available on PATH.
set -uo pipefail

DAIMON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DAIMON_LIB_DIR/common.sh"

BACKEND="${1:-unknown}"
[ -f "${DAIMON_TRANSCRIPT:-}" ] || exit 0

if grep -qiE "usage limit|hit your limit|rate limit|quota" "$DAIMON_TRANSCRIPT"; then
  ensure_state_dirs
  python3 - "$(runtime_dir)/throttle.json" "$BACKEND" <<'PY'
import json, sys, time
path, backend = sys.argv[1], sys.argv[2]
json.dump({
    "level": "halt",
    "set_at": time.time(),
    "expires_at": time.time() + 3600,
    "reason": f"{backend} usage limit detected in transcript",
}, open(path, "w"))
PY
fi
