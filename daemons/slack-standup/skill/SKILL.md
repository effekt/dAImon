---
name: slack-standup
description: Generate the daily standup and post it to a Slack channel (Mon–Fri, once per day).
---

# slack-standup

Post the daily standup to **#{{inputs.channel_name}}** (`{{inputs.channel_id}}`).
You run inside `working_dir`, so repo- and tracker-aware skills target it
automatically.

## 1. Discover

Confirm today's standup hasn't already been posted: read `daimon state get` —
if `last_posted` equals today's date in `{{inputs.tz}}`, stop and report
"already posted". (discover.sh normally prevents this, but a manual run can
bypass it.)

## 2. Act

1. Invoke the `{{inputs.standup_command}}` skill to generate the standup. Use
   its output as-is — it is already Slack-ready; do not restructure or pad it.
2. Post it with the Slack MCP tool `slack_send_message` to
   `{{inputs.channel_id}}`. One message, posted directly — no draft, no
   thread. If the Slack tools are deferred, load them with ToolSearch first.

If `{{inputs.standup_command}}` produces nothing to report, still post a short
"no updates today" line rather than staying silent — an absent standup reads
as a missed run.

## 3. Finish

Record `{"last_posted": "<today YYYY-MM-DD in {{inputs.tz}}>"}` with
`daimon state set`. Summarize with the posted message's permalink (or channel +
timestamp).
