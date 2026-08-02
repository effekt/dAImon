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

`daimon state get` → `last_ts`, a map of channel id → newest message
timestamp already forwarded. For each watched channel, read it with the
Slack MCP `slack_read_channel` (`oldest` = that channel's `last_ts`; load
deferred tools via ToolSearch). A message is a command when it is: newer
than `last_ts`, top-level (not a thread reply), from a human user, and its
text starts with `{{inputs.trigger_prefix}}` — everything else in the
channel is ignored, so mixed-purpose channels are safe.

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
it. Then run `daimon run {{inputs.target}}` — the inbox gate launches the
engine immediately.

## 3. Finish

`daimon state set` with the updated per-channel `last_ts` map (merged over
the existing record). Summarize: how many forwarded, from which channels.
