#!/usr/bin/env bash
# Hourly launch accounting. Sourced after common.sh.

_budget_file() { echo "$(runtime_dir)/hourly-usage.json"; }

budget_record() {  # slug — count one launch in the current hour
  local slug="$1" f; f="$(_budget_file)"
  mkdir -p "$(dirname "$f")"
  python3 - "$f" "$slug" <<'PY'
import json, sys, datetime
path, slug = sys.argv[1], sys.argv[2]
hour = datetime.datetime.now().strftime("%Y-%m-%dT%H")
try: data = json.load(open(path))
except Exception: data = {}
h = data.setdefault(hour, {"total": 0, "by_daemon": {}})
h["total"] += 1
h["by_daemon"][slug] = h["by_daemon"].get(slug, 0) + 1
json.dump(data, open(path, "w"))
PY
}

budget_total_this_hour() {
  python3 - "$(_budget_file)" <<'PY'
import json, sys, datetime
hour = datetime.datetime.now().strftime("%Y-%m-%dT%H")
try: print(json.load(open(sys.argv[1])).get(hour, {}).get("total", 0))
except Exception: print(0)
PY
}

budget_check() {  # sets BUDGET_OVER (0/1) and BUDGET_REASON
  local cap pct total threshold
  cap="$(cfg get budget.hourly_cap)"
  pct="$(cfg get budget.defer_at_pct)"
  total="$(budget_total_this_hour)"
  threshold=$(( cap * pct / 100 ))
  if [ "$total" -ge "$threshold" ]; then
    BUDGET_OVER=1
    BUDGET_REASON="hourly budget: ${total}/${cap} launches (>= ${pct}% cap), deferring"
  else
    BUDGET_OVER=0
    BUDGET_REASON=""
  fi
}
