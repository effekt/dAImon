#!/usr/bin/env bats
# Unit tests for the GitHub source profile's gate helpers. gh is mocked, so these
# exercise the fail-closed and pass-through behaviour without network or auth.

setup() {
  ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  source "$ROOT/profiles/github/lib.sh"
}

@test "load_seen_state: missing file -> []" {
  run load_seen_state "$BATS_TEST_TMPDIR/nope.json"
  [ "$output" = "[]" ]
}

@test "load_seen_state: invalid json -> []" {
  printf 'not json {' > "$BATS_TEST_TMPDIR/s.json"
  run load_seen_state "$BATS_TEST_TMPDIR/s.json"
  [ "$output" = "[]" ]
}

@test "load_seen_state: valid json -> contents" {
  printf '[{"number":1,"headSha":"abc"}]' > "$BATS_TEST_TMPDIR/s.json"
  run load_seen_state "$BATS_TEST_TMPDIR/s.json"
  [ "$output" = '[{"number":1,"headSha":"abc"}]' ]
}

@test "gh_pr_json: gh failure -> []" {
  gh() { return 1; }
  run gh_pr_json --state open
  [ "$output" = "[]" ]
}

@test "gh_pr_json: empty output -> []" {
  gh() { printf ''; }
  run gh_pr_json --state open
  [ "$output" = "[]" ]
}

@test "gh_pr_json: passes json through" {
  gh() { printf '[{"number":7}]'; }
  run gh_pr_json --state open
  [ "$output" = '[{"number":7}]' ]
}

@test "gh_pr_count: gh failure -> 0" {
  gh() { return 1; }
  run gh_pr_count --state open
  [ "$output" = "0" ]
}

@test "gh_pr_count: returns gh's count" {
  gh() { printf '3'; }
  run gh_pr_count --state open
  [ "$output" = "3" ]
}

@test "gh_search_pr_count: gh failure -> 0" {
  gh() { return 1; }
  run gh_search_pr_count --author=@me --state=open
  [ "$output" = "0" ]
}
