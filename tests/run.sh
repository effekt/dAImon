#!/usr/bin/env bash
# Run the full dAImon test suite: bash syntax checks + Python unit tests.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

echo "== bash syntax =="
while IFS= read -r f; do
  if bash -n "$f"; then echo "  ok  $f"; else echo "  FAIL $f"; fail=1; fi
done < <(find "$ROOT/lib" "$ROOT/backends" "$ROOT/daemons" -name '*.sh')

echo "== python unit tests =="
( cd "$ROOT" && python3 -m unittest discover -s tests -p 'test_*.py' -v ) || fail=1

echo "== bash gate tests =="
bash "$ROOT/tests/test_bash.sh" || fail=1

exit "$fail"
