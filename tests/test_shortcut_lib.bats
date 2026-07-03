#!/usr/bin/env bats
# Unit tests for the Shortcut source profile's owner-scoping gate helper.
# shortcut_count / shortcut_mention are mocked, so these exercise the scoping and
# fail-closed behaviour without network or a token.

setup() {
  ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  source "$ROOT/profiles/shortcut/lib.sh"
}

@test "shortcut_owner_count: no owner -> workspace count" {
  unset DAIMON_INPUT_OWNER
  shortcut_count() { echo 5; }
  run shortcut_owner_count 'label:"x"'
  [ "$status" -eq 0 ]
  [ "$output" = "5" ]
}

@test "shortcut_owner_count: owner resolves -> owner + requester" {
  export DAIMON_INPUT_OWNER="123"
  shortcut_mention() { echo "me"; }
  shortcut_count() { case "$1" in owner:*) echo 3;; requester:*) echo 2;; *) echo 0;; esac; }
  run shortcut_owner_count 'label:"x"'
  [ "$status" -eq 0 ]
  [ "$output" = "5" ]
}

@test "shortcut_owner_count: owner set but unresolvable -> fails closed with stderr" {
  export DAIMON_INPUT_OWNER="123"
  shortcut_mention() { echo ""; }
  shortcut_count() { echo 99; }  # must NOT be consulted
  run shortcut_owner_count 'label:"x"'
  [ "$status" -eq 1 ]
  [[ "$output" == *"could not resolve owner mention for 123"* ]]
}
