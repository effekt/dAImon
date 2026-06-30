# Writing a daemon

A daemon is a folder under `daemons/<slug>/` with three files. The framework
auto-discovers it; `daimon sync` regenerates its plist and renders its skill.

## 1. `daemon.toml`

```toml
[daemon]
backend = "claude"
working_dir = "~/code/my-repo"     # the repo the agent runs inside
schedule = { interval = 1800 }     # or { minutes = [8,38] } / { daily = "13:02" }
command = "/my-daemon"             # slash-command typed into the session
required_inputs = ["repo", "filter"]  # asserted non-empty before discover runs
# model / danger / stuck_after override [defaults] when set

[inputs]                           # task variables, your own keys
source = "github-issues"
access = "gh"
repo = "me/my-repo"
filter = "label:needs-triage"
```

## 2. `discover.sh`

The gate. Inputs arrive as `DAIMON_INPUT_*`. Keep it cheap. Exit codes are read as:

- `0` — work found; launch the agent this fire.
- `1` with no stderr — nothing to do; skip until the next run.
- any stderr output, or exit `≥2` — the gate itself errored. `run.sh` logs this as
  `discover_error` rather than silently treating it as "no work", so a broken gate
  surfaces instead of disabling the daemon invisibly. List the inputs the gate
  depends on in `required_inputs` so a missing one is caught before this runs.

```bash
#!/usr/bin/env bash
set -uo pipefail
source "$(dirname "$0")/../../profiles/github/lib.sh"
[ "$(gh_pr_count --search "$DAIMON_INPUT_FILTER")" -gt 0 ]
```

`profiles/github/lib.sh` provides fail-closed gate helpers (`gh_pr_json`,
`gh_pr_count`, `gh_search_pr_count`, `load_seen_state`); `profiles/shortcut/lib.sh`
is the equivalent for story gates.

## 3. `skill/SKILL.md`

The prompt, in Claude Code skill format. Reference inputs as `{{inputs.<key>}}`;
`daimon sync` renders them and installs the result to `~/.claude/skills/<command>`.

```markdown
---
name: my-daemon
description: What this daemon does.
---

# my-daemon
Find work in {{inputs.source}} via `{{inputs.access}}` matching {{inputs.filter}}.
For each item: <do the work>. Record what you handled so the next run skips it.
```

Every rendered skill also gets `references/learning.md` appended — a protocol for
reading this project's Claude memory at the start of a run (to skip known false
positives) and writing lessons at the end (so the next run is smarter). Set
`learning = false` in `[daemon]` to opt a daemon out.

A daemon that posts comments (it has a `bot_marker` input) additionally gets
`references/skill-conventions.md` appended — the marker-every-comment and
durable-state-in `$DAIMON_STATE_FILE` conventions — so you inherit them instead of
restating them in each skill.

## Activate

```bash
daimon config validate
daimon run my-daemon      # one gated run now
daimon sync               # regenerate plist + skill
daimon tui                # enable scheduling with [e]
```

## Tips

- One daemon targets one repo. Cover many repos with one daemon each.
- `/daimon-builder` scaffolds all three files interactively.
- `stuck_after` is the idle-gap reaper, not a runtime cap — set it to comfortably
  exceed the longest quiet stretch a healthy run goes through mid-task.
