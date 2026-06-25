#!/usr/bin/env bash
# Human "next run" display derived from a daemon's configured schedule.

next_run_display() {  # slug -> e.g. "next run ~14:38"
  local slug="$1" desc
  desc="$(cfg schedule "$slug" 2>/dev/null)" || { echo "next run unknown"; return; }
  python3 - "$desc" <<'PY'
import sys, datetime
parts = sys.argv[1].split()
kind = parts[0]
now = datetime.datetime.now()
def fmt(dt): return dt.strftime("%H:%M")
if kind == "interval":
    nxt = now + datetime.timedelta(seconds=int(parts[1]))
    print(f"next run ~{fmt(nxt)} (every {parts[1]}s)")
elif kind == "minutes":
    mins = sorted(int(m) for m in parts[1:])
    cands = [now.replace(minute=m, second=0, microsecond=0) for m in mins]
    cands = [c if c > now else c + datetime.timedelta(hours=1) for c in cands]
    print(f"next run ~{fmt(min(cands))}")
elif kind == "daily":
    hh, mm = parts[1].split(":")
    nxt = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
    if nxt <= now: nxt += datetime.timedelta(days=1)
    print(f"next run ~{fmt(nxt)} daily")
else:
    print("next run unknown")
PY
}
