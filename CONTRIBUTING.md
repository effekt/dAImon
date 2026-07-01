# Contributing to dAImon

Thanks for your interest! This guide covers the local setup and the workflow for
changes. For the internals and conventions, see [AGENTS.md](AGENTS.md); to build a
daemon, see [docs/writing-a-daemon.md](docs/writing-a-daemon.md).

## Dev setup

```bash
git clone <your-fork> && cd dAImon
uv sync                 # dev tools: ruff, pyright (the runtime itself is stdlib-only)
make doctor             # confirm your toolchain (python 3.12+, tmux, gh, jq, claude)
```

## Before you push

```bash
make test               # bash syntax, python unittests, shellcheck, bats
make lint               # ruff check + ruff format --check
make typecheck          # pyright
```

CI runs the same checks on every pull request (`.github/workflows/ci.yml`); a green
`make test && make lint && make typecheck` locally means CI should pass.

## Conventions

- **Shell must stay Bash 3.2-compatible** — macOS ships `/bin/bash` 3.2, and
  shellcheck won't catch 4.x-only syntax. No associative arrays, `${x,,}`, `mapfile`, etc.
- **Never commit machine-local config or secrets.** `*.local.toml`, `config/daimon.toml`,
  and `.env` are gitignored. Add new machine-specific settings as a tracked
  `*.local.toml.example`, not a real value.
- **Keep daemons self-contained** — a daemon is a folder under `daemons/<slug>/`; the
  framework auto-discovers it. Run `daimon sync` after editing a `daemon.toml` or skill.
- Match the style of the surrounding code; keep functions small and comments scarce.

## Pull requests

- Branch off `main`; use a descriptive `feat/…` or `fix/…` branch name.
- Keep PRs focused; write a clear title and a body explaining the why.
- Make sure the checks above pass and update docs when behavior changes.
