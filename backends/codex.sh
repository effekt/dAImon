#!/usr/bin/env bash
# Codex agent backend. Implements the contract in backends/README.md.
# Completion is idle-based: Codex does not expose a Claude-style Stop hook, so the
# launcher infers completion from heartbeat staleness rather than a sentinel.

backend_bin() {
  echo "${DAIMON_CODEX_BIN:-$(command -v codex || echo codex)}"
}

backend_cli_args() {  # model danger(0/1) session_name -> args after the binary
  local model="$1" danger="$2" flag=""
  [ "$danger" = "1" ] && flag="--dangerously-bypass-approvals-and-sandbox"
  printf '%s -m %s' "$flag" "$model"
}

backend_ready_regex() { echo ""; }

backend_completion_mode() { echo "idle"; }
