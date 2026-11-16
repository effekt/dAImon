#!/usr/bin/env bash
# Claude agent backend. Implements the contract in backends/README.md.

backend_bin() {
  echo "${DAIMON_CLAUDE_BIN:-$(command -v claude || echo claude)}"
}

backend_cli_args() {  # model danger(0/1) session_name -> args after the binary
  local model="$1" danger="$2" session_name="$3" flag="" mcp=""
  [ "$danger" = "1" ] && flag="--dangerously-skip-permissions"
  [ -n "${DAIMON_MCP_CONFIG:-}" ] && mcp="--mcp-config ${DAIMON_MCP_CONFIG} --strict-mcp-config"
  # Pin the session id so the Stop hook can tell this agent from any child
  # `claude -p` a user hook spawns (it inherits DAIMON_SENTINEL too).
  # A resumed run continues an earlier session (same id) instead of starting one.
  if [ -n "${DAIMON_AGENT_SESSION:-}" ]; then
    if [ "${DAIMON_RESUME:-0}" = "1" ]; then mcp="$mcp --resume ${DAIMON_AGENT_SESSION}"
    else mcp="$mcp --session-id ${DAIMON_AGENT_SESSION}"; fi
  fi
  printf '%s --model %s -n %s %s' "$flag" "$model" "$session_name" "$mcp"
}

backend_ready_regex() {  # 1 if danger -> bypass banner, else the idle input prompt
  if [ "${1:-1}" = "1" ]; then echo "bypass permissions"; else echo "for shortcuts"; fi
}

backend_completion_mode() { echo "hook"; }

# Can continue an earlier session by id (see "Resuming a session" in README.md).
backend_supports_resume() { return 0; }

backend_exhausted_regex() {
  echo "you('ve| have) hit your ((weekly|monthly)[[:space:]]+)?((usage|spend)[[:space:]]+)?limit"
}
