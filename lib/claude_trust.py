#!/usr/bin/env python3
"""Exit 0 if claude has recorded a trust decision for the given directory.

    claude_trust.py <dir>

Trust lives in ~/.claude.json under projects[<dir>].hasTrustDialogAccepted.
Claude prompts per workspace, so a parent directory trust record is not enough;
an untrusted working_dir makes a claude daemon hang on the first-run trust prompt.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def is_trusted(directory: str) -> bool:
    try:
        with open(os.path.expanduser("~/.claude.json")) as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return False
    projects = data.get("projects", {})
    if not isinstance(projects, dict):
        return False

    path = str(Path(directory).expanduser().resolve())
    project = projects.get(path)
    if isinstance(project, dict) and "hasTrustDialogAccepted" in project:
        return bool(project.get("hasTrustDialogAccepted"))
    return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: claude_trust.py <dir>", file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if is_trusted(sys.argv[1]) else 1)
