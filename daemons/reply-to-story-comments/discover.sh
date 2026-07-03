#!/usr/bin/env bash
# Gate for reply-to-story-comments: launch when an owner-scoped story is sitting in
# the awaiting-input state (carries the assist label) — that's the canonical "a
# human reply is expected on a bot comment" signal. Coarse on purpose: the prompt
# does the precise "new human reply after my last bot comment, not yet processed"
# filtering against the state file. Story search comes from the shortcut profile.
set -uo pipefail

source "$(dirname "$0")/../../profiles/shortcut/lib.sh"

base="label:\"$DAIMON_INPUT_ASSIST_LABEL\" !label:\"$DAIMON_INPUT_SKIP_LABEL\""

count=$(shortcut_owner_count "$base") || exit 1

[ "${count:-0}" -gt 0 ]
