# AGENTS.md

Guidance for AI agents and contributors working **on** dAImon itself. For what
dAImon *is* and how to operate it, see [README.md](README.md).

## Orientation

- [docs/architecture.md](docs/architecture.md) — how the pieces fit.
- [docs/writing-a-daemon.md](docs/writing-a-daemon.md) — add or change a daemon.
- [docs/writing-a-source.md](docs/writing-a-source.md) — add a source profile (GitHub, Shortcut, Datadog, …).
- [docs/configuration.md](docs/configuration.md) — every config field.
- [docs/troubleshooting.md](docs/troubleshooting.md) — common failures and fixes.
- `lib/` framework · `backends/` agent CLIs · `daemons/` the daemons · `daimon/`
  sync · `tui/` control panel · `skills/` management commands · `config/` defaults.

## Workflow

```bash
make test        # bash syntax + shellcheck + python unit tests + gate tests
make lint        # ruff + shellcheck
make typecheck   # pyright
make fmt         # ruff format + autofix
```

`uv run pre-commit install` wires lint + typecheck into every commit. CI runs the
same checks. Use feature branches and PRs; never commit to `main` directly.

## Invariants — do not break these

- **`lib/config.py` is the single source of truth for config.** Bash, the TUI,
  and the installer all shell out to it. Never parse `daemon.toml` elsewhere.
- **The runtime core stays stdlib-only.** Nothing under `lib/`, `daemons/`, or
  `daimon/` may import a third-party package — daemons and gates run with no
  venv. Only `tui/` may depend on `textual`. New deps go in pyproject's `dev`
  group, never in `[project.dependencies]`.
- **Every daemon must set `working_dir`** (in its gitignored `daemon.local.toml`)
  to the target repo. Left unset, `config.py` defaults it to the dAImon install
  root, so the agent would run against this repo instead of its target.
- **`*.local.toml` is gitignored** and holds machine-specific `working_dir` +
  `[inputs]`. Committed `daemon.toml` holds shared defaults only.

## Documentation

- **Each daemon has a generated `README.md`** (and there's a generated
  `daemons/README.md` index). They're built from committed metadata only —
  `daemon.toml` + `skill/SKILL.md` — never machine-local files. Do not hand-edit
  them; run `make docs` to regenerate. A pre-commit hook regenerates them when a
  `daemon.toml` or `SKILL.md` changes, and `tests/test_docs.py` fails CI if any is
  stale. Change the daemon's metadata (or `daimon/gen_docs.py`), not the README.

## House style

- Shell: hand-aligned definitions and the compact `cmd; return 0` dispatch style
  are intentional. shellcheck is enforced; shfmt is deliberately not.
- This repo's `.claude/settings.json` is committed and grants permissions only —
  it never defines hooks. The runtime sentinel/heartbeat hooks are installed at
  the user level by `bin/daimon-install`; keep them out of repo config.
