"""Parse a human schedule string from the config screen into a schedule table.

  "20m" / "1h" / "30s"  -> { interval = N }
  ":8,38"               -> { minutes = [8, 38] }
  "09:02"               -> { daily = "09:02" }
"""
import re

_INTERVAL = re.compile(r"(\d+)([smh])")
_DAILY = re.compile(r"\d{1,2}:\d{2}")


def parse(text: str) -> dict:
    text = text.strip()
    if text.startswith(":"):
        return {"minutes": [int(x) for x in text[1:].split(",") if x.strip()]}
    m = _INTERVAL.fullmatch(text)
    if m:
        return {"interval": int(m.group(1)) * {"s": 1, "m": 60, "h": 3600}[m.group(2)]}
    if _DAILY.fullmatch(text):
        return {"daily": text}
    raise ValueError(f"bad schedule: {text!r}")


def display(sched: dict) -> str:
    if "interval" in sched:
        return f"{sched['interval']}s"
    if "minutes" in sched:
        return ":" + ",".join(str(m) for m in sched["minutes"])
    if "daily" in sched:
        return sched["daily"]
    return ""
