#!/usr/bin/env python3
"""Idempotently merge dAImon's agent hooks into a settings file.

usage: install_hooks.py <settings.json> <hooks.json>
Backs up the settings file, then appends our hook entries to each event only if
an entry referencing $DAIMON_ is not already present.
"""
import json
import shutil
import sys
from pathlib import Path

MARKER = "$DAIMON_"


def _has_marker(entries) -> bool:
    return any(
        MARKER in h.get("command", "")
        for entry in entries
        for h in entry.get("hooks", [])
    )


def main(argv):
    settings_path = Path(argv[0])
    hooks = json.loads(Path(argv[1]).read_text())

    settings = {}
    if settings_path.exists():
        settings = json.loads(settings_path.read_text())
        shutil.copy(settings_path, str(settings_path) + ".daimon-bak")

    settings.setdefault("hooks", {})
    added = 0
    for event, entries in hooks.items():
        existing = settings["hooks"].setdefault(event, [])
        if _has_marker(existing):
            continue
        existing.extend(entries)
        added += 1

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"hooks: merged {added} event(s) into {settings_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
