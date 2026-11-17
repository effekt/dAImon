# Slack commands

Run commands against your local agent environment from Slack, and let
daemons post updates back. Three pieces:

| Piece | What it does |
|---|---|
| `slack-commands` daemon | The engine. Reads commands from its inbox, runs the matching plugin runbook, replies in Slack. |
| A front door | The `slack-channel-watch` daemon (polls channels for `?`-prefixed messages — no Slack app needed). |
| `slack-standup` daemon | Scheduled outbound: posts a standup on a weekday cadence. |

## Prerequisites

- **Slack MCP** — the daemons reach Slack only through Slack's hosted MCP server.
  For Claude, run `plugin install slack@claude-plugins-official`, then authorize
  once in an interactive session with `/mcp`. For Codex fallback, run
  `daimon mcp setup slack` once and complete Slack OAuth in the browser. The
  first setup in a workspace uses Slack CLI authentication to create a
  dedicated internal `dAImon Codex` app with MCP + PKCE enabled and a fixed
  local callback. It stores only the public app and client IDs under dAImon's
  state directory. Run `daimon mcp share slack` to print the setup command for
  teammates; each developer reuses the same app but completes OAuth into their
  own Codex credential store. If your workspace already provides an
  MCP-enabled app, pass its public ID as `daimon mcp setup slack <client-id>`
  instead. `daimon doctor` checks both paths, including whether Codex completed
  OAuth.
- **jq** and **gh**. `make tooling` reports what's missing.

## Set up the front door

**Channel watcher (no app, no admin approval).** Configure
`~/.config/daimon/daemons/slack-channel-watch.toml` with the channel IDs to
watch; anyone types `?help` in one of them. Two polling modes:

- *Scripted* (preferred): set `token_command` to a command printing a
  Slack token with `channels:history` / `groups:history` scope. The gate
  polls in pure script — no agent launches, so ticks are free and the
  interval can go to 30s.
- *Agent fallback* (`token_command` empty): each tick is a short agent
  session using the Slack MCP. Works with no extra token; costs a model
  call per tick, so keep the interval at 120s or higher.

## Writing a command

Commands are markdown runbooks, one file per command:

- `catalog/slack-commands/commands/` — committed, shared by everyone.
- `commands/` in each [pack](packs.md) — your team's.
- `~/.config/daimon/commands/` — yours, outside every repo; a file here
  overrides a shared or pack one of the same `name`. `daimon command new <name>`
  writes here. (Older installs kept these in the gitignored
  `daemons/slack-commands/commands.local/`; it is still read until
  `daimon migrate` moves its files.)

Drop a file in, and it's live on the next run — no sync, no restart.

```markdown
---
name: prod-status
match: prod-status
mutating: false
description: What shipped to production recently.
---

1. `gh pr list --state merged --limit 50` filtered to the window.
2. Reply with ticket-led bullets grouped by scope.
```

Conventions:

- **Name**: one hyphenated token, `{domain}-{action/topic}`
  (`staging-push`, `epic-status`); a bare domain only when unambiguous
  (`standup`). Everything after the first space is arguments.
- **`mutating: true`** — restricted to the `mutate_allowlist` (config) plus
  anyone granted from Slack via `access grant @user`. Use it for anything
  that writes, deploys, or spends real work.
- **`admin: true`** — allowlist only, and hidden from listings for
  everyone else.
- Runbooks run from the daemon's `working_dir`, so repo tooling is just
  there. Write them as instructions, not scripts: state the goal, the
  commands to run, and the reply shape.
- Long work (an implementation, a deploy) must be **launched detached**
  and reported asynchronously — never block the engine, or other queued
  commands stall behind it.

## Access control

`mutate_allowlist` in your `~/.config/daimon/daemons/slack-commands.toml` is the root of trust (Slack user
IDs, machine-only). Those admins manage everyone else from Slack:
`access list` / `access grant @user` / `access revoke @user`, persisted in
daemon state. Grants never confer admin.
