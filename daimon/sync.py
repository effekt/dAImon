"""Regenerate launchd plists and render daemon skills from the daemon folders.
Run via `daimon sync` or `python -m daimon.sync`."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

INSTALL_ROOT = Path(__file__).resolve().parent.parent


def _import_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def materialize(cfg_mod):
    cfg = cfg_mod.Config.load()
    skills_root = Path(os.path.expanduser("~/.claude/skills"))
    agents = Path(os.path.expanduser("~/Library/LaunchAgents"))
    ns = cfg.core["namespace"]
    for slug in cfg.discover():
        cmd = cfg.daemon(slug)["command"].lstrip("/")
        sd = skills_root / cmd
        sd.mkdir(parents=True, exist_ok=True)
        (sd / "SKILL.md").write_text(cfg_mod.render_skill(cfg, slug))
        if agents.is_dir():
            (agents / f"com.{ns}.{slug}.plist").write_text(cfg_mod.render_plist(cfg, slug))
    if agents.is_dir():
        (agents / f"com.{ns}.watchdog.plist").write_text(cfg_mod.render_watchdog_plist(cfg))
    return cfg


def main(argv: list[str]) -> int:
    cfg_mod = _import_from_path("daimon_config", INSTALL_ROOT / "lib" / "config.py")
    errs = cfg_mod.validate(cfg_mod.Config.load())
    if errs:
        print("config INVALID after sync:", *(f"  - {e}" for e in errs), sep="\n", file=sys.stderr)
        return 1
    cfg = materialize(cfg_mod)
    print(f"synced {len(cfg.discover())} daemon(s): plists + skills regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
