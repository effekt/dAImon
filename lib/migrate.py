#!/usr/bin/env python3
"""Bring an install up to the current layout: personal settings out of the repo
into the personal config dir, and an explicit list of installed daemons.

Legacy files sat beside the committed ones (gitignored):
  <daemon dir>/daemon.local.toml      -> <personal dir>/daemons/<slug>.toml
  profiles/<name>/profile.local.toml  -> <personal dir>/profiles/<name>.toml
  daemons/slack-commands/commands.local/*  -> <personal dir>/commands/
where <personal dir> is the folder holding daimon.toml (~/.config/daimon). When
dAImon's daemons moved from daemons/ to catalog/, a daemon.local.toml stayed
behind in daemons/<slug>/ (it is gitignored); it is migrated from there too, and
the leftover folder is removed once only migration stubs and caches remain.

A daimon.toml without `[daemons].installed` predates the catalog: every catalog
daemon not in `disabled` was active. That set is written as `installed` once,
so nothing starts or stops; `disabled` is left as it is.

Idempotent, stdlib only. A legacy file's text moves verbatim (comments kept); when
the personal file already exists, only the keys it lacks are appended, and its own
values win. The legacy file is then reduced to a one-line comment (it parses as
empty TOML) rather than deleted, so nothing that globs for it breaks. `*.example`
files are never touched. Run: `daimon migrate` or `python3 lib/migrate.py`.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402
import toml_emit  # noqa: E402

STUB_RE = re.compile(r"\A# moved to .* by daimon migrate\s*\Z")
HEADER_RE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(#.*)?$")


def stub_text(new: Path) -> str:
    return f"# moved to {new} by daimon migrate\n"


def is_stub(text: str) -> bool:
    return bool(STUB_RE.match(text))


def atomic_write(path: Path, text: str) -> None:
    """Write via a temp file in the same folder + rename, keeping the file's mode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else None
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def set_config_key(path: Path, table: str, key: str, value) -> None:
    """Set `key = value` under [table] in a TOML file (daimon.toml), keeping its
    comments and every other setting. Refuses to write a file that would not
    load back to exactly that value."""
    text = path.read_text() if path.exists() else ""
    new = toml_emit.set_key_text(text, table, key, value)
    try:
        written = tomllib.loads(new).get(table, {}).get(key)
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"cannot set [{table}].{key} in {path}: {e}") from e
    if written != value:
        raise ValueError(f"cannot set [{table}].{key} in {path}: it would read back {written!r}")
    atomic_write(path, new)


def _section_end(lines: list[str], name: str) -> int | None:
    """Index just past the last non-blank line of top-level table [name], or None."""
    start = None
    for i, ln in enumerate(lines):
        m = HEADER_RE.match(ln)
        if m and m.group(1).strip() == name:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if HEADER_RE.match(lines[j]) or lines[j].lstrip().startswith("[["):
            end = j
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1
    return end


def _first_header(lines: list[str]) -> int:
    for i, ln in enumerate(lines):
        if HEADER_RE.match(ln) or ln.lstrip().startswith("[["):
            return i
    return len(lines)


def _scalars(data: dict) -> dict:
    return {k: v for k, v in data.items() if not isinstance(v, dict)}


def _missing(legacy: dict, have: dict) -> list[str]:
    return [toml_emit.emit_kv(k, v) for k, v in legacy.items() if k not in have]


def _overridden(legacy: dict, have: dict, prefix: str) -> list[str]:
    return [
        f"# {prefix}{toml_emit.emit_kv(k, v)}"
        for k, v in legacy.items()
        if k in have and have[k] != v
    ]


def _add_to_table(lines: list[str], name: str, missing: list[str]) -> None:
    """Insert `missing` key lines at the end of table [name], creating it if absent."""
    end = _section_end(lines, name)
    if end is None:
        lines += ["", f"[{name}]", *missing]
    else:
        lines[end:end] = missing


def merge_text(new_text: str, new: dict, legacy: dict, legacy_path: Path) -> str:
    """Add to `new_text` every key of `legacy` that `new` lacks, under the right
    table; record legacy values that `new` overrides as comments. New values win."""
    lines = new_text.splitlines()
    top_legacy = _scalars(legacy)
    overridden = _overridden(top_legacy, new, "")
    if top_missing := _missing(top_legacy, new):
        at = _first_header(lines)
        lines[at:at] = top_missing
    for name, table in legacy.items():
        if name in top_legacy:
            continue
        have = new.get(name)
        have = have if isinstance(have, dict) else {}
        overridden += _overridden(table, have, f"[{name}] ")
        if missing := _missing(table, have):
            _add_to_table(lines, name, missing)
    if overridden:
        note = f"# Overridden by this file when {legacy_path} was merged in by daimon migrate:"
        lines += ["", note, *overridden]
    return "\n".join(lines).lstrip("\n") + "\n"


