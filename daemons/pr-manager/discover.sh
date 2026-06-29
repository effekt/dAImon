#!/usr/bin/env bash
# Gate for pr-manager: launch when a managed PR needs action — approved & green
# (ready to merge), conflicting, failing CI, or changes-requested. "Managed" =
# a PR you authored on a daimon/* branch, or any PR carrying the manage label.
# Runs inside working_dir, so gh targets the current repo automatically. Failing
# closed (no gh, no auth) means "skip", which is the safe default.
set -uo pipefail

gh pr list --author @me --state open \
  --json number,headRefName,reviewDecision,mergeable,isDraft,labels,statusCheckRollup \
  2>/dev/null | jq -e --arg label "$DAIMON_INPUT_MANAGE_LABEL" '
  def managed: (.headRefName | startswith("daimon/")) or
               ([.labels[].name] | index($label) != null);
  def checks: (.statusCheckRollup // []);
  def failing: any(checks[]; .conclusion as $c
    | ["FAILURE","CANCELLED","TIMED_OUT","ACTION_REQUIRED","STARTUP_FAILURE"]
    | index($c) != null);
  def pending: any(checks[]; (.conclusion // "") == "");
  def green: ((checks | length) > 0) and (failing | not) and (pending | not);
  def actionable: managed and (.isDraft | not) and (
    (.reviewDecision == "APPROVED" and green) or
    (.reviewDecision == "CHANGES_REQUESTED") or
    (.mergeable == "CONFLICTING") or
    failing);
  [ .[] | select(actionable) ] | length > 0
' >/dev/null
