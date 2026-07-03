#!/usr/bin/env bash
# Shared helpers for the Datadog source profile: log search via the `pup` CLI, for
# discovery gates. Sourced by a daemon's discover.sh. Every helper fails closed
# (no pup, no auth, bad output) to the "no work" answer, so a gate never launches
# on a broken query.

# dd_log_json "<query>" "<lookback>" -> JSON array of matching log events, or [] on
# any failure. pup may wrap results as {data:[...]} or return a bare array; unwrap
# to the bare array so callers can `jq length` regardless of the exact envelope.
dd_log_json() {
  local out
  # --no-agent: pup auto-enables "agent mode" for AI assistants, which reshapes
  # output; the gate parses the plain JSON, so pin it off for a stable envelope.
  out="$(pup logs search --query="$1" --from="$2" --output json --no-agent 2>/dev/null)" || { printf '[]'; return; }
  printf '%s' "$out" \
    | jq -c 'if type == "array" then . elif type == "object" then (.data // []) else [] end' 2>/dev/null \
    || printf '[]'
}

# dd_log_count "<query>" "<lookback>" -> integer count of matching events (0 on failure).
dd_log_count() {
  dd_log_json "$1" "$2" | jq 'length' 2>/dev/null || echo 0
}
