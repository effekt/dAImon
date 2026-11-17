"""Own a copy of a daemon: `daimon eject`, `uneject`, `outdated`, `diff`.

A linked daemon runs from its catalog (dAImon's `catalog/` or a pack's
`daemons/`), so updates reach it. `daimon eject <slug>` copies it into the
install's gitignored `daemons/<slug>/` to edit, which then takes precedence;
`daimon eject <slug> --pack [dir]` copies a dAImon catalog daemon into a pack's
`daemons/<slug>/` instead, for the team to own and change by PR. Either copy
records where it came from in `.origin.json`: {source, path, hash}, the hash
covering the files as copied (daimon/fingerprint.py). Comparing that hash with
upstream's files today, and with the copy's, tells which side changed since
(`outdated`, `diff`). `daimon uneject <slug>` deletes a local copy so the
daemon is linked again."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from daimon.catalog import _confirm, _modules, _set_list, _sync
from daimon.fingerprint import DIFF_EXCLUDES, content_hash, copy_content


def _fail(message: str) -> int:
    print(f"✗ {message}", file=sys.stderr)
    return 1


def _sync_or_warn() -> int:
    if _sync():
        return 0
    print("  sync failed: run `daimon sync`", file=sys.stderr)
    return 1


def _root_of(cfg, source: str) -> Path | None:
    if source == "dAImon":
        return cfg.install_root
    return next((p for p in cfg.packs if p.name == source), None)


def upstream_dir(cfg, origin: dict) -> Path | None:
    """The folder a copy was taken from, when it still holds a daemon."""
    root = _root_of(cfg, str(origin.get("source", "")))
    path = origin.get("path")
    if root is None or not isinstance(path, str) or not path:
        return None
    folder = root / path
    return folder if (folder / "daemon.toml").exists() else None


def copy_daemon(src: Path, dest: Path, source: str, rel_path: str) -> None:
    copy_content(src, dest)
    origin = {"source": source, "path": rel_path, "hash": content_hash(dest)}
    (dest / ".origin.json").write_text(json.dumps(origin, indent=2) + "\n")


@dataclass
class Copy:
    slug: str
    folder: Path
    where: str  # "local" or the pack's name
    origin: dict

    def edited(self) -> bool:
        return content_hash(self.folder) != self.origin.get("hash")

    def upstream_changed(self, cfg) -> bool | None:
        """None when upstream no longer has the daemon."""
        up = upstream_dir(cfg, self.origin)
        return None if up is None else content_hash(up) != self.origin.get("hash")


def copies(cfg) -> list[Copy]:
    """Every copy with an .origin.json: local ejected ones, then packs'."""
    config, _ = _modules()
    found = [
        (slug, folder, "local")
        for slug, dirs in sorted(cfg.ejected_locations().items())
        for folder in dirs
    ]
    for pack in cfg.packs:
        for toml in sorted((pack / "daemons").glob("*/daemon.toml")):
            found.append((toml.parent.name, toml.parent, pack.name))
    return [
        Copy(slug, folder, where, origin)
        for slug, folder, where in found
        if (origin := config.read_origin(folder)) is not None
    ]


def choose_pack(cfg, pack: str) -> Path:
    """`--pack` with no directory means the only configured pack."""
    if pack:
        chosen = Path(pack).expanduser().resolve()
        if chosen not in cfg.packs:
            raise ValueError(f"{chosen} is not in [packs].paths")
        return chosen
    if not cfg.packs:
        raise ValueError("no packs configured ([packs].paths in daimon.toml)")
    if len(cfg.packs) > 1:
        names = ", ".join(map(str, cfg.packs))
        raise ValueError(f"several packs configured ({names}); name one: --pack <dir>")
    return cfg.packs[0]


