---
name: slack-standup
description: Generate the daily standup and post it to a Slack channel (Mon–Fri, once per day).
---

# slack-standup

Post the daily standup to **#{{inputs.channel_name}}** (`{{inputs.channel_id}}`).
You run inside `working_dir`, so repo- and tracker-aware tools target it
automatically. Audience is a PM plus other devs — factual, lean, grouped by
theme.

## 1. Discover

Confirm today's standup hasn't already been posted: read `daimon state get` —
if `last_posted` equals today's date in `{{inputs.tz}}`, stop and report
"already posted". (discover.sh normally prevents this, but a manual run can
bypass it.)

## 2. Generate

**Override:** if `{{inputs.standup_command}}` is non-empty, invoke that skill,
use its output verbatim, and skip to §3. Otherwise build the standup from the
steps below.

1. **Window** — shipped work since the start of yesterday (in
   `{{inputs.tz}}`); use the current date from the environment, never
   hardcoded. Also compute `STALE_CUTOFF` = 7 days back.
2. **Merged PRs** — `gh pr list --state merged --author "@me"` filtered to
   the window.
3. **Open PRs** — `gh pr list --state open --author "@me"`;
   keep every non-draft, drop drafts untouched since `STALE_CUTOFF` (note them
   in one trailing italic aside).
4. **Tracker context** — follow these instructions if present (how to query
   the work tracker: CLI, owner handle, state names):

   > {{inputs.tracker_hints}}

   Use ticket references in PR titles to pair PRs with tickets, mark shipped
   tickets Done ✅, and find what's next: ready-state tickets with no PR yet,
   restricted to ones updated since `STALE_CUTOFF` — a months-old "next up" is
   worse than none. Skip this step entirely if the blockquote above is empty.
5. **Focus hints** — apply these instructions if present (extra sections to
   split out, extra sources to check, work beyond PRs/tickets to surface,
   exclusions):

   > {{inputs.focus_hints}}

## 3. Format

A single Slack-markdown message (`**bold**`, `[text](https://url)`, `- `
bullets, emoji shortcodes; no `#` headers, tables, or `---` rules):

- Lead line: `:calendar: **Standup — <weekday M/D>**`.
- Sections, each `:emoji: **Title**` + bullets; omit empty ones, blank line
  between: `:white_check_mark: **Shipped**`, any section the focus hints call
  for, `:construction: **In progress**` (one-clause status per item; :no_entry:
  + reason when blocked), `:arrow_right: **Next up**` (top 1–2).
- Bullet shape — ticket-led: `[<ticket-id>](https://ticket-url): <title,
  truncated to ~60 chars at a word boundary> ([#NNNN](https://pr-url))`.
  Several PRs on one ticket → one bullet, PR links listed together. PR with
  no ticket → PR title only. Ticket with no PR → drop the parens.
- Links are always labeled (`[text](https://url)`), never bare URLs — bare
  URLs make Slack attach link previews; the message must post without any.
- Never include timestamps or times of day; dates come only from the lead
  line. One line per item. No closing offers.

If there is nothing to report, still post a short "no updates today" line —
an absent standup reads as a missed run.

## 4. Post and finish

Post with the Slack MCP tool `slack_send_message` to `{{inputs.channel_id}}`.
One message, posted directly — no draft, no thread. If the Slack tools are
deferred, load them with ToolSearch first.

Record `{"last_posted": "<today YYYY-MM-DD in {{inputs.tz}}>"}` with
`daimon state set`. Summarize with the posted message's permalink (or channel +
timestamp).
