"""Discovery-gate context handed to a registered daemon function. The function
returns truthy to launch the agent, falsy to skip this fire."""
from __future__ import annotations

import subprocess


class Ctx:
    def __init__(self, inputs: dict):
        self.inputs = inputs

    def sh(self, *cmd: str) -> str:
        try:
            return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    def gh_count(self, search: str, repo: str | None = None, kind: str = "pr") -> int:
        repo = repo or self.inputs.get("repo", "")
        out = self.sh("gh", kind, "list", "--repo", repo, "--search", search,
                      "--json", "number", "--jq", "length")
        return int(out) if out.isdigit() else 0
