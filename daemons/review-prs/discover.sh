#!/usr/bin/env bash
# Discovery gate for review-prs. Exit 0 to launch (work found), non-zero to skip.
# Runs inside working_dir, so gh targets the current repo automatically.
set -uo pipefail

count=$(gh pr list --search "$DAIMON_INPUT_FILTER" \
  --json number --jq 'length' 2>/dev/null || echo 0)

[ "${count:-0}" -gt 0 ]
