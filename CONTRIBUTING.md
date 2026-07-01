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
- Keep PRs focused and write a body explaining the why.
- **PR titles must be [Conventional Commits](https://www.conventionalcommits.org/)**
  (`type(scope): summary`, e.g. `feat(tui): …`, `fix: …`, `docs: …`). Merges are
  **squash-only** and the squash commit uses the PR title, so the title becomes the
  entry in `main`'s history. The `pr-title` CI check enforces this.
- Make sure the checks pass (`test`, `lint`, `pr-title`) and update docs when
  behavior changes.

## Maintainers: repository settings

Merge method is squash-only with auto-delete of merged branches (set via the repo
API). Branch protection for `main` requires a public repo or GitHub Pro; once the
repo is public, require CI before merge with:

```bash
gh api -X PUT repos/effekt/dAImon/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -f 'required_status_checks[strict]=true' \
  -f 'required_status_checks[contexts][]=test' \
  -f 'required_status_checks[contexts][]=lint' \
  -f 'required_status_checks[contexts][]=conventional' \
  -f 'required_pull_request_reviews[required_approving_review_count]=0' \
  -F 'enforce_admins=false' -F 'restrictions=' -F 'required_linear_history=true' \
  -F 'allow_force_pushes=false' -F 'allow_deletions=false'
```
