#!/usr/bin/env bash
# Gate for pr-manager: launch when a managed PR needs action — ready to merge
# (approved & green), conflicting, failing CI, change-requested, a green draft
# eligible for self-promotion, or a ready PR still missing its reviewers.
# "Managed" = a PR you authored on a daimon/* branch, or any PR carrying the
# manage label. Runs inside working_dir, so gh targets the current repo. Failing
# closed (no gh, no auth) means "skip", the safe default.
set -uo pipefail

source "$(dirname "$0")/../../profiles/github/lib.sh"

prs="$(gh_pr_json --author @me --state open \
  --json number,headRefName,reviewDecision,mergeable,isDraft,labels,statusCheckRollup,createdAt,reviewRequests,latestReviews)"

printf '%s' "$prs" | jq -e \
  --arg label "$DAIMON_INPUT_MANAGE_LABEL" \
  --arg reviewers "$DAIMON_INPUT_REVIEWERS" \
  --argjson promote "$DAIMON_INPUT_PROMOTE_DRAFTS" \
  --argjson automerge "$DAIMON_INPUT_AUTO_MERGE" \
  --argjson min_age "$DAIMON_INPUT_PROMOTE_MIN_AGE_HOURS" '
  ($reviewers | split(" ") | map(select(. != ""))) as $want
  | def managed: (.headRefName | startswith("daimon/")) or
                 ([.labels[].name] | index($label) != null);
  def checks: (.statusCheckRollup // []);
  def failing: any(checks[]; .conclusion as $c
    | ["FAILURE","CANCELLED","TIMED_OUT","ACTION_REQUIRED","STARTUP_FAILURE"]
    | index($c) != null);
  def pending: any(checks[]; (.conclusion // "") == "");
  def green: ((checks | length) > 0) and (failing | not) and (pending | not);
  def age_hours: (now - (.createdAt | fromdateiso8601)) / 3600;
  def seen: ([.reviewRequests[]?.login] + [.latestReviews[]?.author.login]);
  def actionable_ready: (.isDraft | not) and (
    (.reviewDecision == "APPROVED" and green) or
    ($automerge == 1 and green and .reviewDecision != "CHANGES_REQUESTED"
      and .mergeable != "CONFLICTING") or
    (.reviewDecision == "CHANGES_REQUESTED") or
    (.mergeable == "CONFLICTING") or
    failing);
  def promotable_draft: ($promote == 1) and .isDraft and green
    and (.mergeable != "CONFLICTING")
    and (.reviewDecision != "CHANGES_REQUESTED")
    and (age_hours >= $min_age);
  def needs_reviewers: ($want | length > 0) and (.isDraft | not)
    and (seen as $s | any($want[]; . as $r | $s | index($r) == null));
  [ .[] | select(managed and (actionable_ready or promotable_draft or needs_reviewers)) ]
  | length > 0
' >/dev/null
