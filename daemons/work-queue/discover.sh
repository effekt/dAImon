#!/usr/bin/env bash
# Gate for work-queue: launch when there's an AI-ready story (labelled, not
# skipped, not already in progress) owned by the configured owner AND open PRs
# are under the cap. Story search comes from the source profile; PR count from
# gh (current repo).
set -uo pipefail

source "$(dirname "$0")/../../profiles/shortcut/lib.sh"

base="label:\"$DAIMON_INPUT_READY_LABEL\" \
  !label:\"$DAIMON_INPUT_SKIP_LABEL\" !state:\"$DAIMON_INPUT_IN_PROGRESS_STATE\""

if [ -z "${DAIMON_INPUT_OWNER:-}" ]; then
  ready=$(shortcut_count "$base")
else
  mention="$(shortcut_mention "$DAIMON_INPUT_OWNER")"
  if [ -z "$mention" ]; then
    # An owner is configured but unresolvable: fail closed rather than widen the
    # gate to the whole workspace, which would let work-queue implement others' stories.
    echo "discover: could not resolve owner mention for $DAIMON_INPUT_OWNER" >&2
    exit 1
  fi
  owned=$(shortcut_count "owner:$mention $base")
  requested=$(shortcut_count "requester:$mention $base")
  ready=$(( ${owned:-0} + ${requested:-0} ))
fi

open_prs=$(gh search prs --author=@me --state=open --json number --jq 'length' 2>/dev/null || echo 0)

[ "${ready:-0}" -gt 0 ] && [ "${open_prs:-0}" -lt "${DAIMON_INPUT_MAX_OPEN_PRS:-2}" ]
