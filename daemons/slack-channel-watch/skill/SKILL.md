---
name: slack-channel-watch
description: Poll a Slack channel for command messages and forward them to the command daemon's inbox.
---

# slack-channel-watch

Front door for the `{{inputs.target}}` plugin engine when no Slack app can
be installed: watch **#{{inputs.watch_channel_name}}**
(`{{inputs.watch_channel_id}}`) and forward new command messages. Be fast
and cheap — read, forward, exit. Never execute commands yourself.

## 1. Read new messages

`daimon state get` → `last_ts` (the newest message timestamp already
forwarded). Read the channel with the Slack MCP `slack_read_channel`
(`oldest` = `last_ts`; load deferred tools via ToolSearch). Keep only
messages that are: newer than `last_ts`, top-level (not thread replies),
from a human user, and not obvious acks/bot output. Each remaining
message's text is a command.

If there are none, record nothing and finish with a one-line "no new
messages".

## 2. Forward

Resolve the state dir (`daimon config paths` → `DAIMON_STATE_DIR`). Append
one entry per command to `$DAIMON_STATE_DIR/runtime/inbox.json`
(`{"messages": [...]}`, preserving existing messages):

```json
{"to": "{{inputs.target}}", "command": "<text>", "channel": "{{inputs.watch_channel_id}}",
 "thread_ts": "<message ts>", "user": "<author user id>", "via": "channel"}
```

`thread_ts` is the command message's own `ts`, so the reply threads under
it. Then run `daimon run {{inputs.target}}` — the inbox gate launches the
engine immediately.

## 3. Finish

`daimon state set` with `last_ts` = the newest forwarded message's `ts`
(merged over the existing record). Summarize: how many forwarded.
