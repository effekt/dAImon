#!/usr/bin/env bash
# Discovery gate for review-prs. Exit 0 to launch (work found), non-zero to skip.
# Fires only for a PR matching the filter that hasn't already been reviewed at its
# current head commit — the skill records reviewed PRs as {number, headSha} in the
# state file, and we skip those. This keeps the gate cheap at a tight cadence: a
# review-requested PR that lingers (flag not cleared) won't relaunch the agent every
# tick. Runs inside working_dir, so gh targets the current repo automatically.
set -uo pipefail

source "$(dirname "$0")/../../lib/common.sh"

seen='[]'
state="$(state_file review-prs)"
if [ -f "$state" ]; then
  contents="$(cat "$state")"
  echo "$contents" | jq empty 2>/dev/null && seen="$contents"
fi

prs="$(gh pr list --search "$DAIMON_INPUT_FILTER" --json number,headRefOid 2>/dev/null)"
[ -z "$prs" ] && prs='[]'

printf '%s' "$prs" | jq -e --argjson seen "$seen" '
  [ .[] | select(. as $p
    | ($seen | any((.number == $p.number) and (.headSha == $p.headRefOid))) | not)
  ] | length > 0
' >/dev/null
