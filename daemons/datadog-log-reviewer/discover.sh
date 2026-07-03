#!/usr/bin/env bash
# Gate for datadog-log-reviewer: fire when the log query matches any events in the
# lookback window. Coarse on purpose — the skill clusters the events and dedupes
# against already-filed clusters ($DAIMON_STATE_FILE), no-opping if all are known,
# so a persistent error already turned into a story doesn't file a duplicate.
# Fails closed (no pup, no auth, bad query) to "skip".
set -uo pipefail

source "$(dirname "$0")/../../profiles/datadog/lib.sh"

[ "$(dd_log_count "$DAIMON_INPUT_LOG_QUERY" "${DAIMON_INPUT_LOOKBACK:-30m}")" -gt 0 ]
