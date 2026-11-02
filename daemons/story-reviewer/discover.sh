#!/usr/bin/env bash
# Gate for story-reviewer: launch when an un-assessed story belonging to the
# configured owner sits in the intake and hasn't already been reviewed unchanged.
#
# Intake (union, each owner-scoped, open, not skipped, no assessment label yet):
#   1. stories in the triage state;
#   2. stories carrying any of $DAIMON_INPUT_INTAKE_LABELS (any state but
#      in-progress), minus those carrying any $DAIMON_INPUT_INTAKE_EXCLUDE_LABELS;
#   3. every story in an open epic labelled with the ready label (epic opt-in).
#
# A story already recorded in the state file with the same updated_at is dropped:
# the skill reviewed it and nothing changed since (e.g. a human removed the
# label on purpose). Without that, such a story keeps the gate open every run.
set -uo pipefail

source "$(dirname "$0")/../../lib/common.sh"
source "$(dirname "$0")/../../profiles/shortcut/lib.sh"

open="!label:\"$DAIMON_INPUT_READY_LABEL\" !label:\"$DAIMON_INPUT_ASSIST_LABEL\" \
  !label:\"$DAIMON_INPUT_HUMAN_LABEL\" !label:\"$DAIMON_INPUT_SKIP_LABEL\" \
  !is:done !is:archived$(shortcut_exclusions)"
active="$open !state:\"$DAIMON_INPUT_IN_PROGRESS_STATE\""

drop=""
for l in ${DAIMON_INPUT_INTAKE_EXCLUDE_LABELS:-}; do drop="$drop !label:\"$l\""; done

candidates="$(
  {
    shortcut_owner_ids "state:\"$DAIMON_INPUT_TRIAGE_STATE\" $open" || exit 1
    for l in ${DAIMON_INPUT_INTAKE_LABELS:-}; do
      shortcut_owner_ids "label:\"$l\" $active$drop" || exit 1
    done
    for e in $(shortcut_labelled_epics "$DAIMON_INPUT_READY_LABEL"); do
      shortcut_owner_ids "epic:$e $active" || exit 1
    done
  } | sort -u
)" || exit 1

[ -n "$(printf '%s\n' "$candidates" | shortcut_unseen "$(state_file story-reviewer)")" ]
