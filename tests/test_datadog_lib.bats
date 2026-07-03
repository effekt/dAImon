#!/usr/bin/env bats
# Unit tests for the Datadog source profile's gate helpers. `pup` is mocked, so
# these exercise the envelope-unwrapping and fail-closed behaviour without the CLI,
# auth, or network.

setup() {
  ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  source "$ROOT/profiles/datadog/lib.sh"
}

@test "dd_log_count: {data:[...]} envelope -> count of data" {
  pup() { printf '{"data":[{"id":1},{"id":2},{"id":3}],"meta":{}}'; }
  run dd_log_count "status:error" "30m"
  [ "$output" = "3" ]
}

@test "dd_log_count: bare array -> its length" {
  pup() { printf '[{"id":1},{"id":2}]'; }
  run dd_log_count "status:error" "30m"
  [ "$output" = "2" ]
}

@test "dd_log_count: empty result -> 0" {
  pup() { printf '{"data":[]}'; }
  run dd_log_count "status:error" "30m"
  [ "$output" = "0" ]
}

@test "dd_log_count: pup failure -> 0" {
  pup() { return 1; }
  run dd_log_count "status:error" "30m"
  [ "$output" = "0" ]
}

@test "dd_log_count: non-json output -> 0" {
  pup() { printf 'error: not authenticated'; }
  run dd_log_count "status:error" "30m"
  [ "$output" = "0" ]
}

@test "dd_log_json: pup failure -> []" {
  pup() { return 1; }
  run dd_log_json "status:error" "30m"
  [ "$output" = "[]" ]
}
