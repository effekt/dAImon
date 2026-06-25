#!/usr/bin/env python3
"""Single source of truth for dAImon config: load, merge, validate, render.

All other components (bash libs, the TUI, the installer) shell out to this rather
than parse TOML themselves, so defaults/merge/validation live in exactly one place.
"""
from __future__ import annotations

import argparse
import os
import shlex
import sys
import tomllib
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
import toml_emit  # noqa: E402

BACKENDS = ("claude", "codex", "both")

CORE_DEFAULTS = {
    "namespace": "daimon",
    "state_dir": "~/.local/state/daimon",
    "timezone": "UTC",
    "log_retention_days": 14,
    "log_max_mb": 10,
    "log_keep": 3,
}
DEFAULT_DEFAULTS = {
    "backend": "claude",
    "model": "opus",
    "danger": True,
    "stuck_after": 2700,
    "ready_timeout": 20,
}
THROTTLE_DEFAULTS = {
    "exempt": [],
    "moderate_mod": 2,
    "severe_mod": 4,
    "severe_critical": [],
}
BUDGET_DEFAULTS = {"hourly_cap": 12, "defer_at_pct": 80}

DAEMON_FIELDS = ("backend", "model", "danger", "stuck_after", "command", "schedule")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def expand(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve() if p else p


def global_config_path() -> Path:
    env = os.environ.get("DAIMON_CONFIG")
    if env:
        return Path(os.path.expanduser(env))
    return Path(os.path.expanduser("~/.config/daimon/daimon.toml"))


def _load_toml(path: Path) -> dict:
    with open(path, "rb") as fh:
        return tomllib.load(fh)


class Config:
    def __init__(self, raw: dict, source: Path | None):
        self.source = source
        self.core = {**CORE_DEFAULTS, **raw.get("core", {})}
        self.defaults = {**DEFAULT_DEFAULTS, **raw.get("defaults", {})}
        self.throttle = {**THROTTLE_DEFAULTS, **raw.get("throttle", {})}
        self.budget = {**BUDGET_DEFAULTS, **raw.get("budget", {})}
        self.disabled = list(raw.get("daemons", {}).get("disabled", []))
        if "install_root" in self.core:
            self.install_root = expand(self.core["install_root"])
        else:
            self.install_root = repo_root()
        self.state_dir = expand(self.core["state_dir"])

    @classmethod
    def load(cls) -> "Config":
        path = global_config_path()
        raw = _load_toml(path) if path.exists() else {}
        return cls(raw, path if path.exists() else None)

    def daemons_dir(self) -> Path:
        return self.install_root / "daemons"

    def discover(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        ddir = self.daemons_dir()
        if not ddir.is_dir():
            return out
        for cfg in sorted(ddir.glob("*/daemon.toml")):
            slug = cfg.parent.name
            if slug in self.disabled:
                continue
            out[slug] = _load_toml(cfg)
        return out

    def profiles_dir(self) -> Path:
        return self.install_root / "profiles"

    def load_profile(self, name: str) -> dict | None:
        path = self.profiles_dir() / name / "profile.toml"
        if not path.exists():
            return None
        prof = _load_toml(path)
        local = self.profiles_dir() / name / "profile.local.toml"
        if local.exists():
            prof.setdefault("defaults", {}).update(_load_toml(local).get("defaults", {}))
        return prof

    def daemon_local_path(self, slug: str) -> Path:
        return self.daemons_dir() / slug / "daemon.local.toml"

    def raw_daemon(self, slug: str) -> dict:
        raw = self.discover().get(slug, {})
        d, i = dict(raw.get("daemon", {})), dict(raw.get("inputs", {}))
        lp = self.daemon_local_path(slug)
        if lp.exists():
            local = _load_toml(lp)
            d.update(local.get("daemon", {}))
            i.update(local.get("inputs", {}))
        return {"daemon": d, "inputs": i}

    def daemon(self, slug: str) -> dict:
        if self.discover().get(slug) is None:
            raise KeyError(f"unknown daemon: {slug}")
        raw = self.raw_daemon(slug)
        merged = dict(self.defaults)
        merged.update(raw["daemon"])
        source = merged.get("source", "")
        prof = self.load_profile(source) if source else None
        inputs = dict(prof.get("defaults", {})) if prof else {}
        inputs.update(raw["inputs"])
        merged["inputs"] = inputs
        merged["source"] = source
        merged["slug"] = slug
        wd = merged.get("working_dir")
        merged["working_dir"] = str(expand(wd)) if wd else str(self.install_root)
        return merged

    def backends(self, slug: str) -> list[str]:
        b = self.daemon(slug)["backend"]
        return ["claude", "codex"] if b == "both" else [b]

    def model_for(self, slug: str, backend: str) -> str:
        m = self.daemon(slug)["model"]
        if isinstance(m, dict):
            return m.get(backend) or m.get("default") or ""
        return m

    def daemon_toml_path(self, slug: str) -> Path:
        return self.daemons_dir() / slug / "daemon.toml"

    def _merge_write(self, path: Path, daemon: dict, inputs: dict | None) -> None:
        raw = _load_toml(path) if path.exists() else {}
        raw.setdefault("daemon", {}).update(daemon)
        if inputs is not None:
            raw["inputs"] = inputs
        path.write_text(toml_emit.dump_sections(
            {"daemon": raw.get("daemon", {}), "inputs": raw.get("inputs", {})}))

    def update_daemon_field(self, slug: str, field: str, value) -> None:
        self._merge_write(self.daemon_toml_path(slug), {field: value}, None)

    def update_local(self, slug: str, daemon: dict, inputs: dict | None = None) -> None:
        self._merge_write(self.daemon_local_path(slug), daemon, inputs)


def _schedule_to_plist(sched: dict) -> str:
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


def schedule_descriptor(sched: dict) -> str:
    if "interval" in sched:
        return f"interval {int(sched['interval'])}"
    if "minutes" in sched:
        return "minutes " + " ".join(str(int(m)) for m in sched["minutes"])
    if "daily" in sched:
        return f"daily {sched['daily']} {sched.get('tz', 'local')}"
    raise ValueError(f"unrecognized schedule: {sched}")


def render_plist(cfg: Config, slug: str) -> str:
    d = cfg.daemon(slug)
    return render_plist_raw(
        label=f"com.{cfg.core['namespace']}.{slug}",
        program=[str(cfg.install_root / "lib" / "run.sh"), slug],
        working_dir=d["working_dir"],
        schedule_xml=_schedule_to_plist(d["schedule"]),
        log=str(cfg.state_dir / "logs" / f"{slug}.log"),
    )


def render_watchdog_plist(cfg: Config) -> str:
    return render_plist_raw(
        label=f"com.{cfg.core['namespace']}.watchdog",
        program=[str(cfg.install_root / "lib" / "watchdog.sh")],
        working_dir=str(cfg.install_root),
        schedule_xml="    <key>StartInterval</key>\n    <integer>300</integer>",
        log=str(cfg.state_dir / "logs" / "watchdog.log"),
    )


def render_plist_raw(label, program, working_dir, schedule_xml, log) -> str:
    args = "\n".join(f"        <string>{escape(a)}</string>" for a in program)
    env_xml = "\n".join(
        f"        <key>{k}</key>\n        <string>{escape(os.environ[k])}</string>"
        for k in ("PATH", "HOME", "SSH_AUTH_SOCK") if os.environ.get(k))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
{args}
    </array>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
{schedule_xml}
    <key>StandardOutPath</key>
    <string>{log}</string>
    <key>StandardErrorPath</key>
    <string>{log}</string>
    <key>EnvironmentVariables</key>
    <dict>
{env_xml}
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
"""


def render_skill(cfg: Config, slug: str) -> str:
    d = cfg.daemon(slug)
    text = (cfg.daemons_dir() / slug / "skill" / "SKILL.md").read_text()
    source = d.get("source")
    if source:
        ref = cfg.profiles_dir() / source / "reference.md"
        if ref.exists():
            text += f"\n\n---\n\n{ref.read_text()}"
    for key, val in d["inputs"].items():
        rendered = ", ".join(str(x) for x in val) if isinstance(val, list) else str(val)
        text = text.replace(f"{{{{inputs.{key}}}}}", rendered)
    return text


def validate(cfg: Config) -> list[str]:
    errors: list[str] = []
    if cfg.source is None:
        errors.append(f"no config file at {global_config_path()} (copy config/daimon.toml.example)")
    if cfg.defaults["backend"] not in BACKENDS:
        errors.append(f"[defaults].backend must be one of {BACKENDS}")
    daemons = cfg.discover()
    if not daemons:
        errors.append(f"no daemons discovered under {cfg.daemons_dir()}")
    for slug, raw in daemons.items():
        d = raw.get("daemon", {})
        be = d.get("backend", cfg.defaults["backend"])
        if be not in BACKENDS:
            errors.append(f"{slug}: backend must be one of {BACKENDS}")
        cmd = d.get("command")
        if not cmd or not str(cmd).startswith("/"):
            errors.append(f"{slug}: [daemon].command must be set and start with '/'")
        sched = d.get("schedule")
        if not sched:
            errors.append(f"{slug}: [daemon].schedule is required")
        else:
            try:
                schedule_descriptor(sched)
            except ValueError as e:
                errors.append(f"{slug}: {e}")
        skill = cfg.daemons_dir() / slug / "skill" / "SKILL.md"
        if not skill.exists():
            errors.append(f"{slug}: missing skill/SKILL.md")
        source = d.get("source")
        if source and cfg.load_profile(source) is None:
            errors.append(f"{slug}: unknown source profile '{source}' (no profiles/{source}/profile.toml)")
    for slug in cfg.disabled:
        if slug not in {p.parent.name for p in cfg.daemons_dir().glob("*/daemon.toml")}:
            errors.append(f"[daemons].disabled references unknown daemon: {slug}")
    return errors


def _emit(value) -> str:
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, list):
        return " ".join(str(v) for v in value)
    return str(value)


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="daimon-config")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("get"); g.add_argument("key")
    d = sub.add_parser("daemon"); d.add_argument("slug"); d.add_argument("field")
    i = sub.add_parser("input"); i.add_argument("slug"); i.add_argument("key")
    sub.add_parser("daemons")
    b = sub.add_parser("backends"); b.add_argument("slug")
    m = sub.add_parser("model"); m.add_argument("slug"); m.add_argument("backend")
    s = sub.add_parser("schedule"); s.add_argument("slug")
    e = sub.add_parser("env"); e.add_argument("slug")
    sub.add_parser("validate")
    rp = sub.add_parser("render-plist"); rp.add_argument("slug")
    rs = sub.add_parser("render-skill"); rs.add_argument("slug")
    sub.add_parser("paths")
    args = p.parse_args(argv)
    cfg = Config.load()

    if args.cmd == "get":
        section, _, field = args.key.partition(".")
        table = {"core": cfg.core, "defaults": cfg.defaults,
                 "throttle": cfg.throttle, "budget": cfg.budget}.get(section)
        if table is None or field not in table:
            print(f"unknown key: {args.key}", file=sys.stderr); return 2
        print(_emit(table[field])); return 0
    if args.cmd == "daemon":
        print(_emit(cfg.daemon(args.slug)[args.field])); return 0
    if args.cmd == "input":
        print(_emit(cfg.daemon(args.slug)["inputs"].get(args.key, ""))); return 0
    if args.cmd == "daemons":
        print("\n".join(cfg.discover().keys())); return 0
    if args.cmd == "backends":
        print(" ".join(cfg.backends(args.slug))); return 0
    if args.cmd == "model":
        print(cfg.model_for(args.slug, args.backend)); return 0
    if args.cmd == "schedule":
        print(schedule_descriptor(cfg.daemon(args.slug)["schedule"])); return 0
    if args.cmd == "env":
        # Output is eval'd by run.sh (set -a), so each value must be shell-quoted
        # or input values containing spaces (e.g. "In Progress") break the eval.
        for k, v in cfg.daemon(args.slug)["inputs"].items():
            print(f"DAIMON_INPUT_{k.upper()}={shlex.quote(_emit(v))}")
        return 0
    if args.cmd == "validate":
        errs = validate(cfg)
        if errs:
            print("config INVALID:", file=sys.stderr)
            for er in errs:
                print(f"  - {er}", file=sys.stderr)
            return 1
        print(f"config OK ({len(cfg.discover())} daemon(s))"); return 0
    if args.cmd == "render-plist":
        print(render_plist(cfg, args.slug), end=""); return 0
    if args.cmd == "render-skill":
        print(render_skill(cfg, args.slug), end=""); return 0
    if args.cmd == "paths":
        print(f"DAIMON_INSTALL_ROOT='{cfg.install_root}'")
        print(f"DAIMON_STATE_DIR='{cfg.state_dir}'")
        print(f"DAIMON_NS='{cfg.core['namespace']}'")
        print(f"DAIMON_TIMEZONE='{cfg.core['timezone']}'")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
