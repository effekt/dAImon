#!/usr/bin/env bash
# Discovery gate for reply-to-comments. Exit 0 to launch, non-zero to skip.
# Coarse gate: launch when any open PR exists; the prompt does the precise
# "new human reply to a bot comment" filtering. gh targets the current repo.
set -uo pipefail

count=$(gh pr list --state open --json number --jq 'length' 2>/dev/null || echo 0)

[ "${count:-0}" -gt 0 ]
