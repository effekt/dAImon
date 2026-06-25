# Agent backends

A backend teaches dAImon how to drive one agent CLI inside a tmux session. Each
backend is a bash file (`backends/<name>.sh`) sourced by `lib/launch.sh`. Select
it per daemon with `[daemon].backend` = `claude` | `codex` | `both` (`both` runs
the listed backends sequentially, each in its own session).

## Contract

A backend must define these functions:

| Function | Args | Returns / effect |
|----------|------|------------------|
| `backend_bin` | — | Absolute path to the CLI (honor `DAIMON_<NAME>_BIN` override). |
| `backend_cli_args` | `model danger session_name` | The argument string placed after the binary. `danger` is `1`/`0`; map it to the CLI's run-dangerous flag (empty when `0`). |
| `backend_ready_regex` | `danger` | A regex `lib/launch.sh` greps the pane for to know the UI is ready. Echo empty to skip banner detection and use a fixed boot delay instead. |
| `backend_completion_mode` | — | `hook` (a Stop-hook touches the sentinel; precise) or `idle` (no hook; completion inferred from heartbeat staleness). |

## How the launcher uses them

`lib/launch.sh` exports `DAIMON_SENTINEL`, `DAIMON_HEARTBEAT`, and `DAIMON_WAIT`,
opens `tmux new-session` running `<env> exec <backend_bin> <backend_cli_args>`,
waits for `backend_ready_regex` (or the boot delay), types the daemon's
`command`, then blocks until: the sentinel appears (`hook` mode), the session
dies, or the heartbeat goes stale for `stuck_after` seconds. Teardown and the
MCP-orphan sweep in `lib/reap.sh` are backend-independent.

## Hooks

`hook`-mode backends need their hooks installed once (the installer merges
`config/hooks/<name>-hooks.*`). The hooks are gated on the `DAIMON_*` env vars so
they are inert in your own non-daemon sessions.
