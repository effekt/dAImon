<p align="center">
  <img src="assets/logo.jpeg" alt="dAImon" width="240">
</p>

<h1 align="center">dAImon</h1>

Scheduled, autonomous agent daemons. Each daemon fires on a schedule, launches an
interactive agent CLI (Claude or Codex) inside a detached tmux session pointed at a
target repository, drives it with a slash-command, and blocks until the run
finishes or goes idle — no wall-clock cap, just an idle-gap reaper. A watchdog
sweeps orphans and leaked MCP servers; a Textual TUI is the control panel.

## Concepts

- **Daemon** — a self-contained folder `daemons/<slug>/` with `daemon.toml`
  (settings + task `[inputs]`), `discover.sh` (a gate: should this fire do work?),
  and `skill/SKILL.md` (the prompt). Auto-discovered; drop one in and it exists.
- **Backend** — the agent CLI that drives the session: `claude`, `codex`, or
  `both` (sequential). Pluggable via `backends/<name>.sh`.
- **working_dir** — the repository a daemon operates in. The agent runs *inside*
  that trusted folder so it gets project context, MCP servers, and project skills.
  One daemon targets one repo; run many repos by registering one daemon per repo.
- **Completion/liveness** — Claude signals done via a Stop hook (a sentinel file);
  liveness via a heartbeat touched on every tool call. Codex has no such hook, so
  it uses idle detection backed by a pane-activity heartbeat.

## Quick start

```bash
git clone <your-fork> ~/dev/dAImon
cd ~/dev/dAImon
make install                 # hooks, TUI venv, skills, plists (not scheduled); puts `daimon` on PATH
make doctor                  # verify tools, gh auth, hooks, config
$EDITOR ~/.config/daimon/daimon.toml                       # globals: state_dir, defaults
$EDITOR daemons/review-prs/daemon.local.toml               # your working_dir + [inputs] (gitignored)
make validate
daimon run review-prs        # one gated run, now — watch with `daimon tui`
make install-load            # schedule everything via launchd
```

`make install` symlinks `daimon`/`daimonctl` into `~/.local/bin`; `make help` lists targets.

## Adding a daemon

Two ways, both producing the same `daemons/<slug>/` folder:

1. **Interactive** — run `/daimon-builder` in Claude; it interviews you and writes
   the folder.
2. **By hand** — copy an existing `daemons/<slug>/`, edit `daemon.toml`, then
   `daimon sync` to regenerate its plist and render its skill.

## CLI

```
daimon run <slug>        gated run (throttle/inbox/discovery) then launch
daimon launch <slug>     launch now, bypass gates
daimon daemons           list discovered daemons
daimon status            launchd + running-session state
daimon models <backend>  available models (live API or bundled fallback)
daimon config <args>     config core (validate|get|daemon|schedule|...)
daimon sync              regenerate plists + render skills
daimon kill <slug|all>   hard-kill a run
daimon ps <slug|all>     process tree
daimon watchdog          sweep orphans + leaked MCP + old logs
daimon tui               control panel
```

## Configuration

Global settings in `~/.config/daimon/daimon.toml`; per-daemon in
`daemons/<slug>/daemon.toml`. Full field reference: [docs/configuration.md](docs/configuration.md).
Run-dangerous, model, schedule, backend, and idle timeout are all configurable
globally and per daemon.

## Logging

Per daemon, under `state_dir/logs/`: a structured operational log (`<slug>.log`)
and per-run agent transcripts (`transcripts/<slug>-<backend>-<ts>.log`).
Transcripts are pruned after `log_retention_days`; operational logs rotate at
`log_max_mb`. Cleanup runs in the watchdog cycle.

## Testing

```bash
bash tests/run.sh
```

Covers config merge/validation/rendering, model discovery, the skills validator,
and bash syntax across all libs.

## Layout

`lib/` framework · `backends/` agent CLIs · `daemons/` the daemons · `daimon/`
sync (plists + skills) · `tui/` control panel · `skills/` management commands ·
`config/` defaults + hooks · `docs/`.
