#!/usr/bin/env python3
"""List available models per backend, for setup/config pickers.

Claude queries the live provider API when a key is present, else a bundled
fallback. Codex uses a bundled list plus the model set in `~/.codex/config.toml`.
  Claude: https://platform.claude.com/docs/en/about-claude/models/overview
"""

from __future__ import annotations

import json
import os
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

# Claude daemons pass these to `claude --model`, which accepts aliases or ids.
CLAUDE_FALLBACK = [
    "opus",
    "sonnet",
    "haiku",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]

# Codex daemons pass these to `codex exec -m`.
CODEX_FALLBACK = [
    "gpt-5.5",
    "gpt-5.3-codex",
    "gpt-5.3-codex-spark",
]


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
    models = list(CODEX_FALLBACK)
    configured = _codex_configured_model()
    if configured and configured not in models:
        models.insert(0, configured)
    return models


def _codex_configured_model() -> str | None:
    path = Path(os.path.expanduser("~/.codex/config.toml"))
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh).get("model")
    except (OSError, tomllib.TOMLDecodeError):
        return None


def list_models(backend: str) -> list[str]:
    if backend == "claude":
        return claude_models()
    if backend == "codex":
        return codex_models()
    raise ValueError(f"unknown backend: {backend}")


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in ("claude", "codex"):
        print("usage: models.py claude|codex", file=sys.stderr)
        return 2
    for m in list_models(argv[0]):
        print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
