#!/usr/bin/env bash
# Claude agent backend. Implements the contract in backends/README.md.

backend_bin() {
  echo "${DAIMON_CLAUDE_BIN:-$(command -v claude || echo claude)}"
}

backend_cli_args() {  # model danger(0/1) session_name -> args after the binary
  local model="$1" danger="$2" session_name="$3" flag="" mcp=""
  [ "$danger" = "1" ] && flag="--dangerously-skip-permissions"
  [ -n "${DAIMON_MCP_CONFIG:-}" ] && mcp="--mcp-config ${DAIMON_MCP_CONFIG} --strict-mcp-config"
  printf '%s --model %s -n %s %s' "$flag" "$model" "$session_name" "$mcp"
}

backend_ready_regex() {  # 1 if danger -> bypass banner, else the idle input prompt
  if [ "${1:-1}" = "1" ]; then echo "bypass permissions"; else echo "for shortcuts"; fi
}

backend_completion_mode() { echo "hook"; }
