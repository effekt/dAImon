#!/usr/bin/env bash
# Show (or clear) a daemon's durable work-tracking record.
# usage: state-show.sh <slug> [--clear]
set -uo pipefail
DAIMON_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$DAIMON_LIB_DIR/common.sh"

SLUG="${1:?usage: state-show.sh <slug> [--clear]}"
FILE="$(state_file "$SLUG")"

if [ "${2:-}" = "--clear" ]; then
  rm -f "$FILE" && echo "cleared $FILE"
  exit 0
fi

if [ -f "$FILE" ]; then
  cat "$FILE"
else
  echo "(no state yet for $SLUG — $FILE)"
fi
