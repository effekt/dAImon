"""The one owner of schedule format conversions, shared by the config core and
the TUI.

A schedule is a dict in one of three shapes:
    {"interval": 1200}              every N seconds
    {"minutes": [8, 38]}            at these minutes past each hour
    {"daily": "09:02", "tz": ...}   once a day at HH:MM

Human string form (TUI input/display):
    "20m" / "1h" / "30s"  <-> {"interval": N}
    ":8,38"               <-> {"minutes": [8, 38]}
    "09:02"               <-> {"daily": "09:02"}
"""
import re

_INTERVAL = re.compile(r"(\d+)([smh])")
_DAILY = re.compile(r"\d{1,2}:\d{2}")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600}


def parse(text: str) -> dict:
    text = text.strip()
    if text.startswith(":"):
        return {"minutes": [int(x) for x in text[1:].split(",") if x.strip()]}
    m = _INTERVAL.fullmatch(text)
    if m:
        return {"interval": int(m.group(1)) * _UNIT_SECONDS[m.group(2)]}
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


def descriptor(sched: dict) -> str:
    if "interval" in sched:
        return f"interval {int(sched['interval'])}"
    if "minutes" in sched:
        return "minutes " + " ".join(str(int(m)) for m in sched["minutes"])
    if "daily" in sched:
        return f"daily {sched['daily']} {sched.get('tz', 'local')}"
    raise ValueError(f"unrecognized schedule: {sched}")


def to_plist(sched: dict) -> str:
    if "interval" in sched:
        return f"    <key>StartInterval</key>\n    <integer>{int(sched['interval'])}</integer>"
    if "minutes" in sched:
        entries = "\n".join(
            f"        <dict><key>Minute</key><integer>{int(m)}</integer></dict>"
            for m in sched["minutes"]
        )
        return f"    <key>StartCalendarInterval</key>\n    <array>\n{entries}\n    </array>"
    if "daily" in sched:
        hh, mm = sched["daily"].split(":")
        return (
            "    <key>StartCalendarInterval</key>\n    <dict>"
            f"<key>Hour</key><integer>{int(hh)}</integer>"
            f"<key>Minute</key><integer>{int(mm)}</integer></dict>"
        )
    raise ValueError(f"unrecognized schedule: {sched}")
