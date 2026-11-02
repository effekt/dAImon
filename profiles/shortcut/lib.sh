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

# shortcut_mention "<member-id>" -> the member's @mention name ("" on any error).
# The search DSL's owner:/requester: operators take a mention name, not the id.
shortcut_mention() {
  local token; token="$(shortcut_token)"
  [ -z "$token" ] && return
  curl -s "https://api.app.shortcut.com/api/v3/members/$1" -H "Shortcut-Token: $token" \
    | python3 -c "import sys,json;m=json.load(sys.stdin);p=m.get('profile') or {};print(p.get('mention_name') or m.get('mention_name') or '')" 2>/dev/null
}

# shortcut_exclusions -> query terms excluding every epic id in
# $DAIMON_INPUT_EXCLUDE_EPICS (space-separated), e.g. " !epic:1234". Empty when
# unset, so a gate can append it unconditionally. The search DSL takes the epic
# id directly; `epic_id:` is not an operator and matches nothing.
shortcut_exclusions() {
  local id out=""
  for id in ${DAIMON_INPUT_EXCLUDE_EPICS:-}; do out="$out !epic:$id"; done
  printf '%s' "$out"
}

# shortcut_owner_count "<base query>" -> story count scoped to $DAIMON_INPUT_OWNER
# (owner + requester), or workspace-wide if OWNER is unset. When OWNER is set but
# its mention can't be resolved it writes to stderr and returns 1, so run.sh
# surfaces a discover_error rather than letting the gate silently widen to the
# whole workspace and touch others' stories.
shortcut_owner_count() {
  local base="$1"
  if [ -z "${DAIMON_INPUT_OWNER:-}" ]; then shortcut_count "$base"; return; fi
  local mention; mention="$(shortcut_mention "$DAIMON_INPUT_OWNER")"
  if [ -z "$mention" ]; then
    echo "discover: could not resolve owner mention for $DAIMON_INPUT_OWNER" >&2
    return 1
  fi
  echo $(( $(shortcut_count "owner:$mention $base") + $(shortcut_count "requester:$mention $base") ))
}

# shortcut_search_ids "<query>" -> one "id updated_at" line per matching story
# (nothing on any error). Gates that must compare stories against a state record
# need ids, not a count. One page of up to 250 results — enough for a gate, which
# only needs to know whether any candidate survives.
shortcut_search_ids() {
  local token; token="$(shortcut_token)"
  [ -z "$token" ] && return
  curl -s -G "https://api.app.shortcut.com/api/v3/search/stories" \
    --data-urlencode "query=$1" --data-urlencode page_size=250 --data-urlencode detail=slim \
    -H "Shortcut-Token: $token" \
    | python3 -c "import sys,json;[print(s['id'],s['updated_at']) for s in json.load(sys.stdin).get('data',[])]" 2>/dev/null
}

# shortcut_owner_ids "<base query>" -> shortcut_search_ids scoped to
# $DAIMON_INPUT_OWNER (owner + requester, deduped), or workspace-wide if OWNER is
# unset. Fails closed like shortcut_owner_count when the mention can't resolve.
shortcut_owner_ids() {
  local base="$1"
  if [ -z "${DAIMON_INPUT_OWNER:-}" ]; then shortcut_search_ids "$base"; return; fi
  local mention; mention="$(shortcut_mention "$DAIMON_INPUT_OWNER")"
  if [ -z "$mention" ]; then
    echo "discover: could not resolve owner mention for $DAIMON_INPUT_OWNER" >&2
    return 1
  fi
  { shortcut_search_ids "owner:$mention $base"; shortcut_search_ids "requester:$mention $base"; } | sort -u
}

# shortcut_labelled_epics "<label>" -> ids of open epics carrying that label, one
# per line (nothing on any error). Stories don't inherit epic labels and the
# story search's label: only matches story labels, so an epic-level opt-in has to
# be resolved to epic ids first.
shortcut_labelled_epics() {
  local token; token="$(shortcut_token)"
  [ -z "$token" ] && return
  curl -s -G "https://api.app.shortcut.com/api/v3/search/epics" \
    --data-urlencode "query=label:\"$1\" !is:done !is:archived" \
    --data-urlencode page_size=250 --data-urlencode detail=slim \
    -H "Shortcut-Token: $token" \
    | python3 -c "import sys,json;[print(e['id']) for e in json.load(sys.stdin).get('data',[])]" 2>/dev/null
}

# shortcut_unseen "<state-file>" -> reads "id updated_at" lines on stdin, prints
# the ids of stories NOT already handled: no record in the state file, or the
# story changed since (updated_at newer than the recorded one). Fractional
# seconds are dropped before comparing so "…28.5Z" vs "…28Z" can't misorder.
shortcut_unseen() {
  local seen="{}"
  if [ -f "$1" ] && jq -e 'type == "object"' "$1" >/dev/null 2>&1; then seen="$(cat "$1")"; fi
  jq -R -r --argjson seen "$seen" '
    def ts: sub("\\.[0-9]+"; "");
    select(length > 0) | split(" ") | .[0] as $id | (.[1] // "" | ts) as $at
    | ($seen[$id].updated_at // "" | ts) as $rec
    | select($rec == "" or $at > $rec) | $id'
}
