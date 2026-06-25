#!/usr/bin/env bash
# Safety-net sweep, run on a schedule. Reaps orphaned agent sessions (launcher
# died but tmux survived), kills leaked MCP node servers reparented to pid 1, and
# enforces log/transcript retention.
set -uo pipefail

DAIMON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DAIMON_LIB_DIR/common.sh"
source "$DAIMON_LIB_DIR/logging.sh"
source "$DAIMON_LIB_DIR/reap.sh"
ensure_state_dirs
WLOG="$(logs_dir)/watchdog.log"

wlog() { log_event watchdog "$1" "$2" >> "$WLOG"; }

slug_of_session() {  # strips the namespace prefix and any -<backend> suffix
  local s="${1#${DAIMON_NS}-}"
  s="${s%-claude}"; s="${s%-codex}"; echo "$s"
}

# 1. Orphaned/stuck agent sessions.
for sess in $(tmux ls -F '#{session_name}' 2>/dev/null | grep -E "^${DAIMON_NS}-" || true); do
  hb="$(heartbeat_file "$sess")"
  slug="$(slug_of_session "$sess")"
  stuck="$(cfg daemon "$slug" stuck_after 2>/dev/null || cfg get defaults.stuck_after)"
  if [ -f "$hb" ]; then
    age=$(( $(now_epoch) - $(stat -f %m "$hb" 2>/dev/null || now_epoch) ))
  else
    age=$(( stuck + 1 ))
  fi
  if [ "$age" -ge "$stuck" ]; then
    wlog reap "stuck/orphan session=$sess slug=$slug age=${age}s"
    reap_session "$sess"
    rm -f "$hb" "$(sentinel_file "$sess")" "$(wait_file "$sess")"
  fi
done

# 2. Leaked MCP node servers (ppid 1) from torn-down sessions.
for pid in $(pgrep -f 'npx .*mcp|mcp-server' 2>/dev/null || true); do
  ppid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
  if [ "$ppid" = "1" ]; then
    wlog reap_mcp "orphan mcp pid=$pid"
    kill "$pid" 2>/dev/null; sleep 1; kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null
  fi
done

# 3. Retention.
prune_old_transcripts
for f in "$(logs_dir)"/*.log; do rotate_if_large "$f"; done
