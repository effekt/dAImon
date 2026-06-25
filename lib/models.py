#!/usr/bin/env python3
"""List available models per backend, for setup/config pickers.

Queries the live provider API when a key is present, otherwise returns a bundled
fallback. Authoritative sources:
  Claude: https://platform.claude.com/docs/en/about-claude/models/overview
  Codex:  https://developers.openai.com/codex/models
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# Claude daemons pass these to `claude --model`, which accepts aliases or ids.
CLAUDE_FALLBACK = ["opus", "sonnet", "haiku",
                   "claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5"]
CODEX_FALLBACK = ["gpt-5-codex", "gpt-5", "gpt-5-mini", "o4-mini"]


def _get_json(url: str, headers: dict, timeout: float = 6.0):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def claude_models() -> list[str]:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            data = _get_json(
                "https://api.anthropic.com/v1/models?limit=100",
                {"x-api-key": key, "anthropic-version": "2023-06-01"},
            )
            ids = [m["id"] for m in data.get("data", [])]
            if ids:
                return ["opus", "sonnet", "haiku"] + ids
        except (urllib.error.URLError, KeyError, TimeoutError, OSError):
            pass
    return CLAUDE_FALLBACK


def codex_models() -> list[str]:
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        try:
            data = _get_json(
                "https://api.openai.com/v1/models",
                {"Authorization": f"Bearer {key}"},
            )
            ids = [m["id"] for m in data.get("data", [])
                   if any(t in m["id"] for t in ("gpt-5", "codex", "o4", "o3"))]
            if ids:
                return sorted(set(ids))
        except (urllib.error.URLError, KeyError, TimeoutError, OSError):
            pass
    return CODEX_FALLBACK


def list_models(backend: str) -> list[str]:
    if backend == "claude":
        return claude_models()
    if backend == "codex":
        return codex_models()
    raise ValueError(f"unknown backend: {backend}")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in ("claude", "codex"):
        print("usage: models.py <claude|codex>", file=sys.stderr)
        return 2
    for m in list_models(argv[0]):
        print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
