#!/usr/bin/env bats
# Unit tests for the Shortcut source profile's owner-scoping gate helper.
# shortcut_count / shortcut_mention are mocked, so these exercise the scoping and
# fail-closed behaviour without network or a token.

setup() {
  ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
  source "$ROOT/profiles/shortcut/lib.sh"
}

@test "shortcut_exclusions: unset -> empty" {
  unset DAIMON_INPUT_EXCLUDE_EPICS
  run shortcut_exclusions
  [ "$status" -eq 0 ]
  [ "$output" = "" ]
}

@test "shortcut_exclusions: one epic -> one negated term" {
  export DAIMON_INPUT_EXCLUDE_EPICS="1234"
  run shortcut_exclusions
  [ "$output" = " !epic:1234" ]
}

@test "shortcut_exclusions: several epics -> one term each" {
  export DAIMON_INPUT_EXCLUDE_EPICS="1234 5678"
  run shortcut_exclusions
  [ "$output" = " !epic:1234 !epic:5678" ]
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

@test "shortcut_owner_ids: owner + requester merged and deduped" {
  export DAIMON_INPUT_OWNER="123"
  shortcut_mention() { echo "me"; }
  shortcut_search_ids() { case "$1" in owner:*) printf '1 a\n2 b\n';; requester:*) printf '2 b\n3 c\n';; esac; }
  run shortcut_owner_ids 'label:"x"'
  [ "$status" -eq 0 ]
  [ "$output" = "$(printf '1 a\n2 b\n3 c')" ]
}

@test "shortcut_owner_ids: owner set but unresolvable -> fails closed" {
  export DAIMON_INPUT_OWNER="123"
  shortcut_mention() { echo ""; }
  shortcut_search_ids() { echo "1 a"; }  # must NOT be consulted
  run shortcut_owner_ids 'label:"x"'
  [ "$status" -eq 1 ]
  [[ "$output" == *"could not resolve owner mention"* ]]
}

@test "shortcut_unseen: drops recorded-and-unchanged, keeps new and changed" {
  f="$BATS_TEST_TMPDIR/state.json"
  echo '{"1":{"updated_at":"2026-03-14T08:15:30Z"},"2":{"updated_at":"2026-10-01T00:00:00Z"}}' > "$f"
  run shortcut_unseen "$f" <<< "$(printf '1 2026-03-14T08:15:30Z\n2 2026-10-02T09:00:00Z\n3 2026-10-03T00:00:00Z')"
  [ "$status" -eq 0 ]
  [ "$output" = "$(printf '2\n3')" ]
}

@test "shortcut_unseen: fractional seconds compare as the same instant" {
  f="$BATS_TEST_TMPDIR/state.json"
  echo '{"1":{"updated_at":"2026-03-14T08:15:30Z"}}' > "$f"
  run shortcut_unseen "$f" <<< "1 2026-03-14T08:15:30.512Z"
  [ "$output" = "" ]
}

@test "shortcut_unseen: missing or array state file -> everything is unseen" {
  run shortcut_unseen "$BATS_TEST_TMPDIR/nope.json" <<< "7 2026-01-01T00:00:00Z"
  [ "$output" = "7" ]
  f="$BATS_TEST_TMPDIR/arr.json"; echo '[]' > "$f"
  run shortcut_unseen "$f" <<< "7 2026-01-01T00:00:00Z"
  [ "$output" = "7" ]
}
