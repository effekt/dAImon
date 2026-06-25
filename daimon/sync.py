"""Compile Daimon registrations into daemons/<slug>/ folders, then regenerate
plists and render daemon skills. Run via `daimon sync` or `python -m daimon.sync`."""
from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path

from .app import Daimon

INSTALL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(INSTALL_ROOT / "lib"))
import toml_emit  # noqa: E402


def _import_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_app(module_path: Path):
    mod = _import_from_path("daimon_user_daemons", module_path)
    for v in vars(mod).values():
        if isinstance(v, Daimon):
            return v
    raise SystemExit(f"no Daimon() instance found in {module_path}")


def spec_to_toml(spec) -> str:
    daemon = {"backend": spec.backend}
    if spec.model is not None:
        daemon["model"] = spec.model
    if spec.working_dir:
        daemon["working_dir"] = spec.working_dir
    daemon["schedule"] = spec.schedule
    daemon["command"] = spec.command
    if spec.danger is not None:
        daemon["danger"] = spec.danger
    if spec.stuck_after is not None:
        daemon["stuck_after"] = spec.stuck_after
    return toml_emit.dump_sections({"daemon": daemon, "inputs": spec.inputs})


def _default_skill(spec) -> str:
    return (f"---\nname: {spec.slug}\ndescription: {spec.slug} daemon.\n---\n\n"
            f"# {spec.slug}\n\nDescribe what this daemon should do each run.\n")


def write_spec(spec, module_path: Path):
    ddir = INSTALL_ROOT / "daemons" / spec.slug
    (ddir / "skill").mkdir(parents=True, exist_ok=True)
    (ddir / "daemon.toml").write_text(spec_to_toml(spec))

    tmpl = (INSTALL_ROOT / "templates" / "discover.sh.template").read_text()
    discover = (tmpl.replace("__INSTALL_ROOT__", str(INSTALL_ROOT))
                    .replace("__MODULE__", str(module_path))
                    .replace("__SLUG__", spec.slug))
    dpath = ddir / "discover.sh"
    dpath.write_text(discover)
    dpath.chmod(dpath.stat().st_mode | stat.S_IEXEC)

    skill = ddir / "skill" / "SKILL.md"
    if spec.prompt:
        skill.write_text(spec.prompt)
    elif not skill.exists():
        skill.write_text(_default_skill(spec))


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
    module_path = None
    if argv:
        module_path = Path(os.path.expanduser(argv[0]))
    elif os.environ.get("DAIMON_DAEMONS_MODULE"):
        module_path = Path(os.path.expanduser(os.environ["DAIMON_DAEMONS_MODULE"]))

    if module_path and module_path.exists():
        app = load_app(module_path)
        for spec in app.specs.values():
            write_spec(spec, module_path)
        print(f"compiled {len(app.specs)} registration(s) from {module_path}")

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
