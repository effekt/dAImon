# Writing a daemon

A daemon is a folder under `daemons/<slug>/` with three files. The framework
auto-discovers it; `daimon sync` regenerates its plist and renders its skill.

## 1. `daemon.toml`

```toml
[daemon]
backend = "claude"                 # claude | codex | both
working_dir = "~/code/my-repo"     # the repo the agent runs inside
schedule = { interval = 1800 }     # or { minutes = [8,38] } / { daily = "13:02" }
command = "/my-daemon"             # slash-command typed into the session
# model / danger / stuck_after override [defaults] when set

[inputs]                           # task variables, your own keys
source = "github-issues"
access = "gh"
repo = "me/my-repo"
filter = "label:needs-triage"
```

## 2. `discover.sh`

The gate: exit `0` to launch the agent this fire, non-zero to skip. Inputs arrive
as `DAIMON_INPUT_*`. Keep it cheap.

```bash
#!/usr/bin/env bash
set -uo pipefail
count=$(gh issue list --repo "$DAIMON_INPUT_REPO" --search "$DAIMON_INPUT_FILTER" \
  --json number --jq 'length' 2>/dev/null || echo 0)
[ "${count:-0}" -gt 0 ]
```

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

## Activate

```bash
daimon config validate
daimon run my-daemon      # one gated run now
daimon sync               # regenerate plist + skill
daimon tui                # enable scheduling with [e]
```

## Generating from Python

Instead of writing the folder by hand, register in `examples/daemons.py` and run
`daimon sync` — the decorated function becomes `discover.sh`. Loop over a list of
repos to emit one daemon per repo. See the README.

## Tips

- One daemon targets one repo. Cover many repos with one daemon each.
- `/daimon-builder` scaffolds all three files interactively.
- Codex completion is idle-based — set a sensible `stuck_after` (the quiet window
  that means "done") for `codex`/`both` daemons.
