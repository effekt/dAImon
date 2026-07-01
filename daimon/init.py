"""Scaffold machine-local config from *.example files and choose which daemons to
enable on this machine. Run via `daimon init [slug ...]` or `python -m daimon.init`.

With slugs, those daemons are the active set; the rest are added to
`[daemons].disabled` so they aren't synced or scheduled. With no slugs, prompts
interactively (defaulting to all); non-interactively it configures the current
active set without changing what's disabled."""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
from pathlib import Path

INSTALL_ROOT = Path(__file__).resolve().parent.parent


def _import_config():
    path = INSTALL_ROOT / "lib" / "config.py"
    spec = importlib.util.spec_from_file_location("daimon_config", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load config from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def all_slugs(root: Path) -> list[str]:
    return sorted(p.parent.name for p in (root / "daemons").glob("*/daemon.toml"))


def set_disabled_text(text: str, disabled: list[str]) -> str:
    """Rewrite the `disabled = [...]` line under `[daemons]`, preserving comments and
    other sections. Adds the section/line if absent."""
    arr = "[" + ", ".join(f'"{s}"' for s in disabled) + "]"
    new_line = f"disabled = {arr}"
    out: list[str] = []
    in_daemons = False
    done = False
    for ln in text.splitlines():
        stripped = ln.strip()
        is_header = (
            stripped.startswith("[") and stripped.endswith("]") and not stripped.startswith("[[")
        )
        if is_header:
            if in_daemons and not done:
                out.append(new_line)
                done = True
            in_daemons = stripped == "[daemons]"
            out.append(ln)
            continue
        if in_daemons and not done and re.match(r"\s*disabled\s*=", ln):
            out.append(new_line)
            done = True
            continue
        out.append(ln)
    if in_daemons and not done:
        out.append(new_line)
        done = True
    if not done:
        if out and out[-1].strip():
            out.append("")
        out += ["[daemons]", new_line]
    result = "\n".join(out)
    return result + "\n" if text.endswith("\n") else result


def _scaffold(example: Path) -> None:
    dest = example.with_suffix("")  # drop the trailing .example
    rel = dest.relative_to(INSTALL_ROOT)
    if dest.exists():
        print(f"  skip  {rel} (exists)")
    else:
        shutil.copy(example, dest)
        print(f"  new   {rel}")


def _resolve_selection(
    slugs: list[str], disabled: list[str], argv: list[str]
) -> tuple[list[str], bool]:
    """Return (selected, explicit). `explicit` means the disabled set should be rewritten."""
    if argv:
        unknown = [s for s in argv if s not in slugs]
        if unknown:
            sys.exit(f"unknown daemon(s): {', '.join(unknown)}\nknown: {', '.join(slugs)}")
        return sorted(set(argv)), True
    if sys.stdin.isatty():
        print("daemons (● active, ○ disabled):")
        for s in slugs:
            print(f"  {'○' if s in disabled else '●'} {s}")
        resp = input("enable which? space-separated, or 'all' [all]: ").strip()
        if resp in ("", "all"):
            return slugs, True
        chosen = resp.split()
        unknown = [s for s in chosen if s not in slugs]
        if unknown:
            sys.exit(f"unknown daemon(s): {', '.join(unknown)}")
        return sorted(set(chosen)), True
    # non-interactive, no args: keep the current active set, don't touch disabled
    return [s for s in slugs if s not in disabled], False


def main(argv: list[str]) -> int:
    cfg_mod = _import_config()
    config_path = cfg_mod.global_config_path()
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(INSTALL_ROOT / "config" / "daimon.toml.example", config_path)
        print(f"  new   {config_path}")

    slugs = all_slugs(INSTALL_ROOT)
    cfg = cfg_mod.Config.load()
    selected, explicit = _resolve_selection(slugs, cfg.disabled, argv)

    if explicit:
        disabled = [s for s in slugs if s not in selected]
        config_path.write_text(set_disabled_text(config_path.read_text(), disabled))
        print(f"active: {', '.join(selected) or '(none)'}")
        if disabled:
            print(f"disabled: {', '.join(disabled)}")

    print("scaffolding local config for active daemons:")
    cfg = cfg_mod.Config.load()  # reload so newly-enabled daemons are discoverable
    sources: set[str] = set()
    for slug in selected:
        ex = INSTALL_ROOT / "daemons" / slug / "daemon.local.toml.example"
        if ex.exists():
            _scaffold(ex)
        sources.update(cfg.daemon(slug)["sources"])
    for src in sorted(sources):
        ex = INSTALL_ROOT / "profiles" / src / "profile.local.toml.example"
        if ex.exists():
            _scaffold(ex)

    print("\nnext: set working_dir in each daemons/*/daemon.local.toml, then run 'daimon doctor'.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
