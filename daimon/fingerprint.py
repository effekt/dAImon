"""A daemon folder's content, minus what is not part of the daemon: the
`.origin.json` record, caches, and personal files (*.local.toml settings,
legacy commands.local/ runbooks). `daimon eject` copies exactly these files
and records their hash, so the hash later tells whether either side changed."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

SKIP_NAMES = (".origin.json", "__pycache__", ".DS_Store", "commands.local")
SKIP_SUFFIXES = (".pyc", ".local.toml")
# The same exclusions as `diff -x` patterns.
DIFF_EXCLUDES = (*SKIP_NAMES, *(f"*{s}" for s in SKIP_SUFFIXES))


def skipped(name: str) -> bool:
    return name in SKIP_NAMES or name.endswith(SKIP_SUFFIXES)


def content_files(folder: Path) -> list[Path]:
    """The daemon's files, relative to `folder`, sorted."""
    out = []
    for path in folder.rglob("*"):
        rel = path.relative_to(folder)
        if path.is_file() and not any(skipped(part) for part in rel.parts):
            out.append(rel)
    return sorted(out)


def content_hash(folder: Path) -> str:
    """Deterministic: each file's path, executable bit and bytes, in path order."""
    digest = hashlib.sha256()
    for rel in content_files(folder):
        path = folder / rel
        digest.update(rel.as_posix().encode() + b"\0")
        digest.update(b"x" if os.access(path, os.X_OK) else b"-")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return f"sha256:{digest.hexdigest()}"


def copy_content(src: Path, dest: Path) -> None:
    """Copy `src` to `dest` without the skipped files. `dest` may already exist
    (a leftover folder holding only migration stubs)."""
    shutil.copytree(
        src, dest, ignore=lambda _d, names: [n for n in names if skipped(n)], dirs_exist_ok=True
    )
