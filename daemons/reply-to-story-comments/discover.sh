#!/usr/bin/env bash
# Gate for reply-to-story-comments: launch when an owner-scoped story is sitting in
# the awaiting-input state (carries the assist label) — that's the canonical "a
# human reply is expected on a bot comment" signal. Coarse on purpose: the prompt
# does the precise "new human reply after my last bot comment, not yet processed"
# filtering against the state file. Story search comes from the shortcut profile.
set -uo pipefail

source "$(dirname "$0")/../../profiles/shortcut/lib.sh"

base="label:\"$DAIMON_INPUT_ASSIST_LABEL\" !label:\"$DAIMON_INPUT_SKIP_LABEL\""

if [ -z "${DAIMON_INPUT_OWNER:-}" ]; then
  count=$(shortcut_count "$base")
else
  mention="$(shortcut_mention "$DAIMON_INPUT_OWNER")"
  if [ -z "$mention" ]; then
    # An owner is configured but unresolvable: fail closed rather than widen the
    # gate to the whole workspace, which would let the daemon touch others' stories.
    echo "discover: could not resolve owner mention for $DAIMON_INPUT_OWNER" >&2
    exit 1
  fi
  owned=$(shortcut_count "owner:$mention $base")
  requested=$(shortcut_count "requester:$mention $base")
  count=$(( ${owned:-0} + ${requested:-0} ))
fi

[ "${count:-0}" -gt 0 ]
