"""Scaffold machine-local config from *.example files and choose which daemons to
enable on this machine. Run via `daimon init [slug ...]` or `python -m daimon.init`.

With slugs, those daemons are the active set; the rest are added to
`[daemons].disabled` so they aren't synced or scheduled. With no slugs, prompts
interactively (defaulting to all); non-interactively it configures the current
active set without changing what's disabled."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

INSTALL_ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER_WORKING_DIRS = {"~/code", "~/code/your-repo"}


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


def _scaffold(example: Path) -> Path:
    dest = example.with_suffix("")  # drop the trailing .example
    rel = dest.relative_to(INSTALL_ROOT)
    if dest.exists():
        print(f"  skip  {rel} (exists)")
    else:
        shutil.copy(example, dest)
        print(f"  new   {rel}")
    return dest


def set_working_dir_text(text: str, working_dir: str) -> str:
    """Rewrite `working_dir = ...` under `[daemon]`, preserving the rest of the file."""
    new_value = json.dumps(working_dir)
    out: list[str] = []
    in_daemon = False
    done = False
    for ln in text.splitlines():
        stripped = ln.strip()
        is_header = (
            stripped.startswith("[") and stripped.endswith("]") and not stripped.startswith("[[")
        )
        if is_header:
            if in_daemon and not done:
                out.append(f"working_dir = {new_value}")
                done = True
            in_daemon = stripped == "[daemon]"
            out.append(ln)
            continue
        if in_daemon and not done:
            m = re.match(r"(\s*)working_dir\s*=", ln)
            if m:
                comment = ""
                hash_at = ln.find("#")
                if hash_at >= 0:
                    comment = " " + ln[hash_at:].strip()
                out.append(f"{m.group(1)}working_dir = {new_value}{comment}")
                done = True
                continue
        out.append(ln)
    if in_daemon and not done:
        out.append(f"working_dir = {new_value}")
        done = True
    if not done:
        if out and out[-1].strip():
            out.append("")
        out += ["[daemon]", f"working_dir = {new_value}"]
    result = "\n".join(out)
    return result + "\n" if text.endswith("\n") else result


def _raw_working_dir(path: Path) -> str:
    try:
        with open(path, "rb") as fh:
            raw = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return ""
    value = raw.get("daemon", {}).get("working_dir", "")
    return value if isinstance(value, str) else ""


def _git_root(path: Path) -> Path | None:
    cur = path.resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _cwd_working_dir_default() -> str:
    git_root = _git_root(Path.cwd())
    if git_root is None or git_root == INSTALL_ROOT.resolve():
        return ""
    return str(git_root)


def _normalize_working_dir(value: str) -> str:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return str(path.resolve())


def _needs_working_dir(path: Path) -> bool:
    value = _raw_working_dir(path)
    return not value or value in PLACEHOLDER_WORKING_DIRS


def _set_working_dir(path: Path, working_dir: str) -> None:
    path.write_text(set_working_dir_text(path.read_text(), working_dir))


def _resolve_working_dir(auto_default: str, interactive: bool) -> str:
    cwd = str(Path.cwd().resolve())
    if not interactive:
        if auto_default:
            print(f"using working_dir for selected daemons: {auto_default} (from cwd)")
            return auto_default
        return ""
    print(f"current directory: {cwd}")
    resp = input(f"working_dir for selected daemons [{cwd}]: ").strip()
    if not resp:
        return cwd
    return _normalize_working_dir(resp)


def _configure_working_dirs(local_paths: list[Path], default: str, interactive: bool) -> None:
    pending = [path for path in local_paths if _needs_working_dir(path)]
    if not pending:
        return
    working_dir = _resolve_working_dir(default, interactive)
    if not working_dir:
        for path in pending:
            print(f"  keep  {path.relative_to(INSTALL_ROOT)} working_dir placeholder")
        return
    for path in pending:
        _set_working_dir(path, working_dir)
        print(f"  set   {path.relative_to(INSTALL_ROOT)} working_dir = {working_dir}")


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
    default_working_dir = _cwd_working_dir_default()
    interactive = sys.stdin.isatty()
    local_paths: list[Path] = []
    for slug in selected:
        ex = INSTALL_ROOT / "daemons" / slug / "daemon.local.toml.example"
        if ex.exists():
            local_path = _scaffold(ex)
            local_paths.append(local_path)
        sources.update(cfg.daemon(slug)["sources"])
    _configure_working_dirs(local_paths, default_working_dir, interactive)
    for src in sorted(sources):
        ex = INSTALL_ROOT / "profiles" / src / "profile.local.toml.example"
        if ex.exists():
            _scaffold(ex)

    print("\nnext: review daemons/*/daemon.local.toml, then run 'daimon doctor'.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
