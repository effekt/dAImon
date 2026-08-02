---
name: slack-commands
description: Handle bridged Slack commands from the daimon inbox via plugin runbooks, with an allowlist gate on mutating commands.
---

# slack-commands

You are launched because a Slack bridge app queued command messages in the
daimon inbox. Handle every queued message, reply in Slack, and finish. You
run inside `working_dir`.

## 1. Drain the inbox

Resolve the state dir (`daimon config paths` → `DAIMON_STATE_DIR`); the inbox
is `$DAIMON_STATE_DIR/runtime/inbox.json` with shape
`{"messages": [{"to": "<slug>", ...}]}`. In one small python/jq step, take
every message with `to == "slack-commands"` and rewrite the file with exactly
those removed (other daemons' messages stay). If none were queued, report
"inbox empty" and stop.

Each taken message has: `command` (text), `channel`, optional `thread_ts`,
`user` (Slack user ID of the requester), `via`.

## 2. Load command plugins

Read every `*.md` in `{{inputs.commands_dir}}` then
`{{inputs.local_commands_dir}}` (paths relative to the dAImon install root;
a local plugin with the same `name` replaces the shared one). Each plugin has
frontmatter — `name`, `match` (prefix the command text must start with),
`mutating` (bool), `description` — and a body that is the runbook to follow.

## 3. Handle each message

1. Match `command` against the plugins: case-insensitive, longest `match`
   prefix wins; the remainder of the text is the arguments.
2. **No match** → reply with the command list (`name` — description per
   plugin, mutating ones marked "restricted").
3. **`mutating: true`** and `user` is not in `{{inputs.mutate_allowlist}}`
   → reply that the command is restricted and who to ask; do NOT execute
   any part of the runbook.
4. Otherwise follow the plugin's runbook with the arguments. Runbooks run
   from `working_dir`.

## 4. Reply

Reply with the Slack MCP tool `slack_send_message` to the message's
`channel`, threading on `thread_ts` when present (load deferred tools with
ToolSearch first). One concise reply per message: labeled links only (never
bare URLs), no timestamps, no closing offers. On a runbook failure, reply
with the actual error rather than staying silent — a missing reply reads as
a lost command.

## 5. Finish

Append the handled commands to `daimon state set` as
`{"handled": [{"command", "user", "ok"}]}` merged over the previous record.
Summarize what was handled and how each reply went.
