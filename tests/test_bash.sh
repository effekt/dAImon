#!/usr/bin/env bash
# Exercise the bash gate libraries (throttle / budget / inbox) against a temp
# config + state dir. Run from tests/run.sh.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "$TMP/daimon.toml" <<EOF
[core]
install_root = "$ROOT"
state_dir = "$TMP/state"
namespace = "datest"
[defaults]
stuck_after = 100
[throttle]
exempt = ["exempted"]
moderate_mod = 2
severe_mod = 4
[budget]
hourly_cap = 12
defer_at_pct = 80
[daemons]
disabled = []
EOF
export DAIMON_CONFIG="$TMP/daimon.toml"

source "$ROOT/lib/common.sh"
source "$ROOT/lib/budget.sh"
ensure_state_dirs

fails=0
check() { if [ "$1" = "$2" ]; then echo "  ok  $3"; else echo "  FAIL $3 ($1 != $2)"; fails=1; fi }

budget_record foo
budget_record foo
check "$(budget_total_this_hour)" "2" "budget counts launches"

DAEMON_NAME=foo source "$ROOT/lib/throttle.sh"
check "$SHOULD_SKIP" "0" "throttle off -> run"

python3 -c "import json;json.dump({'level':'halt'},open('$TMP/state/runtime/throttle.json','w'))"
DAEMON_NAME=foo source "$ROOT/lib/throttle.sh"
check "$SHOULD_SKIP" "1" "throttle halt -> skip"
DAEMON_NAME=exempted source "$ROOT/lib/throttle.sh"
check "$SHOULD_SKIP" "0" "throttle halt + exempt -> run"

python3 -c "import json;json.dump({'messages':[{'to':'foo'},{'to':'bar'}]},open('$TMP/state/runtime/inbox.json','w'))"
DAEMON_NAME=foo source "$ROOT/lib/inbox.sh"
check "$HAS_INBOX_MESSAGES" "1" "inbox counts messages for daemon"

exit "$fails"
