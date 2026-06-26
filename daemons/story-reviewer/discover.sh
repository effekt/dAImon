#!/usr/bin/env bash
# Gate for story-reviewer: launch when there are un-assessed stories in triage
# (no assessment label yet, not skipped) that belong to the configured owner.
set -uo pipefail

source "$(dirname "$0")/../../profiles/shortcut/lib.sh"

base="state:\"$DAIMON_INPUT_TRIAGE_STATE\" \
  !label:\"$DAIMON_INPUT_READY_LABEL\" !label:\"$DAIMON_INPUT_ASSIST_LABEL\" \
  !label:\"$DAIMON_INPUT_HUMAN_LABEL\" !label:\"$DAIMON_INPUT_SKIP_LABEL\""

if [ -z "${DAIMON_INPUT_OWNER:-}" ]; then
  count=$(shortcut_count "$base")
else
  mention="$(shortcut_mention "$DAIMON_INPUT_OWNER")"
  if [ -z "$mention" ]; then
    # An owner is configured but unresolvable: fail closed rather than widen the
    # gate to the whole workspace, which is what let the reviewer touch others' stories.
    echo "discover: could not resolve owner mention for $DAIMON_INPUT_OWNER" >&2
    exit 1
  fi
  owned=$(shortcut_count "owner:$mention $base")
  requested=$(shortcut_count "requester:$mention $base")
  count=$(( ${owned:-0} + ${requested:-0} ))
fi

[ "${count:-0}" -gt 0 ]
