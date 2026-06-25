"""Programmatic daemon registration. `Daimon` collects DaemonSpecs that
`daimon sync` compiles into daemons/<slug>/ folders."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


def parse_schedule(s) -> dict:
    if isinstance(s, dict):
        return s
    if isinstance(s, str):
        m = re.fullmatch(r"(\d+)([smh])", s)
        if m:
            secs = int(m.group(1)) * {"s": 1, "m": 60, "h": 3600}[m.group(2)]
            return {"interval": secs}
        if re.fullmatch(r"\d{2}:\d{2}", s):
            return {"daily": s}
    raise ValueError(f"bad schedule: {s!r}")


@dataclass
class DaemonSpec:
    slug: str
    fn: Callable
    backend: str = "claude"
    schedule: dict = field(default_factory=lambda: {"interval": 1800})
    command: str = ""
    working_dir: str | None = None
    model: object = None
    danger: bool | None = None
    stuck_after: int | None = None
    inputs: dict = field(default_factory=dict)
    prompt: str | None = None


class Daimon:
    def __init__(self):
        self.specs: dict[str, DaemonSpec] = {}

    def daemon(self, slug: str, *, backend: str = "claude", schedule="30m",
               command: str | None = None, working_dir: str | None = None,
               model=None, danger: bool | None = None, stuck_after: int | None = None,
               inputs: dict | None = None, prompt: str | None = None):
        def deco(fn: Callable) -> Callable:
            self.specs[slug] = DaemonSpec(
                slug=slug, fn=fn, backend=backend,
                schedule=parse_schedule(schedule),
                command=command or f"/{slug}",
                working_dir=working_dir, model=model, danger=danger,
                stuck_after=stuck_after, inputs=inputs or {}, prompt=prompt,
            )
            return fn
        return deco
