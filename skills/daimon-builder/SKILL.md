---
name: daimon-builder
description: Interactively scaffold a new dAImon daemon — gather the task, source, access tool, schedule, and backend, then write the daemon folder and validate it.
---

# daimon-builder

Guide the user through creating a new daemon and write the files for them. A daemon
is a self-contained folder containing `daemon.toml`, `discover.sh`, and
`skill/SKILL.md`. The framework auto-discovers it.

## 0. Where it goes

A daemon lives in dAImon's own `daemons/` (generic, shareable with anyone) or in a
**pack**: a team's own repo of daemons and settings (`docs/packs.md`).

- If the arguments include `--pack` (optionally with a directory), it goes in that
  pack, or the first configured one.
- Otherwise run `daimon packs`. If any pack is configured, ask: is this daemon
  generic, or specific to the team (its systems, channels, IDs, workflow)? Team
  daemons go in the pack.

## 1. Interview

Ask for whatever isn't already clear. Keep it to a few focused questions:

- **Slug** — kebab-case id (e.g. `triage-issues`). Becomes the folder name, the
  tmux session prefix, and the launchd label.
- **What it does** — one sentence; becomes the SKILL.md description and shapes the prompt.
- **Source** — where the work items live (e.g. `github-issues`, `github-prs`, a REST API).
- **Access** — the CLI or MCP that reads the source (`gh`, `git`, `mcp:<server>`, `curl`).
  Confirm it's installed/configured; if it's an MCP, note the server name.
- **Filter / scope** — repo, labels, query, etc. — whatever narrows the work set.
- **Schedule** — `{ interval = N }` seconds, `{ minutes = [..] }`, or `{ daily = "HH:MM" }`.
- **Backend** — `claude` (interactive) or `codex` (one-shot `codex exec`). Offer
  the models with `daimon models <backend>` and let them pick; on `codex`, set the
  model as a table (`model = { codex = "..." }`).
- **Fallback backend** — optionally set `fallback_backend = "codex"` for a Claude
  daemon. It runs only when Claude reports provider-cap exhaustion.
- **MCP** — optionally attach an MCP server (opt-in; e.g. `mcp = ["codex"]` gives a
  Claude daemon a Codex second opinion). Requires danger on.
- **Danger** — whether to run with permissions/approvals skipped (default: inherit `[defaults]`).

## 2. Write the files

Start from the skeleton, which works in either place and starts inert:

```bash
daimon scaffold <slug>            # dAImon's daemons/
daimon scaffold <slug> --pack     # the first pack (or --pack <dir>)
```

It prints the folder it created; edit the files there (below, `<dir>`). In a pack,
put values the team shares in `daemon.toml` and anything personal in
`daemon.local.toml` (gitignored).

Fill in `<dir>/daemon.toml`:

```toml
[daemon]
backend = "<backend>"
schedule = { <chosen schedule> }
command = "/<slug>"
# include model/danger/stuck_after only when overriding [defaults]

[inputs]
source = "<source>"
access = "<access>"
# plus repo/filter/etc. the prompt needs
```

Fill in `<dir>/skill/SKILL.md` from the template below, referencing inputs
as `{{inputs.<key>}}` so `daimon sync` can render them. For a source that doesn't
fit the template's shape, rewrite the prose to match how that source actually works.

```markdown
---
name: <slug>
description: <what it does>
---

# <slug>

## 1. Discover
Find work items in **{{inputs.source}}** via `{{inputs.access}}` matching <filter>.
Skip anything already handled (track it in the daemon's state file).

## 2. Act
For each item: <the per-item work>.

## 3. Finish
Record what was handled; summarize briefly.
```

Write the gate in `<dir>/discover.sh`: exit 0 to launch, non-zero to skip. Inputs
arrive as `DAIMON_INPUT_*`. Model it on `daemons/review-prs/discover.sh`, but keep
the skeleton's `source "$DAIMON_INSTALL_ROOT/..."` lines rather than `../../`
paths, which break in a pack. Replace the skeleton's final `exit 1`: until then the
daemon never launches.

## 3. Validate and offer to activate

Run `daimon config validate`. If clean, tell the user they can `daimon sync` to
generate the launchd plist and render the skill into `~/.claude/skills/`, then
`daimon run <slug>` to try it once. Do not enable launchd scheduling without asking.
For a pack daemon, remind them to commit it in the pack's repo (a PR, if the team
reviews pack changes) so teammates get it on their next `daimon sync`.
