#!/usr/bin/env bash
# Generic per-daemon wrapper invoked by launchd (or `daimon run <slug>`):
# gate on throttle/budget, check the inbox, run the daemon's discovery step, and
# launch the agent only if there is work.
set -uo pipefail

SLUG="${1:?usage: run.sh <slug>}"
DAIMON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DAIMON_LIB_DIR/common.sh"
source "$DAIMON_LIB_DIR/logging.sh"
source "$DAIMON_LIB_DIR/schedule.sh"
ensure_state_dirs
OPLOG="$(logs_dir)/$SLUG.log"

cd "$(cfg daemon "$SLUG" working_dir)" || cd "$DAIMON_INSTALL_ROOT" || exit 1

DAEMON_NAME="$SLUG" source "$DAIMON_LIB_DIR/throttle.sh"
if [ "$SHOULD_SKIP" -eq 1 ]; then log_event "$SLUG" skip "$SKIP_REASON" >> "$OPLOG"; exit 0; fi

DAEMON_NAME="$SLUG" source "$DAIMON_LIB_DIR/inbox.sh"
if [ "${HAS_INBOX_MESSAGES:-0}" -gt 0 ]; then
  log_event "$SLUG" inbox "$HAS_INBOX_MESSAGES message(s); launching" >> "$OPLOG"
  exec bash "$DAIMON_LIB_DIR/launch.sh" "$SLUG"
fi

DISCOVER="$DAIMON_INSTALL_ROOT/daemons/$SLUG/discover.sh"
if [ -x "$DISCOVER" ] || [ -f "$DISCOVER" ]; then
  set -a; eval "$(cfg env "$SLUG")"; set +a
  if bash "$DISCOVER"; then
    log_event "$SLUG" launch_decision "discovery found work" >> "$OPLOG"
    exec bash "$DAIMON_LIB_DIR/launch.sh" "$SLUG"
  else
    log_event "$SLUG" skip "discovery found nothing; $(next_run_display "$SLUG")" >> "$OPLOG"
    exit 0
  fi
fi

log_event "$SLUG" launch_decision "no discovery step; launching" >> "$OPLOG"
exec bash "$DAIMON_LIB_DIR/launch.sh" "$SLUG"