def _merge_into(legacy: Path, legacy_data: dict, new: Path) -> str:
    new_text = new.read_text()
    try:
        new_data = tomllib.loads(new_text)
    except tomllib.TOMLDecodeError as e:
        return f"skip  {legacy}: {new} is not valid TOML ({e}); left both in place"
    try:
        merged = merge_text(new_text, new_data, legacy_data, legacy)
    except TypeError as e:  # a value toml_emit can't write (e.g. a datetime)
        return f"skip  {legacy}: cannot merge into {new} ({e}); left both in place"
    if merged != new_text:
        try:
            tomllib.loads(merged)  # never write a file the loader would reject
        except tomllib.TOMLDecodeError as e:
            return f"skip  {legacy}: cannot merge into {new} ({e}); left both in place"
        atomic_write(new, merged)
    atomic_write(legacy, stub_text(new))
    return f"merged {legacy} -> {new}"


def migrate_file(legacy: Path, new: Path) -> str | None:
    """Move one legacy file into its personal location. Returns a line describing
    what happened, or None when there was nothing to do."""
    if not legacy.is_file() or legacy.name.endswith(".example"):
        return None
    text = legacy.read_text()
    if is_stub(text):
        return None
    try:
        legacy_data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return f"skip  {legacy}: not valid TOML ({e}); left in place"
    if new.exists():
        return _merge_into(legacy, legacy_data, new)
    atomic_write(new, text)
    atomic_write(legacy, stub_text(new))
    return f"moved {legacy} -> {new}"


def pairs(cfg: config.Config) -> list[tuple[Path, Path]]:
    """Every (legacy, personal) pair: daemons in the install root (including
    `.local` folders) and in packs, then the install root's profiles. Only the
    folder that loads a slug is migrated, so a duplicate can't change behaviour."""
    out: list[tuple[Path, Path]] = []
    for slug in sorted(cfg.daemon_locations()):
        for legacy in cfg.legacy_daemon_local_paths(slug):
            out.append((legacy, cfg.daemon_local_path(slug)))
    for local in sorted(cfg.profiles_dir().glob("*/profile.local.toml")):
        name = local.parent.name
        out.append((local, cfg.profile_local_path(name)))
    return out


def migrate_installed(cfg: config.Config) -> str | None:
    """Write `[daemons].installed` as today's active set when it is absent."""
    if cfg.source is None or cfg.installed_list is not None:
        return None
    active = [s for s in cfg.catalog_locations() if s not in cfg.disabled]
    set_config_key(cfg.source, "daemons", "installed", active)
    return f"installed {cfg.source}: [daemons].installed = the {len(active)} active daemon(s)"


def migrate_commands(cfg: config.Config) -> list[str]:
    """Move your own slack-commands runbooks to <personal dir>/commands/."""
    legacy, new = cfg.legacy_local_commands_dir(), cfg.local_commands_dir()
    if not legacy.is_dir():
        return []
    lines: list[str] = []
    for src in sorted(p for p in legacy.iterdir() if p.is_file() and p.name != ".DS_Store"):
        dest = new / src.name
        if dest.exists() and dest.read_bytes() != src.read_bytes():
            lines.append(f"skip  {src}: {dest} exists and differs; left both in place")
            continue
        if not dest.exists():
            atomic_write(dest, src.read_text())
        src.unlink()
        lines.append(f"moved {src} -> {dest}")
    return lines


LEFTOVER_JUNK = {"__pycache__", ".DS_Store"}


def _tidy(folder: Path) -> bool:
    """Empty `folder` of migration stubs, caches and empty subfolders; remove it
    if nothing else is left. Never touches anything else."""
    for entry in folder.iterdir():
        if entry.name in LEFTOVER_JUNK:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        elif entry.is_file() and entry.suffix == ".toml" and is_stub(entry.read_text()):
            entry.unlink()
        elif entry.is_dir() and not entry.is_symlink():
            _tidy(entry)
    if any(folder.iterdir()):
        return False
    folder.rmdir()
    return True


def tidy_leftovers(cfg: config.Config) -> list[str]:
    """Remove daemons/<slug>/ folders the move to catalog/ left behind (no
    daemon.toml, only stubs and caches). Anything with real content stays."""
    root = cfg.daemons_dir()
    if not root.is_dir():
        return []
    lines = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and not p.is_symlink()):
        if not (folder / "daemon.toml").exists() and _tidy(folder):
            lines.append(f"removed {folder} (left behind when daemons moved to catalog/)")
    return lines


def migrate(cfg: config.Config | None = None) -> list[str]:
    cfg = cfg or config.Config.load()
    lines = [line for legacy, new in pairs(cfg) if (line := migrate_file(legacy, new))]
    lines += migrate_commands(cfg)
    lines += tidy_leftovers(cfg)
    if line := migrate_installed(cfg):
        lines.append(line)
    return lines


def main() -> int:
    lines = migrate()
    for line in lines:
        print(f"migrate: {line}")
    if not lines:
        print("migrate: already up to date — nothing to move")
    return 1 if any(line.startswith("skip") for line in lines) else 0


if __name__ == "__main__":
    sys.exit(main())
