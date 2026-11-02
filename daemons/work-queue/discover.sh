#!/usr/bin/env bash
# Gate for work-queue: launch when there's an AI-ready story (labelled, not
# skipped, not already in progress, not done) owned by the configured owner AND
# the queue's own open PRs are under the cap. Story search comes from the source
# profile. The PR cap counts only daimon/* branches in the current repo
# (working_dir), so hand-authored PRs — and stale PRs in unrelated repos — never
# starve the queue.
set -uo pipefail

source "$(dirname "$0")/../../profiles/shortcut/lib.sh"
source "$(dirname "$0")/../../profiles/github/lib.sh"

base="label:\"$DAIMON_INPUT_READY_LABEL\" \
  !label:\"$DAIMON_INPUT_SKIP_LABEL\" !state:\"$DAIMON_INPUT_IN_PROGRESS_STATE\" \
  !is:done !is:archived\
$(shortcut_exclusions)"

ready=$(shortcut_owner_count "$base") || exit 1

open_prs=$(gh_pr_json --author @me --state open --json headRefName \
  | jq '[.[] | select(.headRefName | startswith("daimon/"))] | length' 2>/dev/null)

[ "${ready:-0}" -gt 0 ] && [ "${open_prs:-0}" -lt "${DAIMON_INPUT_MAX_OPEN_PRS:-2}" ]
