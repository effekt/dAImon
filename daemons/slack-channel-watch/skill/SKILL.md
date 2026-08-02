---
name: slack-channel-watch
description: Poll Slack channels for trigger-prefixed command messages and forward them to the command daemon's inbox.
---

# slack-channel-watch

Front door for the `{{inputs.target}}` plugin engine when no Slack app can
be installed: watch the channels in `{{inputs.watch_channels}}` and forward
new command messages. Be fast and cheap — read, forward, exit. Never
execute commands yourself.

## 1. Read new messages

`daimon state get` → `last_ts`, a map of channel id → newest activity
timestamp already seen. For each watched channel, read it with the Slack
MCP `slack_read_channel` (load deferred tools via ToolSearch). A message
is a command when it is: newer than `last_ts`, from a human user, and its
text starts with `{{inputs.trigger_prefix}}` — everything else is ignored,
so mixed-purpose channels are safe. Commands count **in threads too**: for
any message whose thread has replies newer than `last_ts`, read the thread
(`slack_read_thread`) and apply the same test to the replies. A channel
with no recorded `last_ts` yet gets a baseline-only pass — record the
newest timestamp, forward nothing old.

If nothing qualifies anywhere, finish with a one-line "no new commands"
(still advance `last_ts` per channel so old chatter isn't rescanned).

## 2. Forward

Strip the trigger prefix from each command's text. Resolve the state dir
(`daimon config paths` → `DAIMON_STATE_DIR`) and append one entry per
command to `$DAIMON_STATE_DIR/runtime/inbox.json` (`{"messages": [...]}`,
preserving existing messages):

```json
{"to": "{{inputs.target}}", "command": "<text without prefix>", "channel": "<message's channel id>",
 "thread_ts": "<message ts>", "user": "<author user id>", "via": "channel"}
```

`thread_ts` is the command message's own `ts`, so the reply threads under
it. Then nudge the engine with `daimon run {{inputs.target}}` — the inbox
gate launches it immediately. Run the nudge **in the background /
fire-and-forget** (e.g. Bash `run_in_background`): `daimon run` blocks
until the launched agent finishes, and you must not sit through the
engine's whole run — forward, nudge, exit.

## 3. Finish

`daimon state set` with the updated per-channel map, EXACTLY this shape —
timestamps nested under a `last_ts` key, never at the top level (the
scripted gate reads this same record):

```json
{"last_ts": {"<channel id>": "<newest ts>", "...": "..."}}
```

Summarize: how many forwarded, from which channels.
