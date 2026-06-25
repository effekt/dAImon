#!/usr/bin/env bash
# One-line status per daemon: launchd state, running session, schedule, last log.
set -uo pipefail
DAIMON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DAIMON_LIB_DIR/common.sh"
source "$DAIMON_LIB_DIR/schedule.sh"

printf '%-22s %-8s %-9s %s\n' DAEMON LAUNCHD RUNNING SCHEDULE
for slug in $(cfg daemons); do
  label="com.${DAIMON_NS}.${slug}"
  if launchctl list 2>/dev/null | grep -q "$label"; then loaded=yes; else loaded=no; fi
  if tmux ls -F '#{session_name}' 2>/dev/null | grep -qE "^${DAIMON_NS}-${slug}(\$|-)"; then running=yes; else running=no; fi
  printf '%-22s %-8s %-9s %s\n' "$slug" "$loaded" "$running" "$(next_run_display "$slug")"
done