def eject_to_pack(cfg, slug: str, pack: str) -> Path:
    """Copy dAImon's catalog/<slug> into a pack's daemons/<slug>, team-owned."""
    target = choose_pack(cfg, pack)
    src = cfg.catalog_dir() / slug
    if not (src / "daemon.toml").exists():
        raise ValueError(f"{slug} is not in dAImon's catalog ({cfg.catalog_dir()})")
    dest = target / "daemons" / slug
    if dest.exists():
        raise ValueError(f"{dest} already exists")
    copy_daemon(src, dest, "dAImon", f"catalog/{slug}")
    print(f"+ {dest}/ (from dAImon's catalog; .origin.json records it)")
    print("  it now replaces dAImon's copy: commit it in the pack's repo")
    return dest


def _ensure_installed(cfg, migrate, slug: str) -> None:
    if slug not in cfg.installed() and not _set_list(
        cfg, migrate, "installed", [*cfg.installed(), slug]
    ):
        raise ValueError(f"could not add {slug} to [daemons].installed")


def _move_legacy_settings(cfg, migrate, slug: str, folders: list[Path]) -> None:
    """A gitignored daemon.local.toml beside the daemon is still read; a copy
    leaves it behind and deleting a copy would lose it, so move it to the
    personal settings file first, and stop if it can't be moved."""
    for folder in folders:
        line = migrate.migrate_file(folder / "daemon.local.toml", cfg.daemon_local_path(slug))
        if line and line.startswith("skip"):
            raise ValueError(f"{line}; fix it, then retry")
        if line:
            print(f"  {line}")


def eject_local(cfg, migrate, slug: str) -> Path:
    mine = cfg.ejected_locations().get(slug)
    if mine:
        raise ValueError(f"{slug} is already ejected: {mine[0]}")
    entry = cfg.catalog().get(slug)
    if entry is None:
        raise ValueError(f"{slug} is not in any catalog (see `daimon catalog`)")
    src, source = entry["path"], entry["source"]
    root = _root_of(cfg, source)
    if root is None:
        raise ValueError(f"cannot tell which catalog {src} belongs to")
    rel = src.relative_to(root).as_posix()
    dest = cfg.daemons_dir() / slug
    _move_legacy_settings(cfg, migrate, slug, [src, dest])
    copy_daemon(src, dest, source, rel)
    _ensure_installed(cfg, migrate, slug)
    print(f"+ {dest}/ (from {source}: {rel})")
    print(f"  edit it there; `daimon outdated` / `daimon diff {slug}` show upstream changes,")
    print(f"  `daimon uneject {slug}` links it again")
    return dest


def eject(config, migrate, slug: str, pack: str | None) -> int:
    cfg = config.Config.load()
    try:
        if pack is None:
            eject_local(cfg, migrate, slug)
        else:
            eject_to_pack(cfg, slug, pack)
    except ValueError as e:
        return _fail(str(e))
    return _sync_or_warn() if slug in config.Config.load().discover() else 0


def _unejectable(cfg, slug: str) -> Copy:
    """The local copy uneject may delete; ValueError says why not."""
    mine = cfg.ejected_locations().get(slug)
    if not mine:
        team = [c for c in copies(cfg) if c.slug == slug and c.where != "local"]
        if team:
            raise ValueError(
                f"{slug} is the {team[0].where} pack's copy ({team[0].folder}): "
                "change it by a PR to the pack"
            )
        raise ValueError(f"{slug} is not ejected")
    local = [c for c in copies(cfg) if c.folder == mine[0]]
    if not local:
        raise ValueError(f"{mine[0]} has no .origin.json: it is your own daemon, not a copy")
    if slug not in cfg.catalog():
        raise ValueError(f"no catalog offers {slug} any more: keeping {mine[0]}")
    return local[0]


