#!/usr/bin/env bash
# Gate for work-queue: launch when there's an AI-ready story (labelled, not
# skipped, not already in progress) AND open PRs are under the cap. Story search
# comes from the source profile; PR count from gh (current repo).
set -uo pipefail

source "$(dirname "$0")/../../profiles/shortcut/lib.sh"

ready=$(shortcut_count "label:\"$DAIMON_INPUT_READY_LABEL\" \
  !label:\"$DAIMON_INPUT_SKIP_LABEL\" !state:\"$DAIMON_INPUT_IN_PROGRESS_STATE\"")
open_prs=$(gh search prs --author=@me --state=open --json number --jq 'length' 2>/dev/null || echo 0)

[ "${ready:-0}" -gt 0 ] && [ "${open_prs:-0}" -lt "${DAIMON_INPUT_MAX_OPEN_PRS:-2}" ]
