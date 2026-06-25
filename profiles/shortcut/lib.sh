#!/usr/bin/env bash
# Shared helpers for the Shortcut source profile: API token + story search.
# Sourced by a daemon's discover.sh.

shortcut_token() {
  if [ -n "${SHORTCUT_API_TOKEN:-}" ]; then
    echo "$SHORTCUT_API_TOKEN"
    return
  fi
  local f
  for f in "$HOME/.config/short/config.json" "$HOME/.config/shortcut-cli/config.json"; do
    if [ -f "$f" ]; then
      python3 -c "import json;print(json.load(open('$f')).get('token',''))" 2>/dev/null
      return
    fi
  done
}

# shortcut_count "<search query>" -> number of matching stories (0 on any error).
shortcut_count() {
  local token; token="$(shortcut_token)"
  [ -z "$token" ] && { echo 0; return; }
  curl -s -G "https://api.app.shortcut.com/api/v3/search/stories" \
    --data-urlencode "query=$1" -H "Shortcut-Token: $token" \
    | python3 -c "import sys,json;print(json.load(sys.stdin).get('total',0))" 2>/dev/null || echo 0
}