def uneject(config, migrate, slug: str, yes: bool) -> int:
    cfg = config.Config.load()
    try:
        copy = _unejectable(cfg, slug)
    except ValueError as e:
        return _fail(str(e))
    source = cfg.catalog()[slug]["source"]
    lost = " (your edits there are lost)" if copy.edited() else ""
    if not yes and not _confirm(f"Delete {copy.folder}{lost} and link {slug} to {source} again?"):
        print(f"  kept {copy.folder} (pass --yes to delete it)", file=sys.stderr)
        return 1
    try:
        _move_legacy_settings(cfg, migrate, slug, [copy.folder])
        shutil.rmtree(copy.folder)
        print(f"- {copy.folder}")
        print(f"  {slug} is linked to {source} again; personal settings kept")
        _ensure_installed(cfg, migrate, slug)
    except ValueError as e:
        return _fail(str(e))
    return _sync_or_warn()


UPSTREAM_LABEL = {None: "gone", True: "changed", False: "unchanged"}


def report(cfg) -> list[tuple[Copy, bool | None, bool]]:
    """(copy, upstream changed (None = gone), edited) for every copy."""
    return [(c, c.upstream_changed(cfg), c.edited()) for c in copies(cfg)]


def _print_table(rows: list[tuple[Copy, bool | None, bool]]) -> None:
    width = max(len(c.slug) for c, _, _ in rows) + 2
    where_width = max(len(c.where) for c, _, _ in rows) + 2
    print(f"{'DAEMON':<{width}}{'COPY':<{where_width}}{'UPSTREAM':<12}{'YOUR COPY':<12}FROM")
    for c, up, edited in rows:
        src = f"{c.origin.get('source')}: {c.origin.get('path')}"
        mine = "edited" if edited else "unchanged"
        print(f"{c.slug:<{width}}{c.where:<{where_width}}{UPSTREAM_LABEL[up]:<12}{mine:<12}{src}")


def outdated(config, brief: bool) -> int:
    rows = report(config.Config.load())
    if brief:
        for c, up, _ in rows:
            if up is not False:
                print(f"{c.slug} ({c.where}): upstream {UPSTREAM_LABEL[up]}")
        return 0
    if not rows:
        print("no ejected daemons (daimon eject <slug>)")
        return 0
    _print_table(rows)
    print("\n(changed since the copy was made; see one: daimon diff <slug>)")
    return 0


def diff(config, slug: str) -> int:
    cfg = config.Config.load()
    copy = next((c for c in copies(cfg) if c.slug == slug), None)
    if copy is None:
        return _fail(f"{slug} has no ejected copy with an .origin.json")
    up = upstream_dir(cfg, copy.origin)
    if up is None:
        return _fail(f"upstream {copy.origin.get('source')}: {copy.origin.get('path')} is gone")
    upstream = "changed" if copy.upstream_changed(cfg) else "unchanged"
    mine = "edited" if copy.edited() else "unchanged"
    print(f"# {slug}: --- upstream {up}  +++ your copy {copy.folder}")
    print(f"# since the eject: upstream {upstream}, your copy {mine}", flush=True)
    excludes = [arg for name in DIFF_EXCLUDES for arg in ("-x", name)]
    proc = subprocess.run(["diff", "-ru", *excludes, str(up), str(copy.folder)], check=False)
    return 0 if proc.returncode in (0, 1) else proc.returncode


def _parse(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="daimon")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("eject", help="copy a daemon into daemons/ (or a pack) to edit")
    e.add_argument("slug")
    e.add_argument("--pack", nargs="?", const="", default=None, metavar="DIR")
    u = sub.add_parser("uneject", help="delete your ejected copy; link the daemon again")
    u.add_argument("slug")
    u.add_argument("--yes", "-y", action="store_true")
    o = sub.add_parser("outdated", help="ejected copies whose upstream or copy changed")
    o.add_argument("--brief", action="store_true", help="only copies whose upstream changed")
    d = sub.add_parser("diff", help="diff -ru upstream against your copy")
    d.add_argument("slug")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse(argv)
    config, migrate = _modules()
    if args.cmd == "eject":
        return eject(config, migrate, args.slug, args.pack)
    if args.cmd == "uneject":
        return uneject(config, migrate, args.slug, args.yes)
    if args.cmd == "outdated":
        return outdated(config, args.brief)
    return diff(config, args.slug)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
