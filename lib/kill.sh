#!/usr/bin/env bash
# Hard-kill a daemon's run: agent session(s) + descendant tree + wrappers.
set -uo pipefail
DAIMON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DAIMON_LIB_DIR/common.sh"
source "$DAIMON_LIB_DIR/reap.sh"

TARGET="${1:?usage: kill.sh <slug|all>}"

kill_slug() {
  local slug="$1" sess
  for sess in $(tmux ls -F '#{session_name}' 2>/dev/null | grep -E "^${DAIMON_NS}-${slug}(\$|-claude\$)" || true); do
    echo "reaping $sess"
    reap_session "$sess"
    rm -f "$(sentinel_file "$sess")" "$(heartbeat_file "$sess")" "$(wait_file "$sess")"
  done
  for pid in $(pgrep -f "lib/(run|launch)\.sh ${slug}\$" 2>/dev/null || true); do
    echo "killing wrapper pid=$pid"
    kill "$pid" 2>/dev/null
  done
}

if [ "$TARGET" = "all" ]; then
  for slug in $(cfg daemons); do kill_slug "$slug"; done
else
  kill_slug "$TARGET"
fi
