# env-bridge

A deliberately thin Slack → local-agent bridge. It runs on your machine in
Socket Mode (no hosting, no public endpoint) and does exactly one thing: turn
a slash command or @-mention into a message in your
[dAImon](https://github.com/effekt/dAImon) inbox, then nudge the
`slack-commands` daemon to handle it. All command logic — parsing,
authorization, execution, replying — lives in that daemon's plugin-driven
skill, so adding a command never touches this app.

```
/hub standup            env-bridge (Socket Mode, local)
@env-bridge epic 123  ─────────────► daimon inbox ──► slack-commands daemon
                                                        (your local agent:
                                                         full MCP + repo access)
```

## Why this shape

- **The app is dumb on purpose.** No AI key, no business logic, ~60 lines.
  The brain is your existing local agent environment, which already has the
  credentials and context (repo, tracker CLI, MCP servers) that a hosted app
  can't have.
- **Commands are plugins.** Each command is a markdown runbook in the
  daemon's `commands/` directory (shared) or `commands.local/` (yours /
  your company's, gitignored). Drop in a file, get a command.
- **Authorization is central.** Mutating commands are gated on a Slack
  user-ID allowlist in the daemon's config, not in app code.

## Setup

1. Prereqs: [Slack CLI](https://docs.slack.dev/tools/slack-cli) (authed to
   your workspace), Node 18+, a dAImon install with the `slack-commands`
   daemon configured.
2. `slack run` — installs the app to your workspace (workspace admin
   approval may be required) and starts the local Socket Mode process.
3. Try `/hub` in Slack for usage, or `@env-bridge help`.

## Configuration (env)

| Variable | Default | Purpose |
|----------|---------|---------|
| `BRIDGE_SLASH_COMMAND` | `/hub` | Slash command to listen for (must match the manifest) |
| `DAIMON_STATE_DIR` | `~/.local/state/daimon` | Where the daimon inbox lives |
| `DAIMON_BIN` | `~/.local/bin/daimon` | The daimon CLI used to nudge the daemon |

## Notes

- Replies come from the daemon's Slack credentials, not this bot — the app
  only posts the ephemeral "queued" acknowledgement.
- `.scrap/` holds unused Slack starter-template parts; delete it freely.
