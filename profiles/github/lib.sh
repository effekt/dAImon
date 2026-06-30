#!/usr/bin/env bash
# Shared helpers for the GitHub source profile: PR queries and seen-state loading
# for discovery gates. Pure bash + gh/jq — sourced by a daemon's discover.sh.
# Every helper fails closed (no gh, no auth, bad json) to the "no work" answer.

# gh_pr_json <gh-pr-list-args...> -> a JSON array on stdout ([] on none/failure).
gh_pr_json() {
  local out
  out="$(gh pr list "$@" 2>/dev/null)"
  [ -n "$out" ] && printf '%s' "$out" || printf '[]'
}

# gh_pr_count <gh-pr-list-args...> -> integer count of matching PRs (0 on failure).
gh_pr_count() {
  gh pr list "$@" --json number --jq 'length' 2>/dev/null || echo 0
}

# gh_search_pr_count <gh-search-prs-args...> -> integer count (0 on failure).
gh_search_pr_count() {
  gh search prs "$@" --json number --jq 'length' 2>/dev/null || echo 0
}

# load_seen_state <state-file-path> -> the file's JSON array on stdout, or [] if
# the file is missing or not valid JSON. A daemon's skill writes this record; the
# gate reads it to skip work already handled.
load_seen_state() {
  local f="$1" contents
  [ -f "$f" ] || { printf '[]'; return; }
  contents="$(cat "$f")"
  if printf '%s' "$contents" | jq empty 2>/dev/null; then
    printf '%s' "$contents"
  else
    printf '[]'
  fi
}
