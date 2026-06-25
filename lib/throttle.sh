#!/usr/bin/env bash
# Throttle gate. Caller sets DAEMON_NAME, then sources this; reads SHOULD_SKIP /
# SKIP_REASON. Levels: off | moderate | severe | halt (in runtime/throttle.json).

_throttle_file() { echo "$(runtime_dir)/throttle.json"; }
_fires_file()    { echo "$(runtime_dir)/throttle-fires.json"; }

throttle_level() {  # echoes the active level, honoring expiry
  python3 - "$(_throttle_file)" <<'PY'
import json, sys, time
try: d = json.load(open(sys.argv[1]))
except Exception: print("off"); raise SystemExit
exp = d.get("expires_at")
if exp and time.time() > exp: print("off")
else: print(d.get("level", "off"))
PY
}

_in_list() {  # value cfg-key
  local v="$1" key="$2" item
  for item in $(cfg get "$key" 2>/dev/null); do [ "$item" = "$v" ] && return 0; done
  return 1
}

_bump_fire() {  # daemon -> echoes the new fire count
  python3 - "$(_fires_file)" "$1" <<'PY'
import json, sys
path, slug = sys.argv[1], sys.argv[2]
try: d = json.load(open(path))
except Exception: d = {}
d[slug] = d.get(slug, 0) + 1
json.dump(d, open(path, "w"))
print(d[slug])
PY
}

SHOULD_SKIP=0
SKIP_REASON=""
{
  level="$(throttle_level)"
  if _in_list "$DAEMON_NAME" throttle.exempt; then
    :
  elif [ "$level" = "off" ]; then
    :
  elif [ "$level" = "halt" ]; then
    SHOULD_SKIP=1; SKIP_REASON="throttle=halt: skipping $DAEMON_NAME"
  else
    mod="$(cfg get throttle.moderate_mod)"
    if [ "$level" = "severe" ] && ! _in_list "$DAEMON_NAME" throttle.severe_critical; then
      mod="$(cfg get throttle.severe_mod)"
    fi
    count="$(_bump_fire "$DAEMON_NAME")"
    if [ $(( count % mod )) -ne 0 ]; then
      SHOULD_SKIP=1; SKIP_REASON="throttle=$level: $DAEMON_NAME fire $count not a multiple of $mod"
    fi
  fi
}
