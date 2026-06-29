#!/usr/bin/env bash
# Preflight: check that everything a real run needs is present and configured.
set -uo pipefail
DAIMON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DAIMON_LIB_DIR/common.sh"

WARN=0; FAIL=0
ok()   { echo "  ok    $1"; }
warn() { echo "  warn  $1"; WARN=1; }
bad()  { echo "  FAIL  $1"; FAIL=1; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "tools"
have python3 && ok "python3 $(python3 --version 2>&1 | awk '{print $2}')" || bad "python3 missing"
have tmux && ok "tmux" || bad "tmux missing"
have gh && ok "gh" || warn "gh missing (PR/issue daemons need it)"
have claude && ok "claude" || warn "claude not on PATH (set DAIMON_CLAUDE_BIN)"
have gh && { gh auth status >/dev/null 2>&1 && ok "gh authenticated" || warn "gh not authenticated (gh auth login)"; }

echo "paths"
mkdir -p "$DAIMON_STATE_DIR" 2>/dev/null
[ -w "$DAIMON_STATE_DIR" ] && ok "state_dir writable: $DAIMON_STATE_DIR" || bad "state_dir not writable"
[ -d "$DAIMON_INSTALL_ROOT" ] && ok "install_root: $DAIMON_INSTALL_ROOT" || bad "install_root missing"

echo "claude integration"
grep -q "DAIMON_" "$HOME/.claude/settings.json" 2>/dev/null \
  && ok "completion/heartbeat hooks installed" || warn "hooks NOT installed — run: daimon install"

echo "config"
cfg validate >/dev/null 2>&1 && ok "config valid" || bad "config invalid — run: daimon validate"

echo "daemons"
needs_shortcut=0
for slug in $(cfg daemons); do
  wd="$(cfg daemon "$slug" working_dir)"
  cmd="$(cfg daemon "$slug" command | sed 's#^/##')"
  [ "$(cfg daemon "$slug" source 2>/dev/null)" = "shortcut" ] && needs_shortcut=1
  msg="$slug"
  if [ "$wd" = "$DAIMON_INSTALL_ROOT" ]; then msg="$msg [working_dir not set — point it at your repo]"
  elif [ ! -d "$wd" ]; then msg="$msg [working_dir missing: $wd]"; fi
  [ -f "$HOME/.claude/skills/$cmd/SKILL.md" ] || msg="$msg [skill not synced — run: daimon sync]"
  ( set -u; eval "$(cfg env "$slug")" ) >/dev/null 2>&1 \
    || msg="$msg [inputs do not eval cleanly — run: daimon validate]"
  [ "$msg" = "$slug" ] && ok "$slug" || warn "$msg"
done

if [ "$needs_shortcut" = 1 ]; then
  echo "shortcut"
  source "$DAIMON_INSTALL_ROOT/profiles/shortcut/lib.sh"
  [ -n "$(shortcut_token)" ] && ok "API token resolves" \
    || warn "no token (~/.config/short/config.json or \$SHORTCUT_API_TOKEN)"
fi

echo ""
[ "$FAIL" = 1 ] && { echo "FAIL — fix the above before running."; exit 1; }
[ "$WARN" = 1 ] && { echo "ready, with warnings above."; exit 0; }
echo "all checks passed."
