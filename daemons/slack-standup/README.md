# slack-standup

Posts a daily standup to a Slack channel, Mon–Fri at the scheduled time, once
per day.

- **Schedule** — `daily = "11:00"` in the configured tz; `discover.sh` gates to
  weekdays and skips if the state file already records a post for today
  (launchd re-fires missed jobs on wake, so the gate — not the schedule —
  enforces once-per-day).
- **Content** — the run invokes the configured `standup_command` skill inside
  `working_dir` and posts its output verbatim.
- **Slack access** — via the user-level `slack` plugin's MCP tools
  (`slack_send_message`), which must already be OAuth'd. No daimon `mcp` entry
  is involved.
- **Inputs** — `channel_id` (required), `channel_name`, `tz` (must match the
  schedule's tz), `standup_command`.
- **State** — `{"last_posted": "YYYY-MM-DD"}`, written by the skill after a
  successful post and read by `discover.sh`.

Copy `daemon.local.toml.example` → `daemon.local.toml` and set `working_dir`,
the channel inputs, and any schedule override.
